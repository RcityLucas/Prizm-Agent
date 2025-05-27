#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试修复后的 API

测试修复后的 API 是否正常工作，包括会话创建、对话处理等功能。
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

def test_api_test():
    """测试API测试端点"""
    print_separator("测试 API 测试端点")
    
    url = f"{BASE_URL}/api/v1/test"
    response = requests.get(url)
    
    print(f"请求: GET {url}")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()

def test_dialogue_types():
    """测试获取对话类型"""
    print_separator("测试获取对话类型")
    
    url = f"{BASE_URL}/api/v1/dialogue_types"
    response = requests.get(url)
    
    print(f"请求: GET {url}")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()

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
    
    response = requests.post(url, json=data)
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()

def test_get_sessions():
    """测试获取会话列表"""
    print_separator("测试获取会话列表")
    
    url = f"{BASE_URL}/api/v1/sessions"
    response = requests.get(url)
    
    print(f"请求: GET {url}")
    print(f"状态码: {response.status_code}")
    
    # 只打印会话数量和第一个会话的详情，避免输出过多
    data = response.json()
    sessions = data.get("sessions", [])
    print(f"会话数量: {len(sessions)}")
    
    if sessions:
        print(f"第一个会话: {json.dumps(sessions[0], indent=2, ensure_ascii=False)}")
    
    return data

def test_get_session(session_id):
    """测试获取会话详情"""
    print_separator(f"测试获取会话详情: {session_id}")
    
    url = f"{BASE_URL}/api/v1/sessions/{session_id}"
    response = requests.get(url)
    
    print(f"请求: GET {url}")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        session = data.get("session", {})
        turns = session.get("turns", [])
        
        print(f"会话ID: {session.get('id')}")
        print(f"标题: {session.get('title')}")
        print(f"对话类型: {session.get('dialogue_type')}")
        print(f"创建时间: {session.get('created_at')}")
        print(f"轮次数量: {len(turns)}")
        
        if turns:
            print("\n前两个轮次:")
            for i, turn in enumerate(turns[:2]):
                print(f"  轮次 {i+1}:")
                print(f"    ID: {turn.get('id')}")
                print(f"    角色: {turn.get('role')}")
                print(f"    内容: {turn.get('content')}")
    else:
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()

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
    
    response = requests.post(url, json=data)
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()

def test_create_turn(session_id):
    """测试创建轮次"""
    print_separator(f"测试创建轮次: {session_id}")
    
    url = f"{BASE_URL}/api/v1/sessions/{session_id}/turns"
    data = {
        "role": "user",
        "content": f"这是一条手动创建的轮次消息，发送于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "metadata": {
            "user_id": "test_user",
            "client": "test_script"
        }
    }
    
    print(f"请求: POST {url}")
    print(f"数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    response = requests.post(url, json=data)
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()

def test_get_turns(session_id):
    """测试获取轮次"""
    print_separator(f"测试获取轮次: {session_id}")
    
    url = f"{BASE_URL}/api/v1/sessions/{session_id}/turns"
    response = requests.get(url)
    
    print(f"请求: GET {url}")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        turns = data.get("turns", [])
        
        print(f"轮次数量: {len(turns)}")
        
        if turns:
            print("\n所有轮次:")
            for i, turn in enumerate(turns):
                print(f"  轮次 {i+1}:")
                print(f"    ID: {turn.get('id')}")
                print(f"    角色: {turn.get('role')}")
                print(f"    内容: {turn.get('content')}")
    else:
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()

def run_all_tests():
    """运行所有测试"""
    print("\n开始测试修复后的 API...\n")
    
    # 测试 API 测试端点
    test_api_test()
    
    # 测试获取对话类型
    test_dialogue_types()
    
    # 测试创建会话
    session_result = test_create_session()
    session_id = session_result.get("id")
    
    if session_id:
        # 测试获取会话列表
        test_get_sessions()
        
        # 测试获取会话详情
        test_get_session(session_id)
        
        # 测试创建轮次
        test_create_turn(session_id)
        
        # 测试获取轮次
        test_get_turns(session_id)
        
        # 测试处理对话（使用已有会话）
        test_process_dialogue(session_id)
    
    # 测试处理对话（自动创建会话）
    dialogue_result = test_process_dialogue()
    new_session_id = dialogue_result.get("session_id")
    
    if new_session_id:
        # 测试获取会话详情
        test_get_session(new_session_id)
        
        # 测试获取轮次
        test_get_turns(new_session_id)
    
    print("\n所有测试完成！\n")

if __name__ == "__main__":
    run_all_tests()
