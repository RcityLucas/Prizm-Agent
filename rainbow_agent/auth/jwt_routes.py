"""
JWT认证路由
支持前后端分离的Token-based认证API
"""

from flask import Blueprint, request, jsonify, current_app
from rainbow_agent.auth.models import User
from rainbow_agent.auth.jwt_auth import JWTAuthService, jwt_required
from rainbow_agent.auth.storage import UserStorage
from rainbow_agent.utils.logger import get_logger

logger = get_logger(__name__)

# 创建JWT认证蓝图
jwt_auth_api = Blueprint('jwt_auth', __name__, url_prefix='/api/auth')

# 全局变量
jwt_service: JWTAuthService = None
user_storage: UserStorage = None


def init_jwt_auth(app, storage: UserStorage):
    """
    初始化JWT认证
    
    Args:
        app: Flask应用
        storage: 用户存储
    """
    global jwt_service, user_storage
    
    user_storage = storage
    jwt_service = JWTAuthService(app, storage)
    
    # 将JWT服务添加到应用上下文
    app.jwt_service = jwt_service
    
    logger.info("JWT认证组件初始化完成")


@jwt_auth_api.route('/login', methods=['POST'])
def jwt_login():
    """
    JWT登录端点
    支持用户名密码登录，返回JWT令牌
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': '请提供用户名和密码'
            }), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Missing credentials',
                'message': '用户名和密码不能为空'
            }), 400
        
        # 验证用户凭据
        user = user_storage.authenticate_user(username, password)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Invalid credentials',
                'message': '用户名或密码错误'
            }), 401
        
        # 生成JWT令牌
        tokens = jwt_service.generate_tokens(user)
        
        logger.info(f"User {username} logged in successfully")
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'data': tokens
        })
        
    except Exception as e:
        logger.error(f"JWT login error: {e}")
        return jsonify({
            'success': False,
            'error': 'Login failed',
            'message': f'登录失败: {str(e)}'
        }), 500


@jwt_auth_api.route('/refresh', methods=['POST'])
def refresh_token():
    """
    刷新访问令牌
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': '请提供刷新令牌'
            }), 400
        
        refresh_token = data.get('refresh_token')
        if not refresh_token:
            return jsonify({
                'success': False,
                'error': 'Missing refresh token',
                'message': '刷新令牌不能为空'
            }), 400
        
        # 刷新令牌
        new_tokens = jwt_service.refresh_access_token(refresh_token)
        if not new_tokens:
            return jsonify({
                'success': False,
                'error': 'Invalid refresh token',
                'message': '无效的刷新令牌'
            }), 401
        
        return jsonify({
            'success': True,
            'message': '令牌刷新成功',
            'data': new_tokens
        })
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({
            'success': False,
            'error': 'Refresh failed',
            'message': f'令牌刷新失败: {str(e)}'
        }), 500


@jwt_auth_api.route('/verify', methods=['GET'])
@jwt_required
def verify_token():
    """
    验证令牌有效性
    """
    return jsonify({
        'success': True,
        'message': '令牌有效',
        'data': {
            'user': request.current_user.to_dict()
        }
    })


@jwt_auth_api.route('/logout', methods=['POST'])
@jwt_required
def jwt_logout():
    """
    JWT登出端点
    注意：JWT是无状态的，这里主要是通知前端清除令牌
    """
    logger.info(f"User {request.current_user.username} logged out")
    
    return jsonify({
        'success': True,
        'message': '已退出登录',
        'data': {
            'instruction': '请在前端清除存储的令牌'
        }
    })


@jwt_auth_api.route('/profile', methods=['GET'])
@jwt_required
def get_profile():
    """
    获取当前用户资料
    """
    return jsonify({
        'success': True,
        'message': '获取用户资料成功',
        'data': {
            'user': request.current_user.to_dict()
        }
    })


@jwt_auth_api.route('/profile', methods=['PUT'])
@jwt_required
def update_profile():
    """
    更新用户资料
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': '请提供更新数据'
            }), 400
        
        user = request.current_user
        
        # 更新用户信息
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        
        # 保存更新
        updated_user = user_storage.update_user(user)
        
        return jsonify({
            'success': True,
            'message': '用户资料更新成功',
            'data': {
                'user': updated_user.to_dict()
            }
        })
        
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        return jsonify({
            'success': False,
            'error': 'Update failed',
            'message': f'更新失败: {str(e)}'
        }), 500


# OAuth适配器（用于前后端分离的OAuth流程）
@jwt_auth_api.route('/oauth/google', methods=['GET'])
def oauth_google_url():
    """
    获取Google OAuth授权URL
    前端可以重定向用户到这个URL进行授权
    """
    try:
        # 这里需要根据实际的OAuth实现来获取授权URL
        # 暂时返回占位符
        return jsonify({
            'success': True,
            'message': '获取授权URL成功',
            'data': {
                'auth_url': '/api/auth/login/google',
                'callback_url': '/api/auth/jwt/oauth/google/callback'
            }
        })
        
    except Exception as e:
        logger.error(f"Get OAuth URL error: {e}")
        return jsonify({
            'success': False,
            'error': 'OAuth URL generation failed',
            'message': f'获取OAuth URL失败: {str(e)}'
        }), 500


@jwt_auth_api.route('/oauth/google/callback', methods=['GET'])
def oauth_google_callback():
    """
    Google OAuth回调处理
    将OAuth流程的结果转换为JWT令牌
    """
    try:
        # 这里需要处理OAuth回调并转换为JWT
        # 具体实现需要根据现有的OAuth逻辑来适配
        
        # 暂时返回占位符
        return jsonify({
            'success': False,
            'error': 'Not implemented',
            'message': 'OAuth JWT适配还未实现'
        }), 501
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return jsonify({
            'success': False,
            'error': 'OAuth callback failed',
            'message': f'OAuth回调处理失败: {str(e)}'
        }), 500