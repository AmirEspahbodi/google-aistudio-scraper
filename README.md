# before run the project:
```
1) Close all running instances of Chrome
2) Run the following command in your terminal (adjust the path to your Chrome executable if necessary):
--> & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\selenium\ChromeProfile"
```

# Google AI Studio Advanced Web Scraper

A production-ready, enterprise-grade web scraper for Google AI Studio built with Clean Architecture principles. Features advanced anti-bot detection evasion, human-like interaction simulation, and concurrent processing using the Producer-Consumer pattern.

## 🏗️ Architecture

This project follows **Clean Architecture** with clear separation of concerns:

```
├── config.py           # Configuration Layer (Pydantic models)
├── models.py           # Domain Models (Business entities)
├── browser.py          # Infrastructure Layer (Browser management & stealth)
├── interaction.py      # Service Layer (Human-like interactions)
├── scraper.py          # Service Layer (Scraping logic)
├── orchestrator.py     # Application Layer (Producer-Consumer orchestration)
├── main.py             # Entry point
└── requirements.txt    # Dependencies
```

### Design Principles

- **SOLID**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **DRY**: Don't Repeat Yourself
- **Clean Architecture**: Separation of concerns with clear boundaries
- **Async-First**: Built entirely on Python's asyncio for maximum performance

## 🚀 Features

### Anti-Detection & Stealth
- ✅ **Persistent Chrome Context** - Leverages existing authenticated sessions
- ✅ **CDP Evasions** - Patches navigator properties and removes automation flags
- ✅ **Playwright-Stealth** - Comprehensive stealth patches
- ✅ **Human-Like Behavior** - Character-by-character typing with randomized delays
- ✅ **Mouse Movement Simulation** - Hover effects before clicking
- ✅ **Accessibility Tree Selectors** - Stable selectors immune to CSS changes

### Scalability & Performance
- ✅ **Producer-Consumer Pattern** - Efficient task queue management
- ✅ **Concurrent Workers** - Multiple browser tabs processing in parallel
- ✅ **Async I/O** - Non-blocking file operations with aiofiles
- ✅ **Graceful Error Handling** - Automatic retries with exponential backoff
- ✅ **Worker Statistics** - Detailed performance metrics

### Code Quality
- ✅ **Type Hints** - Full Python 3.10+ type annotations
- ✅ **Pydantic Validation** - Runtime data validation
- ✅ **Comprehensive Logging** - Detailed execution traces
- ✅ **Configuration Management** - Environment-based settings

## 📋 Prerequisites

- **Python 3.10+**
- **Google Chrome** (installed and logged into Google AI Studio)
- **Windows** (paths configured for Windows; adjust for Linux/Mac)

## 🔧 Installation

### 1. Clone or Create Project Structure

```bash
mkdir google-ai-scraper
cd google-ai-scraper
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers

```bash
playwright install chromium
```

## ⚙️ Configuration

### Update `main.py` with Your Paths

```python
config = AppConfig(
    browser=BrowserConfig(
        chrome_executable_path=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        user_data_dir=Path(r"C:\Users\YourUsername\AppData\Local\Google\Chrome\User Data"),
        headless=False
    ),
    scraper=ScraperConfig(
        model_name="Gemini 3 Pro Preview",
        max_workers=3
    ),
    output_file=Path("final_result.json")
)
```

### Finding Your Chrome User Data Directory

**Windows:**
```
C:\Users\<YourUsername>\AppData\Local\Google\Chrome\User Data
```

**macOS:**
```
~/Library/Application Support/Google/Chrome
```

**Linux:**
```
~/.config/google-chrome
```

## 🎯 Usage

### Basic Usage

```bash
python main.py
```

### Custom Prompts

Modify the `load_sample_prompts()` function in `main.py`:

```python
async def load_sample_prompts() -> List[dict]:
    return [
        {"id": "custom_1", "prompt": "Your custom prompt here"},
        {"id": "custom_2", "prompt": "Another prompt"},
    ]
```

### Load Prompts from File

```python
async def load_prompts_from_file(filepath: Path) -> List[dict]:
    async with aiofiles.open(filepath, 'r') as f:
        content = await f.read()
        return json.loads(content)

# In main():
prompts = await load_prompts_from_file(Path("prompts.json"))
```

## 📊 Output

Results are saved to `final_result.json`:

```json
[
  {
    "key": "prompt_1",
    "value": "Quantum entanglement is a phenomenon where...",
    "timestamp": "2024-12-08T10:30:45.123456",
    "worker_id": 0
  }
]
```

## 🔍 How It Works

### 1. Browser Initialization
```python
# Launches persistent Chrome context with stealth patches
context = await browser_manager.initialize()
page = await browser_manager.create_stealth_page()
```

### 2. Human-Like Typing
```python
# Types character-by-character with random delays
await interaction.human_type(page, input_area, prompt)
```

### 3. Producer-Consumer Pattern
```python
# Producer loads tasks into queue
await orchestrator.load_prompts(prompts)

# Multiple workers consume from queue concurrently
workers = [asyncio.create_task(worker(i)) for i in range(num_workers)]
```

### 4. Workflow per Task
1. **Reset Context** - Navigate to fresh chat
2. **Select Model** - Choose "Gemini 3 Pro Preview"
3. **Input Prompt** - Type with human-like delays
4. **Submit** - Click "Run" button
5. **Wait for Completion** - Monitor UI state changes
6. **Extract Response** - Parse the AI's response
7. **Save Result** - Add to results queue

## 🛡️ Anti-Detection Techniques

### CDP Evasions
```javascript
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});
```

### Stealth Arguments
```python
args = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage"
]
```

### Human Behavior Simulation
- **Typing**: 50-150ms delay per character + thinking pauses
- **Clicking**: Mouse movement → hover (100-300ms) → click
- **Action Delays**: 500-1500ms between major actions

### Accessibility Tree Selectors
```python
# ❌ Bad: Fragile CSS classes
page.locator('.mat-button-3Xf9s')

# ✅ Good: Stable accessibility tree
page.get_by_role("button", name="Run")
```

## 🔧 Troubleshooting

### Issue: "Path does not exist" Error

**Solution:** Update Chrome paths in `main.py` to match your system.

### Issue: Authentication Required

**Solution:** Manually log into Google AI Studio in Chrome first. The scraper will reuse your session.

### Issue: Model Not Found

**Solution:** Update `model_name` in config to match the exact text displayed in the UI.

### Issue: Slow Performance

**Solution:** Reduce `max_workers` or increase delays in `ScraperConfig`.

### Issue: Bot Detection

**Solution:** 
- Increase typing delays (`typing_delay_max_ms`)
- Increase action delays (`action_delay_max_ms`)
- Reduce `max_workers` to 1-2

## 📝 Logging

Logs are written to:
- **Console** (stdout)
- **scraper.log** (file)

Adjust log level in `main.py`:
```python
logging.basicConfig(level=logging.DEBUG)  # More verbose
logging.basicConfig(level=logging.WARNING)  # Less verbose
```

## 🧪 Testing

```bash
# Run with minimal prompts for testing
pytest tests/  # If you add tests

# Manual testing
python main.py  # Watch logs for issues
```

## 🎨 Customization

### Change Model
```python
ScraperConfig(model_name="Gemini 1.5 Flash")
```

### Adjust Worker Count
```python
ScraperConfig(max_workers=5)
```

### Modify Typing Speed
```python
ScraperConfig(
    typing_delay_min_ms=100,  # Slower
    typing_delay_max_ms=300
)
```

### Enable Headless Mode
```python
BrowserConfig(headless=True)
```

## ⚠️ Important Notes

1. **Authentication**: You must be logged into Google AI Studio in Chrome first
2. **Rate Limiting**: Google may rate-limit aggressive scraping
3. **Terms of Service**: Ensure compliance with Google's ToS
4. **Ethical Use**: Use responsibly and respect service limitations

## 📚 Dependencies

- **playwright**: Browser automation framework
- **playwright-stealth**: Stealth patches for Playwright
- **pydantic**: Data validation using Python type hints
- **aiofiles**: Async file I/O operations

## 🤝 Contributing

This is a reference implementation. Customize as needed for your use case.

## 📄 License

This code is provided for educational purposes. Ensure compliance with applicable laws and terms of service.

## 🔮 Future Enhancements

- [ ] Add support for multiple Google accounts
- [ ] Implement response validation with Pydantic
- [ ] Add retry strategies for network failures
- [ ] Support for image-based prompts
- [ ] Export results to multiple formats (CSV, Excel)
- [ ] Add progress bar with tqdm
- [ ] Implement distributed scraping across multiple machines

---

**Built with ❤️ using Clean Architecture principles**