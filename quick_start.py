"""
Quick Start Helper Script
Validates setup and provides guidance for first-time users.
"""
import sys
import subprocess
from pathlib import Path
import json


def print_header(text: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def check_python_version() -> bool:
    """Check if Python version is adequate."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")
        return True
    else:
        print(f"✗ Python 3.9+ required, found {version.major}.{version.minor}")
        return False


def check_dependencies() -> bool:
    """Check if required packages are installed."""
    try:
        import playwright
        import aiofiles
        print("✓ Required packages installed")
        return True
    except ImportError as e:
        print(f"✗ Missing package: {e}")
        print("  Run: pip install -r requirements.txt")
        return False


def check_playwright_browsers() -> bool:
    """Check if Playwright browsers are installed."""
    try:
        result = subprocess.run(
            ["playwright", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ Playwright installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        print("✗ Playwright not found")
        print("  Run: playwright install chromium")
        return False


def check_input_file() -> bool:
    """Check if input file exists and is valid."""
    input_file = Path("_0prompts.json")
    
    if not input_file.exists():
        print("✗ Input file '_0prompts.json' not found")
        print("\nCreating sample _0prompts.json...")
        
        sample_data = [
            {
                "id": "test_1",
                "prompt": "Hello! Can you help me understand what you can do?"
            },
            {
                "id": "test_2",
                "prompt": "Explain the concept of clean code in 3 sentences."
            }
        ]
        
        try:
            with open(input_file, 'w', encoding='utf-8') as f:
                json.dump(sample_data, f, indent=2, ensure_ascii=False)
            print("✓ Created sample _0prompts.json with 2 test prompts")
            return True
        except Exception as e:
            print(f"✗ Failed to create sample file: {e}")
            return False
    else:
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                print("✗ _0prompts.json must contain a JSON array")
                return False
            
            if len(data) == 0:
                print("✗ _0prompts.json is empty")
                return False
            
            # Validate structure
            valid = True
            for idx, item in enumerate(data):
                if not isinstance(item, dict):
                    print(f"✗ Item {idx} is not a JSON object")
                    valid = False
                elif 'id' not in item or 'prompt' not in item:
                    print(f"✗ Item {idx} missing 'id' or 'prompt' field")
                    valid = False
            
            if valid:
                print(f"✓ Input file valid with {len(data)} prompts")
            
            return valid
            
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON in _0prompts.json: {e}")
            return False
        except Exception as e:
            print(f"✗ Error reading _0prompts.json: {e}")
            return False


def check_chrome_debugging() -> None:
    """Provide instructions for Chrome debugging setup."""
    print("\n📋 Chrome Remote Debugging Setup")
    print("-" * 70)
    print("\nYou need to start Chrome with remote debugging enabled.")
    print("\n1. Close ALL Chrome windows")
    print("\n2. Run this command:\n")
    
    if sys.platform == "win32":
        print('   "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" ^')
        print('   --remote-debugging-port=9222 ^')
        print('   --user-data-dir="C:\\ChromeDebug"')
    elif sys.platform == "darwin":
        print('   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\')
        print('   --remote-debugging-port=9222 \\')
        print('   --user-data-dir="/tmp/ChromeDebug"')
    else:
        print('   google-chrome \\')
        print('   --remote-debugging-port=9222 \\')
        print('   --user-data-dir="/tmp/ChromeDebug"')
    
    print("\n3. In the Chrome window that opens:")
    print("   - Navigate to: https://aistudio.google.com")
    print("   - Sign in with your Google account")
    print("   - Keep this window OPEN while running the scraper")


def main() -> None:
    """Main quick start routine."""
    print_header("Google AI Studio Scraper - Quick Start")
    
    print("Checking prerequisites...\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Playwright", check_playwright_browsers),
        ("Input File", check_input_file),
    ]
    
    all_passed = True
    for name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            print(f"✗ Error checking {name}: {e}")
            all_passed = False
    
    check_chrome_debugging()
    
    print_header("Status Summary")
    
    if all_passed:
        print("✅ All prerequisites met!")
        print("\nYou're ready to run the scraper:")
        print("\n  1. Start Chrome with remote debugging (see instructions above)")
        print("  2. Login to Google AI Studio")
        print("  3. Run: python main.py")
        print("\nFor detailed help, see README.md and SETUP_GUIDE.md")
    else:
        print("❌ Some prerequisites are missing")
        print("\nPlease fix the issues above and run this script again.")
        print("\nFor detailed help, see SETUP_GUIDE.md")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()