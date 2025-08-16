# Development Guide

This guide covers development setup, testing, and contribution guidelines for the Reddit MCP Server.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- uv (modern Python package manager) - install from https://docs.astral.sh/uv/
- Git

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Ormorshtein/reddit-mcp.git
   cd reddit-mcp
   ```

2. **Install in development mode with uv**
   ```bash
   # uv automatically creates and manages virtual environments
   uv sync --extra dev --extra test
   
   # Or if you prefer manual venv management:
   uv venv
   source .venv/bin/activate  # On macOS/Linux
   # or .venv\Scripts\activate on Windows
   uv pip install -e ".[dev,test]"
   ```

3. **Set up environment variables**
   ```bash
   cp env-template.txt .env
   # Edit .env with your Reddit API credentials
   ```

4. **Install pre-commit hooks**
   ```bash
   uv run pre-commit install
   ```

## Project Structure

```
reddit-mcp-server/
├── src/reddit_mcp/          # Main package source
│   ├── __init__.py          # Package initialization
│   ├── main.py              # MCP server implementation
│   ├── reddit_client.py     # Reddit API client
│   ├── config.py            # Configuration management
│   └── utils.py             # Utility functions
├── tests/                   # Test suite
├── pyproject.toml           # Modern Python project configuration
├── main.py                  # Entry point (backward compatibility)
├── env-template.txt         # Environment variables template
└── README.md                # Project documentation
```

## Development Commands

### Running the Server

**Development mode:**
```bash
uv run python -m reddit_mcp.main
# or
uv run python main.py
```

**Installed package:**
```bash
uv run reddit-mcp
```

### Testing

**Run all tests:**
```bash
uv run pytest
```

**Run with coverage:**
```bash
uv run pytest --cov=reddit_mcp --cov-report=html
```

**Run specific test file:**
```bash
uv run pytest tests/test_config.py -v
```

### Code Quality

**Format code:**
```bash
uv run black src/ tests/
```

**Sort imports:**
```bash
uv run isort src/ tests/
```

**Lint code:**
```bash
uv run ruff check src/ tests/
uv run flake8 src/ tests/
```

**Type checking:**
```bash
uv run mypy src/
```

**Run all quality checks:**
```bash
uv run pre-commit run --all-files
```

### Building and Distribution

**Build the package:**
```bash
uv build
```

**Install from local build:**
```bash
uv pip install dist/reddit_mcp-*.whl
```

## Configuration

### Environment Variables

The application uses environment variables for configuration. See `env-template.txt` for all available options.

### Reddit API Setup

1. Go to https://www.reddit.com/prefs/apps/
2. Click "Create App" or "Create Another App"
3. Choose "script" for application type
4. Note down your client ID and secret
5. Set up your `.env` file with these credentials

### Pydantic Settings

Configuration is managed using Pydantic Settings, which provides:
- Automatic environment variable loading
- Type validation and conversion
- Clear error messages for invalid configurations
- IDE autocomplete support

## Testing Strategy

### Unit Tests
- Test individual functions and classes
- Mock external dependencies (Reddit API)
- Focus on business logic and edge cases

### Integration Tests
- Test Reddit API integration (with rate limiting)
- Test MCP protocol compliance
- Use real Reddit API for comprehensive testing

### Test Categories

Use pytest markers to categorize tests:
```bash
uv run pytest -m unit          # Run only unit tests
uv run pytest -m integration   # Run only integration tests
uv run pytest -m "not slow"    # Skip slow tests
```

## Code Style

This project follows modern Python best practices:

- **Black** for code formatting
- **isort** for import sorting
- **Ruff** for fast linting
- **MyPy** for static type checking
- **Pre-commit hooks** for automated checks

### Type Hints

All code should include comprehensive type hints:
```python
from typing import List, Optional, Dict, Any

async def get_posts(subreddit: str, limit: int = 25) -> List[Dict[str, Any]]:
    """Get posts with proper type annotations."""
    pass
```

## Error Handling

### Custom Exceptions
```python
from reddit_mcp.reddit_client import RedditAPIError

try:
    result = await reddit_client.get_posts()
except RedditAPIError as e:
    logger.error(f"Reddit API error: {e}")
```

### Retry Logic
The client includes automatic retry with exponential backoff for transient failures.

## Logging

Structured logging with configurable levels:
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Operation completed", extra={"count": 42})
logger.error("API error", exc_info=True)
```

## Performance

### Rate Limiting
- Respects Reddit's 60 requests/minute limit
- Configurable rate limiting parameters
- Graceful handling of rate limit errors

### Caching
- TTL-based caching for API responses
- Configurable cache size and TTL
- Cache invalidation strategies

### Async/Await
- Fully asynchronous implementation
- Non-blocking I/O operations
- Efficient resource utilization

## Contributing

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Add tests for new functionality**
5. **Ensure all tests pass**
   ```bash
   uv run pytest
   uv run pre-commit run --all-files
   ```
6. **Commit with descriptive messages**
   ```bash
   git commit -m "feat: add amazing feature"
   ```
7. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```
8. **Create a Pull Request**

### Commit Convention

Use conventional commits:
- `feat:` new features
- `fix:` bug fixes
- `docs:` documentation changes
- `style:` formatting changes
- `refactor:` code refactoring
- `test:` adding tests
- `chore:` maintenance tasks

## Debugging

### Enable Debug Logging
```bash
export LOG_LEVEL=DEBUG
```

### Common Issues

**Authentication errors:**
- Verify Reddit API credentials
- Check user agent format
- Ensure proper scopes

**Rate limiting:**
- Reduce request frequency
- Implement exponential backoff
- Use caching effectively

**Network timeouts:**
- Increase timeout values
- Check network connectivity
- Verify Reddit API status

## IDE Setup

### VS Code
Recommended extensions:
- Python
- Pylance
- Black Formatter
- isort
- GitLens

### PyCharm
- Enable type checking
- Configure code style (Black)
- Set up run configurations

## Release Process

1. **Update version in `src/reddit_mcp/__init__.py`**
2. **Update CHANGELOG.md**
3. **Create release commit**
4. **Tag the release**
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   ```
5. **Push tags**
   ```bash
   git push origin --tags
   ```
6. **Build and upload to PyPI**
   ```bash
   uv build
   uv publish
   ```
