"""
认证配置

存储OAuth认证相关的配置信息。
"""
import os
import pathlib
from typing import Dict, Any

# 尝试加载.env文件
try:
    from dotenv import load_dotenv
    # 获取项目根目录
    root_dir = pathlib.Path(__file__).parent.parent.parent
    env_path = root_dir / '.env'
    # 加载.env文件
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"已从 {env_path} 加载环境变量")
except ImportError:
    print("警告: python-dotenv 未安装，无法从.env文件加载环境变量")
    print("提示: 安装 python-dotenv 以支持.env文件: pip install python-dotenv")

# OAuth配置
OAUTH_CONFIG = {
    # Google OAuth配置
    "GOOGLE_CLIENT_ID": os.environ.get("GOOGLE_CLIENT_ID", ""),
    "GOOGLE_CLIENT_SECRET": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
    
    # GitHub OAuth配置
    "GITHUB_CLIENT_ID": os.environ.get("GITHUB_CLIENT_ID", ""),
    "GITHUB_CLIENT_SECRET": os.environ.get("GITHUB_CLIENT_SECRET", ""),
    
    # 会话配置
    "SECRET_KEY": os.environ.get("SECRET_KEY", "prizm-agent-secret-key"),
    "SESSION_TYPE": "filesystem",
    "SESSION_PERMANENT": True,
    "PERMANENT_SESSION_LIFETIME": 86400 * 30,  # 30天
    "SESSION_USE_SIGNER": True,  # 使用签名保护会话数据
    "SESSION_FILE_DIR": os.environ.get("SESSION_FILE_DIR", "./flask_session"),  # 会话文件存储路径
    
    # 安全配置
    "REMEMBER_COOKIE_DURATION": 86400 * 30,  # 30天
    "REMEMBER_COOKIE_SECURE": False,  # 开发环境设置为False，生产环境设置为True
    "REMEMBER_COOKIE_HTTPONLY": True,
    "SESSION_COOKIE_SECURE": False,  # 开发环境设置为False，生产环境设置为True
    "SESSION_COOKIE_HTTPONLY": True,
    "SESSION_COOKIE_SAMESITE": "Lax",  # 防止CSRF攻击
}

def get_oauth_config() -> Dict[str, Any]:
    """
    获取OAuth配置
    
    Returns:
        OAuth配置字典
    """
    return OAUTH_CONFIG

def update_flask_config(app) -> None:
    """
    更新Flask应用配置
    
    Args:
        app: Flask应用
    """
    for key, value in OAUTH_CONFIG.items():
        app.config[key] = value
