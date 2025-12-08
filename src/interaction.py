"""
Service Layer - Human-Like Interaction Methods
"""
import asyncio
import random
import logging
from typing import Optional
from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError
from src.config import ScraperConfig

logger = logging.getLogger(__name__)


class HumanInteractionService:
    """Simulates human-like interactions to evade bot detection."""
    
    def __init__(self, config: ScraperConfig):
        self.config = config
    
    def _random_delay(self, min_ms: int, max_ms: int) -> float:
        """Generate random delay in seconds."""
        return random.randint(min_ms, max_ms) / 1000.0
    
    async def human_type(
        self, 
        page: Page, 
        locator: Locator, 
        text: str,
        clear_first: bool = False
    ) -> None:
        """
        Type text character-by-character with human-like randomization.
        
        Args:
            page: Playwright page instance
            locator: Element locator (from accessibility tree)
            text: Text to type
            clear_first: Clear existing content before typing
        """
        logger.debug(f"Human typing: {text[:50]}...")
        
        # Wait for element and focus
        await locator.wait_for(state="visible", timeout=10000)
        await locator.focus()
        await asyncio.sleep(self._random_delay(100, 300))
        
        # Clear if requested
        if clear_first:
            await page.keyboard.press("Control+A")
            await asyncio.sleep(0.05)
            await page.keyboard.press("Backspace")
            await asyncio.sleep(self._random_delay(100, 200))
        
        # Type each character with random delays
        for i, char in enumerate(text):
            await page.keyboard.type(char)
            
            # Random typing delay
            delay = self._random_delay(
                self.config.typing_delay_min_ms,
                self.config.typing_delay_max_ms
            )
            await asyncio.sleep(delay)
            
            # Occasional "thinking" pause
            if random.random() < self.config.thinking_pause_probability:
                thinking_delay = self.config.thinking_pause_duration_ms / 1000.0
                await asyncio.sleep(thinking_delay)
                logger.debug(f"Thinking pause after char {i}")
    
    async def safe_click(
        self, 
        page: Page, 
        locator: Locator,
        hover_before: bool = True
    ) -> None:
        """
        Click element with human-like mouse movement and hover.
        
        Args:
            page: Playwright page instance
            locator: Element locator (from accessibility tree)
            hover_before: Whether to hover before clicking
        """
        # Wait for element to be visible and enabled
        await locator.wait_for(state="visible", timeout=10000)
        
        # Get bounding box for mouse movement
        box = await locator.bounding_box()
        if not box:
            logger.warning("Could not get bounding box, falling back to direct click")
            await locator.click()
            return
        
        # Calculate center point with slight randomization
        x = box["x"] + box["width"] / 2 + random.uniform(-5, 5)
        y = box["y"] + box["height"] / 2 + random.uniform(-5, 5)
        
        # Move mouse to element
        await page.mouse.move(x, y)
        
        # Hover for human-like delay
        if hover_before:
            hover_delay = self._random_delay(
                self.config.hover_duration_min_ms,
                self.config.hover_duration_max_ms
            )
            await asyncio.sleep(hover_delay)
        
        # Click at current mouse position
        await page.mouse.click(x, y)
        logger.debug(f"Human click executed at ({x:.2f}, {y:.2f})")
    
    async def wait_for_element_state(
        self,
        locator: Locator,
        state: str = "visible",
        timeout: int = 30000
    ) -> bool:
        """
        Wait for element to reach a specific state.
        
        Args:
            locator: Element locator
            state: Target state (visible, hidden, attached, detached)
            timeout: Timeout in milliseconds
            
        Returns:
            True if state reached, False if timeout
        """
        try:
            await locator.wait_for(state=state, timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            logger.warning(f"Timeout waiting for element state: {state}")
            return False
    
    async def random_action_delay(self) -> None:
        """Add random delay between actions to appear more human."""
        delay = self._random_delay(
            self.config.action_delay_min_ms,
            self.config.action_delay_max_ms
        )
        await asyncio.sleep(delay)