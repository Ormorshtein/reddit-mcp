"""
Reddit API client with rate limiting, caching, and error handling.

Provides a high-level interface to Reddit's API using PRAW,
with built-in rate limiting, caching, and robust error handling.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import praw
from cachetools import TTLCache
from praw.models import Comment, Redditor, Submission, Subreddit
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import RedditMCPConfig
from .utils import (
    extract_post_id,
    setup_logging,
    validate_subreddit_name,
    validate_username,
)


class RateLimiter:
    """Simple rate limiter implementation."""

    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    async def acquire(self) -> None:
        """Acquire permission to make a request."""
        now = time.time()

        # Remove old requests outside the time window
        self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]

        # If we're at the limit, wait
        if len(self.requests) >= self.max_requests:
            oldest_request = min(self.requests)
            wait_time = self.time_window - (now - oldest_request)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                return await self.acquire()

        # Record this request
        self.requests.append(now)

    def get_remaining(self) -> int:
        """Get remaining requests in current window."""
        now = time.time()
        self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
        return max(0, self.max_requests - len(self.requests))


class RedditAPIError(Exception):
    """Custom exception for Reddit API errors."""

    pass


class RedditClient:
    """
    High-level Reddit API client with rate limiting and caching.
    """

    def __init__(self, config: RedditMCPConfig):
        self.config = config
        self.logger = setup_logging(config.log_level)
        self.reddit: Optional[praw.Reddit] = None
        self.rate_limiter = RateLimiter(
            max_requests=config.rate_limit_requests,
            time_window=config.rate_limit_window,
        )
        self.cache = TTLCache(
            maxsize=config.cache_max_size,
            ttl=config.cache_ttl,
        )

    async def initialize(self) -> None:
        """Initialize the Reddit client."""
        try:
            self.reddit = praw.Reddit(
                client_id=self.config.reddit_client_id,
                client_secret=self.config.reddit_client_secret,
                user_agent=self.config.reddit_user_agent,
                username=self.config.reddit_username,
                password=self.config.reddit_password,
                timeout=self.config.request_timeout,
            )

            # Test the connection
            await self._run_in_executor(lambda: self.reddit.user.me())
            self.logger.info("Reddit client initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize Reddit client: {e}")
            raise RedditAPIError(f"Reddit client initialization failed: {e}")

    async def _run_in_executor(self, func) -> Any:
        """Run blocking PRAW operations in executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func)

    async def _make_request(self, func, cache_key: Optional[str] = None) -> Any:
        """
        Make a rate-limited, cached Reddit API request.

        Args:
            func: Function to execute
            cache_key: Optional cache key

        Returns:
            API response
        """
        # Check cache first
        if cache_key and cache_key in self.cache:
            self.logger.debug(f"Cache hit for key: {cache_key}")
            return self.cache[cache_key]

        # Apply rate limiting
        await self.rate_limiter.acquire()

        try:
            # Execute the request
            result = await self._run_in_executor(func)

            # Cache the result
            if cache_key:
                self.cache[cache_key] = result
                self.logger.debug(f"Cached result for key: {cache_key}")

            return result

        except Exception as e:
            self.logger.error(f"Reddit API request failed: {e}")
            raise RedditAPIError(f"API request failed: {e}")

    @retry(
        retry=retry_if_exception_type((RedditAPIError, praw.exceptions.RedditAPIException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def get_subreddit_posts(
        self,
        subreddit: str,
        sort: str = "hot",
        time_filter: str = "day",
        limit: int = 25,
    ) -> List[Submission]:
        """
        Get posts from a subreddit.

        Args:
            subreddit: Subreddit name
            sort: Sort method (hot, new, top, rising)
            time_filter: Time filter for top posts
            limit: Number of posts to retrieve

        Returns:
            List of Reddit submissions
        """
        subreddit = validate_subreddit_name(subreddit)
        cache_key = f"subreddit:{subreddit}:{sort}:{time_filter}:{limit}"

        def _get_posts():
            sub = self.reddit.subreddit(subreddit)
            if sort == "hot":
                return list(sub.hot(limit=limit))
            elif sort == "new":
                return list(sub.new(limit=limit))
            elif sort == "top":
                return list(sub.top(time_filter=time_filter, limit=limit))
            elif sort == "rising":
                return list(sub.rising(limit=limit))
            else:
                raise ValueError(f"Invalid sort method: {sort}")

        posts = await self._make_request(_get_posts, cache_key)
        self.logger.info(f"Retrieved {len(posts)} posts from r/{subreddit}")
        return posts

    @retry(
        retry=retry_if_exception_type((RedditAPIError, praw.exceptions.RedditAPIException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def search_reddit(
        self,
        query: str,
        subreddit: Optional[str] = None,
        sort: str = "relevance",
        time_filter: str = "week",
        limit: int = 25,
    ) -> List[Submission]:
        """
        Search Reddit for posts.

        Args:
            query: Search query
            subreddit: Optional subreddit to limit search
            sort: Sort method
            time_filter: Time filter
            limit: Number of results

        Returns:
            List of Reddit submissions
        """
        if subreddit:
            subreddit = validate_subreddit_name(subreddit)

        cache_key = f"search:{query}:{subreddit}:{sort}:{time_filter}:{limit}"

        def _search():
            search_target = self.reddit.subreddit(subreddit) if subreddit else self.reddit.subreddit("all")
            return list(
                search_target.search(
                    query=query,
                    sort=sort,
                    time_filter=time_filter,
                    limit=limit,
                )
            )

        posts = await self._make_request(_search, cache_key)
        self.logger.info(f"Found {len(posts)} posts for query: {query}")
        return posts

    @retry(
        retry=retry_if_exception_type((RedditAPIError, praw.exceptions.RedditAPIException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def get_post_comments(
        self,
        post_id: str,
        sort: str = "best",
        limit: int = 100,
        depth: int = 3,
    ) -> Tuple[Optional[Submission], List[Comment]]:
        """
        Get comments for a Reddit post.

        Args:
            post_id: Reddit post ID or URL
            sort: Comment sort method
            limit: Maximum number of comments
            depth: Maximum thread depth

        Returns:
            Tuple of (post, comments list)
        """
        post_id = extract_post_id(post_id)
        cache_key = f"comments:{post_id}:{sort}:{limit}:{depth}"

        def _get_comments():
            submission = self.reddit.submission(id=post_id)
            submission.comment_sort = sort
            submission.comment_limit = limit
            submission.comments.replace_more(limit=0)  # Don't load "more comments"

            comments = []

            def extract_comments(comment_list, current_depth=0):
                if current_depth >= depth:
                    return
                for comment in comment_list:
                    if isinstance(comment, Comment):
                        comments.append(comment)
                        if hasattr(comment, "replies") and comment.replies:
                            extract_comments(comment.replies, current_depth + 1)

            extract_comments(submission.comments)
            return submission, comments[:limit]

        post, comments = await self._make_request(_get_comments, cache_key)
        self.logger.info(f"Retrieved {len(comments)} comments for post {post_id}")
        return post, comments

    @retry(
        retry=retry_if_exception_type((RedditAPIError, praw.exceptions.RedditAPIException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def get_user_profile(
        self,
        username: str,
        include_posts: bool = False,
        post_limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Get user profile information.

        Args:
            username: Reddit username
            include_posts: Whether to include recent posts
            post_limit: Number of recent posts to include

        Returns:
            User profile data
        """
        username = validate_username(username)
        cache_key = f"user:{username}:{include_posts}:{post_limit}"

        def _get_user():
            user = self.reddit.redditor(username)
            user_data = {"user": user, "posts": []}

            if include_posts:
                try:
                    user_data["posts"] = list(user.submissions.new(limit=post_limit))
                except Exception as e:
                    self.logger.warning(f"Failed to get posts for user {username}: {e}")

            return user_data

        result = await self._make_request(_get_user, cache_key)
        self.logger.info(f"Retrieved profile for user {username}")
        return result

    @retry(
        retry=retry_if_exception_type((RedditAPIError, praw.exceptions.RedditAPIException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def get_trending_subreddits(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Get trending subreddits.

        Args:
            limit: Number of trending subreddits

        Returns:
            List of trending subreddit data
        """
        cache_key = f"trending:{limit}"

        def _get_trending():
            # Use popular subreddits as a proxy for trending
            popular_subs = []
            for sub in self.reddit.subreddits.popular(limit=limit):
                try:
                    popular_subs.append({
                        "name": sub.display_name,
                        "title": getattr(sub, "title", ""),
                        "subscribers": getattr(sub, "subscribers", 0),
                        "description": getattr(sub, "public_description", "")[:200],
                        "over18": getattr(sub, "over18", False),
                        "url": f"https://reddit.com/r/{sub.display_name}",
                    })
                except Exception as e:
                    self.logger.warning(f"Failed to get data for subreddit: {e}")
                    continue

            return popular_subs

        subreddits = await self._make_request(_get_trending, cache_key)
        self.logger.info(f"Retrieved {len(subreddits)} trending subreddits")
        return subreddits

    def get_rate_limit_remaining(self) -> int:
        """Get remaining API requests in current rate limit window."""
        return self.rate_limiter.get_remaining()

    def clear_cache(self) -> None:
        """Clear the request cache."""
        self.cache.clear()
        self.logger.info("Request cache cleared")
