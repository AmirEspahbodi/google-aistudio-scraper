"""
Application Layer - Producer-Consumer Orchestration
"""
import asyncio
import logging
from typing import List
from asyncio import Queue
from src.config import AppConfig
from src.models import PromptTask, ScraperResult, PromptStatus, WorkerStats
from src.browser import BrowserManager
from src.scraper import GoogleAIStudioScraper

logger = logging.getLogger(__name__)


class ScraperOrchestrator:
    """Orchestrates multi-worker scraping using producer-consumer pattern."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.browser_manager = BrowserManager(config.browser)
        self.task_queue: Queue[PromptTask] = Queue()
        self.results: List[ScraperResult] = []
        self.worker_stats: List[WorkerStats] = []
        self._shutdown = False
    
    async def load_prompts(self, prompts: List[dict]) -> None:
        """
        Producer: Load prompts into the queue.
        
        Args:
            prompts: List of dicts with 'id' and 'prompt' keys
        """
        logger.info(f"Loading {len(prompts)} prompts into queue")
        
        for prompt_data in prompts:
            task = PromptTask(
                id=prompt_data.get("id", str(len(self.results))),
                prompt=prompt_data["prompt"]
            )
            await self.task_queue.put(task)
        
        logger.info(f"Queue loaded with {self.task_queue.qsize()} tasks")
    
    async def worker(self, worker_id: int) -> None:
        """
        Consumer: Process tasks from the queue.
        
        Args:
            worker_id: Unique identifier for this worker
        """
        logger.info(f"Worker {worker_id}: Starting")
        
        # Create worker stats
        stats = WorkerStats(worker_id=worker_id)
        self.worker_stats.append(stats)
        
        try:
            # Create a stealth page for this worker
            page = await self.browser_manager.create_stealth_page()
            
            # Initialize scraper
            scraper = GoogleAIStudioScraper(
                page=page,
                config=self.config.scraper,
                worker_id=worker_id
            )
            await scraper.initialize()
            
            # Process tasks from queue
            while not self._shutdown:
                try:
                    # Get task with timeout to allow periodic shutdown checks
                    task = await asyncio.wait_for(
                        self.task_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    # Check if queue is empty and we should shutdown
                    if self.task_queue.empty():
                        break
                    continue
                
                # Update task status
                task.status = PromptStatus.PROCESSING
                logger.info(f"Worker {worker_id}: Processing task {task.id}")
                
                # Process the task
                import time
                start_time = time.time()
                
                result = await scraper.process_prompt(task)
                
                processing_time = time.time() - start_time
                stats.total_processing_time += processing_time
                
                if result:
                    # Success
                    task.status = PromptStatus.COMPLETED
                    self.results.append(result)
                    stats.tasks_completed += 1
                    logger.info(
                        f"Worker {worker_id}: Completed task {task.id} "
                        f"in {processing_time:.2f}s"
                    )
                else:
                    # Failure - retry if possible
                    if task.can_retry():
                        task.increment_retry()
                        task.status = PromptStatus.PENDING
                        await self.task_queue.put(task)
                        logger.warning(
                            f"Worker {worker_id}: Task {task.id} failed, "
                            f"requeued (retry {task.retry_count}/{task.max_retries})"
                        )
                    else:
                        task.status = PromptStatus.FAILED
                        stats.tasks_failed += 1
                        logger.error(
                            f"Worker {worker_id}: Task {task.id} failed permanently"
                        )
                
                # Mark task as done
                self.task_queue.task_done()
                
                # Small delay between tasks
                await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Worker {worker_id}: Fatal error: {e}", exc_info=True)
        
        finally:
            logger.info(
                f"Worker {worker_id}: Shutting down. "
                f"Completed: {stats.tasks_completed}, Failed: {stats.tasks_failed}"
            )
    
    async def run(self, prompts: List[dict]) -> List[ScraperResult]:
        """
        Main orchestration method.
        
        Args:
            prompts: List of prompt dictionaries
            
        Returns:
            List of scraper results
        """
        try:
            # Initialize browser
            await self.browser_manager.initialize()
            
            # Load prompts into queue (Producer)
            await self.load_prompts(prompts)
            
            # Start workers (Consumers)
            num_workers = min(
                self.config.scraper.max_workers,
                len(prompts)  # Don't create more workers than tasks
            )
            
            logger.info(f"Starting {num_workers} workers")
            
            workers = [
                asyncio.create_task(self.worker(worker_id))
                for worker_id in range(num_workers)
            ]
            
            # Wait for all tasks to be processed
            await self.task_queue.join()
            
            # Signal workers to shutdown
            self._shutdown = True
            
            # Wait for all workers to finish
            await asyncio.gather(*workers, return_exceptions=True)
            
            # Log statistics
            total_completed = sum(s.tasks_completed for s in self.worker_stats)
            total_failed = sum(s.tasks_failed for s in self.worker_stats)
            total_time = sum(s.total_processing_time for s in self.worker_stats)
            
            logger.info(
                f"Orchestration complete. "
                f"Completed: {total_completed}, Failed: {total_failed}, "
                f"Total processing time: {total_time:.2f}s"
            )
            
            return self.results
        
        finally:
            # Cleanup
            await self.browser_manager.close()