"""
Configuration settings for Google AI Studio Scraper.
Centralized configuration management following Single Responsibility Principle.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class BrowserConfig:
    """Browser-specific configuration settings."""
    
    headless: bool = False
    timeout: int = 60000  # milliseconds
    chrome_executable_path: Optional[str] = None
    user_data_dir: Optional[str] = None
    viewport_width: int = 1920
    viewport_height: int = 1080
    
    @property
    def chrome_path(self) -> str:
        """Get Chrome executable path for Windows."""
        if self.chrome_executable_path:
            return self.chrome_executable_path
        return r"C:\Program Files\Google\Chrome\Application\chrome.exe"


@dataclass(frozen=True)
class ScraperConfig:
    """Scraper-specific configuration settings."""
    
    base_url: str = "https://aistudio.google.com"
    concurrent_pages: int = 3
    max_retries: int = 3
    retry_delay: int = 2  # seconds
    stream_completion_timeout: int = 300  # seconds
    model_name: str = "Gemini 2.0 Flash Experimental"
    
    # Selectors
    home_button_selector: str = 'a[href="/app"]'
    new_chat_selector: str = 'button:has-text("New chat")'
    model_selector_button: str = 'button[aria-label*="model"]'
    prompt_input_selector: str = 'div[contenteditable="true"]'
    submit_button_selector: str = 'button[aria-label="Send message"]'
    stop_button_selector: str = 'button[aria-label="Stop generating"]'
    response_container_selector: str = '.response-content'


@dataclass(frozen=True)
class StorageConfig:
    """Storage and file path configuration."""
    
    base_dir: Path = Path(__file__).parent.parent
    input_file: str = "_0prompts.json"
    output_file: str = "final_result.json"
    log_file: str = "scraper.log"
    
    @property
    def input_path(self) -> Path:
        """Get full path to input file."""
        return self.base_dir / self.input_file
    
    @property
    def output_path(self) -> Path:
        """Get full path to output file."""
        return self.base_dir / self.output_file
    
    @property
    def log_path(self) -> Path:
        """Get full path to log file."""
        return self.base_dir / self.log_file


@dataclass(frozen=True)
class AppConfig:
    """Main application configuration aggregator."""
    
    browser: BrowserConfig = BrowserConfig()
    scraper: ScraperConfig = ScraperConfig()
    storage: StorageConfig = StorageConfig()
    debug_mode: bool = False


# Global configuration instance
config = AppConfig()