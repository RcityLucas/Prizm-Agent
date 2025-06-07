"""
系统初始化器

负责初始化Rainbow Agent系统的各个组件
"""
import os
import logging
from typing import Dict, Any, Optional, Tuple

from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage
from rainbow_agent.storage.config import get_surreal_config
from rainbow_agent.ai.openai_service import OpenAIService
from rainbow_agent.core.dialogue_manager import DialogueManager
from rainbow_agent.core.multi_modal_manager import MultiModalToolManager
from rainbow_agent.utils.logger import get_logger

# 配置日志
logger = get_logger(__name__)

class SystemInitializer:
    """系统初始化器"""
    
    @staticmethod
    def init_storage() -> Optional[UnifiedDialogueStorage]:
        """
        初始化统一存储系统
        
        Returns:
            storage: 统一对话存储实例
        """
        try:
            logger.info("开始初始化统一存储系统...")
            
            # 获取 SurrealDB 配置
            surreal_config = get_surreal_config()
            logger.info(f"SurrealDB 配置: {surreal_config}")
            
            # 初始化统一存储
            storage = UnifiedDialogueStorage(
                url=surreal_config["url"],
                namespace=surreal_config["namespace"],
                database=surreal_config["database"],
                username=surreal_config["username"],
                password=surreal_config["password"]
            )
            
            # 测试连接
            health = storage.health_check()
            if health["status"] == "healthy":
                logger.info("统一存储系统初始化成功")
                return storage
            else:
                logger.error(f"存储系统健康检查失败: {health}")
                return None
        except Exception as e:
            logger.error(f"统一存储系统初始化失败: {e}")
            return None
    
    @staticmethod
    def init_dialogue_system(storage: UnifiedDialogueStorage) -> Optional[DialogueManager]:
        """
        初始化对话系统
        
        Args:
            storage: 统一存储实例
            
        Returns:
            dialogue_manager: 对话管理器实例
        """
        try:
            logger.info("开始初始化对话系统...")
            
            # 初始化OpenAI服务
            openai_service = OpenAIService()
            
            # 初始化对话管理器
            dialogue_manager = DialogueManager(
                storage=storage,
                ai_service=openai_service
            )
            
            logger.info("对话系统初始化成功")
            return dialogue_manager
        except Exception as e:
            logger.error(f"对话系统初始化失败: {e}")
            return None
    
    @staticmethod
    def init_multi_modal_system() -> Optional[MultiModalToolManager]:
        """
        初始化多模态系统
        
        Returns:
            multi_modal_manager: 多模态工具管理器实例
        """
        try:
            logger.info("开始初始化多模态系统...")
            
            # 初始化多模态工具管理器
            multi_modal_manager = MultiModalToolManager()
            
            logger.info("多模态系统初始化成功")
            return multi_modal_manager
        except Exception as e:
            logger.error(f"多模态系统初始化失败: {e}")
            return None
    
    @staticmethod
    def init_system() -> Dict[str, Any]:
        """
        初始化整个系统
        
        Returns:
            系统组件字典，包含session_manager, turn_manager, dialogue_manager, multi_modal_manager
        """
        logger.info("开始初始化Rainbow Agent系统...")
        
        # 初始化存储系统
        session_manager, turn_manager = SystemInitializer.init_storage()
        if not session_manager or not turn_manager:
            logger.error("存储系统初始化失败，无法继续初始化系统")
            return {}
        
        # 初始化对话系统
        dialogue_manager = SystemInitializer.init_dialogue_system(session_manager, turn_manager)
        if not dialogue_manager:
            logger.error("对话系统初始化失败")
            return {
                "session_manager": session_manager,
                "turn_manager": turn_manager
            }
        
        # 初始化多模态系统
        multi_modal_manager = SystemInitializer.init_multi_modal_system()
        
        logger.info("Rainbow Agent系统初始化成功")
        return {
            "session_manager": session_manager,
            "turn_manager": turn_manager,
            "dialogue_manager": dialogue_manager,
            "multi_modal_manager": multi_modal_manager
        }

# SQLite会话管理器
class SQLiteSessionManager:
    """SQLite会话管理器"""
    
    def __init__(self):
        """初始化SQLite会话管理器"""
        logger.info("SQLite会话管理器初始化")
        
        # 确保数据库目录存在
        db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "db")
        os.makedirs(db_dir, exist_ok=True)
        
        # 数据库文件路径
        self.db_path = os.path.join(db_dir, "rainbow.db")
        
        # 初始化数据库
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        import sqlite3
        
        # 连接数据库
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            isolation_level=None,  # 自动提交模式
            check_same_thread=False  # 允许在其他线程中使用
        )
        
        # 启用WAL模式，提高并发性能
        conn.execute("PRAGMA journal_mode=WAL")
        
        # 创建会话表
        conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            metadata TEXT
        )
        """)
        
        # 关闭连接
        conn.close()
    
    def get_connection(self):
        """获取数据库连接"""
        import sqlite3
        
        # 连接数据库
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            isolation_level=None,  # 自动提交模式
            check_same_thread=False  # 允许在其他线程中使用
        )
        
        # 启用WAL模式，提高并发性能
        conn.execute("PRAGMA journal_mode=WAL")
        
        # 设置行工厂，返回字典
        conn.row_factory = sqlite3.Row
        
        return conn
    
    def create_session(self, user_id, title=None, dialogue_type="human_to_ai_private", participants=None):
        """创建新会话"""
        import json
        import uuid
        from datetime import datetime
        
        # 生成会话ID
        session_id = str(uuid.uuid4())
        
        # 生成会话标题
        if not title:
            title = f"新对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # 生成参与者列表
        if not participants:
            participants = [
                {
                    "id": user_id,
                    "name": "用户",
                    "type": "human"
                },
                {
                    "id": "ai_assistant",
                    "name": "Rainbow助手",
                    "type": "ai"
                }
            ]
        
        # 生成元数据
        metadata = {
            "dialogue_type": dialogue_type,
            "participants": participants,
            "status": "active"
        }
        
        # 当前时间
        now = datetime.now().isoformat()
        
        # 获取数据库连接
        conn = self.get_connection()
        try:
            # 插入会话
            cursor = conn.execute(
                """
                INSERT INTO sessions (id, title, user_id, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, title, user_id, now, now, json.dumps(metadata))
            )
            
            # 获取创建的会话
            cursor = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            
            if row:
                # 转换为字典
                session = dict(row)
                
                # 解析元数据
                if session.get("metadata"):
                    session["metadata"] = json.loads(session["metadata"])
                
                return session
            else:
                logger.error(f"创建会话失败: 未找到新创建的会话 {session_id}")
                return None
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            return None
        finally:
            conn.close()
    
    def get_sessions(self, user_id=None, limit=10, offset=0):
        """获取会话列表"""
        import json
        
        # 获取数据库连接
        conn = self.get_connection()
        try:
            # 构建查询
            query = "SELECT * FROM sessions"
            params = []
            
            if user_id:
                query += " WHERE user_id = ?"
                params.append(user_id)
            
            query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            # 执行查询
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            # 转换为字典列表
            sessions = []
            for row in rows:
                session = dict(row)
                
                # 解析元数据
                if session.get("metadata"):
                    session["metadata"] = json.loads(session["metadata"])
                
                sessions.append(session)
            
            return sessions
        except Exception as e:
            logger.error(f"获取会话列表失败: {e}")
            return []
        finally:
            conn.close()
    
    def get_session(self, session_id):
        """获取特定会话"""
        import json
        
        # 获取数据库连接
        conn = self.get_connection()
        try:
            # 执行查询
            cursor = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            
            if row:
                # 转换为字典
                session = dict(row)
                
                # 解析元数据
                if session.get("metadata"):
                    session["metadata"] = json.loads(session["metadata"])
                
                return session
            else:
                logger.warning(f"会话不存在: {session_id}")
                return None
        except Exception as e:
            logger.error(f"获取会话失败: {e}")
            return None
        finally:
            conn.close()
    
    def update_session(self, session_id, updates):
        """更新会话"""
        import json
        from datetime import datetime
        
        # 当前时间
        now = datetime.now().isoformat()
        
        # 更新字段
        fields = []
        params = []
        
        # 添加更新时间
        fields.append("updated_at = ?")
        params.append(now)
        
        # 处理其他更新字段
        for key, value in updates.items():
            if key == "metadata":
                fields.append("metadata = ?")
                params.append(json.dumps(value))
            elif key in ["title", "user_id"]:
                fields.append(f"{key} = ?")
                params.append(value)
        
        # 如果没有要更新的字段，直接返回
        if not fields:
            logger.warning(f"没有要更新的字段: {session_id}")
            return None
        
        # 构建更新语句
        query = f"UPDATE sessions SET {', '.join(fields)} WHERE id = ?"
        params.append(session_id)
        
        # 获取数据库连接
        conn = self.get_connection()
        try:
            # 执行更新
            conn.execute(query, params)
            
            # 获取更新后的会话
            return self.get_session(session_id)
        except Exception as e:
            logger.error(f"更新会话失败: {e}")
            return None
        finally:
            conn.close()
    
    def update_session_activity(self, session_id):
        """更新会话活动时间"""
        return self.update_session(session_id, {})

# SQLite轮次管理器
class SQLiteTurnManager:
    """SQLite轮次管理器"""
    
    def __init__(self):
        """初始化SQLite轮次管理器"""
        logger.info("SQLite轮次管理器初始化")
        
        # 确保数据库目录存在
        db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "db")
        os.makedirs(db_dir, exist_ok=True)
        
        # 数据库文件路径
        self.db_path = os.path.join(db_dir, "rainbow.db")
        
        # 初始化数据库
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        import sqlite3
        
        # 连接数据库
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            isolation_level=None,  # 自动提交模式
            check_same_thread=False  # 允许在其他线程中使用
        )
        
        # 启用WAL模式，提高并发性能
        conn.execute("PRAGMA journal_mode=WAL")
        
        # 创建轮次表
        conn.execute("""
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
        
        # 创建索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_turns_session_id ON turns (session_id)")
        
        # 关闭连接
        conn.close()
    
    def get_connection(self):
        """获取数据库连接"""
        import sqlite3
        
        # 连接数据库
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            isolation_level=None,  # 自动提交模式
            check_same_thread=False  # 允许在其他线程中使用
        )
        
        # 启用WAL模式，提高并发性能
        conn.execute("PRAGMA journal_mode=WAL")
        
        # 设置行工厂，返回字典
        conn.row_factory = sqlite3.Row
        
        return conn
    
    def create_turn(self, session_id, role, content, metadata=None):
        """创建新轮次"""
        import json
        import uuid
        from datetime import datetime
        
        # 生成轮次ID
        turn_id = str(uuid.uuid4())
        
        # 当前时间
        now = datetime.now().isoformat()
        
        # 元数据
        metadata_json = json.dumps(metadata) if metadata else None
        
        # 获取数据库连接
        conn = self.get_connection()
        try:
            # 插入轮次
            conn.execute(
                """
                INSERT INTO turns (id, session_id, role, content, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (turn_id, session_id, role, content, now, metadata_json)
            )
            
            # 获取创建的轮次
            cursor = conn.execute("SELECT * FROM turns WHERE id = ?", (turn_id,))
            row = cursor.fetchone()
            
            if row:
                # 转换为字典
                turn = dict(row)
                
                # 解析元数据
                if turn.get("metadata"):
                    turn["metadata"] = json.loads(turn["metadata"])
                
                return turn
            else:
                logger.error(f"创建轮次失败: 未找到新创建的轮次 {turn_id}")
                return None
        except Exception as e:
            logger.error(f"创建轮次失败: {e}")
            return None
        finally:
            conn.close()
    
    def get_turns(self, session_id):
        """获取会话的轮次"""
        import json
        
        # 获取数据库连接
        conn = self.get_connection()
        try:
            # 执行查询
            cursor = conn.execute(
                "SELECT * FROM turns WHERE session_id = ? ORDER BY created_at",
                (session_id,)
            )
            rows = cursor.fetchall()
            
            # 转换为字典列表
            turns = []
            for row in rows:
                turn = dict(row)
                
                # 解析元数据
                if turn.get("metadata"):
                    turn["metadata"] = json.loads(turn["metadata"])
                
                turns.append(turn)
            
            return turns
        except Exception as e:
            logger.error(f"获取轮次失败: {e}")
            return []
        finally:
            conn.close()
