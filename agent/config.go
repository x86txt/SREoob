package main

import (
	"fmt"
	"os"
	"strings"
)

// Config holds the agent configuration
type Config struct {
	MasterFQDN      string
	APIKey          string
	AgentPort       string
	AgentServerPort string // New dedicated agent server port
	UserAgent       string
	LogLevel        string
	UseWebSocket    bool
	AgentID         string
	Hostname        string
}

// LoadConfig loads configuration from environment variables
func LoadConfig() (*Config, error) {
	hostname, _ := os.Hostname()
	if hostname == "" {
		hostname = "unknown"
	}

	config := &Config{
		UserAgent:       "SiteUp-Agent/1.0",
		LogLevel:        "info",
		AgentPort:       "8081", // Default agent port for local health checks
		AgentServerPort: "5227", // New dedicated agent communication port
		UseWebSocket:    true,   // Default to WebSocket for better performance
		Hostname:        hostname,
	}

	// Required: Master FQDN
	masterFQDN := os.Getenv("MASTER_FQDN")
	if masterFQDN == "" {
		return nil, fmt.Errorf("MASTER_FQDN environment variable is required")
	}

	// Ensure the FQDN has a protocol
	if !strings.HasPrefix(masterFQDN, "http://") && !strings.HasPrefix(masterFQDN, "https://") {
		masterFQDN = "https://" + masterFQDN
	}
	config.MasterFQDN = strings.TrimSuffix(masterFQDN, "/")

	// Required: API Key (now for agent authentication)
	apiKey := os.Getenv("AGENT_API_KEY")
	if apiKey == "" {
		// Fallback to old API_KEY for backward compatibility
		apiKey = os.Getenv("API_KEY")
	}
	if apiKey == "" {
		return nil, fmt.Errorf("AGENT_API_KEY environment variable is required")
	}
	if len(apiKey) < 64 {
		return nil, fmt.Errorf("AGENT_API_KEY must be at least 64 characters long for security")
	}
	config.APIKey = apiKey

	// Optional: Agent ID (defaults to hostname)
	if agentID := os.Getenv("AGENT_ID"); agentID != "" {
		config.AgentID = agentID
	} else {
		config.AgentID = hostname
	}

	// Optional: Agent server port
	if agentServerPort := os.Getenv("AGENT_SERVER_PORT"); agentServerPort != "" {
		config.AgentServerPort = agentServerPort
	}

	// Optional: Agent port (for local health checks)
	if agentPort := os.Getenv("AGENT_PORT"); agentPort != "" {
		config.AgentPort = agentPort
	}

	// Optional: Log level
	if logLevel := os.Getenv("LOG_LEVEL"); logLevel != "" {
		config.LogLevel = strings.ToLower(logLevel)
	}

	// Optional: Disable WebSocket (default is enabled)
	if useWS := os.Getenv("USE_WEBSOCKET"); useWS != "" {
		config.UseWebSocket = strings.ToLower(useWS) != "false"
	}

	return config, nil
}

// Validate validates the configuration
func (c *Config) Validate() error {
	if c.MasterFQDN == "" {
		return fmt.Errorf("master FQDN is required")
	}
	if c.APIKey == "" {
		return fmt.Errorf("API key is required")
	}
	if c.AgentID == "" {
		return fmt.Errorf("agent ID is required")
	}
	return nil
}
