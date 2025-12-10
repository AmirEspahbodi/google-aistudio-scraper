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
from src.utils import IncrementalJSONSaver  # <--- IMPORT ADDED

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

        # Initialize Incremental Saver
        # This creates the file immediately with [] if it doesn't exist
        self.saver = IncrementalJSONSaver(config.output_file)

    async def load_prompts(self, prompts: List[dict]) -> None:
        """
        Producer: Load prompts into the queue.
        """
        logger.info(f"Loading {len(prompts)} prompts into queue")

        for prompt_data in prompts:
            # Ensure ID is present
            task_id = prompt_data.get("id") or str(len(self.results))

            task = PromptTask(id=task_id, prompt=prompt_data["prompt"])
            await self.task_queue.put(task)

        logger.info(f"Queue loaded with {self.task_queue.qsize()} tasks")

    async def worker(self, worker_id: int) -> None:
        """
        Consumer: Process tasks from the queue.
        """
        logger.info(f"Worker {worker_id}: Starting")

        stats = WorkerStats(worker_id=worker_id)
        self.worker_stats.append(stats)

        try:
            page = await self.browser_manager.create_stealth_page()

            scraper = GoogleAIStudioScraper(
                page=page, config=self.config.scraper, worker_id=worker_id
            )
            await scraper.initialize()

            while not self._shutdown:
                try:
                    task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    if self.task_queue.empty():
                        break
                    continue

                task.status = PromptStatus.PROCESSING
                logger.info(f"Worker {worker_id}: Processing task {task.id}")

                import time

                start_time = time.time()

                result = await scraper.process_prompt(task)

                processing_time = time.time() - start_time
                stats.total_processing_time += processing_time

                if result:
                    # Success logic
                    task.status = PromptStatus.COMPLETED

                    # 1. Update In-Memory List (optional, good for final stats)
                    self.results.append(result)

                    # 2. INCREMENTAL SAVE (Real-time I/O)
                    # Convert Pydantic model to dict for serialization
                    result_dict = {
                        "key": result.key,
                        "value": result.value,
                    }
                    await self.saver.save(result_dict)

                    stats.tasks_completed += 1
                    logger.info(
                        f"Worker {worker_id}: Completed & Saved task {task.id} "
                        f"in {processing_time:.2f}s"
                    )
                else:
                    # Failure logic
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

                self.task_queue.task_done()
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Worker {worker_id}: Fatal error: {e}", exc_info=True)

        finally:
            logger.info(f"Worker {worker_id}: Shutting down.")

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
                len(prompts),  # Don't create more workers than tasks
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
