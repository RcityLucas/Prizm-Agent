"""
CORS跨域配置
用于前后端分离架构的跨域资源共享配置
"""

from flask_cors import CORS
from rainbow_agent.utils.logger import get_logger

logger = get_logger(__name__)


def configure_cors(app):
    """
    配置CORS跨域设置
    
    Args:
        app: Flask应用实例
    """
    
    # 开发环境配置（宽松）
    if app.config.get('DEBUG', False):
        cors_config = {
            'origins': [
                'http://localhost:3000',  # React开发服务器
                'http://localhost:8080',  # Vue开发服务器
                'http://localhost:4200',  # Angular开发服务器
                'http://localhost:5173',  # Vite开发服务器
                'http://127.0.0.1:3000',
                'http://127.0.0.1:8080',
                'http://127.0.0.1:4200',
                'http://127.0.0.1:5173',
            ],
            'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            'allow_headers': [
                'Content-Type',
                'Authorization',
                'X-Requested-With',
                'Accept',
                'Origin'
            ],
            'supports_credentials': False,  # JWT不需要credentials
            'max_age': 86400  # 24小时
        }
        logger.info("CORS配置: 开发环境（宽松模式）")
    
    # 生产环境配置（严格）
    else:
        # 从环境变量或配置文件获取允许的域名
        allowed_origins = app.config.get('CORS_ORIGINS', []).split(',')
        
        if not allowed_origins or allowed_origins == ['']:
            # 如果没有配置，默认只允许同源
            allowed_origins = [app.config.get('SERVER_NAME', 'http://localhost:5000')]
        
        cors_config = {
            'origins': allowed_origins,
            'methods': ['GET', 'POST', 'PUT', 'DELETE'],  # 不包含OPTIONS，自动处理
            'allow_headers': [
                'Content-Type',
                'Authorization'
            ],
            'supports_credentials': False,  # JWT不需要credentials
            'max_age': 3600  # 1小时
        }
        logger.info(f"CORS配置: 生产环境，允许域名: {allowed_origins}")
    
    # 应用CORS配置
    CORS(app, **cors_config)
    
    # 添加额外的安全头
    @app.after_request
    def after_request(response):
        # 安全头
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # 严格的CSP策略
        if not app.config.get('DEBUG', False):
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self'"
            )
        
        return response
    
    logger.info("CORS跨域配置完成")


def validate_origin(origin, allowed_origins):
    """
    验证请求来源是否被允许
    
    Args:
        origin: 请求来源
        allowed_origins: 允许的来源列表
        
    Returns:
        bool: 是否允许
    """
    if not origin:
        return False
        
    # 精确匹配
    if origin in allowed_origins:
        return True
    
    # 通配符匹配（仅用于开发环境）
    for allowed in allowed_origins:
        if allowed == '*':
            return True
        if allowed.endswith('*') and origin.startswith(allowed[:-1]):
            return True
    
    return False


# 中间件：验证请求来源
def origin_validation_middleware(app):
    """
    请求来源验证中间件
    
    Args:
        app: Flask应用实例
    """
    
    @app.before_request
    def validate_request_origin():
        from flask import request, jsonify
        
        # 跳过非跨域请求
        if not request.headers.get('Origin'):
            return
        
        # 跳过预检请求，由CORS处理
        if request.method == 'OPTIONS':
            return
        
        # 获取配置的允许来源
        allowed_origins = app.config.get('CORS_ORIGINS', '').split(',')
        
        # 开发环境跳过验证
        if app.config.get('DEBUG', False):
            return
        
        # 验证来源
        origin = request.headers.get('Origin')
        if not validate_origin(origin, allowed_origins):
            logger.warning(f"阻止来自未授权来源的请求: {origin}")
            return jsonify({
                'success': False,
                'error': 'Forbidden',
                'message': '请求来源未被授权'
            }), 403
    
    logger.info("请求来源验证中间件已启用")


# API限流配置
def configure_rate_limiting(app):
    """
    配置API限流
    
    Args:
        app: Flask应用实例
    """
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        
        limiter = Limiter(
            app,
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"]
        )
        
        # 认证相关接口的特殊限制
        limiter.limit("5 per minute")(app.view_functions.get('auth.jwt_login'))
        limiter.limit("10 per minute")(app.view_functions.get('auth.refresh_token'))
        
        logger.info("API限流配置完成")
        
    except ImportError:
        logger.warning("flask-limiter未安装，跳过限流配置")


# 完整的安全配置函数
def configure_security(app):
    """
    配置完整的安全设置
    
    Args:
        app: Flask应用实例
    """
    
    # CORS配置
    configure_cors(app)
    
    # 请求来源验证
    origin_validation_middleware(app)
    
    # API限流
    configure_rate_limiting(app)
    
    # JWT配置
    app.config.setdefault('JWT_SECRET_KEY', app.config['SECRET_KEY'])
    app.config.setdefault('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 24)
    app.config.setdefault('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 30)
    
    logger.info("安全配置完成")