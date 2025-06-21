package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"time"
)

// Monitor handles site monitoring
type Monitor struct {
	client          *MasterClient
	sites           map[int]*Site
	tasks           map[int]context.CancelFunc
	mu              sync.RWMutex
	ctx             context.Context
	cancel          context.CancelFunc
	httpClient      *http.Client
	minSyncInterval time.Duration
}

// NewMonitor creates a new monitor instance
func NewMonitor(client *MasterClient) *Monitor {
	ctx, cancel := context.WithCancel(context.Background())

	return &Monitor{
		client: client,
		sites:  make(map[int]*Site),
		tasks:  make(map[int]context.CancelFunc),
		ctx:    ctx,
		cancel: cancel,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
			Transport: &http.Transport{
				MaxIdleConns:       100,
				IdleConnTimeout:    90 * time.Second,
				DisableCompression: false,
			},
		},
		minSyncInterval: 5 * time.Minute, // Default fallback
	}
}

// parseScanInterval parses scan interval string like "30s", "2m", "1h" into duration
func (m *Monitor) parseScanInterval(interval string) (time.Duration, error) {
	interval = strings.TrimSpace(strings.ToLower(interval))

	re := regexp.MustCompile(`^(\d+(?:\.\d+)?)([smh])$`)
	matches := re.FindStringSubmatch(interval)

	if len(matches) != 3 {
		return 0, fmt.Errorf("invalid interval format: %s", interval)
	}

	value, err := strconv.ParseFloat(matches[1], 64)
	if err != nil {
		return 0, fmt.Errorf("invalid interval value: %s", matches[1])
	}

	unit := matches[2]
	var duration time.Duration

	switch unit {
	case "s":
		duration = time.Duration(value * float64(time.Second))
	case "m":
		duration = time.Duration(value * float64(time.Minute))
	case "h":
		duration = time.Duration(value * float64(time.Hour))
	default:
		return 0, fmt.Errorf("unsupported time unit: %s", unit)
	}

	return duration, nil
}

// calculateSyncInterval calculates the optimal sync interval based on site scan intervals
func (m *Monitor) calculateSyncInterval(sites []Site) time.Duration {
	if len(sites) == 0 {
		return 5 * time.Minute // Default when no sites
	}

	minInterval := 5 * time.Minute // Default minimum

	for _, site := range sites {
		if interval, err := m.parseScanInterval(site.ScanInterval); err == nil {
			// Sync should be at least 4x faster than the fastest scan interval
			syncInterval := interval / 4
			if syncInterval < minInterval {
				minInterval = syncInterval
			}
		}
	}

	// Don't sync faster than every 10 seconds
	if minInterval < 10*time.Second {
		minInterval = 10 * time.Second
	}

	// Don't sync slower than every 5 minutes
	if minInterval > 5*time.Minute {
		minInterval = 5 * time.Minute
	}

	return minInterval
}

// checkHTTPSite checks an HTTP/HTTPS site
func (m *Monitor) checkHTTPSite(ctx context.Context, site *Site) CheckResult {
	start := time.Now()
	result := CheckResult{
		SiteID:    site.ID,
		Status:    "down",
		CheckedAt: time.Now().UTC().Format("2006-01-02T15:04:05.000Z"),
	}

	req, err := http.NewRequestWithContext(ctx, "GET", site.URL, nil)
	if err != nil {
		errMsg := fmt.Sprintf("Failed to create request: %v", err)
		result.ErrorMessage = &errMsg
		responseTime := time.Since(start).Seconds()
		result.ResponseTime = &responseTime
		return result
	}

	req.Header.Set("User-Agent", "SREoob-Agent/1.0")

	resp, err := m.httpClient.Do(req)
	responseTime := time.Since(start).Seconds()
	result.ResponseTime = &responseTime

	if err != nil {
		errMsg := fmt.Sprintf("Request failed: %v", err)
		result.ErrorMessage = &errMsg
		return result
	}
	defer resp.Body.Close()

	result.StatusCode = &resp.StatusCode

	if resp.StatusCode < 400 {
		result.Status = "up"
	} else {
		result.Status = "down"
		errMsg := fmt.Sprintf("HTTP %d", resp.StatusCode)
		result.ErrorMessage = &errMsg
	}

	return result
}

// checkPingSite checks a ping:// site
func (m *Monitor) checkPingSite(ctx context.Context, site *Site) CheckResult {
	start := time.Now()
	result := CheckResult{
		SiteID:    site.ID,
		Status:    "down",
		CheckedAt: time.Now().UTC().Format("2006-01-02T15:04:05.000Z"),
	}

	// Extract hostname from ping://hostname
	host := strings.TrimPrefix(site.URL, "ping://")

	// Create ping command with timeout
	var cmd *exec.Cmd
	if isWindows() {
		cmd = exec.CommandContext(ctx, "ping", "-n", "1", "-w", "5000", host)
	} else {
		cmd = exec.CommandContext(ctx, "ping", "-c", "1", "-W", "5", host)
	}

	output, err := cmd.Output()
	responseTime := time.Since(start).Seconds()
	result.ResponseTime = &responseTime

	if err != nil {
		errMsg := fmt.Sprintf("Ping failed: %v", err)
		result.ErrorMessage = &errMsg
		return result
	}

	// Try to extract actual ping time from output
	outputStr := string(output)
	timeRegex := regexp.MustCompile(`time[=<](\d+(?:\.\d+)?)ms`)
	if matches := timeRegex.FindStringSubmatch(outputStr); len(matches) > 1 {
		if pingTime, err := strconv.ParseFloat(matches[1], 64); err == nil {
			actualTime := pingTime / 1000.0 // Convert ms to seconds
			result.ResponseTime = &actualTime
		}
	}

	result.Status = "up"
	return result
}

// checkSite performs a check on a single site
func (m *Monitor) checkSite(ctx context.Context, site *Site) CheckResult {
	if strings.HasPrefix(site.URL, "ping://") {
		return m.checkPingSite(ctx, site)
	} else {
		return m.checkHTTPSite(ctx, site)
	}
}

// monitorSite monitors a single site according to its scan interval
func (m *Monitor) monitorSite(ctx context.Context, site *Site) {
	interval, err := m.parseScanInterval(site.ScanInterval)
	if err != nil {
		log.Printf("ERROR: Invalid scan interval '%s' for site '%s': %v", site.ScanInterval, site.Name, err)
		return
	}

	log.Printf("INFO: Starting monitoring for site '%s' (ID: %d) with %s interval", site.Name, site.ID, site.ScanInterval)

	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	// Perform initial check
	result := m.checkSite(ctx, site)
	m.logCheckResult(site, result)
	m.submitResult(ctx, result)

	for {
		select {
		case <-ctx.Done():
			log.Printf("INFO: Stopped monitoring site '%s' (ID: %d)", site.Name, site.ID)
			return
		case <-ticker.C:
			result := m.checkSite(ctx, site)
			m.logCheckResult(site, result)
			m.submitResult(ctx, result)
		}
	}
}

// submitResult submits a check result to the master if possible
func (m *Monitor) submitResult(ctx context.Context, result CheckResult) {
	// Try to submit result to master (best effort)
	if err := m.client.SubmitCheckResult(ctx, result); err != nil {
		// Log error but don't fail - monitoring continues
		log.Printf("WARN: Failed to submit result for site %d: %v", result.SiteID, err)
	}
}

// logCheckResult logs the result of a site check
func (m *Monitor) logCheckResult(site *Site, result CheckResult) {
	status := "❌"
	if result.Status == "up" {
		status = "✅"
	}

	responseTimeStr := ""
	if result.ResponseTime != nil {
		responseTimeStr = fmt.Sprintf(" (%.3fs)", *result.ResponseTime)
	}

	errorStr := ""
	if result.ErrorMessage != nil {
		errorStr = fmt.Sprintf(" - %s", *result.ErrorMessage)
	}

	log.Printf("%s %s: %s%s%s", status, site.Name, result.Status, responseTimeStr, errorStr)
}

// RefreshSites fetches sites from master and updates monitoring
func (m *Monitor) RefreshSites(ctx context.Context) error {
	sites, err := m.client.GetSites(ctx)
	if err != nil {
		return fmt.Errorf("failed to fetch sites: %w", err)
	}

	m.updateSites(sites)
	return nil
}

// updateSites updates the monitoring with new site list
func (m *Monitor) updateSites(sites []Site) {
	m.mu.Lock()
	defer m.mu.Unlock()

	// Create map of current sites
	currentSites := make(map[int]*Site)
	for i := range sites {
		currentSites[sites[i].ID] = &sites[i]
	}

	// Stop monitoring for sites that no longer exist
	for siteID, cancelFunc := range m.tasks {
		if _, exists := currentSites[siteID]; !exists {
			log.Printf("INFO: Stopping monitoring for removed site ID: %d", siteID)
			cancelFunc()
			delete(m.tasks, siteID)
			delete(m.sites, siteID)
		}
	}

	// Start monitoring for new sites
	for siteID, site := range currentSites {
		if _, exists := m.tasks[siteID]; !exists {
			log.Printf("INFO: Starting monitoring for new site: %s", site.Name)
			siteCtx, cancel := context.WithCancel(m.ctx)
			m.tasks[siteID] = cancel
			m.sites[siteID] = site
			go m.monitorSite(siteCtx, site)
		}
	}

	// Update sync interval based on new sites
	m.minSyncInterval = m.calculateSyncInterval(sites)

	log.Printf("INFO: Monitoring refresh complete - %d sites active, sync interval: %v",
		len(m.tasks), m.minSyncInterval)
}

// handleRealTimeUpdates processes real-time site updates via WebSocket
func (m *Monitor) handleRealTimeUpdates() {
	updateChan := m.client.GetUpdateChannel()

	for {
		select {
		case <-m.ctx.Done():
			return
		case sites, ok := <-updateChan:
			if !ok {
				log.Println("INFO: Update channel closed")
				return
			}
			log.Printf("INFO: Processing real-time site update: %d sites", len(sites))
			m.updateSites(sites)
		}
	}
}

// Start starts the monitoring system
func (m *Monitor) Start() error {
	log.Println("INFO: Starting SREoob monitoring agent")

	// Initial fetch and start monitoring
	if err := m.RefreshSites(m.ctx); err != nil {
		return fmt.Errorf("failed to start monitoring: %w", err)
	}

	// Start real-time update handler for WebSocket
	go m.handleRealTimeUpdates()

	// Fallback HTTP polling (in case WebSocket fails or is disabled)
	go func() {
		ticker := time.NewTicker(m.minSyncInterval)
		defer ticker.Stop()

		for {
			select {
			case <-m.ctx.Done():
				return
			case <-ticker.C:
				// Only use HTTP polling if WebSocket is not connected
				if !m.client.IsWebSocketConnected() {
					if err := m.RefreshSites(m.ctx); err != nil {
						log.Printf("ERROR: Failed to refresh sites via HTTP: %v", err)
					}
				}

				// Update ticker interval based on current sites
				ticker.Reset(m.minSyncInterval)
			}
		}
	}()

	return nil
}

// Stop stops the monitoring system
func (m *Monitor) Stop() {
	log.Println("INFO: Stopping monitoring agent")

	m.mu.Lock()
	defer m.mu.Unlock()

	// Cancel all monitoring tasks
	for siteID, cancelFunc := range m.tasks {
		cancelFunc()
		delete(m.tasks, siteID)
	}

	m.cancel()
	log.Println("INFO: Monitoring agent stopped")
}

// isWindows checks if the current OS is Windows
func isWindows() bool {
	return strings.Contains(strings.ToLower(os.Getenv("OS")), "windows")
}
