import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger('TrellisConfig')

class TrellisConfig:
    """Configuration manager for Trellis ComfyUI integration"""
    
    DEFAULT_CONFIG = {
        "server": {
            "websocket_url": "ws://localhost:5000", #"ws://18.199.134.45:46173"
            "rest_api_url": "http://localhost:8000",
            "timeout_seconds": 60,
            "reconnect_attempts": 3,
            "reconnect_delay_seconds": 2
        },
        "processing": {
            "default_parameters": {
                "seed": 1,
                "sparse_steps": 12,
                "sparse_cfg_strength": 7.5,
                "slat_steps": 12,
                "slat_cfg_strength": 3,
                "simplify": 0.95,
                "texture_size": 1024
            },
            "parameter_presets": {
                "fast": {
                    "sparse_steps": 8,
                    "slat_steps": 8,
                    "texture_size": 512
                },
                "quality": {
                    "sparse_steps": 20,
                    "slat_steps": 16,
                    "texture_size": 2048
                },
                "balanced": {
                    "sparse_steps": 12,
                    "slat_steps": 12,
                    "texture_size": 1024
                }
            }
        },
        "storage": {
            "download_dir": "trellis_downloads",
            "api_download_dir": "trellis_api_downloads",
            "session_dir": "trellis_sessions",
            "metadata_dir": "trellis_metadata",
            "cleanup_temp_files_hours": 24,
            "max_cache_size_mb": 1024
        },
        "logging": {
            "level": "INFO",
            "file": "trellis_comfy.log",
            "max_size_mb": 10,
            "backup_count": 3
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file. If None, will look for
                         config.json in the current directory, then in the parent directory.
        """
        self.config_path = config_path
        self.config = self.DEFAULT_CONFIG.copy()
        
        # Try to load config
        if config_path is None:
            # Try current directory
            if os.path.exists("config.json"):
                self.config_path = "config.json"
            # Try parent directory
            elif os.path.exists(os.path.join(os.path.dirname(__file__), "config.json")):
                self.config_path = os.path.join(os.path.dirname(__file__), "config.json")
        
        if self.config_path and os.path.exists(self.config_path):
            self._load_config()
        else:
            logger.warning(f"Config file not found, using default configuration.")
            self._save_config()  # Save default config for future use
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                loaded_config = json.load(f)
            
            # Merge with defaults (to ensure all keys exist)
            self._deep_update(self.config, loaded_config)
            logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading config from {self.config_path}: {str(e)}")
    
    def _save_config(self) -> None:
        """Save current configuration to file."""
        if not self.config_path:
            self.config_path = "config.json"
            
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config to {self.config_path}: {str(e)}")
    
    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Recursively update a nested dictionary."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation.
        
        Example:
            config.get("server", "websocket_url")
            
        Args:
            *keys: Key path to the desired value
            default: Value to return if the key is not found
            
        Returns:
            The configuration value, or default if not found
        """
        current = self.config
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, value: Any, *keys: str, save: bool = True) -> bool:
        """Set a configuration value using dot notation.
        
        Example:
            config.set("ws://new.url", "server", "websocket_url")
            
        Args:
            value: The value to set
            *keys: Key path to the setting
            save: Whether to save the config to disk after setting
            
        Returns:
            True if successful, False otherwise
        """
        if not keys:
            return False
            
        current = self.config
        try:
            # Navigate to the parent of the target key
            for key in keys[:-1]:
                if key not in current or not isinstance(current[key], dict):
                    current[key] = {}
                current = current[key]
                
            # Set the value
            current[keys[-1]] = value
            
            # Save if requested
            if save:
                self._save_config()
                
            return True
        except Exception as e:
            logger.error(f"Error setting config value: {str(e)}")
            return False
    
    def get_processing_preset(self, preset_name: str) -> Dict[str, Any]:
        """Get a processing parameter preset by name.
        
        Args:
            preset_name: Name of the preset ('fast', 'quality', 'balanced')
            
        Returns:
            Dictionary of parameter values, or default parameters if preset not found
        """
        # Start with default parameters
        preset = self.get("processing", "default_parameters", default={}).copy()
        
        # Update with preset values if the preset exists
        preset_values = self.get("processing", "parameter_presets", preset_name, default={})
        preset.update(preset_values)
        
        return preset
    
    def add_preset(self, name: str, parameters: Dict[str, Any], save: bool = True) -> bool:
        """Add a new processing parameter preset.
        
        Args:
            name: Name of the preset
            parameters: Dictionary of parameter values
            save: Whether to save the config to disk after adding
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current presets
            presets = self.get("processing", "parameter_presets", default={}).copy()
            
            # Add new preset
            presets[name] = parameters
            
            # Update config
            return self.set(presets, "processing", "parameter_presets", save=save)
        except Exception as e:
            logger.error(f"Error adding preset: {str(e)}")
            return False
    
    def get_all_presets(self) -> Dict[str, Dict[str, Any]]:
        """Get all processing parameter presets.
        
        Returns:
            Dictionary of preset names to parameter dictionaries
        """
        return self.get("processing", "parameter_presets", default={})
    
    @property
    def websocket_url(self) -> str:
        """Get the WebSocket server URL."""
        return self.get("server", "websocket_url", default="ws://18.199.134.45:46173")
    
    @property
    def rest_api_url(self) -> str:
        """Get the REST API server URL."""
        return self.get("server", "rest_api_url", default="http://localhost:8000")
    
    @property
    def download_dir(self) -> str:
        """Get the download directory for WebSocket API."""
        return self.get("storage", "download_dir", default="trellis_downloads")
    
    @property
    def api_download_dir(self) -> str:
        """Get the download directory for REST API."""
        return self.get("storage", "api_download_dir", default="trellis_api_downloads")
    
    @property
    def default_parameters(self) -> Dict[str, Any]:
        """Get the default processing parameters."""
        return self.get("processing", "default_parameters", default={})


# Create a global instance for easy access
config = TrellisConfig()

# Configure the logging based on config
log_level = getattr(logging, config.get("logging", "level", default="INFO"), logging.INFO)
log_file = config.get("logging", "file", default="trellis_comfy.log")
max_size = config.get("logging", "max_size_mb", default=10) * 1024 * 1024
backup_count = config.get("logging", "backup_count", default=3)

# Setup rotating file handler
try:
    from logging.handlers import RotatingFileHandler
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create directory for log file if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_size, backupCount=backup_count)
    file_handler.setFormatter(formatter)
    
    # Configure root logger for the package
    package_logger = logging.getLogger('ComfyUI-Trellis')
    package_logger.setLevel(log_level)
    package_logger.addHandler(file_handler)
    
except Exception as e:
    logger.error(f"Error setting up logging: {str(e)}")
