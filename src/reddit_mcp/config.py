"""
Configuration management for Reddit MCP Server.

Uses Pydantic Settings for modern, type-safe configuration management
with automatic environment variable loading and validation.
"""

import os
from typing import Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class RedditMCPConfig(BaseSettings):
    """Configuration settings for Reddit MCP Server."""

    # Reddit API Configuration
    reddit_client_id: str = Field(
        ...,
        description="Reddit API client ID",
        env="REDDIT_CLIENT_ID",
    )
    reddit_client_secret: str = Field(
        ...,
        description="Reddit API client secret",
        env="REDDIT_CLIENT_SECRET",
    )
    reddit_user_agent: str = Field(
        ...,
        description="Reddit API user agent string",
        env="REDDIT_USER_AGENT",
    )
    reddit_username: Optional[str] = Field(
        None,
        description="Reddit username for authenticated requests (optional)",
        env="REDDIT_USERNAME",
    )
    reddit_password: Optional[str] = Field(
        None,
        description="Reddit password for authenticated requests (optional)",
        env="REDDIT_PASSWORD",
    )

    # Server Configuration
    log_level: str = Field(
        "INFO",
        description="Logging level",
        env="LOG_LEVEL",
    )
    max_retries: int = Field(
        3,
        description="Maximum number of API request retries",
        env="MAX_RETRIES",
    )
    request_timeout: int = Field(
        30,
        description="Request timeout in seconds",
        env="REQUEST_TIMEOUT",
    )

    # Cache Configuration
    cache_ttl: int = Field(
        300,  # 5 minutes
        description="Cache time-to-live in seconds",
        env="CACHE_TTL",
    )
    cache_max_size: int = Field(
        1000,
        description="Maximum number of cached items",
        env="CACHE_MAX_SIZE",
    )

    # Rate Limiting Configuration
    rate_limit_requests: int = Field(
        60,
        description="Maximum requests per minute",
        env="RATE_LIMIT_REQUESTS",
    )
    rate_limit_window: int = Field(
        60,
        description="Rate limiting time window in seconds",
        env="RATE_LIMIT_WINDOW",
    )

    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    @validator("reddit_user_agent")
    def validate_user_agent(cls, v: str) -> str:
        """Validate Reddit user agent format."""
        if not v or len(v.strip()) < 10:
            raise ValueError(
                "User agent must be at least 10 characters and descriptive. "
                "Format: 'AppName/Version by YourUsername'"
            )
        return v

    @validator("max_retries")
    def validate_max_retries(cls, v: int) -> int:
        """Validate max retries."""
        if v < 0 or v > 10:
            raise ValueError("Max retries must be between 0 and 10")
        return v

    @validator("request_timeout")
    def validate_request_timeout(cls, v: int) -> int:
        """Validate request timeout."""
        if v < 1 or v > 300:
            raise ValueError("Request timeout must be between 1 and 300 seconds")
        return v

    @validator("cache_ttl")
    def validate_cache_ttl(cls, v: int) -> int:
        """Validate cache TTL."""
        if v < 0 or v > 3600:
            raise ValueError("Cache TTL must be between 0 and 3600 seconds")
        return v

    @validator("rate_limit_requests")
    def validate_rate_limit_requests(cls, v: int) -> int:
        """Validate rate limit requests."""
        if v < 1 or v > 1000:
            raise ValueError("Rate limit requests must be between 1 and 1000")
        return v

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True


def get_config() -> RedditMCPConfig:
    """Get configuration instance."""
    return RedditMCPConfig()
