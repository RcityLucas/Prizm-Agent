#!/usr/bin/env python3
"""
认证系统配置验证脚本

验证数据库配置一致性，检测和修复导致"用户不存在"错误的根本原因。
"""

import os
import sys
import time
import logging
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = str(Path(__file__).absolute().parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# 配置基础日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_surreal_connection():
    """检查SurrealDB连接状态"""
    print("\n🔍 检查SurrealDB连接状态...")
    
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ SurrealDB HTTP接口可访问")
            return True
        else:
            print(f"❌ SurrealDB HTTP接口返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ SurrealDB连接失败: {e}")
        return False

def validate_unified_client_config():
    """验证统一客户端配置"""
    print("\n🔍 验证统一客户端配置...")
    
    try:
        from rainbow_agent.storage.surreal.unified_client import UnifiedSurrealClient
        from rainbow_agent.config.settings import get_settings
        
        # 获取配置
        settings = get_settings()
        print("📋 检查SurrealDB配置:")
        print(f"  - URL: {settings.get('storage.url')}")
        print(f"  - Namespace: {settings.get('storage.namespace')}")  
        print(f"  - Database: {settings.get('storage.database')}")
        print(f"  - Username: {settings.get('storage.username')}")
        
        # 创建统一客户端
        client = UnifiedSurrealClient(
            url=settings.get('storage.url'),
            namespace=settings.get('storage.namespace'),
            database=settings.get('storage.database'),
            username=settings.get('storage.username'),
            password=settings.get('storage.password')
        )
        
        # 测试连接
        test_sql = "SELECT count() FROM users LIMIT 1;"
        result = client.execute_sql(test_sql)
        print(f"✅ 统一客户端连接测试成功，查询结果: {len(result) if result else 0}")
        
        return client
        
    except Exception as e:
        print(f"❌ 统一客户端配置验证失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return None

def validate_storage_consistency():
    """验证存储实例一致性"""
    print("\n🔍 验证存储实例一致性...")
    
    try:
        # 模拟注册流程获取存储实例
        print("📋 模拟注册流程:")
        from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage
        from rainbow_agent.auth.storage import SurrealUserStorage
        
        # 注册存储实例
        register_storage_instance = UnifiedDialogueStorage()
        register_user_storage = SurrealUserStorage(db_client=register_storage_instance.shared_client)
        
        print(f"  - 注册存储实例ID: {id(register_storage_instance)}")
        print(f"  - 注册用户存储ID: {id(register_user_storage)}")
        print(f"  - 注册数据库客户端ID: {id(register_storage_instance.shared_client)}")
        
        # 模拟登录流程获取存储实例  
        print("📋 模拟登录流程:")
        login_storage_instance = UnifiedDialogueStorage()
        login_user_storage = SurrealUserStorage(db_client=login_storage_instance.shared_client)
        
        print(f"  - 登录存储实例ID: {id(login_storage_instance)}")
        print(f"  - 登录用户存储ID: {id(login_user_storage)}")
        print(f"  - 登录数据库客户端ID: {id(login_storage_instance.shared_client)}")
        
        # 检查一致性
        if id(register_storage_instance.shared_client) == id(login_storage_instance.shared_client):
            print("✅ 存储客户端实例一致")
        else:
            print("⚠️ 存储客户端实例不一致 - 这可能是问题根源!")
            
        # 测试两个实例查询相同数据
        print("\n📋 测试数据一致性:")
        register_users = register_user_storage.get_all_users_sync()
        login_users = login_user_storage.get_all_users_sync()
        
        print(f"  - 注册存储查询到用户数: {len(register_users)}")
        print(f"  - 登录存储查询到用户数: {len(login_users)}")
        
        if len(register_users) == len(login_users):
            print("✅ 数据查询结果一致")
            return True
        else:
            print("❌ 数据查询结果不一致!")
            return False
            
    except Exception as e:
        print(f"❌ 存储一致性验证失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return False

def test_auth_workflow():
    """测试完整的认证工作流"""
    print("\n🔍 测试完整认证工作流...")
    
    test_username = f"test_user_{int(time.time())}"
    test_password = "test_password_123"
    
    try:
        # 导入认证路由模块
        from rainbow_agent.auth.routes import get_user_storage
        
        print(f"📋 测试用户: {test_username}")
        
        # 1. 获取存储实例（模拟注册）
        print("步骤1: 获取注册存储实例")
        register_storage = get_user_storage()
        print(f"  - 注册存储实例ID: {id(register_storage)}")
        
        # 2. 创建测试用户
        print("步骤2: 创建测试用户")
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
        
        if not saved_user:
            print("❌ 用户创建失败")
            return False
            
        # 3. 获取存储实例（模拟登录）
        print("步骤3: 获取登录存储实例")
        login_storage = get_user_storage()
        print(f"  - 登录存储实例ID: {id(login_storage)}")
        
        # 检查实例是否相同
        if id(register_storage) == id(login_storage):
            print("✅ 注册和登录使用相同存储实例")
        else:
            print("⚠️ 注册和登录使用不同存储实例")
        
        # 4. 查找用户（模拟登录验证）
        print("步骤4: 查找用户进行登录验证")
        users = login_storage.get_all_users_sync()
        found_user = None
        
        for user in users:
            user_username = getattr(user, 'username', user.name)
            if user_username == test_username:
                found_user = user
                break
                
        if found_user:
            print(f"✅ 找到用户: {getattr(found_user, 'username', found_user.name)}")
            
            # 5. 验证密码
            stored_hash = getattr(found_user, 'password_hash', None)
            if stored_hash and bcrypt.checkpw(test_password.encode('utf-8'), stored_hash.encode('utf-8')):
                print("✅ 密码验证成功")
                result = True
            else:
                print("❌ 密码验证失败")
                result = False
        else:
            print("❌ 未找到用户 - 这就是问题所在!")
            print(f"数据库中共有 {len(users)} 个用户:")
            for i, user in enumerate(users):
                user_username = getattr(user, 'username', user.name)
                print(f"  用户{i+1}: {user_username}")
            result = False
            
        # 6. 清理测试用户
        print("步骤5: 清理测试用户")
        if saved_user:
            delete_success = register_storage.delete_user_sync(user_id)
            print(f"  - 用户删除结果: {delete_success}")
            
        return result
        
    except Exception as e:
        print(f"❌ 认证工作流测试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return False

def provide_solutions():
    """提供解决方案"""
    print("\n💡 解决方案建议:")
    
    print("1. 🔧 立即修复方案:")
    print("   - 重启SurrealDB服务确保数据库状态一致")
    print("   - 重启Flask应用清除缓存的存储实例")
    print("   - 设置环境变量强制数据库配置一致性")
    
    print("\n2. 🛡️ 长期解决方案:")
    print("   - 实现存储实例单例模式，确保全局使用同一实例")
    print("   - 添加数据库连接池管理，避免连接不一致")
    print("   - 实现存储实例健康检查和自动重连机制")
    
    print("\n3. 🔍 配置验证:")
    print("   - 添加启动时配置一致性检查")
    print("   - 实现存储实例状态监控")
    print("   - 添加数据库连接测试接口")

def main():
    """主函数"""
    print("🚀 开始认证系统配置验证...")
    print("=" * 60)
    
    # 检查SurrealDB连接
    if not check_surreal_connection():
        print("\n❌ SurrealDB未运行，请先启动数据库服务")
        print("请运行: .\\start-surreal.ps1")
        return False
    
    # 验证统一客户端配置
    if not validate_unified_client_config():
        print("\n❌ 统一客户端配置验证失败")
        return False
    
    # 验证存储一致性
    if not validate_storage_consistency():
        print("\n❌ 存储实例一致性验证失败")
    
    # 测试完整认证工作流
    if test_auth_workflow():
        print("\n✅ 认证工作流测试成功!")
    else:
        print("\n❌ 认证工作流测试失败!")
    
    # 提供解决方案
    provide_solutions()
    
    print("\n" + "=" * 60)
    print("🎯 配置验证完成")
    
    return True

if __name__ == "__main__":
    main()