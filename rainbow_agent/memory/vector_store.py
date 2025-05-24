"""
向量记忆存储

使用向量表示和相似度搜索实现高级的记忆检索
"""
from typing import List, Dict, Any, Optional, Tuple, Union
import json
import time
import os
import pickle
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    VECTOR_SUPPORT = True
except ImportError:
    VECTOR_SUPPORT = False

from .base import Memory, MemoryItem
from ..utils.logger import get_logger

logger = get_logger(__name__)


class VectorMemoryItem(MemoryItem):
    """向量记忆项"""
    
    def __init__(
        self, 
        content: Any,
        vector: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        memory_id: Optional[str] = None
    ):
        """
        初始化向量记忆项
        
        Args:
            content: 记忆内容
            vector: 内容的向量表示
            metadata: 记忆元数据
            memory_id: 记忆ID，如果不提供则自动生成
        """
        super().__init__(content, metadata, memory_id)
        self.vector = vector or []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        result = super().to_dict()
        result["vector"] = self.vector[:10] + ["..."]  # 仅保留前10个元素用于显示
        return result


class VectorMemory(Memory):
    """
    向量记忆系统
    
    使用向量嵌入和相似度搜索进行高效的语义记忆检索
    """
    
    def __init__(
        self, 
        model_name: str = "paraphrase-MiniLM-L6-v2", 
        capacity: int = 1000,
        save_path: Optional[str] = None
    ):
        """
        初始化向量记忆系统
        
        Args:
            model_name: 嵌入模型名称
            capacity: 记忆容量
            save_path: 记忆保存路径
        """
        self.capacity = capacity
        self.memories: Dict[str, VectorMemoryItem] = {}
        self.save_path = save_path
        
        # 检查向量支持
        if not VECTOR_SUPPORT:
            logger.warning("缺少向量支持库。请安装所需依赖: pip install numpy sentence-transformers")
            self.model = None
        else:
            try:
                self.model = SentenceTransformer(model_name)
                logger.info(f"向量记忆系统初始化完成，使用模型: {model_name}")
            except Exception as e:
                logger.error(f"加载嵌入模型时出错: {e}")
                self.model = None
        
        # 如果有保存路径且文件存在，则加载记忆
        if save_path and os.path.exists(save_path):
            self.load()
    
    def _encode_text(self, text: str) -> List[float]:
        """编码文本为向量"""
        if not self.model:
            return []
        
        try:
            # 使用模型将文本转换为向量
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"编码文本时出错: {e}")
            return []
    
    def add(self, content: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加一条记忆"""
        # 检查容量
        if len(self.memories) >= self.capacity:
            self._evict_least_important()
        
        # 将内容转换为字符串
        content_str = str(content)
        
        # 创建向量表示
        vector = self._encode_text(content_str)
        
        # 创建记忆项
        memory_item = VectorMemoryItem(
            content=content,
            vector=vector,
            metadata=metadata
        )
        
        # 存储记忆
        self.memories[memory_item.memory_id] = memory_item
        logger.debug(f"添加向量记忆: {memory_item.memory_id[:8]}...")
        
        # 如果指定了保存路径，保存记忆
        if self.save_path:
            self.save()
        
        return memory_item.memory_id
    
    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """获取指定ID的记忆"""
        if memory_id in self.memories:
            memory_item = self.memories[memory_id]
            memory_item.access()
            return memory_item.to_dict()
        return None
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        搜索相关记忆
        
        Args:
            query: 查询字符串
            limit: 返回结果数量限制
            
        Returns:
            相关记忆列表
        """
        # 如果没有向量支持，回退到简单文本匹配
        if not self.model or not VECTOR_SUPPORT:
            return self._fallback_search(query, limit)
        
        try:
            # 将查询编码为向量
            query_vector = self._encode_text(query)
            
            # 计算所有记忆与查询的相似度
            similarities = []
            for memory_id, memory in self.memories.items():
                if memory.vector:
                    # 计算余弦相似度
                    similarity = self._cosine_similarity(query_vector, memory.vector)
                    similarities.append((memory_id, similarity))
            
            # 按相似度排序
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # 获取最相关的记忆
            results = []
            for memory_id, similarity in similarities[:limit]:
                memory = self.memories[memory_id]
                memory.access()
                result = memory.to_dict()
                result["similarity"] = similarity
                results.append(result)
            
            return results
        
        except Exception as e:
            logger.error(f"向量搜索时出错: {e}")
            return self._fallback_search(query, limit)
    
    def _fallback_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """回退到基于文本的简单搜索"""
        query = query.lower()
        results = []
        
        for memory_item in self.memories.values():
            content_str = str(memory_item.content).lower()
            
            # 简单文本匹配
            if query in content_str:
                memory_item.access()
                results.append(memory_item.to_dict())
        
        # 按最近访问时间排序
        results.sort(key=lambda x: x["last_accessed"], reverse=True)
        return results[:limit]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            vec1: 第一个向量
            vec2: 第二个向量
            
        Returns:
            余弦相似度 (-1到1之间的值)
        """
        try:
            if not VECTOR_SUPPORT:
                return 0.0
                
            # 使用numpy计算余弦相似度
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm_vec1 = np.linalg.norm(vec1)
            norm_vec2 = np.linalg.norm(vec2)
            
            # 避免除以零
            if norm_vec1 == 0 or norm_vec2 == 0:
                return 0.0
                
            similarity = dot_product / (norm_vec1 * norm_vec2)
            return float(similarity)
        except Exception as e:
            logger.error(f"计算余弦相似度时出错: {e}")
            return 0.0
    
    def clear(self) -> None:
        """清除所有记忆"""
        self.memories.clear()
        logger.debug("清除所有向量记忆")
        
        if self.save_path:
            self.save()
    
    def save(self) -> bool:
        """
        保存记忆到文件
        
        Returns:
            是否成功保存
        """
        if not self.save_path:
            return False
        
        try:
            # 创建目录（如果不存在）
            os.makedirs(os.path.dirname(os.path.abspath(self.save_path)), exist_ok=True)
            
            # 将记忆保存为pickle格式
            with open(self.save_path, 'wb') as f:
                pickle.dump(self.memories, f)
                
            logger.info(f"记忆已保存到 {self.save_path}")
            return True
        except Exception as e:
            logger.error(f"保存记忆时出错: {e}")
            return False
    
    def load(self) -> bool:
        """
        从文件加载记忆
        
        Returns:
            是否成功加载
        """
        if not self.save_path or not os.path.exists(self.save_path):
            return False
        
        try:
            # 从pickle文件加载记忆
            with open(self.save_path, 'rb') as f:
                self.memories = pickle.load(f)
                
            logger.info(f"从 {self.save_path} 加载了 {len(self.memories)} 条记忆")
            return True
        except Exception as e:
            logger.error(f"加载记忆时出错: {e}")
            return False
    
    def _evict_least_important(self) -> None:
        """移除最不重要的记忆"""
        if not self.memories:
            return
        
        # 根据重要性评分
        current_time = time.time()
        memory_scores = {}
        
        for memory_id, memory in self.memories.items():
            recency = 1 / (current_time - memory.created_at + 1)  # 新近度
            access_score = memory.access_count
            
            # 重要性评分（访问次数 * 0.7 + 新近度 * 0.3）
            importance = access_score * 0.7 + recency * 0.3
            memory_scores[memory_id] = importance
        
        # 找出最不重要的记忆并移除
        least_important = min(memory_scores, key=memory_scores.get)
        self.memories.pop(least_important)
        logger.debug(f"移除最不重要的记忆: {least_important[:8]}...")
