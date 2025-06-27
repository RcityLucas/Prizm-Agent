"""
认证路由集成模块

将认证路由集成到主应用中
"""
from flask import Blueprint, request, jsonify, redirect, url_for, session, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_session import Session

from rainbow_agent.auth.models import User
from rainbow_agent.auth.oauth import OAuthService
from rainbow_agent.auth.storage import UserStorage, FileUserStorage, SurrealUserStorage
from rainbow_agent.config.auth_config import update_flask_config
from rainbow_agent.utils.logger import get_logger

# 配置日志
logger = get_logger(__name__)

# 全局变量
oauth_service = None
user_storage = None
login_manager = None

def init_auth_components(app):
    """
    初始化认证组件
    
    Args:
        app: Flask应用
    """
    global oauth_service, user_storage, login_manager
    
    # 更新Flask配置
    update_flask_config(app)
    
    # 初始化Flask-Session
    Session(app)
    logger.info("Flask-Session 初始化成功")
    
    # 初始化用户存储
    try:
        # 强制使用SurrealDB存储
        # 从统一存储系统获取数据库客户端
        from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage
        storage_instance = UnifiedDialogueStorage()
        logger.info(f"统一存储实例: {storage_instance}")
        logger.info(f"数据库客户端: {storage_instance.shared_client if storage_instance else None}")
        
        # 检查数据库可用性
        if not storage_instance or not storage_instance.shared_client:
            logger.error("无法获取SurrealDB客户端，请检查SurrealDB是否正在运行")
            raise Exception("无法获取SurrealDB客户端")
            
        # 检查数据库连接状态
        logger.info(f"SurrealDB连接状态: {storage_instance.shared_client.conn if hasattr(storage_instance.shared_client, 'conn') else '未知'}")
        
        # 初始化SurrealDB用户存储
        user_storage = SurrealUserStorage(db_client=storage_instance.shared_client)
        logger.info(f"SurrealDB用户存储初始化成功，存储类型: {type(user_storage).__name__}")
        
        # 验证数据库连接和模式
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        # 验证数据库模式
        try:
            # 先尝试初始化模式
            loop.run_until_complete(user_storage.init_db_schema())
            
            # 然后验证模式
            schema_status = loop.run_until_complete(user_storage.check_db_schema())
            logger.info(f"初始化时数据库模式验证结果: {schema_status}")
            
            if schema_status.get('status') != 'success':
                logger.error(f"数据库模式验证失败: {schema_status}")
                raise Exception(f"数据库模式验证失败: {schema_status}")
                
            # 测试数据库连接
            test_user = User(
                id="test_user_id",
                email="test@example.com",
                name="Test User",
                provider="test",
                provider_id="test_id"
            )
            test_result = user_storage.db.execute_sql(f"SELECT * FROM {user_storage.table} LIMIT 1")
            logger.info(f"测试查询结果: {test_result}")
            
        except Exception as schema_e:
            logger.error(f"初始化时验证数据库模式失败: {schema_e}")
            raise Exception(f"初始化时验证数据库模式失败: {schema_e}")
            
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
