"""
分层记忆系统实现

提供多层次记忆存储和管理，包括工作记忆、短期记忆和长期记忆
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import sqlite3
import heapq

from .memory import Memory
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MemoryLayer:
    """记忆层基类"""
    
    def __init__(self, name: str, capacity: int, ttl: Optional[int] = None):
        """
        初始化记忆层
        
        Args:
            name: 层名称
            capacity: 最大容量
            ttl: 生存时间(秒)，None表示永不过期
        """
        self.name = name
        self.capacity = capacity
        self.ttl = ttl
        self.memories = []
    
    def add(self, memory_item: Dict[str, Any]) -> None:
        """
        添加记忆项
        
        Args:
            memory_item: 记忆项，必须包含timestamp字段
        """
        # 添加记忆
        self.memories.append(memory_item)
        
        # 清理过期记忆
        self._clean_expired()
        
        # 如果超出容量，移除最旧的记忆
        if len(self.memories) > self.capacity:
            self.memories = self.memories[-self.capacity:]
    
    def get(self, limit: int = -1) -> List[Dict[str, Any]]:
        """
        获取记忆项
        
        Args:
            limit: 返回数量限制，-1表示返回所有
            
        Returns:
            记忆项列表
        """
        self._clean_expired()
        
        if limit < 0:
            return self.memories
        return self.memories[-limit:]
    
    def _clean_expired(self) -> None:
        """清理过期记忆"""
        if self.ttl is None:
            return
            
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.ttl)
        
        # 过滤出未过期的记忆
        self.memories = [
            memory for memory in self.memories
            if datetime.fromisoformat(memory["timestamp"]) > cutoff
        ]
    
    def clear(self) -> None:
        """清空记忆层"""
        self.memories = []


class HierarchicalMemory(Memory):
    """
    分层记忆系统
    
    实现工作记忆、短期记忆和长期记忆的分层管理
    """
    
    def __init__(
        self,
        working_memory_capacity: int = 10,
        working_memory_ttl: int = 3600,  # 1小时
        short_term_capacity: int = 100,
        short_term_ttl: int = 86400,  # 1天
        long_term_capacity: int = 1000,
        db_path: str = "memory.db"
    ):
        """
        初始化分层记忆系统
        
        Args:
            working_memory_capacity: 工作记忆容量
            working_memory_ttl: 工作记忆生存时间(秒)
            short_term_capacity: 短期记忆容量
            short_term_ttl: 短期记忆生存时间(秒)
            long_term_capacity: 长期记忆容量
            db_path: 长期记忆数据库路径
        """
        # 初始化各记忆层
        self.working_memory = MemoryLayer(
            name="working_memory",
            capacity=working_memory_capacity,
            ttl=working_memory_ttl
        )
        
        self.short_term_memory = MemoryLayer(
            name="short_term_memory",
            capacity=short_term_capacity,
            ttl=short_term_ttl
        )
        
        # 长期记忆使用SQLite存储
        self.long_term_capacity = long_term_capacity
        self.db_path = db_path
        self._init_long_term_db()
        
        logger.info("分层记忆系统初始化完成")
    
    def _init_long_term_db(self) -> None:
        """初始化长期记忆数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建长期记忆表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS long_term_memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_input TEXT NOT NULL,
            assistant_response TEXT NOT NULL,
            importance REAL DEFAULT 0.5,
            embedding TEXT,
            metadata TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"长期记忆数据库初始化完成: {self.db_path}")
    
    def save(self, user_input: str, assistant_response: str, importance: float = 0.5, metadata: Dict[str, Any] = None) -> None:
        """
        保存对话记录到记忆系统
        
        Args:
            user_input: 用户输入
            assistant_response: 助手回复
            importance: 重要性评分 (0.0-1.0)
            metadata: 元数据
        """
        timestamp = datetime.now().isoformat()
        memory_item = {
            "timestamp": timestamp,
            "user_input": user_input,
            "assistant_response": assistant_response,
            "importance": importance,
            "metadata": metadata or {}
        }
        
        # 保存到工作记忆
        self.working_memory.add(memory_item)
        
        # 保存到短期记忆
        self.short_term_memory.add(memory_item)
        
        # 如果重要性超过阈值，保存到长期记忆
        if importance >= 0.7:
            self._save_to_long_term(memory_item)
            
        logger.debug(f"记忆已保存，重要性: {importance}")
    
    def _save_to_long_term(self, memory_item: Dict[str, Any]) -> None:
        """
        保存到长期记忆
        
        Args:
            memory_item: 记忆项
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 序列化元数据
        metadata_json = json.dumps(memory_item.get("metadata", {}))
        
        cursor.execute(
            """
            INSERT INTO long_term_memories 
            (timestamp, user_input, assistant_response, importance, metadata) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                memory_item["timestamp"],
                memory_item["user_input"],
                memory_item["assistant_response"],
                memory_item["importance"],
                metadata_json
            )
        )
        
        # 控制长期记忆容量
        cursor.execute("SELECT COUNT(*) FROM long_term_memories")
        count = cursor.fetchone()[0]
        
        if count > self.long_term_capacity:
            # 删除最不重要的记忆
            cursor.execute(
                """
                DELETE FROM long_term_memories 
                WHERE id IN (
                    SELECT id FROM long_term_memories 
                    ORDER BY importance ASC 
                    LIMIT ?
                )
                """,
                (count - self.long_term_capacity,)
            )
        
        conn.commit()
        conn.close()
    
    def retrieve(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        从记忆系统中检索相关记忆
        
        Args:
            query: 查询文本
            limit: 返回结果数量限制
            
        Returns:
            相关记忆列表
        """
        # 从各层检索记忆
        working_memories = self.working_memory.get()
        short_term_memories = self.short_term_memory.get()
        long_term_memories = self._retrieve_from_long_term(limit)
        
        # 合并记忆（简单实现，后续可以基于相关性排序）
        all_memories = []
        all_memories.extend(working_memories)
        
        # 添加不在工作记忆中的短期记忆
        working_timestamps = {m["timestamp"] for m in working_memories}
        for memory in short_term_memories:
            if memory["timestamp"] not in working_timestamps:
                all_memories.append(memory)
        
        # 添加不在工作记忆和短期记忆中的长期记忆
        all_timestamps = {m["timestamp"] for m in all_memories}
        for memory in long_term_memories:
            if memory["timestamp"] not in all_timestamps:
                all_memories.append(memory)
        
        # 按时间排序
        all_memories.sort(key=lambda x: x["timestamp"])
        
        # 返回最近的limit条
        return all_memories[-limit:] if limit > 0 else all_memories
    
    def _retrieve_from_long_term(self, limit: int) -> List[Dict[str, Any]]:
        """
        从长期记忆中检索
        
        Args:
            limit: 返回数量限制
            
        Returns:
            记忆项列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT timestamp, user_input, assistant_response, importance, metadata
            FROM long_term_memories
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        memories = []
        for row in rows:
            timestamp, user_input, assistant_response, importance, metadata_json = row
            
            try:
                metadata = json.loads(metadata_json) if metadata_json else {}
            except json.JSONDecodeError:
                metadata = {}
            
            memories.append({
                "timestamp": timestamp,
                "user_input": user_input,
                "assistant_response": assistant_response,
                "importance": importance,
                "metadata": metadata
            })
        
        return memories
    
    def retrieve_by_layer(self, query: str, layer: str = "all", limit: int = 5) -> List[Dict[str, Any]]:
        """
        从指定记忆层检索记忆
        
        Args:
            query: 查询文本
            layer: 记忆层名称 ("working", "short_term", "long_term", "all")
            limit: 返回结果数量限制
            
        Returns:
            相关记忆列表
        """
        if layer == "working":
            return self.working_memory.get(limit)
        elif layer == "short_term":
            return self.short_term_memory.get(limit)
        elif layer == "long_term":
            return self._retrieve_from_long_term(limit)
        else:  # "all"
            return self.retrieve(query, limit)
    
    def clear_layer(self, layer: str) -> None:
        """
        清空指定记忆层
        
        Args:
            layer: 记忆层名称 ("working", "short_term", "long_term", "all")
        """
        if layer in ["working", "all"]:
            self.working_memory.clear()
            
        if layer in ["short_term", "all"]:
            self.short_term_memory.clear()
            
        if layer in ["long_term", "all"]:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM long_term_memories")
            conn.commit()
            conn.close()
