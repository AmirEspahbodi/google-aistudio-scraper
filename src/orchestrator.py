"""
Orchestrator
Implements the Producer-Consumer pattern for concurrent scraping.
"""
import asyncio
import json
import time
from typing import List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from pathlib import Path

from src.config import config
from src.models import PromptTask, ScraperResult, ScraperMetrics
from src.stealth_manager import StealthManager
from src.human_interaction import HumanInteractionService
from src.scraper_service import AIStudioScraperService


class ScraperOrchestrator:
    """
    Orchestrates the entire scraping operation.
    Implements Producer-Consumer pattern with asyncio.Queue.
    """
    
    def __init__(self, prompts: List[PromptTask]):
        self.prompts = prompts
        self.queue: asyncio.Queue = asyncio.Queue()
        self.results: List[ScraperResult] = []
        self.stealth_manager = StealthManager()
        
    async def producer(self) -> None:
        """
        Producer: Loads prompts into the queue.
        """
        for prompt_task in self.prompts:
            await self.queue.put(prompt_task)
        
        # Add sentinel values to signal workers to stop
        for _ in range(config.num_workers):
            await self.queue.put(None)
    
    async def consumer(self, worker_id: int, context: BrowserContext) -> None:
        """
        Consumer: Processes prompts from the queue.
        Each consumer operates on its own browser tab.
        """
        # Create a new page (tab) for this worker
        page = await context.new_page()
        
        # Apply stealth
        await self.stealth_manager.apply_stealth(page)
        await self.stealth_manager.add_viewport_randomization(page)
        
        # Initialize services
        human_service = HumanInteractionService()
        scraper_service = AIStudioScraperService(page, human_service)
        
        # Navigate to AI Studio
        await scraper_service.navigate_to_studio()
        
        print(f"[Worker {worker_id}] Ready and waiting for tasks...")
        
        while True:
            # Get task from queue
            task = await self.queue.get()
            
            # Check for sentinel (None means stop)
            if task is None:
                self.queue.task_done()
                break
            
            print(f"[Worker {worker_id}] Processing: {task.id}")
            
            # Process the prompt
            result = await scraper_service.process_single_prompt(task.id, task.prompt)
            
            # Store result
            self.results.append(result)
            
            if result.success:
                print(f"[Worker {worker_id}] ✓ Success: {task.id} ({result.processing_time_seconds:.2f}s)")
            else:
                print(f"[Worker {worker_id}] ✗ Failed: {task.id} - {result.error_message}")
            
            # Mark task as done
            self.queue.task_done()
        
        # Cleanup
        await page.close()
        print(f"[Worker {worker_id}] Finished")
    
    async def run(self) -> ScraperMetrics:
        """
        Main orchestration method.
        Launches browser, spawns workers, and coordinates the scraping.
        """
        start_time = time.time()
        
        async with async_playwright() as p:
            # Launch persistent context
            print("Launching persistent Chrome context...")
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(config.user_data_dir),
                headless=False,  # Must be False for persistent context
                executable_path=str(config.chrome_executable_path),
                args=self.stealth_manager.get_launch_args(),
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="America/New_York",
            )
            
            print(f"Spawning {config.num_workers} workers...")
            
            # Create producer task
            producer_task = asyncio.create_task(self.producer())
            
            # Create consumer tasks
            consumer_tasks = [
                asyncio.create_task(self.consumer(i, context))
                for i in range(config.num_workers)
            ]
            
            # Wait for all tasks to complete
            await producer_task
            await self.queue.join()
            await asyncio.gather(*consumer_tasks)
            
            # Close browser
            await context.close()
        
        total_time = time.time() - start_time
        
        # Calculate metrics
        successful = sum(1 for r in self.results if r.success)
        failed = len(self.results) - successful
        
        metrics = ScraperMetrics(
            total_prompts=len(self.prompts),
            successful=successful,
            failed=failed,
            total_time_seconds=total_time
        )
        
        return metrics
    
    def save_results(self) -> None:
        """
        Saves results to JSON file.
        Output format: [{"key": "id", "value": "response"}, ...]
        """
        output_data = [
            {"key": r.key, "value": r.value}
            for r in self.results
            if r.success
        ]
        
        with open(config.output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Results saved to {config.output_file}")

