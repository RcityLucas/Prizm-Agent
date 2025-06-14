"""
Configuration system module for Rainbow Agent.

This module provides a centralized configuration system for the Rainbow Agent project.
It loads configuration from environment variables, .env files, and optionally
configuration files, and provides a validated configuration object.
"""
from .base import ConfigManager
from .schema import Config

# Create a singleton instance
_config_manager = ConfigManager()

# Export the main functions and objects
def load_config(env_file=None, config_file=None) -> Config:
    """
    Load configuration from environment and optionally a config file.
    
    Args:
        env_file: Path to .env file. If None, tries to find .env in default locations.
        config_file: Path to configuration file (JSON or YAML).
        
    Returns:
        Validated configuration object.
    """
    return _config_manager.load(env_file, config_file)

def get_config() -> Config:
    """
    Get the current configuration.
    
    Returns:
        Current configuration object.
    """
    return _config_manager.config

# For convenience, also export the current configuration
config = get_config()
