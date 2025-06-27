"""
认证路由

提供认证相关的API路由，包括登录、注销和用户信息。
"""
import os
import json
from typing import Dict, Any, Optional
from functools import wraps

from flask import Blueprint, request, jsonify, redirect, url_for, session, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.exceptions import Unauthorized

from rainbow_agent.auth.models import User
from rainbow_agent.auth.oauth import OAuthService
from rainbow_agent.auth.storage import UserStorage
from rainbow_agent.utils.logger import get_logger

# 配置日志
logger = get_logger(__name__)

# 创建Blueprint
auth_api = Blueprint('auth', __name__, url_prefix='/api/auth')

# 全局变量
oauth_service = None
user_storage = None
login_manager = None

# 初始化标志
_is_initialized = False

def init_auth(app, storage: UserStorage):
    """
    初始化认证模块
    
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
    
    # 设置初始化标志
    _is_initialized = True
    
    logger.info("认证模块初始化完成")

def api_login_required(f):
    """API登录要求装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                "success": False,
                "error": "未授权",
                "message": "请先登录"
            }), 401
        return f(*args, **kwargs)
    return decorated

@auth_api.route('/login', methods=['GET'])
def login():
    """登录页面"""
    return jsonify({
        "success": True,
        "message": "请选择登录方式",
        "providers": ["google", "github"]
    })

@auth_api.route('/login/<provider>', methods=['GET'])
def oauth_login(provider):
    """OAuth登录"""
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
    
    if provider not in ['google', 'github']:
        return jsonify({
            "success": False,
            "error": f"不支持的登录方式: {provider}",
            "message": f"不支持的登录方式: {provider}"
        }), 400
    
    # 获取OAuth客户端
    try:
        client = oauth_service.get_oauth_client(provider)
        if not client:
            logger.warning(f"未配置 {provider} 登录凭证")
            return jsonify({
                "success": False,
                "error": f"未配置 {provider} 登录凭证",
                "message": f"请在环境变量中设置 {provider.upper()}_CLIENT_ID 和 {provider.upper()}_CLIENT_SECRET"
            }), 500
    except Exception as e:
        logger.error(f"获取 {provider} OAuth 客户端失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取 {provider} OAuth 客户端失败",
            "message": f"请检查环境变量配置和日志以获取更多信息"
        }), 500
    
    # 获取重定向URI
    redirect_uri = oauth_service.get_redirect_uri(provider)
    
    # 保存下一个URL
    next_url = request.args.get('next') or url_for('pages.index')
    session['next_url'] = next_url
    
    # 生成状态并存储到会话
    import secrets
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    # 强制保存会话
    session.modified = True
    
    # 重定向到授权页面
    return client.authorize_redirect(redirect_uri, state=state)

@auth_api.route('/callback/google', methods=['GET'])
def google_callback():
    """Google回调"""
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
    
    # 获取OAuth客户端
    try:
        client = oauth_service.get_oauth_client('google')
        if not client:
            logger.warning("未配置 Google 登录凭证")
            return jsonify({
                "success": False,
                "error": "未配置 Google 登录凭证",
                "message": "请在环境变量中设置 GOOGLE_CLIENT_ID 和 GOOGLE_CLIENT_SECRET"
            }), 500
    except Exception as e:
        logger.error(f"获取 Google OAuth 客户端失败: {e}")
        return jsonify({
            "success": False,
            "error": "获取 Google OAuth 客户端失败",
            "message": "请检查环境变量配置和日志以获取更多信息"
        }), 500
        
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
    token = client.authorize_access_token()
    
    # 处理回调
    user, error = oauth_service.handle_oauth_callback_sync('google', token)
    
    if error or not user:
        return jsonify({
            "success": False,
            "error": error or "登录失败",
            "message": error or "登录失败"
        }), 500
    
    # 登录用户
    login_user(user)
    
    # 直接重定向到用户资料页面
    next_url = session.pop('next_url', None) or url_for('pages.profile')
    logger.info(f"OAuth登录成功，重定向到: {next_url}")
    return redirect(next_url)

@auth_api.route('/callback/github', methods=['GET'])
def github_callback():
    """GitHub回调"""
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
    
    # 获取OAuth客户端
    try:
        client = oauth_service.get_oauth_client('github')
        if not client:
            logger.warning("未配置 GitHub 登录凭证")
            return jsonify({
                "success": False,
                "error": "未配置 GitHub 登录凭证",
                "message": "请在环境变量中设置 GITHUB_CLIENT_ID 和 GITHUB_CLIENT_SECRET"
            }), 500
    except Exception as e:
        logger.error(f"获取 GitHub OAuth 客户端失败: {e}")
        return jsonify({
            "success": False,
            "error": "获取 GitHub OAuth 客户端失败",
            "message": "请检查环境变量配置和日志以获取更多信息"
        }), 500
        
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
    token = client.authorize_access_token()
    
    # 处理回调
    user, error = oauth_service.handle_oauth_callback_sync('github', token)
    
    if error or not user:
        return jsonify({
            "success": False,
            "error": error or "登录失败",
            "message": error or "登录失败"
        }), 500
    
    # 登录用户
    login_user(user)
    
    # 直接重定向到用户资料页面
    next_url = session.pop('next_url', None) or url_for('pages.profile')
    logger.info(f"OAuth登录成功，重定向到: {next_url}")
    return redirect(next_url)

@auth_api.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """注销"""
    logout_user()
    return jsonify({
        "success": True,
        "message": "注销成功"
    })

@auth_api.route('/user', methods=['GET'])
@api_login_required
def get_user_info():
    """获取用户信息"""
    return jsonify({
        "success": True,
        "data": current_user.to_dict(),
        "user": current_user.to_dict(),
        "message": "获取用户信息成功"
    })

@auth_api.route('/check', methods=['GET'])
def check_auth():
    """检查认证状态"""
    if current_user.is_authenticated:
        return jsonify({
            "success": True,
            "authenticated": True,
            "user": current_user.to_dict(),
            "message": "已登录"
        })
    else:
        return jsonify({
            "success": True,
            "authenticated": False,
            "message": "未登录"
        })

def register_auth_routes(app):
    """注册认证路由到Flask应用"""
    app.register_blueprint(auth_api)
    logger.info("认证路由已注册")
