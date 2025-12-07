"""
Main entry point for Google AI Studio Scraper.
Implements Dependency Injection and application bootstrap.
"""
import asyncio
import logging
import sys
from pathlib import Path

from config.settings import AppConfig, config
from infrastructure.browser import BrowserManager, create_browser_session
from infrastructure.storage import (
    PromptRepository,
    ResultRepository,
    BackupManager
)
from services.scraper_service import ScraperService, HealthChecker
from use_cases.batch_processor import BatchProcessor


def setup_logging(config: AppConfig) -> None:
    """
    Configure logging with both file and console handlers.
    Implements comprehensive logging strategy.
    """
    log_level = logging.DEBUG if config.debug_mode else logging.INFO
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handler (detailed)
    file_handler = logging.FileHandler(
        config.storage.log_path,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler (simpler)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Suppress verbose third-party loggers
    logging.getLogger('playwright').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)


class Application:
    """
    Main application class implementing Composition Root pattern.
    Handles dependency injection and lifecycle management.
    """
    
    def __init__(self, config: AppConfig):
        self._config = config
        self._logger = logging.getLogger(__name__)
    
    async def run(self) -> int:
        """
        Main application entry point.
        Returns exit code (0 for success, 1 for failure).
        """
        try:
            self._logger.info("Initializing Google AI Studio Scraper...")
            
            # Validate prerequisites
            self._validate_prerequisites()
            
            # Initialize browser connection
            async with create_browser_session(self._config.browser) as browser_manager:
                
                # Create dependencies
                scraper_service = ScraperService(
                    browser_manager=browser_manager,
                    scraper_config=self._config.scraper
                )
                
                prompt_repo = PromptRepository(self._config.storage)
                result_repo = ResultRepository(self._config.storage)
                backup_manager = BackupManager(self._config.storage)
                
                # Create and execute use case
                batch_processor = BatchProcessor(
                    scraper_service=scraper_service,
                    prompt_repo=prompt_repo,
                    result_repo=result_repo,
                    backup_manager=backup_manager,
                    config=self._config
                )
                
                # Execute batch processing
                metrics = await batch_processor.execute()
                
                # Report final status
                if metrics.failed == 0:
                    self._logger.info("✓ All prompts processed successfully!")
                    return 0
                else:
                    self._logger.warning(
                        f"⚠ Processing completed with {metrics.failed} failures"
                    )
                    return 0 if metrics.successful > 0 else 1
                    
        except KeyboardInterrupt:
            self._logger.info("Process interrupted by user")
            return 1
        except Exception as e:
            self._logger.error(f"Fatal error: {e}", exc_info=True)
            return 1
    
    def _validate_prerequisites(self) -> None:
        """Validate that all prerequisites are met."""
        # Check input file exists
        if not self._config.storage.input_path.exists():
            raise FileNotFoundError(
                f"Input file not found: {self._config.storage.input_path}\n"
                f"Please create '_0prompts.json' with your prompts."
            )
        
        self._logger.info("✓ Prerequisites validated")
        self._logger.info(
            f"Input file: {self._config.storage.input_path} "
            f"({self._config.storage.input_path.stat().st_size} bytes)"
        )
        self._logger.info(f"Output file: {self._config.storage.output_path}")
        
        # Log configuration
        self._logger.info(
            f"Concurrent pages: {self._config.scraper.concurrent_pages}"
        )
        self._logger.info(f"Model: {self._config.scraper.model_name}")


async def async_main() -> int:
    """Async main function."""
    setup_logging(config)
    app = Application(config)
    return await app.run()


def main() -> None:
    """
    Synchronous entry point for the application.
    Sets up event loop and runs async main.
    """
    print("=" * 70)
    print("    Google AI Studio Scraper - Production Ready Edition")
    print("=" * 70)
    print()
    
    # Check for Chrome debugging port instruction
    print("IMPORTANT: Ensure Chrome is running with remote debugging enabled:")
    print('  chrome.exe --remote-debugging-port=9222 --user-data-dir="C:/ChromeDebug"')
    print()
    print("Starting in 3 seconds...")
    print()
    
    import time
    time.sleep(3)
    
    # Run the async application
    try:
        if sys.platform == 'win32':
            # Use ProactorEventLoop on Windows for better compatibility
            asyncio.set_event_loop_policy(
                asyncio.WindowsProactorEventLoopPolicy()
            )
        
        exit_code = asyncio.run(async_main())
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"\n✗ Fatal Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()