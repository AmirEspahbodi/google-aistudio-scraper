"""
Infrastructure Layer - Browser Setup and Stealth Configuration
"""
import asyncio
import logging
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright_stealth import stealth_async
from src.config import BrowserConfig

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages browser lifecycle with stealth configurations."""
    
    def __init__(self, config: BrowserConfig):
        self.config = config
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
    async def initialize(self) -> BrowserContext:
        """Initialize browser with persistent context and stealth settings."""
        logger.info("Initializing browser with persistent context...")
        
        self.playwright = await async_playwright().start()
        
        # Launch arguments for stealth and anti-detection
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-setuid-sandbox",
            "--disable-infobars",
            "--window-position=0,0",
            "--ignore-certificate-errors",
            "--ignore-certificate-errors-spki-list",
            "--start-maximized",  # Start maximized so you can see everything
        ]
        
        # Use persistent context to leverage existing login session
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.config.user_data_dir),
            executable_path=str(self.config.chrome_executable_path),
            headless=self.config.headless,
            args=launch_args,
            viewport={
                "width": self.config.viewport_width,
                "height": self.config.viewport_height
            },
            locale="en-US",
            timezone_id="America/New_York",
            permissions=["clipboard-read", "clipboard-write"],
            ignore_default_args=["--enable-automation"],
        )
        
        logger.info(f"Browser context initialized with {len(self.context.pages)} existing pages")
        return self.context
    
    async def create_stealth_page(self) -> Page:
        """Create a new page with stealth patches applied."""
        if not self.context:
            raise RuntimeError("Browser context not initialized")
        
        page = await self.context.new_page()
        
        # Apply playwright-stealth patches
        await stealth_async(page)
        
        # Additional CDP evasions
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            window.chrome = {
                runtime: {}
            };
            
            Object.defineProperty(navigator, 'permissions', {
                get: () => ({
                    query: () => Promise.resolve({ state: 'granted' })
                })
            });
        """)
        
        logger.debug("Created new stealth page with CDP evasions")
        return page
    
    async def close(self) -> None:
        """Close browser and cleanup resources."""
        if self.context:
            await self.context.close()
            logger.info("Browser context closed")
        
        if self.playwright:
            await self.playwright.stop()
            logger.info("Playwright stopped")