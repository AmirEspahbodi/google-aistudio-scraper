"""
Setup script for Google AI Studio Scraper
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """Run a shell command and handle errors."""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}:")
        print(e.stderr)
        return False


def check_python_version():
    """Check if Python version is 3.10+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"❌ Python 3.10+ required. Current version: {version.major}.{version.minor}")
        return False
    print(f"✅ Python version {version.major}.{version.minor}.{version.micro} OK")
    return True


def create_virtual_environment():
    """Create a virtual environment."""
    venv_path = Path("venv")
    if venv_path.exists():
        print("⚠️  Virtual environment already exists. Skipping creation.")
        return True
    
    return run_command(
        [sys.executable, "-m", "venv", "venv"],
        "Creating virtual environment"
    )


def get_pip_command():
    """Get the appropriate pip command based on OS."""
    if os.name == 'nt':  # Windows
        return str(Path("venv") / "Scripts" / "pip.exe")
    else:  # Unix/Linux/Mac
        return str(Path("venv") / "bin" / "pip")


def install_dependencies():
    """Install project dependencies."""
    pip_cmd = get_pip_command()
    
    # Upgrade pip
    if not run_command(
        [pip_cmd, "install", "--upgrade", "pip"],
        "Upgrading pip"
    ):
        return False
    
    # Install requirements
    return run_command(
        [pip_cmd, "install", "-r", "requirements.txt"],
        "Installing dependencies"
    )


def install_playwright_browsers():
    """Install Playwright browsers."""
    if os.name == 'nt':  # Windows
        playwright_cmd = str(Path("venv") / "Scripts" / "playwright.exe")
    else:
        playwright_cmd = str(Path("venv") / "bin" / "playwright")
    
    return run_command(
        [playwright_cmd, "install", "chromium"],
        "Installing Playwright browsers"
    )


def create_sample_files():
    """Create sample configuration files."""
    print(f"\n{'='*60}")
    print("📁 Creating sample files")
    print(f"{'='*60}")
    
    # Sample prompts file
    prompts_file = Path("prompts.json")
    if not prompts_file.exists():
        sample_prompts = [
            {"id": "1", "prompt": "Explain quantum computing in simple terms"},
            {"id": "2", "prompt": "What is the future of AI?"},
            {"id": "3", "prompt": "How does blockchain work?"}
        ]
        
        import json
        with open(prompts_file, 'w') as f:
            json.dump(sample_prompts, f, indent=2)
        print(f"✅ Created {prompts_file}")
    else:
        print(f"⚠️  {prompts_file} already exists")
    
    return True


def print_next_steps():
    """Print instructions for next steps."""
    print(f"\n{'='*60}")
    print("🎉 Setup Complete!")
    print(f"{'='*60}")
    print("\nNext Steps:")
    print("1. Update main.py with your Chrome paths:")
    print("   - chrome_executable_path")
    print("   - user_data_dir")
    print("\n2. Activate virtual environment:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("\n3. Run the scraper:")
    print("   python main.py")
    print("\n4. Check output:")
    print("   final_result.json")
    print(f"{'='*60}\n")


def main():
    """Main setup workflow."""
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║   Google AI Studio Scraper - Setup Script            ║
    ║   Clean Architecture | Production Ready | Advanced    ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    steps = [
        # ("Checking Python version", check_python_version),
        # ("Creating virtual environment", create_virtual_environment),
        # ("Installing dependencies", install_dependencies),
        ("Installing Playwright browsers", install_playwright_browsers),
        ("Creating sample files", create_sample_files),
    ]
    
    for description, func in steps:
        if not func():
            print(f"\n❌ Setup failed at: {description}")
            print("Please fix the error and run setup again.")
            return 1
    
    print_next_steps()
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)