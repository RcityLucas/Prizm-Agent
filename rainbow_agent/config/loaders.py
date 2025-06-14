"""
Configuration loaders for Rainbow Agent.

This module provides functions to load configuration from environment variables,
.env files, and configuration files.
"""
import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv


def load_env_config(env_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from environment variables and .env file.
    
    Args:
        env_file: Path to .env file. If None, tries to find .env in default locations.
        
    Returns:
        Dictionary with configuration values.
    """
    # Only load .env if it hasn't been loaded already to avoid duplicate loading
    if not os.environ.get("_RAINBOW_ENV_LOADED"):
        if env_file is not None and os.path.exists(env_file):
            load_dotenv(env_file)
        else:
            load_dotenv()  # Try default locations
        os.environ["_RAINBOW_ENV_LOADED"] = "1"
    
    # Build configuration from environment variables
    config = {
        "surreal": {
            "url": os.getenv("SURREALDB_URL", "ws://localhost:8000/rpc"),
            "http_url": os.getenv("SURREALDB_HTTP_URL"),  # Will be derived if None
            "namespace": os.getenv("SURREALDB_NAMESPACE", "rainbow"),
            "database": os.getenv("SURREALDB_DATABASE", "test"),
            "username": os.getenv("SURREALDB_USERNAME", "root"),
            "password": os.getenv("SURREALDB_PASSWORD", "root"),
        },
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "default_model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "1000")),
        },
        "agent": {
            "name": os.getenv("AGENT_NAME", "Rainbow Agent"),
            "system_prompt": os.getenv("AGENT_SYSTEM_PROMPT", "You are a helpful AI assistant."),
            "max_tool_calls": int(os.getenv("AGENT_MAX_TOOL_CALLS", "5")),
            "timeout": int(os.getenv("AGENT_TIMEOUT", "60")),
            "stream": os.getenv("AGENT_STREAM", "").lower() == "true",
            "retry_attempts": int(os.getenv("AGENT_RETRY_ATTEMPTS", "2")),
        },
        "app": {
            "debug": os.getenv("DEBUG", "").lower() == "true",
            "host": os.getenv("HOST", "0.0.0.0"),
            "port": int(os.getenv("PORT", "5000")),
            "cors_origins": os.getenv("CORS_ORIGINS", "*").split(","),
        }
    }
    
    return config


def load_file_config(config_file: str) -> Dict[str, Any]:
    """
    Load configuration from a JSON/YAML file.
    
    Args:
        config_file: Path to configuration file.
        
    Returns:
        Dictionary with configuration values.
    """
    if not os.path.exists(config_file):
        return {}
        
    with open(config_file, 'r') as f:
        if config_file.endswith('.json'):
            return json.load(f)
        elif config_file.endswith(('.yaml', '.yml')):
            try:
                import yaml
                return yaml.safe_load(f)
            except ImportError:
                raise ImportError("PyYAML is required to load YAML configuration files")
    
    return {}
