#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple test script for the centralized configuration system.
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to Python path
import pathlib
root_dir = str(pathlib.Path(__file__).absolute().parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

def main():
    # Test configuration loading
    logger.info("Testing configuration loading...")
    try:
        from rainbow_agent.config import load_config, config
        logger.info("✅ Successfully imported configuration module")
    except ImportError as e:
        logger.error(f"❌ Failed to import configuration module: {e}")
        return False

    # Test configuration loading with defaults
    try:
        config = load_config()
        logger.info("✅ Successfully loaded configuration with defaults")
    except Exception as e:
        logger.error(f"❌ Failed to load configuration: {e}")
        return False

    # Test accessing configuration values
    try:
        logger.info(f"SurrealDB URL: {config.surreal.url}")
        logger.info(f"SurrealDB HTTP URL: {config.surreal.http_url}")
        logger.info(f"SurrealDB namespace: {config.surreal.namespace}")
        logger.info(f"OpenAI default model: {config.openai.default_model}")
        logger.info(f"Agent name: {config.agent.name}")
        logger.info(f"App port: {config.app.port}")
        logger.info("✅ Successfully accessed configuration values")
    except Exception as e:
        logger.error(f"❌ Failed to access configuration values: {e}")
        return False

    # Test compatibility with existing code
    logger.info("Testing compatibility with existing code...")
    try:
        from rainbow_agent.storage.config import get_surreal_config
        surreal_config = get_surreal_config()
        logger.info(f"SurrealDB URL from compatibility layer: {surreal_config['url']}")
        logger.info(f"SurrealDB namespace from compatibility layer: {surreal_config['namespace']}")
        logger.info("✅ Successfully used compatibility layer")
    except Exception as e:
        logger.error(f"❌ Failed to use compatibility layer: {e}")
        return False

    logger.info("All tests completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
