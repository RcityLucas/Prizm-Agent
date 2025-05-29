"""
SQLite 存储功能测试脚本

这个脚本用于测试 SQLite 的存储功能，包括：
1. 连接测试
2. 会话创建测试
3. 轮次添加测试
4. 数据查询测试
"""
import os
import sys
import asyncio
import uuid
import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("sqlite_test")

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试配置
TEST_DB_PATH = "test_rainbow.db"
TEST_USER_ID = "test_user"
TEST_USER_MESSAGE = "这是一条测试消息"
TEST_AI_RESPONSE = "这是AI的回复"

def print_separator(title: str):
    """打印分隔线"""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "="))
    print("=" * 50 + "\n")

def get_connection():
    """获取SQLite连接"""
    conn = sqlite3.connect(TEST_DB_PATH, timeout=30.0, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def test_connection():
    """测试SQLite连接"""
    print_separator("测试SQLite连接")
    
    try:
        # 连接到数据库
        print("尝试连接到SQLite...")
        conn = get_connection()
        print("连接成功！")
        
        # 执行简单查询测试连接
        print("执行测试查询...")
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode")
        result = cursor.fetchone()
        print(f"查询结果: {result}")
        
        # 关闭连接
        conn.close()
        print("测试完成，连接已关闭")
        return True
    except Exception as e:
        print(f"连接测试失败: {e}")
        return False

def init_database():
    """初始化数据库表"""
    print_separator("初始化数据库")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 创建会话表
        print("创建会话表...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            dialogue_type TEXT NOT NULL,
            model TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            metadata TEXT
        )
        """)
        
        # 创建轮次表
        print("创建轮次表...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS turns (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            metadata TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
        """)
        
        conn.commit()
        conn.close()
        print("数据库初始化成功")
        return True
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        return False

def test_session_creation():
    """测试会话创建"""
    print_separator("测试会话创建")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 创建测试会话
        session_id = str(uuid.uuid4())
        print(f"创建测试会话 {session_id}...")
        
        now = datetime.now().isoformat()
        session_data = {
            "id": session_id,
            "user_id": TEST_USER_ID,
            "title": "测试会话",
            "dialogue_type": "human_ai",
            "model": "gpt-3.5-turbo",
            "created_at": now,
            "updated_at": now,
            "metadata": json.dumps({"test": True, "description": "这是一个测试会话"})
        }
        
        # 插入会话数据
        cursor.execute("""
        INSERT INTO sessions (id, user_id, title, dialogue_type, model, created_at, updated_at, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_data["id"],
            session_data["user_id"],
            session_data["title"],
            session_data["dialogue_type"],
            session_data["model"],
            session_data["created_at"],
            session_data["updated_at"],
            session_data["metadata"]
        ))
        
        conn.commit()
        print("会话创建成功！")
        
        # 验证会话是否创建成功
        print("验证会话是否创建成功...")
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        session = cursor.fetchone()
        
        if session:
            print(f"获取到的会话: {session}")
            print("会话创建验证成功！")
            conn.close()
            return True, session_id
        else:
            print("会话创建验证失败！")
            conn.close()
            return False, None
    except Exception as e:
        print(f"会话创建测试失败: {e}")
        return False, None

def test_turn_creation(session_id):
    """测试轮次创建"""
    print_separator("测试轮次创建")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 创建用户轮次
        print(f"为会话 {session_id} 创建用户轮次...")
        user_turn_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        cursor.execute("""
        INSERT INTO turns (id, session_id, role, content, created_at, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_turn_id,
            session_id,
            "user",
            TEST_USER_MESSAGE,
            now,
            json.dumps({"test": True})
        ))
        
        # 创建AI轮次
        print(f"为会话 {session_id} 创建AI轮次...")
        ai_turn_id = str(uuid.uuid4())
        
        cursor.execute("""
        INSERT INTO turns (id, session_id, role, content, created_at, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            ai_turn_id,
            session_id,
            "assistant",
            TEST_AI_RESPONSE,
            now,
            json.dumps({"test": True})
        ))
        
        conn.commit()
        print("轮次创建成功！")
        
        # 验证轮次是否创建成功
        print("获取会话的所有轮次...")
        cursor.execute("SELECT * FROM turns WHERE session_id = ?", (session_id,))
        turns = cursor.fetchall()
        
        if turns and len(turns) >= 2:
            print(f"获取到的轮次: {turns}")
            print("轮次创建验证成功！")
            conn.close()
            return True
        else:
            print("轮次创建验证失败！")
            conn.close()
            return False
    except Exception as e:
        print(f"轮次创建测试失败: {e}")
        return False

def test_data_update(session_id):
    """测试数据更新"""
    print_separator("测试数据更新")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 更新会话标题
        print(f"更新会话 {session_id} 的标题...")
        new_title = f"更新的测试会话 {datetime.now().isoformat()}"
        
        cursor.execute("""
        UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?
        """, (new_title, datetime.now().isoformat(), session_id))
        
        conn.commit()
        print("会话更新成功！")
        
        # 验证更新是否成功
        print("验证更新是否成功...")
        cursor.execute("SELECT title FROM sessions WHERE id = ?", (session_id,))
        title = cursor.fetchone()
        
        if title and title[0] == new_title:
            print(f"更新后的标题: {title[0]}")
            print("数据更新验证成功！")
            conn.close()
            return True
        else:
            print("数据更新验证失败！")
            conn.close()
            return False
    except Exception as e:
        print(f"数据更新测试失败: {e}")
        return False

def test_data_cleanup(session_id):
    """清理测试数据"""
    print_separator("清理测试数据")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 删除测试轮次
        print(f"删除会话 {session_id} 的所有轮次...")
        cursor.execute("DELETE FROM turns WHERE session_id = ?", (session_id,))
        print(f"删除了 {cursor.rowcount} 条轮次记录")
        
        # 删除测试会话
        print(f"删除测试会话 {session_id}...")
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        print(f"删除了 {cursor.rowcount} 条会话记录")
        
        conn.commit()
        
        # 验证删除是否成功
        print("验证删除是否成功...")
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        session = cursor.fetchone()
        
        if not session:
            print("测试数据清理成功！")
            conn.close()
            return True
        else:
            print("测试数据清理失败！")
            conn.close()
            return False
    except Exception as e:
        print(f"数据清理测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print_separator("开始SQLite存储功能测试")
    
    # 测试连接
    connection_success = test_connection()
    if not connection_success:
        print("连接测试失败，终止后续测试")
        return False
    
    # 初始化数据库
    init_success = init_database()
    if not init_success:
        print("数据库初始化失败，终止后续测试")
        return False
    
    # 测试会话创建
    session_success, session_id = test_session_creation()
    if not session_success or not session_id:
        print("会话创建测试失败，终止后续测试")
        return False
    
    print(f"使用会话ID: {session_id} 进行后续测试")
    
    # 测试轮次创建
    turn_success = test_turn_creation(session_id)
    if not turn_success:
        print("轮次创建测试失败")
        # 继续执行清理
    
    # 测试数据更新
    update_success = test_data_update(session_id)
    if not update_success:
        print("数据更新测试失败")
        # 继续执行清理
    
    # 清理测试数据
    cleanup_success = test_data_cleanup(session_id)
    
    # 总结测试结果
    print_separator("测试结果总结")
    print(f"连接测试: {'成功' if connection_success else '失败'}")
    print(f"数据库初始化: {'成功' if init_success else '失败'}")
    print(f"会话创建测试: {'成功' if session_success else '失败'}")
    print(f"轮次创建测试: {'成功' if turn_success else '失败'}")
    print(f"数据更新测试: {'成功' if update_success else '失败'}")
    print(f"数据清理测试: {'成功' if cleanup_success else '失败'}")
    
    # 总体结果
    overall_success = connection_success and init_success and session_success and turn_success and update_success and cleanup_success
    print(f"\n总体测试结果: {'成功' if overall_success else '失败'}")
    
    return overall_success

def main():
    """主函数"""
    try:
        # 运行所有测试
        success = run_all_tests()
        
        # 根据测试结果设置退出码
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生未处理的异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
