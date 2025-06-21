package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func main() {
	// Load configuration
	config, err := LoadConfig()
	if err != nil {
		log.Fatalf("FATAL: Configuration error: %v", err)
	}

	// Validate configuration
	if err := config.Validate(); err != nil {
		log.Fatalf("FATAL: Configuration validation failed: %v", err)
	}

	log.Printf("INFO: SiteUp Agent starting")
	log.Printf("INFO: Agent ID: %s", config.AgentID)
	log.Printf("INFO: Hostname: %s", config.Hostname)
	log.Printf("INFO: Master FQDN: %s", config.MasterFQDN)
	log.Printf("INFO: Agent Server Port: %s", config.AgentServerPort)
	log.Printf("INFO: Local Agent Port: %s", config.AgentPort)

	if config.UseWebSocket {
		log.Println("INFO: WebSocket enabled - will try WSS → HTTP/2 → HTTP/1.1 fallback")
	} else {
		log.Println("INFO: WebSocket disabled - will use HTTP/2 → HTTP/1.1 fallback")
	}

	// Create master API client
	client := NewMasterClient(config)
	defer client.Close() // Ensure cleanup

	// Test connection to master with protocol fallback
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	if err := client.TestConnection(ctx); err != nil {
		cancel()
		log.Fatalf("FATAL: Failed to connect to master at %s: %v", config.MasterFQDN, err)
	}
	cancel()

	log.Printf("INFO: Successfully connected to master using %s", client.GetProtocol())
	if client.IsWebSocketConnected() {
		log.Println("INFO: WebSocket connection established for real-time updates")
	} else {
		log.Printf("INFO: Using HTTP polling with %s protocol", client.GetProtocol())
	}

	// Create and start monitor
	monitor := NewMonitor(client)

	if err := monitor.Start(); err != nil {
		log.Fatalf("FATAL: Failed to start monitoring: %v", err)
	}

	// Setup graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// Wait for shutdown signal
	<-sigChan
	log.Println("INFO: Shutdown signal received")

	// Stop monitoring
	monitor.Stop()

	log.Println("INFO: SiteUp Agent shutdown complete")
}
