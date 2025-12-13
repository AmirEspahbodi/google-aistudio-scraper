"""
Application Layer - Producer-Consumer Orchestration
"""

import asyncio
import logging
from asyncio import Queue
from typing import List

from src.browser import BrowserManager
from src.config import AppConfig
from src.models import (
    PromptStatus,
    PromptTask,
    RateLimitDetected,
    ScraperResult,
    WorkerStats,
)
from src.scraper import GoogleAIStudioScraper
from src.utils import IncrementalJSONSaver

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

        # Event to signal a forced user switch due to rate limits
        self._switch_user_event = asyncio.Event()

        self.saver = IncrementalJSONSaver(config.output_file)

    async def load_prompts(self, prompts: List[dict]) -> None:
        """Producer: Load prompts into the queue."""
        logger.info(f"Loading {len(prompts)} prompts into queue")
        for prompt_data in prompts:
            task_id = prompt_data.get("id") or str(len(self.results))
            task = PromptTask(id=task_id, prompt=prompt_data["prompt"])
            await self.task_queue.put(task)
        logger.info(f"Queue loaded with {self.task_queue.qsize()} tasks")

    async def worker(self, worker_id: int, base_url: str) -> None:
        """
        Consumer: Process tasks from the queue for a specific user session.
        """
        logger.info(f"Worker {worker_id}: Starting for {base_url}")
        page = None

        # Find or create stats for this worker ID
        stats = next((s for s in self.worker_stats if s.worker_id == worker_id), None)
        if not stats:
            stats = WorkerStats(worker_id=worker_id)
            self.worker_stats.append(stats)

        try:
            page = await self.browser_manager.create_stealth_page()

            scraper = GoogleAIStudioScraper(
                page=page, config=self.config.scraper, worker_id=worker_id
            )
            # Initialize with the specific User URL
            await scraper.initialize(url=base_url)

            while not self._shutdown and not self._switch_user_event.is_set():
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

                try:
                    result = await scraper.process_prompt(task)

                    processing_time = time.time() - start_time
                    stats.total_processing_time += processing_time

                    if result:
                        task.status = PromptStatus.COMPLETED
                        self.results.append(result)
                        result_dict = {"key": result.key, "value": result.value}
                        await self.saver.save(result_dict)
                        stats.tasks_completed += 1
                        logger.info(
                            f"Worker {worker_id}: Completed & Saved task {task.id} in {processing_time:.2f}s"
                        )
                    else:
                        # Standard failure (not rate limit)
                        if task.can_retry():
                            task.increment_retry()
                            task.status = PromptStatus.PENDING
                            await self.task_queue.put(task)
                            logger.warning(
                                f"Worker {worker_id}: Task {task.id} failed, requeued"
                            )
                        else:
                            task.status = PromptStatus.FAILED
                            stats.tasks_failed += 1
                            logger.error(
                                f"Worker {worker_id}: Task {task.id} failed permanently"
                            )

                except RateLimitDetected:
                    logger.warning(
                        f"Worker {worker_id}: RATE LIMIT DETECTED for task {task.id}"
                    )

                    # 1. Put the task back in the queue to be processed by next user
                    task.status = PromptStatus.PENDING
                    await self.task_queue.put(task)

                    # 2. Signal orchestration to switch user
                    self._switch_user_event.set()

                    # 3. Mark the 'get()' as done so we don't block logic
                    self.task_queue.task_done()
                    break

                self.task_queue.task_done()
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Worker {worker_id}: Fatal error: {e}", exc_info=True)

        finally:
            logger.info(f"Worker {worker_id}: Shutting down (closing page).")
            if page:
                try:
                    await page.close()
                except Exception:
                    pass

    async def run(self, prompts: List[dict]) -> List[ScraperResult]:
        """
        Main orchestration method with Multi-User Rate Limit Switching.
        """
        try:
            # Initialize browser (Persistent Context)
            await self.browser_manager.initialize()

            # Load prompts into queue
            await self.load_prompts(prompts)

            base_urls = self.config.scraper.base_url
            current_url_index = 0

            # Loop through available users/URLs
            while current_url_index < len(base_urls) and not self.task_queue.empty():
                current_url = base_urls[current_url_index]
                logger.info(f"\n{'=' * 60}")
                logger.info(
                    f" Starting Session with User {current_url_index + 1}/{len(base_urls)}"
                )
                logger.info(f" URL: {current_url}")
                logger.info(f" Remaining Tasks: {self.task_queue.qsize()}")
                logger.info(f"{'=' * 60}\n")

                # Reset Control Flags
                self._shutdown = False
                self._switch_user_event.clear()

                num_workers = min(
                    self.config.scraper.max_workers,
                    self.task_queue.qsize() + 5,  # Buffer
                )

                # Start Workers with CURRENT URL
                workers = [
                    asyncio.create_task(self.worker(i, current_url))
                    for i in range(num_workers)
                ]

                # Wait Logic: Wait for EITHER (Queue Empty) OR (Rate Limit Signal)
                queue_join_task = asyncio.create_task(self.task_queue.join())
                switch_signal_task = asyncio.create_task(self._switch_user_event.wait())

                done, pending = await asyncio.wait(
                    [queue_join_task, switch_signal_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                # Check what happened
                if self._switch_user_event.is_set():
                    logger.warning(
                        "Rate Limit Signal received. Stopping current workers..."
                    )
                    self._shutdown = True  # Tell workers to stop naturally

                    # Cancel the queue waiter since we are interrupting
                    if not queue_join_task.done():
                        queue_join_task.cancel()

                    # Wait for all workers to clean up and close their pages
                    await asyncio.gather(*workers, return_exceptions=True)

                    logger.info("  Switching to next user account...")
                    current_url_index += 1

                else:
                    # Queue is empty, job done
                    logger.info("All tasks completed for this session.")
                    self._shutdown = True
                    if not switch_signal_task.done():
                        switch_signal_task.cancel()
                    await asyncio.gather(*workers, return_exceptions=True)
                    break

            if current_url_index >= len(base_urls) and not self.task_queue.empty():
                logger.error(
                    " All user accounts have reached their rate limits. Stopping."
                )

            # Log final statistics
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
            await self.browser_manager.close()
