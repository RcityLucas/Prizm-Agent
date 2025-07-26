#!/usr/bin/env python3
"""
全面调试删除问题
"""

import sys
import os
import requests
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def comprehensive_delete_debug():
    """全面调试删除问题"""
    print("=== 全面调试删除问题 ===\n")
    
    BASE_URL = "http://localhost:5000"
    AUTH_API_BASE = f"{BASE_URL}/api/auth"
    
    # 1. 创建测试用户
    timestamp = int(time.time())
    username = f"debug_test_{timestamp}"
    password = "test123"
    
    print(f"1. 创建测试用户: {username}")
    register_response = requests.post(f"{AUTH_API_BASE}/register", json={
        "username": username,
        "password": password
    })
    
    if register_response.status_code != 201:
        print(f"❌ 注册失败: {register_response.json()}")
        return
    
    user_data = register_response.json()['user']
    user_id = user_data['id']
    print(f"✅ 注册成功，用户ID: {user_id}")
    
    # 2. 直接检查数据库中的用户
    try:
        from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage
        from rainbow_agent.auth.storage import SurrealUserStorage
        
        storage_instance = UnifiedDialogueStorage()
        user_storage = SurrealUserStorage(db_client=storage_instance.shared_client)
        
        print(f"\n2. 数据库中查找用户...")
        users_before = user_storage.db.execute_sql("SELECT * FROM users")
        user_count_before = len(users_before) if users_before else 0
        print(f"删除前用户总数: {user_count_before}")
        
        # 查找我们的测试用户
        found_user = None
        for user in (users_before or []):
            if isinstance(user, dict):
                db_user_id = user.get('id', {})
                if isinstance(db_user_id, dict) and 'id' in db_user_id:
                    actual_id = db_user_id['id']
                else:
                    actual_id = str(db_user_id)
                
                if actual_id == user_id:
                    found_user = user
                    print(f"✅ 在数据库中找到用户: {user.get('username')} (ID: {actual_id})")
                    break
        
        if not found_user:
            print(f"❌ 在数据库中未找到用户: {user_id}")
            return
    
        # 3. 登录用户
        print(f"\n3. 登录用户...")
        session = requests.Session()
        login_response = session.post(f"{AUTH_API_BASE}/login", json={
            "username": username,
            "password": password
        })
        
        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.json()}")
            return
        
        print(f"✅ 登录成功")
        
        # 4. 调用删除API
        print(f"\n4. 调用删除API...")
        delete_response = session.delete(f"{AUTH_API_BASE}/user")
        print(f"删除API响应状态: {delete_response.status_code}")
        print(f"删除API响应内容: {delete_response.json()}")
        
        # 5. 立即检查数据库状态
        print(f"\n5. 删除后立即检查数据库状态...")
        users_after = user_storage.db.execute_sql("SELECT * FROM users")
        user_count_after = len(users_after) if users_after else 0
        print(f"删除后用户总数: {user_count_after}")
        
        # 查找我们的测试用户是否还存在
        still_exists = False
        for user in (users_after or []):
            if isinstance(user, dict):
                db_user_id = user.get('id', {})
                if isinstance(db_user_id, dict) and 'id' in db_user_id:
                    actual_id = db_user_id['id']
                else:
                    actual_id = str(db_user_id)
                
                if actual_id == user_id:
                    still_exists = True
                    print(f"❌ 用户仍在数据库中: {user.get('username')} (ID: {actual_id})")
                    break
        
        if not still_exists:
            print(f"✅ 用户已从数据库中删除")
        
        # 6. 尝试再次登录验证
        print(f"\n6. 尝试再次登录验证...")
        verify_login = requests.post(f"{AUTH_API_BASE}/login", json={
            "username": username,
            "password": password
        })
        
        print(f"验证登录状态: {verify_login.status_code}")
        if verify_login.status_code == 200:
            print(f"❌ 用户仍可登录，删除未生效")
            print(f"验证响应: {verify_login.json()}")
        else:
            print(f"✅ 用户无法登录，删除已生效")
            print(f"验证响应: {verify_login.json()}")
        
        # 7. 检查删除API内部的具体执行情况
        print(f"\n7. 直接调用删除方法...")
        try:
            # 直接调用删除方法
            result = user_storage.delete_user_sync(user_id)
            print(f"直接删除方法结果: {result}")
            
            # 再次检查数据库
            final_users = user_storage.db.execute_sql("SELECT * FROM users")
            final_count = len(final_users) if final_users else 0
            print(f"最终用户总数: {final_count}")
            
            # 检查是否还存在
            final_exists = False
            for user in (final_users or []):
                if isinstance(user, dict):
                    db_user_id = user.get('id', {})
                    if isinstance(db_user_id, dict) and 'id' in db_user_id:
                        actual_id = db_user_id['id']
                    else:
                        actual_id = str(db_user_id)
                    
                    if actual_id == user_id:
                        final_exists = True
                        print(f"❌ 用户最终仍存在: {user.get('username')} (ID: {actual_id})")
                        break
            
            if not final_exists:
                print(f"✅ 用户最终已删除")
                
        except Exception as direct_err:
            print(f"直接删除方法异常: {direct_err}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"数据库检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    comprehensive_delete_debug()