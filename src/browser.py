"""
Infrastructure Layer - Browser Setup and Stealth Configuration
"""
import asyncio
import logging
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
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
            "--disable-blink-features=AutomationControlled", # Critical: Removes navigator.webdriver flag at browser level
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-features=IsolateOrigins,site-per-process", # Helps with iframes, sometimes causes issues so keep an eye on it
            "--disable-infobars",
            "--window-position=0,0",
            "--ignore-certificate-errors",
            "--ignore-certificate-errors-spki-list",
            "--start-maximized",
        ]
        
        # Use persistent context to leverage existing login session
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.config.user_data_dir),
            executable_path=str(self.config.chrome_executable_path),
            headless=self.config.headless,
            args=launch_args,
            # CRITICAL FIX: When using --start-maximized, viewport must be None 
            # to allow the window to actually fill the screen.
            viewport=None, 
            locale="en-US",
            timezone_id="America/New_York",
            permissions=["clipboard-read", "clipboard-write"],
            ignore_default_args=["--enable-automation"], # Removes "Chrome is being controlled..." banner
        )
        
        logger.info(f"Browser context initialized with {len(self.context.pages)} existing pages")
        return self.context
    
    async def create_stealth_page(self) -> Page:
        """Create a new page with stealth patches applied."""
        if not self.context:
            raise RuntimeError("Browser context not initialized")
        
        page = await self.context.new_page()
        
        # REMOVE THIS LINE
        # await stealth_async(page) 
        
        # Apply Surgical Manual Evasions
        # This overrides the JS property without breaking the Google App
        await page.add_init_script("""
            // 1. Pass the Webdriver Test
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // 2. Mock Plugins (Google checks this to ensure you aren't headless)
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // 3. Mock Chrome Runtime
            window.chrome = {
                runtime: {}
            };
            
            // 4. Pass Permissions Test
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: 'denied' }) :
                originalQuery(parameters)
            );
        """)
        
        logger.debug("Created new stealth page with surgical CDP evasions")
        return page
    
    async def close(self) -> None:
        """Close browser and cleanup resources."""
        if self.context:
            await self.context.close()
            logger.info("Browser context closed")
        
        if self.playwright:
            await self.playwright.stop()
            logger.info("Playwright stopped")