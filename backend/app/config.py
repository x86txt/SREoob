from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    # Path for the SQLite database
    DATABASE_PATH: str = "siteup.db"
    
    # Scan interval settings
    MIN_SCAN_INTERVAL_SECONDS: int = 30
    MAX_SCAN_INTERVAL_SECONDS: int = 3600
    DEVELOPMENT_MODE: bool = False
    
    # Logging level
    LOG_LEVEL: str = "INFO"

    # Optional Admin API Key Hash for authentication
    ADMIN_API_KEY_HASH: str | None = None
    
    # Optional Agent API Key Hash for agent authentication
    AGENT_API_KEY_HASH: str | None = None
    
    # Agent communication port
    AGENT_PORT: int = 5227

    model_config = SettingsConfigDict(
        env_file='../.env', 
        env_file_encoding='utf-8', 
        case_sensitive=False,
        extra='ignore'  # Ignore extra fields from .env file
    )

    @property
    def scan_interval_range_description(self) -> str:
        """Returns a human-readable description of the scan interval range."""
        def format_time(seconds: int) -> str:
            if seconds < 60:
                return f"{seconds}s"
            if seconds < 3600:
                return f"{seconds // 60}m"
            return f"{seconds // 3600}h"
        
        min_val = self.MIN_SCAN_INTERVAL_SECONDS
        max_val = self.MAX_SCAN_INTERVAL_SECONDS
        return f"{format_time(min_val)}-{format_time(max_val)}"

# Create a single, global instance of the settings
settings = Settings()

# Function to get the settings instance, for FastAPI dependency injection
def get_settings() -> Settings:
    return settings 