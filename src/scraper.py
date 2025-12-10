"""
Service Layer - Google AI Studio Scraper Implementation
"""
import asyncio
import logging
from typing import Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from src.config import ScraperConfig
from src.models import PromptTask, ScraperResult
from src.interaction import HumanInteractionService

logger = logging.getLogger(__name__)


class GoogleAIStudioScraper:
    """Orchestrates the scraping workflow for Google AI Studio."""
    
    def __init__(self, page: Page, config: ScraperConfig, worker_id: int):
        self.page = page
        self.config = config
        self.worker_id = worker_id
        self.interaction = HumanInteractionService(config)
    
    async def initialize(self) -> None:
        """Navigate to Google AI Studio and prepare the page."""
        logger.info(f"Worker {self.worker_id}: Initializing Google AI Studio")
        
        # Set timeouts
        self.page.set_default_timeout(self.config.page_load_timeout)
        self.page.set_default_navigation_timeout(self.config.navigation_timeout)
        
        # Navigate to base URL
        await self.page.goto(self.config.base_url, wait_until="domcontentloaded")
        await asyncio.sleep(2)  # Allow page to fully render
        
        logger.info(f"Worker {self.worker_id}: Initialized at {self.config.base_url}")
    
    async def reset_chat_context(self) -> None:
        """
        Reset to a fresh chat session:
        1. Click "Home" in left navbar
        2. Ensure "Chat prompt" mode
        3. Click "Chat with models"
        """
        logger.debug(f"Worker {self.worker_id}: Resetting chat context")
        
        # Click Home button in navigation
        # home_button = self.page.get_by_role("button", name="Home")
        await self.page.wait_for_selector("//span[contains(@class, 'material-symbols-outlined') and normalize-space()='home']", timeout=10000)
        home_button = self.page.locator("//span[contains(@class, 'material-symbols-outlined') and normalize-space()='home']")
        await self.interaction.safe_click(self.page, home_button)
        await self.interaction.random_action_delay()
        
        # Wait for page to load
        await asyncio.sleep(1)
        
        # Look for "Chat with models" button or link
        # Try multiple possible selectors from accessibility tree
        chat_link = None
        possible_names = [
            "Chat with models",
            "Chat with model",
            "Start chat",
            "New chat"
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
            logger.warning(f"Worker {self.worker_id}: Could not find 'Chat with models' button")
    
    async def select_model(self) -> None:
        """
        Select the specified model (e.g., "Gemini 3 Pro Preview").
        This assumes we're on a temporary chat page where model can be selected.
        """
        logger.debug(f"Worker {self.worker_id}: Selecting model: {self.config.model_name}")
        
        # Wait a moment for model selector to be available
        await asyncio.sleep(1)
        
        # Try to find and click the model name
        # Models are typically displayed as buttons or clickable text
        try:
            # Try as button first
            model_button = self.page.get_by_role("button", name=self.config.model_name).first
            await model_button.wait_for(state="visible", timeout=5000)
            await self.interaction.safe_click(self.page, model_button)
        except PlaywrightTimeoutError:
            # Try as text/link
            try:
                model_text = self.page.get_by_text(self.config.model_name, exact=False)
                await model_text.first.wait_for(state="visible", timeout=5000)
                await self.interaction.safe_click(self.page, model_text.first)
            except PlaywrightTimeoutError:
                logger.warning(f"Worker {self.worker_id}: Could not find model: {self.config.model_name}")
                # Continue anyway - may already be selected
        
        await self.interaction.random_action_delay()

    async def temporary_mode(self) -> None:
        """
        Ensure the chat is in temporary mode (incognito).
        Checks if the toggle button is active; if not, clicks it.
        """
        logger.debug(f"Worker {self.worker_id}: Checking temporary mode status")
        
        try:
            # Locator for the temporary chat toggle button using the aria-label
            # which is stable across both states.
            toggle_button = self.page.locator("button[aria-label='Temporary chat toggle']")
            
            # Wait for button to be visible to ensure we can read attributes
            await toggle_button.wait_for(state="visible", timeout=5000)
            
            # Get the class attribute
            # Enabled: "... ms-button-active"
            # Disabled: "..." (missing ms-button-active)
            class_attr = await toggle_button.get_attribute("class")
            
            if class_attr and "ms-button-active" in class_attr:
                logger.debug(f"Worker {self.worker_id}: Temporary mode is already active")
            else:
                logger.info(f"Worker {self.worker_id}: Enabling temporary mode")
                await self.interaction.safe_click(self.page, toggle_button)
                await self.interaction.random_action_delay()
                
        except Exception as e:
            # Log specific warning but don't crash the workflow
            logger.warning(f"Worker {self.worker_id}: Failed to toggle temporary mode: {e}")

    async def input_prompt(self, prompt: str) -> None:
        """
        Type the prompt into the content-editable input area.
        Uses human-like character-by-character typing.
        """
        logger.debug(f"Worker {self.worker_id}: Inputting prompt")
        
        # Find the input area using accessibility tree
        # Common patterns: textbox, combobox with "Enter a prompt" or similar
        input_area = None
        possible_labels = [
            "Enter a prompt",
            "Enter prompt",
            "Type a message",
            "Message",
            "Prompt"
        ]
        
        for label in possible_labels:
            try:
                input_area = self.page.get_by_role("textbox", name=label)
                await input_area.wait_for(state="visible", timeout=3000)
                break
            except PlaywrightTimeoutError:
                continue
        
        # Fallback: try to find any editable div with contenteditable
        if not input_area:
            try:
                input_area = self.page.locator('[contenteditable="true"]').first
                await input_area.wait_for(state="visible", timeout=3000)
            except PlaywrightTimeoutError:
                raise RuntimeError(f"Worker {self.worker_id}: Could not find input area")
        
        # Type the prompt with human-like behavior
        await self.interaction.human_type(self.page, input_area, prompt, clear_first=True)
        await self.interaction.random_action_delay()
    
    async def submit_and_wait(self) -> None:
        """
        Click the "Run" button and wait for generation to complete.
        Uses the appearance of the 'Good response' button (thumbs up) 
        as the definitive signal that the stream has finished.
        """
        logger.debug(f"Worker {self.worker_id}: Submitting prompt")
        
        # 1. Click Run
        # Using the existing locator strategy
        run_button = self.page.locator("//button[@aria-label='Run']").first
        await self.interaction.safe_click(self.page, run_button)
        
        logger.debug(f"Worker {self.worker_id}: Waiting for generation to complete")
        
        try:
            # CRITICAL FIX BASED ON HTML ANALYSIS:
            # Instead of waiting for a "Stop" button to hide (which can be flaky),
            # we wait for the "Good response" button to become visible.
            # This button is only present in the "completed" HTML state.
            
            # We target the last instance to ensure we are checking the current turn
            completion_signal = self.page.locator("button[aria-label='Good response']").last
            
            # Increased timeout to 120s to allow for long generations
            await completion_signal.wait_for(state="visible", timeout=120000)
            
            logger.debug(f"Worker {self.worker_id}: Generation completed (Feedback button detected)")
            
        except Exception as e:
            logger.warning(f"Worker {self.worker_id}: Timeout or error waiting for completion signal: {e}")

        await asyncio.sleep(5)
    
    async def extract_response(self) -> Optional[str]:
        """
        Extract the AI response from the last message in the conversation.
        Includes a wait-for-text loop to handle streaming latency and background throttling.
        """
        logger.debug(f"Worker {self.worker_id}: Extracting response")
        
        try:
            # 1. Wait a brief moment for initial rendering
            await asyncio.sleep(1)
            
            # 2. Locate the LAST model turn
            model_turns = self.page.locator('div[data-turn-role="Model"]')
            
            if await model_turns.count() == 0:
                logger.warning(f"Worker {self.worker_id}: No model turns found")
                return None
            
            last_turn = model_turns.last
            
            # 3. Find the content container
            content_container = last_turn.locator('.turn-content')
            
            # 4. Wait for container to be attached
            try:
                await content_container.wait_for(state="attached", timeout=10000)
            except Exception:
                logger.warning(f"Worker {self.worker_id}: Content container never appeared")
                return None

            # 5. POLLING LOOP: Wait for text to actually appear (Fixes empty text bug)
            # We try for up to 10 seconds to get non-empty text
            for _ in range(20):  # 20 attempts * 0.5s = 10 seconds
                response_text = await content_container.inner_text()
                
                if response_text and len(response_text.strip()) > 0:
                    clean_text = response_text.strip()
                    logger.debug(f"Worker {self.worker_id}: Extracted {len(clean_text)} chars")
                    return clean_text
                
                # If empty, wait a bit and try again (waiting for stream to start)
                await asyncio.sleep(0.5)

            # If we reach here, the container was found but text never appeared
            logger.warning(f"Worker {self.worker_id}: Content container found but text remained empty (Stream timeout)")
            return None
                
        except Exception as e:
            logger.error(f"Worker {self.worker_id}: Error extracting response: {e}")
            return None
    
    async def process_prompt(self, task: PromptTask) -> Optional[ScraperResult]:
        """
        Complete workflow: reset context, select model, input prompt, submit, extract.
        
        Args:
            task: The prompt task to process
            
        Returns:
            ScraperResult if successful, None if failed
        """
        try:
            logger.info(f"Worker {self.worker_id}: Processing task {task.id}")
            
            # Step 1: Reset to fresh chat
            await self.reset_chat_context()
            
            # Step 2.5: Ensure chat is in temporary mode
            await self.temporary_mode()
            
            # Step 2: Select model
            await self.select_model()
            
            # Step 3: Input the prompt
            await self.input_prompt(task.prompt)
            
            # Step 4: Submit and wait for completion
            await self.submit_and_wait()
            
            # Step 5: Extract response
            response = await self.extract_response()
            
            if response:
                result = ScraperResult(
                    key=task.id,
                    value=response,
                    worker_id=self.worker_id
                )
                logger.info(f"Worker {self.worker_id}: Successfully completed task {task.id}")
                return result
            else:
                logger.error(f"Worker {self.worker_id}: Failed to extract response for task {task.id}")
                return None
                
        except Exception as e:
            logger.error(f"Worker {self.worker_id}: Error processing task {task.id}: {e}")
            return None