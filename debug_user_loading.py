#!/usr/bin/env python3
"""
调试用户加载问题
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rainbow_agent.auth.storage import SurrealUserStorage
from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage

def test_user_loading():
    print("=== 调试用户加载 ===")
    
    try:
        # 初始化存储
        storage_instance = UnifiedDialogueStorage()
        user_storage = SurrealUserStorage(db_client=storage_instance.shared_client)
        
        # 测试获取所有用户
        print("\n1. 获取所有用户")
        all_users = user_storage.get_all_users_sync()
        print(f"找到 {len(all_users)} 个用户")
        
        for i, user in enumerate(all_users):
            print(f"\n用户 {i+1}:")
            print(f"  - Raw ID: {user.id} (type: {type(user.id)})")
            print(f"  - get_id(): {user.get_id()} (type: {type(user.get_id())})")
            print(f"  - username: {getattr(user, 'username', 'N/A')}")
            print(f"  - name: {user.name}")
            
            # 测试用该ID能否找到用户
            if hasattr(user, 'username') and user.username == 'testuser':
                test_id = user.get_id()
                print(f"\n2. 测试通过 get_id() 查找用户: {test_id}")
                found_user = user_storage.get_user_sync(test_id)
                if found_user:
                    print(f"  ✓ 成功找到用户: {found_user.username}")
                else:
                    print(f"  ✗ 无法找到用户")
                
                # 测试用原始ID查找用户
                raw_id = user.id
                if isinstance(raw_id, dict) and 'id' in raw_id:
                    actual_id = raw_id['id']
                    print(f"\n3. 测试通过原始ID查找用户: {actual_id}")
                    found_user2 = user_storage.get_user_sync(actual_id)
                    if found_user2:
                        print(f"  ✓ 成功找到用户: {found_user2.username}")
                    else:
                        print(f"  ✗ 无法找到用户")
                break
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_user_loading()