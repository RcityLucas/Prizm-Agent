"""
SQLite 会话管理测试脚本

这个脚本用于测试使用SQLite的会话管理功能
"""
import os
import sys
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
logger = logging.getLogger("sqlite_session_test")

# 测试配置
TEST_DB_PATH = "test_rainbow.db"
TEST_USER_ID = "test_user"
TEST_SESSION_TITLE = "测试会话"

def print_separator(title: str):
    """打印分隔线"""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "="))
    print("=" * 50 + "\n")

class SQLiteSessionManager:
    """SQLite会话管理器"""
    
    def __init__(self, db_path: str = TEST_DB_PATH):
        """初始化会话管理器
        
        Args:
            db_path: SQLite数据库路径
        """
        self.db_path = db_path
        self._init_db()
        logger.info(f"SQLite会话管理器初始化完成，使用数据库: {db_path}")
    
    def _get_connection(self):
        """获取SQLite连接"""
        conn = sqlite3.connect(self.db_path, timeout=30.0, isolation_level=None)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn
    
    def _init_db(self):
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 创建会话表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            dialogue_type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            metadata TEXT
        )
        """)
        
        # 创建轮次表
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
        logger.info("数据库表初始化完成")
    
    def create_session(self, user_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        """创建新会话
        
        Args:
            user_id: 用户ID
            title: 会话标题，如果不提供则使用默认标题
            
        Returns:
            创建的会话
        """
        logger.info(f"开始创建新会话: user_id={user_id}, title={title}")
        
        # 生成会话ID
        session_id = str(uuid.uuid4()).replace('-', '')
        
        # 创建会话数据
        now = datetime.now().isoformat()
        session_title = title if title else f"新对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # 插入会话数据
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
            INSERT INTO sessions (id, user_id, title, dialogue_type, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                user_id,
                session_title,
                "human_to_ai_private",
                now,
                now,
                json.dumps({})
            ))
            
            conn.commit()
            logger.info(f"会话创建成功: {session_id}")
            
            # 返回会话数据
            session_data = {
                "id": session_id,
                "user_id": user_id,
                "title": session_title,
                "dialogue_type": "human_to_ai_private",
                "created_at": now,
                "updated_at": now
            }
            
            return session_data
        except Exception as e:
            logger.error(f"会话创建失败: {e}")
            raise
        finally:
            conn.close()
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取特定会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据，如果不存在则返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            session = cursor.fetchone()
            
            if session:
                # 将查询结果转换为字典
                columns = [col[0] for col in cursor.description]
                session_dict = dict(zip(columns, session))
                
                # 解析元数据
                if "metadata" in session_dict and session_dict["metadata"]:
                    session_dict["metadata"] = json.loads(session_dict["metadata"])
                
                logger.info(f"获取会话成功: {session_id}")
                return session_dict
            else:
                logger.info(f"会话不存在: {session_id}")
                return None
        except Exception as e:
            logger.error(f"获取会话失败: {e}")
            return None
        finally:
            conn.close()
    
    def add_turn(self, session_id: str, role: str, content: str) -> Dict[str, Any]:
        """添加对话轮次
        
        Args:
            session_id: 会话ID
            role: 角色（user或assistant）
            content: 内容
            
        Returns:
            创建的轮次
        """
        logger.info(f"添加轮次: session_id={session_id}, role={role}")
        
        # 生成轮次ID
        turn_id = str(uuid.uuid4()).replace('-', '')
        
        # 创建轮次数据
        now = datetime.now().isoformat()
        
        # 插入轮次数据
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
            INSERT INTO turns (id, session_id, role, content, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                turn_id,
                session_id,
                role,
                content,
                now,
                json.dumps({})
            ))
            
            conn.commit()
            logger.info(f"轮次添加成功: {turn_id}")
            
            # 返回轮次数据
            turn_data = {
                "id": turn_id,
                "session_id": session_id,
                "role": role,
                "content": content,
                "created_at": now
            }
            
            return turn_data
        except Exception as e:
            logger.error(f"轮次添加失败: {e}")
            raise
        finally:
            conn.close()
    
    def get_turns(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话的所有轮次
        
        Args:
            session_id: 会话ID
            
        Returns:
            轮次列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM turns WHERE session_id = ? ORDER BY created_at", (session_id,))
            turns = cursor.fetchall()
            
            # 将查询结果转换为字典列表
            columns = [col[0] for col in cursor.description]
            turn_dicts = []
            
            for turn in turns:
                turn_dict = dict(zip(columns, turn))
                
                # 解析元数据
                if "metadata" in turn_dict and turn_dict["metadata"]:
                    turn_dict["metadata"] = json.loads(turn_dict["metadata"])
                
                turn_dicts.append(turn_dict)
            
            logger.info(f"获取轮次成功: {session_id}, 共 {len(turn_dicts)} 条")
            return turn_dicts
        except Exception as e:
            logger.error(f"获取轮次失败: {e}")
            return []
        finally:
            conn.close()

def test_session_creation():
    """测试会话创建"""
    print_separator("测试会话创建")
    
    # 创建会话管理器
    session_manager = SQLiteSessionManager()
    
    try:
        # 创建测试会话
        print(f"创建测试会话...")
        session = session_manager.create_session(TEST_USER_ID, TEST_SESSION_TITLE)
        print(f"会话创建结果: {session}")
        
        # 获取会话ID
        session_id = session["id"]
        print(f"会话ID: {session_id}")
        
        # 验证会话是否创建成功
        print("验证会话是否创建成功...")
        retrieved_session = session_manager.get_session(session_id)
        print(f"获取到的会话: {retrieved_session}")
        
        if retrieved_session and retrieved_session["id"] == session_id:
            print("会话创建成功！")
            return True, session_id
        else:
            print("会话创建失败！")
            return False, None
    except Exception as e:
        print(f"会话创建测试失败: {e}")
        return False, None

def test_turn_creation(session_id):
    """测试轮次创建"""
    print_separator("测试轮次创建")
    
    # 创建会话管理器
    session_manager = SQLiteSessionManager()
    
    try:
        # 添加用户轮次
        print(f"添加用户轮次...")
        user_turn = session_manager.add_turn(session_id, "user", "这是一条测试消息")
        print(f"用户轮次添加结果: {user_turn}")
        
        # 添加AI轮次
        print(f"添加AI轮次...")
        ai_turn = session_manager.add_turn(session_id, "assistant", "这是AI的回复")
        print(f"AI轮次添加结果: {ai_turn}")
        
        # 获取所有轮次
        print("获取所有轮次...")
        turns = session_manager.get_turns(session_id)
        print(f"轮次列表: {turns}")
        
        if len(turns) >= 2:
            print("轮次创建成功！")
            return True
        else:
            print("轮次创建失败！")
            return False
    except Exception as e:
        print(f"轮次创建测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print_separator("开始SQLite会话管理测试")
    
    # 测试会话创建
    session_success, session_id = test_session_creation()
    if not session_success or not session_id:
        print("会话创建测试失败，终止后续测试")
        return False
    
    # 测试轮次创建
    turn_success = test_turn_creation(session_id)
    if not turn_success:
        print("轮次创建测试失败")
        return False
    
    # 总结测试结果
    print_separator("测试结果总结")
    print(f"会话创建测试: {'成功' if session_success else '失败'}")
    print(f"轮次创建测试: {'成功' if turn_success else '失败'}")
    
    # 总体结果
    overall_success = session_success and turn_success
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
