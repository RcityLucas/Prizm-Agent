"""
Unified Turn Vector Manager

扩展UnifiedTurnManager，添加向量搜索和相关功能
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .unified_turn_manager import UnifiedTurnManager
from ..utils.vector_utils import cosine_similarity, sort_by_similarity

logger = logging.getLogger(__name__)

class UnifiedTurnVectorManager(UnifiedTurnManager):
    """
    统一对话轮次向量管理器
    
    扩展UnifiedTurnManager，添加向量搜索和相关功能
    """
    
    async def init_vector_storage_schema(self) -> bool:
        """
        初始化向量存储模式
        
        确保turns表有正确的嵌入向量字段和索引
        
        Returns:
            初始化是否成功
        """
        try:
            if not self.client:
                await self.connect()
                
            # 确保turns表存在并有正确的嵌入向量字段
            # 注意：SurrealDB会根据插入的数据自动创建字段，所以这里主要是创建索引
            
            # 创建索引以加快查询速度
            index_queries = [
                "DEFINE INDEX turn_embedding ON TABLE turns COLUMNS embedding;",
                "DEFINE INDEX turn_session_id ON TABLE turns COLUMNS session_id;",
                "DEFINE INDEX turn_created_at ON TABLE turns COLUMNS created_at;"
            ]
            
            for query in index_queries:
                try:
                    await self.client.query(query)
                    logger.info(f"成功执行索引创建查询: {query}")
                except Exception as e:
                    # 如果索引已存在，会抛出异常，但这不是错误
                    logger.warning(f"创建索引时出现异常（可能已存在）: {e}")
            
            return True
        except Exception as e:
            logger.error(f"初始化向量存储模式失败: {e}")
            return False
    
    async def get_turns_with_embeddings(self, 
                                       session_id: Optional[str] = None, 
                                       limit: int = 100, 
                                       offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取带有嵌入向量的对话轮次
        
        Args:
            session_id: 会话ID，如果为None则获取所有会话的轮次
            limit: 最大返回数量
            offset: 起始偏移
            
        Returns:
            带有嵌入向量的对话轮次列表
        """
        try:
            if not self.client:
                await self.connect()
                
            # 构建查询条件
            if session_id:
                # 查询特定会话的轮次，并且只返回有嵌入向量的轮次
                query = f"SELECT * FROM turns WHERE session_id = $session_id AND embedding != NULL ORDER BY created_at DESC LIMIT $limit OFFSET $offset"
                vars = {"session_id": session_id, "limit": limit, "offset": offset}
            else:
                # 查询所有会话的轮次，并且只返回有嵌入向量的轮次
                query = f"SELECT * FROM turns WHERE embedding != NULL ORDER BY created_at DESC LIMIT $limit OFFSET $offset"
                vars = {"limit": limit, "offset": offset}
                
            # 执行查询
            result = await self.client.query(query, vars)
            
            # 处理结果
            if result and isinstance(result, list) and len(result) > 0:
                # 提取结果中的记录
                if isinstance(result[0], dict) and "result" in result[0]:
                    turns = result[0]["result"]
                    return turns if turns else []
                else:
                    return result
            
            return []
        except Exception as e:
            logger.error(f"获取带有嵌入向量的对话轮次失败: {e}")
            return []
    
    async def search_similar_turns(self, 
                                  query_embedding: List[float], 
                                  session_id: Optional[str] = None,
                                  top_k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索与查询向量相似的对话轮次
        
        Args:
            query_embedding: 查询嵌入向量
            session_id: 会话ID，如果为None则搜索所有会话
            top_k: 返回的最相似结果数量
            
        Returns:
            按相似度降序排序的对话轮次列表，每个轮次增加一个"similarity"字段
        """
        try:
            # 获取带有嵌入向量的轮次
            # 这里获取较多的记录以确保有足够的候选项进行相似度排序
            limit = max(100, top_k * 5)
            turns_with_embeddings = await self.get_turns_with_embeddings(session_id, limit=limit)
            
            if not turns_with_embeddings:
                logger.warning("没有找到带有嵌入向量的对话轮次")
                return []
                
            # 计算相似度并排序
            sorted_turns = sort_by_similarity(turns_with_embeddings, query_embedding)
            
            # 返回前top_k个结果
            return sorted_turns[:top_k]
        except Exception as e:
            logger.error(f"搜索相似对话轮次失败: {e}")
            return []
