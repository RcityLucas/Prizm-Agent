#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试对话输入API
"""
import requests
import json

def test_dialogue_input():
    """测试对话输入API"""
    base_url = "http://localhost:5003"
    input_url = f"{base_url}/api/dialogue/input"
    
    # 使用一个已知存在的会话ID
    session_id = "0a2ad3c4-882c-4a94-bdcb-22f229755002"
    
    try:
        input_data = {
            "sessionId": session_id,
            "content": "你好，请问今天北京的天气怎么样？"
        }
        
        print(f"发送请求到 {input_url}")
        print(f"请求数据: {json.dumps(input_data, ensure_ascii=False)}")
        
        input_response = requests.post(input_url, json=input_data)
        print(f"状态码: {input_response.status_code}")
        
        if input_response.status_code == 200:
            input_result = input_response.json()
            print(f"对话响应: {json.dumps(input_result, ensure_ascii=False, indent=2)}")
        else:
            print(f"错误响应: {input_response.text}")
    except Exception as e:
        print(f"测试对话输入API出错: {e}")

if __name__ == "__main__":
    test_dialogue_input()
