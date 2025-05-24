"""
相关性检索系统实现

提供基于语义相似度的记忆检索功能
"""
from typing import List, Dict, Any, Optional, Tuple
import json
import sqlite3
import numpy as np
from datetime import datetime

from .memory import Memory
from ..utils.logger import get_logger
from ..utils.llm import get_llm_client

logger = get_logger(__name__)


class RelevanceRetrieval:
    """
    相关性检索系统
    
    使用向量嵌入和相似度计算实现基于语义的记忆检索
    """
    
    def __init__(
        self,
        db_path: str = "memory.db",
        embedding_model: str = "text-embedding-ada-002",
        embedding_dimension: int = 1536,
        llm_client = None,
        relevance_threshold: float = 0.7,
        time_decay_factor: float = 0.1
    ):
        """
        初始化相关性检索系统
        
        Args:
            db_path: 数据库路径
            embedding_model: 嵌入模型名称
            embedding_dimension: 嵌入向量维度
            llm_client: LLM客户端
            relevance_threshold: 相关性阈值
            time_decay_factor: 时间衰减因子
        """
        self.db_path = db_path
        self.embedding_model = embedding_model
        self.embedding_dimension = embedding_dimension
        self.llm_client = llm_client or get_llm_client()
        self.relevance_threshold = relevance_threshold
        self.time_decay_factor = time_decay_factor
        
        self._init_db()
        
        logger.info("相关性检索系统初始化完成")
    
    def _init_db(self) -> None:
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建记忆表（如果不存在）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memory_id INTEGER NOT NULL,
            embedding BLOB NOT NULL,
            content_type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (memory_id) REFERENCES long_term_memories(id)
        )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_id ON memory_embeddings(memory_id)')
        
        conn.commit()
        conn.close()
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        生成文本的嵌入向量
        
        Args:
            text: 输入文本
            
        Returns:
            嵌入向量
        """
        try:
            response = self.llm_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            embedding = np.array(response.data[0].embedding, dtype=np.float32)
            return embedding
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            # 返回零向量作为后备
            return np.zeros(self.embedding_dimension, dtype=np.float32)
    
    def save_embedding(self, memory_id: int, content: str, content_type: str, timestamp: str) -> None:
        """
        保存内容的嵌入向量
        
        Args:
            memory_id: 记忆ID
            content: 内容文本
            content_type: 内容类型 (user_input, assistant_response)
            timestamp: 时间戳
        """
        embedding = self.generate_embedding(content)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 将numpy数组转换为二进制blob
        embedding_blob = embedding.tobytes()
        
        cursor.execute(
            """
            INSERT INTO memory_embeddings 
            (memory_id, embedding, content_type, timestamp) 
            VALUES (?, ?, ?, ?)
            """,
            (memory_id, embedding_blob, content_type, timestamp)
        )
        
        conn.commit()
        conn.close()
        
        logger.debug(f"已保存记忆ID {memory_id} 的嵌入向量")
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            余弦相似度 (-1 到 1)
        """
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return np.dot(vec1, vec2) / (norm1 * norm2)
    
    def retrieve_relevant_memories(
        self, 
        query: str, 
        limit: int = 5, 
        content_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        检索与查询相关的记忆
        
        Args:
            query: 查询文本
            limit: 返回结果数量限制
            content_type: 内容类型过滤 (user_input, assistant_response, None表示不过滤)
            
        Returns:
            相关记忆列表，按相关性排序
        """
        # 生成查询的嵌入向量
        query_embedding = self.generate_embedding(query)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取所有记忆的嵌入向量
        if content_type:
            cursor.execute(
                """
                SELECT e.id, e.memory_id, e.embedding, e.content_type, e.timestamp,
                       m.user_input, m.assistant_response, m.importance, m.metadata
                FROM memory_embeddings e
                JOIN long_term_memories m ON e.memory_id = m.id
                WHERE e.content_type = ?
                """,
                (content_type,)
            )
        else:
            cursor.execute(
                """
                SELECT e.id, e.memory_id, e.embedding, e.content_type, e.timestamp,
                       m.user_input, m.assistant_response, m.importance, m.metadata
                FROM memory_embeddings e
                JOIN long_term_memories m ON e.memory_id = m.id
                """
            )
        
        rows = cursor.fetchall()
        conn.close()
        
        # 计算相似度并排序
        memory_similarities = []
        now = datetime.now()
        
        for row in rows:
            _, memory_id, embedding_blob, content_type, timestamp, user_input, assistant_response, importance, metadata_json = row
            
            # 将二进制blob转换回numpy数组
            embedding = np.frombuffer(embedding_blob, dtype=np.float32)
            
            # 计算余弦相似度
            similarity = self.cosine_similarity(query_embedding, embedding)
            
            # 应用时间衰减
            time_diff = (now - datetime.fromisoformat(timestamp)).total_seconds() / 86400.0  # 转换为天
            time_factor = np.exp(-self.time_decay_factor * time_diff)
            
            # 计算最终分数 (结合相似度、重要性和时间因素)
            final_score = similarity * 0.6 + float(importance) * 0.2 + time_factor * 0.2
            
            try:
                metadata = json.loads(metadata_json) if metadata_json else {}
            except json.JSONDecodeError:
                metadata = {}
            
            memory_similarities.append({
                "memory_id": memory_id,
                "score": final_score,
                "similarity": similarity,
                "timestamp": timestamp,
                "user_input": user_input,
                "assistant_response": assistant_response,
                "importance": importance,
                "content_type": content_type,
                "metadata": metadata
            })
        
        # 按分数降序排序
        memory_similarities.sort(key=lambda x: x["score"], reverse=True)
        
        # 过滤低于阈值的结果
        relevant_memories = [m for m in memory_similarities if m["similarity"] >= self.relevance_threshold]
        
        # 返回前limit个结果
        return relevant_memories[:limit]
    
    def hybrid_retrieval(
        self, 
        query: str, 
        recency_limit: int = 3, 
        relevance_limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        混合检索策略：结合最近记忆和相关记忆
        
        Args:
            query: 查询文本
            recency_limit: 基于时间的检索数量
            relevance_limit: 基于相关性的检索数量
            
        Returns:
            混合记忆列表
        """
        # 获取最近的记忆
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, timestamp, user_input, assistant_response, importance, metadata
            FROM long_term_memories
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (recency_limit,)
        )
        
        recent_rows = cursor.fetchall()
        conn.close()
        
        recent_memories = []
        for row in recent_rows:
            memory_id, timestamp, user_input, assistant_response, importance, metadata_json = row
            
            try:
                metadata = json.loads(metadata_json) if metadata_json else {}
            except json.JSONDecodeError:
                metadata = {}
                
            recent_memories.append({
                "memory_id": memory_id,
                "timestamp": timestamp,
                "user_input": user_input,
                "assistant_response": assistant_response,
                "importance": importance,
                "metadata": metadata,
                "retrieval_type": "recent"
            })
        
        # 获取相关的记忆
        relevant_memories = self.retrieve_relevant_memories(query, relevance_limit)
        for memory in relevant_memories:
            memory["retrieval_type"] = "relevant"
        
        # 合并并去重
        recent_ids = {m["memory_id"] for m in recent_memories}
        unique_relevant_memories = [m for m in relevant_memories if m["memory_id"] not in recent_ids]
        
        combined_memories = recent_memories + unique_relevant_memories
        
        # 按时间排序
        combined_memories.sort(key=lambda x: x["timestamp"])
        
        return combined_memories
