# Google AI Studio Scraper - Production Ready

A highly-advanced, robust, and modern web scraper for Google AI Studio built with async Python and Playwright, following Clean Architecture principles.

## 🏗️ Architecture

This project implements Clean Architecture with clear separation of concerns:

```
├── config/              # Configuration layer
│   ├── __init__.py
│   └── settings.py      # Centralized settings (SOLID)
├── domain/              # Domain layer (business entities)
│   ├── __init__.py
│   └── models.py        # Immutable value objects & entities
├── infrastructure/      # Infrastructure layer (external concerns)
│   ├── __init__.py
│   ├── browser.py       # Playwright browser management
│   └── storage.py       # File I/O and persistence
├── services/            # Service layer (business logic)
│   ├── __init__.py
│   └── scraper_service.py  # Core scraping orchestration
├── use_cases/           # Use cases layer (workflows)
│   ├── __init__.py
│   └── batch_processor.py  # Batch processing workflow
├── _0prompts.json       # Input: prompts to process
├── final_result.json    # Output: scraped results
├── requirements.txt     # Python dependencies
└── main.py             # Application entry point
```

## ✨ Features

- **Clean Architecture**: SOLID principles, DRY, separation of concerns
- **Async/Await**: Fully asynchronous for maximum efficiency
- **Concurrent Processing**: Process N prompts in parallel
- **Robust Error Handling**: Automatic retries with exponential backoff
- **Rate Limiting**: Token bucket algorithm to prevent overload
- **Comprehensive Logging**: File and console logging with rotation
- **Progress Tracking**: Real-time progress monitoring
- **Metrics Collection**: Detailed performance metrics
- **Backup System**: Automatic backup and cleanup
- **Type Safety**: Full type hints throughout
- **Dependency Injection**: Testable and maintainable code

## 🚀 Quick Start

### Prerequisites

1. **Python 3.9+** installed
2. **Google Chrome** browser installed
3. **Chrome Remote Debugging** enabled

### Installation

1. Clone or download this project

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install chromium
```

### Configuration

1. **Start Chrome with remote debugging:**
```bash
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:/ChromeDebug"

# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="/tmp/ChromeDebug"

# Linux
google-chrome --remote-debugging-port=9222 --user-data-dir="/tmp/ChromeDebug"
```

2. **Login to Google AI Studio manually** in the Chrome window that opened
   - Navigate to https://aistudio.google.com
   - Sign in with your Google account
   - Ensure you have access to the models

3. **Prepare your prompts** in `_0prompts.json`:
```json
[
  {
    "id": "unique_id_1",
    "prompt": "Your prompt text here"
  },
  {
    "id": "unique_id_2",
    "prompt": "Another prompt"
  }
]
```

### Running

Simply run:
```bash
python main.py
```

The scraper will:
1. Connect to your Chrome instance
2. Load prompts from `_0prompts.json`
3. Process them in concurrent batches
4. Save results to `final_result.json`
5. Generate metrics in `scraper_metrics.json`
6. Log everything to `scraper.log`

## ⚙️ Configuration

Edit `config/settings.py` to customize:

```python
@dataclass(frozen=True)
class ScraperConfig:
    concurrent_pages: int = 3  # Number of parallel pages
    max_retries: int = 3       # Retry attempts per prompt
    retry_delay: int = 2       # Delay between retries (seconds)
    model_name: str = "Gemini 2.0 Flash Experimental"
```

## 📊 Output Format

`final_result.json`:
```json
[
  {
    "key": "prompt_001",
    "value": "The AI's response to the prompt..."
  },
  {
    "key": "prompt_002",
    "value": "Another response..."
  }
]
```

`scraper_metrics.json`:
```json
{
  "total_prompts": 10,
  "successful": 9,
  "failed": 1,
  "success_rate": "90.00%",
  "average_processing_time": "15.32s",
  "total_duration": "156.45s"
}
```

## 🔧 Advanced Usage

### Adjusting Concurrency

For faster processing (if you have good internet and resources):
```python
# config/settings.py
concurrent_pages: int = 5  # Increase to 5 or more
```

For more reliable processing (slower but more stable):
```python
concurrent_pages: int = 1  # Process one at a time
```

### Custom Model Selection

To use a different model:
```python
# config/settings.py
model_name: str = "Gemini Pro"  # or any other available model
```

### Debug Mode

Enable detailed logging:
```python
# config/settings.py
@dataclass(frozen=True)
class AppConfig:
    debug_mode: bool = True
```

## 🏛️ Design Patterns Used

1. **Clean Architecture**: Layered architecture with dependency inversion
2. **Repository Pattern**: Data access abstraction (storage.py)
3. **Service Pattern**: Business logic encapsulation (scraper_service.py)
4. **Use Case Pattern**: Application workflow orchestration (batch_processor.py)
5. **Facade Pattern**: Simplified interface for complex operations (AIStudioPage)
6. **Singleton Pattern**: Single browser instance management
7. **Strategy Pattern**: Configurable retry and rate limiting strategies
8. **Observer Pattern**: Progress tracking and metrics collection
9. **Dependency Injection**: Loose coupling between components
10. **Factory Pattern**: Page and result creation

## 🛡️ Error Handling

The scraper handles various failure scenarios:

- **Connection failures**: Automatic reconnection attempts
- **Page timeouts**: Configurable timeout with retries
- **Element not found**: Multiple selector fallbacks
- **Rate limiting**: Token bucket rate limiter
- **Network errors**: Exponential backoff retry strategy

## 📝 Logging

Logs are written to both console and `scraper.log`:

```
2024-01-20 10:30:15 - INFO - Loading prompts...
2024-01-20 10:30:15 - INFO - Loaded 10 prompts
2024-01-20 10:30:16 - INFO - Initializing 3 concurrent pages...
2024-01-20 10:30:20 - INFO - Processing Batch 1 (3 prompts, 7 remaining)
2024-01-20 10:30:35 - INFO - Progress: 30.0% (Success: 3, Failed: 0)
```

## 🧪 Testing

The clean architecture makes testing straightforward:

```python
# Example: Mock the browser manager for unit tests
mock_browser = Mock(spec=BrowserManager)
scraper = ScraperService(mock_browser, config.scraper)

# Test prompt processing
result = await scraper.process_prompt(test_prompt, 0)
assert result.status == ProcessingStatus.COMPLETED
```

## 🔒 Security Considerations

- Uses existing Chrome profile (logged-in session)
- No credentials stored in code
- Rate limiting to avoid detection
- Respects robots.txt and terms of service
- Implements exponential backoff to reduce load

## 🐛 Troubleshooting

### "Browser not connected"
- Ensure Chrome is running with `--remote-debugging-port=9222`
- Check that port 9222 is not blocked by firewall

### "Could not find prompt input field"
- Google AI Studio UI may have changed
- Update selectors in `config/settings.py`

### "Rate limit exceeded"
- Reduce `concurrent_pages` in config
- Increase `retry_delay`

### Slow processing
- Increase `concurrent_pages` if your system can handle it
- Check your internet connection
- Consider the model's response time

## 📚 Dependencies

- **playwright**: Browser automation
- **aiofiles**: Async file operations
- **typing-extensions**: Enhanced type hints

## 📄 License

This project is provided as-is for educational and personal use.

## 🤝 Contributing

This is a production-ready template. Feel free to:
- Add more models
- Implement additional retry strategies
- Add monitoring and alerting
- Create a web UI
- Add database persistence

## 📧 Support

For issues or questions, check the logs in `scraper.log` for detailed error information.

---

**Built with ❤️ using Clean Architecture principles**