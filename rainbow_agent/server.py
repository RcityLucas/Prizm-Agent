"""
Rainbow Agent API服务器

提供与前端交互的API服务和Web接口。
"""
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import setup_routes
from .config.settings import get_settings
from .utils.logger import get_logger

# 获取配置和日志记录器
settings = get_settings()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    """
    创建FastAPI应用实例
    
    Returns:
        FastAPI实例
    """
    # 创建FastAPI应用
    app = FastAPI(
        title="Rainbow Agent API",
        description="Rainbow Agent智能助手API服务",
        version="1.0.0"
    )
    
    # 配置CORS中间件，允许跨域请求
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",     # 前端开发服务器
            "http://127.0.0.1:3000",     # 前端开发服务器替代URL
            "http://localhost:8000",     # 后端服务器URL
            "*"                         # 允许所有源（开发环境）
        ],  
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # 设置API路由
    setup_routes(app)
    
    # 加载应用事件
    @app.on_event("startup")
    async def startup_event():
        logger.info("Rainbow Agent API服务启动")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Rainbow Agent API服务关闭")
    
    return app


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    启动Rainbow Agent API服务器
    
    Args:
        host: 主机地址
        port: 端口号
        reload: 是否启用热重载（开发模式）
    """
    # 获取环境变量中的端口（如果有）
    env_port = os.environ.get("PORT")
    if env_port:
        try:
            port = int(env_port)
        except ValueError:
            logger.warning(f"无效的PORT环境变量值: {env_port}，使用默认端口: {port}")
    
    logger.info(f"启动Rainbow Agent API服务器: http://{host}:{port}")
    
    # 启动服务器
    uvicorn.run(
        "rainbow_agent.server:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True
    )


if __name__ == "__main__":
    start_server(reload=True)  # 开发模式启用热重载
