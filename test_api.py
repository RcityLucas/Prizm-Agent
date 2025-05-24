#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试API端点的简单脚本
"""
import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def print_separator():
    print("="*80)

def test_api(name, url, method="GET", data=None):
    """测试API端点并格式化输出"""
    print_separator()
    print(f"测试: {name}")
    print(f"URL: {url}")
    print(f"方法: {method}")
    if data:
        print(f"数据: {json.dumps(data, ensure_ascii=False)}")
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            print(f"不支持的方法: {method}")
            return
        
        print(f"状态码: {response.status_code}")
        
        # 尝试解析响应为JSON
        try:
            json_response = response.json()
            print(f"响应内容: {json.dumps(json_response, indent=2, ensure_ascii=False)}")
            return json_response
        except ValueError:
            print(f"响应不是JSON格式: {response.text[:200]}...")
            return response.text
    
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
    
    print_separator()
    print()

def test_dialogue_tools():
    """测试获取工具列表API"""
    url = f"{BASE_URL}/api/dialogue/tools"
    test_api("获取工具列表", url)

def test_dialogue_sessions():
    """测试获取会话列表API"""
    url = f"{BASE_URL}/api/dialogue/sessions"
    test_api("获取会话列表", url)

def test_create_session():
    """测试创建新会话API"""
    url = f"{BASE_URL}/api/dialogue/sessions"
    data = {
        "userId": "test_user",
        "title": f"测试会话 - {json.dumps({"时间": str(requests.get('http://worldtimeapi.org/api/timezone/Asia/Shanghai').json()['datetime'])})}",
        "dialogueType": "HUMAN_AI_PRIVATE",
        "participants": [
            {
                "id": "test_user",
                "name": "测试用户",
                "type": "human"
            },
            {
                "id": "ai_assistant",
                "name": "Rainbow助手",
                "type": "ai"
            }
        ]
    }
    session = test_api("创建新会话", url, "POST", data)
    return session

def test_get_session(session_id):
    """测试获取特定会话信息API"""
    url = f"{BASE_URL}/api/dialogue/sessions/{session_id}"
    test_api(f"获取会话 {session_id} 的信息", url)

def test_send_message(session_id, message="你好，这是一条测试消息。"):
    """测试发送消息API"""
    url = f"{BASE_URL}/api/dialogue/input"
    data = {
        "sessionId": session_id,
        "userId": "test_user",
        "input": message
    }
    response = test_api(f"向会话 {session_id} 发送消息", url, "POST", data)
    return response

def test_get_turns(session_id):
    """测试获取会话轮次API"""
    url = f"{BASE_URL}/api/dialogue/sessions/{session_id}/turns"
    turns = test_api(f"获取会话 {session_id} 的轮次", url)
    return turns

def test_surreal_db_integration():
    """测试SurrealDB集成功能"""
    print("\n开始测试 SurrealDB 集成...")
    # 1. 创建会话
    session = test_create_session()
    if not session or not session.get('id'):
        print("\n创建会话失败，无法继续测试")
        return
    
    session_id = session.get('id')
    print(f"\n成功创建会话，ID: {session_id}")
    
    # 2. 获取创建的会话
    test_get_session(session_id)
    
    # 3. 发送消息
    response = test_send_message(session_id, "你好，这是一条测试消息。请用中文回复。")
    if not response:
        print("\n发送消息失败，无法继续测试")
        return
    
    # 4. 获取轮次
    turns = test_get_turns(session_id)
    if turns and turns.get('total', 0) > 0:
        print(f"\n成功获取到 {turns.get('total')} 个轮次，说明 SurrealDB 集成正常")
    else:
        print("\n获取轮次失败或轮次为空，可能 SurrealDB 集成有问题")

def test_dialogue_sessions_with_user_id():
    """测试获取指定用户的会话列表API"""
    user_id = "user_dg88v9qg"
    url = f"{BASE_URL}/api/dialogue/sessions?userId={user_id}"
    test_api(f"获取用户 {user_id} 的会话列表", url)

def test_create_dialogue_session():
    """测试创建新会话 API"""
    url = f"{BASE_URL}/api/dialogue/sessions"
    data = {
        "userId": "user_dg88v9qg",
        "title": "测试会话",
        "dialogueType": "HUMAN_AI_PRIVATE",
        "participants": ["user_dg88v9qg"]
    }
    test_api("创建新会话", url, "POST", data)

def main():
    """主函数，根据命令行参数运行不同的测试"""
    print("开始测试 API 端点...\n")
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name == "tools":
            test_dialogue_tools()
        elif test_name == "sessions":
            test_dialogue_sessions()
        elif test_name == "create":
            session = test_create_session()
            if session and session.get('id'):
                print(f"\n成功创建会话，ID: {session.get('id')}")
        elif test_name == "get_session":
            if len(sys.argv) > 2:
                session_id = sys.argv[2]
                test_get_session(session_id)
            else:
                print("需要提供 session_id 参数")
        elif test_name == "send_message":
            if len(sys.argv) > 2:
                session_id = sys.argv[2]
                message = sys.argv[3] if len(sys.argv) > 3 else "这是一条测试消息"
                test_send_message(session_id, message)
            else:
                print("需要提供 session_id 参数")
        elif test_name == "get_turns":
            if len(sys.argv) > 2:
                session_id = sys.argv[2]
                test_get_turns(session_id)
            else:
                print("需要提供 session_id 参数")
        elif test_name == "surreal":
            test_surreal_db_integration()
        elif test_name == "all":
            # 运行所有基本测试
            test_dialogue_tools()
            test_dialogue_sessions()
            test_dialogue_sessions_with_user_id()
            test_create_dialogue_session()
        else:
            print(f"未知测试: {test_name}")
    else:
        # 打印帮助信息
        print("可用的测试选项:")
        print("  tools - 测试工具列表API")
        print("  sessions - 测试会话列表API")
        print("  create - 测试创建会话API")
        print("  get_session [session_id] - 测试获取特定会话信息API")
        print("  send_message [session_id] [message] - 测试发送消息API")
        print("  get_turns [session_id] - 测试获取会话轮次API")
        print("  surreal - 测试 SurrealDB 集成（创建会话+发送消息+获取轮次）")
        print("  all - 运行所有基本测试")

if __name__ == "__main__":
    main()
