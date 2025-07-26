#!/usr/bin/env python3
"""
检查系统使用的存储类型
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_storage_type():
    """检查系统使用的存储类型"""
    print("=== 检查存储类型 ===\n")
    
    try:
        # 检查API存储
        from rainbow_agent.api.auth_routes import user_storage as api_storage
        print(f"API存储类型: {type(api_storage).__name__ if api_storage else 'None'}")
        print(f"API存储实例: {api_storage}")
        
        # 检查Auth存储
        from rainbow_agent.auth.routes import get_user_storage
        auth_storage = get_user_storage()
        print(f"Auth存储类型: {type(auth_storage).__name__ if auth_storage else 'None'}")
        print(f"Auth存储实例: {auth_storage}")
        
        print(f"存储实例相同: {api_storage is auth_storage}")
        
        # 检查数据库客户端
        if hasattr(auth_storage, 'db'):
            print(f"数据库客户端: {type(auth_storage.db).__name__}")
            print(f"数据库客户端实例: {auth_storage.db}")
        
        # 测试简单查询
        if auth_storage:
            print(f"\n测试查询所有用户...")
            try:
                users = auth_storage.get_all_users_sync()
                print(f"用户数量: {len(users)}")
                
                if users:
                    print("前3个用户:")
                    for i, user in enumerate(users[:3]):
                        username = getattr(user, 'username', 'N/A')
                        print(f"  {i+1}. {username} ({user.id})")
            except Exception as e:
                print(f"查询失败: {e}")
        
        # 检查是否为SurrealDB存储
        if hasattr(auth_storage, 'db') and hasattr(auth_storage.db, 'execute_sql'):
            print(f"\n测试SurrealDB连接...")
            try:
                result = auth_storage.db.execute_sql("SELECT count() FROM users")
                print(f"用户数量查询结果: {result}")
            except Exception as e:
                print(f"SurrealDB查询失败: {e}")
        
        return auth_storage
        
    except Exception as e:
        print(f"检查存储类型失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_direct_sql_delete():
    """直接测试SQL删除"""
    print("\n=== 直接测试SQL删除 ===\n")
    
    storage = check_storage_type()
    
    if not storage or not hasattr(storage, 'db'):
        print("无法获取SurrealDB存储")
        return
    
    # 查询所有用户
    try:
        users_sql = "SELECT * FROM users LIMIT 5"
        users_result = storage.db.execute_sql(users_sql)
        print(f"当前用户查询结果: {users_result}")
        
        if users_result and len(users_result) > 0:
            for batch in users_result:
                if isinstance(batch, list):
                    for user in batch:
                        if isinstance(user, dict):
                            user_id = user.get('id', {}).get('id') if isinstance(user.get('id'), dict) else user.get('id')
                            username = user.get('username')
                            print(f"  找到用户: {username} (ID: {user_id})")
                            
                            # 如果这是测试用户，尝试删除
                            if username and 'test' in username:
                                print(f"  尝试删除测试用户: {username}")
                                
                                # 尝试多种删除方法
                                delete_methods = [
                                    f"DELETE users:{user_id}",
                                    f"DELETE FROM users WHERE id.id = '{user_id}'",
                                    f"DELETE FROM users WHERE username = '{username}'"
                                ]
                                
                                for method in delete_methods:
                                    try:
                                        print(f"    尝试: {method}")
                                        result = storage.db.execute_sql(method)
                                        print(f"    结果: {result}")
                                        
                                        # 验证是否删除
                                        verify = storage.db.execute_sql(f"SELECT * FROM users WHERE username = '{username}'")
                                        if not verify or (len(verify) > 0 and len(verify[0]) == 0):
                                            print(f"    ✅ 删除成功")
                                            break
                                        else:
                                            print(f"    ❌ 仍然存在")
                                    except Exception as e:
                                        print(f"    错误: {e}")
                                break
                break
                        
    except Exception as e:
        print(f"SQL操作失败: {e}")

if __name__ == "__main__":
    check_storage_type()
    test_direct_sql_delete()