#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试聊天 API

测试修复后的聊天 API 是否正常工作。
"""
import os
import sys
import json
import time
import requests
from datetime import datetime

# 设置服务器地址
BASE_URL = "http://localhost:5000"

def print_separator(title):
    """打印分隔符"""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "-"))
    print("=" * 50 + "\n")

def test_chat_api():
    """测试聊天 API"""
    print_separator("测试聊天 API")
    
    url = f"{BASE_URL}/api/chat"
    data = {
        "messages": [
            {"role": "system", "content": "你是一个有用的AI助手，名为Rainbow助手。"},
            {"role": "user", "content": "你好，请介绍一下自己。"}
        ],
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    print(f"请求: POST {url}")
    print(f"数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=data)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"成功: {result.get('success')}")
            
            if result.get('success'):
                response_message = result.get('response', {})
                print(f"响应内容: {response_message.get('content')}")
                print(f"使用情况: {result.get('usage')}")
            else:
                print(f"错误: {result.get('error')}")
        else:
            print(f"响应: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    return None

def test_api_test():
    """测试 API 测试端点"""
    print_separator("测试 API 测试端点")
    
    url = f"{BASE_URL}/api/v1/test"
    
    try:
        response = requests.get(url)
        
        print(f"请求: GET {url}")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        return response.json()
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def test_create_session():
    """测试创建会话"""
    print_separator("测试创建会话")
    
    url = f"{BASE_URL}/api/v1/sessions"
    data = {
        "user_id": "test_user",
        "title": f"测试会话 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "dialogue_type": "human_to_ai_private"
    }
    
    print(f"请求: POST {url}")
    print(f"数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=data)
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        return response.json()
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def test_process_dialogue(session_id=None):
    """测试处理对话"""
    print_separator("测试处理对话")
    
    url = f"{BASE_URL}/api/v1/dialogue/process"
    data = {
        "user_id": "test_user",
        "content": f"这是一条测试消息，发送于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "auto_create_session": True
    }
    
    if session_id:
        data["session_id"] = session_id
    
    print(f"请求: POST {url}")
    print(f"数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=data)
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        return response.json()
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def run_all_tests():
    """运行所有测试"""
    print("\n开始测试修复后的 API...\n")
    
    # 测试 API 测试端点
    test_api_test()
    
    # 测试创建会话
    session_result = test_create_session()
    if session_result and session_result.get('success'):
        session_id = session_result.get('id')
        
        # 测试处理对话（使用已有会话）
        test_process_dialogue(session_id)
    
    # 测试处理对话（自动创建会话）
    test_process_dialogue()
    
    # 测试聊天 API
    test_chat_api()
    
    print("\n所有测试完成！\n")

if __name__ == "__main__":
    run_all_tests()
