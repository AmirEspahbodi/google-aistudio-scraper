"""
Browser infrastructure layer using Playwright.
Handles all browser interactions following Repository and Adapter patterns.
"""
import asyncio
import logging
from typing import Optional, List
from contextlib import asynccontextmanager
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
    Error as PlaywrightError
)

from config.settings import BrowserConfig, ScraperConfig


logger = logging.getLogger(__name__)


class BrowserConnectionError(Exception):
    """Raised when browser connection fails."""
    pass


class PageInteractionError(Exception):
    """Raised when page interaction fails."""
    pass


class BrowserManager:
    """
    Manages browser lifecycle and connection to existing Chrome instance.
    Implements Singleton pattern for browser instance.
    """
    
    def __init__(self, browser_config: BrowserConfig):
        self._config = browser_config
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        
    async def initialize(self) -> None:
        """Initialize Playwright and connect to existing Chrome instance."""
        try:
            logger.info("Initializing Playwright...")
            self._playwright = await async_playwright().start()
            
            logger.info(f"Connecting to Chrome at: {self._config.chrome_path}")
            self._browser = await self._playwright.chromium.connect_over_cdp(
                f"http://localhost:9222"
            )
            
            # Get the default context (existing user session)
            contexts = self._browser.contexts
            if contexts:
                self._context = contexts[0]
                logger.info("Connected to existing browser context")
            else:
                raise BrowserConnectionError("No existing browser context found")
                
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise BrowserConnectionError(f"Browser initialization failed: {e}")
    
    async def create_page(self) -> Page:
        """Create a new page in the existing context."""
        if not self._context:
            raise BrowserConnectionError("Browser context not initialized")
        
        try:
            page = await self._context.new_page()
            await page.set_viewport_size({
                "width": self._config.viewport_width,
                "height": self._config.viewport_height
            })
            page.set_default_timeout(self._config.timeout)
            logger.debug(f"Created new page: {page}")
            return page
        except Exception as e:
            logger.error(f"Failed to create page: {e}")
            raise BrowserConnectionError(f"Page creation failed: {e}")
    
    async def close(self) -> None:
        """Cleanup resources (does not close the user's Chrome instance)."""
        try:
            if self._playwright:
                await self._playwright.stop()
                logger.info("Playwright stopped")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    @property
    def is_connected(self) -> bool:
        """Check if browser is connected."""
        return self._browser is not None and self._browser.is_connected()


class AIStudioPage:
    """
    Encapsulates all interactions with Google AI Studio page.
    Implements Facade pattern for complex DOM operations.
    """
    
    def __init__(self, page: Page, scraper_config: ScraperConfig):
        self._page = page
        self._config = scraper_config
        self._is_initialized = False
    
    async def navigate_and_initialize(self) -> None:
        """Navigate to AI Studio and ensure page is ready."""
        try:
            logger.info(f"Navigating to {self._config.base_url}")
            await self._page.goto(
                self._config.base_url,
                wait_until="domcontentloaded",
                timeout=60000
            )
            
            # Wait for the main application to load
            await self._page.wait_for_load_state("networkidle", timeout=30000)
            await asyncio.sleep(2)  # Additional buffer for JS initialization
            
            self._is_initialized = True
            logger.info("AI Studio page initialized successfully")
            
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            raise PageInteractionError(f"Failed to initialize AI Studio: {e}")
    
    async def start_new_chat(self) -> None:
        """Reset context by going home and starting a new chat."""
        try:
            # Click Home button
            await self._safe_click(
                self._config.home_button_selector,
                "Home button",
                timeout=10000
            )
            await asyncio.sleep(1)
            
            # Click "New chat" or "Chat with model"
            new_chat_selectors = [
                self._config.new_chat_selector,
                'button:has-text("Chat with model")',
                'a[href*="chat"]'
            ]
            
            for selector in new_chat_selectors:
                try:
                    await self._safe_click(selector, "New chat", timeout=5000)
                    logger.debug("Started new chat session")
                    await asyncio.sleep(1.5)
                    return
                except:
                    continue
            
            logger.warning("Could not find new chat button, continuing anyway")
            
        except Exception as e:
            logger.error(f"Failed to start new chat: {e}")
            raise PageInteractionError(f"Could not start new chat: {e}")
    
    async def select_model(self, model_name: str) -> None:
        """Select the specified AI model."""
        try:
            # Look for model selector button
            model_selectors = [
                'button[aria-label*="model"]',
                'button[aria-label*="Model"]',
                'div[role="button"]:has-text("model")'
            ]
            
            for selector in model_selectors:
                try:
                    await self._safe_click(selector, "Model selector", timeout=5000)
                    await asyncio.sleep(1)
                    
                    # Select the desired model from dropdown
                    model_option = await self._page.wait_for_selector(
                        f'text="{model_name}"',
                        timeout=5000
                    )
                    if model_option:
                        await model_option.click()
                        logger.debug(f"Selected model: {model_name}")
                        await asyncio.sleep(1)
                        return
                except:
                    continue
            
            logger.warning(f"Could not select model {model_name}, using default")
            
        except Exception as e:
            logger.warning(f"Model selection failed (non-critical): {e}")
    
    async def submit_prompt(self, prompt_text: str) -> None:
        """Submit a prompt and wait for response to start."""
        try:
            # Focus and fill the prompt input
            input_selectors = [
                self._config.prompt_input_selector,
                'div[contenteditable="true"]',
                'textarea[placeholder*="prompt"]',
                'div[role="textbox"]'
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    input_element = await self._page.wait_for_selector(
                        selector,
                        timeout=5000
                    )
                    if input_element:
                        break
                except:
                    continue
            
            if not input_element:
                raise PageInteractionError("Could not find prompt input field")
            
            await input_element.click()
            await asyncio.sleep(0.5)
            
            # Clear existing content and type new prompt
            await input_element.fill("")
            await input_element.type(prompt_text, delay=10)
            await asyncio.sleep(0.5)
            
            # Submit the prompt
            submit_selectors = [
                self._config.submit_button_selector,
                'button[aria-label*="Send"]',
                'button[type="submit"]'
            ]
            
            for selector in submit_selectors:
                try:
                    submit_btn = await self._page.wait_for_selector(
                        selector,
                        timeout=3000
                    )
                    if submit_btn:
                        await submit_btn.click()
                        logger.debug("Prompt submitted successfully")
                        await asyncio.sleep(1)
                        return
                except:
                    continue
            
            # Fallback: try pressing Enter
            await input_element.press("Enter")
            logger.debug("Prompt submitted via Enter key")
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Failed to submit prompt: {e}")
            raise PageInteractionError(f"Prompt submission failed: {e}")
    
    async def wait_for_response_completion(self, timeout: int = 300) -> None:
        """Wait for the AI response stream to complete."""
        try:
            # Strategy 1: Wait for Stop button to disappear
            stop_selectors = [
                self._config.stop_button_selector,
                'button[aria-label*="Stop"]',
                'button:has-text("Stop")'
            ]
            
            # First, check if stop button appears (response is streaming)
            for selector in stop_selectors:
                try:
                    await self._page.wait_for_selector(
                        selector,
                        timeout=10000,
                        state="visible"
                    )
                    logger.debug("Response streaming detected")
                    
                    # Now wait for it to disappear (streaming complete)
                    await self._page.wait_for_selector(
                        selector,
                        timeout=timeout * 1000,
                        state="hidden"
                    )
                    logger.debug("Response streaming completed")
                    await asyncio.sleep(2)  # Buffer for DOM update
                    return
                except:
                    continue
            
            # Fallback: wait for network idle
            logger.debug("Using fallback: waiting for network idle")
            await self._page.wait_for_load_state("networkidle", timeout=timeout * 1000)
            await asyncio.sleep(3)
            
        except Exception as e:
            logger.error(f"Timeout waiting for response: {e}")
            raise PageInteractionError(f"Response wait timeout: {e}")
    
    async def extract_response(self) -> str:
        """Extract the AI response from the page."""
        try:
            # Try multiple selectors to find the response
            response_selectors = [
                'div[data-message-role="model"]',
                '.model-response',
                '.response-text',
                'div[class*="response"]',
                'div[class*="message"] >> nth=-1'
            ]
            
            for selector in response_selectors:
                try:
                    elements = await self._page.query_selector_all(selector)
                    if elements:
                        # Get the last (most recent) response
                        last_element = elements[-1]
                        text = await last_element.inner_text()
                        if text and text.strip():
                            logger.debug(f"Extracted response ({len(text)} chars)")
                            return text.strip()
                except:
                    continue
            
            # Ultimate fallback: get all text from visible area
            logger.warning("Using fallback extraction method")
            body_text = await self._page.inner_text("body")
            
            # Try to extract just the response part (very naive approach)
            lines = body_text.split('\n')
            # Return the last substantial block of text
            substantial_lines = [l for l in lines if len(l.strip()) > 50]
            if substantial_lines:
                return substantial_lines[-1].strip()
            
            raise PageInteractionError("Could not find response text")
            
        except Exception as e:
            logger.error(f"Failed to extract response: {e}")
            raise PageInteractionError(f"Response extraction failed: {e}")
    
    async def _safe_click(self, selector: str, element_name: str, timeout: int = 10000) -> None:
        """Safely click an element with retries."""
        try:
            element = await self._page.wait_for_selector(selector, timeout=timeout)
            if element:
                await element.click()
                logger.debug(f"Clicked: {element_name}")
        except Exception as e:
            raise PageInteractionError(f"Could not click {element_name}: {e}")
    
    async def close(self) -> None:
        """Close the page."""
        try:
            if not self._page.is_closed():
                await self._page.close()
                logger.debug("Page closed")
        except Exception as e:
            logger.error(f"Error closing page: {e}")


@asynccontextmanager
async def create_browser_session(browser_config: BrowserConfig):
    """Context manager for browser session lifecycle."""
    manager = BrowserManager(browser_config)
    try:
        await manager.initialize()
        yield manager
    finally:
        await manager.close()