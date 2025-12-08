# before run the project:
```
1) Close all running instances of Chrome
2) Run the following command in your terminal (adjust the path to your Chrome executable if necessary):
--> & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\selenium\ChromeProfile"
```


# Quick Start Guide

Get the Google AI Studio scraper running in 5 minutes!

## 🚀 Fast Setup

### Step 1: Install Dependencies (2 minutes)

```bash
# Run automated setup
python setup.py
```

This will:
- ✅ Check Python version
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Install Playwright browsers
- ✅ Create sample files

### Step 2: Configure Paths (1 minute)

Open `main.py` and update these two paths:

```python
chrome_executable_path=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
user_data_dir=Path(r"C:\Users\YourUsername\AppData\Local\Google\Chrome\User Data"),
```

**💡 Find Your Paths:**

**Windows:**
- Chrome: Usually at `C:\Program Files\Google\Chrome\Application\chrome.exe`
- User Data: Press `Win + R`, type `%LOCALAPPDATA%\Google\Chrome\User Data`

**Mac:**
- Chrome: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- User Data: `~/Library/Application Support/Google/Chrome`

**Linux:**
- Chrome: `/usr/bin/google-chrome`
- User Data: `~/.config/google-chrome`

### Step 3: Login to Google AI Studio (1 minute)

1. Open Chrome (the one you configured)
2. Go to https://aistudio.google.com
3. Login with your Google account
4. Close Chrome

**Important:** The scraper will reuse this authenticated session!

### Step 4: Run (1 minute)

```bash
# Activate virtual environment
# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

# Run the scraper
python main.py
```

## 📊 What to Expect

You'll see logs like this:

```
2024-12-08 10:30:00 - INFO - Google AI Studio Scraper - Starting
2024-12-08 10:30:01 - INFO - Browser context initialized
2024-12-08 10:30:02 - INFO - Starting 3 workers
2024-12-08 10:30:05 - INFO - Worker 0: Processing task prompt_1
2024-12-08 10:30:15 - INFO - Worker 0: Successfully completed task prompt_1
...
2024-12-08 10:32:00 - INFO - Results saved to final_result.json
```

## ✅ Success Check

After completion, check `final_result.json`:

```json
[
  {
    "key": "prompt_1",
    "value": "Quantum entanglement is...",
    "timestamp": "2024-12-08T10:30:45",
    "worker_id": 0
  }
]
```

## 🎯 Customize Your Prompts

Edit the `load_sample_prompts()` function in `main.py`:

```python
async def load_sample_prompts() -> List[dict]:
    return [
        {"id": "my_prompt_1", "prompt": "Your question here"},
        {"id": "my_prompt_2", "prompt": "Another question"},
    ]
```

## 🔧 Common Issues

### Issue: "Path does not exist"
**Fix:** Update Chrome paths in `main.py` to match your system

### Issue: "Please login to Google"
**Fix:** Manually login to Google AI Studio in Chrome first

### Issue: Bot detected
**Fix:** In `main.py`, increase delays:
```python
ScraperConfig(
    typing_delay_max_ms=300,  # Slower typing
    max_workers=1  # Fewer concurrent tabs
)
```

### Issue: Model not found
**Fix:** Check the exact model name in Google AI Studio and update:
```python
ScraperConfig(model_name="Exact Name From UI")
```

## 📈 Scaling Up

### More Workers
```python
ScraperConfig(max_workers=5)  # Up to 10 recommended
```

### Load Prompts from File
```python
import json
import aiofiles

async def load_prompts_from_file(filepath: str) -> List[dict]:
    async with aiofiles.open(filepath, 'r') as f:
        return json.loads(await f.read())

# In main():
prompts = await load_prompts_from_file("my_prompts.json")
```

Format of `my_prompts.json`:
```json
[
  {"id": "1", "prompt": "First prompt"},
  {"id": "2", "prompt": "Second prompt"}
]
```

## 🛡️ Best Practices

1. **Start Small**: Test with 3-5 prompts first
2. **Monitor Logs**: Watch for errors or rate limits
3. **Respect Rate Limits**: Don't run too many workers
4. **Backup Results**: Save `final_result.json` after each run
5. **Update Regularly**: Check for model name changes in Google AI Studio

## 💡 Pro Tips

### Run in Background (Windows)
```bash
pythonw main.py
```

### Run in Background (Mac/Linux)
```bash
nohup python main.py &
```

### Schedule with Cron (Linux/Mac)
```bash
# Edit crontab
crontab -e

# Run every day at 2 AM
0 2 * * * cd /path/to/scraper && /path/to/venv/bin/python main.py
```

### Schedule with Task Scheduler (Windows)
1. Open Task Scheduler
2. Create Basic Task
3. Action: Start a program
4. Program: `C:\path\to\venv\Scripts\python.exe`
5. Arguments: `C:\path\to\main.py`

## 📚 Learn More

- **Full Documentation**: See `README.md`
- **Architecture Details**: See inline code comments
- **Troubleshooting**: Check `scraper.log` for detailed errors

## 🎓 Next Steps

1. ✅ Get basic scraping working
2. 📝 Customize prompts for your use case
3. 🔧 Tune delays and workers for optimal performance
4. 📊 Integrate results into your workflow
5. 🚀 Scale up to production

---

**Need Help?** Check the logs in `scraper.log` for detailed error messages.

**Happy Scraping! 🎉**