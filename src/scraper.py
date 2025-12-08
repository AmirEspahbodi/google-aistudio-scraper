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
            model_button = self.page.get_by_role("button", name=self.config.model_name)[0]
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
        Monitors UI state changes to detect completion.
        """
        logger.debug(f"Worker {self.worker_id}: Submitting prompt")
        
        # Find and click the Run button
        run_button = self.page.get_by_role("button", name="Run")
        await self.interaction.safe_click(self.page, run_button)
        
        # Wait for generation to start (Stop button appears)
        logger.debug(f"Worker {self.worker_id}: Waiting for generation to start")
        stop_button = self.page.get_by_role("button", name="Stop")
        
        try:
            await stop_button.wait_for(state="visible", timeout=10000)
            logger.debug(f"Worker {self.worker_id}: Generation started")
        except PlaywrightTimeoutError:
            logger.warning(f"Worker {self.worker_id}: Stop button did not appear")
        
        # Wait for generation to complete (Stop button disappears or Run button re-enables)
        logger.debug(f"Worker {self.worker_id}: Waiting for generation to complete")
        
        # Poll for completion with timeout
        max_wait = 120  # 2 minutes max
        poll_interval = 1
        elapsed = 0
        
        while elapsed < max_wait:
            # Check if Stop button is hidden
            try:
                is_stop_hidden = not await stop_button.is_visible()
                if is_stop_hidden:
                    logger.debug(f"Worker {self.worker_id}: Generation completed (Stop hidden)")
                    break
            except Exception:
                pass
            
            # Check if Run button is enabled
            try:
                is_run_enabled = await run_button.is_enabled()
                if is_run_enabled:
                    logger.debug(f"Worker {self.worker_id}: Generation completed (Run enabled)")
                    break
            except Exception:
                pass
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        if elapsed >= max_wait:
            logger.warning(f"Worker {self.worker_id}: Timeout waiting for completion")
        
        # Additional buffer to ensure rendering is complete
        await asyncio.sleep(2)
    
    async def extract_response(self) -> Optional[str]:
        """
        Extract the AI response from the last message in the conversation.
        Returns the innerText of the response container.
        """
        logger.debug(f"Worker {self.worker_id}: Extracting response")
        
        # Wait a moment for content to render
        await asyncio.sleep(1)
        
        # Try to find response content
        # Responses are typically in elements with role="article" or similar
        try:
            # Look for the last message that's not from the user
            # This is heuristic-based since Google's structure may vary
            
            # Try finding by common patterns
            response_selectors = [
                '[data-test-id*="response"]',
                '[data-test-id*="message"]',
                '.response-content',
                '.model-response',
            ]
            
            # Fallback: get all text content from main area
            main_content = self.page.locator('main')
            text = await main_content.inner_text()
            
            # Basic extraction: get everything after our prompt
            # This is a simplified approach - in production, you'd want more robust parsing
            lines = text.split('\n')
            
            # Find lines that look like responses (contain substantial text)
            response_lines = [line.strip() for line in lines if len(line.strip()) > 20]
            
            if response_lines:
                # Take the last substantial text block as the response
                response = response_lines[-1]
                logger.debug(f"Worker {self.worker_id}: Extracted {len(response)} chars")
                return response
            else:
                logger.warning(f"Worker {self.worker_id}: No response content found")
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