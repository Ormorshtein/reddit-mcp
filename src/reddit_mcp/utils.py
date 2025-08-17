"""
Utility functions and helpers for Reddit MCP Server.

Provides data formatting, logging setup, and common helper functions.
"""

import logging
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import praw
from praw.models import Comment, Redditor, Submission, Subreddit


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Set up logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("reddit_mcp")
    logger.setLevel(getattr(logging, level.upper()))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Create console handler - use stderr for MCP servers to avoid interfering with stdout
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(getattr(logging, level.upper()))

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger


def safe_getattr(obj: Any, attr: str, default: Any = None) -> Any:
    """
    Safely get attribute from object, handling AttributeError and None values.

    Args:
        obj: Object to get attribute from
        attr: Attribute name
        default: Default value if attribute doesn't exist or is None

    Returns:
        Attribute value or default
    """
    try:
        value = getattr(obj, attr, default)
        return value if value is not None else default
    except (AttributeError, TypeError):
        return default


def format_timestamp(timestamp: Union[float, int, None]) -> Optional[str]:
    """
    Format Unix timestamp to ISO 8601 string.

    Args:
        timestamp: Unix timestamp

    Returns:
        ISO 8601 formatted datetime string or None
    """
    if timestamp is None:
        return None
    try:
        return datetime.fromtimestamp(timestamp).isoformat()
    except (ValueError, TypeError, OSError):
        return None


def format_post_data(post: Submission) -> Dict[str, Any]:
    """
    Format Reddit post data into standardized dictionary.

    Args:
        post: PRAW Submission object

    Returns:
        Formatted post data dictionary
    """
    return {
        "id": safe_getattr(post, "id"),
        "title": safe_getattr(post, "title"),
        "author": safe_getattr(post, "author", {}).name if post.author else "[deleted]",
        "subreddit": safe_getattr(post, "subreddit", {}).display_name,
        "created_utc": format_timestamp(safe_getattr(post, "created_utc")),
        "score": safe_getattr(post, "score", 0),
        "upvote_ratio": safe_getattr(post, "upvote_ratio"),
        "num_comments": safe_getattr(post, "num_comments", 0),
        "url": safe_getattr(post, "url"),
        "permalink": f"https://reddit.com{safe_getattr(post, 'permalink', '')}",
        "selftext": safe_getattr(post, "selftext", "")[:1000],  # Limit text length
        "is_self": safe_getattr(post, "is_self", False),
        "is_video": safe_getattr(post, "is_video", False),
        "over_18": safe_getattr(post, "over_18", False),
        "spoiler": safe_getattr(post, "spoiler", False),
        "stickied": safe_getattr(post, "stickied", False),
        "locked": safe_getattr(post, "locked", False),
        "flair_text": safe_getattr(post, "link_flair_text"),
        "gilded": safe_getattr(post, "gilded", 0),
        "awards_received": safe_getattr(post, "total_awards_received", 0),
    }


def format_comment_data(comment: Comment, depth: int = 0) -> Dict[str, Any]:
    """
    Format Reddit comment data into standardized dictionary.

    Args:
        comment: PRAW Comment object
        depth: Comment nesting depth

    Returns:
        Formatted comment data dictionary
    """
    return {
        "id": safe_getattr(comment, "id"),
        "author": safe_getattr(comment, "author", {}).name if comment.author else "[deleted]",
        "body": safe_getattr(comment, "body", "")[:1000],  # Limit text length
        "created_utc": format_timestamp(safe_getattr(comment, "created_utc")),
        "score": safe_getattr(comment, "score", 0),
        "is_submitter": safe_getattr(comment, "is_submitter", False),
        "stickied": safe_getattr(comment, "stickied", False),
        "gilded": safe_getattr(comment, "gilded", 0),
        "awards_received": safe_getattr(comment, "total_awards_received", 0),
        "depth": depth,
        "permalink": f"https://reddit.com{safe_getattr(comment, 'permalink', '')}",
        "parent_id": safe_getattr(comment, "parent_id"),
        "replies_count": len(safe_getattr(comment, "replies", [])),
    }


def format_user_data(user: Redditor) -> Dict[str, Any]:
    """
    Format Reddit user data into standardized dictionary.

    Args:
        user: PRAW Redditor object

    Returns:
        Formatted user data dictionary
    """
    return {
        "username": safe_getattr(user, "name"),
        "id": safe_getattr(user, "id"),
        "created_utc": format_timestamp(safe_getattr(user, "created_utc")),
        "comment_karma": safe_getattr(user, "comment_karma", 0),
        "link_karma": safe_getattr(user, "link_karma", 0),
        "total_karma": safe_getattr(user, "total_karma", 0),
        "is_employee": safe_getattr(user, "is_employee", False),
        "is_mod": safe_getattr(user, "is_mod", False),
        "is_gold": safe_getattr(user, "is_gold", False),
        "verified": safe_getattr(user, "verified", False),
        "has_verified_email": safe_getattr(user, "has_verified_email", False),
        "icon_img": safe_getattr(user, "icon_img"),
        "subreddit": {
            "display_name": safe_getattr(user, "subreddit", {}).display_name
            if hasattr(user, "subreddit") and user.subreddit
            else None,
            "subscribers": safe_getattr(user, "subreddit", {}).subscribers
            if hasattr(user, "subreddit") and user.subreddit
            else 0,
        },
    }


def format_subreddit_data(subreddit: Subreddit) -> Dict[str, Any]:
    """
    Format Reddit subreddit data into standardized dictionary.

    Args:
        subreddit: PRAW Subreddit object

    Returns:
        Formatted subreddit data dictionary
    """
    return {
        "name": safe_getattr(subreddit, "display_name"),
        "id": safe_getattr(subreddit, "id"),
        "title": safe_getattr(subreddit, "title"),
        "description": safe_getattr(subreddit, "public_description", "")[:500],
        "subscribers": safe_getattr(subreddit, "subscribers", 0),
        "active_users": safe_getattr(subreddit, "active_user_count", 0),
        "created_utc": format_timestamp(safe_getattr(subreddit, "created_utc")),
        "over18": safe_getattr(subreddit, "over18", False),
        "lang": safe_getattr(subreddit, "lang"),
        "url": f"https://reddit.com/r/{safe_getattr(subreddit, 'display_name', '')}",
        "icon_url": safe_getattr(subreddit, "icon_img"),
        "banner_url": safe_getattr(subreddit, "banner_img"),
    }


def extract_post_id(url_or_id: str) -> str:
    """
    Extract Reddit post ID from URL or return ID if already provided.

    Args:
        url_or_id: Reddit post URL or ID

    Returns:
        Reddit post ID

    Raises:
        ValueError: If unable to extract valid post ID
    """
    # If it's already just an ID (alphanumeric, 6-7 characters)
    if url_or_id.isalnum() and 6 <= len(url_or_id) <= 7:
        return url_or_id

    # Extract from various Reddit URL formats
    import re

    patterns = [
        r"/comments/([a-zA-Z0-9]{6,7})/",  # Standard Reddit URL
        r"/r/\w+/comments/([a-zA-Z0-9]{6,7})/",  # Subreddit URL
        r"reddit\.com/.*?/([a-zA-Z0-9]{6,7})/?",  # General Reddit URL
        r"redd\.it/([a-zA-Z0-9]{6,7})",  # Shortened URL
    ]

    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    # If no pattern matches, assume it's already an ID
    cleaned_id = re.sub(r"[^a-zA-Z0-9]", "", url_or_id)
    if 6 <= len(cleaned_id) <= 7:
        return cleaned_id

    raise ValueError(f"Unable to extract valid post ID from: {url_or_id}")


def truncate_text(text: str, max_length: int = 1000) -> str:
    """
    Truncate text to maximum length with ellipsis.

    Args:
        text: Text to truncate
        max_length: Maximum allowed length

    Returns:
        Truncated text with ellipsis if needed
    """
    if not text or len(text) <= max_length:
        return text

    return text[: max_length - 3] + "..."


def validate_subreddit_name(name: str) -> str:
    """
    Validate and clean subreddit name.

    Args:
        name: Subreddit name

    Returns:
        Clean subreddit name

    Raises:
        ValueError: If subreddit name is invalid
    """
    if not name:
        raise ValueError("Subreddit name cannot be empty")

    # Remove r/ prefix if present
    if name.startswith("r/"):
        name = name[2:]

    # Basic validation
    if not name.replace("_", "").isalnum():
        raise ValueError("Subreddit name contains invalid characters")

    if len(name) < 2 or len(name) > 21:
        raise ValueError("Subreddit name must be 2-21 characters long")

    return name


def validate_username(username: str) -> str:
    """
    Validate and clean Reddit username.

    Args:
        username: Reddit username

    Returns:
        Clean username

    Raises:
        ValueError: If username is invalid
    """
    if not username:
        raise ValueError("Username cannot be empty")

    # Remove u/ prefix if present
    if username.startswith("u/"):
        username = username[2:]

    # Basic validation
    if not username.replace("_", "").replace("-", "").isalnum():
        raise ValueError("Username contains invalid characters")

    if len(username) < 3 or len(username) > 20:
        raise ValueError("Username must be 3-20 characters long")

    return username
