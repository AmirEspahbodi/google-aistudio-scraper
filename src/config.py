"""
Configuration Layer - Pydantic Models for Application Settings
"""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class BrowserConfig(BaseModel):
    """Browser configuration with persistent context settings."""

    chrome_executable_path: Path = Field(
        default=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        description="Path to Chrome executable",
    )
    user_data_dir: Path = Field(
        default=Path(r"C:\selenium\ChromeProfile"),
        description="Chrome User Data Directory for persistent session",
    )
    headless: bool = Field(default=False, description="Run browser in headless mode")
    viewport_width: int = Field(default=1920, ge=800)
    viewport_height: int = Field(default=1080, ge=600)

    @field_validator("chrome_executable_path", "user_data_dir")
    @classmethod
    def validate_paths(cls, v: Path) -> Path:
        """Validate that paths exist."""
        if not v.exists():
            raise ValueError(f"Path does not exist: {v}")
        return v


class ScraperConfig(BaseModel):
    """Scraper configuration and behavior settings."""

    base_url: list[str] = Field(
        default=[
            "https://aistudio.google.com/u/0/",
            "https://aistudio.google.com/u/1/",
            "https://aistudio.google.com/u/2/",
            "https://aistudio.google.com/u/3/",
            "https://aistudio.google.com/u/4/",
            "https://aistudio.google.com/u/5/",
            "https://aistudio.google.com/u/6/",
            "https://aistudio.google.com/u/7/",
            "https://aistudio.google.com/u/8/",
            "https://aistudio.google.com/u/9/"
            
        ], description="Google AI Studio base URL"
    )
    model_name: str = Field(
        default="Gemini 3 Pro Preview",
        description="AI model to select in the interface",
    )
    max_workers: int = Field(
        default=1, ge=1, le=10, description="Concurrent browser tabs"
    )
    page_load_timeout: int = Field(default=60000, description="Page load timeout in ms")
    navigation_timeout: int = Field(
        default=30000, description="Navigation timeout in ms"
    )

    # Human behavior simulation parameters
    typing_delay_min_ms: int = Field(default=50, ge=10)
    typing_delay_max_ms: int = Field(default=150, le=500)
    thinking_pause_probability: float = Field(default=0.1, ge=0.0, le=1.0)
    thinking_pause_duration_ms: int = Field(default=300, ge=100)
    hover_duration_min_ms: int = Field(default=100, ge=50)
    hover_duration_max_ms: int = Field(default=300, le=1000)
    action_delay_min_ms: int = Field(default=500, ge=100)
    action_delay_max_ms: int = Field(default=1500, le=5000)


class AppConfig(BaseModel):
    """Main application configuration."""

    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    scraper: ScraperConfig = Field(default_factory=ScraperConfig)
    output_file: Path = Field(default=Path("final_result.json"))
    log_level: str = Field(default="INFO")

    model_config = {"arbitrary_types_allowed": True}
