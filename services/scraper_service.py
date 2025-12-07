"""
Scraper service layer orchestrating browser interactions.
Implements Service pattern and encapsulates business logic.
"""
import asyncio
import logging
from typing import Optional
from time import time

from domain.models import Prompt, ProcessingResult, ProcessingStatus
from infrastructure.browser import AIStudioPage, BrowserManager
from config.settings import ScraperConfig


logger = logging.getLogger(__name__)


class ScraperService:
    """
    High-level service for scraping AI responses.
    Coordinates page interactions and error handling.
    """
    
    def __init__(
        self,
        browser_manager: BrowserManager,
        scraper_config: ScraperConfig
    ):
        self._browser_manager = browser_manager
        self._config = scraper_config
        self._active_pages: dict[int, AIStudioPage] = {}
    
    async def initialize_pages(self, count: int) -> None:
        """Initialize N concurrent pages for batch processing."""
        logger.info(f"Initializing {count} concurrent pages...")
        
        tasks = []
        for i in range(count):
            tasks.append(self._initialize_single_page(i))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful initializations
        successful = sum(1 for r in results if not isinstance(r, Exception))
        logger.info(f"Successfully initialized {successful}/{count} pages")
        
        if successful == 0:
            raise RuntimeError("Failed to initialize any pages")
    
    async def _initialize_single_page(self, page_id: int) -> None:
        """Initialize a single page."""
        try:
            page = await self._browser_manager.create_page()
            ai_page = AIStudioPage(page, self._config)
            await ai_page.navigate_and_initialize()
            self._active_pages[page_id] = ai_page
            logger.debug(f"Page {page_id} initialized")
        except Exception as e:
            logger.error(f"Failed to initialize page {page_id}: {e}")
            raise
    
    async def process_prompt(
        self,
        prompt: Prompt,
        page_id: int,
        retry_count: int = 0
    ) -> ProcessingResult:
        """
        Process a single prompt on a specific page.
        Implements retry logic with exponential backoff.
        """
        result = ProcessingResult(
            prompt_id=prompt.id,
            prompt_text=prompt.prompt
        )
        
        start_time = time()
        
        try:
            if page_id not in self._active_pages:
                raise ValueError(f"Page {page_id} not initialized")
            
            page = self._active_pages[page_id]
            result.mark_processing()
            
            logger.info(f"Processing prompt '{prompt.id}' on page {page_id}")
            
            # Step 1: Start new chat session
            await page.start_new_chat()
            
            # Step 2: Select model (optional, may fail gracefully)
            try:
                await page.select_model(self._config.model_name)
            except Exception as e:
                logger.warning(f"Model selection failed (continuing): {e}")
            
            # Step 3: Submit prompt
            await page.submit_prompt(prompt.prompt)
            
            # Step 4: Wait for response completion
            await page.wait_for_response_completion(
                timeout=self._config.stream_completion_timeout
            )
            
            # Step 5: Extract response
            response = await page.extract_response()
            
            processing_time = time() - start_time
            result.mark_completed(response, processing_time)
            
            logger.info(
                f"Successfully processed '{prompt.id}' "
                f"in {processing_time:.2f}s (page {page_id})"
            )
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Error processing '{prompt.id}' on page {page_id}: {error_msg}"
            )
            
            # Retry logic
            if retry_count < self._config.max_retries:
                result.mark_retrying()
                logger.info(
                    f"Retrying '{prompt.id}' "
                    f"(attempt {retry_count + 1}/{self._config.max_retries})"
                )
                
                # Exponential backoff
                await asyncio.sleep(self._config.retry_delay * (2 ** retry_count))
                
                # Reinitialize page if needed
                await self._reinitialize_page_if_needed(page_id)
                
                return await self.process_prompt(prompt, page_id, retry_count + 1)
            else:
                result.mark_failed(error_msg)
                logger.error(f"Failed to process '{prompt.id}' after {retry_count} retries")
                return result
    
    async def _reinitialize_page_if_needed(self, page_id: int) -> None:
        """Reinitialize a page if it's in a bad state."""
        try:
            if page_id in self._active_pages:
                page = self._active_pages[page_id]
                await page.close()
                del self._active_pages[page_id]
            
            await self._initialize_single_page(page_id)
            logger.info(f"Page {page_id} reinitialized")
            
        except Exception as e:
            logger.error(f"Failed to reinitialize page {page_id}: {e}")
    
    async def cleanup(self) -> None:
        """Clean up all pages."""
        logger.info("Cleaning up pages...")
        
        for page_id, page in self._active_pages.items():
            try:
                await page.close()
                logger.debug(f"Closed page {page_id}")
            except Exception as e:
                logger.error(f"Error closing page {page_id}: {e}")
        
        self._active_pages.clear()
        logger.info("All pages cleaned up")
    
    @property
    def active_page_count(self) -> int:
        """Get the number of active pages."""
        return len(self._active_pages)


class RateLimiter:
    """
    Rate limiter to prevent overwhelming the service.
    Implements Token Bucket algorithm.
    """
    
    def __init__(self, requests_per_minute: int = 30):
        self._rate = requests_per_minute
        self._tokens = requests_per_minute
        self._last_update = time()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary."""
        async with self._lock:
            now = time()
            elapsed = now - self._last_update
            
            # Refill tokens based on elapsed time
            self._tokens = min(
                self._rate,
                self._tokens + (elapsed * self._rate / 60)
            )
            self._last_update = now
            
            # Wait if no tokens available
            if self._tokens < 1:
                wait_time = (1 - self._tokens) * 60 / self._rate
                logger.debug(f"Rate limit: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                self._tokens = 0
            else:
                self._tokens -= 1


class HealthChecker:
    """Monitors system health and connection status."""
    
    def __init__(self, browser_manager: BrowserManager):
        self._browser_manager = browser_manager
    
    async def check_health(self) -> dict:
        """Perform health check and return status."""
        health_status = {
            "browser_connected": self._browser_manager.is_connected,
            "timestamp": time()
        }
        
        if not health_status["browser_connected"]:
            logger.warning("Health check failed: Browser not connected")
        
        return health_status
    
    async def monitor(self, interval: int = 60) -> None:
        """Continuously monitor health at specified interval."""
        while True:
            await asyncio.sleep(interval)
            status = await self.check_health()
            logger.debug(f"Health status: {status}")