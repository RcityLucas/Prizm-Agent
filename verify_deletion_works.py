#!/usr/bin/env python3
"""
验证删除是否真的生效
"""

import sys
import os
import requests
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_deletion_works():
    """验证删除是否真的生效"""
    print("=== 验证删除是否真的生效 ===\n")
    
    BASE_URL = "http://localhost:5000"
    AUTH_API_BASE = f"{BASE_URL}/api/auth"
    
    # 1. 创建一个新的测试用户
    timestamp = int(time.time())
    username = f"verify_delete_{timestamp}"
    password = "test123"
    
    print(f"1. 创建新测试用户: {username}")
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
    
    # 2. 直接查询数据库确认用户存在
    try:
        from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage
        
        storage = UnifiedDialogueStorage()
        client = storage.shared_client
        
        # 查询用户是否存在
        print(f"\n2. 数据库查询确认用户存在...")
        query_sql = f"SELECT * FROM users WHERE username = '{username}'"
        query_result = client.execute_sql(query_sql)
        
        if query_result and len(query_result) > 0:
            print(f"✅ 用户在数据库中存在: {len(query_result)} 条记录")
            db_user = query_result[0]
            db_user_id = db_user['id']['id'] if isinstance(db_user['id'], dict) else db_user['id']
            print(f"数据库中的用户ID: {db_user_id}")
        else:
            print(f"❌ 用户在数据库中不存在")
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
        
        # 4. 使用API删除用户
        print(f"\n4. 使用API删除用户...")
        delete_response = session.delete(f"{AUTH_API_BASE}/user")
        print(f"删除API响应: {delete_response.status_code} - {delete_response.json()}")
        
        if delete_response.status_code != 200:
            print(f"❌ 删除API调用失败")
            return
        
        # 5. 立即使用数据库查询验证删除
        print(f"\n5. 数据库查询验证删除...")
        verify_sql = f"SELECT * FROM users WHERE username = '{username}'"
        verify_result = client.execute_sql(verify_sql)
        
        if not verify_result or len(verify_result) == 0:
            print(f"✅ 数据库确认用户已删除")
        else:
            print(f"❌ 数据库显示用户仍存在: {len(verify_result)} 条记录")
            for user in verify_result:
                user_id_field = user.get('id', {})
                if isinstance(user_id_field, dict) and 'id' in user_id_field:
                    actual_id = user_id_field['id']
                else:
                    actual_id = str(user_id_field)
                print(f"  仍存在的用户: {user.get('username')} (ID: {actual_id})")
        
        # 6. 尝试再次登录验证
        print(f"\n6. 尝试再次登录验证...")
        verify_login = requests.post(f"{AUTH_API_BASE}/login", json={
            "username": username,
            "password": password
        })
        
        if verify_login.status_code == 200:
            print(f"❌ 用户仍可登录，删除未完全生效")
            print(f"登录响应: {verify_login.json()}")
        else:
            print(f"✅ 用户无法登录，删除已生效")
            print(f"登录失败响应: {verify_login.json()}")
        
        # 7. 检查用户总数变化
        print(f"\n7. 检查用户总数变化...")
        count_sql = "SELECT count() FROM users"
        count_result = client.execute_sql(count_sql)
        total_count = count_result[0]['count'] if count_result and len(count_result) > 0 else 0
        print(f"当前用户总数: {total_count}")
        
        # 8. 列出所有测试用户
        print(f"\n8. 列出所有测试相关用户...")
        test_users_sql = "SELECT username, id FROM users"
        test_users = client.execute_sql(test_users_sql)
        
        test_count = 0
        for user in (test_users or []):
            if isinstance(user, dict):
                db_username = user.get('username', 'N/A')
                if any(keyword in db_username.lower() for keyword in ['test', 'debug', 'verify', 'quick']):
                    test_count += 1
                    user_id_field = user.get('id', {})
                    if isinstance(user_id_field, dict) and 'id' in user_id_field:
                        actual_id = user_id_field['id']
                    else:
                        actual_id = str(user_id_field)
                    print(f"  测试用户: {db_username} (ID: {actual_id})")
        
        print(f"测试相关用户总数: {test_count}")
        
    except Exception as e:
        print(f"数据库验证失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_deletion_works()