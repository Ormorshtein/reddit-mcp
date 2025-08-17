#!/usr/bin/env python3
"""
Reddit MCP Server for Claude Desktop

A Model Context Protocol (MCP) server that provides Claude Desktop with access to Reddit's API.
Enables querying subreddits, searching posts, analyzing comments, and retrieving user profiles.

Main entry point for the MCP server.
"""

import asyncio
import sys
import tracemalloc
from datetime import datetime
from typing import Any, Dict, Optional

# Enable memory tracing for debugging
tracemalloc.start()

from mcp.server.fastmcp import FastMCP

from .config import get_config
from .reddit_client import RedditClient
from .utils import (
    format_comment_data,
    format_post_data,
    format_user_data,
    setup_logging,
)

# Create the MCP server instance
mcp = FastMCP("reddit-mcp-server")

# Global variables for configuration and clients
config = get_config()
logger = setup_logging(config.log_level)
reddit_client: Optional[RedditClient] = None


async def initialize_reddit_client() -> None:
    """Initialize the Reddit client with API credentials."""
    global reddit_client
    try:
        reddit_client = RedditClient(config)
        await reddit_client.initialize()
        logger.info("Reddit MCP Server initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Reddit client: {e}")
        raise


@mcp.tool()
async def get_subreddit_posts(
    subreddit: str, 
    sort: str = "hot", 
    time_filter: str = "day", 
    limit: int = 25
) -> Dict[str, Any]:
    """
    Retrieve posts from a specific subreddit with sorting and filtering options.
    
    Args:
        subreddit: Subreddit name (without r/ prefix)
        sort: Sort method for posts (hot, new, top, rising)
        time_filter: Time period for 'top' sort (hour, day, week, month, year, all)
        limit: Number of posts to retrieve (1-100)
    """
    if not reddit_client:
        raise RuntimeError("Reddit client not initialized")
    
    posts = await reddit_client.get_subreddit_posts(
        subreddit=subreddit, sort=sort, time_filter=time_filter, limit=limit
    )

    return {
        "status": "success",
        "data": {
            "subreddit": subreddit,
            "posts": [format_post_data(post) for post in posts],
            "metadata": {
                "total_count": len(posts),
                "sort": sort,
                "time_filter": time_filter,
                "fetch_time": datetime.utcnow().isoformat(),
                "rate_limit_remaining": reddit_client.get_rate_limit_remaining(),
            },
        },
    }


@mcp.tool()
async def search_reddit(
    query: str,
    subreddit: Optional[str] = None,
    sort: str = "relevance",
    time_filter: str = "week",
    limit: int = 25,
) -> Dict[str, Any]:
    """
    Search across Reddit for posts matching specific criteria.
    
    Args:
        query: Search query string
        subreddit: Limit search to specific subreddit (optional)
        sort: Sort method for search results (relevance, hot, top, new, comments)
        time_filter: Time period filter (hour, day, week, month, year, all)
        limit: Number of search results (1-100)
    """
    if not reddit_client:
        raise RuntimeError("Reddit client not initialized")
    
    posts = await reddit_client.search_reddit(
        query=query, subreddit=subreddit, sort=sort, time_filter=time_filter, limit=limit
    )

    return {
        "status": "success",
        "data": {
            "query": query,
            "subreddit": subreddit,
            "posts": [format_post_data(post) for post in posts],
            "metadata": {
                "total_count": len(posts),
                "sort": sort,
                "time_filter": time_filter,
                "fetch_time": datetime.utcnow().isoformat(),
                "rate_limit_remaining": reddit_client.get_rate_limit_remaining(),
            },
        },
    }


@mcp.tool()
async def get_post_comments(
    post_id: str, 
    sort: str = "best", 
    limit: int = 100, 
    depth: int = 3
) -> Dict[str, Any]:
    """
    Fetch comments for a specific Reddit post.
    
    Args:
        post_id: Reddit post ID or full URL
        sort: Comment sort method (best, top, new, controversial, old, qa)
        limit: Maximum number of comments (1-500)
        depth: Maximum comment thread depth (1-10)
    """
    if not reddit_client:
        raise RuntimeError("Reddit client not initialized")
    
    post, comments = await reddit_client.get_post_comments(
        post_id=post_id, sort=sort, limit=limit, depth=depth
    )

    return {
        "status": "success",
        "data": {
            "post": format_post_data(post) if post else None,
            "comments": [
                format_comment_data(comment, getattr(comment, "depth", 0))
                for comment in comments
            ],
            "metadata": {
                "total_comments": len(comments),
                "sort": sort,
                "max_depth": depth,
                "fetch_time": datetime.utcnow().isoformat(),
                "rate_limit_remaining": reddit_client.get_rate_limit_remaining(),
            },
        },
    }


@mcp.tool()
async def get_user_profile(
    username: str, 
    include_posts: bool = False, 
    post_limit: int = 10
) -> Dict[str, Any]:
    """
    Retrieve public information about a Reddit user.
    
    Args:
        username: Reddit username (without u/ prefix)
        include_posts: Include recent posts in response
        post_limit: Number of recent posts to include (1-50)
    """
    if not reddit_client:
        raise RuntimeError("Reddit client not initialized")
    
    user_data = await reddit_client.get_user_profile(
        username=username, include_posts=include_posts, post_limit=post_limit
    )

    formatted_data = {
        "user": format_user_data(user_data["user"]),
        "posts": [format_post_data(post) for post in user_data.get("posts", [])],
    }

    return {
        "status": "success",
        "data": formatted_data,
        "metadata": {
            "include_posts": include_posts,
            "post_count": len(formatted_data["posts"]),
            "fetch_time": datetime.utcnow().isoformat(),
            "rate_limit_remaining": reddit_client.get_rate_limit_remaining(),
        },
    }


@mcp.tool()
async def get_trending_subreddits(limit: int = 15) -> Dict[str, Any]:
    """
    Get currently trending/popular subreddits.
    
    Args:
        limit: Number of trending subreddits (1-50)
    """
    if not reddit_client:
        raise RuntimeError("Reddit client not initialized")
    
    subreddits = await reddit_client.get_trending_subreddits(limit=limit)

    return {
        "status": "success",
        "data": {
            "trending_subreddits": subreddits,
            "metadata": {
                "total_count": len(subreddits),
                "fetch_time": datetime.utcnow().isoformat(),
                "rate_limit_remaining": reddit_client.get_rate_limit_remaining(),
            },
        },
    }





def main() -> None:
    """Main entry point for the MCP server."""
    try:
        # Initialize Reddit client before starting the server
        asyncio.run(initialize_reddit_client())
        
        # Run the MCP server
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
