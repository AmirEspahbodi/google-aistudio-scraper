# Google AI Studio Scraper

> **Advanced Production-Grade Web Automation System**  
> Multi-account orchestration with intelligent rate limit handling and human-like interaction simulation

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/playwright-1.49.0-green.svg)](https://playwright.dev/)
[![Pydantic](https://img.shields.io/badge/pydantic-2.10.3-red.svg)](https://pydantic-docs.helpmanual.io/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Technical Stack](#technical-stack)
- [Design Patterns](#design-patterns)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Key Components](#key-components)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This is an enterprise-grade automation system designed to interact with Google AI Studio programmatically. The system orchestrates multiple browser sessions across different Google accounts, automatically handles rate limits, simulates human-like behavior to evade bot detection, and processes large batches of prompts with built-in resilience and resume capabilities.

### Use Cases

- **Batch AI Response Collection**: Process hundreds/thousands of prompts efficiently
- **Multi-Model Testing**: Test prompts across different AI models systematically
- **Dataset Generation**: Create training/evaluation datasets from AI responses
- **Rate Limit Circumvention**: Automatically rotate through multiple accounts when limits are reached

---

## 🏗️ Architecture

The project follows **Clean Architecture** principles with clear separation of concerns:
```
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                      │
│              (main.py, orchestrator.py)                  │
├─────────────────────────────────────────────────────────┤
│                    Service Layer                         │
│         (scraper.py, interaction.py, utils.py)          │
├─────────────────────────────────────────────────────────┤
│                   Domain Layer                           │
│                   (models.py)                            │
├─────────────────────────────────────────────────────────┤
│                Infrastructure Layer                      │
│              (browser.py, config.py)                     │
└─────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Responsibility | Key Files |
|-------|---------------|-----------|
| **Application** | Orchestration, workflow coordination, job management | `main.py`, `orchestrator.py` |
| **Service** | Business logic, scraping operations, I/O operations | `scraper.py`, `interaction.py`, `utils.py` |
| **Domain** | Core entities, business rules, validation | `models.py` |
| **Infrastructure** | External services, browser management, configuration | `browser.py`, `config.py` |

---

## ✨ Features

### Core Capabilities

- ✅ **Multi-Account Orchestration**: Automatically rotates through 10+ Google accounts
- ✅ **Intelligent Rate Limit Handling**: Detects rate limits and switches accounts seamlessly
- ✅ **Human-Like Interaction**: Advanced anti-bot detection evasion
- ✅ **Incremental Saving**: Results saved immediately, no data loss on crashes
- ✅ **Resume Support**: Skip already-processed prompts on restart
- ✅ **Concurrent Processing**: Multiple browser tabs for parallel execution
- ✅ **Persistent Browser Context**: Leverages existing login sessions
- ✅ **Virtual Scroll Handling**: Handles dynamic content rendering
- ✅ **Comprehensive Logging**: Detailed logs for debugging and monitoring

### Anti-Detection Mechanisms

1. **Stealth Browser Configuration**
   - Navigator.webdriver masking
   - Plugin spoofing
   - Chrome runtime mocking
   - Permission API patching

2. **Human Behavior Simulation**
   - Randomized typing delays (50-150ms per character)
   - Smart paste strategy for long prompts
   - Mouse movement and hover simulation
   - Natural action delays (500-1500ms)
   - Thinking pauses during typing

3. **Browser Fingerprint Normalization**
   - Timezone/locale configuration
   - Viewport randomization
   - User-Agent consistency

---

## 🛠️ Technical Stack

### Core Dependencies

| Technology | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.10+ | Runtime environment |
| **Playwright** | 1.49.0 | Browser automation framework |
| **Pydantic** | 2.10.3 | Data validation and settings management |
| **AsyncIO** | Built-in | Asynchronous I/O operations |
| **aiofiles** | 24.1.0 | Async file operations |

### Development Dependencies
```
black==24.10.0      # Code formatting
isort==5.13.2       # Import sorting
mypy==1.13.0        # Static type checking
pytest==8.3.4       # Testing framework
pytest-asyncio==0.24.0  # Async test support
```

---

## 🎨 Design Patterns

### 1. **Producer-Consumer Pattern**
**Location**: `orchestrator.py`
```python
async def load_prompts()  # Producer: Loads tasks into queue
async def worker()        # Consumer: Processes tasks from queue
```

### 2. **Service Layer Pattern**
**Location**: `scraper.py`, `interaction.py`

Encapsulates business logic in reusable service classes:
- `GoogleAIStudioScraper`: Orchestrates scraping workflow
- `HumanInteractionService`: Provides interaction primitives

### 3. **Repository Pattern**
**Location**: `utils.py`

Data access abstraction:
- `IncrementalJSONSaver`: Manages result persistence
- `PromptLoader`: Handles input data loading

### 4. **Strategy Pattern**
**Location**: `interaction.py`

Multiple typing strategies:
```python
if len(text) < 50:
    await self._type_character_by_character(page, text)
else:
    await self._type_and_paste(page, locator, text)
```

### 5. **Builder Pattern**
**Location**: `browser.py`

Configurable browser setup with fluent interface via Pydantic models.

### 6. **Domain-Driven Design (DDD)**
**Location**: `models.py`

Rich domain models with business logic:
```python
class PromptTask(BaseModel):
    def can_retry(self) -> bool
    def increment_retry(self) -> None
```

---

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- Google Chrome installed
- Chrome user profile with logged-in Google accounts

### Quick Setup
```bash
# Clone the repository
git clone <repository-url>
cd google-ai-studio-scraper

# Run automated setup (creates venv, installs dependencies, downloads browsers)
python setup.py

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Unix/MacOS:
source venv/bin/activate
```

### Manual Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Unix/MacOS
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

---

## ⚙️ Configuration

### 1. Browser Configuration

Edit `main.py` to set your Chrome paths:
```python
config = AppConfig(
    browser=BrowserConfig(
        chrome_executable_path=Path(
            r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        ),
        user_data_dir=Path(r"C:\selenium\ChromeProfile"),
        headless=False,  # Set True for headless mode
    ),
    scraper=ScraperConfig(
        model_name="Gemini 3 Pro Preview",
        max_workers=1,  # Concurrent browser tabs
    ),
    output_file=Path("final_result.json"),
)
```

### 2. Multi-Account Setup

Configure account URLs in `src/config.py`:
```python
base_url: list[str] = Field(
    default=[
        "https://aistudio.google.com/u/0/",
        "https://aistudio.google.com/u/1/",
        # ... up to u/9/
    ]
)
```

**Requirements**:
- Each `/u/N/` must correspond to a logged-in Google account in your Chrome profile
- Accounts should be pre-authenticated with Google AI Studio access

### 3. Prompt Configuration

Create `prompts.json` in the project root:
```json
[
  {
    "id": "prompt_001",
    "prompt": "Explain quantum computing in simple terms"
  },
  {
    "id": "prompt_002",
    "prompt": "What are the ethical implications of AGI?"
  }
]
```

**Format Requirements**:
- Each prompt must have a unique `id` (used for resume logic)
- The `prompt` field contains the text to send to the AI

---

## 🚀 Usage

### Basic Execution
```bash
# Make sure virtual environment is activated
python main.py
```

### Advanced Options

#### Headless Mode
```python
# In main.py
browser=BrowserConfig(
    headless=True,  # Run without GUI
)
```

#### Adjust Concurrency
```python
scraper=ScraperConfig(
    max_workers=3,  # Run 3 tabs simultaneously (careful with rate limits!)
)
```

#### Custom Output File
```python
config = AppConfig(
    output_file=Path("custom_results.json"),
)
```

### Monitoring Progress

- **Console Output**: Real-time logging of task processing
- **Log File**: Detailed logs saved to `scraper.log`
- **Output File**: Results incrementally saved to `final_result.json`

### Resume Behavior

The scraper automatically resumes from where it left off:

1. On startup, reads `final_result.json`
2. Identifies completed task IDs
3. Skips prompts that have already been processed
4. Processes only remaining prompts

**No configuration needed** - resume works automatically!

---

## 📂 Project Structure
```
google-ai-studio-scraper/
├── src/
│   ├── __init__.py
│   ├── models.py          # Domain models (PromptTask, ScraperResult, etc.)
│   ├── config.py          # Pydantic configuration models
│   ├── browser.py         # Browser lifecycle management + stealth
│   ├── interaction.py     # Human-like interaction simulation
│   ├── scraper.py         # Core scraping workflow logic
│   ├── orchestrator.py    # Multi-worker orchestration
│   └── utils.py           # Utilities (saving, loading, stats)
├── main.py                # Application entry point
├── setup.py               # Automated setup script
├── requirements.txt       # Python dependencies
├── prompts.json           # Input prompts (user-created)
├── final_result.json      # Output results (auto-generated)
├── scraper.log            # Detailed logs (auto-generated)
└── README.md              # This file
```

---

## 🔧 Key Components

### 1. `GoogleAIStudioScraper` (scraper.py)

**Responsibilities**:
- Navigate to Google AI Studio
- Select AI model
- Input prompts with human-like typing
- Submit and wait for responses
- Extract AI-generated text from DOM
- Handle virtual scrolling issues

**Key Methods**:
```python
async def initialize(url: str)                    # Setup browser page
async def reset_chat_context()                    # Start fresh chat
async def select_model()                          # Choose AI model
async def input_prompt(prompt: str)              # Type prompt
async def submit_and_wait()                       # Send & wait for response
async def extract_response() -> Optional[str]    # Parse AI response
async def process_prompt(task) -> ScraperResult  # Complete workflow
```

### 2. `ScraperOrchestrator` (orchestrator.py)

**Responsibilities**:
- Manage task queue (Producer-Consumer)
- Spawn and coordinate worker tasks
- Handle rate limit signals
- Switch between user accounts
- Aggregate results and statistics

**Key Features**:
- Automatic user switching on rate limit detection
- Graceful worker shutdown
- Progress tracking and statistics

### 3. `HumanInteractionService` (interaction.py)

**Responsibilities**:
- Simulate human typing patterns
- Natural mouse movements
- Randomized delays and pauses

**Anti-Detection Techniques**:
```python
# Smart typing strategy
if len(text) < 50:
    type_character_by_character()  # Looks human
else:
    type_prefix_then_paste()       # Efficient for long prompts
```

### 4. `IncrementalJSONSaver` (utils.py)

**Responsibilities**:
- Thread-safe JSON array management
- Incremental result appending
- Maintain valid JSON structure at all times

**Technical Implementation**:
- Binary file mode with precise seeking
- Backward search for closing bracket `]`
- Atomic append-and-rewrite operations

---

## 🚨 Advanced Features

### Rate Limit Detection & Recovery

**Detection Points**:
1. Page content scanning for "reached your rate limit" text
2. Empty response text after completion signal
3. DOM inspection during extraction

**Recovery Strategy**:
```python
try:
    result = await scraper.process_prompt(task)
except RateLimitDetected:
    # Put task back in queue
    await self.task_queue.put(task)
    # Signal orchestrator to switch user
    self._switch_user_event.set()
    break  # Exit worker loop
```

### Virtual Scroll Handling

Google AI Studio uses virtual scrolling (content rendered on-demand). Solution:
```python
async def scroll_to_latest_response():
    # 1. Scroll element into view
    await last_turn.scroll_into_view_if_needed()
    
    # 2. Mouse wheel scroll (triggers virtual list)
    await self.page.mouse.wheel(0, 5000)
    
    # 3. Keyboard 'End' press (most reliable)
    await self.page.keyboard.press("End")
    
    # 4. Wait for DOM update
    await asyncio.sleep(1.0)
```

### Smart Typing Strategy

**Problem**: Typing long prompts character-by-character is slow and obvious.

**Solution**: Hybrid approach
```python
# Short prompts (<50 chars): Type naturally
for char in text:
    await page.keyboard.type(char)
    await random_delay(50, 150)

# Long prompts: Type prefix + paste remainder
prefix = text[:8]  # Type first few chars
await type_prefix(prefix)
await clipboard_paste(remaining_text)
```

### Persistent Browser Context

**Benefit**: No need to log in on each run
```python
self.context = await playwright.chromium.launch_persistent_context(
    user_data_dir=str(self.config.user_data_dir),  # Existing Chrome profile
    # ... other settings
)
```

**Requirements**:
- Chrome user profile must exist
- Must have pre-authenticated Google accounts

---

## 🐛 Troubleshooting

### Common Issues

#### 1. **"Path does not exist" Error**

**Cause**: Chrome executable or user data directory path is incorrect

**Solution**:
```python
# Windows
chrome_executable_path=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
user_data_dir=Path(r"C:\Users\YourUsername\AppData\Local\Google\Chrome\User Data")

# macOS
chrome_executable_path=Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
user_data_dir=Path.home() / "Library/Application Support/Google/Chrome"

# Linux
chrome_executable_path=Path("/usr/bin/google-chrome")
user_data_dir=Path.home() / ".config/google-chrome"
```

#### 2. **Rate Limit Hit Immediately**

**Cause**: Account already at rate limit or not logged in

**Solution**:
- Manually open Chrome with the profile and verify login status
- Check if `/u/0/`, `/u/1/`, etc. are different accounts
- Wait 24 hours for rate limit reset

#### 3. **Empty Response Extraction**

**Cause**: Virtual scrolling not triggered, DOM content not rendered

**Solution**: Already handled in `scroll_to_latest_response()`, but you can increase wait time:
```python
await asyncio.sleep(2.0)  # Increase from 1.0 to 2.0
```

#### 4. **"Could not find input area" Error**

**Cause**: UI has changed or page not fully loaded

**Solution**:
- Increase `page_load_timeout` in config
- Check if Google AI Studio UI has been updated
- Manually verify selectors in browser DevTools

#### 5. **Worker Hangs**

**Cause**: Waiting for element that never appears

**Solution**: All waits have timeouts, but you can adjust:
```python
await element.wait_for(state="visible", timeout=30000)  # 30 seconds
```

### Debug Mode

Enable verbose logging:
```python
# In main.py
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    # ...
)
```

### Browser Debugging

Disable headless mode to watch the browser:
```python
browser=BrowserConfig(
    headless=False,  # You'll see the browser window
)
```

---

## 📊 Performance & Scalability

### Benchmarks (Approximate)

- **Single prompt processing**: 30-60 seconds (including AI generation time)
- **Throughput**: ~1-2 prompts/minute per account
- **Multi-account scaling**: Linear (10 accounts ≈ 10-20 prompts/minute)

### Optimization Tips

1. **Increase max_workers** (carefully):
```python
   max_workers=2  # Run 2 tabs per account (may trigger rate limits faster)
```

2. **Reduce delays** (increases bot detection risk):
```python
   typing_delay_min_ms=30  # Faster typing
   action_delay_min_ms=300  # Faster navigation
```

3. **Use headless mode** (saves resources):
```python
   headless=True
```

---

## 📝 License

This project is for educational and research purposes only. Use responsibly and in accordance with Google's Terms of Service.

---

## 🤝 Contributing

Contributions are welcome! Please ensure:

1. Code follows Black formatting
2. Type hints are used throughout
3. Docstrings follow Google style
4. Tests pass (when available)
```bash
# Format code
black src/ main.py setup.py

# Sort imports
isort src/ main.py setup.py

# Type check
mypy src/
```

---

## 🙏 Acknowledgments

- **Playwright**: Robust browser automation framework
- **Pydantic**: Excellent data validation library
- **AsyncIO**: Python's powerful async primitives

---

**Built with ❤️ using Clean Architecture principles**
