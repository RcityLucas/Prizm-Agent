"""
Prizm Agent 主应用程序

整合了API路由、认证系统和页面路由的主应用程序。
"""
import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = str(Path(__file__).absolute().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from flask import Flask
from flask_cors import CORS

from rainbow_agent.api.unified_routes import register_api_routes
from rainbow_agent.api.auth_routes import register_auth_routes
from rainbow_agent.ui.page_routes import register_page_routes
from rainbow_agent.utils.logger import get_logger

# 配置日志
logger = get_logger(__name__)

def create_app():
    """创建Flask应用"""
    # 创建Flask应用
    app = Flask(__name__, 
                static_folder='ui/static',
                template_folder='ui/templates')
    
    # 启用CORS，明确允许temp-prizm-front.vercel.app域名
    CORS(app, resources={r"/*": {"origins": ["https://temp-prizm-front.vercel.app", "*"], 
                               "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                               "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Origin", "Accept", "x-internal-api-request"],
                               "expose_headers": ["Content-Length", "X-JSON"],
                               "supports_credentials": True,
                               "max_age": 86400}})
    
    # 添加一个中间件来手动设置CORS头部，确保它们被正确应用
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With,Origin,Accept,x-internal-api-request')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    
    # 注册认证路由
    register_auth_routes(app)
    
    # 注册API路由
    register_api_routes(app)
    
    # 注册页面路由
    register_page_routes(app)
    
    logger.info("应用程序初始化完成")
    
    return app

# 应用实例
app = create_app()

if __name__ == '__main__':
    # 从环境变量获取端口和主机
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # 启动应用
    logger.info(f"启动应用程序，监听 {host}:{port}，调试模式: {debug}")
    app.run(host=host, port=port, debug=debug)
