"""
应用配置管理
"""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import json

from ..utils.logger import get_logger

logger = get_logger(__name__)

# 加载环境变量
load_dotenv()


class Settings:
    """
    应用配置管理类
    
    负责加载和管理应用配置
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径 (可选)
        """
        self.config = {}
        
        # 首先加载默认配置
        self._load_defaults()
        
        # 如果提供了配置文件，则加载配置文件
        if config_path and os.path.exists(config_path):
            self._load_from_file(config_path)
        
        # 最后从环境变量加载配置，环境变量优先级最高
        self._load_from_env()
        
        logger.info("配置加载完成")
    
    def _load_defaults(self):
        """加载默认配置"""
        self.config = {
            # API设置
            "api": {
                "base_url": "https://api.openai.com/v1",  # 默认OpenAI API地址
                "timeout": 60,  # 请求超时时间（秒）
                "proxy": None,  # HTTP代理
                "max_retries": 3,  # 最大重试次数
                "api_key": None,  # OpenAI API密钥
                "chat_anywhere": {
                    "enabled": False,  # 是否启用ChatAnywhere
                    "base_url": None,  # ChatAnywhere基础URL
                },
            },
            
            # LLM设置
            "llm": {
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 2000,
                "system_message": "你是一个有帮助的AI助手，请用简洁、准确、友好的方式回答用户的问题。",
            },
            
            # 记忆系统设置
            "memory": {
                "type": "simple",  # 'simple' 或 'sqlite'
                "sqlite_path": "memory.db",
                "max_items": 100,
                "max_conversations": 10,  # 最大会话数量
            },
            
            # 工具设置
            "tools": {
                "enabled": ["web_search", "weather"],
                "api_keys": {},
                "auto_discover": True,  # 自动发现工具
            },
            
            # 日志设置
            "logging": {
                "level": "INFO",
                "file": None,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            
            # 存储系统设置 (从storage/config.py整合)
            "storage": {
                "type": "surreal",  # 存储类型
                "url": "ws://localhost:8000/rpc",  # SurrealDB WebSocket URL
                "http_url": "http://localhost:8000",  # SurrealDB HTTP URL
                "health_url": "http://localhost:8000/health",  # 健康检查URL
                "namespace": "rainbow",  # 命名空间
                "database": "test",  # 数据库名
                "username": "root",  # 用户名
                "password": "root",  # 密码
            },
            
            # 服务器设置
            "server": {
                "host": "0.0.0.0",  # 服务器主机
                "port": 5000,  # 服务器端口
                "debug": True,  # 是否启用调试模式
            },
            
            # 上下文设置 (从context_settings.py整合)
            "context": {
                # 是否启用上下文注入
                "enable_injection": True,
                
                # 上下文优先级 (low, medium, high)
                # - low: 仅在没有足够对话历史时使用上下文
                # - medium: 正常使用上下文
                # - high: 上下文优先于对话历史
                "priority_level": "medium",
                
                # 最大上下文标记数
                "max_tokens": 1000,
                
                # 上下文注入位置
                # - prefix: 在提示前添加上下文
                # - system: 作为系统消息添加
                # - inline: 在对话中内联添加
                "injection_position": "prefix",
                
                # 是否记录上下文使用情况
                "log_usage": True,
                
                # 是否在响应中包含上下文元数据
                "include_metadata_in_response": True,
                
                # 上下文处理超时（秒）
                "processing_timeout": 2.0,
                
                # 上下文类型配置
                "types": {
                    "general": {
                        "enabled": True,
                        "priority": "medium"
                    },
                    "user_profile": {
                        "enabled": True,
                        "priority": "high"
                    },
                    "domain": {
                        "enabled": True,
                        "priority": "medium"
                    },
                    "system": {
                        "enabled": True,
                        "priority": "low"
                    },
                    "custom": {
                        "enabled": True,
                        "priority": "medium"
                    }
                }
            },
        }
    
    def _load_from_file(self, config_path: str):
        """从文件加载配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            
            # 递归更新配置
            self._update_config(self.config, file_config)
            logger.info(f"从文件加载配置: {config_path}")
        except Exception as e:
            logger.error(f"加载配置文件出错: {e}")
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        # OpenAI API设置
        if os.environ.get("OPENAI_API_KEY"):
            api_key = os.environ.get("OPENAI_API_KEY")
            self.config["api"]["api_key"] = api_key
            # 检测是否可能是ChatAnywhere的API Key
            if api_key.startswith("sk-") and len(api_key) < 60:
                self.config["api"]["chat_anywhere"]["enabled"] = True
                logger.info("Detected ChatAnywhere API key format")
        
        # API基础URL
        if os.environ.get("OPENAI_BASE_URL"):
            base_url = os.environ.get("OPENAI_BASE_URL")
            self.config["api"]["base_url"] = base_url
            
            # 如果基础URL包含chatanywhere.tech，自动启用ChatAnywhere
            if "chatanywhere.tech" in base_url.lower():
                self.config["api"]["chat_anywhere"]["enabled"] = True
                self.config["api"]["chat_anywhere"]["base_url"] = base_url
                logger.info("Using ChatAnywhere as API proxy service")
        
        # 代理设置
        if os.environ.get("HTTP_PROXY"):
            self.config["api"]["proxy"] = os.environ.get("HTTP_PROXY")
        elif os.environ.get("HTTPS_PROXY"):
            self.config["api"]["proxy"] = os.environ.get("HTTPS_PROXY")
            
        # LLM设置
        if os.environ.get("OPENAI_API_MODEL"):
            self.config["llm"]["model"] = os.environ.get("OPENAI_API_MODEL")
        
        if os.environ.get("OPENAI_API_TEMPERATURE"):
            self.config["llm"]["temperature"] = float(os.environ.get("OPENAI_API_TEMPERATURE"))
        
        if os.environ.get("OPENAI_API_MAX_TOKENS"):
            self.config["llm"]["max_tokens"] = int(os.environ.get("OPENAI_API_MAX_TOKENS"))
        
        if os.environ.get("OPENAI_SYSTEM_MESSAGE"):
            self.config["llm"]["system_message"] = os.environ.get("OPENAI_SYSTEM_MESSAGE")
        
        # 记忆系统设置
        if os.environ.get("MEMORY_TYPE"):
            self.config["memory"]["type"] = os.environ.get("MEMORY_TYPE")
        
        if os.environ.get("MEMORY_SQLITE_PATH"):
            self.config["memory"]["sqlite_path"] = os.environ.get("MEMORY_SQLITE_PATH")
        
        if os.environ.get("MEMORY_MAX_ITEMS"):
            self.config["memory"]["max_items"] = int(os.environ.get("MEMORY_MAX_ITEMS"))
            
        if os.environ.get("MEMORY_MAX_CONVERSATIONS"):
            self.config["memory"]["max_conversations"] = int(os.environ.get("MEMORY_MAX_CONVERSATIONS"))
        
        # 日志设置
        if os.environ.get("LOG_LEVEL"):
            self.config["logging"]["level"] = os.environ.get("LOG_LEVEL")
        
        if os.environ.get("LOG_FILE"):
            self.config["logging"]["file"] = os.environ.get("LOG_FILE")
            
        if os.environ.get("LOG_FORMAT"):
            self.config["logging"]["format"] = os.environ.get("LOG_FORMAT")
        
        # 工具配置
        if os.environ.get("TOOLS_AUTO_DISCOVER") and os.environ.get("TOOLS_AUTO_DISCOVER").lower() in ['0', 'false', 'no']:
            self.config["tools"]["auto_discover"] = False
            
        if os.environ.get("TOOLS_ENABLED"):
            enabled_tools = os.environ.get("TOOLS_ENABLED").split(',')
            self.config["tools"]["enabled"] = [tool.strip() for tool in enabled_tools]
        
        # 工具API密钥
        # 从环境变量读取所有TOOL_API_KEY_前缀的变量
        for key, value in os.environ.items():
            if key.startswith("TOOL_API_KEY_"):
                tool_name = key[len("TOOL_API_KEY_"):].lower()
                self.config["tools"]["api_keys"][tool_name] = value
                
        # 读取SEARCH_API_KEY作为特殊情况
        if os.environ.get("SEARCH_API_KEY"):
            self.config["tools"]["api_keys"]["web_search"] = os.environ.get("SEARCH_API_KEY")
        
        # 存储系统设置
        if os.environ.get("SURREALDB_URL"):
            self.config["storage"]["url"] = os.environ.get("SURREALDB_URL")
            # 更新HTTP URL
            from urllib.parse import urlparse
            parsed = urlparse(self.config["storage"]["url"])
            scheme = 'http' if parsed.scheme == 'ws' else 'https' if parsed.scheme == 'wss' else parsed.scheme
            self.config["storage"]["http_url"] = f"{scheme}://{parsed.netloc}"
            self.config["storage"]["health_url"] = f"{self.config['storage']['http_url']}/health"
        
        if os.environ.get("SURREALDB_NAMESPACE"):
            self.config["storage"]["namespace"] = os.environ.get("SURREALDB_NAMESPACE")
            
        if os.environ.get("SURREALDB_DATABASE"):
            self.config["storage"]["database"] = os.environ.get("SURREALDB_DATABASE")
            
        if os.environ.get("SURREALDB_USERNAME"):
            self.config["storage"]["username"] = os.environ.get("SURREALDB_USERNAME")
            
        if os.environ.get("SURREALDB_PASSWORD"):
            self.config["storage"]["password"] = os.environ.get("SURREALDB_PASSWORD")
        
        # 服务器设置
        if os.environ.get("HOST"):
            self.config["server"]["host"] = os.environ.get("HOST")
            
        if os.environ.get("PORT"):
            self.config["server"]["port"] = int(os.environ.get("PORT"))
            
        if os.environ.get("DEBUG") and os.environ.get("DEBUG").lower() in ['1', 'true', 'yes']:
            self.config["server"]["debug"] = True
        elif os.environ.get("DEBUG") and os.environ.get("DEBUG").lower() in ['0', 'false', 'no']:
            self.config["server"]["debug"] = False
            
        # 上下文设置
        if os.environ.get("CONTEXT_ENABLE_INJECTION") and os.environ.get("CONTEXT_ENABLE_INJECTION").lower() in ['0', 'false', 'no']:
            self.config["context"]["enable_injection"] = False
            
        if os.environ.get("CONTEXT_PRIORITY_LEVEL"):
            level = os.environ.get("CONTEXT_PRIORITY_LEVEL").lower()
            if level in ["low", "medium", "high"]:
                self.config["context"]["priority_level"] = level
                
        if os.environ.get("CONTEXT_MAX_TOKENS"):
            self.config["context"]["max_tokens"] = int(os.environ.get("CONTEXT_MAX_TOKENS"))
            
        if os.environ.get("CONTEXT_INJECTION_POSITION"):
            position = os.environ.get("CONTEXT_INJECTION_POSITION").lower()
            if position in ["prefix", "system", "inline"]:
                self.config["context"]["injection_position"] = position
    
    def _update_config(self, target: Dict[str, Any], source: Dict[str, Any]):
        """递归更新配置字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_config(target[key], value)
            else:
                target[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键，支持点号分隔的嵌套键，如 'llm.model'
            default: 默认值，如果配置项不存在则返回此值
            
        Returns:
            配置项的值
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """
    获取全局配置实例
    
    Returns:
        Settings实例
    """
    return settings
