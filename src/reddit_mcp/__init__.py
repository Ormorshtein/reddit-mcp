"""
Reddit MCP Server

A Python-based Model Context Protocol (MCP) server that connects Claude Desktop to Reddit's API.
Enables querying subreddits, searching posts, analyzing comments, and retrieving user profiles.
"""

__version__ = "1.0.0"
__author__ = "Oren Morshtein"
__description__ = "Reddit MCP Server for Claude Desktop"

from .main import main

__all__ = ["main"]
