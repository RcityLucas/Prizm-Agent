"""
Configuration schema for Rainbow Agent.

This module defines the Pydantic models for validating and typing configuration.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List


class SurrealDBConfig(BaseModel):
    """SurrealDB configuration."""
    url: str = Field("ws://localhost:8000/rpc", description="SurrealDB WebSocket URL")
    http_url: Optional[str] = Field(None, description="SurrealDB HTTP URL (derived from WebSocket URL if not provided)")
    namespace: str = Field("rainbow", description="SurrealDB namespace")
    database: str = Field("test", description="SurrealDB database name")
    username: str = Field("root", description="SurrealDB username")
    password: str = Field("root", description="SurrealDB password")
    
    @validator('http_url', always=True)
    def derive_http_url(cls, v, values):
        """Derive HTTP URL from WebSocket URL if not provided."""
        if v is None and 'url' in values:
            from urllib.parse import urlparse
            parsed = urlparse(values['url'])
            scheme = 'https' if parsed.scheme == 'wss' else 'http'
            return f"{scheme}://{parsed.netloc}"
        return v


class OpenAIConfig(BaseModel):
    """OpenAI API configuration."""
    api_key: str = Field("", description="OpenAI API key")
    default_model: str = Field("gpt-3.5-turbo", description="Default model to use")
    temperature: float = Field(0.7, description="Default temperature for generation")
    max_tokens: int = Field(1000, description="Default max tokens for generation")


class AgentConfig(BaseModel):
    """Agent behavior configuration."""
    name: str = Field("Rainbow Agent", description="Agent name")
    system_prompt: str = Field("You are a helpful AI assistant.", description="Default system prompt")
    max_tool_calls: int = Field(5, description="Maximum number of tool calls per response")
    timeout: int = Field(60, description="Timeout for API calls in seconds")
    stream: bool = Field(False, description="Whether to use streaming by default")
    retry_attempts: int = Field(2, description="Number of retry attempts for API calls")


class AppConfig(BaseModel):
    """Application server configuration."""
    debug: bool = Field(False, description="Debug mode")
    host: str = Field("0.0.0.0", description="Host to bind the server to")
    port: int = Field(5000, description="Port to bind the server to")
    cors_origins: List[str] = Field(["*"], description="CORS allowed origins")


class Config(BaseModel):
    """Main configuration model."""
    surreal: SurrealDBConfig = Field(default_factory=SurrealDBConfig)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    app: AppConfig = Field(default_factory=AppConfig)
