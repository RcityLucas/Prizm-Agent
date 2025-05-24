"""
SurrealDB记忆存储

使用SurrealDB存储对话记忆，提供更好的并发性能和可扩展性
"""
import json
import asyncio
from typing import Dict, List, Any, Optional
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SurrealMemory:
    """使用SurrealDB存储对话记忆"""
    
    def __init__(self, storage_factory):
        """初始化SurrealMemory
        
        Args:
            storage_factory: 存储工厂实例
        """
        self.storage_factory = storage_factory
        self.memory_table = "memories"
        logger.info("SurrealMemory初始化完成")
    
    def add(self, session_id: str, content: Dict[str, Any]) -> None:
        """添加记忆
        
        Args:
            session_id: 会话ID
            content: 记忆内容
        """
        try:
            # 获取存储实例
            storage = self.storage_factory.get_storage()
            
            # 准备记忆数据
            memory_data = {
                "session_id": session_id,
                "content": json.dumps(content) if isinstance(content, dict) else content,
                "timestamp": content.get("timestamp", "")
            }
            
            # 创建异步循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 添加记忆
            loop.run_until_complete(storage.create(self.memory_table, memory_data))
            
            logger.info(f"为会话 {session_id} 添加记忆成功")
        except Exception as e:
            logger.error(f"添加记忆失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
    
    def get(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取记忆
        
        Args:
            session_id: 会话ID
            limit: 限制返回的记忆数量
            
        Returns:
            记忆列表
        """
        try:
            # 获取存储实例
            storage = self.storage_factory.get_storage()
            
            # 创建异步循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 构建查询
            query = f"""
            SELECT * FROM {self.memory_table}
            WHERE session_id = '{session_id}'
            ORDER BY timestamp DESC
            LIMIT {limit}
            """
            
            # 执行查询
            results = loop.run_until_complete(storage.query(query))
            
            # 处理结果
            memories = []
            if results and len(results) > 0:
                for item in results[0]:
                    try:
                        content = item.get("content", "{}")
                        if isinstance(content, str):
                            content = json.loads(content)
                        memories.append(content)
                    except json.JSONDecodeError:
                        logger.warning(f"解析记忆内容失败: {content}")
                        continue
            
            logger.info(f"获取会话 {session_id} 的记忆成功，共 {len(memories)} 条")
            return memories
        except Exception as e:
            logger.error(f"获取记忆失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            return []
    
    def clear(self, session_id: str) -> None:
        """清除记忆
        
        Args:
            session_id: 会话ID
        """
        try:
            # 获取存储实例
            storage = self.storage_factory.get_storage()
            
            # 创建异步循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 构建查询
            query = f"""
            DELETE FROM {self.memory_table}
            WHERE session_id = '{session_id}'
            """
            
            # 执行查询
            loop.run_until_complete(storage.query(query))
            
            logger.info(f"清除会话 {session_id} 的记忆成功")
        except Exception as e:
            logger.error(f"清除记忆失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
    
    def search(self, session_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索记忆
        
        Args:
            session_id: 会话ID
            query: 搜索关键词
            limit: 限制返回的记忆数量
            
        Returns:
            记忆列表
        """
        # 由于SurrealDB不支持全文搜索，我们先获取所有记忆，然后在Python中进行简单的关键词匹配
        try:
            # 获取所有记忆
            all_memories = self.get(session_id, 100)  # 获取较多的记忆以便搜索
            
            # 在Python中进行简单的关键词匹配
            matched_memories = []
            for memory in all_memories:
                # 将记忆内容转换为字符串进行搜索
                memory_str = json.dumps(memory, ensure_ascii=False)
                if query.lower() in memory_str.lower():
                    matched_memories.append(memory)
                    if len(matched_memories) >= limit:
                        break
            
            logger.info(f"搜索会话 {session_id} 的记忆成功，共找到 {len(matched_memories)} 条")
            return matched_memories
        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            return []
