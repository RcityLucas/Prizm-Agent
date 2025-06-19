"""
向量操作工具模块

提供向量相关的工具函数，如相似度计算等
"""
import logging
import math
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """计算两个向量的余弦相似度
    
    Args:
        vec1: 第一个向量
        vec2: 第二个向量
        
    Returns:
        余弦相似度，范围为[-1, 1]，值越大表示越相似
    """
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        logger.warning(f"向量维度不匹配: {len(vec1) if vec1 else 0} vs {len(vec2) if vec2 else 0}")
        return -1.0
        
    try:
        # 计算点积
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # 计算模长
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        # 避免除零错误
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
            
        # 计算余弦相似度
        similarity = dot_product / (magnitude1 * magnitude2)
        
        # 确保结果在[-1, 1]范围内
        return max(-1.0, min(1.0, similarity))
    except Exception as e:
        logger.error(f"计算余弦相似度时出错: {e}")
        return -1.0

def sort_by_similarity(items: List[Dict[str, Any]], 
                      query_embedding: List[float], 
                      embedding_key: str = "embedding") -> List[Dict[str, Any]]:
    """根据嵌入向量的相似度对项目进行排序
    
    Args:
        items: 包含嵌入向量的项目列表
        query_embedding: 查询嵌入向量
        embedding_key: 项目中嵌入向量的键名
        
    Returns:
        按相似度降序排序的项目列表，每个项目增加一个"similarity"字段
    """
    result = []
    
    for item in items:
        embedding = item.get(embedding_key)
        if embedding:
            # 计算相似度
            similarity = cosine_similarity(query_embedding, embedding)
            
            # 创建包含相似度的新项目
            item_with_similarity = item.copy()
            item_with_similarity["similarity"] = similarity
            
            result.append(item_with_similarity)
        else:
            logger.warning(f"项目缺少嵌入向量: {item.get('id', 'unknown')}")
    
    # 按相似度降序排序
    result.sort(key=lambda x: x.get("similarity", -1.0), reverse=True)
    
    return result
