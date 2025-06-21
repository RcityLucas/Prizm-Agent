"""
Recency-based memory retriever implementation.

This module provides a retriever that prioritizes recent memories.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from langmem.core.models import Memory, MemoryQuery, RetrievedMemory
from langmem.retrievers.base import RetrieverBase, RetrieverError
from langmem.storage.base import StorageBase


logger = logging.getLogger(__name__)


class RecencyRetriever(RetrieverBase):
    """
    基于时间近期性的记忆检索器。
    
    此检索器优先返回最近创建的记忆，适用于需要考虑时间因素的场景，
    如对话上下文、最近事件等。
    """
    
    def __init__(
        self, 
        storage: StorageBase,
        recency_window_days: int = 7,
        decay_factor: float = 0.1
    ):
        """
        初始化近期性检索器。
        
        Args:
            storage: 存储后端实例，用于访问记忆
            recency_window_days: 近期记忆的时间窗口（天），默认为7天
            decay_factor: 时间衰减因子，控制相关度随时间的衰减速率
        """
        super().__init__(storage)
        self.recency_window_days = recency_window_days
        self.decay_factor = decay_factor
        logger.info(
            "RecencyRetriever initialized with window of %d days and decay factor %.2f",
            recency_window_days, decay_factor
        )
    
    async def retrieve(self, query: MemoryQuery, limit: int = 5) -> List[RetrievedMemory]:
        """
        根据查询检索相关记忆，优先考虑近期创建的记忆。
        
        Args:
            query: 查询对象，包含查询内容和过滤条件
            limit: 返回结果的最大数量
            
        Returns:
            检索到的记忆列表，按近期性排序
            
        Raises:
            RetrieverError: 如果检索过程中发生错误
        """
        try:
            # 合并查询过滤条件
            filters = dict(query.filters) if query.filters else {}
            
            # 如果需要，可以添加时间范围过滤
            # 例如，只检索最近N天的记忆
            if self.recency_window_days > 0:
                cutoff_date = datetime.now() - timedelta(days=self.recency_window_days)
                # 注意：这里假设存储后端支持日期比较
                # 实际实现可能需要根据具体存储后端调整
                filters["created_at"] = {"$gte": cutoff_date}
            
            # 查询记忆
            try:
                # 尝试使用存储后端的查询功能
                memories = await self.storage.query(filters, limit=limit * 2)  # 获取更多记忆以便进行筛选
            except Exception as e:
                logger.error("Failed to query memories: %s", str(e))
                raise RetrieverError(f"Failed to query memories: {str(e)}")
            
            # 计算每个记忆的相关度分数
            retrieved_memories = []
            for memory in memories:
                relevance = self.score_memory(memory, query)
                retrieved_memories.append(RetrievedMemory(memory=memory, relevance=relevance))
            
            # 按相关度排序并限制结果数量
            retrieved_memories.sort(key=lambda x: x.relevance, reverse=True)
            retrieved_memories = retrieved_memories[:limit]
            
            logger.debug("Retrieved %d memories based on recency", len(retrieved_memories))
            return retrieved_memories
        except Exception as e:
            logger.error("Failed to retrieve memories: %s", str(e))
            raise RetrieverError(f"Failed to retrieve memories: {str(e)}")
    
    def score_memory(self, memory: Memory, query: MemoryQuery) -> float:
        """
        计算记忆的近期性分数。
        
        分数基于记忆的创建时间，越近的记忆分数越高。
        
        Args:
            memory: 要评分的记忆
            query: 查询对象（在此实现中不使用查询内容）
            
        Returns:
            近期性分数，范围为0到1
        """
        try:
            # 计算记忆创建时间与当前时间的差距（天）
            now = datetime.now()
            age_days = (now - memory.created_at).total_seconds() / (24 * 3600)
            
            # 使用指数衰减函数计算近期性分数
            # score = exp(-decay_factor * age_days)
            # 这会使得分数随着时间的推移而指数衰减
            score = 1.0 * (2.71828 ** (-self.decay_factor * age_days))
            
            # 确保分数在0到1之间
            score = max(0.0, min(1.0, score))
            
            return float(score)
        except Exception as e:
            logger.error("Failed to calculate memory score: %s", str(e))
            return 0.0
    
    def set_recency_window(self, days: int) -> None:
        """
        设置近期记忆的时间窗口。
        
        Args:
            days: 时间窗口（天）
        """
        self.recency_window_days = days
        logger.debug("Set recency window to %d days", days)
    
    def set_decay_factor(self, factor: float) -> None:
        """
        设置时间衰减因子。
        
        Args:
            factor: 衰减因子，值越大，分数随时间衰减越快
        """
        self.decay_factor = factor
        logger.debug("Set decay factor to %.2f", factor)
