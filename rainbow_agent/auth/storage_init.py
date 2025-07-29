"""
SurrealDB用户存储初始化

确保SurrealDB用户存储正确初始化，并提供测试功能
"""
import logging
import asyncio
from typing import Optional

from rainbow_agent.auth.models import User
from rainbow_agent.auth.surreal_user_storage import SurrealUserStorage

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def initialize_surreal_storage() -> SurrealUserStorage:
    """
    初始化SurrealDB用户存储并验证连接
    
    Returns:
        SurrealUserStorage实例
    """
    try:
        # 创建SurrealDB用户存储实例
        storage = SurrealUserStorage()
        
        # 测试连接
        await storage.db.connect()
        
        # 确保表结构存在
        await storage._ensure_schema()
        
        logger.info("SurrealDB用户存储初始化成功")
        return storage
    except Exception as e:
        logger.error(f"SurrealDB用户存储初始化失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

async def test_user_operations():
    """
    测试用户操作
    """
    try:
        # 初始化存储
        storage = await initialize_surreal_storage()
        
        # 测试创建用户
        import uuid
        import bcrypt
        
        user_id = str(uuid.uuid4())
        username = f"test_user_{user_id[:8]}"
        password = "test_password"
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        test_user = User(
            id=user_id,
            name=username,
            email=f"{username}@test.com",
            provider="local",
            provider_id=user_id,
            avatar_url=None
        )
        # 设置username和password_hash
        setattr(test_user, 'username', username)
        setattr(test_user, 'password_hash', password_hash)
        
        # 创建用户
        logger.info(f"创建测试用户: {username}")
        created_user = await storage.create_user(test_user)
        logger.info(f"测试用户创建成功: {created_user.id}")
        
        # 测试通过用户名获取用户
        found_user = await storage.get_user_by_username(username)
        if found_user:
            logger.info(f"通过用户名找到用户: {found_user.id}")
        else:
            logger.error(f"通过用户名未找到用户: {username}")
        
        # 测试通过ID获取用户
        found_user_by_id = await storage.get_user(user_id)
        if found_user_by_id:
            logger.info(f"通过ID找到用户: {found_user_by_id.id}")
        else:
            logger.error(f"通过ID未找到用户: {user_id}")
        
        # 测试获取所有用户
        all_users = await storage.get_all_users()
        logger.info(f"找到 {len(all_users)} 个用户")
        
        # 测试删除用户
        delete_success = await storage.delete_user(user_id)
        logger.info(f"删除用户{'成功' if delete_success else '失败'}: {user_id}")
        
        return True
    except Exception as e:
        logger.error(f"测试用户操作失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # 运行测试
    loop = asyncio.get_event_loop()
    success = loop.run_until_complete(test_user_operations())
    
    if success:
        logger.info("SurrealDB用户存储测试成功")
    else:
        logger.error("SurrealDB用户存储测试失败")
