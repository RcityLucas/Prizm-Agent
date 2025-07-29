#!/usr/bin/env python3
"""
调试远程服务器存储单例问题
"""

import sys
import os
sys.path.insert(0, '/data/prizmAi/Prizm-Agent')

def debug_storage_creation():
    """调试存储创建过程"""
    print("🔍 调试远程服务器存储单例创建过程")
    print("=" * 50)
    
    try:
        # 1. 测试基础存储创建
        print("1️⃣ 测试基础存储创建...")
        from rainbow_agent.storage.storage_singleton import get_global_storage
        storage = get_global_storage()
        print(f"✅ 基础存储创建成功: {type(storage)}")
        print(f"实例ID: {id(storage)}")
        
        # 2. 检查shared_client
        print("\n2️⃣ 检查shared_client...")
        if hasattr(storage, 'shared_client'):
            print(f"✅ shared_client存在: {type(storage.shared_client)}")
            print(f"shared_client ID: {id(storage.shared_client)}")
        else:
            print("❌ shared_client不存在")
            return False
        
        # 3. 测试用户存储创建
        print("\n3️⃣ 测试用户存储创建...")
        from rainbow_agent.storage.storage_singleton import get_global_user_storage
        user_storage = get_global_user_storage()
        
        print(f"用户存储返回值: {user_storage}")
        print(f"用户存储类型: {type(user_storage)}")
        print(f"是否为None: {user_storage is None}")
        
        if user_storage is not None:
            print(f"✅ 用户存储创建成功: {type(user_storage)}")
            print(f"用户存储实例ID: {id(user_storage)}")
        else:
            print("❌ 用户存储创建失败，返回None")
            return False
        
        # 4. 检查create_user_sync方法是否存在
        print("\n4️⃣ 检查create_user_sync方法...")
        if hasattr(user_storage, 'create_user_sync'):
            print("✅ create_user_sync方法存在")
        else:
            print("❌ create_user_sync方法不存在")
            print(f"可用方法: {[m for m in dir(user_storage) if not m.startswith('_')]}")
            return False
        
        # 5. 测试认证路由中的get_user_storage
        print("\n5️⃣ 测试认证路由中的get_user_storage...")
        from rainbow_agent.auth.routes import get_user_storage as route_get_storage
        route_storage = route_get_storage()
        
        print(f"路由存储返回值: {route_storage}")
        print(f"路由存储类型: {type(route_storage)}")
        print(f"路由存储是否为None: {route_storage is None}")
        
        if route_storage is None:
            print("❌ 路由中的get_user_storage返回None！这就是问题所在！")
            return False
        
        # 6. 检查路由存储和单例存储是否是同一个实例
        print("\n6️⃣ 检查存储实例一致性...")
        if id(route_storage) == id(user_storage):
            print("✅ 路由存储和单例存储是同一个实例")
        else:
            print("❌ 路由存储和单例存储不是同一个实例！")
            print(f"单例存储ID: {id(user_storage)}")
            print(f"路由存储ID: {id(route_storage)}")
        
        print("\n" + "=" * 50)
        print("✅ 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 调试过程中出现异常: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = debug_storage_creation()
    print(f"\n🎯 测试结果: {'成功' if success else '失败'}")