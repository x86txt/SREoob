package main

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"runtime"
	"strings"
	"syscall"
	"time"
)

// Version information (set by build flags)
var (
	Version   = "dev"
	BuildTime = "unknown"
	GitCommit = "unknown"
)

// getGoVersion returns the Go version used to build the binary
func getGoVersion() string {
	return runtime.Version()
}

// generateAPIKey generates a secure 64-character API key
func generateAPIKey() (string, error) {
	bytes := make([]byte, 32) // 32 bytes = 64 hex characters
	if _, err := rand.Read(bytes); err != nil {
		return "", fmt.Errorf("failed to generate random bytes: %w", err)
	}
	return hex.EncodeToString(bytes), nil
}

// generateSHA256Hash generates a SHA-256 hash for the given API key
func generateSHA256Hash(apiKey string) string {
	hash := sha256.Sum256([]byte(apiKey))
	return hex.EncodeToString(hash[:])
}

func main() {
	// Parse command line flags
	var genKey = flag.Bool("genkey", false, "Generate a new API key and SHA-256 hash")
	var showVersion = flag.Bool("version", false, "Show version information")
	flag.Parse()

	// Handle version display
	if *showVersion {
		fmt.Printf("SREoob Agent %s\n", Version)
		fmt.Printf("Build Time: %s\n", BuildTime)
		fmt.Printf("Git Commit: %s\n", GitCommit)
		fmt.Printf("Go Version: %s\n", getGoVersion())
		return
	}

	// Handle key generation
	if *genKey {
		fmt.Println("Generating new API key and SHA-256 hash...")
		fmt.Println(strings.Repeat("=", 50))

		apiKey, err := generateAPIKey()
		if err != nil {
			log.Fatalf("FATAL: Failed to generate API key: %v", err)
		}

		hash := generateSHA256Hash(apiKey)

		fmt.Printf("Generated API Key (64 characters):\n")
		fmt.Printf("AGENT_API_KEY=%s\n\n", apiKey)

		fmt.Printf("Generated SHA-256 Hash (for server .env file):\n")
		fmt.Printf("AGENT_API_KEY_HASH=%s\n\n", hash)

		fmt.Println("Instructions:")
		fmt.Println("1. Copy the AGENT_API_KEY to your agent's .env file")
		fmt.Println("2. Copy the AGENT_API_KEY_HASH to your server's .env file")
		fmt.Println("3. Restart the server to load the new hash")
		fmt.Println("4. Start the agent with the new API key")

		return
	}

	// Normal agent operation starts here
	// Load configuration
	config, err := LoadConfig()
	if err != nil {
		log.Fatalf("FATAL: Configuration error: %v", err)
	}

	// Validate configuration
	if err := config.Validate(); err != nil {
		log.Fatalf("FATAL: Configuration validation failed: %v", err)
	}

	log.Printf("INFO: SREoob Agent v%s starting", Version)
	log.Printf("INFO: Build: %s (%s)", BuildTime, GitCommit)
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

	log.Println("INFO: SREoob Agent shutdown complete")
}
