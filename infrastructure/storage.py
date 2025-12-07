"""
Storage infrastructure layer for data persistence.
Implements Repository pattern for data access abstraction.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import aiofiles

from domain.models import Prompt, ProcessingResult
from config.settings import StorageConfig


logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Raised when storage operations fail."""
    pass


class PromptRepository:
    """
    Repository for loading prompts from JSON file.
    Abstracts data access details from business logic.
    """
    
    def __init__(self, storage_config: StorageConfig):
        self._config = storage_config
    
    async def load_all(self) -> List[Prompt]:
        """Load all prompts from the input JSON file."""
        try:
            if not self._config.input_path.exists():
                raise StorageError(
                    f"Input file not found: {self._config.input_path}"
                )
            
            logger.info(f"Loading prompts from: {self._config.input_path}")
            
            async with aiofiles.open(self._config.input_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)
            
            prompts = []
            if isinstance(data, list):
                for item in data:
                    try:
                        prompt = Prompt(
                            id=str(item.get('id', '')),
                            prompt=str(item.get('prompt', ''))
                        )
                        prompts.append(prompt)
                    except ValueError as e:
                        logger.warning(f"Skipping invalid prompt: {e}")
                        continue
            else:
                raise StorageError("Input file must contain a JSON array")
            
            logger.info(f"Loaded {len(prompts)} prompts successfully")
            return prompts
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in input file: {e}")
            raise StorageError(f"Failed to parse JSON: {e}")
        except Exception as e:
            logger.error(f"Failed to load prompts: {e}")
            raise StorageError(f"Error loading prompts: {e}")


class ResultRepository:
    """
    Repository for saving processing results to JSON file.
    Handles incremental saves and final result compilation.
    """
    
    def __init__(self, storage_config: StorageConfig):
        self._config = storage_config
        self._results_cache: List[Dict[str, Any]] = []
    
    def add_result(self, result: ProcessingResult) -> None:
        """Add a result to the cache (synchronous operation)."""
        result_dict = {
            "key": result.prompt_id,
            "value": result.response if result.response else ""
        }
        self._results_cache.append(result_dict)
        logger.debug(f"Cached result for prompt: {result.prompt_id}")
    
    async def save_batch(self, results: List[ProcessingResult]) -> None:
        """Save a batch of results incrementally."""
        try:
            for result in results:
                if result.response:  # Only save successful results
                    self.add_result(result)
            
            logger.info(f"Batch saved, total cached results: {len(self._results_cache)}")
            
        except Exception as e:
            logger.error(f"Failed to save batch: {e}")
            raise StorageError(f"Batch save failed: {e}")
    
    async def save_final_results(self, all_results: List[ProcessingResult]) -> None:
        """Save all results to the final output file."""
        try:
            # Ensure all results are in cache
            for result in all_results:
                if result.response and not any(
                    r['key'] == result.prompt_id for r in self._results_cache
                ):
                    self.add_result(result)
            
            # Sort results by prompt ID for consistency
            sorted_results = sorted(self._results_cache, key=lambda x: x['key'])
            
            logger.info(f"Saving {len(sorted_results)} results to: {self._config.output_path}")
            
            async with aiofiles.open(
                self._config.output_path,
                'w',
                encoding='utf-8'
            ) as f:
                json_content = json.dumps(sorted_results, indent=2, ensure_ascii=False)
                await f.write(json_content)
            
            logger.info("Final results saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save final results: {e}")
            raise StorageError(f"Final save failed: {e}")
    
    async def save_metrics(self, metrics: Dict[str, Any]) -> None:
        """Save processing metrics to a separate file."""
        try:
            metrics_path = self._config.base_dir / "scraper_metrics.json"
            
            async with aiofiles.open(metrics_path, 'w', encoding='utf-8') as f:
                json_content = json.dumps(metrics, indent=2, ensure_ascii=False)
                await f.write(json_content)
            
            logger.info(f"Metrics saved to: {metrics_path}")
            
        except Exception as e:
            logger.warning(f"Failed to save metrics: {e}")


class BackupManager:
    """Manages backup operations for data safety."""
    
    def __init__(self, storage_config: StorageConfig):
        self._config = storage_config
    
    async def create_backup(self, file_path: Path) -> None:
        """Create a timestamped backup of a file."""
        try:
            if not file_path.exists():
                return
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = file_path.with_suffix(f'.{timestamp}.backup.json')
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as src:
                content = await src.read()
            
            async with aiofiles.open(backup_path, 'w', encoding='utf-8') as dst:
                await dst.write(content)
            
            logger.info(f"Backup created: {backup_path}")
            
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
    
    async def cleanup_old_backups(self, max_backups: int = 5) -> None:
        """Remove old backup files, keeping only the most recent ones."""
        try:
            backup_pattern = "*.backup.json"
            backups = sorted(
                self._config.base_dir.glob(backup_pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            for old_backup in backups[max_backups:]:
                old_backup.unlink()
                logger.debug(f"Removed old backup: {old_backup}")
                
        except Exception as e:
            logger.warning(f"Failed to cleanup backups: {e}")