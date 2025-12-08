"""
Main Entry Point
Configures the scraper and starts the orchestration.
"""
import asyncio
from pathlib import Path
from src.models import PromptTask
from src.orchestrator import ScraperOrchestrator
from src.config import config


async def main():
    """
    Main function to run the scraper.
    """
    print("=" * 80)
    print("Google AI Studio Advanced Scraper")
    print("=" * 80)
    
    # IMPORTANT: Update these paths before running!
    print("\n⚠️  CONFIGURATION CHECK:")
    print(f"Chrome Path: {config.chrome_executable_path}")
    print(f"User Data:   {config.user_data_dir}")
    print(f"Workers:     {config.num_workers}")
    print(f"Model:       {config.model_name}")
    
    # Example prompts (replace with your actual prompts)
    prompts = [
        PromptTask(id="prompt_1", prompt="What is the capital of France?"),
        PromptTask(id="prompt_2", prompt="Explain quantum computing in simple terms."),
        PromptTask(id="prompt_3", prompt="Write a haiku about technology."),
        PromptTask(id="prompt_4", prompt="What are the benefits of async programming?"),
        PromptTask(id="prompt_5", prompt="Describe the architecture of a modern web scraper."),
    ]
    
    print(f"\n📋 Loaded {len(prompts)} prompts")
    print("\n🚀 Starting scraper...\n")
    
    # Create and run orchestrator
    orchestrator = ScraperOrchestrator(prompts)
    metrics = await orchestrator.run()
    
    # Save results
    orchestrator.save_results()
    
    # Print summary
    print("\n" + "=" * 80)
    print("SCRAPING COMPLETE")
    print("=" * 80)
    print(f"Total Prompts:  {metrics.total_prompts}")
    print(f"Successful:     {metrics.successful}")
    print(f"Failed:         {metrics.failed}")
    print(f"Total Time:     {metrics.total_time_seconds:.2f}s")
    print(f"Avg Time/Prompt: {metrics.total_time_seconds/metrics.total_prompts:.2f}s")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())