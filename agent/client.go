package main

import (
	"bytes"
	"context"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	"golang.org/x/net/http2"
)

// MasterClient handles communication with the master SiteUp API
type MasterClient struct {
	config      *Config
	client      *http.Client
	http2Client *http.Client
	wsConn      *websocket.Conn
	wsMutex     sync.RWMutex
	wsConnected bool
	updateChan  chan []Site
	protocol    string // "wss", "http2", or "http1.1"
}

// Site represents a site to monitor
type Site struct {
	ID           int    `json:"id"`
	URL          string `json:"url"`
	Name         string `json:"name"`
	ScanInterval string `json:"scan_interval"`
	CreatedAt    string `json:"created_at"`
}

// CheckResult represents the result of a site check
type CheckResult struct {
	SiteID       int      `json:"site_id"`
	Status       string   `json:"status"`
	ResponseTime *float64 `json:"response_time"`
	StatusCode   *int     `json:"status_code"`
	ErrorMessage *string  `json:"error_message"`
	CheckedAt    string   `json:"checked_at"`
}

// WebSocketMessage represents messages sent over WebSocket
type WebSocketMessage struct {
	Type string      `json:"type"`
	Data interface{} `json:"data,omitempty"`
}

// AgentRegistration represents agent registration data
type AgentRegistration struct {
	AgentID      string   `json:"agent_id"`
	Hostname     string   `json:"hostname"`
	Version      string   `json:"version"`
	Capabilities []string `json:"capabilities"`
}

// NewMasterClient creates a new master API client
func NewMasterClient(config *Config) *MasterClient {
	// Create HTTP/1.1 client
	http1Client := &http.Client{
		Timeout: 30 * time.Second,
		Transport: &http.Transport{
			MaxIdleConns:       10,
			IdleConnTimeout:    30 * time.Second,
			DisableCompression: false,
			DisableKeepAlives:  false,
			TLSClientConfig: &tls.Config{
				InsecureSkipVerify: true, // For development
			},
		},
	}

	// Create HTTP/2 client
	http2Transport := &http2.Transport{
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: true, // For development
		},
		AllowHTTP: true, // Allow HTTP/2 over plain HTTP
	}
	http2Client := &http.Client{
		Timeout:   30 * time.Second,
		Transport: http2Transport,
	}

	return &MasterClient{
		config:      config,
		client:      http1Client,
		http2Client: http2Client,
		updateChan:  make(chan []Site, 10), // Buffered channel for site updates
		protocol:    "unknown",
	}
}

// getAgentURL returns the agent server URL with proper port
func (c *MasterClient) getAgentURL(endpoint string, websocket bool) string {
	baseURL := c.config.MasterFQDN

	// Parse the base URL to add agent server port
	if u, err := url.Parse(baseURL); err == nil {
		// Always use the agent server port for agent communication
		if !strings.Contains(u.Host, ":") {
			u.Host = u.Host + ":" + c.config.AgentServerPort
		} else {
			// Replace existing port with agent server port
			parts := strings.Split(u.Host, ":")
			u.Host = parts[0] + ":" + c.config.AgentServerPort
		}
		baseURL = u.String()
	}

	if websocket {
		// Convert http(s) to ws(s)
		wsURL := strings.Replace(baseURL, "http://", "ws://", 1)
		wsURL = strings.Replace(wsURL, "https://", "wss://", 1)
		return wsURL + "/agent/ws?agent_id=" + url.QueryEscape(c.config.AgentID) + "&api_key=" + url.QueryEscape(c.config.APIKey)
	}

	return baseURL + endpoint
}

// tryConnectWebSocket attempts to establish a WebSocket connection (WSS first)
func (c *MasterClient) tryConnectWebSocket(ctx context.Context) error {
	if !c.config.UseWebSocket {
		return fmt.Errorf("WebSocket disabled in configuration")
	}

	wsURL := c.getAgentURL("", true)

	header := http.Header{}
	header.Set("User-Agent", c.config.UserAgent)
	header.Set("Authorization", "Bearer "+c.config.APIKey)
	header.Set("X-API-Key", c.config.APIKey)

	log.Printf("INFO: Attempting WebSocket connection: %s", wsURL)

	// Create dialer with TLS config for development
	dialer := websocket.DefaultDialer
	dialer.TLSClientConfig = &tls.Config{
		InsecureSkipVerify: true, // For development
	}

	conn, resp, err := dialer.Dial(wsURL, header)
	if err != nil {
		if resp != nil {
			body, _ := io.ReadAll(resp.Body)
			resp.Body.Close()
			return fmt.Errorf("WebSocket connection failed (HTTP %d): %s - %w", resp.StatusCode, string(body), err)
		}
		return fmt.Errorf("WebSocket connection failed: %w", err)
	}

	c.wsMutex.Lock()
	c.wsConn = conn
	c.wsConnected = true
	c.protocol = "wss"
	c.wsMutex.Unlock()

	log.Println("INFO: WebSocket connected successfully")

	// Start listening for messages
	go c.handleWebSocketMessages(ctx)

	return nil
}

// makeRequest makes an HTTP request with protocol fallback
func (c *MasterClient) makeRequest(ctx context.Context, method, endpoint string, body interface{}) (*http.Response, error) {
	url := c.getAgentURL(endpoint, false)

	var reqBody io.Reader
	if body != nil {
		jsonBody, err := json.Marshal(body)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal request body: %w", err)
		}
		reqBody = bytes.NewBuffer(jsonBody)
	}

	req, err := http.NewRequestWithContext(ctx, method, url, reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("User-Agent", c.config.UserAgent)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+c.config.APIKey)

	// Try HTTP/2 first, then fallback to HTTP/1.1
	var resp *http.Response

	// Try HTTP/2
	if c.protocol == "unknown" || c.protocol == "http2" {
		resp, err = c.http2Client.Do(req)
		if err == nil {
			c.protocol = "http2"
			log.Printf("DEBUG: Using HTTP/2 for %s %s", method, endpoint)
			return c.validateResponse(resp)
		}
		log.Printf("WARN: HTTP/2 failed for %s %s: %v, falling back to HTTP/1.1", method, endpoint, err)
	}

	// Fallback to HTTP/1.1
	resp, err = c.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("HTTP/1.1 request failed: %w", err)
	}

	c.protocol = "http1.1"
	log.Printf("DEBUG: Using HTTP/1.1 for %s %s", method, endpoint)
	return c.validateResponse(resp)
}

// validateResponse checks the HTTP response status
func (c *MasterClient) validateResponse(resp *http.Response) (*http.Response, error) {
	if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		return nil, fmt.Errorf("API request failed with status %d: %s", resp.StatusCode, string(body))
	}
	return resp, nil
}

// RegisterAgent registers this agent with the master server
func (c *MasterClient) RegisterAgent(ctx context.Context) error {
	registration := AgentRegistration{
		AgentID:      c.config.AgentID,
		Hostname:     c.config.Hostname,
		Version:      "1.0",
		Capabilities: []string{"http", "ping"},
	}

	resp, err := c.makeRequest(ctx, "POST", "/agent/register", registration)
	if err != nil {
		return fmt.Errorf("failed to register agent: %w", err)
	}
	defer resp.Body.Close()

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return fmt.Errorf("failed to decode registration response: %w", err)
	}

	log.Printf("INFO: Agent registered successfully: %s", result["message"])
	return nil
}

// GetSites fetches all sites from the master
func (c *MasterClient) GetSites(ctx context.Context) ([]Site, error) {
	resp, err := c.makeRequest(ctx, "GET", "/agent/sites", nil)
	if err != nil {
		return nil, fmt.Errorf("failed to get sites: %w", err)
	}
	defer resp.Body.Close()

	var sites []Site
	if err := json.NewDecoder(resp.Body).Decode(&sites); err != nil {
		return nil, fmt.Errorf("failed to decode sites response: %w", err)
	}

	return sites, nil
}

// SubmitCheckResult submits a check result to the master
func (c *MasterClient) SubmitCheckResult(ctx context.Context, result CheckResult) error {
	// Try WebSocket first if available
	if c.IsWebSocketConnected() {
		msg := WebSocketMessage{
			Type: "check_result",
			Data: result,
		}
		if err := c.sendWebSocketMessage(msg); err == nil {
			return nil
		}
		log.Printf("WARN: WebSocket submit failed, falling back to HTTP")
	}

	// Fallback to HTTP
	resp, err := c.makeRequest(ctx, "POST", "/agent/checks", []CheckResult{result})
	if err != nil {
		return fmt.Errorf("failed to submit check result: %w", err)
	}
	defer resp.Body.Close()

	return nil
}

// TestConnection tests the connection to the master with protocol fallback
func (c *MasterClient) TestConnection(ctx context.Context) error {
	// First, try to register the agent
	if err := c.RegisterAgent(ctx); err != nil {
		return fmt.Errorf("agent registration failed: %w", err)
	}

	// Test getting sites
	_, err := c.GetSites(ctx)
	if err != nil {
		return fmt.Errorf("failed to fetch sites: %w", err)
	}

	log.Printf("INFO: HTTP connection established using %s", c.protocol)

	// Try WebSocket connection if enabled
	if c.config.UseWebSocket {
		wsCtx, cancel := context.WithTimeout(ctx, 10*time.Second)
		defer cancel()

		if err := c.tryConnectWebSocket(wsCtx); err != nil {
			log.Printf("WARN: WebSocket connection failed, will use HTTP polling: %v", err)
		}
	}

	return nil
}

// handleWebSocketMessages processes incoming WebSocket messages
func (c *MasterClient) handleWebSocketMessages(ctx context.Context) {
	defer func() {
		c.wsMutex.Lock()
		if c.wsConn != nil {
			c.wsConn.Close()
			c.wsConn = nil
		}
		c.wsConnected = false
		c.wsMutex.Unlock()
	}()

	for {
		select {
		case <-ctx.Done():
			return
		default:
			c.wsMutex.RLock()
			conn := c.wsConn
			c.wsMutex.RUnlock()

			if conn == nil {
				return
			}

			var msg WebSocketMessage
			if err := conn.ReadJSON(&msg); err != nil {
				log.Printf("ERROR: WebSocket read error: %v", err)
				return
			}

			switch msg.Type {
			case "sites_updated":
				if sitesData, ok := msg.Data.([]interface{}); ok {
					var sites []Site
					// Convert interface{} to []Site
					jsonData, _ := json.Marshal(sitesData)
					if err := json.Unmarshal(jsonData, &sites); err == nil {
						select {
						case c.updateChan <- sites:
							log.Printf("INFO: Received site update via WebSocket: %d sites", len(sites))
						default:
							log.Println("WARN: Update channel full, dropping site update")
						}
					}
				}
			case "ping":
				// Respond to ping
				c.sendWebSocketMessage(WebSocketMessage{Type: "pong"})
			case "check_result_ack":
				// Acknowledgment for submitted check result
				log.Printf("DEBUG: Check result acknowledged: %v", msg.Data)
			default:
				log.Printf("INFO: Unknown WebSocket message type: %s", msg.Type)
			}
		}
	}
}

// sendWebSocketMessage sends a message via WebSocket
func (c *MasterClient) sendWebSocketMessage(msg WebSocketMessage) error {
	c.wsMutex.RLock()
	conn := c.wsConn
	connected := c.wsConnected
	c.wsMutex.RUnlock()

	if !connected || conn == nil {
		return fmt.Errorf("WebSocket not connected")
	}

	return conn.WriteJSON(msg)
}

// GetUpdateChannel returns the channel for receiving real-time site updates
func (c *MasterClient) GetUpdateChannel() <-chan []Site {
	return c.updateChan
}

// IsWebSocketConnected returns whether WebSocket is connected
func (c *MasterClient) IsWebSocketConnected() bool {
	c.wsMutex.RLock()
	defer c.wsMutex.RUnlock()
	return c.wsConnected
}

// GetProtocol returns the current communication protocol being used
func (c *MasterClient) GetProtocol() string {
	return c.protocol
}

// Close cleans up the client connections
func (c *MasterClient) Close() {
	c.wsMutex.Lock()
	defer c.wsMutex.Unlock()

	if c.wsConn != nil {
		c.wsConn.Close()
		c.wsConn = nil
	}
	c.wsConnected = false
	close(c.updateChan)
}
