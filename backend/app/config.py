"""Application configuration using Pydantic settings."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="Game Time", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    secret_key: str = Field(
        default="change-this-to-a-random-secret-key",
        description="Secret key for signing",
    )
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        description="Comma-separated list of allowed CORS origins",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://gametime_user:gametime_pass@localhost:5432/gametime",
        description="Database connection URL",
    )
    database_pool_size: int = Field(default=20, description="Database pool size")
    database_max_overflow: int = Field(default=10, description="Max overflow connections")

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    redis_max_connections: int = Field(default=50, description="Max Redis connections")

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")  # nosec B104
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=False, description="Auto-reload on code changes")

    # Security
    session_expire_hours: int = Field(default=24, description="Session expiry in hours")
    room_code_length: int = Field(default=4, description="Room code length")
    room_timeout_hours: int = Field(default=1, description="Room inactivity timeout")

    # Rate Limiting
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_room_creation: int = Field(default=5, description="Room creation per hour per IP")
    rate_limit_api_requests: int = Field(default=100, description="API requests per minute per IP")
    rate_limit_ws_messages: int = Field(
        default=60, description="WS messages per minute per connection"
    )

    # Game Settings
    max_players_per_room: int = Field(default=12, description="Maximum players per room")
    min_players_per_room: int = Field(default=2, description="Minimum players per room")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")

    # Monitoring
    sentry_dsn: str | None = Field(default=None, description="Sentry DSN for error tracking")
    prometheus_port: int = Field(default=9090, description="Prometheus metrics port")

    # Testing
    testing: bool = Field(default=False, description="Testing mode")

    @field_validator("room_code_length")
    @classmethod
    def validate_room_code_length(cls, v: int) -> int:
        """Validate room code length is between 4 and 6."""
        if not 4 <= v <= 6:
            raise ValueError("room_code_length must be between 4 and 6")
        return v

    @field_validator("max_players_per_room")
    @classmethod
    def validate_max_players(cls, v: int) -> int:
        """Validate max players is reasonable."""
        if not 2 <= v <= 20:
            raise ValueError("max_players_per_room must be between 2 and 20")
        return v

    @property
    def cors_origins(self) -> list[str]:
        """Parse allowed origins from comma-separated string."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]


# Global settings instance
settings = Settings()
