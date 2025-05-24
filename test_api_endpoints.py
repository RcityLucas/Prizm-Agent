#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试API端点的脚本，使用requests库直接发送请求
"""
import requests
import json
import sys

BASE_URL = "http://localhost:5001"

def test_endpoint(endpoint, method="GET", data=None):
    """测试指定的API端点"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n测试 {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=data, headers=headers)
        else:
            print(f"不支持的HTTP方法: {method}")
            return
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {response.headers}")
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                print(f"响应内容:\n{json.dumps(json_response, ensure_ascii=False, indent=2)}")
            except json.JSONDecodeError:
                print(f"响应内容不是有效的JSON: {response.text[:200]}")
        else:
            print(f"错误响应: {response.text[:200]}")
    
    except Exception as e:
        print(f"请求出错: {e}")

def main():
    """主函数"""
    # 测试工具列表API
    test_endpoint("/api/dialogue/tools")
    
    # 测试会话列表API
    test_endpoint("/api/dialogue/sessions")
    
    # 测试创建会话API
    test_endpoint("/api/dialogue/sessions", "POST", {"userId": "test_user"})
    
    # 测试系统状态API
    test_endpoint("/api/system/status")

if __name__ == "__main__":
    main()
