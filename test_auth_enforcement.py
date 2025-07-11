#!/usr/bin/env python3
"""
测试认证系统修复后的功能
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_auth_enforcement():
    print("=== 测试认证系统修复 ===")
    
    # 测试1: 未登录时访问受保护的端点
    print("\n1. 测试未登录访问受保护端点:")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # 不携带任何认证信息访问sessions端点
    try:
        response = requests.get(f"{BASE_URL}/api/dialogue/sessions", headers=headers)
        print(f"未登录访问状态码: {response.status_code}")
        data = response.json()
        print(f"未登录访问响应: {data}")
        
        if response.status_code == 401:
            print("✅ 认证系统正常工作：未登录用户被正确拒绝")
        else:
            print("❌ 认证系统异常：未登录用户不应该能访问受保护端点")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试2: 登录后访问受保护端点
    print("\n2. 测试登录后访问受保护端点:")
    session = requests.Session()
    
    # 登录
    login_data = {"username": "testuser", "password": "testpass"}
    login_response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
    
    if login_response.status_code == 200:
        print("✅ 登录成功")
        
        # 访问受保护端点
        sessions_response = session.get(f"{BASE_URL}/api/dialogue/sessions")
        print(f"登录后访问状态码: {sessions_response.status_code}")
        
        if sessions_response.status_code == 200:
            data = sessions_response.json()
            print(f"✅ 登录后访问成功，获取到 {len(data.get('sessions', []))} 个会话")
            
            # 检查是否获取的是正确用户的会话
            if data.get('sessions'):
                first_session = data['sessions'][0]
                user_id = first_session.get('user_id')
                print(f"会话所属用户ID: {user_id}")
        else:
            print("❌ 登录后访问失败")
    else:
        print(f"❌ 登录失败: {login_response.status_code}")
    
    # 测试3: 模拟PowerShell请求（无认证）
    print("\n3. 模拟PowerShell请求（无认证）:")
    ps_headers = {
        "Accept": "application/json",
        "Referer": "http://localhost:3000/",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "sec-ch-ua-mobile": "?0",
        "x-internal-api-request": "1",
        "sec-ch-ua-platform": '"Windows"',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        ps_response = requests.get(f"{BASE_URL}/api/dialogue/sessions?_t=1752128498476", 
                                  headers=ps_headers)
        print(f"PowerShell请求状态码: {ps_response.status_code}")
        ps_data = ps_response.json()
        print(f"PowerShell请求响应: {ps_data}")
        
        if ps_response.status_code == 401:
            print("✅ PowerShell请求被正确拒绝")
        else:
            print("❌ PowerShell请求应该被拒绝")
    except Exception as e:
        print(f"PowerShell请求失败: {e}")
    
    # 测试4: 模拟PowerShell请求（有认证）
    print("\n4. 模拟PowerShell请求（有认证）:")
    # 使用已登录的session的cookie
    if 'session' in session.cookies:
        ps_cookies = {'session': session.cookies['session']}
        
        try:
            ps_auth_response = requests.get(f"{BASE_URL}/api/dialogue/sessions?_t=1752128498476",
                                           headers=ps_headers,
                                           cookies=ps_cookies)
            print(f"PowerShell认证请求状态码: {ps_auth_response.status_code}")
            
            if ps_auth_response.status_code == 200:
                ps_auth_data = ps_auth_response.json()
                print(f"✅ PowerShell认证请求成功，获取到 {len(ps_auth_data.get('sessions', []))} 个会话")
            else:
                print("❌ PowerShell认证请求失败")
        except Exception as e:
            print(f"PowerShell认证请求失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_auth_enforcement()