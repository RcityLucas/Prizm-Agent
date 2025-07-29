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
        try:
            logger.debug(f"Loading user with ID: {user_id} (type: {type(user_id)})")
            user = user_storage.get_user_sync(user_id)
            if user:
                logger.debug(f"Successfully loaded user: {user.username}")
            else:
                logger.debug(f"User not found for ID: {user_id}")
            return user
        except Exception as e:
            logger.error(f"Error loading user {user_id}: {e}")
            return None
    
    # 标记为已初始化
    _is_initialized = True
    
    logger.info("认证组件初始化完成")

def require_auth(f):
    """需要认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            # 直接返回JSON响应，不抛出异常
            return jsonify({
                "success": False,
                "error": "未授权",
                "message": "请先登录"
            }), 401
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


# 获取用户存储实例
def get_user_storage():
    """获取用户存储实例（单例模式）"""
    try:
        from rainbow_agent.storage.storage_singleton import get_global_user_storage
        user_storage = get_global_user_storage()
        logger.debug(f"获取用户存储实例: {type(user_storage).__name__}, 实例ID: {id(user_storage)}")
        
        # 尝试同步到API模块以保持一致性
        try:
            import rainbow_agent.api.auth_routes
            rainbow_agent.api.auth_routes.user_storage = user_storage
            logger.debug("已将用户存储实例同步到API模块")
        except Exception as sync_err:
            logger.warning(f"无法同步用户存储到API模块: {sync_err}")
            
        return user_storage
        
    except Exception as e:
        logger.error(f"获取用户存储实例失败: {e}")
        raise e

# 用户名密码认证端点
@auth_api.route('/register', methods=['POST'])
def register():
    """用户注册端点"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "无效的请求数据",
                "message": "请提供用户名和密码"
            }), 400
        
        username = data.get('username')
        password = data.get('password')
        
        # 验证数据
        if not username or not password:
            return jsonify({
                "success": False,
                "error": "缺少必要参数",
                "message": "用户名和密码不能为空"
            }), 400
        
        # 获取用户存储实例
        user_storage = get_user_storage()
        logger.info(f"注册使用的存储实例类型: {type(user_storage)}")
        logger.info(f"注册使用的存储实例ID: {id(user_storage)}")
        logger.info(f"注册使用的数据库客户端ID: {id(user_storage.db) if hasattr(user_storage, 'db') else 'None'}")
        
        # 检查用户是否已存在
        existing_users = user_storage.get_all_users_sync()
        for user in existing_users:
            # 更robust的用户名检查
            user_username = None
            if hasattr(user, 'username'):
                user_username = user.username
            elif hasattr(user, 'name') and user.name:
                user_username = user.name
                
            if user_username == username:
                logger.info(f"用户名 {username} 已存在")
                return jsonify({
                    "success": False,
                    "error": "用户已存在",
                    "message": "该用户名已被注册"
                }), 409
        
        # 创建新用户
        import bcrypt
        import uuid
        
        # 生成密码哈希
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # 创建用户对象
        user_id = str(uuid.uuid4())
        new_user = User(
            id=user_id,
            name=username,  # 使用 name 而不是 username
            email=f"{username}@local.user",  # 生成一个本地邮箱
            provider="local",  # 本地认证
            provider_id=user_id,  # 使用用户ID作为provider_id
            avatar_url=None
        )
        # 手动设置 username 和 password_hash 属性
        setattr(new_user, 'username', username)
        setattr(new_user, 'password_hash', password_hash)
        
        # 保存用户
        logger.info(f"准备保存用户: {new_user.username}, ID: {new_user.id}")
        saved_user = user_storage.create_user_sync(new_user)
        
        # 验证保存结果
        logger.info(f"保存结果: {saved_user.id if saved_user else 'None'}")
        
        if not saved_user or not saved_user.id:
            return jsonify({
                "success": False,
                "error": "用户创建失败",
                "message": "服务器内部错误，请稍后再试"
            }), 500
        
        # 立即验证用户是否真的被保存
        logger.info(f"验证用户是否真的被保存...")
        verify_users = user_storage.get_all_users_sync()
        user_found = False
        for u in verify_users:
            # 使用相同的robust检查方法
            user_username = None
            if hasattr(u, 'username'):
                user_username = u.username
            elif hasattr(u, 'name') and u.name:
                user_username = u.name
                
            if user_username == username:
                logger.info(f"✅ 验证成功: 在数据库中找到用户 {username}")
                user_found = True
                break
        
        if not user_found:
            logger.warning(f"⚠️ 验证失败: 在数据库中未找到用户 {username}")
            # 打印详细的用户信息
            for i, u in enumerate(verify_users):
                logger.warning(f"验证用户 {i}: id={getattr(u, 'id', None)}, username={getattr(u, 'username', None)}, name={getattr(u, 'name', None)}")
        
        # 返回成功响应
        return jsonify({
            "success": True,
            "message": "用户注册成功",
            "user": {
                "id": saved_user.id,
                "username": getattr(saved_user, 'username', saved_user.name),
                "display_name": getattr(saved_user, 'display_name', saved_user.name)
            }
        }), 201
        
    except Exception as e:
        logger.error(f"用户注册失败: {e}")
        return jsonify({
            "success": False,
            "error": "注册失败",
            "message": "服务器内部错误，请稍后再试"
        }), 500

@auth_api.route('/login', methods=['POST'])
def login():
    """用户登录端点"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "无效的请求数据",
                "message": "请提供用户名和密码"
            }), 400
        
        username = data.get('username')
        password = data.get('password')
        
        # 验证数据
        if not username or not password:
            return jsonify({
                "success": False,
                "error": "缺少必要参数",
                "message": "用户名和密码不能为空"
            }), 400
        
        # 获取用户存储实例
        storage = get_user_storage()
        logger.info(f"登录使用的存储实例类型: {type(storage)}")
        logger.info(f"登录使用的存储实例ID: {id(storage)}")
        logger.info(f"登录使用的数据库客户端ID: {id(storage.db) if hasattr(storage, 'db') else 'None'}")
        
        # 查找用户
        users = storage.get_all_users_sync()
        logger.info(f"找到 {len(users)} 个用户")
        found_user = None
        
        for user in users:
            # 更robust的用户名检查，支持多种属性名
            user_username = None
            if hasattr(user, 'username'):
                user_username = user.username
            elif hasattr(user, 'name') and user.name:
                user_username = user.name
            
            logger.info(f"检查用户: username={getattr(user, 'username', None)}, name={user.name}, email={user.email}, actual_username={user_username}")
            
            # 检查用户名匹配
            if user_username == username:
                logger.info(f"找到匹配用户: {user_username}")
                found_user = user
                break
        
        if not found_user:
            logger.warning(f"未找到用户名为 '{username}' 的用户")
            # 打印所有用户的详细信息用于调试
            for i, user in enumerate(users):
                logger.warning(f"用户 {i}: id={getattr(user, 'id', None)}, username={getattr(user, 'username', None)}, name={getattr(user, 'name', None)}, email={getattr(user, 'email', None)}")
            
            return jsonify({
                "success": False,
                "error": "用户不存在",
                "message": "用户名或密码错误"
            }), 401
        
        # 验证密码
        import bcrypt
        
        # 获取密码哈希，处理可能不存在的属性
        password_hash = getattr(found_user, 'password_hash', None)
        if not password_hash:
            logger.error(f"用户 {username} 没有密码哈希")
            return jsonify({
                "success": False,
                "error": "密码错误",
                "message": "用户名或密码错误"
            }), 401
        
        logger.info(f"验证用户 {username} 的密码")
        if not bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
            logger.warning(f"用户 {username} 密码验证失败")
            return jsonify({
                "success": False,
                "error": "密码错误",
                "message": "用户名或密码错误"
            }), 401
        
        # 登录用户
        login_user(found_user)
        
        # 返回成功响应
        logger.info(f"用户 {username} 登录成功")
        return jsonify({
            "success": True,
            "message": "登录成功",
            "user": {
                "id": found_user.id,
                "username": getattr(found_user, 'username', found_user.name),
                "display_name": getattr(found_user, 'display_name', found_user.name)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"用户登录失败: {e}")
        return jsonify({
            "success": False,
            "error": "登录失败",
            "message": "服务器内部错误，请稍后再试"
        }), 500

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
    """检查登录状态 - 修改为允许通过用户ID直接获取用户信息"""
    # 检查是否有用户ID参数
    user_id = request.args.get('user_id')
    
    # 如果有用户ID，直接获取用户信息
    if user_id:
        logger.debug(f"Status check with user_id: {user_id}")
        try:
            # 获取用户存储实例
            storage = get_user_storage()
            user = storage.get_user_sync(user_id)
            
            if user:
                return jsonify({
                    "success": True,
                    "message": "获取用户信息成功",
                    "data": {
                        "authenticated": True,
                        "user": user.to_dict()
                    }
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "用户不存在",
                    "data": {
                        "authenticated": False,
                        "user": None
                    }
                })
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return jsonify({
                "success": False,
                "message": f"获取用户信息失败: {str(e)}",
                "data": {
                    "authenticated": False,
                    "user": None
                }
            })
    
    # 否则检查当前用户是否已登录
    logger.debug(f"Status check - current_user: {current_user}, is_authenticated: {current_user.is_authenticated}")
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

@auth_api.route('/user', methods=['DELETE'])
@require_auth
@ensure_initialized
def delete_user():
    """删除用户账户"""
    global user_storage
    
    try:
        # 获取当前用户ID，处理可能的复杂ID格式
        raw_user_id = current_user.id
        
        # 处理SurrealDB的复杂ID格式
        if isinstance(raw_user_id, dict) and 'id' in raw_user_id:
            user_id = raw_user_id['id']
        elif isinstance(raw_user_id, str):
            user_id = raw_user_id
        else:
            user_id = str(raw_user_id)
            
        logger.info(f"开始删除用户: {user_id} (原始ID: {raw_user_id})")
        
        # 验证用户存在
        user = user_storage.get_user_sync(user_id)
        if not user:
            return jsonify({
                "success": False,
                "error": "用户不存在",
                "message": "无法找到要删除的用户"
            }), 404
        
        # 执行删除操作
        success = user_storage.delete_user_sync(user_id)
        
        if success:
            # 登出用户
            logout_user()
            
            logger.info(f"用户删除成功: {user_id}")
            return jsonify({
                "success": True,
                "message": "用户账户已成功删除",
                "data": {
                    "deleted_user_id": user_id,
                    "authenticated": False
                }
            }), 200
        else:
            logger.error(f"用户删除失败: {user_id}")
            return jsonify({
                "success": False,
                "error": "删除失败",
                "message": "无法删除用户账户，请稍后再试"
            }), 500
            
    except Exception as e:
        logger.error(f"删除用户时发生异常: {e}")
        return jsonify({
            "success": False,
            "error": "删除失败",
            "message": "服务器内部错误，请稍后再试"
        }), 500

@auth_api.route('/admin/users/<user_id>', methods=['DELETE'])
@require_auth
@ensure_initialized
def admin_delete_user(user_id: str):
    """管理员删除指定用户（需要管理员权限）"""
    global user_storage
    
    try:
        # 检查当前用户是否有管理员权限
        if not current_user.has_role('admin'):
            return jsonify({
                "success": False,
                "error": "权限不足",
                "message": "只有管理员可以删除其他用户"
            }), 403
        
        # 处理current_user.id的复杂格式
        current_user_id = current_user.id
        if isinstance(current_user_id, dict) and 'id' in current_user_id:
            current_user_id = current_user_id['id']
        elif not isinstance(current_user_id, str):
            current_user_id = str(current_user_id)
        
        # 防止管理员删除自己
        if current_user_id == user_id:
            return jsonify({
                "success": False,
                "error": "操作不允许",
                "message": "不能删除自己的账户，请使用普通删除接口"
            }), 400
        
        logger.info(f"管理员 {current_user.id} 开始删除用户: {user_id}")
        
        # 验证要删除的用户存在
        user = user_storage.get_user_sync(user_id)
        if not user:
            return jsonify({
                "success": False,
                "error": "用户不存在",
                "message": "无法找到要删除的用户"
            }), 404
        
        # 记录用户信息用于日志
        user_info = {
            "id": user.id,
            "username": getattr(user, 'username', None),
            "email": user.email,
            "name": user.name
        }
        
        # 执行删除操作
        success = user_storage.delete_user_sync(user_id)
        
        if success:
            logger.info(f"管理员删除用户成功: {user_info}")
            return jsonify({
                "success": True,
                "message": "用户已成功删除",
                "data": {
                    "deleted_user": user_info,
                    "deleted_by": current_user.id
                }
            }), 200
        else:
            logger.error(f"管理员删除用户失败: {user_id}")
            return jsonify({
                "success": False,
                "error": "删除失败",
                "message": "无法删除指定用户，请稍后再试"
            }), 500
            
    except Exception as e:
        logger.error(f"管理员删除用户时发生异常: {e}")
        return jsonify({
            "success": False,
            "error": "删除失败",
            "message": "服务器内部错误，请稍后再试"
        }), 500

@auth_api.route('/admin/users', methods=['GET'])
@require_auth
@ensure_initialized
def list_users():
    """管理员获取用户列表（需要管理员权限）"""
    global user_storage
    
    try:
        # 检查当前用户是否有管理员权限
        if not current_user.has_role('admin'):
            return jsonify({
                "success": False,
                "error": "权限不足",
                "message": "只有管理员可以查看用户列表"
            }), 403
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 100)  # 限制最大数量
        
        offset = (page - 1) * limit
        
        logger.info(f"管理员 {current_user.id} 获取用户列表: page={page}, limit={limit}")
        
        # 获取用户列表
        users = user_storage.get_all_users_sync(limit=limit, offset=offset)
        
        # 转换为安全的字典格式（不包含敏感信息）
        users_data = []
        for user in users:
            user_dict = {
                "id": user.id,
                "username": getattr(user, 'username', None),
                "email": user.email,
                "name": user.name,
                "provider": user.provider,
                "avatar_url": user.avatar_url,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "roles": user.roles,
                "is_active": user._is_active,
                "language": user.language,
                "timezone": user.timezone
            }
            users_data.append(user_dict)
        
        logger.info(f"返回 {len(users_data)} 个用户信息")
        
        return jsonify({
            "success": True,
            "message": "获取用户列表成功",
            "data": {
                "users": users_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "count": len(users_data)
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"获取用户列表时发生异常: {e}")
        return jsonify({
            "success": False,
            "error": "获取失败",
            "message": "服务器内部错误，请稍后再试"
        }), 500
