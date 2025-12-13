"""
Domain Models - Core business entities
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RateLimitDetected(Exception):
    """Raised when Google AI Studio rate limit is reached."""

    pass


class PromptStatus(str, Enum):
    """Status of a prompt in the processing pipeline."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PromptTask(BaseModel):
    """Represents a single prompt to be processed."""

    id: str = Field(description="Unique identifier for the prompt")
    prompt: str = Field(description="The actual prompt text")
    status: PromptStatus = Field(default=PromptStatus.PENDING)
    retry_count: int = Field(default=0, ge=0)
    max_retries: int = Field(default=3, ge=0)

    def can_retry(self) -> bool:
        """Check if the task can be retried."""
        return self.retry_count < self.max_retries

    def increment_retry(self) -> None:
        """Increment the retry counter."""
        self.retry_count += 1


class ScraperResult(BaseModel):
    """Result of a scraping operation."""

    key: str = Field(description="Prompt identifier")
    value: str = Field(description="AI response text")

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}


class WorkerStats(BaseModel):
    """Statistics for a worker."""

    worker_id: int
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_processing_time: float = 0.0
