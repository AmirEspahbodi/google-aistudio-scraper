# Google AI Studio Scraper

An asynchronous, Playwright-powered automation tool for submitting prompts to Google AI Studio, collecting model responses, and saving results incrementally. The project is structured with a clean architecture approach and includes anti-detection techniques and human-like interaction behavior to improve reliability when operating against the AI Studio web UI.

## What this project does

- Opens Google AI Studio in a persistent Chromium context (reusing a logged-in profile).
- Iterates through a list of prompts and submits them to a selected model.
- Collects model responses and saves them to a JSON file incrementally.
- Automatically switches between multiple AI Studio user URLs when rate limits are detected.
- Simulates human-like typing, mouse movement, and interaction delays to reduce automation detection.

## Key technologies

- **Python 3.10+** for async orchestration and scripting.
- **Playwright** (Chromium) for browser automation.
- **Pydantic v2** for structured configuration and validation.
- **aiofiles** for async file I/O.

## Architecture overview

This codebase follows a layered, clean-architecture style with explicit separation of concerns:

- **Infrastructure Layer**
  - `BrowserManager` handles Playwright lifecycle, persistent context, and stealth configuration.
- **Service Layer**
  - `GoogleAIStudioScraper` implements the workflow for a single prompt: navigation, model selection, input, submission, and response extraction.
  - `HumanInteractionService` simulates realistic user interactions (typing cadence, hover delays, clipboard paste strategy).
- **Application Layer**
  - `ScraperOrchestrator` coordinates multi-worker scraping with an async queue and rate-limit switching.
- **Domain Layer**
  - `PromptTask`, `ScraperResult`, and `WorkerStats` define the core data models.
- **Utility Layer**
  - `IncrementalJSONSaver` appends results to a JSON array safely and supports resuming.

### Design patterns used

- **Producer–Consumer pattern**: Prompts are enqueued and workers consume them concurrently via `asyncio.Queue`.
- **Worker pool**: The orchestrator spawns a configurable number of workers per account session.
- **Retry strategy**: Each task tracks its retry count and requeues failures up to a limit.
- **Incremental persistence**: Results are appended to a JSON array as each prompt completes, enabling safe restarts.
- **Clean architecture layering**: Clear separation between infrastructure, application orchestration, and domain models.

## Repository layout

```
.
├── main.py                  # Entry point
├── setup.py                 # Optional setup helper
├── requirements.txt         # Dependencies
└── src/
    ├── browser.py           # Playwright lifecycle + stealth setup
    ├── config.py            # Pydantic configuration models
    ├── interaction.py       # Human-like interaction utilities
    ├── models.py            # Domain models (tasks, results, stats)
    ├── orchestrator.py      # Producer-consumer orchestration
    ├── scraper.py           # Core scraping workflow
    └── utils.py             # I/O helpers and statistics
```

## Setup

### 1) Install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2) Configure Chrome paths

Update the paths in `main.py` to point at your local Chrome installation and a persistent profile directory. The scraper depends on an existing logged-in session in Google AI Studio.

```python
BrowserConfig(
    chrome_executable_path=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    user_data_dir=Path(r"C:\selenium\ChromeProfile"),
    headless=False,
)
```

> Tip: You can also use `PathValidator` utilities in `src/utils.py` to locate Chrome paths.

### 3) Provide prompts

Create a `prompts.json` file in the project root with the following structure:

```json
[
  {"id": "1", "prompt": "Explain quantum computing in simple terms"},
  {"id": "2", "prompt": "What is the future of AI?"}
]
```

### 4) Run the scraper

```bash
python main.py
```

Results are written to `final_result.json` and appended incrementally after each prompt completes.

## Configuration reference

Configuration is managed via Pydantic models in `src/config.py`:

- **`BrowserConfig`**: Chrome executable path, user profile directory, headless flag, and viewport settings.
- **`ScraperConfig`**: Base URLs for user sessions, model name, worker count, timeouts, and human-like interaction settings.
- **`AppConfig`**: Top-level container with browser config, scraper config, and output file.

## How the scraping flow works

1. **Startup**: `main.py` builds the configuration and loads prompts from JSON.
2. **Resume logic**: Completed prompt IDs are detected and skipped using the existing output file.
3. **Orchestration**: The `ScraperOrchestrator` initializes a persistent Playwright context and spawns workers.
4. **Prompt processing**: Each worker navigates, selects the model, inputs a prompt, waits for generation, and extracts the result.
5. **Persistence**: Results are appended to the output JSON immediately.
6. **Rate-limit handling**: If rate limits are detected, the orchestrator switches to the next configured user URL.

## Output format

`final_result.json` is a JSON array of objects:

```json
[
  {"key": "1", "value": "Response text..."}
]
```

## Notes and limitations

- The project relies on a **logged-in** Chrome user profile for Google AI Studio access.
- UI selectors are based on the current AI Studio interface and may need adjustments if the UI changes.
- Rate limits are detected by parsing response content and page text; this may require tuning.
- Use responsibly and ensure compliance with Google’s terms of service.

## Development commands (optional)

```bash
black .
isort .
pytest
```

## License

This project does not currently include a license file. Add one if you plan to distribute or open-source the code.
