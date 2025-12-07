"""
Batch processing use case orchestrating the entire workflow.
Implements Use Case pattern from Clean Architecture.
"""
import asyncio
import logging
from typing import List, Optional
from collections import deque

from domain.models import (
    Prompt,
    Batch,
    ProcessingResult,
    ScraperMetrics,
    ProcessingStatus
)
from services.scraper_service import ScraperService, RateLimiter
from infrastructure.storage import PromptRepository, ResultRepository, BackupManager
from config.settings import AppConfig


logger = logging.getLogger(__name__)


class BatchProcessor:
    """
    Main use case orchestrating the batch processing workflow.
    Implements the complete processing pipeline.
    """
    
    def __init__(
        self,
        scraper_service: ScraperService,
        prompt_repo: PromptRepository,
        result_repo: ResultRepository,
        backup_manager: BackupManager,
        config: AppConfig
    ):
        self._scraper = scraper_service
        self._prompt_repo = prompt_repo
        self._result_repo = result_repo
        self._backup_manager = backup_manager
        self._config = config
        self._rate_limiter = RateLimiter(requests_per_minute=30)
        self._metrics = ScraperMetrics()
        self._all_results: List[ProcessingResult] = []
    
    async def execute(self) -> ScraperMetrics:
        """
        Execute the complete batch processing workflow.
        Returns metrics about the processing session.
        """
        try:
            logger.info("=" * 60)
            logger.info("Starting Batch Processing Workflow")
            logger.info("=" * 60)
            
            # Phase 1: Load prompts
            prompts = await self._load_prompts()
            
            # Phase 2: Initialize metrics
            self._metrics.start(len(prompts))
            
            # Phase 3: Create backup
            await self._backup_manager.create_backup(
                self._config.storage.output_path
            )
            
            # Phase 4: Initialize concurrent pages
            await self._scraper.initialize_pages(
                self._config.scraper.concurrent_pages
            )
            
            # Phase 5: Process batches
            await self._process_all_batches(prompts)
            
            # Phase 6: Save results
            await self._save_final_results()
            
            # Phase 7: Finalize metrics
            self._metrics.finish()
            await self._result_repo.save_metrics(self._metrics.to_dict())
            
            # Phase 8: Cleanup
            await self._backup_manager.cleanup_old_backups()
            
            logger.info("=" * 60)
            logger.info("Batch Processing Completed")
            self._log_metrics()
            logger.info("=" * 60)
            
            return self._metrics
            
        except Exception as e:
            logger.error(f"Fatal error in batch processing: {e}")
            raise
        finally:
            await self._scraper.cleanup()
    
    async def _load_prompts(self) -> List[Prompt]:
        """Load and validate prompts from storage."""
        logger.info("Loading prompts...")
        prompts = await self._prompt_repo.load_all()
        
        if not prompts:
            raise ValueError("No prompts found to process")
        
        logger.info(f"Loaded {len(prompts)} prompts")
        return prompts
    
    async def _process_all_batches(self, prompts: List[Prompt]) -> None:
        """Process all prompts in batches."""
        queue = deque(prompts)
        batch_size = self._config.scraper.concurrent_pages
        batch_number = 0
        
        logger.info(
            f"Processing {len(prompts)} prompts in batches of {batch_size}"
        )
        
        while queue:
            batch_number += 1
            
            # Dequeue next batch
            batch_prompts = []
            for _ in range(min(batch_size, len(queue))):
                if queue:
                    batch_prompts.append(queue.popleft())
            
            if not batch_prompts:
                break
            
            batch = Batch(prompts=batch_prompts, batch_id=batch_number)
            
            logger.info(
                f"Processing Batch {batch_number} "
                f"({batch.size} prompts, {len(queue)} remaining)"
            )
            
            # Process batch concurrently
            results = await self._process_batch(batch)
            
            # Save batch results incrementally
            await self._result_repo.save_batch(results)
            
            # Update metrics
            for result in results:
                if result.status == ProcessingStatus.COMPLETED:
                    self._metrics.record_success(result.processing_time or 0.0)
                else:
                    self._metrics.record_failure()
            
            # Log progress
            progress = (
                (len(prompts) - len(queue)) / len(prompts) * 100
            )
            logger.info(
                f"Progress: {progress:.1f}% "
                f"(Success: {self._metrics.successful}, "
                f"Failed: {self._metrics.failed})"
            )
    
    async def _process_batch(self, batch: Batch) -> List[ProcessingResult]:
        """Process a single batch concurrently."""
        tasks = []
        
        for idx, prompt in enumerate(batch):
            page_id = idx  # Assign each prompt to a page
            
            # Apply rate limiting
            await self._rate_limiter.acquire()
            
            # Create processing task
            task = asyncio.create_task(
                self._scraper.process_prompt(prompt, page_id)
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions in results
        processed_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task exception: {result}")
                # Create failed result
                prompt = list(batch)[idx]
                failed_result = ProcessingResult(
                    prompt_id=prompt.id,
                    prompt_text=prompt.prompt
                )
                failed_result.mark_failed(str(result))
                processed_results.append(failed_result)
            else:
                processed_results.append(result)
        
        # Store all results
        self._all_results.extend(processed_results)
        
        return processed_results
    
    async def _save_final_results(self) -> None:
        """Save all results to final output file."""
        logger.info("Saving final results...")
        
        # Filter and save only successful results
        successful_results = [
            r for r in self._all_results
            if r.status == ProcessingStatus.COMPLETED
        ]
        
        logger.info(
            f"Saving {len(successful_results)} successful results "
            f"(out of {len(self._all_results)} total)"
        )
        
        await self._result_repo.save_final_results(successful_results)
    
    def _log_metrics(self) -> None:
        """Log final metrics summary."""
        logger.info("Processing Metrics:")
        logger.info(f"  Total Prompts: {self._metrics.total_prompts}")
        logger.info(f"  Successful: {self._metrics.successful}")
        logger.info(f"  Failed: {self._metrics.failed}")
        logger.info(f"  Success Rate: {self._metrics.success_rate:.2f}%")
        logger.info(
            f"  Avg Processing Time: "
            f"{self._metrics.average_processing_time:.2f}s"
        )
        logger.info(
            f"  Total Duration: "
            f"{self._metrics.total_duration:.2f}s"
        )


class ProgressTracker:
    """Tracks and reports processing progress."""
    
    def __init__(self, total: int):
        self._total = total
        self._completed = 0
        self._lock = asyncio.Lock()
    
    async def increment(self) -> None:
        """Increment completion counter."""
        async with self._lock:
            self._completed += 1
    
    @property
    def progress_percentage(self) -> float:
        """Get progress as percentage."""
        if self._total == 0:
            return 100.0
        return (self._completed / self._total) * 100
    
    @property
    def remaining(self) -> int:
        """Get remaining items count."""
        return self._total - self._completed
    
    def __str__(self) -> str:
        return f"{self._completed}/{self._total} ({self.progress_percentage:.1f}%)"