# Complete Setup Guide

## Step-by-Step Installation

### 1. Environment Setup

#### Windows

```bash
# Install Python 3.9+ from python.org
# Verify installation
python --version

# Create project directory
mkdir ai-studio-scraper
cd ai-studio-scraper

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux

```bash
# Install Python 3.9+ (usually pre-installed)
python3 --version

# Create project directory
mkdir ai-studio-scraper
cd ai-studio-scraper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
```

### 2. Project Structure

Create the following directory structure:

```
ai-studio-scraper/
├── config/
│   ├── __init__.py
│   └── settings.py
├── domain/
│   ├── __init__.py
│   └── models.py
├── infrastructure/
│   ├── __init__.py
│   ├── browser.py
│   └── storage.py
├── services/
│   ├── __init__.py
│   └── scraper_service.py
├── use_cases/
│   ├── __init__.py
│   └── batch_processor.py
├── _0prompts.json
├── requirements.txt
├── main.py
└── README.md
```

### 3. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Verify installation
playwright --version
```

### 4. Chrome Remote Debugging Setup

#### Windows

1. Close all Chrome windows
2. Create a debug profile directory:
   ```bash
   mkdir C:\ChromeDebug
   ```
3. Start Chrome with remote debugging:
   ```bash
   "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\ChromeDebug"
   ```

#### macOS

1. Close all Chrome windows
2. Start Chrome with remote debugging:
   ```bash
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="/tmp/ChromeDebug"
   ```

#### Linux

1. Close all Chrome windows
2. Start Chrome with remote debugging:
   ```bash
   google-chrome --remote-debugging-port=9222 --user-data-dir="/tmp/ChromeDebug"
   ```

### 5. Google AI Studio Login

1. In the Chrome window that opened, navigate to: `https://aistudio.google.com`
2. Sign in with your Google account
3. Accept any terms of service
4. Verify you can access the chat interface
5. Keep this Chrome window open!

### 6. Prepare Input Data

Create `_0prompts.json`:

```json
[
  {
    "id": "test_1",
    "prompt": "Hello, how are you?"
  },
  {
    "id": "test_2",
    "prompt": "Explain quantum computing"
  }
]
```

**Important JSON format rules:**
- Must be valid JSON
- Each item must have `id` (string) and `prompt` (string)
- IDs should be unique
- No trailing commas

### 7. First Run

```bash
# Make sure Chrome is running with debugging
# Make sure you're logged into AI Studio

# Run the scraper
python main.py
```

Expected output:
```
======================================================================
    Google AI Studio Scraper - Production Ready Edition
======================================================================

IMPORTANT: Ensure Chrome is running with remote debugging enabled:
  chrome.exe --remote-debugging-port=9222 --user-data-dir="C:/ChromeDebug"

Starting in 3 seconds...

INFO: Loading prompts...
INFO: Loaded 2 prompts
INFO: Initializing 3 concurrent pages...
INFO: Processing Batch 1 (2 prompts, 0 remaining)
...
```

## Troubleshooting

### Issue: "Failed to initialize browser"

**Solutions:**
1. Verify Chrome is running with `--remote-debugging-port=9222`
2. Check if port 9222 is accessible:
   ```bash
   # Windows
   netstat -an | findstr 9222
   
   # macOS/Linux
   netstat -an | grep 9222
   ```
3. Try restarting Chrome with debugging enabled
4. Check firewall settings

### Issue: "Input file not found"

**Solutions:**
1. Ensure `_0prompts.json` is in the same directory as `main.py`
2. Verify the file name is exactly `_0prompts.json` (with underscore and zero)
3. Check JSON syntax:
   ```bash
   python -m json.tool _0prompts.json
   ```

### Issue: "Could not find prompt input field"

**Solutions:**
1. Google AI Studio UI may have changed
2. Update selectors in `config/settings.py`
3. Enable debug mode to see detailed logs:
   ```python
   # config/settings.py
   debug_mode: bool = True
   ```

### Issue: Slow performance

**Solutions:**
1. Reduce concurrent pages:
   ```python
   # config/settings.py
   concurrent_pages: int = 1
   ```
2. Check your internet connection
3. Try a different time of day (less load on servers)

### Issue: High failure rate

**Solutions:**
1. Increase retry delay:
   ```python
   # config/settings.py
   retry_delay: int = 5  # seconds
   ```
2. Reduce concurrent pages
3. Check if you're being rate-limited
4. Verify you're still logged into AI Studio

## Configuration Tips

### For Maximum Speed

```python
# config/settings.py
concurrent_pages: int = 5
max_retries: int = 2
retry_delay: int = 1
```

### For Maximum Reliability

```python
# config/settings.py
concurrent_pages: int = 1
max_retries: int = 5
retry_delay: int = 3
```

### For Large Datasets (1000+ prompts)

```python
# config/settings.py
concurrent_pages: int = 3
max_retries: int = 3
stream_completion_timeout: int = 600  # 10 minutes
```

## Advanced Configuration

### Custom Chrome Path

If Chrome is installed in a non-standard location:

```python
# config/settings.py
@dataclass(frozen=True)
class BrowserConfig:
    chrome_executable_path: str = r"D:\Programs\Chrome\chrome.exe"
```

### Custom Selectors

If AI Studio UI changes:

```python
# config/settings.py
@dataclass(frozen=True)
class ScraperConfig:
    prompt_input_selector: str = 'textarea[placeholder="Enter your prompt"]'
    submit_button_selector: str = 'button[aria-label="Send"]'
    # ... other selectors
```

### Rate Limiting

Adjust rate limiting to avoid detection:

```python
# services/scraper_service.py
rate_limiter = RateLimiter(requests_per_minute=20)  # Slower
```

## Monitoring

### Real-time Progress

Check `scraper.log` for real-time progress:

```bash
# Windows
type scraper.log

# macOS/Linux
tail -f scraper.log
```

### Metrics

After completion, check `scraper_metrics.json`:

```json
{
  "total_prompts": 100,
  "successful": 98,
  "failed": 2,
  "success_rate": "98.00%",
  "average_processing_time": "12.34s",
  "total_duration": "1234.56s"
}
```

## Production Deployment

### Running as a Service

#### Windows (Task Scheduler)

1. Create a batch file `run_scraper.bat`:
   ```batch
   @echo off
   cd C:\path\to\project
   venv\Scripts\activate
   python main.py
   ```

2. Schedule in Task Scheduler

#### Linux (cron)

```bash
# Edit crontab
crontab -e

# Add line (runs daily at 2 AM)
0 2 * * * cd /path/to/project && /path/to/venv/bin/python main.py
```

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium

COPY . .
CMD ["python", "main.py"]
```

## Best Practices

1. **Always backup your data** before running large batches
2. **Test with small batches** first (5-10 prompts)
3. **Monitor the first few runs** to ensure everything works
4. **Keep Chrome window visible** to catch any issues
5. **Don't close Chrome** while scraper is running
6. **Check logs regularly** for errors or warnings
7. **Update selectors** if AI Studio UI changes
8. **Use version control** (git) for your prompts and config

## Getting Help

1. Check `scraper.log` for detailed error messages
2. Enable debug mode for more information
3. Review this guide and README.md
4. Test with minimal configuration first
5. Verify all prerequisites are met

---

Happy scraping! 🚀