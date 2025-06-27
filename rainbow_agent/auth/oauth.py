"""
OAuth认证服务

提供OAuth认证功能，支持Google和GitHub登录。
"""
import os
import json
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from urllib.parse import urlencode

from authlib.integrations.flask_client import OAuth
from flask import url_for, redirect, session, request, current_app
import requests

from rainbow_agent.auth.models import User
from rainbow_agent.auth.storage import UserStorage
from rainbow_agent.utils.logger import get_logger
from rainbow_agent.config.auth_config import get_oauth_config

# 配置日志
logger = get_logger(__name__)

class OAuthService:
    """OAuth认证服务"""
    
    def __init__(self, app=None, user_storage=None):
        """
        初始化
        
        Args:
            app: Flask应用
            user_storage: 用户存储
        """
        self.oauth = OAuth()
        self.user_storage = user_storage
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        初始化应用
        
        Args:
            app: Flask应用
        """
        # 设置 OAuth
        self.oauth.init_app(app)
        
        # 注册 OAuth 客户端
        self._register_oauth_clients(app)
    
    def _register_oauth_clients(self, app):
        """
        注册OAuth客户端
        
        Args:
            app: Flask应用
        """
        # 创建OAuth对象
        self.oauth = OAuth(app)
        
        # 获取配置
        config = get_oauth_config()
        
        # 注册Google OAuth
        if config.get('GOOGLE_CLIENT_ID') and config.get('GOOGLE_CLIENT_SECRET'):
            self.oauth.register(
                name='google',
                client_id=config.get('GOOGLE_CLIENT_ID'),
                client_secret=config.get('GOOGLE_CLIENT_SECRET'),
                server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
                client_kwargs={
                    'scope': 'openid email profile'
                },
                fetch_token=lambda request: request.session.get('google_token'),
                save_token=lambda token, request: request.session.__setitem__('google_token', token)
            )
            logger.info("Google OAuth客户端注册成功")
        else:
            logger.warning("Google OAuth客户端注册失败: 缺少必要的配置")
        
        # 注册GitHub OAuth
        if config.get('GITHUB_CLIENT_ID') and config.get('GITHUB_CLIENT_SECRET'):
            self.oauth.register(
                name='github',
                client_id=config.get('GITHUB_CLIENT_ID'),
                client_secret=config.get('GITHUB_CLIENT_SECRET'),
                access_token_url='https://github.com/login/oauth/access_token',
                access_token_params=None,
                authorize_url='https://github.com/login/oauth/authorize',
                authorize_params=None,
                api_base_url='https://api.github.com/',
                client_kwargs={'scope': 'user:email'},
                fetch_token=lambda request: request.session.get('github_token'),
                save_token=lambda token, request: request.session.__setitem__('github_token', token)
            )
            logger.info("GitHub OAuth客户端注册成功")
        else:
            logger.warning("GitHub OAuth客户端注册失败: 缺少必要的配置")
    
    def get_oauth_client(self, provider: str):
        """
        获取OAuth客户端
        
        Args:
            provider: 认证提供商
            
        Returns:
            OAuth客户端
        """
        return self.oauth.create_client(provider)
    
    def get_redirect_uri(self, provider: str) -> str:
        """
        获取重定向URI
        
        Args:
            provider: 认证提供商
            
        Returns:
            重定向URI
        """
        return url_for(f'auth.{provider}_callback', _external=True)
    
    async def handle_oauth_callback(self, provider: str, token) -> Tuple[Optional[User], Optional[str]]:
        """
        处理OAuth回调
        
        Args:
            provider: 认证提供商
            token: OAuth令牌
            
        Returns:
            (用户对象, 错误信息)
        """
        if provider == 'google':
            return await self._handle_google_callback(token)
        elif provider == 'github':
            return await self._handle_github_callback(token)
        else:
            return None, f"不支持的认证提供商: {provider}"
    
    async def _handle_google_callback(self, token) -> Tuple[Optional[User], Optional[str]]:
        """
        处理Google回调
        
        Args:
            token: OAuth令牌
            
        Returns:
            (用户对象, 错误信息)
        """
        try:
            # 获取用户信息
            resp = self.oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
            user_info = resp.json()
            
            # 提取用户数据
            provider_id = user_info.get('sub')
            email = user_info.get('email')
            name = user_info.get('name')
            avatar_url = user_info.get('picture')
            
            # 检查是否已存在用户
            user = None
            if self.user_storage:
                user = await self.user_storage.get_user_by_provider('google', provider_id)
                
                # 如果用户不存在但邮箱存在，则关联账号
                if not user and email:
                    user = await self.user_storage.get_user_by_email(email)
                    if user:
                        # 更新提供商信息
                        user.provider = 'google'
                        user.provider_id = provider_id
                        user = await self.user_storage.update_user(user)
            
            # 如果用户不存在，创建新用户
            if not user:
                user = User(
                    email=email,
                    name=name,
                    avatar_url=avatar_url,
                    provider='google',
                    provider_id=provider_id,
                    access_token=token.get('access_token'),
                    refresh_token=token.get('refresh_token'),
                    token_expiry=datetime.now() + timedelta(seconds=token.get('expires_in', 3600)) if token.get('expires_in') else None
                )
                
                if self.user_storage:
                    user = await self.user_storage.create_user(user)
            else:
                # 更新令牌和登录时间
                user.access_token = token.get('access_token')
                user.refresh_token = token.get('refresh_token')
                user.token_expiry = datetime.now() + timedelta(seconds=token.get('expires_in', 3600)) if token.get('expires_in') else None
                user.last_login = datetime.now()
                
                if self.user_storage:
                    user = await self.user_storage.update_user(user)
            
            return user, None
        except Exception as e:
            logger.error(f"处理Google回调失败: {e}")
            return None, f"处理Google回调失败: {e}"
    
    async def _handle_github_callback(self, token) -> Tuple[Optional[User], Optional[str]]:
        """
        处理GitHub回调
        
        Args:
            token: OAuth令牌
            
        Returns:
            (用户对象, 错误信息)
        """
        try:
            # 获取用户信息
            resp = self.oauth.github.get('user', token=token)
            user_info = resp.json()
            
            # 获取邮箱（可能需要额外请求）
            email = user_info.get('email')
            if not email:
                # 获取邮箱列表
                email_resp = self.oauth.github.get('user/emails', token=token)
                emails = email_resp.json()
                
                # 查找主邮箱
                primary_email = next((e for e in emails if e.get('primary')), None)
                if primary_email:
                    email = primary_email.get('email')
                elif emails:
                    email = emails[0].get('email')
            
            # 提取用户数据
            provider_id = str(user_info.get('id'))
            name = user_info.get('name') or user_info.get('login')
            avatar_url = user_info.get('avatar_url')
            
            # 检查是否已存在用户
            user = None
            if self.user_storage:
                user = await self.user_storage.get_user_by_provider('github', provider_id)
                
                # 如果用户不存在但邮箱存在，则关联账号
                if not user and email:
                    user = await self.user_storage.get_user_by_email(email)
                    if user:
                        # 更新提供商信息
                        user.provider = 'github'
                        user.provider_id = provider_id
                        user = await self.user_storage.update_user(user)
            
            # 如果用户不存在，创建新用户
            if not user:
                user = User(
                    email=email,
                    name=name,
                    avatar_url=avatar_url,
                    provider='github',
                    provider_id=provider_id,
                    access_token=token.get('access_token'),
                    refresh_token=token.get('refresh_token'),
                    token_expiry=datetime.now() + timedelta(seconds=token.get('expires_in', 3600)) if token.get('expires_in') else None
                )
                
                if self.user_storage:
                    user = await self.user_storage.create_user(user)
            else:
                # 更新令牌和登录时间
                user.access_token = token.get('access_token')
                user.refresh_token = token.get('refresh_token')
                user.token_expiry = datetime.now() + timedelta(seconds=token.get('expires_in', 3600)) if token.get('expires_in') else None
                user.last_login = datetime.now()
                
                if self.user_storage:
                    user = await self.user_storage.update_user(user)
            
            return user, None
        except Exception as e:
            logger.error(f"处理GitHub回调失败: {e}")
            return None, f"处理GitHub回调失败: {e}"
            
    def handle_oauth_callback_sync(self, provider: str, token) -> Tuple[Optional[User], Optional[str]]:
        """
        同步处理OAuth回调
        
        Args:
            provider: 认证提供商
            token: OAuth令牌
            
        Returns:
            (用户对象, 错误信息)
        """
        if provider == 'google':
            return self._handle_google_callback_sync(token)
        elif provider == 'github':
            return self._handle_github_callback_sync(token)
        else:
            return None, f"不支持的认证提供商: {provider}"
            
    def _handle_google_callback_sync(self, token) -> Tuple[Optional[User], Optional[str]]:
        """
        同步处理Google回调
        
        Args:
            token: OAuth令牌
            
        Returns:
            (用户对象, 错误信息)
        """
        try:
            # 获取用户信息
            resp = self.oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
            user_info = resp.json()
            
            # 提取用户数据
            provider_id = user_info.get('sub')
            email = user_info.get('email')
            name = user_info.get('name')
            avatar_url = user_info.get('picture')
            
            # 检查是否已存在用户
            user = None
            if self.user_storage:
                user = self.user_storage.get_user_by_provider_sync('google', provider_id)
                
                # 如果用户不存在但邮箱存在，则关联账号
                if not user and email:
                    user = self.user_storage.get_user_by_email_sync(email)
                    if user:
                        # 更新提供商信息
                        user.provider = 'google'
                        user.provider_id = provider_id
                        user = self.user_storage.update_user_sync(user)
            
            # 如果用户不存在，创建新用户
            if not user:
                user = User(
                    email=email,
                    name=name,
                    avatar_url=avatar_url,
                    provider='google',
                    provider_id=provider_id,
                    access_token=token.get('access_token'),
                    refresh_token=token.get('refresh_token'),
                    token_expiry=datetime.now() + timedelta(seconds=token.get('expires_in', 3600)) if token.get('expires_in') else None
                )
                
                if self.user_storage:
                    user = self.user_storage.create_user_sync(user)
            else:
                # 更新令牌和登录时间
                user.access_token = token.get('access_token')
                user.refresh_token = token.get('refresh_token')
                user.token_expiry = datetime.now() + timedelta(seconds=token.get('expires_in', 3600)) if token.get('expires_in') else None
                user.last_login = datetime.now()
                
                if self.user_storage:
                    user = self.user_storage.update_user_sync(user)
            
            return user, None
        except Exception as e:
            logger.error(f"处理Google回调失败: {e}")
            return None, f"处理Google回调失败: {e}"
            
    def _handle_github_callback_sync(self, token) -> Tuple[Optional[User], Optional[str]]:
        """
        同步处理GitHub回调
        
        Args:
            token: OAuth令牌
            
        Returns:
            (用户对象, 错误信息)
        """
        try:
            # 获取用户信息
            resp = self.oauth.github.get('user', token=token)
            user_info = resp.json()
            
            # 获取邮箱（可能需要额外请求）
            email = user_info.get('email')
            if not email:
                # 获取邮箱列表
                email_resp = self.oauth.github.get('user/emails', token=token)
                emails = email_resp.json()
                
                # 查找主邮箱
                primary_email = next((e for e in emails if e.get('primary')), None)
                if primary_email:
                    email = primary_email.get('email')
                elif emails:
                    email = emails[0].get('email')
            
            # 提取用户数据
            provider_id = str(user_info.get('id'))
            name = user_info.get('name') or user_info.get('login')
            avatar_url = user_info.get('avatar_url')
            
            # 检查是否已存在用户
            user = None
            if self.user_storage:
                user = self.user_storage.get_user_by_provider_sync('github', provider_id)
                
                # 如果用户不存在但邮箱存在，则关联账号
                if not user and email:
                    user = self.user_storage.get_user_by_email_sync(email)
                    if user:
                        # 更新提供商信息
                        user.provider = 'github'
                        user.provider_id = provider_id
                        user = self.user_storage.update_user_sync(user)
            
            # 如果用户不存在，创建新用户
            if not user:
                user = User(
                    email=email,
                    name=name,
                    avatar_url=avatar_url,
                    provider='github',
                    provider_id=provider_id,
                    access_token=token.get('access_token'),
                    refresh_token=token.get('refresh_token'),
                    token_expiry=datetime.now() + timedelta(seconds=token.get('expires_in', 3600)) if token.get('expires_in') else None
                )
                
                if self.user_storage:
                    user = self.user_storage.create_user_sync(user)
            else:
                # 更新令牌和登录时间
                user.access_token = token.get('access_token')
                user.refresh_token = token.get('refresh_token')
                user.token_expiry = datetime.now() + timedelta(seconds=token.get('expires_in', 3600)) if token.get('expires_in') else None
                user.last_login = datetime.now()
                
                if self.user_storage:
                    user = self.user_storage.update_user_sync(user)
            
            return user, None
        except Exception as e:
            logger.error(f"处理GitHub回调失败: {e}")
            return None, f"处理GitHub回调失败: {e}"
