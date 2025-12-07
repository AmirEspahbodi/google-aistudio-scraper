"""
Domain models representing core business entities.
Following Domain-Driven Design principles with immutable value objects.
"""
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class ProcessingStatus(Enum):
    """Enumeration of processing states."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass(frozen=True)
class Prompt:
    """Immutable value object representing a prompt to be processed."""
    
    id: str
    prompt: str
    
    def __post_init__(self):
        """Validate prompt data."""
        if not self.id or not isinstance(self.id, str):
            raise ValueError("Prompt ID must be a non-empty string")
        if not self.prompt or not isinstance(self.prompt, str):
            raise ValueError("Prompt text must be a non-empty string")
    
    def __hash__(self):
        return hash((self.id, self.prompt))


@dataclass
class ProcessingResult:
    """Mutable entity representing the result of prompt processing."""
    
    prompt_id: str
    prompt_text: str
    response: Optional[str] = None
    status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None
    retry_count: int = 0
    processing_time: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def mark_processing(self) -> None:
        """Mark result as currently being processed."""
        self.status = ProcessingStatus.PROCESSING
        self.timestamp = datetime.now()
    
    def mark_completed(self, response: str, processing_time: float) -> None:
        """Mark result as successfully completed."""
        self.status = ProcessingStatus.COMPLETED
        self.response = response
        self.processing_time = processing_time
        self.timestamp = datetime.now()
    
    def mark_failed(self, error: str) -> None:
        """Mark result as failed."""
        self.status = ProcessingStatus.FAILED
        self.error_message = error
        self.timestamp = datetime.now()
    
    def mark_retrying(self) -> None:
        """Mark result as retrying after failure."""
        self.status = ProcessingStatus.RETRYING
        self.retry_count += 1
        self.timestamp = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert result to dictionary for serialization."""
        return {
            "key": self.prompt_id,
            "value": self.response,
            "status": self.status.value,
            "error": self.error_message,
            "retry_count": self.retry_count,
            "processing_time": self.processing_time,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Batch:
    """Represents a batch of prompts to be processed concurrently."""
    
    prompts: List[Prompt]
    batch_id: int
    
    def __post_init__(self):
        """Validate batch data."""
        if not self.prompts:
            raise ValueError("Batch must contain at least one prompt")
        if self.batch_id < 0:
            raise ValueError("Batch ID must be non-negative")
    
    @property
    def size(self) -> int:
        """Get the number of prompts in this batch."""
        return len(self.prompts)
    
    def __iter__(self):
        """Allow iteration over prompts in the batch."""
        return iter(self.prompts)


@dataclass
class ScraperMetrics:
    """Aggregate metrics for scraping session."""
    
    total_prompts: int = 0
    successful: int = 0
    failed: int = 0
    total_processing_time: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def start(self, total: int) -> None:
        """Start tracking metrics."""
        self.total_prompts = total
        self.start_time = datetime.now()
    
    def record_success(self, processing_time: float) -> None:
        """Record a successful processing."""
        self.successful += 1
        self.total_processing_time += processing_time
    
    def record_failure(self) -> None:
        """Record a failed processing."""
        self.failed += 1
    
    def finish(self) -> None:
        """Finalize metrics."""
        self.end_time = datetime.now()
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_prompts == 0:
            return 0.0
        return (self.successful / self.total_prompts) * 100
    
    @property
    def average_processing_time(self) -> float:
        """Calculate average processing time."""
        if self.successful == 0:
            return 0.0
        return self.total_processing_time / self.successful
    
    @property
    def total_duration(self) -> Optional[float]:
        """Calculate total duration in seconds."""
        if not self.start_time or not self.end_time:
            return None
        return (self.end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> dict:
        """Convert metrics to dictionary."""
        return {
            "total_prompts": self.total_prompts,
            "successful": self.successful,
            "failed": self.failed,
            "success_rate": f"{self.success_rate:.2f}%",
            "average_processing_time": f"{self.average_processing_time:.2f}s",
            "total_duration": f"{self.total_duration:.2f}s" if self.total_duration else None
        }