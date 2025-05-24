#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试API端点的简单脚本
"""
import requests
import json

BASE_URL = "http://localhost:5001"

def test_dialogue_tools():
    """测试获取工具列表API"""
    url = f"{BASE_URL}/api/dialogue/tools"
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

def test_dialogue_sessions():
    """测试获取会话列表API"""
    url = f"{BASE_URL}/api/dialogue/sessions"
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

if __name__ == "__main__":
    print("测试工具列表API...")
    test_dialogue_tools()
    print("\n测试会话列表API...")
    test_dialogue_sessions()
