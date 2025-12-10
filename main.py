"""
Main Application Entry Point
"""
import asyncio
import logging
import sys
from pathlib import Path
from src.config import AppConfig, BrowserConfig, ScraperConfig
from src.orchestrator import ScraperOrchestrator
from src.utils import load_prompts_from_json, IncrementalJSONSaver

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

async def main():
    """Main application workflow."""
    logger.info("=" * 80)
    logger.info("Google AI Studio Scraper - Advanced Edition")
    logger.info("=" * 80)
    
    try:
        # 1. Initialize Configuration
        config = AppConfig(
            browser=BrowserConfig(
                # Update these paths for your environment
                chrome_executable_path=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
                user_data_dir=Path(r"C:\selenium\ChromeProfile"),
                headless=False
            ),
            scraper=ScraperConfig(
                model_name="Gemini 3 Pro Preview",
                max_workers=1,
            ),
            output_file=Path("final_result.json")
        )
        
        # 2. Load Prompts from JSON file
        prompts_file = Path("prompts.json")
        if not prompts_file.exists():
            logger.error(f"❌ Prompts file not found: {prompts_file}")
            logger.info("Please run 'python setup.py' to generate sample files or create prompts.json manually.")
            return 1
            
        all_prompts = await load_prompts_from_json(prompts_file)
        
        # 3. Resume Logic: Filter out already completed prompts
        saver = IncrementalJSONSaver(config.output_file)
        processed_keys = saver.get_existing_keys()
        
        prompts_to_run = []
        for p in all_prompts:
            p_id = p.get("id")
            if p_id and p_id not in processed_keys:
                prompts_to_run.append(p)
            elif not p_id:
                # If prompt has no ID, we can't reliably check if it's done, so we run it
                logger.warning(f"Prompt without ID found: {p.get('prompt')[:20]}.")
                # prompts_to_run.append(p)

        # 4. Log Statistics
        total_count = len(all_prompts)
        skipped_count = total_count - len(prompts_to_run)
        
        logger.info(f"📊 Job Statistics:")
        logger.info(f"   - Total Prompts: {total_count}")
        logger.info(f"   - Already Done:  {skipped_count}")
        logger.info(f"   - Remaining:     {len(prompts_to_run)}")
        
        if not prompts_to_run:
            logger.info("✅ All prompts have been processed. Nothing to do!")
            return 0

        # 5. Run Orchestrator
        orchestrator = ScraperOrchestrator(config)
        
        # Note: We don't need to save results at the end anymore because 
        # orchestrator handles incremental saving via IncrementalJSONSaver
        await orchestrator.run(prompts_to_run)
        
        return 0
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)