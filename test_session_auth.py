#!/usr/bin/env python3
"""
测试会话权限的脚本
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_session_auth():
    print("=== 测试会话权限 ===")
    
    # 创建会话以保持 cookies
    session = requests.Session()
    
    # 1. 先登录
    print("\n1. 用户登录")
    login_data = {
        "username": "testuser",
        "password": "testpass"
    }
    
    login_response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"登录状态码: {login_response.status_code}")
    print(f"登录响应: {login_response.json()}")
    
    if login_response.status_code != 200:
        print("登录失败，无法继续测试")
        return
    
    # 2. 检查登录状态
    print("\n2. 检查登录状态")
    status_response = session.get(f"{BASE_URL}/api/auth/status")
    print(f"状态码: {status_response.status_code}")
    print(f"状态响应: {status_response.json()}")
    
    # 3. 获取会话列表
    print("\n3. 获取会话列表")
    sessions_response = session.get(f"{BASE_URL}/api/dialogue/sessions")
    print(f"会话状态码: {sessions_response.status_code}")
    print(f"会话响应: {sessions_response.json()}")
    
    # 4. 检查 cookies
    print("\n4. 检查 cookies")
    print(f"Cookies: {session.cookies}")
    
    # 5. 检查 headers
    print("\n5. 检查响应头")
    print(f"Login response headers: {dict(login_response.headers)}")
    print(f"Sessions response headers: {dict(sessions_response.headers)}")

if __name__ == "__main__":
    test_session_auth()