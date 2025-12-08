"""
Utility Functions - Helper methods for common operations
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import aiofiles

logger = logging.getLogger(__name__)


class PromptLoader:
    """Utility class for loading prompts from various sources."""
    
    @staticmethod
    async def from_json_file(filepath: Path) -> List[Dict[str, str]]:
        """
        Load prompts from a JSON file.
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            List of prompt dictionaries
            
        Example JSON format:
            [
                {"id": "1", "prompt": "Your prompt here"},
                {"id": "2", "prompt": "Another prompt"}
            ]
        """
        logger.info(f"Loading prompts from {filepath}")
        
        async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
            content = await f.read()
            prompts = json.loads(content)
        
        logger.info(f"Loaded {len(prompts)} prompts from {filepath}")
        return prompts
    
    @staticmethod
    async def from_text_file(filepath: Path) -> List[Dict[str, str]]:
        """
        Load prompts from a text file (one prompt per line).
        
        Args:
            filepath: Path to text file
            
        Returns:
            List of prompt dictionaries with auto-generated IDs
        """
        logger.info(f"Loading prompts from {filepath}")
        
        prompts = []
        async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
            async for i, line in enumerate(f):
                line = line.strip()
                if line:  # Skip empty lines
                    prompts.append({
                        "id": f"prompt_{i+1:03d}",
                        "prompt": line
                    })
        
        logger.info(f"Loaded {len(prompts)} prompts from {filepath}")
        return prompts
    
    @staticmethod
    def from_list(prompts: List[str]) -> List[Dict[str, str]]:
        """
        Convert a list of strings to prompt dictionaries.
        
        Args:
            prompts: List of prompt strings
            
        Returns:
            List of prompt dictionaries with auto-generated IDs
        """
        return [
            {"id": f"prompt_{i+1:03d}", "prompt": prompt}
            for i, prompt in enumerate(prompts)
        ]


class ResultExporter:
    """Utility class for exporting results to various formats."""
    
    @staticmethod
    async def to_json(
        results: List[Any], 
        filepath: Path,
        pretty: bool = True
    ) -> None:
        """
        Export results to JSON file.
        
        Args:
            results: List of ScraperResult objects
            filepath: Output file path
            pretty: Whether to format with indentation
        """
        logger.info(f"Exporting {len(results)} results to {filepath}")
        
        # Convert to JSON-serializable format
        data = [
            {
                "key": r.key,
                "value": r.value,
                "timestamp": r.timestamp.isoformat(),
                "worker_id": r.worker_id
            }
            for r in results
        ]
        
        indent = 2 if pretty else None
        json_str = json.dumps(data, indent=indent, ensure_ascii=False)
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(json_str)
        
        logger.info(f"Results exported to {filepath}")
    
    @staticmethod
    async def to_csv(results: List[Any], filepath: Path) -> None:
        """
        Export results to CSV file.
        
        Args:
            results: List of ScraperResult objects
            filepath: Output file path
        """
        logger.info(f"Exporting {len(results)} results to {filepath}")
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8', newline='') as f:
            # Write header
            await f.write("id,prompt_response,timestamp,worker_id\n")
            
            # Write data
            for r in results:
                # Escape quotes in value
                value = r.value.replace('"', '""')
                row = f'"{r.key}","{value}","{r.timestamp.isoformat()}",{r.worker_id}\n'
                await f.write(row)
        
        logger.info(f"Results exported to {filepath}")
    
    @staticmethod
    async def to_markdown(results: List[Any], filepath: Path) -> None:
        """
        Export results to Markdown file.
        
        Args:
            results: List of ScraperResult objects
            filepath: Output file path
        """
        logger.info(f"Exporting {len(results)} results to {filepath}")
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            # Write header
            await f.write("# Google AI Studio Scraper Results\n\n")
            await f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            await f.write(f"Total Results: {len(results)}\n\n")
            await f.write("---\n\n")
            
            # Write each result
            for i, r in enumerate(results, 1):
                await f.write(f"## Result {i}: {r.key}\n\n")
                await f.write(f"**Timestamp:** {r.timestamp.isoformat()}\n\n")
                await f.write(f"**Worker:** {r.worker_id}\n\n")
                await f.write(f"**Response:**\n\n")
                await f.write(f"{r.value}\n\n")
                await f.write("---\n\n")
        
        logger.info(f"Results exported to {filepath}")


class PathValidator:
    """Utility class for validating and finding system paths."""
    
    @staticmethod
    def find_chrome_executable() -> Path:
        """
        Attempt to find Chrome executable on the system.
        
        Returns:
            Path to Chrome executable
            
        Raises:
            FileNotFoundError: If Chrome cannot be found
        """
        import platform
        import os
        
        system = platform.system()
        possible_paths = []
        
        if system == "Windows":
            possible_paths = [
                Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
                Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
                Path(os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")),
            ]
        elif system == "Darwin":  # macOS
            possible_paths = [
                Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            ]
        elif system == "Linux":
            possible_paths = [
                Path("/usr/bin/google-chrome"),
                Path("/usr/bin/google-chrome-stable"),
                Path("/usr/bin/chromium"),
                Path("/usr/bin/chromium-browser"),
            ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Found Chrome at: {path}")
                return path
        
        raise FileNotFoundError(
            f"Could not find Chrome executable for {system}. "
            f"Please specify chrome_executable_path manually."
        )
    
    @staticmethod
    def find_chrome_user_data() -> Path:
        """
        Attempt to find Chrome User Data directory.
        
        Returns:
            Path to Chrome User Data directory
            
        Raises:
            FileNotFoundError: If directory cannot be found
        """
        import platform
        import os
        
        system = platform.system()
        possible_paths = []
        
        if system == "Windows":
            possible_paths = [
                Path(os.path.expandvars(r"C:\selenium\ChromeProfile")),
            ]
        elif system == "Darwin":  # macOS
            possible_paths = [
                Path.home() / "Library/Application Support/Google/Chrome",
            ]
        elif system == "Linux":
            possible_paths = [
                Path.home() / ".config/google-chrome",
                Path.home() / ".config/chromium",
            ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Found Chrome User Data at: {path}")
                return path
        
        raise FileNotFoundError(
            f"Could not find Chrome User Data directory for {system}. "
            f"Please specify user_data_dir manually."
        )


class StatsCalculator:
    """Utility class for calculating scraping statistics."""
    
    @staticmethod
    def calculate_success_rate(total: int, successful: int) -> float:
        """Calculate success rate percentage."""
        if total == 0:
            return 0.0
        return (successful / total) * 100
    
    @staticmethod
    def calculate_average_time(total_time: float, count: int) -> float:
        """Calculate average processing time."""
        if count == 0:
            return 0.0
        return total_time / count
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.2f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.2f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.2f}h"
    
    @staticmethod
    def generate_summary(worker_stats: List[Any]) -> Dict[str, Any]:
        """
        Generate summary statistics from worker stats.
        
        Args:
            worker_stats: List of WorkerStats objects
            
        Returns:
            Dictionary with summary statistics
        """
        total_completed = sum(s.tasks_completed for s in worker_stats)
        total_failed = sum(s.tasks_failed for s in worker_stats)
        total_time = sum(s.total_processing_time for s in worker_stats)
        total_tasks = total_completed + total_failed
        
        return {
            "total_tasks": total_tasks,
            "successful": total_completed,
            "failed": total_failed,
            "success_rate": StatsCalculator.calculate_success_rate(
                total_tasks, total_completed
            ),
            "total_processing_time": total_time,
            "average_time_per_task": StatsCalculator.calculate_average_time(
                total_time, total_completed
            ),
            "formatted_total_time": StatsCalculator.format_duration(total_time),
            "workers_used": len(worker_stats)
        }


# Convenience functions for quick access
async def load_prompts_from_json(filepath: str) -> List[Dict[str, str]]:
    """Quick function to load prompts from JSON file."""
    return await PromptLoader.from_json_file(Path(filepath))


async def load_prompts_from_text(filepath: str) -> List[Dict[str, str]]:
    """Quick function to load prompts from text file."""
    return await PromptLoader.from_text_file(Path(filepath))


async def export_results_json(results: List[Any], filepath: str) -> None:
    """Quick function to export results to JSON."""
    await ResultExporter.to_json(results, Path(filepath))


async def export_results_csv(results: List[Any], filepath: str) -> None:
    """Quick function to export results to CSV."""
    await ResultExporter.to_csv(results, Path(filepath))


async def export_results_markdown(results: List[Any], filepath: str) -> None:
    """Quick function to export results to Markdown."""
    await ResultExporter.to_markdown(results, Path(filepath))