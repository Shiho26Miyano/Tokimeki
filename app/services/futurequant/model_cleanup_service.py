"""
FutureQuant Trader Model Cleanup Service
Automatically removes old model files after trades are executed
"""
import logging
import os
import glob
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)

class FutureQuantModelCleanupService:
    """Service for automatically cleaning up old model files after trades"""
    
    def __init__(self):
        self.models_dir = Path("models")
        self.cleanup_enabled = True
        self.keep_latest_count = 1  # Keep only the latest model of each type
        self.cleanup_delay_seconds = 5  # Wait 5 seconds after trade before cleanup
        
    async def cleanup_after_trade(self, trade_info: Dict[str, Any]) -> None:
        """Clean up old models after a trade is executed"""
        if not self.cleanup_enabled:
            logger.info("Model cleanup is disabled")
            return
            
        try:
            # Wait a bit to ensure trade is fully processed
            await asyncio.sleep(self.cleanup_delay_seconds)
            
            logger.info(f"Starting model cleanup after trade: {trade_info.get('symbol', 'unknown')}")
            
            # Perform cleanup
            removed_count = await self._cleanup_old_models()
            
            if removed_count > 0:
                logger.info(f"Model cleanup completed: {removed_count} old models removed")
            else:
                logger.info("Model cleanup completed: no old models to remove")
                
        except Exception as e:
            logger.error(f"Error during model cleanup: {str(e)}")
    
    async def _cleanup_old_models(self) -> int:
        """Clean up old model files, keeping only the most recent ones"""
        if not self.models_dir.exists():
            logger.warning("Models directory not found")
            return 0
        
        try:
            # Find all .joblib files
            model_files = list(self.models_dir.glob("*.joblib"))
            
            if not model_files:
                logger.info("No model files found")
                return 0
            
            logger.info(f"Found {len(model_files)} model files")
            
            # Group models by type (symbol_modeltype_horizon)
            model_groups = await self._group_models_by_type(model_files)
            
            if not model_groups:
                logger.info("No valid model groups found")
                return 0
            
            logger.info(f"Grouped into {len(model_groups)} model types")
            
            # Clean up each group
            total_removed = 0
            
            for base_id, models in model_groups.items():
                if len(models) > self.keep_latest_count:
                    # Sort by timestamp (newest first)
                    models.sort(key=lambda x: x['timestamp'], reverse=True)
                    
                    # Keep the newest ones
                    models_to_keep = models[:self.keep_latest_count]
                    models_to_remove = models[self.keep_latest_count:]
                    
                    logger.info(f"{base_id}: Keeping {len(models_to_keep)} newest models")
                    
                    # Remove older models
                    for old_model in models_to_remove:
                        try:
                            os.remove(old_model['file'])
                            logger.info(f"  Removed: {old_model['filename']}")
                            total_removed += 1
                        except OSError as e:
                            logger.error(f"  Error removing {old_model['filename']}: {e}")
                else:
                    logger.info(f"{base_id}: Keeping all {len(models)} models (within limit)")
            
            return total_removed
            
        except Exception as e:
            logger.error(f"Error during model cleanup: {str(e)}")
            return 0
    
    async def _group_models_by_type(self, model_files: List[Path]) -> Dict[str, List[Dict[str, Any]]]:
        """Group model files by their base type"""
        model_groups = {}
        
        for model_file in model_files:
            filename = model_file.name
            
            # Parse filename: ES=F_transformer_0.5m_20250831_224805.joblib
            pattern = r'^(.+)_(\d{8}_\d{6})\.joblib$'
            match = re.match(pattern, filename)
            
            if match:
                base_id = match.group(1)  # e.g., ES=F_transformer_0.5m
                timestamp_str = match.group(2)  # e.g., 20250831_224805
                
                # Parse timestamp
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                    
                    if base_id not in model_groups:
                        model_groups[base_id] = []
                    
                    model_groups[base_id].append({
                        'file': model_file,
                        'timestamp': timestamp,
                        'filename': filename
                    })
                    
                except ValueError:
                    logger.warning(f"Could not parse timestamp from {filename}")
                    continue
            else:
                logger.warning(f"Could not parse filename format: {filename}")
                continue
        
        return model_groups
    
    async def cleanup_by_age(self, days_old: int = 7) -> int:
        """Remove models older than specified days"""
        if not self.models_dir.exists():
            logger.warning("Models directory not found")
            return 0
        
        try:
            cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            
            logger.info(f"Removing models older than {days_old} days...")
            
            model_files = list(self.models_dir.glob("*.joblib"))
            removed_count = 0
            
            for model_file in model_files:
                # Get file modification time
                mtime = model_file.stat().st_mtime
                
                if mtime < cutoff_date:
                    try:
                        os.remove(model_file)
                        logger.info(f"Removed old model: {model_file.name}")
                        removed_count += 1
                    except OSError as e:
                        logger.error(f"Error removing {model_file.name}: {e}")
            
            logger.info(f"Age-based cleanup completed: {removed_count} old models removed")
            return removed_count
            
        except Exception as e:
            logger.error(f"Error during age-based cleanup: {str(e)}")
            return 0
    
    def enable_cleanup(self) -> None:
        """Enable automatic model cleanup"""
        self.cleanup_enabled = True
        logger.info("Model cleanup enabled")
    
    def disable_cleanup(self) -> None:
        """Disable automatic model cleanup"""
        self.cleanup_enabled = False
        logger.info("Model cleanup disabled")
    
    def set_keep_latest_count(self, count: int) -> None:
        """Set how many latest models to keep for each type"""
        if count < 1:
            raise ValueError("Keep count must be at least 1")
        self.keep_latest_count = count
        logger.info(f"Set keep latest count to {count}")
    
    def set_cleanup_delay(self, seconds: int) -> None:
        """Set delay before cleanup after trade execution"""
        if seconds < 0:
            raise ValueError("Cleanup delay cannot be negative")
        self.cleanup_delay_seconds = seconds
        logger.info(f"Set cleanup delay to {seconds} seconds")
    
    async def get_cleanup_status(self) -> Dict[str, Any]:
        """Get current cleanup service status"""
        return {
            "cleanup_enabled": self.cleanup_enabled,
            "keep_latest_count": self.keep_latest_count,
            "cleanup_delay_seconds": self.cleanup_delay_seconds,
            "models_directory": str(self.models_dir),
            "models_directory_exists": self.models_dir.exists()
        }
