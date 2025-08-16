#!/usr/bin/env python3
"""
Reddit MCP Server for Claude Desktop

A Model Context Protocol (MCP) server that provides Claude Desktop with access to Reddit's API.
Enables querying subreddits, searching posts, analyzing comments, and retrieving user profiles.

Main entry point for the MCP server.
"""

import asyncio
import json
import sys
import tracemalloc
from datetime import datetime
from typing import Any, Dict, List, Optional

# Enable memory tracing for debugging
tracemalloc.start()

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, ListToolsResult, TextContent, Tool

from .config import get_config
from .reddit_client import RedditAPIError, RedditClient
from .utils import (
    format_comment_data,
    format_post_data,
    format_subreddit_data,
    format_user_data,
    setup_logging,
)


class RedditMCPServer:
    """Reddit MCP Server implementation."""

    def __init__(self):
        self.config = get_config()
        self.logger = setup_logging(self.config.log_level)
        self.server = Server("reddit-mcp-server")
        self.reddit_client: Optional[RedditClient] = None

        # Register handlers using decorators
        self.setup_handlers()

    def setup_handlers(self):
        """Set up MCP server handlers using decorators."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            return await self._list_tools()
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            return await self._call_tool(name, arguments)

    async def initialize(self) -> None:
        """Initialize the Reddit client with API credentials."""
        try:
            self.reddit_client = RedditClient(self.config)
            await self.reddit_client.initialize()
            self.logger.info("Reddit MCP Server initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Reddit client: {e}")
            raise

    async def _list_tools(self) -> ListToolsResult:
        """List all available Reddit tools."""
        tools = [
            Tool(
                name="get_subreddit_posts",
                description="Retrieve posts from a specific subreddit with sorting and filtering options",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "subreddit": {
                            "type": "string",
                            "description": "Subreddit name (without r/ prefix)",
                        },
                        "sort": {
                            "type": "string",
                            "enum": ["hot", "new", "top", "rising"],
                            "default": "hot",
                            "description": "Sort method for posts",
                        },
                        "time_filter": {
                            "type": "string",
                            "enum": ["hour", "day", "week", "month", "year", "all"],
                            "default": "day",
                            "description": "Time period for 'top' sort",
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 25,
                            "description": "Number of posts to retrieve",
                        },
                    },
                    "required": ["subreddit"],
                },
            ),
            Tool(
                name="search_reddit",
                description="Search across Reddit for posts matching specific criteria",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query string",
                        },
                        "subreddit": {
                            "type": "string",
                            "description": "Limit search to specific subreddit (optional)",
                        },
                        "sort": {
                            "type": "string",
                            "enum": ["relevance", "hot", "top", "new", "comments"],
                            "default": "relevance",
                            "description": "Sort method for search results",
                        },
                        "time_filter": {
                            "type": "string",
                            "enum": ["hour", "day", "week", "month", "year", "all"],
                            "default": "week",
                            "description": "Time period filter",
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 25,
                            "description": "Number of search results",
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="get_post_comments",
                description="Fetch comments for a specific Reddit post",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "post_id": {
                            "type": "string",
                            "description": "Reddit post ID or full URL",
                        },
                        "sort": {
                            "type": "string",
                            "enum": ["best", "top", "new", "controversial", "old", "qa"],
                            "default": "best",
                            "description": "Comment sort method",
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 500,
                            "default": 100,
                            "description": "Maximum number of comments",
                        },
                        "depth": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                            "default": 3,
                            "description": "Maximum comment thread depth",
                        },
                    },
                    "required": ["post_id"],
                },
            ),
            Tool(
                name="get_user_profile",
                description="Retrieve public information about a Reddit user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "description": "Reddit username (without u/ prefix)",
                        },
                        "include_posts": {
                            "type": "boolean",
                            "default": False,
                            "description": "Include recent posts in response",
                        },
                        "post_limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 50,
                            "default": 10,
                            "description": "Number of recent posts to include",
                        },
                    },
                    "required": ["username"],
                },
            ),
            Tool(
                name="get_trending_subreddits",
                description="Get currently trending/popular subreddits",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 50,
                            "default": 15,
                            "description": "Number of trending subreddits",
                        }
                    },
                },
            ),
        ]

        return ListToolsResult(tools=tools)

    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """Execute a tool call and return the result."""
        try:
            if not self.reddit_client:
                raise RuntimeError("Reddit client not initialized")

            result = None

            if name == "get_subreddit_posts":
                result = await self._get_subreddit_posts(**arguments)
            elif name == "search_reddit":
                result = await self._search_reddit(**arguments)
            elif name == "get_post_comments":
                result = await self._get_post_comments(**arguments)
            elif name == "get_user_profile":
                result = await self._get_user_profile(**arguments)
            elif name == "get_trending_subreddits":
                result = await self._get_trending_subreddits(**arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(result, indent=2))]
            )

        except Exception as e:
            self.logger.error(f"Tool {name} failed: {e}")
            error_result = {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.utcnow().isoformat(),
            }
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(error_result, indent=2))],
                isError=True,
            )

    async def _get_subreddit_posts(
        self, subreddit: str, sort: str = "hot", time_filter: str = "day", limit: int = 25
    ) -> Dict[str, Any]:
        """Get posts from a subreddit."""
        posts = await self.reddit_client.get_subreddit_posts(
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
                    "rate_limit_remaining": self.reddit_client.get_rate_limit_remaining(),
                },
            },
        }

    async def _search_reddit(
        self,
        query: str,
        subreddit: Optional[str] = None,
        sort: str = "relevance",
        time_filter: str = "week",
        limit: int = 25,
    ) -> Dict[str, Any]:
        """Search Reddit for posts."""
        posts = await self.reddit_client.search_reddit(
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
                    "rate_limit_remaining": self.reddit_client.get_rate_limit_remaining(),
                },
            },
        }

    async def _get_post_comments(
        self, post_id: str, sort: str = "best", limit: int = 100, depth: int = 3
    ) -> Dict[str, Any]:
        """Get comments for a post."""
        post, comments = await self.reddit_client.get_post_comments(
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
                    "rate_limit_remaining": self.reddit_client.get_rate_limit_remaining(),
                },
            },
        }

    async def _get_user_profile(
        self, username: str, include_posts: bool = False, post_limit: int = 10
    ) -> Dict[str, Any]:
        """Get user profile information."""
        user_data = await self.reddit_client.get_user_profile(
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
                "rate_limit_remaining": self.reddit_client.get_rate_limit_remaining(),
            },
        }

    async def _get_trending_subreddits(self, limit: int = 15) -> Dict[str, Any]:
        """Get trending subreddits."""
        subreddits = await self.reddit_client.get_trending_subreddits(limit=limit)

        return {
            "status": "success",
            "data": {
                "trending_subreddits": subreddits,
                "metadata": {
                    "total_count": len(subreddits),
                    "fetch_time": datetime.utcnow().isoformat(),
                    "rate_limit_remaining": self.reddit_client.get_rate_limit_remaining(),
                },
            },
        }


async def main() -> None:
    """Main entry point for the MCP server."""
    # Initialize the server
    mcp_server = RedditMCPServer()

    try:
        # Initialize Reddit client
        await mcp_server.initialize()

        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            await mcp_server.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="reddit-mcp-server",
                    server_version="1.0.0",
                    capabilities=mcp_server.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities=None
                    ),
                ),
            )

    except KeyboardInterrupt:
        mcp_server.logger.info("Server shutdown requested")
    except Exception as e:
        mcp_server.logger.error(f"Server error: {e}")
        mcp_server.logger.error(f"Error type: {type(e).__name__}")
        mcp_server.logger.error(f"Error details: {str(e)}")
        import traceback
        mcp_server.logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


def cli_main() -> None:
    """CLI entry point for console script."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
