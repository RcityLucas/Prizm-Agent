#!/usr/bin/env python3
"""
模拟前端请求来调试认证问题
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_frontend_like_requests():
    print("=== 模拟前端请求测试 ===")
    
    # 测试不同的请求方式
    test_scenarios = [
        {
            "name": "场景1: 使用 requests.Session (推荐)",
            "use_session": True,
            "credentials": True
        },
        {
            "name": "场景2: 不使用 Session",
            "use_session": False, 
            "credentials": True
        },
        {
            "name": "场景3: 手动管理 Cookies",
            "use_session": False,
            "credentials": True,
            "manual_cookies": True
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n{'='*60}")
        print(f"测试 {scenario['name']}")
        print(f"{'='*60}")
        
        if scenario['use_session']:
            test_with_session(scenario)
        else:
            test_without_session(scenario)

def test_with_session(scenario):
    """使用 requests.Session 测试"""
    session = requests.Session()
    
    # 设置通用 headers
    session.headers.update({
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Frontend Test)'
    })
    
    print("\n1. 用户登录")
    login_data = {"username": "testuser", "password": "testpass"}
    login_response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
    
    print(f"登录状态码: {login_response.status_code}")
    print(f"登录响应: {login_response.json()}")
    print(f"登录 Cookies: {dict(login_response.cookies)}")
    print(f"Session Cookies: {dict(session.cookies)}")
    
    if login_response.status_code == 200:
        print("\n2. 检查登录状态")
        status_response = session.get(f"{BASE_URL}/api/auth/status")
        print(f"状态码: {status_response.status_code}")
        print(f"状态响应: {status_response.json()}")
        
        print("\n3. 获取会话列表")
        sessions_response = session.get(f"{BASE_URL}/api/dialogue/sessions")
        print(f"会话状态码: {sessions_response.status_code}")
        try:
            sessions_data = sessions_response.json()
            print(f"会话响应: {sessions_data.get('success', 'Unknown')}")
            if 'error' in sessions_data:
                print(f"错误信息: {sessions_data['error']}")
        except:
            print(f"会话响应 (原始): {sessions_response.text}")

def test_without_session(scenario):
    """不使用 Session 测试"""
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Frontend Test)'
    }
    
    print("\n1. 用户登录")
    login_data = {"username": "testuser", "password": "testpass"}
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, headers=headers)
    
    print(f"登录状态码: {login_response.status_code}")
    print(f"登录响应: {login_response.json()}")
    print(f"登录 Cookies: {dict(login_response.cookies)}")
    
    if login_response.status_code == 200:
        # 获取 cookies
        cookies = login_response.cookies
        
        print("\n2. 检查登录状态 (携带 cookies)")
        status_response = requests.get(f"{BASE_URL}/api/auth/status", headers=headers, cookies=cookies)
        print(f"状态码: {status_response.status_code}")
        print(f"状态响应: {status_response.json()}")
        
        print("\n3. 获取会话列表 (携带 cookies)")
        sessions_response = requests.get(f"{BASE_URL}/api/dialogue/sessions", headers=headers, cookies=cookies)
        print(f"会话状态码: {sessions_response.status_code}")
        try:
            sessions_data = sessions_response.json()
            print(f"会话响应: {sessions_data.get('success', 'Unknown')}")
            if 'error' in sessions_data:
                print(f"错误信息: {sessions_data['error']}")
        except:
            print(f"会话响应 (原始): {sessions_response.text}")

def test_javascript_like_requests():
    """模拟 JavaScript fetch 请求"""
    print(f"\n{'='*60}")
    print("模拟 JavaScript fetch 请求")
    print(f"{'='*60}")
    
    # 创建 session 来模拟浏览器行为
    session = requests.Session()
    
    # 模拟浏览器 headers
    browser_headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json',
        'Origin': 'http://localhost:3000',
        'Referer': 'http://localhost:3000/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    session.headers.update(browser_headers)
    
    print("\n1. 模拟前端登录请求")
    login_data = {"username": "testuser", "password": "testpass"}
    
    # 模拟 fetch 带 credentials: 'include'
    login_response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
    
    print(f"登录状态码: {login_response.status_code}")
    print(f"登录响应: {login_response.json()}")
    print(f"Response Headers: {dict(login_response.headers)}")
    print(f"Cookies: {dict(session.cookies)}")
    
    if login_response.status_code == 200:
        print("\n2. 模拟前端获取会话请求")
        # 模拟带 credentials: 'include' 的请求
        sessions_response = session.get(f"{BASE_URL}/api/dialogue/sessions")
        
        print(f"会话状态码: {sessions_response.status_code}")
        print(f"会话响应头: {dict(sessions_response.headers)}")
        
        try:
            sessions_data = sessions_response.json()
            print(f"会话响应成功: {sessions_data.get('success', 'Unknown')}")
            if not sessions_data.get('success', True):
                print(f"错误信息: {sessions_data.get('error', 'Unknown error')}")
            else:
                print(f"会话数量: {len(sessions_data.get('sessions', []))}")
        except Exception as e:
            print(f"解析响应失败: {e}")
            print(f"原始响应: {sessions_response.text[:200]}...")

if __name__ == "__main__":
    test_frontend_like_requests()
    test_javascript_like_requests()