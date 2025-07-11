#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试认证流程：用户注册、登录和会话查询
"""

import requests
import json
import sys
import time

# 配置
BASE_URL = "http://localhost:5000"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpass"

# 设置请求会话，保持cookies
session = requests.Session()

def print_separator(title):
    """打印分隔符"""
    print(f"\n== {title} ==")

def main():
    """主测试流程"""
    print(f"使用API基础URL: {BASE_URL}")
    print(f"测试用户: {TEST_USERNAME}")
    
    # 1. 测试用户注册
    print_separator("测试用户注册")
    register_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    register_url = f"{BASE_URL}/api/auth/register"
    print(f"请求 URL: {register_url}")
    print(f"请求数据: {json.dumps(register_data, indent=2)}")
    
    try:
        register_response = session.post(register_url, json=register_data)
        print(f"状态码: {register_response.status_code}")
        try:
            response_json = register_response.json()
            print("响应 JSON:")
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
        except:
            print(f"原始响应: {register_response.text}")
        
        if register_response.status_code == 409:
            print("用户已存在，继续测试登录流程")
        elif register_response.status_code != 201:
            print("注册失败，但继续测试登录流程")
    except Exception as e:
        print(f"注册请求异常: {e}")
        print("继续测试登录流程")
    
    # 2. 测试用户登录
    print_separator("测试用户登录")
    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    login_url = f"{BASE_URL}/api/auth/login"
    print(f"请求 URL: {login_url}")
    print(f"请求数据: {json.dumps(login_data, indent=2)}")
    
    try:
        login_response = session.post(login_url, json=login_data)
        print(f"状态码: {login_response.status_code}")
        try:
            response_json = login_response.json()
            print("响应 JSON:")
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
        except:
            print(f"原始响应: {login_response.text}")
        
        if login_response.status_code != 200:
            print("登录失败，无法继续测试会话查询")
            return
        
        # 解析登录响应
        try:
            user_id = response_json.get("user", {}).get("id")
            print(f"登录成功，用户ID: {user_id}")
        except Exception as e:
            print(f"解析登录响应时出错: {e}")
            user_id = None
    except Exception as e:
        print(f"登录请求异常: {e}")
        return
    
    # 3. 测试会话查询
    print_separator("测试会话查询")
    sessions_url = f"{BASE_URL}/api/dialogue/sessions"
    print(f"请求 URL: {sessions_url}")
    
    try:
        sessions_response = session.get(sessions_url)
        print(f"状态码: {sessions_response.status_code}")
        try:
            response_json = sessions_response.json()
            print("响应 JSON:")
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
        except:
            print(f"原始响应: {sessions_response.text}")
        
        if sessions_response.status_code == 200:
            try:
                sessions_data = response_json.get("sessions", [])
                print(f"找到 {len(sessions_data)} 个会话")
                if sessions_data:
                    for i, session_data in enumerate(sessions_data[:3]):  # 只显示前3个会话
                        print(f"会话 {i+1}:")
                        print(json.dumps(session_data, indent=2, ensure_ascii=False))
                    if len(sessions_data) > 3:
                        print(f"还有 {len(sessions_data) - 3} 个会话未显示...")
            except Exception as e:
                print(f"处理会话数据时出错: {e}")
    except Exception as e:
        print(f"会话查询请求异常: {e}")

if __name__ == "__main__":
    main()
