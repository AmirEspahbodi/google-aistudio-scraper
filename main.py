"""
Main Application Entry Point
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List
import aiofiles
from src.config import AppConfig, BrowserConfig, ScraperConfig
from src.orchestrator import ScraperOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scraper.log')
    ]
)

logger = logging.getLogger(__name__)


async def load_sample_prompts() -> List[dict]:
    """Load sample prompts for demonstration."""
    return [
        {
            "id": "prompt_1",
            "prompt": "Explain quantum entanglement in simple terms."
        },
        {
            "id": "prompt_2",
            "prompt": "What are the key differences between Python and JavaScript?"
        },
        {
            "id": "prompt_3",
            "prompt": "Write a short poem about artificial intelligence."
        },
        {
            "id": "prompt_4",
            "prompt": "How does photosynthesis work?"
        },
        {
            "id": "prompt_5",
            "prompt": "Explain the concept of machine learning to a 10-year-old."
        }
    ]


async def save_results(results: List[dict], output_file: Path) -> None:
    """
    Save results to JSON file using async I/O.
    
    Args:
        results: List of result dictionaries
        output_file: Path to output file
    """
    logger.info(f"Saving {len(results)} results to {output_file}")
    
    # Convert results to JSON-serializable format
    output_data = [
        {
            "key": r.key,
            "value": r.value,
            "timestamp": r.timestamp.isoformat(),
            "worker_id": r.worker_id
        }
        for r in results
    ]
    
    # Write to file asynchronously
    async with aiofiles.open(output_file, mode='w', encoding='utf-8') as f:
        await f.write(json.dumps(output_data, indent=2, ensure_ascii=False))
    
    logger.info(f"Results saved successfully to {output_file}")


async def main():
    """Main application workflow."""
    logger.info("=" * 80)
    logger.info("Google AI Studio Scraper - Starting")
    logger.info("=" * 80)
    
    try:
        # Initialize configuration
        # NOTE: Update these paths to match your system
        config = AppConfig(
            browser=BrowserConfig(
                chrome_executable_path=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
                user_data_dir=Path(r"C:\selenium\ChromeProfile"),
                headless=False  # Set to True for headless mode
            ),
            scraper=ScraperConfig(
                model_name="Gemini 3 Pro Preview",
                max_workers=3,
                typing_delay_min_ms=50,
                typing_delay_max_ms=150,
            ),
            output_file=Path("final_result.json")
        )
        
        logger.info(f"Configuration loaded:")
        logger.info(f"  - Chrome: {config.browser.chrome_executable_path}")
        logger.info(f"  - User Data: {config.browser.user_data_dir}")
        logger.info(f"  - Model: {config.scraper.model_name}")
        logger.info(f"  - Workers: {config.scraper.max_workers}")
        logger.info(f"  - Output: {config.output_file}")
        
        # Load prompts
        prompts = await load_sample_prompts()
        logger.info(f"Loaded {len(prompts)} prompts")
        
        # Create orchestrator and run
        orchestrator = ScraperOrchestrator(config)
        results = await orchestrator.run(prompts)
        
        # Save results
        await save_results(results, config.output_file)
        
        # Print summary
        logger.info("=" * 80)
        logger.info("Scraping Summary:")
        logger.info(f"  - Total prompts: {len(prompts)}")
        logger.info(f"  - Successful: {len(results)}")
        logger.info(f"  - Failed: {len(prompts) - len(results)}")
        logger.info(f"  - Output file: {config.output_file}")
        logger.info("=" * 80)
        
        return 0
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)