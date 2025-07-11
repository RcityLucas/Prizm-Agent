#!/usr/bin/env python3
"""
简单的用户存储测试脚本，用于验证用户创建和查询功能
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rainbow_agent.auth.models import User
from rainbow_agent.auth.storage import SurrealUserStorage
from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage

def test_user_storage():
    print("=== 测试用户存储功能 ===")
    
    try:
        # 初始化存储
        storage_instance = UnifiedDialogueStorage()
        user_storage = SurrealUserStorage(db_client=storage_instance.shared_client)
        
        print("✓ 用户存储初始化成功")
        
        # 创建测试用户
        import uuid
        import bcrypt
        
        test_user = User(
            id=str(uuid.uuid4()),
            name="testuser",
            email=None,
            provider=None,
            provider_id=None,
            avatar_url=None
        )
        test_user.username = "testuser"
        test_user.password_hash = bcrypt.hashpw("testpass".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        print(f"✓ 创建测试用户对象: {test_user.id}")
        print(f"  - username: {test_user.username}")
        print(f"  - password_hash: {test_user.password_hash[:20]}...")
        
        # 保存用户
        saved_user = user_storage.create_user_sync(test_user)
        print(f"✓ 用户保存结果: {saved_user.id}")
        
        # 查询所有用户
        all_users = user_storage.get_all_users_sync()
        print(f"✓ 查询到 {len(all_users)} 个用户")
        
        for i, user in enumerate(all_users):
            print(f"  用户 {i+1}:")
            print(f"    - ID: {user.id}")
            print(f"    - name: {user.name}")
            print(f"    - email: {user.email}")
            print(f"    - username: {getattr(user, 'username', 'NOT_SET')}")
            print(f"    - password_hash: {getattr(user, 'password_hash', 'NOT_SET')}")
            
        # 测试用户名查找
        target_username = "testuser"
        found_user = None
        for user in all_users:
            if hasattr(user, 'username') and user.username == target_username:
                found_user = user
                break
                
        if found_user:
            print(f"✓ 成功找到用户: {found_user.username}")
            
            # 测试密码验证
            import bcrypt
            if bcrypt.checkpw("testpass".encode('utf-8'), found_user.password_hash.encode('utf-8')):
                print("✓ 密码验证成功")
            else:
                print("✗ 密码验证失败")
        else:
            print(f"✗ 没有找到用户名为 '{target_username}' 的用户")
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_user_storage()