"""
语义索引管理器

管理对话内容的语义索引，提供高效的语义搜索功能
"""
import os
import uuid
import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

from .surreal_http_client import SurrealDBHttpClient
from .config import get_surreal_config
from .models import TurnModel

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SemanticIndexManager")

class SemanticIndexManager:
    """语义索引管理器
    
    管理对话内容的语义索引，提供高效的语义搜索功能
    """
    
    # 内存缓存
    _embedding_cache = {}
    
    def __init__(self, 
                 url: Optional[str] = None,
                 namespace: Optional[str] = None,
                 database: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 embedding_dimension: int = 384):
        """初始化语义索引管理器
        
        Args:
            url: SurrealDB服务器URL
            namespace: 命名空间
            database: 数据库名
            username: 用户名
            password: 密码
            embedding_dimension: 嵌入向量维度
        """
        # 获取配置
        config = get_surreal_config()
        
        # 使用传入的参数或配置值
        self.url = url or config["url"]
        self.namespace = namespace or config["namespace"]
        self.database = database or config["database"]
        self.username = username or config["username"]
        self.password = password or config["password"]
        self.embedding_dimension = embedding_dimension
        
        # 将WebSocket URL转换为HTTP URL
        if self.url.startswith("ws://"):
            self.http_url = "http://" + self.url[5:].replace("/rpc", "")
        elif self.url.startswith("wss://"):
            self.http_url = "https://" + self.url[6:].replace("/rpc", "")
        else:
            self.http_url = self.url
        
        # 创建HTTP客户端
        self.client = SurrealDBHttpClient(
            url=self.http_url,
            namespace=self.namespace,
            database=self.database,
            username=self.username,
            password=self.password
        )
        
        logger.info(f"语义索引管理器初始化完成: {self.http_url}, {self.namespace}, {self.database}")
        
        # 确保表结构存在
        self._ensure_table_structure()
    
    def _ensure_table_structure(self) -> None:
        """确保表结构存在"""
        try:
            # 定义semantic_index表
            sql = """
            DEFINE TABLE semantic_index SCHEMAFULL;
            DEFINE FIELD id ON semantic_index TYPE string;
            DEFINE FIELD turn_id ON semantic_index TYPE string;
            DEFINE FIELD session_id ON semantic_index TYPE string;
            DEFINE FIELD user_id ON semantic_index TYPE string;
            DEFINE FIELD content ON semantic_index TYPE string;
            DEFINE FIELD embedding ON semantic_index TYPE array;
            DEFINE FIELD created_at ON semantic_index TYPE datetime;
            DEFINE FIELD metadata ON semantic_index TYPE object;
            """
            
            self.client.execute_sql(sql)
            logger.info("语义索引表结构初始化完成")
        except Exception as e:
            logger.warning(f"语义索引表结构初始化失败，可能已存在: {e}")
    
    def create_index_entry(self, 
                          turn_id: str, 
                          session_id: str,
                          user_id: str,
                          content: str,
                          embedding: List[float],
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建语义索引条目
        
        Args:
            turn_id: 轮次ID
            session_id: 会话ID
            user_id: 用户ID
            content: 内容
            embedding: 嵌入向量
            metadata: 元数据
            
        Returns:
            创建的语义索引条目
        """
        try:
            # 生成索引条目ID
            index_id = str(uuid.uuid4()).replace('-', '')
            
            # 准备索引条目数据
            index_data = {
                "id": index_id,
                "turn_id": turn_id,
                "session_id": session_id,
                "user_id": user_id,
                "content": content,
                "embedding": embedding,
                "created_at": "time::now()"
            }
            
            # 添加元数据（如果有）
            if metadata:
                index_data["metadata"] = metadata
            else:
                index_data["metadata"] = {}
            
            # 使用SQL直接创建完整记录
            logger.info(f"使用SQL直接创建语义索引条目: {index_id}")
            
            # 构建SQL语句
            columns = ", ".join(index_data.keys())
            values_list = []
            
            for key, value in index_data.items():
                if isinstance(value, str):
                    if value == "time::now()":
                        values_list.append("time::now()")
                    else:
                        escaped_value = value.replace("'", "''")
                        values_list.append(f"'{escaped_value}'")
                elif isinstance(value, (int, float, bool)):
                    values_list.append(str(value))
                elif value is None:
                    values_list.append("NULL")
                elif isinstance(value, (dict, list)):
                    import json
                    json_value = json.dumps(value)
                    values_list.append(json_value)
                else:
                    values_list.append(f"'{str(value)}'")
            
            values = ", ".join(values_list)
            sql = f"INSERT INTO semantic_index ({columns}) VALUES ({values});"
            
            # 执行SQL
            logger.info(f"创建语义索引条目SQL: {sql}")
            self.client.execute_sql(sql)
            
            # 将嵌入向量添加到内存缓存
            SemanticIndexManager._embedding_cache[index_id] = embedding
            
            # 返回创建的索引条目
            logger.info(f"语义索引条目创建成功: {index_id}")
            return index_data
        except Exception as e:
            logger.error(f"创建语义索引条目失败: {e}")
            raise
    
    def index_turn(self, turn: Union[Dict[str, Any], TurnModel], embedding_model: Any = None) -> Optional[str]:
        """为轮次创建语义索引
        
        Args:
            turn: 轮次数据或模型
            embedding_model: 嵌入模型（可选）
            
        Returns:
            索引条目ID，如果创建失败则返回None
        """
        try:
            # 获取轮次数据
            if isinstance(turn, TurnModel):
                turn_id = turn.id
                session_id = turn.session_id
                content = turn.content
                existing_embedding = turn.embedding
                metadata = turn.metadata
            else:
                turn_id = turn.get("id")
                session_id = turn.get("session_id")
                content = turn.get("content")
                existing_embedding = turn.get("embedding")
                metadata = turn.get("metadata", {})
            
            # 如果没有内容，无法创建索引
            if not content:
                logger.info(f"轮次 {turn_id} 没有内容，无法创建语义索引")
                return None
            
            # 获取用户ID
            # 这里假设可以从会话中获取用户ID，实际实现可能需要调整
            user_id = "unknown"  # 默认值
            
            # 获取或生成嵌入向量
            embedding = None
            
            # 如果轮次已有嵌入向量，直接使用
            if existing_embedding:
                embedding = existing_embedding
                logger.info(f"使用轮次 {turn_id} 已有的嵌入向量")
            
            # 如果提供了嵌入模型，使用模型生成嵌入向量
            elif embedding_model:
                try:
                    # 使用嵌入模型生成嵌入向量
                    embedding = embedding_model.encode(content)
                    logger.info(f"使用嵌入模型为轮次 {turn_id} 生成嵌入向量")
                except Exception as e:
                    logger.error(f"使用嵌入模型生成嵌入向量失败: {e}")
            
            # 如果没有嵌入向量，生成随机向量（仅用于测试）
            if not embedding:
                embedding = list(np.random.rand(self.embedding_dimension).astype(float))
                logger.warning(f"为轮次 {turn_id} 生成随机嵌入向量（仅用于测试）")
            
            # 创建语义索引条目
            index_entry = self.create_index_entry(
                turn_id=turn_id,
                session_id=session_id,
                user_id=user_id,
                content=content,
                embedding=embedding,
                metadata=metadata
            )
            
            logger.info(f"为轮次 {turn_id} 创建语义索引成功: {index_entry['id']}")
            return index_entry["id"]
        except Exception as e:
            logger.error(f"为轮次创建语义索引失败: {e}")
            return None
    
    def search(self, query: str, embedding_model: Any, limit: int = 5, user_id: Optional[str] = None, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """语义搜索
        
        Args:
            query: 查询文本
            embedding_model: 嵌入模型
            limit: 最大结果数
            user_id: 用户ID（可选，用于限制搜索范围）
            session_id: 会话ID（可选，用于限制搜索范围）
            
        Returns:
            搜索结果列表
        """
        try:
            # 生成查询的嵌入向量
            try:
                query_embedding = embedding_model.encode(query)
            except Exception as e:
                logger.error(f"生成查询嵌入向量失败: {e}")
                # 生成随机向量（仅用于测试）
                query_embedding = list(np.random.rand(self.embedding_dimension).astype(float))
                logger.warning("生成随机查询嵌入向量（仅用于测试）")
            
            # 构建查询条件
            condition = ""
            if user_id:
                condition += f"user_id = '{user_id}'"
            if session_id:
                if condition:
                    condition += f" AND session_id = '{session_id}'"
                else:
                    condition += f"session_id = '{session_id}'"
            
            # 获取所有索引条目
            if condition:
                index_entries = self.client.get_records("semantic_index", condition, 100, 0)
            else:
                index_entries = self.client.get_records("semantic_index", "", 100, 0)
            
            if not index_entries:
                logger.info("没有找到语义索引条目")
                return []
            
            # 计算相似度
            results = []
            for entry in index_entries:
                entry_embedding = entry.get("embedding")
                if not entry_embedding:
                    continue
                
                # 计算余弦相似度
                similarity = self._cosine_similarity(query_embedding, entry_embedding)
                
                # 添加到结果列表
                results.append({
                    "id": entry.get("id"),
                    "turn_id": entry.get("turn_id"),
                    "session_id": entry.get("session_id"),
                    "content": entry.get("content"),
                    "similarity": similarity,
                    "metadata": entry.get("metadata", {})
                })
            
            # 按相似度排序
            results.sort(key=lambda x: x["similarity"], reverse=True)
            
            # 限制结果数量
            top_results = results[:limit]
            
            logger.info(f"语义搜索成功，共找到 {len(top_results)} 条结果")
            return top_results
        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            余弦相似度
        """
        # 转换为numpy数组
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        # 计算余弦相似度
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        
        # 避免除以零
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0
        
        similarity = dot_product / (norm_vec1 * norm_vec2)
        return float(similarity)
    
    def bulk_index_turns(self, turns: List[Union[Dict[str, Any], TurnModel]], embedding_model: Any = None) -> List[str]:
        """批量为轮次创建语义索引
        
        Args:
            turns: 轮次列表
            embedding_model: 嵌入模型（可选）
            
        Returns:
            成功创建的索引条目ID列表
        """
        index_ids = []
        for turn in turns:
            index_id = self.index_turn(turn, embedding_model)
            if index_id:
                index_ids.append(index_id)
        
        logger.info(f"批量创建语义索引成功，共 {len(index_ids)} 条")
        return index_ids
    
    def get_similar_turns(self, turn: Union[Dict[str, Any], TurnModel], limit: int = 5) -> List[Dict[str, Any]]:
        """获取与指定轮次相似的轮次
        
        Args:
            turn: 轮次数据或模型
            limit: 最大结果数
            
        Returns:
            相似轮次列表
        """
        try:
            # 获取轮次内容和嵌入向量
            if isinstance(turn, TurnModel):
                content = turn.content
                embedding = turn.embedding
                turn_id = turn.id
                session_id = turn.session_id
            else:
                content = turn.get("content")
                embedding = turn.get("embedding")
                turn_id = turn.get("id")
                session_id = turn.get("session_id")
            
            # 如果没有嵌入向量，无法搜索
            if not embedding:
                logger.info(f"轮次 {turn_id} 没有嵌入向量，无法搜索相似轮次")
                return []
            
            # 获取所有索引条目（除了当前轮次）
            condition = f"turn_id != '{turn_id}'"
            index_entries = self.client.get_records("semantic_index", condition, 100, 0)
            
            if not index_entries:
                logger.info("没有找到其他语义索引条目")
                return []
            
            # 计算相似度
            results = []
            for entry in index_entries:
                entry_embedding = entry.get("embedding")
                if not entry_embedding:
                    continue
                
                # 计算余弦相似度
                similarity = self._cosine_similarity(embedding, entry_embedding)
                
                # 添加到结果列表
                results.append({
                    "id": entry.get("id"),
                    "turn_id": entry.get("turn_id"),
                    "session_id": entry.get("session_id"),
                    "content": entry.get("content"),
                    "similarity": similarity,
                    "metadata": entry.get("metadata", {})
                })
            
            # 按相似度排序
            results.sort(key=lambda x: x["similarity"], reverse=True)
            
            # 限制结果数量
            top_results = results[:limit]
            
            logger.info(f"获取与轮次 {turn_id} 相似的轮次成功，共找到 {len(top_results)} 条结果")
            return top_results
        except Exception as e:
            logger.error(f"获取相似轮次失败: {e}")
            return []
