"""Tests for utility functions."""

import pytest

from reddit_mcp.utils import (
    extract_post_id,
    format_timestamp,
    validate_subreddit_name,
    validate_username,
    truncate_text,
)


def test_extract_post_id():
    """Test post ID extraction from various formats."""
    # Direct ID
    assert extract_post_id("abc123") == "abc123"
    
    # Standard Reddit URL
    assert extract_post_id("https://reddit.com/r/test/comments/abc123/title/") == "abc123"
    
    # Shortened URL
    assert extract_post_id("https://redd.it/abc123") == "abc123"


def test_validate_subreddit_name():
    """Test subreddit name validation."""
    # Valid names
    assert validate_subreddit_name("python") == "python"
    assert validate_subreddit_name("r/python") == "python"
    assert validate_subreddit_name("test_sub") == "test_sub"
    
    # Invalid names
    with pytest.raises(ValueError):
        validate_subreddit_name("")
    
    with pytest.raises(ValueError):
        validate_subreddit_name("invalid-chars!")


def test_validate_username():
    """Test username validation."""
    # Valid usernames
    assert validate_username("testuser") == "testuser"
    assert validate_username("u/testuser") == "testuser"
    assert validate_username("test_user-123") == "test_user-123"
    
    # Invalid usernames
    with pytest.raises(ValueError):
        validate_username("")
    
    with pytest.raises(ValueError):
        validate_username("ab")  # Too short


def test_format_timestamp():
    """Test timestamp formatting."""
    # Valid timestamp
    result = format_timestamp(1640995200)  # 2022-01-01 00:00:00
    assert result is not None
    assert "2022" in result
    
    # Invalid timestamp
    assert format_timestamp(None) is None
    assert format_timestamp("invalid") is None


def test_truncate_text():
    """Test text truncation."""
    # Short text
    assert truncate_text("short", 100) == "short"
    
    # Long text
    long_text = "a" * 1000
    result = truncate_text(long_text, 100)
    assert len(result) == 100
    assert result.endswith("...")
    
    # Empty text
    assert truncate_text("", 100) == ""
