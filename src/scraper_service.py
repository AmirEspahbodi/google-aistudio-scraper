"""
Scraper Service
Encapsulates the business logic for interacting with Google AI Studio.
"""
import asyncio
import time
from typing import Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout
from src.human_interaction import HumanInteractionService
from src.config import config
from src.models import ScraperResult


class AIStudioScraperService:
    """
    Core service for interacting with Google AI Studio.
    Handles navigation, prompt submission, and response extraction.
    """
    
    def __init__(self, page: Page, human_service: HumanInteractionService):
        self.page = page
        self.human = human_service
    
    async def navigate_to_studio(self) -> None:
        """Navigate to Google AI Studio and wait for load."""
        await self.page.goto(config.target_url, wait_until="networkidle")
        await asyncio.sleep(2)  # Additional safety margin
    
    async def reset_to_home(self) -> None:
        """
        Resets the context by navigating to home.
        Critical for starting each prompt with a clean slate.
        """
        try:
            # Click "Home" in left navbar
            home_button = self.page.get_by_role("button", name="Home")
            await self.human.safe_click(self.page, home_button)
            await self.human.random_action_delay()
            
        except Exception as e:
            # If Home button not found, reload page
            await self.page.reload(wait_until="networkidle")
            await asyncio.sleep(1)
    
    async def select_chat_mode(self) -> None:
        """
        Selects 'Chat prompt' mode and navigates to chat interface.
        Uses accessibility tree to avoid brittle selectors.
        """
        try:
            # Look for "Chat prompt" or similar text/button
            # This is site-specific and may need adjustment
            chat_prompt_button = self.page.get_by_text("Chat prompt", exact=False)
            await self.human.safe_click(self.page, chat_prompt_button)
            await self.human.random_action_delay()
            
            # Click "Chat with models" or equivalent
            chat_with_models = self.page.get_by_text("Chat with models", exact=False)
            await self.human.safe_click(self.page, chat_with_models)
            await self.human.random_action_delay()
            
        except Exception as e:
            raise RuntimeError(f"Failed to select chat mode: {str(e)}")
    
    async def select_model(self) -> None:
        """
        Selects the specific model (e.g., "Gemini 3 Pro Preview").
        Uses exact text matching from accessibility tree.
        """
        try:
            # Wait for temporary chat page to load
            await asyncio.sleep(2)
            
            # Click on the model name
            model_selector = self.page.get_by_text(config.model_name, exact=False)
            await self.human.safe_click(self.page, model_selector)
            await self.human.random_action_delay()
            
        except Exception as e:
            raise RuntimeError(f"Failed to select model: {str(e)}")
    
    async def input_prompt(self, prompt: str) -> None:
        """
        Inputs the prompt using human-like typing.
        Targets the contenteditable area.
        """
        try:
            # Find the input area (usually a contenteditable div)
            # Try multiple strategies
            input_area = None
            
            # Strategy 1: Look for contenteditable
            try:
                input_area = self.page.locator('[contenteditable="true"]').first
                await input_area.wait_for(state="visible", timeout=5000)
            except:
                pass
            
            # Strategy 2: Look by role (textbox)
            if not input_area:
                input_area = self.page.get_by_role("textbox").first
            
            # Type the prompt
            await self.human.human_type(self.page, input_area, prompt)
            await self.human.random_action_delay()
            
        except Exception as e:
            raise RuntimeError(f"Failed to input prompt: {str(e)}")
    
    async def submit_prompt(self) -> None:
        """
        Clicks the 'Run' button to submit the prompt.
        Uses accessibility tree (button with name/label).
        """
        try:
            # Look for "Run" button
            run_button = self.page.get_by_role("button", name="Run")
            await self.human.safe_click(self.page, run_button)
            
        except Exception as e:
            raise RuntimeError(f"Failed to submit prompt: {str(e)}")
    
    async def wait_for_completion(self) -> None:
        """
        Waits for AI generation to complete.
        
        Strategy:
        1. Wait for "Stop" button to appear (generation started)
        2. Wait for "Stop" button to disappear OR "Run" button to be enabled (generation finished)
        """
        try:
            # Wait for Stop button to appear (generation started)
            stop_button = self.page.get_by_role("button", name="Stop")
            await stop_button.wait_for(state="visible", timeout=10000)
            
            # Wait for generation to finish
            # Strategy: Wait for Stop button to be hidden
            await stop_button.wait_for(state="hidden", timeout=config.generation_timeout_ms)
            
            # Additional safety: wait a moment for UI to stabilize
            await asyncio.sleep(2)
            
        except PlaywrightTimeout:
            raise RuntimeError("Generation timeout exceeded")
        except Exception as e:
            raise RuntimeError(f"Failed to wait for completion: {str(e)}")
    
    async def extract_response(self) -> str:
        """
        Extracts the AI response from the conversation history.
        
        Strategy:
        - Locate the last message in the conversation
        - Extract innerText from the Markdown container
        """
        try:
            # Wait a moment for content to render
            await asyncio.sleep(1)
            
            # Strategy: Find all message containers, take the last one
            # This is site-specific; adjust selectors as needed
            
            # Try to find by role or common patterns
            messages = await self.page.locator('[role="article"], .message, .response').all()
            
            if not messages:
                # Fallback: get all text content
                content = await self.page.locator('body').inner_text()
                return content[-5000:]  # Last 5000 chars
            
            # Get the last message
            last_message = messages[-1]
            response_text = await last_message.inner_text()
            
            return response_text.strip()
            
        except Exception as e:
            raise RuntimeError(f"Failed to extract response: {str(e)}")
    
    async def process_single_prompt(self, prompt_id: str, prompt: str) -> ScraperResult:
        """
        Complete workflow for processing a single prompt.
        Returns a ScraperResult with success/failure status.
        """
        start_time = time.time()
        
        try:
            # Step 1: Reset to home
            await self.reset_to_home()
            
            # Step 2: Select chat mode
            await self.select_chat_mode()
            
            # Step 3: Select model
            await self.select_model()
            
            # Step 4: Input prompt
            await self.input_prompt(prompt)
            
            # Step 5: Submit
            await self.submit_prompt()
            
            # Step 6: Wait for completion
            await self.wait_for_completion()
            
            # Step 7: Extract response
            response = await self.extract_response()
            
            processing_time = time.time() - start_time
            
            return ScraperResult(
                key=prompt_id,
                value=response,
                success=True,
                processing_time_seconds=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            return ScraperResult(
                key=prompt_id,
                value="",
                success=False,
                error_message=str(e),
                processing_time_seconds=processing_time
            )

