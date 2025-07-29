#!/usr/bin/env python3
"""
认证存储单例修复脚本

实现全局存储实例单例模式，确保注册和登录使用同一数据库连接。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = str(Path(__file__).absolute().parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

def create_singleton_storage():
    """创建单例存储修复文件"""
    storage_singleton_content = '''"""
全局存储单例模块

确保整个应用使用同一个存储实例，避免注册和登录连接不一致问题。
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 全局存储实例
_global_storage_instance = None
_global_user_storage = None

def get_global_storage():
    """
    获取全局存储实例（单例模式）
    
    Returns:
        UnifiedDialogueStorage实例
    """
    global _global_storage_instance
    
    if _global_storage_instance is None:
        logger.info("创建全局存储实例（单例）")
        from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage
        _global_storage_instance = UnifiedDialogueStorage()
        logger.info(f"全局存储实例创建完成，实例ID: {id(_global_storage_instance)}")
        logger.info(f"全局数据库客户端ID: {id(_global_storage_instance.shared_client)}")
    else:
        logger.debug(f"复用全局存储实例，实例ID: {id(_global_storage_instance)}")
    
    return _global_storage_instance

def get_global_user_storage():
    """
    获取全局用户存储实例（单例模式）
    
    Returns:
        SurrealUserStorage实例
    """
    global _global_user_storage
    
    if _global_user_storage is None:
        logger.info("创建全局用户存储实例（单例）")
        from rainbow_agent.auth.storage import SurrealUserStorage
        storage_instance = get_global_storage()
        _global_user_storage = SurrealUserStorage(db_client=storage_instance.shared_client)
        logger.info(f"全局用户存储实例创建完成，实例ID: {id(_global_user_storage)}")
        logger.info(f"使用数据库客户端ID: {id(storage_instance.shared_client)}")
    else:
        logger.debug(f"复用全局用户存储实例，实例ID: {id(_global_user_storage)}")
    
    return _global_user_storage

def reset_global_storage():
    """重置全局存储实例（用于测试或重启）"""
    global _global_storage_instance, _global_user_storage
    logger.info("重置全局存储实例")
    _global_storage_instance = None
    _global_user_storage = None
'''
    
    # 写入存储单例文件
    singleton_path = "/mnt/e/github/Prizm-Agent/rainbow_agent/storage/storage_singleton.py"
    with open(singleton_path, 'w', encoding='utf-8') as f:
        f.write(storage_singleton_content)
    
    print(f"✅ 创建存储单例文件: {singleton_path}")
    return singleton_path

def patch_auth_routes():
    """修补认证路由以使用单例存储"""
    auth_routes_path = "/mnt/e/github/Prizm-Agent/rainbow_agent/auth/routes.py"
    
    # 读取原文件
    with open(auth_routes_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换get_user_storage函数
    old_function = '''# 获取用户存储实例
def get_user_storage():
    """获取用户存储实例，如果未初始化则尝试初始化"""
    global user_storage
    
    # 如果已经有实例，验证实例是否仍然有效
    if user_storage is not None:
        try:
            # 验证存储实例是否仍然可用
            if hasattr(user_storage, 'db') and user_storage.db:
                logger.info(f"复用现有存储实例: {type(user_storage).__name__}, 实例ID: {id(user_storage)}")
                return user_storage
        except Exception as e:
            logger.warning(f"现有存储实例验证失败: {e}, 重新创建")
            user_storage = None
    
    # 创建新的用户存储实例
    try:
        # 从统一存储系统获取数据库客户端
        from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage
        
        # 创建新的用户存储实例
        storage_instance = UnifiedDialogueStorage()
        
        # 检查数据库可用性
        if not storage_instance or not storage_instance.shared_client:
            raise Exception("无法获取SurrealDB客户端，请检查SurrealDB是否正在运行")
        
        # 初始化SurrealDB用户存储
        from rainbow_agent.auth.storage import SurrealUserStorage
        user_storage = SurrealUserStorage(db_client=storage_instance.shared_client)
        logger.info(f"创建新的SurrealDB用户存储实例: {type(user_storage).__name__}, 实例ID: {id(user_storage)}, 数据库客户端ID: {id(storage_instance.shared_client)}")
        
        # 尝试同步到API模块以保持一致性
        try:
            import rainbow_agent.api.auth_routes
            rainbow_agent.api.auth_routes.user_storage = user_storage
            logger.info("已将用户存储实例同步到API模块")
        except Exception as sync_err:
            logger.warning(f"无法同步用户存储到API模块: {sync_err}")
            
    except Exception as e:
        logger.error(f"获取用户存储实例失败: {e}")
        raise e
    
    return user_storage'''
    
    new_function = '''# 获取用户存储实例
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
        raise e'''
    
    if old_function in content:
        new_content = content.replace(old_function, new_function)
        
        # 写入修改后的文件
        with open(auth_routes_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ 已修补认证路由文件: {auth_routes_path}")
        return True
    else:
        print("⚠️ 未找到目标函数，可能已经修改过")
        return False

def create_test_script():
    """创建测试脚本验证修复效果"""
    test_content = '''#!/usr/bin/env python3
"""
测试单例存储修复效果
"""

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = str(Path(__file__).absolute().parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

def test_singleton_storage():
    """测试单例存储"""
    print("🔍 测试单例存储修复效果...")
    
    try:
        from rainbow_agent.storage.storage_singleton import get_global_user_storage, reset_global_storage
        
        # 重置以确保干净的测试环境
        reset_global_storage()
        
        # 第一次获取
        print("📋 第一次获取存储实例:")
        storage1 = get_global_user_storage()
        print(f"  - 存储实例ID: {id(storage1)}")
        print(f"  - 数据库客户端ID: {id(storage1.db)}")
        
        # 第二次获取
        print("📋 第二次获取存储实例:")
        storage2 = get_global_user_storage()
        print(f"  - 存储实例ID: {id(storage2)}")
        print(f"  - 数据库客户端ID: {id(storage2.db)}")
        
        # 验证是否是同一实例
        if id(storage1) == id(storage2) and id(storage1.db) == id(storage2.db):
            print("✅ 单例模式工作正常，两次获取的是同一实例")
            return True
        else:
            print("❌ 单例模式失败，获取了不同的实例")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_auth_workflow():
    """测试认证工作流"""
    print("\\n🔍 测试认证工作流...")
    
    test_username = f"singleton_test_{int(time.time())}"
    test_password = "test_password_123"
    
    try:
        from rainbow_agent.auth.routes import get_user_storage
        
        # 模拟注册
        print("📋 模拟注册流程:")
        register_storage = get_user_storage()
        print(f"  - 注册存储实例ID: {id(register_storage)}")
        print(f"  - 注册数据库客户端ID: {id(register_storage.db)}")
        
        # 创建测试用户
        from rainbow_agent.auth.models import User
        import bcrypt
        import uuid
        
        password_hash = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user_id = str(uuid.uuid4())
        
        new_user = User(
            id=user_id,
            name=test_username,
            email=f"{test_username}@test.local",
            provider="local",
            provider_id=user_id,
            avatar_url=None
        )
        setattr(new_user, 'username', test_username)
        setattr(new_user, 'password_hash', password_hash)
        
        saved_user = register_storage.create_user_sync(new_user)
        print(f"  - 用户创建结果: {saved_user.id if saved_user else 'None'}")
        
        # 模拟登录
        print("📋 模拟登录流程:")
        login_storage = get_user_storage()
        print(f"  - 登录存储实例ID: {id(login_storage)}")
        print(f"  - 登录数据库客户端ID: {id(login_storage.db)}")
        
        # 检查是否是同一实例
        same_instance = id(register_storage) == id(login_storage)
        same_db_client = id(register_storage.db) == id(login_storage.db)
        
        print(f"  - 存储实例相同: {same_instance}")
        print(f"  - 数据库客户端相同: {same_db_client}")
        
        if same_instance and same_db_client:
            print("✅ 单例修复成功，注册和登录使用同一存储实例")
        else:
            print("❌ 单例修复失败")
            
        # 查找用户
        users = login_storage.get_all_users_sync()
        found_user = None
        
        for user in users:
            user_username = getattr(user, 'username', user.name)
            if user_username == test_username:
                found_user = user
                break
                
        if found_user:
            print("✅ 找到创建的测试用户")
            
            # 验证密码
            stored_hash = getattr(found_user, 'password_hash', None)
            if stored_hash and bcrypt.checkpw(test_password.encode('utf-8'), stored_hash.encode('utf-8')):
                print("✅ 密码验证成功")
                result = True
            else:
                print("❌ 密码验证失败")
                result = False
        else:
            print("❌ 未找到创建的测试用户")
            result = False
            
        # 清理
        if saved_user:
            register_storage.delete_user_sync(user_id)
            print("📋 清理测试用户完成")
            
        return result
        
    except Exception as e:
        print(f"❌ 认证工作流测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始测试单例存储修复效果...")
    print("=" * 50)
    
    # 测试单例存储
    if not test_singleton_storage():
        print("❌ 单例存储测试失败")
        return False
    
    # 测试认证工作流
    if not test_auth_workflow():
        print("❌ 认证工作流测试失败")
        return False
    
    print("\\n" + "=" * 50)
    print("✅ 所有测试通过，单例存储修复成功!")
    return True

if __name__ == "__main__":
    main()
'''
    
    test_path = "/mnt/e/github/Prizm-Agent/test_singleton_fix.py"
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"✅ 创建测试脚本: {test_path}")
    return test_path

def main():
    """主函数"""
    print("🚀 开始修复认证存储单例问题...")
    print("=" * 60)
    
    # 1. 创建存储单例模块
    singleton_path = create_singleton_storage()
    
    # 2. 修补认证路由
    if patch_auth_routes():
        print("✅ 认证路由修补成功")
    else:
        print("⚠️ 认证路由修补跳过")
    
    # 3. 创建测试脚本
    test_path = create_test_script()
    
    print("\\n" + "=" * 60)
    print("🎯 修复完成！")
    print("\\n📋 下一步操作:")
    print("1. 重启Flask应用以应用修复")
    print("2. 运行测试脚本验证修复效果:")
    print(f"   python3 {test_path}")
    print("3. 测试实际的注册登录功能")
    
    return True

if __name__ == "__main__":
    main()