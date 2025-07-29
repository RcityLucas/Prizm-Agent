"""
JWT Token 认证适配器
用于前后端分离架构的Token-based认证
"""

import jwt
import datetime
from typing import Dict, Any, Optional, Tuple
from functools import wraps
from flask import current_app, request, jsonify
from rainbow_agent.auth.models import User
from rainbow_agent.auth.storage import UserStorage
from rainbow_agent.utils.logger import get_logger

logger = get_logger(__name__)


class JWTAuthService:
    """JWT认证服务"""
    
    def __init__(self, app=None, user_storage: UserStorage = None):
        self.app = app
        self.user_storage = user_storage
        self.secret_key = None
        self.algorithm = 'HS256'
        self.access_token_expires = datetime.timedelta(hours=24)
        self.refresh_token_expires = datetime.timedelta(days=30)
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用配置"""
        self.app = app
        self.secret_key = app.config.get('JWT_SECRET_KEY', app.config['SECRET_KEY'])
        
        # 配置项
        self.access_token_expires = datetime.timedelta(
            hours=app.config.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 24)
        )
        self.refresh_token_expires = datetime.timedelta(
            days=app.config.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 30)
        )
    
    def generate_tokens(self, user: User) -> Dict[str, str]:
        """
        生成访问令牌和刷新令牌
        
        Args:
            user: 用户对象
            
        Returns:
            包含access_token和refresh_token的字典
        """
        now = datetime.datetime.utcnow()
        
        # 访问令牌载荷
        access_payload = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'roles': user.roles,
            'iat': now,
            'exp': now + self.access_token_expires,
            'type': 'access'
        }
        
        # 刷新令牌载荷
        refresh_payload = {
            'user_id': user.id,
            'iat': now,
            'exp': now + self.refresh_token_expires,
            'type': 'refresh'
        }
        
        # 生成令牌
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': int(self.access_token_expires.total_seconds()),
            'user': user.to_dict()
        }
    
    def verify_token(self, token: str, token_type: str = 'access') -> Optional[Dict[str, Any]]:
        """
        验证JWT令牌
        
        Args:
            token: JWT令牌
            token_type: 令牌类型 ('access' 或 'refresh')
            
        Returns:
            解码的载荷或None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 检查令牌类型
            if payload.get('type') != token_type:
                logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
                return None
                
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """
        使用刷新令牌生成新的访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            新的令牌对或None
        """
        payload = self.verify_token(refresh_token, 'refresh')
        if not payload:
            return None
        
        # 获取用户信息
        user = self.user_storage.get_user_sync(payload['user_id'])
        if not user:
            logger.warning(f"User not found for refresh token: {payload['user_id']}")
            return None
        
        # 生成新的令牌对
        return self.generate_tokens(user)
    
    def get_current_user_from_token(self, token: str) -> Optional[User]:
        """
        从令牌获取当前用户
        
        Args:
            token: 访问令牌
            
        Returns:
            用户对象或None
        """
        payload = self.verify_token(token, 'access')
        if not payload:
            return None
        
        return self.user_storage.get_user_sync(payload['user_id'])


# JWT认证装饰器
def jwt_required(f):
    """JWT认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头获取令牌
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'Missing token',
                'message': '未提供访问令牌'
            }), 401
        
        # 验证令牌
        from flask import current_app
        jwt_service = current_app.jwt_service
        
        payload = jwt_service.verify_token(token)
        if not payload:
            return jsonify({
                'success': False,
                'error': 'Invalid token',
                'message': '无效的访问令牌'
            }), 401
        
        # 获取用户信息
        user = jwt_service.get_current_user_from_token(token)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'message': '用户不存在'
            }), 401
        
        # 将用户信息添加到请求上下文
        request.current_user = user
        
        return f(*args, **kwargs)
    
    return decorated


def optional_jwt_auth(f):
    """可选JWT认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头获取令牌
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        request.current_user = None
        
        if token:
            # 验证令牌
            from flask import current_app
            jwt_service = current_app.jwt_service
            
            user = jwt_service.get_current_user_from_token(token)
            request.current_user = user
        
        return f(*args, **kwargs)
    
    return decorated