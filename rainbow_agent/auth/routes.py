import os
import json
import secrets
from typing import Dict, Any, Optional, Tuple
from functools import wraps

from flask import Blueprint, request, jsonify, redirect, url_for, session, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.exceptions import Unauthorized

from rainbow_agent.auth.models import User
from rainbow_agent.auth.oauth import OAuthService
from rainbow_agent.auth.storage import UserStorage
from rainbow_agent.utils.logger import get_logger


logger = get_logger(__name__)


auth_api = Blueprint('auth', __name__, url_prefix='/api/auth')


oauth_service = None
user_storage = None
login_manager = None


_is_initialized = False

def init_auth(app, storage: UserStorage):
    """
    初始化认证组件
    
    Args:
        app: Flask应用
        storage: 用户存储
    """
    global oauth_service, user_storage, login_manager, _is_initialized
    
    # 设置用户存储
    user_storage = storage
    
    # 初始化OAuth服务
    oauth_service = OAuthService(app, user_storage)
    
    # 初始化LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # 注册用户加载函数
    @login_manager.user_loader
    def load_user(user_id):
        return user_storage.get_user_sync(user_id)
    
    # 标记为已初始化
    _is_initialized = True
    
    logger.info("认证组件初始化完成")

def require_auth(f):
    """需要认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            raise Unauthorized({
                "success": False,
                "error": "未授权",
                "message": "请先登录"
            })
        return f(*args, **kwargs)
    return decorated


def ensure_initialized(f):
    """确保服务已初始化的装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        global oauth_service, _is_initialized
        
        # 检查是否初始化
        if not _is_initialized or not oauth_service:
            # 如果没有初始化，尝试初始化
            try:
                from rainbow_agent.api.auth_routes import oauth_service as api_oauth_service
                oauth_service = api_oauth_service
                logger.info("从 API 模块获取 OAuth 服务")
            except Exception as e:
                logger.error(f"OAuth服务未初始化: {e}")
                return jsonify({
                    "success": False,
                    "error": "OAuth服务未初始化",
                    "message": "系统配置错误，请联系管理员"
                }), 500
        
        return f(*args, **kwargs)
    return decorated


def get_oauth_client(provider: str):
    """获取OAuth客户端"""
    try:
        client = oauth_service.get_oauth_client(provider)
        if not client:
            logger.warning(f"未配置 {provider} 登录凭证")
            return None, jsonify({
                "success": False,
                "error": f"未配置 {provider} 登录凭证",
                "message": f"请在环境变量中设置 {provider.upper()}_CLIENT_ID 和 {provider.upper()}_CLIENT_SECRET"
            }), 500
        return client, None
    except Exception as e:
        logger.error(f"获取 {provider} OAuth 客户端失败: {e}")
        return None, jsonify({
            "success": False,
            "error": f"获取 {provider} OAuth 客户端失败",
            "message": "请检查环境变量配置和日志以获取更多信息"
        }), 500

def generic_oauth_login(provider: str):
    """通用OAuth登录处理函数 - 返回授权URL给前端"""
    client, error_response = get_oauth_client(provider)
    if error_response:
        return error_response
    
    # 获取回调URL - 指向前端回调页面
    frontend_base_url = os.environ.get('FRONTEND_BASE_URL', 'http://localhost:3000')
    redirect_uri = f"{frontend_base_url}/auth/callback/{provider}"
    
    # 保存下一个URL
    next_url = request.args.get('next')
    if next_url:
        session['next_url'] = next_url
    
    # 生成状态并保存到会话
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    # 强制保存会话
    session.modified = True
    
    # 生成授权URL
    try:
        from urllib.parse import urlencode
        
        if provider == 'google':
            # Google OAuth2 授权URL
            params = {
                'client_id': client.client_id,
                'redirect_uri': redirect_uri,
                'scope': 'openid email profile',
                'response_type': 'code',
                'state': state
            }
            auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        elif provider == 'github':
            # GitHub OAuth2 授权URL
            params = {
                'client_id': client.client_id,
                'redirect_uri': redirect_uri,
                'scope': 'user:email',
                'state': state
            }
            auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
        else:
            return jsonify({
                "success": False,
                "error": f"不支持的OAuth提供商: {provider}",
                "message": f"不支持的OAuth提供商: {provider}"
            }), 400
    except Exception as e:
        logger.error(f"生成{provider}授权URL失败: {e}")
        return jsonify({
            "success": False,
            "error": f"生成{provider}授权URL失败",
            "message": f"生成授权URL时发生错误: {str(e)}"
        }), 500
    
    # 返回JSON响应而非重定向
    return jsonify({
        "success": True,
        "message": f"获取{provider}授权URL成功",
        "data": {
            "auth_url": auth_url,
            "provider": provider,
            "state": state
        }
    })


@auth_api.route('/login/google', methods=['GET'])
@ensure_initialized
def google_login():
    """Google登录"""
    return generic_oauth_login('google')

def generic_oauth_callback(provider: str):
    """通用OAuth回调处理函数 - 返回JSON响应"""
    client, error_response = get_oauth_client(provider)
    if error_response:
        return error_response
        
    # 验证状态
    expected_state = session.pop('oauth_state', None)
    received_state = request.args.get('state')
    
    if not expected_state or expected_state != received_state:
        logger.error(f"OAuth状态验证失败: expected={expected_state}, received={received_state}")
        return jsonify({
            "success": False,
            "error": "CSRF验证失败",
            "message": "登录请求安全验证失败，请重试"
        }), 400
    
    # 获取令牌
    try:
        token = client.authorize_access_token()
    except Exception as e:
        logger.error(f"获取OAuth令牌失败: {e}")
        return jsonify({
            "success": False,
            "error": "获取令牌失败",
            "message": "OAuth授权失败，请重试"
        }), 400
    
    # 处理回调
    user, error = oauth_service.handle_oauth_callback_sync(provider, token)
    
    if error or not user:
        return jsonify({
            "success": False,
            "error": error or "登录失败",
            "message": error or "登录失败"
        }), 500
    
    # 登录用户
    login_user(user)
    
    # 获取下一个URL
    next_url = session.pop('next_url', None) or '/'
    logger.info(f"OAuth登录成功，用户ID: {user.id}")
    
    # 返回JSON响应
    return jsonify({
        "success": True,
        "message": f"{provider}登录成功",
        "data": {
            "user": user.to_dict(),
            "redirect_url": next_url,
            "provider": provider
        }
    })


@auth_api.route('/callback/google', methods=['GET'])
@ensure_initialized
def google_callback():
    """Google回调"""
    return generic_oauth_callback('google')

@auth_api.route('/callback/github', methods=['GET'])
@ensure_initialized
def github_callback():
    """GitHub回调"""
    return generic_oauth_callback('github')

@auth_api.route('/login/github', methods=['GET'])
@ensure_initialized
def github_login():
    """GitHub登录"""
    return generic_oauth_login('github')

@auth_api.route('/logout', methods=['POST'])
@ensure_initialized
def logout():
    """退出登录"""
    was_authenticated = current_user.is_authenticated
    logout_user()
    
    return jsonify({
        "success": True,
        "message": "已退出登录" if was_authenticated else "已退出登录",
        "data": {
            "authenticated": False,
            "user": None
        }
    })

@auth_api.route('/status', methods=['GET'])
def get_auth_status():
    """检查登录状态"""
    if current_user.is_authenticated:
        return jsonify({
            "success": True,
            "message": "已登录",
            "data": {
                "authenticated": True,
                "user": current_user.to_dict()
            }
        })
    else:
        return jsonify({
            "success": True,
            "message": "未登录",
            "data": {
                "authenticated": False,
                "user": None
            }
        })

@auth_api.route('/user', methods=['GET'])
@require_auth
def get_current_user():
    """获取当前用户信息"""
    # @require_auth 装饰器已经确保用户已登录
    return jsonify({
        "success": True,
        "message": "获取用户信息成功",
        "data": {
            "user": current_user.to_dict()
        }
    })

@auth_api.route('/user', methods=['PUT'])
@require_auth
@ensure_initialized
def update_user():
    """更新用户信息"""
    global user_storage
    
    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify({
            "success": False,
            "error": "无效的请求数据",
            "message": "请提供有效的JSON数据"
        }), 400
    
    # 更新用户信息
    try:
        # 获取当前用户
        user = user_storage.get_user_sync(current_user.id)
        if not user:
            return jsonify({
                "success": False,
                "error": "用户不存在",
                "message": "无法找到当前用户"
            }), 404
        
        # 更新用户信息
        for key, value in data.items():
            if hasattr(user, key) and key not in ['id', 'provider', 'provider_id', 'token', 'token_expiry']:
                setattr(user, key, value)
        
        # 保存用户信息
        user = user_storage.update_user_sync(user)
        
        return jsonify({
            "success": True,
            "message": "用户信息已更新",
            "data": user.to_dict()
        })
    except Exception as e:
        logger.error(f"更新用户信息失败: {e}")
        return jsonify({
            "success": False,
            "error": "更新用户信息失败",
            "message": str(e)
        }), 500
