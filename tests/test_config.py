"""Tests for configuration module."""

import pytest
from pydantic import ValidationError

from reddit_mcp.config import RedditMCPConfig


def test_config_validation():
    """Test configuration validation."""
    # Valid configuration
    config = RedditMCPConfig(
        reddit_client_id="test_id",
        reddit_client_secret="test_secret",
        reddit_user_agent="TestApp/1.0 by TestUser"
    )
    assert config.reddit_client_id == "test_id"
    assert config.log_level == "INFO"

def test_invalid_user_agent():
    """Test invalid user agent validation."""
    with pytest.raises(ValidationError):
        RedditMCPConfig(
            reddit_client_id="test_id",
            reddit_client_secret="test_secret",
            reddit_user_agent="short"
        )

def test_invalid_log_level():
    """Test invalid log level validation."""
    with pytest.raises(ValidationError):
        RedditMCPConfig(
            reddit_client_id="test_id",
            reddit_client_secret="test_secret",
            reddit_user_agent="TestApp/1.0 by TestUser",
            log_level="INVALID"
        )
