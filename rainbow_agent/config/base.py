"""
Base configuration manager for Rainbow Agent.

This module provides the ConfigManager class for loading and accessing configuration.
"""
import os
from typing import Dict, Any, Optional, List
from .schema import Config
from .loaders import load_env_config, load_file_config


class ConfigManager:
    """Configuration manager for Rainbow Agent."""
    
    def __init__(self):
        """Initialize the configuration manager."""
        self._config = None
        self._config_sources: List[str] = []
    
    def load(self, 
             env_file: Optional[str] = None,
             config_file: Optional[str] = None) -> Config:
        """
        Load configuration from environment and optionally a config file.
        
        Args:
            env_file: Path to .env file. If None, tries to find .env in default locations.
            config_file: Path to configuration file (JSON or YAML).
            
        Returns:
            Validated configuration object.
        """
        # Track configuration sources for debugging
        self._config_sources = []
        
        # Start with environment variables
        config_data = load_env_config(env_file)
        self._config_sources.append(f"Environment variables{f' from {env_file}' if env_file else ''}")
        
        # Override with file config if provided
        if config_file:
            file_config = load_file_config(config_file)
            self._deep_update(config_data, file_config)
            self._config_sources.append(f"Configuration file: {config_file}")
        
        # Create and validate the configuration
        self._config = Config(**config_data)
        return self._config
    
    @property
    def config(self) -> Config:
        """
        Get the current configuration.
        
        Returns:
            Current configuration object.
        """
        if self._config is None:
            return self.load()
        return self._config
    
    @property
    def sources(self) -> List[str]:
        """
        Get the configuration sources used.
        
        Returns:
            List of configuration source descriptions.
        """
        return self._config_sources
    
    def _deep_update(self, d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively update a dictionary.
        
        Args:
            d: Dictionary to update.
            u: Dictionary with updates.
            
        Returns:
            Updated dictionary.
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._deep_update(d[k], v)
            else:
                d[k] = v
        return d
