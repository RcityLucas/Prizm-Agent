#!/usr/bin/env python3
"""
清理测试用户脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def cleanup_test_users():
    """清理所有测试用户"""
    print("=== 清理测试用户 ===\n")
    
    try:
        from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage
        from rainbow_agent.auth.storage import SurrealUserStorage
        
        # 初始化存储
        storage_instance = UnifiedDialogueStorage()
        user_storage = SurrealUserStorage(db_client=storage_instance.shared_client)
        
        # 1. 查询所有用户
        print("1. 查询所有用户...")
        all_users_sql = "SELECT * FROM users"
        all_users = user_storage.db.execute_sql(all_users_sql)
        
        test_users = []
        total_users = 0
        
        if all_users and len(all_users) > 0:
            for batch in all_users:
                if isinstance(batch, list):
                    for user in batch:
                        if isinstance(user, dict):
                            total_users += 1
                            username = user.get('username', '')
                            user_id = user.get('id', {})
                            
                            # 提取真正的ID
                            if isinstance(user_id, dict) and 'id' in user_id:
                                actual_id = user_id['id']
                            else:
                                actual_id = str(user_id)
                            
                            print(f"   - {username} (ID: {actual_id})")
                            
                            # 如果是测试用户，添加到删除列表
                            if username and ('test' in username.lower() or 'delete' in username.lower()):
                                test_users.append((username, actual_id))
        
        print(f"\n找到 {total_users} 个用户，其中 {len(test_users)} 个测试用户")
        
        # 2. 删除测试用户
        if test_users:
            print(f"\n2. 删除测试用户...")
            for username, user_id in test_users:
                print(f"   删除: {username} (ID: {user_id})")
                
                # 尝试多种删除方法
                deleted = False
                
                # 方法1: DELETE record_id
                try:
                    result1 = user_storage.db.execute_sql(f"DELETE users:{user_id}")
                    print(f"     方法1结果: {result1}")
                    
                    # 验证删除
                    verify = user_storage.db.execute_sql(f"SELECT * FROM users WHERE id.id = '{user_id}'")
                    if not verify or (len(verify) > 0 and len(verify[0]) == 0):
                        print(f"     ✅ 方法1成功删除")
                        deleted = True
                    
                except Exception as e:
                    print(f"     方法1失败: {e}")
                
                # 方法2: DELETE FROM WHERE (如果方法1失败)
                if not deleted:
                    try:
                        result2 = user_storage.db.execute_sql(f"DELETE FROM users WHERE id.id = '{user_id}'")
                        print(f"     方法2结果: {result2}")
                        
                        # 验证删除
                        verify = user_storage.db.execute_sql(f"SELECT * FROM users WHERE id.id = '{user_id}'")
                        if not verify or (len(verify) > 0 and len(verify[0]) == 0):
                            print(f"     ✅ 方法2成功删除")
                            deleted = True
                        
                    except Exception as e:
                        print(f"     方法2失败: {e}")
                
                # 方法3: DELETE FROM WHERE username (如果前两个方法都失败)
                if not deleted:
                    try:
                        result3 = user_storage.db.execute_sql(f"DELETE FROM users WHERE username = '{username}'")
                        print(f"     方法3结果: {result3}")
                        
                        # 验证删除
                        verify = user_storage.db.execute_sql(f"SELECT * FROM users WHERE username = '{username}'")
                        if not verify or (len(verify) > 0 and len(verify[0]) == 0):
                            print(f"     ✅ 方法3成功删除")
                            deleted = True
                        
                    except Exception as e:
                        print(f"     方法3失败: {e}")
                
                if not deleted:
                    print(f"     ❌ 所有方法都失败，无法删除用户")
        else:
            print("\n2. 没有找到测试用户需要清理")
        
        # 3. 最终验证
        print(f"\n3. 最终验证...")
        final_users = user_storage.db.execute_sql("SELECT * FROM users")
        final_count = 0
        
        if final_users and len(final_users) > 0:
            for batch in final_users:
                if isinstance(batch, list):
                    final_count += len(batch)
        
        print(f"清理后剩余用户数: {final_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ 清理失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_unique_test_user():
    """创建一个唯一的测试用户"""
    print("\n=== 创建唯一测试用户 ===\n")
    
    import requests
    import time
    
    BASE_URL = "http://localhost:5000"
    AUTH_API_BASE = f"{BASE_URL}/api/auth"
    
    # 使用时间戳确保唯一性
    timestamp = int(time.time())
    username = f"test_delete_{timestamp}"
    password = "test123456"
    
    print(f"创建用户: {username}")
    
    register_response = requests.post(f"{AUTH_API_BASE}/register", json={
        "username": username,
        "password": password
    })
    
    print(f"注册状态: {register_response.status_code}")
    
    if register_response.status_code == 201:
        print(f"✅ 注册成功: {register_response.json()}")
        return username, password
    else:
        print(f"❌ 注册失败: {register_response.json()}")
        return None, None

if __name__ == "__main__":
    # 先清理测试用户
    if cleanup_test_users():
        # 然后创建一个新的测试用户进行测试
        username, password = create_unique_test_user()
        
        if username and password:
            print(f"\n可以使用以下用户进行测试:")
            print(f"用户名: {username}")
            print(f"密码: {password}")
            
            # 可以在这里直接测试删除功能
            print(f"\n=== 测试删除功能 ===")
            
            import requests
            import time
            
            BASE_URL = "http://localhost:5000"
            AUTH_API_BASE = f"{BASE_URL}/api/auth"
            
            # 登录
            session = requests.Session()
            login_response = session.post(f"{AUTH_API_BASE}/login", json={
                "username": username,
                "password": password
            })
            
            if login_response.status_code == 200:
                print("✅ 登录成功")
                
                # 删除
                delete_response = session.delete(f"{AUTH_API_BASE}/user")
                print(f"删除状态: {delete_response.status_code}")
                print(f"删除响应: {delete_response.json()}")
                
                # 验证
                time.sleep(1)
                verify_login = requests.post(f"{AUTH_API_BASE}/login", json={
                    "username": username,
                    "password": password
                })
                
                if verify_login.status_code == 200:
                    print("❌ 删除失败 - 用户仍可登录")
                else:
                    print("✅ 删除成功 - 用户无法登录")
            else:
                print("❌ 登录失败")
    else:
        print("清理失败，无法继续测试")