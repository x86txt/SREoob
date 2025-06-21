package main

import (
	"context"
	"flag"
	"fmt"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/go-ping/ping"
)

type PingResult struct {
	Timestamp   time.Time
	Host        string
	PacketsSent int
	PacketsRecv int
	PacketLoss  float64
	MinRtt      time.Duration
	MaxRtt      time.Duration
	AvgRtt      time.Duration
	StdDevRtt   time.Duration
	Error       error
}

func main() {
	var (
		host     = flag.String("host", "", "Host to ping (required)")
		interval = flag.Duration("interval", 1*time.Second, "Ping interval (e.g., 1s, 500ms, 2s)")
		timeout  = flag.Duration("timeout", 3*time.Second, "Ping timeout (e.g., 3s, 5s)")
		count    = flag.Int("count", 0, "Number of pings (0 for infinite)")
		size     = flag.Int("size", 56, "Packet size in bytes")
		useIPv6  = flag.Bool("6", false, "Use IPv6")
		useUDP   = flag.Bool("udp", false, "Use UDP instead of ICMP (doesn't require root)")
	)
	flag.Parse()

	if *host == "" {
		fmt.Fprintf(os.Stderr, "Error: Host is required\n")
		flag.Usage()
		os.Exit(1)
	}

	// Resolve host
	resolvedHost, err := resolveHost(*host, *useIPv6)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error resolving host %s: %v\n", *host, err)
		os.Exit(1)
	}

	pingType := "ICMP"
	if *useUDP {
		pingType = "UDP"
	}

	fmt.Printf("PING %s (%s): %d data bytes, %s\n", *host, resolvedHost, *size, pingType)
	fmt.Printf("Interval: %v, Timeout: %v\n", *interval, *timeout)
	fmt.Println("Press Ctrl+C to stop")
	fmt.Println()

	// Setup graceful shutdown
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigChan
		fmt.Println("\nShutting down...")
		cancel()
	}()

	// Statistics tracking
	var stats struct {
		total       int
		success     int
		failed      int
		totalTime   time.Duration
		minTime     time.Duration
		maxTime     time.Duration
		packetsSent int
		packetsRecv int
	}
	stats.minTime = time.Hour // Initialize to a large value

	ticker := time.NewTicker(*interval)
	defer ticker.Stop()

	pingCount := 0
	for {
		select {
		case <-ctx.Done():
			goto cleanup
		case <-ticker.C:
			if *count > 0 && pingCount >= *count {
				goto cleanup
			}

			result := performPing(resolvedHost, *timeout, *size, *useUDP)
			displayResult(result, pingCount)
			updateStats(&stats, result)
			pingCount++
		}
	}

cleanup:
	fmt.Println()
	displayStats(stats, *host)
}

func resolveHost(host string, useIPv6 bool) (string, error) {
	network := "ip4"
	if useIPv6 {
		network = "ip6"
	}

	addr, err := net.ResolveIPAddr(network, host)
	if err != nil {
		return "", err
	}
	return addr.String(), nil
}

func performPing(host string, timeout time.Duration, size int, useUDP bool) PingResult {
	start := time.Now()

	pinger, err := ping.NewPinger(host)
	if err != nil {
		return PingResult{
			Timestamp: start,
			Host:      host,
			Error:     err,
		}
	}

	// Configure pinger
	pinger.Count = 1
	pinger.Timeout = timeout
	pinger.Size = size

	if useUDP {
		pinger.SetPrivileged(false)
	} else {
		// ICMP requires privileged mode on most systems
		pinger.SetPrivileged(true)
	}

	// Run the ping
	err = pinger.Run()

	result := PingResult{
		Timestamp:   start,
		Host:        host,
		PacketsSent: pinger.PacketsSent,
		PacketsRecv: pinger.PacketsRecv,
		Error:       err,
	}

	if err == nil && len(pinger.Statistics().Rtts) > 0 {
		stats := pinger.Statistics()
		result.PacketLoss = stats.PacketLoss
		result.MinRtt = stats.MinRtt
		result.MaxRtt = stats.MaxRtt
		result.AvgRtt = stats.AvgRtt
		result.StdDevRtt = stats.StdDevRtt
	}

	return result
}

func displayResult(result PingResult, seq int) {
	timestamp := result.Timestamp.Format("15:04:05.000")

	if result.Error != nil {
		fmt.Printf("[%s] seq=%d ERROR: %v\n", timestamp, seq, result.Error)
		return
	}

	if result.PacketsRecv == 0 {
		fmt.Printf("[%s] seq=%d timeout (no reply)\n", timestamp, seq)
		return
	}

	fmt.Printf("[%s] seq=%d time=%v\n", timestamp, seq, result.AvgRtt)
}

func updateStats(stats *struct {
	total       int
	success     int
	failed      int
	totalTime   time.Duration
	minTime     time.Duration
	maxTime     time.Duration
	packetsSent int
	packetsRecv int
}, result PingResult) {
	stats.total++
	stats.packetsSent += result.PacketsSent
	stats.packetsRecv += result.PacketsRecv

	if result.Error != nil || result.PacketsRecv == 0 {
		stats.failed++
	} else {
		stats.success++
		rtt := result.AvgRtt
		stats.totalTime += rtt

		if rtt < stats.minTime {
			stats.minTime = rtt
		}
		if rtt > stats.maxTime {
			stats.maxTime = rtt
		}
	}
}

func displayStats(stats struct {
	total       int
	success     int
	failed      int
	totalTime   time.Duration
	minTime     time.Duration
	maxTime     time.Duration
	packetsSent int
	packetsRecv int
}, host string) {
	if stats.total == 0 {
		return
	}

	fmt.Printf("--- %s ping statistics ---\n", host)
	fmt.Printf("%d packets transmitted, %d packets received, %.1f%% packet loss\n",
		stats.packetsSent, stats.packetsRecv,
		float64(stats.packetsSent-stats.packetsRecv)/float64(stats.packetsSent)*100)

	if stats.success > 0 {
		avgTime := stats.totalTime / time.Duration(stats.success)
		fmt.Printf("round-trip min/avg/max = %v/%v/%v\n",
			stats.minTime, avgTime, stats.maxTime)
	}
}
