#!/usr/bin/env python3
"""
修复用户认证存储一致性问题
"""
import requests
import json
import sys
import time

def test_auth_flow(base_url="http://47.236.10.92:5000"):
    """测试完整的认证流程"""
    
    # 创建一个会话对象来保持cookie
    session = requests.Session()
    
    # 使用时间戳创建唯一用户名
    timestamp = int(time.time())
    username = f"test_user_{timestamp}"
    password = "test123456"
    
    print(f"🧪 开始测试用户认证流程")
    print(f"📍 服务器: {base_url}")
    print(f"👤 测试用户: {username}")
    print(f"🔐 密码: {password}")
    print("-" * 50)
    
    # Step 1: 注册用户
    print("1️⃣ 注册用户...")
    register_data = {
        "username": username,
        "password": password
    }
    
    try:
        register_response = session.post(
            f"{base_url}/api/auth/register",
            json=register_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   📨 注册请求: {register_response.status_code}")
        register_result = register_response.json()
        print(f"   📋 注册响应: {json.dumps(register_result, indent=2, ensure_ascii=False)}")
        
        if not register_result.get("success"):
            print(f"❌ 注册失败: {register_result.get('message')}")
            return False
            
        user_id = register_result["user"]["id"]
        print(f"✅ 注册成功，用户ID: {user_id}")
        
    except Exception as e:
        print(f"❌ 注册请求失败: {e}")
        return False
    
    # 等待一秒确保数据写入
    print("⏰ 等待1秒确保数据写入...")
    time.sleep(1)
    
    # Step 2: 立即尝试登录
    print("2️⃣ 尝试登录...")
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        login_response = session.post(
            f"{base_url}/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   📨 登录请求: {login_response.status_code}")
        login_result = login_response.json()
        print(f"   📋 登录响应: {json.dumps(login_result, indent=2, ensure_ascii=False)}")
        
        if login_result.get("success"):
            print(f"✅ 登录成功")
            
            # Step 3: 检查认证状态
            print("3️⃣ 检查认证状态...")
            status_response = session.get(f"{base_url}/api/auth/status")
            status_result = status_response.json()
            print(f"   📋 状态响应: {json.dumps(status_result, indent=2, ensure_ascii=False)}")
            
            if status_result["data"]["authenticated"]:
                print("✅ 认证状态正确")
                
                # Step 4: 删除用户账户（清理）
                print("4️⃣ 删除测试账户...")
                delete_response = session.delete(f"{base_url}/api/auth/user")
                delete_result = delete_response.json()
                print(f"   📋 删除响应: {json.dumps(delete_result, indent=2, ensure_ascii=False)}")
                
                if delete_result.get("success"):
                    print("✅ 测试账户删除成功")
                    print("🎉 完整认证流程测试通过！")
                    return True
                else:
                    print(f"⚠️ 删除失败，但认证流程正常: {delete_result.get('message')}")
                    return True
            else:
                print("❌ 认证状态检查失败")
                return False
        else:
            print(f"❌ 登录失败: {login_result.get('message')}")
            print(f"🔍 错误详情: {login_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return False

def test_user_storage_debug(base_url="http://47.236.10.92:5000"):
    """测试并调试用户存储问题"""
    
    print("🔬 开始存储一致性调试测试")
    print("-" * 50)
    
    # 创建会话
    session = requests.Session()
    
    # 创建测试用户
    timestamp = int(time.time())
    username = f"debug_user_{timestamp}"
    password = "debug123"
    
    print(f"🔧 创建调试用户: {username}")
    
    # 注册
    register_response = session.post(
        f"{base_url}/api/auth/register",
        json={"username": username, "password": password},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"📊 注册响应码: {register_response.status_code}")
    
    if register_response.status_code == 200:
        register_result = register_response.json()
        print(f"✅ 注册成功: {register_result['user']['id']}")
        
        # 多次尝试登录，观察结果
        for i in range(3):
            print(f"\n🔄 第 {i+1} 次登录尝试...")
            time.sleep(0.5)  # 短暂延迟
            
            login_response = session.post(
                f"{base_url}/api/auth/login",
                json={"username": username, "password": password},
                headers={"Content-Type": "application/json"}
            )
            
            login_result = login_response.json()
            print(f"   状态码: {login_response.status_code}")
            print(f"   成功: {login_result.get('success')}")
            print(f"   消息: {login_result.get('message')}")
            print(f"   错误: {login_result.get('error')}")
            
            if login_result.get("success"):
                print("   ✅ 登录成功！")
                break
            else:
                print("   ❌ 登录失败")
        
    else:
        print(f"❌ 注册失败: {register_response.status_code}")

if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://47.236.10.92:5000"
    
    print("🚀 Prizm Agent 认证系统测试工具")
    print("=" * 60)
    
    # 运行测试
    success = test_auth_flow(base_url)
    
    if not success:
        print("\n🔬 运行调试测试...")
        test_user_storage_debug(base_url)
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 所有测试通过！认证系统工作正常。")
    else:
        print("❌ 认证系统存在问题，请检查服务器日志。")