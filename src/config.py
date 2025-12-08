"""
Configuration Module
Manages all constants, paths, and environment-specific settings.
"""
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class ScraperConfig(BaseModel):
    """
    Configuration for the Google AI Studio scraper.
    Uses Pydantic for validation and type safety.
    """
    # Browser Configuration
    chrome_executable_path: Path = Field(
        default=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        description="Path to Chrome executable"
    )
    user_data_dir: Path = Field(
        default=Path(r"C:\Users\amir\AppData\Local\Google\Chrome\User Data"),
        description="Chrome User Data Directory (for persistent context)"
    )
    
    # Target Configuration
    target_url: str = Field(
        default="https://aistudio.google.com",
        description="Google AI Studio URL"
    )
    model_name: str = Field(
        default="Gemini 3 Pro Preview",
        description="Target model name"
    )
    
    # Concurrency Configuration
    num_workers: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of concurrent browser tabs"
    )
    
    # Timing Configuration (anti-detection)
    typing_delay_min_ms: int = Field(default=50, description="Min keystroke delay")
    typing_delay_max_ms: int = Field(default=150, description="Max keystroke delay")
    thinking_pause_chance: float = Field(default=0.1, description="Chance of typing pause")
    thinking_pause_duration_ms: int = Field(default=300, description="Pause duration")
    
    hover_duration_min_ms: int = Field(default=100, description="Min hover time")
    hover_duration_max_ms: int = Field(default=300, description="Max hover time")
    
    action_delay_min_ms: int = Field(default=500, description="Min delay between actions")
    action_delay_max_ms: int = Field(default=1500, description="Max delay between actions")
    
    # Output Configuration
    output_file: Path = Field(
        default=Path("finall_result.json"),
        description="Output JSON file"
    )
    
    # Timeout Configuration
    page_load_timeout_ms: int = Field(default=60000, description="Page load timeout")
    generation_timeout_ms: int = Field(default=300000, description="AI generation timeout")
    
    class Config:
        arbitrary_types_allowed = True


# Global config instance
config = ScraperConfig()