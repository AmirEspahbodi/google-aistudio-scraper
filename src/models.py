from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class PromptTask(BaseModel):
    """Represents a single prompt to be processed."""
    id: str = Field(description="Unique identifier for the prompt")
    prompt: str = Field(description="The actual prompt text")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ScraperResult(BaseModel):
    """Represents the result of processing a prompt."""
    key: str = Field(description="Prompt identifier")
    value: str = Field(description="AI-generated response")
    success: bool = Field(default=True)
    error_message: Optional[str] = Field(default=None)
    processing_time_seconds: Optional[float] = Field(default=None)


class ScraperMetrics(BaseModel):
    """Metrics for the scraping operation."""
    total_prompts: int
    successful: int
    failed: int
    total_time_seconds: float