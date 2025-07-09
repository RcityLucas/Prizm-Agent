"""
认证路由集成模块

将认证路由集成到主应用中
"""
from flask import Blueprint, request, jsonify, redirect, url_for, session, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_session import Session

from rainbow_agent.auth.models import User
from rainbow_agent.auth.oauth import OAuthService
from rainbow_agent.auth.storage import UserStorage, SurrealUserStorage
from rainbow_agent.config.auth_config import update_flask_config
from rainbow_agent.utils.logger import get_logger

# 配置日志
logger = get_logger(__name__)

# 全局变量
oauth_service = None
user_storage = None
login_manager = None

# 初始化状态标志
_auth_components_initialized = False

def init_auth_components(app, force=False):
    """
    初始化认证组件
    
    Args:
        app: Flask应用
        force: 是否强制重新初始化，即使已经初始化过
    """
    global oauth_service, user_storage, login_manager, _auth_components_initialized
    
    # 检查是否已经初始化
    if _auth_components_initialized and not force:
        logger.info("认证组件已经初始化，跳过重复初始化")
        return
    
    # 更新Flask配置
    update_flask_config(app)
    
    # 初始化Flask-Session
    Session(app)
    logger.info("Flask-Session 初始化成功")
    
    # 初始化用户存储
    try:
        # 从统一存储系统获取数据库客户端
        from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage
        storage_instance = UnifiedDialogueStorage()
        
        # 检查数据库可用性
        if not storage_instance or not storage_instance.shared_client:
            raise Exception("无法获取SurrealDB客户端，请检查SurrealDB是否正在运行")
        
        # 初始化SurrealDB用户存储
        user_storage = SurrealUserStorage(db_client=storage_instance.shared_client)
        logger.info("SurrealDB用户存储初始化成功")
        
        # 验证数据库连接和模式
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 初始化并验证数据库模式
        loop.run_until_complete(user_storage.init_db_schema())
        schema_status = loop.run_until_complete(user_storage.check_db_schema())
        
        if schema_status.get('status') != 'success':
            raise Exception(f"数据库模式验证失败: {schema_status}")
            
    except Exception as e:
        logger.error(f"SurrealDB用户存储初始化失败: {e}")
        logger.error("由于用户数据必须存储在SurrealDB中，请确保SurrealDB正在运行并可访问")
        raise e
    
    # 初始化OAuth服务
    oauth_service = OAuthService(app, user_storage)
    logger.info(f"OAuth服务初始化完成，使用存储类型: {type(user_storage).__name__}")
    
    # 初始化LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'pages.login'
    
    # 注册用户加载函数
    @login_manager.user_loader
    def load_user(user_id):
        return user_storage.get_user_sync(user_id)
    
    # 标记为已初始化
    _auth_components_initialized = True
    logger.info("认证组件初始化完成")

def register_auth_routes(app):
    """
    注册认证路由到Flask应用
    
    Args:
        app: Flask应用
    """
    # 初始化认证组件
    init_auth_components(app)
    
    # 导入认证路由
    from rainbow_agent.auth.routes import auth_api
    
    # 注册认证路由
    app.register_blueprint(auth_api)
    
    logger.info("认证路由已注册")
