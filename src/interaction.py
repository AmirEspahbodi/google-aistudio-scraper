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
        self, page: Page, locator: Locator, text: str, clear_first: bool = False
    ) -> None:
        """
        Smart typing: Types short text manually, but uses 'Type + Paste' strategy
        for long prompts to simulate a user pasting from a notepad.

        Args:
            page: Playwright page instance
            locator: Element locator
            text: Text to type
            clear_first: Clear existing content before typing
        """
        logger.debug(f"Smart input for text length: {len(text)}")

        # 1. Wait for element, ensure visibility, and focus
        await locator.wait_for(state="visible", timeout=10000)
        await (
            locator.click()
        )  # Click ensures focus better than .focus() for some JS frameworks
        await asyncio.sleep(self._random_delay(100, 300))

        # 2. Clear if requested
        if clear_first:
            await page.keyboard.press("Control+A")
            await asyncio.sleep(0.05)
            await page.keyboard.press("Backspace")
            await asyncio.sleep(self._random_delay(100, 200))

        # 3. STRATEGY DECISION
        # If text is short (< 50 chars), type it all to look human.
        # If text is long, use the 'Prefix + Paste' strategy.
        if len(text) < 50:
            await self._type_character_by_character(page, text)
        else:
            await self._type_and_paste(page, locator, text)

    async def _type_character_by_character(self, page: Page, text: str):
        """Standard slow typing for short inputs."""
        for char in text:
            await page.keyboard.type(char)
            await asyncio.sleep(
                self._random_delay(
                    self.config.typing_delay_min_ms, self.config.typing_delay_max_ms
                )
            )

    async def _type_and_paste(self, page: Page, locator: Locator, text: str):
        """
        The 'Clipboard Paste' Strategy.
        1. Types the first 3-8 characters (Warms up the input event listeners).
        2. Copies the rest to the clipboard.
        3. Pastes.
        """
        # Split text: Prefix (manual type) + Suffix (clipboard paste)
        # We randomize the prefix length so it doesn't look like a script
        prefix_len = random.randint(3, 8)
        prefix = text[:prefix_len]
        suffix = text[prefix_len:]

        # A. Manually type the prefix
        await self._type_character_by_character(page, prefix)

        # Pause slightly as if the user is switching to copy text or pressing Ctrl+V
        await asyncio.sleep(self._random_delay(300, 600))

        # B. Load Suffix into Clipboard
        # We use page.evaluate with an argument to safely handle special chars/newlines
        await page.evaluate("text => navigator.clipboard.writeText(text)", suffix)

        # C. Paste
        # Detect Mac vs Windows/Linux for correct modifier key
        is_mac = await page.evaluate("navigator.platform.includes('Mac')")
        modifier = "Meta" if is_mac else "Control"

        await page.keyboard.press(f"{modifier}+V")

        # D. Safety Trigger
        # Sometimes React/Angular inputs don't detect the 'paste' event immediately.
        # We dispatch an 'input' event to ensure the "Send" button becomes active.
        await locator.dispatch_event("input")

        logger.debug("Paste strategy execution complete")

    async def safe_click(
        self, page: Page, locator: Locator, hover_before: bool = True
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
                self.config.hover_duration_min_ms, self.config.hover_duration_max_ms
            )
            await asyncio.sleep(hover_delay)

        # Click at current mouse position
        await page.mouse.click(x, y)
        logger.debug(f"Human click executed at ({x:.2f}, {y:.2f})")

    async def wait_for_element_state(
        self, locator: Locator, state: str = "visible", timeout: int = 30000
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
            self.config.action_delay_min_ms, self.config.action_delay_max_ms
        )
        await asyncio.sleep(delay)
