"""
Stealth Manager
Handles all anti-detection measures including CDP evasions and stealth patching.
"""
import asyncio
from typing import Dict, Any, List
from playwright.async_api import Page, BrowserContext
from playwright_stealth import stealth_async


class StealthManager:
    """
    Manages stealth operations and CDP (Chrome DevTools Protocol) evasions.
    
    Why this is critical:
    - Modern anti-bot systems detect automation through CDP properties
    - Properties like `navigator.webdriver` are telltale signs
    - We must patch these at the CDP level before page load
    """
    
    @staticmethod
    def get_launch_args() -> List[str]:
        """
        Returns Chrome launch arguments for maximum stealth.
        
        Critical arguments:
        - --disable-blink-features=AutomationControlled: Removes the main automation flag
        - --no-sandbox: Required for some environments (use with caution)
        """
        return [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-setuid-sandbox',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-infobars',
            '--window-size=1920,1080',
            '--start-maximized',
        ]
    
    @staticmethod
    async def apply_stealth(page: Page) -> None:
        """
        Apply stealth patches to a page instance.
        
        Must be called immediately after page creation, before navigation.
        Uses playwright-stealth to patch navigator properties.
        """
        await stealth_async(page)
        
        # Additional CDP-level evasions
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Patch Chrome runtime
            window.chrome = {
                runtime: {}
            };
            
            // Randomize plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Randomize languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)
    
    @staticmethod
    async def add_viewport_randomization(page: Page) -> None:
        """
        Slightly randomize viewport to avoid fingerprinting.
        Each tab gets a slightly different viewport size.
        """
        import random
        width = 1920 + random.randint(-50, 50)
        height = 1080 + random.randint(-50, 50)
        await page.set_viewport_size({"width": width, "height": height})

