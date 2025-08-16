# Reddit MCP Server for Claude Desktop

A Python-based Model Context Protocol (MCP) server that connects Claude Desktop to Reddit's API, enabling Claude to query Reddit data through standardized functions during conversations.

## 🚀 Features

- **Subreddit Querying**: Fetch posts from specific subreddits with customizable sorting and filtering
- **Post Search**: Search across Reddit using keywords, time ranges, and relevance scoring
- **Comment Analysis**: Retrieve and analyze comment threads for specific posts
- **User Profile Data**: Access public user information and posting history
- **Hot/New/Top Posts**: Get trending content with flexible time period filtering
- **Rate Limiting**: Built-in Reddit API rate limit handling and exponential backoff
- **Caching**: Intelligent caching system to reduce API calls and improve performance

## 📋 Prerequisites

- Python 3.8+
- Reddit API credentials (Client ID, Client Secret, User Agent)
- Claude Desktop application

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/reddit-mcp-server.git
   cd reddit-mcp-server
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Reddit API credentials**
   
   Create a Reddit application at https://www.reddit.com/prefs/apps/
   
   Create a `.env` file in the project root:
   ```env
   REDDIT_CLIENT_ID=your_client_id_here
   REDDIT_CLIENT_SECRET=your_client_secret_here
   REDDIT_USER_AGENT=YourApp/1.0 by YourUsername
   REDDIT_USERNAME=your_reddit_username (optional)
   REDDIT_PASSWORD=your_reddit_password (optional)
   ```

4. **Configure Claude Desktop**
   
   Add the server to your Claude Desktop configuration file:
   
   **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`
   **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   **Linux**: `~/.config/Claude/claude_desktop_config.json`
   
   ```json
   {
     "mcpServers": {
        "reddit-mcp": {
      "args": [
        "--directory",
        <absolute-path-for-your-project>,
        "run",
       "python",
       "-m",
       "main"]
    }
     }
   }
   ```
   
   **Important Notes:**
   - Replace the `cwd` path with your actual project directory
   - Use forward slashes (`/`) even on Windows in the JSON
   - Make sure you have created and filled your `.env` file first
   - Restart Claude Desktop after making configuration changes


## 🎯 Usage with Claude Desktop

Once configured, you can interact with Reddit directly through Claude Desktop conversations:

**Example conversations:**
- "What are the trending posts in r/MachineLearning today?"
- "Search for discussions about Python async/await in the past week"
- "Show me the top comments on this Reddit post: [post URL]"
- "What's the user profile summary for u/reddit_username?"

## 🔧 Available Functions

### `get_subreddit_posts`
Retrieve posts from a specific subreddit.

**Parameters:**
- `subreddit` (string): Subreddit name (without r/)
- `sort` (string): Sort method - "hot", "new", "top", "rising"
- `time_filter` (string): Time period for "top" sort - "hour", "day", "week", "month", "year", "all"
- `limit` (integer): Number of posts to retrieve (1-100)

**Example:**
```python
get_subreddit_posts(subreddit="python", sort="hot", limit=10)
```

### `search_reddit`
Search across Reddit for posts matching specific criteria.

**Parameters:**
- `query` (string): Search query
- `subreddit` (string, optional): Limit search to specific subreddit
- `sort` (string): Sort method - "relevance", "hot", "top", "new", "comments"
- `time_filter` (string): Time period filter
- `limit` (integer): Number of results (1-100)

**Example:**
```python
search_reddit(query="machine learning", subreddit="MachineLearning", sort="top", time_filter="week", limit=20)
```

### `get_post_comments`
Fetch comments for a specific Reddit post.

**Parameters:**
- `post_id` (string): Reddit post ID
- `sort` (string): Comment sort method - "best", "top", "new", "controversial", "old", "qa"
- `limit` (integer): Maximum number of comments to retrieve
- `depth` (integer): Maximum comment thread depth

**Example:**
```python
get_post_comments(post_id="abc123", sort="top", limit=50, depth=3)
```

### `get_user_profile`
Retrieve public information about a Reddit user.

**Parameters:**
- `username` (string): Reddit username (without u/)
- `include_posts` (boolean): Include recent posts in response
- `post_limit` (integer): Number of recent posts to include

**Example:**
```python
get_user_profile(username="spez", include_posts=true, post_limit=10)
```

### `get_trending_subreddits`
Get currently trending/popular subreddits.

**Parameters:**
- `limit` (integer): Number of trending subreddits to retrieve

**Example:**
```python
get_trending_subreddits(limit=15)
```

## 📊 Response Format

All functions return structured JSON data with consistent formatting:

```json
{
  "status": "success",
  "data": {
    "posts": [...],
    "metadata": {
      "total_count": 25,
      "fetch_time": "2024-01-15T10:30:00Z",
      "rate_limit_remaining": 45
    }
  }
}
```

## ⚡ Performance Considerations

- **Rate Limiting**: The server respects Reddit's API rate limits (60 requests per minute)
- **Caching**: Responses are cached for 5 minutes to reduce API calls
- **Batch Processing**: Multiple requests are batched when possible
- **Error Handling**: Robust error handling with exponential backoff for failed requests

## 🔒 Privacy & Security

- No sensitive data is logged or stored permanently
- API credentials are loaded from environment variables
- User data is only accessed through public Reddit API endpoints
- Caching respects Reddit's terms of service

## 🐛 Error Handling

The server handles common scenarios gracefully:

- Invalid subreddit names
- Rate limit exceeded
- Network connectivity issues
- Malformed API responses
- Authentication failures

Error responses include helpful messages and suggested retry strategies.

## 📝 Logging

Comprehensive logging is available at multiple levels:
- `INFO`: General operation status
- `WARNING`: Rate limiting and retry attempts  
- `ERROR`: Failed API calls and configuration issues
- `DEBUG`: Detailed request/response information

Configure logging level via the `LOG_LEVEL` environment variable.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Reddit API documentation and community
- MCP (Model Context Protocol) specification
- Python Reddit API Wrapper (PRAW) library contributors

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation and FAQ
- Review Reddit API terms of service

---

**Note**: This project is not officially affiliated with Reddit, Inc. Please ensure compliance with Reddit's API terms of service and rate limiting guidelines.