"""
OpenAI service module.

Provides functionality for interacting with the OpenAI API.
"""
import os
import logging
from typing import Dict, Any, List, Optional

# Import the new version of the OpenAI client
from openai import OpenAI

# Import the centralized configuration system
try:
    from rainbow_agent.config import config
    USE_CENTRAL_CONFIG = True
except ImportError:
    # Fallback to legacy configuration if the new system is not available
    USE_CENTRAL_CONFIG = False

# Configure logging
logger = logging.getLogger(__name__)

class OpenAIService:
    """OpenAI service class for interacting with the OpenAI API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenAI service.
        
        Args:
            api_key: OpenAI API key, if not provided uses environment variable or config.
        """
        if USE_CENTRAL_CONFIG:
            # Use the centralized configuration system
            self.api_key = api_key or config.openai.api_key
        else:
            # Legacy behavior
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set, OpenAI service will not be available")
            self.client = None
        else:
            # Create OpenAI client
            self.client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI service initialized successfully")
    
    def generate_response(self, 
                        messages: List[Dict[str, str]], 
                        model: str = None,
                        temperature: float = None,
                        max_tokens: int = None) -> str:
        """
        Generate AI response.
        
        Args:
            messages: List of conversation messages in format [{"role": "user", "content": "..."}, ...].
            model: Model name to use.
            temperature: Temperature parameter to control randomness.
            max_tokens: Maximum number of tokens to generate.
            
        Returns:
            Generated response text.
        """
        try:
            if not self.client:
                logger.warning("API key not set, returning default response")
                return "Sorry, I cannot generate a response because the OpenAI API key is not set."
            
            # Set default values from config if available
            if USE_CENTRAL_CONFIG:
                model = model or config.openai.default_model
                temperature = temperature if temperature is not None else config.openai.temperature
                max_tokens = max_tokens or config.openai.max_tokens
            else:
                # Legacy defaults
                model = model or "gpt-3.5-turbo"
                temperature = temperature if temperature is not None else 0.7
                max_tokens = max_tokens or 1000
            
            logger.info(f"Calling OpenAI API, model: {model}, messages: {len(messages)}")
            
            # Use the new API call method
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract response text
            reply = response.choices[0].message.content.strip()
            logger.info(f"Successfully generated response, length: {len(reply)}")
            
            return reply
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            # Return error message
            return f"Sorry, an error occurred while generating a response: {str(e)}"
    
    def format_dialogue_history(self, turns: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Format dialogue turns for the OpenAI API.
        
        Args:
            turns: List of dialogue turns.
            
        Returns:
            Formatted message list.
        """
        messages = []
        
        # Add system message
        system_prompt = "You are a helpful AI assistant. Please respond concisely, accurately, and in a friendly manner."
        if USE_CENTRAL_CONFIG:
            system_prompt = config.agent.system_prompt
            
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Add dialogue history
        for turn in turns:
            role = turn.get("role", "")
            content = turn.get("content", "")
            
            # Map 'human' and 'ai' roles to OpenAI's 'user' and 'assistant' roles
            if role == "human":
                messages.append({"role": "user", "content": content})
            elif role == "ai":
                messages.append({"role": "assistant", "content": content})
        
        return messages
