# Rainbow Agent Configuration System

This module provides a centralized configuration system for the Rainbow Agent project. It loads configuration from environment variables, `.env` files, and optionally configuration files, and provides a validated configuration object.

## Features

- **Centralized Configuration**: All configuration options are defined in one place
- **Type Safety and Validation**: Pydantic models provide validation and type checking
- **Documentation**: Each configuration option has a description
- **Flexibility**: Support for environment variables, `.env` files, and config files
- **Default Values**: Clear and consistent default values
- **Singleton Pattern**: Ensures configuration is loaded only once
- **Backward Compatibility**: Maintains compatibility with existing code

## Usage

### Basic Usage

```python
from rainbow_agent.config import config

# Access configuration values
print(f"Using SurrealDB at {config.surreal.url}")
print(f"Using OpenAI model {config.openai.default_model}")
```

### Loading Configuration

```python
from rainbow_agent.config import load_config, config

# Load configuration at application startup
config = load_config()

# Optionally specify .env file and/or config file
config = load_config(env_file=".env.dev", config_file="config.json")
```

### Configuration Schema

The configuration schema is defined in `schema.py` using Pydantic models:

- `SurrealDBConfig`: Configuration for SurrealDB
- `OpenAIConfig`: Configuration for OpenAI API
- `AgentConfig`: Configuration for agent behavior
- `AppConfig`: Configuration for application server

## Environment Variables

The following environment variables are supported:

### SurrealDB Configuration

- `SURREALDB_URL`: SurrealDB WebSocket URL (default: `ws://localhost:8000/rpc`)
- `SURREALDB_HTTP_URL`: SurrealDB HTTP URL (derived from WebSocket URL if not provided)
- `SURREALDB_NAMESPACE`: SurrealDB namespace (default: `rainbow`)
- `SURREALDB_DATABASE`: SurrealDB database name (default: `test`)
- `SURREALDB_USERNAME`: SurrealDB username (default: `root`)
- `SURREALDB_PASSWORD`: SurrealDB password (default: `root`)

### OpenAI Configuration

- `OPENAI_API_KEY`: OpenAI API key
- `OPENAI_MODEL`: Default model to use (default: `gpt-3.5-turbo`)
- `OPENAI_TEMPERATURE`: Default temperature for generation (default: `0.7`)
- `OPENAI_MAX_TOKENS`: Default max tokens for generation (default: `1000`)

### Agent Configuration

- `AGENT_NAME`: Agent name (default: `Rainbow Agent`)
- `AGENT_SYSTEM_PROMPT`: Default system prompt (default: `You are a helpful AI assistant.`)
- `AGENT_MAX_TOOL_CALLS`: Maximum number of tool calls per response (default: `5`)
- `AGENT_TIMEOUT`: Timeout for API calls in seconds (default: `60`)
- `AGENT_STREAM`: Whether to use streaming by default (default: `false`)
- `AGENT_RETRY_ATTEMPTS`: Number of retry attempts for API calls (default: `2`)

### Application Configuration

- `DEBUG`: Debug mode (default: `false`)
- `HOST`: Host to bind the server to (default: `0.0.0.0`)
- `PORT`: Port to bind the server to (default: `5000`)
- `CORS_ORIGINS`: CORS allowed origins, comma-separated (default: `*`)

## Configuration Files

You can also provide configuration via JSON or YAML files. The structure should match the schema defined in `schema.py`.

Example JSON configuration:

```json
{
  "surreal": {
    "url": "ws://localhost:8000/rpc",
    "namespace": "rainbow",
    "database": "production",
    "username": "admin",
    "password": "secure_password"
  },
  "openai": {
    "default_model": "gpt-4",
    "temperature": 0.8
  },
  "app": {
    "debug": false,
    "port": 8080
  }
}
```

## Extending the Configuration

To add new configuration options:

1. Update the schema in `schema.py`
2. Update the environment variable loading in `loaders.py`
3. Update this documentation
