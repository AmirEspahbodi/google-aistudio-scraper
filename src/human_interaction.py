"""
Human Interaction Service
Simulates human-like typing and clicking behaviors to evade behavioral analysis.
"""
import asyncio
import random
from typing import Optional
from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeout
from src.config import config


class HumanInteractionService:
    """
    Provides human-like interaction methods.
    
    Why this matters:
    - Modern anti-bot systems analyze typing speed, mouse movement, and click patterns
    - Instant actions (page.fill, direct clicks) have isTrusted=false
    - We must simulate realistic human behavior with jitter and randomness
    """
    
    @staticmethod
    async def human_type(page: Page, locator: Locator, text: str) -> None:
        """
        Types text character-by-character with realistic human timing.
        
        Behavior:
        - Random delay between keystrokes (50-150ms)
        - Occasional "thinking pauses" (10% chance)
        - Focuses element first (critical for contenteditable)
        """
        try:
            # Focus the element first
            await locator.focus()
            await asyncio.sleep(random.uniform(0.2, 0.4))
            
            for char in text:
                await page.keyboard.type(char)
                
                # Random keystroke delay
                delay = random.randint(
                    config.typing_delay_min_ms,
                    config.typing_delay_max_ms
                ) / 1000.0
                await asyncio.sleep(delay)
                
                # Occasional "thinking pause"
                if random.random() < config.thinking_pause_chance:
                    pause = config.thinking_pause_duration_ms / 1000.0
                    await asyncio.sleep(pause)
                    
        except Exception as e:
            raise RuntimeError(f"Failed to type text: {str(e)}")
    
    @staticmethod
    async def safe_click(page: Page, locator: Locator, hover: bool = True) -> None:
        """
        Performs a human-like click with optional hover.
        
        Behavior:
        - Waits for element to be visible and enabled
        - Scrolls element into view
        - Optionally hovers before clicking (simulates mouse movement)
        - Random hover duration
        """
        try:
            # Wait for element to be ready
            await locator.wait_for(state="visible", timeout=10000)
            
            # Scroll into view
            await locator.scroll_into_view_if_needed()
            await asyncio.sleep(random.uniform(0.1, 0.3))
            
            # Hover before clicking (simulates mouse movement)
            if hover:
                await locator.hover()
                hover_duration = random.randint(
                    config.hover_duration_min_ms,
                    config.hover_duration_max_ms
                ) / 1000.0
                await asyncio.sleep(hover_duration)
            
            # Perform the click
            await locator.click()
            
        except PlaywrightTimeout:
            raise RuntimeError(f"Element not clickable within timeout")
        except Exception as e:
            raise RuntimeError(f"Failed to click element: {str(e)}")
    
    @staticmethod
    async def random_action_delay() -> None:
        """
        Adds a random delay between actions to reduce bot score.
        Mimics human "thinking time" between interactions.
        """
        delay = random.randint(
            config.action_delay_min_ms,
            config.action_delay_max_ms
        ) / 1000.0
        await asyncio.sleep(delay)