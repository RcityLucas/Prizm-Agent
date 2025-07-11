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

from flask import Flask, session, request, jsonify
from flask_cors import CORS
from flask_session import Session

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
    
    # 从环境变量设置SECRET_KEY
    app.secret_key = os.environ.get('SECRET_KEY')
    if not app.secret_key:
        logger.warning("未设置SECRET_KEY环境变量，使用临时密钥，这将影响会话安全性和持久性")
        app.secret_key = os.urandom(32)
    
    # 配置会话Cookie设置，解决跨域和跨站点请求问题
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # 使用Lax允许同站点链接带上Cookie，同时提供安全性
    app.config['SESSION_COOKIE_DOMAIN'] = None  # 使用当前域名，避免域名不匹配问题
    app.config['SESSION_COOKIE_SECURE'] = False  # 开发环境中禁用HTTPS要求
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # 防止JavaScript访问会话Cookie，增强安全性
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 会话有效1天
    
    # 强制启用持久会话
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'session_data')
    app.config['SESSION_PERMANENT'] = True
    
    # 确保会话目录存在
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    
    # 初始化服务器端会话
    Session(app)
    
    # 调试日志 - 记录会话操作
    logger.info(f"Flask应用使用SECRET_KEY: {app.secret_key is not None}")
    logger.info(f"SESSION配置: SAMESITE={app.config['SESSION_COOKIE_SAMESITE']}, SECURE={app.config['SESSION_COOKIE_SECURE']}, TYPE={app.config['SESSION_TYPE']}")
    logger.info(f"SESSION目录: {app.config['SESSION_FILE_DIR']}")
    
    # 启用CORS - 配置支持认证的跨域请求
    # 添加自定义认证头部支持并调试会话状态
    @app.after_request
    def set_secure_headers(response):
        # 不再手动设置CORS头，由flask-cors处理
        # 但保留会话状态调试
        
        # 调试会话状态
        if app.debug:
            session_data = {k: v for k, v in session.items()} if session else {}
            logger.debug(f"当前会话状态: {session_data}")
            # 调试Cookie信息
            cookies = {k: v for k, v in request.cookies.items()} if request.cookies else {}
            logger.debug(f"请求Cookie: {cookies}")
            logger.debug(f"响应头: {dict(response.headers)}")
            
        return response
    
    # 添加认证错误处理器
    @app.errorhandler(401)
    def handle_unauthorized(error):
        """处理401未授权错误"""
        return jsonify({
            "success": False,
            "error": "未授权",
            "message": "请先登录"
        }), 401
    
    # 添加通用的Unauthorized异常处理器
    from werkzeug.exceptions import Unauthorized
    @app.errorhandler(Unauthorized)
    def handle_unauthorized_exception(error):
        """处理Unauthorized异常"""
        # 如果异常包含自定义数据，使用它
        if hasattr(error, 'description') and isinstance(error.description, dict):
            return jsonify(error.description), 401
        else:
            return jsonify({
                "success": False,
                "error": "未授权",
                "message": "请先登录"
            }), 401
    
    # 启用CORS - 配置支持认证的跨域请求
    CORS(app, 
         supports_credentials=True,  # 允许跨域请求携带Cookie
         origins=['http://localhost:3000', 'http://localhost:8080', 'http://127.0.0.1:3000', 'http://127.0.0.1:8080'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
         expose_headers=['Set-Cookie'])  # 允许前端访问Set-Cookie头
    
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
