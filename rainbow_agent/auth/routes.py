import os
import json
import secrets
from typing import Dict, Any, Optional, Tuple
from functools import wraps

from flask import Blueprint, request, jsonify, redirect, url_for, session, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.exceptions import Unauthorized

from rainbow_agent.auth.models import User
from rainbow_agent.utils.logger import get_logger
# 导入api/auth_routes.py中的全局变量和初始化函数
from rainbow_agent.api.auth_routes import oauth_service, user_storage, login_manager, init_auth_components


logger = get_logger(__name__)


auth_api = Blueprint('auth', __name__, url_prefix='/api/auth')

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
        # 使用api/auth_routes.py中的初始化状态
        from rainbow_agent.api.auth_routes import _auth_components_initialized
        
        # 检查是否初始化
        if not _auth_components_initialized or not oauth_service:
            # 如果没有初始化，尝试初始化
            try:
                # 尝试初始化认证组件
                init_auth_components(current_app)
                logger.info("认证组件已初始化")
            except Exception as e:
                logger.error(f"OAuth服务初始化失败: {e}")
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
    """通用OAuth登录处理函数"""
    client, error_response = get_oauth_client(provider)
    if error_response:
        return error_response
    
    # 获取回调URL
    redirect_uri = url_for(f'auth.{provider}_callback', _external=True)
    
    # 保存下一个URL
    next_url = request.args.get('next')
    if next_url:
        session['next_url'] = next_url
    
    # 生成状态并保存到会话
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    # 强制保存会话
    session.modified = True
    
    # 重定向到授权页面
    return client.authorize_redirect(redirect_uri, state=state)


@auth_api.route('/login/google', methods=['GET'])
@ensure_initialized
def google_login():
    """Google登录"""
    return generic_oauth_login('google')

def generic_oauth_callback(provider: str):
    """通用OAuth回调处理函数"""
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
    token = client.authorize_access_token()
    
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
    
    # 直接重定向到主页
    next_url = session.pop('next_url', None) or '/'
    logger.info(f"OAuth登录成功，重定向到: {next_url}")
    return redirect(next_url)


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

@auth_api.route('/logout', methods=['GET'])
@ensure_initialized
def logout():
    """退出登录"""
    logout_user()
    return jsonify({
        "success": True,
        "message": "已退出登录"
    })

@auth_api.route('/user', methods=['GET'])
@require_auth
def get_current_user():
    """获取当前用户信息"""
    # @require_auth 装饰器已经确保用户已登录
    return jsonify({
        "success": True,
        "data": current_user.to_dict()
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
