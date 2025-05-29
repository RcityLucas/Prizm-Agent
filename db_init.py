#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库初始化脚本

创建必要的数据库表结构
"""
import os
import sqlite3
import json
from datetime import datetime

def init_db(db_path='database.db'):
    """初始化数据库"""
    print(f"初始化数据库: {db_path}")
    
    # 确保数据库目录存在
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    # 使用绝对路径
    abs_db_path = os.path.abspath(db_path)
    print(f"数据库绝对路径: {abs_db_path}")
    
    # 确保目录存在
    db_dir = os.path.dirname(abs_db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"创建目录: {db_dir}")
    
    # 连接数据库
    try:
        conn = sqlite3.connect(abs_db_path)
        cursor = conn.cursor()
        
        # 创建会话表
        cursor.execute('''
        USE NS rainbow DB agent;
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            user_id TEXT NOT NULL,
            dialogue_type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_activity_at TEXT NOT NULL,
            metadata TEXT
        )
        ''')
        
        # 创建轮次表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS turns (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            metadata TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
        ''')
        
        # 创建示例数据
        create_sample_data(conn, cursor)
        
        # 提交更改
        conn.commit()
        conn.close()
        
        print("数据库初始化完成")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        import traceback
        print(traceback.format_exc())

def create_sample_data(conn, cursor):
    """创建示例数据"""
    # 检查是否已有数据
    cursor.execute("SELECT COUNT(*) FROM sessions")
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"数据库已有 {count} 条会话记录，跳过示例数据创建")
        return
    
    print("创建示例数据...")
    
    # 创建示例会话
    session_id = "sess_sample1"
    now = datetime.now().isoformat()
    
    # 默认参与者
    participants = [
        {
            "id": "user_sample",
            "name": "示例用户",
            "type": "human"
        },
        {
            "id": "ai_assistant",
            "name": "Rainbow助手",
            "type": "ai"
        }
    ]
    
    # 会话数据
    session_data = {
        "id": session_id,
        "title": "示例对话",
        "user_id": "user_sample",
        "dialogue_type": "human_to_ai_private",
        "created_at": now,
        "updated_at": now,
        "last_activity_at": now,
        "metadata": json.dumps({
            "participants": participants
        })
    }
    
    # 插入会话
    fields = ", ".join(session_data.keys())
    placeholders = ", ".join(["?" for _ in session_data.keys()])
    values = list(session_data.values())
    
    cursor.execute(f"INSERT INTO sessions ({fields}) VALUES ({placeholders})", values)
    
    # 创建示例轮次
    turns_data = [
        {
            "id": "turn_sample1",
            "session_id": session_id,
            "role": "user",
            "content": "你好，这是一条示例消息",
            "created_at": now,
            "metadata": json.dumps({
                "user_id": "user_sample"
            })
        },
        {
            "id": "turn_sample2",
            "session_id": session_id,
            "role": "assistant",
            "content": "你好！我是 Rainbow 助手，很高兴为你服务。有什么我可以帮助你的吗？",
            "created_at": now,
            "metadata": json.dumps({
                "model": "gpt-3.5-turbo"
            })
        }
    ]
    
    # 插入轮次
    for turn_data in turns_data:
        fields = ", ".join(turn_data.keys())
        placeholders = ", ".join(["?" for _ in turn_data.keys()])
        values = list(turn_data.values())
        
        cursor.execute(f"INSERT INTO turns ({fields}) VALUES ({placeholders})", values)
    
    print("示例数据创建完成")

if __name__ == "__main__":
    # 获取当前工作目录
    cwd = os.getcwd()
    print(f"当前工作目录: {cwd}")
    
    # 初始化主数据库
    init_db('database.db')
    
    # 初始化数据目录下的数据库
    data_dir = os.path.join(cwd, 'data')
    os.makedirs(data_dir, exist_ok=True)
    init_db(os.path.join(data_dir, 'sessions.sqlite'))
