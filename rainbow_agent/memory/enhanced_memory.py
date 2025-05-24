"""
增强记忆系统实现

整合分层记忆、相关性检索和记忆压缩功能
"""
from typing import List, Dict, Any, Optional, Tuple
import json
from datetime import datetime
import sqlite3

from .memory import Memory
from .hierarchical_memory import HierarchicalMemory
from .relevance_retrieval import RelevanceRetrieval
from .memory_compression import MemoryCompression
from ..utils.logger import get_logger

logger = get_logger(__name__)


class EnhancedMemory(Memory):
    """
    增强记忆系统
    
    整合分层记忆、相关性检索和记忆压缩功能，提供完整的记忆管理解决方案
    """
    
    def __init__(
        self,
        db_path: str = "memory.db",
        working_memory_capacity: int = 10,
        working_memory_ttl: int = 3600,  # 1小时
        short_term_capacity: int = 100,
        short_term_ttl: int = 86400,  # 1天
        long_term_capacity: int = 1000,
        embedding_model: str = "text-embedding-ada-002",
        summary_model: str = "gpt-3.5-turbo",
        compression_ratio: float = 0.3,
        relevance_threshold: float = 0.7,
        importance_threshold: float = 0.6,
        auto_compress_days: int = 7,
        auto_compress_threshold: int = 50,
        llm_client = None
    ):
        """
        初始化增强记忆系统
        
        Args:
            db_path: 数据库路径
            working_memory_capacity: 工作记忆容量
            working_memory_ttl: 工作记忆生存时间(秒)
            short_term_capacity: 短期记忆容量
            short_term_ttl: 短期记忆生存时间(秒)
            long_term_capacity: 长期记忆容量
            embedding_model: 嵌入模型名称
            summary_model: 摘要生成模型
            compression_ratio: 压缩比例
            relevance_threshold: 相关性阈值
            importance_threshold: 重要性阈值
            auto_compress_days: 自动压缩天数
            auto_compress_threshold: 自动压缩阈值
            llm_client: LLM客户端
        """
        # 初始化组件
        self.hierarchical_memory = HierarchicalMemory(
            working_memory_capacity=working_memory_capacity,
            working_memory_ttl=working_memory_ttl,
            short_term_capacity=short_term_capacity,
            short_term_ttl=short_term_ttl,
            long_term_capacity=long_term_capacity,
            db_path=db_path
        )
        
        self.relevance_retrieval = RelevanceRetrieval(
            db_path=db_path,
            embedding_model=embedding_model,
            llm_client=llm_client,
            relevance_threshold=relevance_threshold
        )
        
        self.memory_compression = MemoryCompression(
            db_path=db_path,
            llm_client=llm_client,
            summary_model=summary_model,
            compression_ratio=compression_ratio,
            importance_threshold=importance_threshold
        )
        
        # 配置参数
        self.db_path = db_path
        self.auto_compress_days = auto_compress_days
        self.auto_compress_threshold = auto_compress_threshold
        
        # 记忆计数器，用于触发自动压缩
        self.memory_counter = 0
        
        logger.info("增强记忆系统初始化完成")
    
    def save(self, user_input: str, assistant_response: str, importance: float = 0.5, metadata: Dict[str, Any] = None) -> None:
        """
        保存对话记录到记忆系统
        
        Args:
            user_input: 用户输入
            assistant_response: 助手回复
            importance: 重要性评分 (0.0-1.0)
            metadata: 元数据
        """
        # 保存到分层记忆系统
        self.hierarchical_memory.save(
            user_input=user_input,
            assistant_response=assistant_response,
            importance=importance,
            metadata=metadata
        )
        
        # 获取最新保存的记忆ID
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM long_term_memories")
        memory_id = cursor.fetchone()[0]
        conn.close()
        
        if memory_id:
            # 为用户输入和助手回复生成嵌入向量
            timestamp = datetime.now().isoformat()
            self.relevance_retrieval.save_embedding(
                memory_id=memory_id,
                content=user_input,
                content_type="user_input",
                timestamp=timestamp
            )
            self.relevance_retrieval.save_embedding(
                memory_id=memory_id,
                content=assistant_response,
                content_type="assistant_response",
                timestamp=timestamp
            )
        
        # 增加计数器并检查是否需要压缩
        self.memory_counter += 1
        if self.memory_counter >= self.auto_compress_threshold:
            self._check_auto_compress()
            self.memory_counter = 0
    
    def retrieve(self, query: str, limit: int = 5, use_relevance: bool = True) -> List[Dict[str, Any]]:
        """
        从记忆系统中检索相关记忆
        
        Args:
            query: 查询文本
            limit: 返回结果数量限制
            use_relevance: 是否使用相关性检索
            
        Returns:
            相关记忆列表
        """
        if use_relevance:
            # 使用混合检索策略
            return self.relevance_retrieval.hybrid_retrieval(
                query=query,
                recency_limit=limit // 2,  # 一半基于时间
                relevance_limit=limit  # 一半基于相关性
            )
        else:
            # 使用分层记忆系统的基础检索
            return self.hierarchical_memory.retrieve(query=query, limit=limit)
    
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
        return self.hierarchical_memory.retrieve_by_layer(query=query, layer=layer, limit=limit)
    
    def retrieve_by_relevance(self, query: str, limit: int = 5, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        基于相关性检索记忆
        
        Args:
            query: 查询文本
            limit: 返回结果数量限制
            content_type: 内容类型过滤 (user_input, assistant_response, None表示不过滤)
            
        Returns:
            相关记忆列表
        """
        return self.relevance_retrieval.retrieve_relevant_memories(
            query=query,
            limit=limit,
            content_type=content_type
        )
    
    def compress_conversation(self, conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        压缩对话记忆
        
        Args:
            conversation: 对话列表，每项包含user_input和assistant_response
            
        Returns:
            压缩结果，包含摘要和关键点
        """
        return self.memory_compression.compress_conversation(conversation)
    
    def get_summaries(self, start_time: Optional[str] = None, end_time: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取对话摘要
        
        Args:
            start_time: 开始时间 (ISO格式)
            end_time: 结束时间 (ISO格式)
            limit: 返回数量限制
            
        Returns:
            摘要列表
        """
        return self.memory_compression.get_summaries(
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
    
    def clear_layer(self, layer: str) -> None:
        """
        清空指定记忆层
        
        Args:
            layer: 记忆层名称 ("working", "short_term", "long_term", "all")
        """
        self.hierarchical_memory.clear_layer(layer)
    
    def manual_compress(self, days: int = 7, min_count: int = 20) -> Dict[str, Any]:
        """
        手动触发记忆压缩
        
        Args:
            days: 压缩多少天前的记忆
            min_count: 最小记忆数量，低于此数量不压缩
            
        Returns:
            压缩结果
        """
        return self.memory_compression.compress_long_term_memories(
            days=days,
            min_count=min_count
        )
    
    def _check_auto_compress(self) -> None:
        """检查并执行自动压缩"""
        # 获取长期记忆数量
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM long_term_memories")
        count = cursor.fetchone()[0]
        conn.close()
        
        # 如果数量超过阈值，执行压缩
        if count > self.auto_compress_threshold:
            compression_result = self.manual_compress(
                days=self.auto_compress_days,
                min_count=self.auto_compress_threshold
            )
            logger.info(f"自动压缩完成: {compression_result}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        获取记忆系统统计信息
        
        Returns:
            统计信息
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取各表记录数
        cursor.execute("SELECT COUNT(*) FROM long_term_memories")
        long_term_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM memory_embeddings")
        embedding_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM memory_summaries")
        summary_count = cursor.fetchone()[0]
        
        # 获取工作记忆和短期记忆数量
        working_memory_count = len(self.hierarchical_memory.working_memory.memories)
        short_term_memory_count = len(self.hierarchical_memory.short_term_memory.memories)
        
        conn.close()
        
        return {
            "working_memory_count": working_memory_count,
            "short_term_memory_count": short_term_memory_count,
            "long_term_memory_count": long_term_count,
            "embedding_count": embedding_count,
            "summary_count": summary_count,
            "total_memory_items": working_memory_count + short_term_memory_count + long_term_count
        }
