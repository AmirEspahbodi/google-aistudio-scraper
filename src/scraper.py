"""
Service Layer - Google AI Studio Scraper Implementation
"""

import asyncio
import logging
from ast import Return
from typing import Optional

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from src.config import ScraperConfig
from src.interaction import HumanInteractionService
from src.models import PromptTask, RateLimitDetected, ScraperResult

logger = logging.getLogger(__name__)


class GoogleAIStudioScraper:
    """Orchestrates the scraping workflow for Google AI Studio."""

    def __init__(self, page: Page, config: ScraperConfig, worker_id: int):
        self.page = page
        self.config = config
        self.worker_id = worker_id
        self.interaction = HumanInteractionService(config)

    async def initialize(self, url: Optional[str] = None) -> None:
        """Navigate to Google AI Studio and prepare the page."""
        target_url = url or self.config.base_url[0]
        logger.info(
            f"Worker {self.worker_id}: Initializing Google AI Studio at {target_url}"
        )

        # Set timeouts
        self.page.set_default_timeout(self.config.page_load_timeout)
        self.page.set_default_navigation_timeout(self.config.navigation_timeout)

        # Navigate to target URL
        await self.page.goto(target_url, wait_until="domcontentloaded")
        await asyncio.sleep(2)  # Allow page to fully render

    async def reset_chat_context(self) -> None:
        """
        Reset to a fresh chat session:
        1. Click "Home" in left navbar
        2. Ensure "Chat prompt" mode
        3. Click "Chat with models"
        """
        logger.debug(f"Worker {self.worker_id}: Resetting chat context")

        # Click Home button in navigation
        try:
            await self.page.wait_for_selector(
                "//span[contains(@class, 'material-symbols-outlined') and normalize-space()='home']",
                timeout=10000,
            )
            home_button = self.page.locator(
                "//span[contains(@class, 'material-symbols-outlined') and normalize-space()='home']"
            )
            await self.interaction.safe_click(self.page, home_button)
        except Exception:
            # Fallback: sometimes navigating directly to home helps if UI is stuck
            await self.page.goto(self.page.url, wait_until="domcontentloaded")

        await self.interaction.random_action_delay()

        # Wait for page to load
        await asyncio.sleep(1)

        # Look for "Chat with models" button or link
        chat_link = None
        possible_names = [
            "Chat with models",
            "Chat with model",
            "Start chat",
            "New chat",
        ]

        for name in possible_names:
            try:
                chat_link = self.page.get_by_role("link", name=name)
                await chat_link.wait_for(state="visible", timeout=3000)
                break
            except PlaywrightTimeoutError:
                try:
                    chat_link = self.page.get_by_role("button", name=name)
                    await chat_link.wait_for(state="visible", timeout=3000)
                    break
                except PlaywrightTimeoutError:
                    continue

        if chat_link:
            await self.interaction.safe_click(self.page, chat_link)
            await self.interaction.random_action_delay()
        else:
            logger.warning(
                f"Worker {self.worker_id}: Could not find 'Chat with models' button"
            )

    async def select_model(self) -> None:
        """Select the specified model (e.g., "Gemini 3 Pro Preview")."""
        logger.debug(
            f"Worker {self.worker_id}: Selecting model: {self.config.model_name}"
        )
        await asyncio.sleep(1)

        try:
            # Try as button first
            model_button = self.page.get_by_role(
                "button", name=self.config.model_name
            ).first
            await model_button.wait_for(state="visible", timeout=5000)
            await self.interaction.safe_click(self.page, model_button)
        except PlaywrightTimeoutError:
            try:
                model_text = self.page.get_by_text(self.config.model_name, exact=False)
                await model_text.first.wait_for(state="visible", timeout=5000)
                await self.interaction.safe_click(self.page, model_text.first)
            except PlaywrightTimeoutError:
                logger.warning(
                    f"Worker {self.worker_id}: Could not find model: {self.config.model_name}"
                )

        await self.interaction.random_action_delay()

    async def temporary_mode(self) -> None:
        """Ensure the chat is in temporary mode (incognito)."""
        logger.debug(f"Worker {self.worker_id}: Checking temporary mode status")
        try:
            toggle_button = self.page.locator(
                "button[aria-label='Temporary chat toggle']"
            )
            await toggle_button.wait_for(state="visible", timeout=5000)
            class_attr = await toggle_button.get_attribute("class")

            if class_attr and "ms-button-active" in class_attr:
                logger.debug(
                    f"Worker {self.worker_id}: Temporary mode is already active"
                )
            else:
                logger.info(f"Worker {self.worker_id}: Enabling temporary mode")
                await self.interaction.safe_click(self.page, toggle_button)
                await self.interaction.random_action_delay()
        except Exception as e:
            logger.warning(
                f"Worker {self.worker_id}: Failed to toggle temporary mode: {e}"
            )

    async def input_prompt(self, prompt: str) -> None:
        """Type the prompt into the content-editable input area."""
        logger.debug(f"Worker {self.worker_id}: Inputting prompt")
        input_area = None
        possible_labels = [
            "Enter a prompt",
            "Enter prompt",
            "Type a message",
            "Message",
            "Prompt",
        ]

        for label in possible_labels:
            try:
                input_area = self.page.get_by_role("textbox", name=label)
                await input_area.wait_for(state="visible", timeout=3000)
                break
            except PlaywrightTimeoutError:
                continue

        if not input_area:
            try:
                input_area = self.page.locator('[contenteditable="true"]').first
                await input_area.wait_for(state="visible", timeout=3000)
            except PlaywrightTimeoutError:
                raise RuntimeError(
                    f"Worker {self.worker_id}: Could not find input area"
                )

        await self.interaction.human_type(
            self.page, input_area, prompt, clear_first=True
        )
        await self.interaction.random_action_delay()

    async def submit_and_wait(self) -> None:
        logger.debug(f"Worker {self.worker_id}: Submitting prompt")
        run_button = self.page.locator("//button[@aria-label='Run']").first
        await self.interaction.safe_click(self.page, run_button)
        logger.debug(f"Worker {self.worker_id}: Waiting for generation to complete")
        try:
            completion_signal = self.page.locator(
                "button[aria-label='Good response']"
            ).last
            await completion_signal.wait_for(state="visible", timeout=120000)
            logger.debug(
                f"Worker {self.worker_id}: Generation completed (Feedback button detected)"
            )
        except Exception as e:
            logger.warning(
                f"Worker {self.worker_id}: Timeout or error waiting for completion signal: {e}"
            )
        await asyncio.sleep(5)
        content = await self.page.content()
        if content and "reached your rate limit" in content:
            raise RateLimitDetected("Rate limit detected during wait")

    async def scroll_to_latest_response(self) -> None:
        """
        Scrolls to the bottom of the chat interface to ensure the latest response
        is fully rendered and populated in the DOM. This fixes issues with
        virtual scrolling where off-screen text appears empty.
        """
        logger.debug(f"Worker {self.worker_id}: Scrolling to reveal latest response")

        try:
            # Strategy 1: Find the last model turn and explicitly scroll it into view
            model_turns = self.page.locator('div[data-turn-role="Model"]')
            count = await model_turns.count()

            if count > 0:
                last_turn = model_turns.last

                # 1. Standard scroll into view
                await last_turn.scroll_into_view_if_needed()

                # 2. Mouse Wheel Scroll (Stronger trigger for virtual lists)
                # We move the mouse over the element and scroll down
                box = await last_turn.bounding_box()
                if box:
                    # Center mouse on the response
                    await self.page.mouse.move(
                        box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
                    )
                    # Scroll down significantly to ensure bottom is hit
                    await self.page.mouse.wheel(0, 5000)

            # Strategy 2: Keyboard 'End' Press (Backup)
            # This is often the most reliable way to scroll a chat container to the absolute bottom
            await self.page.keyboard.press("End")

            # Allow time for the DOM to update/render after the scroll
            await asyncio.sleep(1.0)

        except Exception as e:
            # Log warning but don't fail the task; extraction might still succeed
            logger.warning(
                f"Worker {self.worker_id}: Warning during scroll attempt: {e}"
            )

    async def extract_response(self) -> Optional[str]:
        """Extract the AI response from the last message in the conversation."""
        logger.debug(f"Worker {self.worker_id}: Extracting response")

        try:
            await asyncio.sleep(1)
            model_turns = self.page.locator('div[data-turn-role="Model"]')

            if await model_turns.count() == 0:
                # Check for rate limit before giving up
                content = await self.page.content()
                if "reached your rate limit" in content:
                    raise RateLimitDetected("Rate limit detected (no model turns)")
                logger.warning(f"Worker {self.worker_id}: No model turns found")
                return None

            last_turn = model_turns.last
            content_container = last_turn.locator(".turn-content")

            try:
                await content_container.wait_for(state="attached", timeout=10000)
            except Exception:
                logger.warning(
                    f"Worker {self.worker_id}: Content container never appeared"
                )
                return None

            # POLLING LOOP
            for _ in range(20):
                response_text = await content_container.inner_text()

                # Check explicitly for Rate Limit message within the response text
                if "reached your rate limit" in response_text:
                    raise RateLimitDetected(
                        "Rate limit message detected in response text"
                    )

                if response_text and len(response_text.strip()) > 0:
                    clean_text = response_text.strip()
                    logger.debug(
                        f"Worker {self.worker_id}: Extracted {len(clean_text)} chars"
                    )
                    return clean_text

                await asyncio.sleep(0.5)

            # Check full page content one last time if extraction failed
            if "reached your rate limit" in await self.page.content():
                raise RateLimitDetected("Rate limit detected in page content")

            logger.warning(
                f"Worker {self.worker_id}: Content container found but text remained empty"
            )
            return None

        except RateLimitDetected:
            raise  # Re-raise to be handled by caller
        except Exception as e:
            logger.error(f"Worker {self.worker_id}: Error extracting response: {e}")
            return None

    async def process_prompt(self, task: PromptTask) -> Optional[ScraperResult]:
        """Complete workflow: reset context, select model, input prompt, submit, extract."""
        try:
            logger.info(f"Worker {self.worker_id}: Processing task {task.id}")
            await self.reset_chat_context()
            await self.temporary_mode()
            await self.select_model()
            await self.input_prompt(task.prompt)
            await self.submit_and_wait()
            await self.scroll_to_latest_response()

            response = await self.extract_response()

            if response:
                result = ScraperResult(key=task.id, value=response)
                logger.info(
                    f"Worker {self.worker_id}: Successfully completed task {task.id}"
                )
                return result
            else:
                logger.error(
                    f"Worker {self.worker_id}: Failed to extract response for task {task.id}"
                )
                return None

        except RateLimitDetected as e:
            # Critical: Allow this specific exception to bubble up to the worker
            raise e
        except Exception as e:
            logger.error(
                f"Worker {self.worker_id}: Error processing task {task.id}: {e}"
            )
            return None
