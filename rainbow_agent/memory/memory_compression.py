"""
记忆压缩系统实现

提供对话记忆的摘要生成和关键信息提取功能
"""
from typing import List, Dict, Any, Optional, Tuple
import json
from datetime import datetime
import sqlite3

from .memory import Memory
from ..utils.logger import get_logger
from ..utils.llm import get_llm_client

logger = get_logger(__name__)


class MemoryCompression:
    """
    记忆压缩系统
    
    实现对话摘要生成和关键信息提取功能
    """
    
    def __init__(
        self,
        db_path: str = "memory.db",
        llm_client = None,
        summary_model: str = "gpt-3.5-turbo",
        compression_ratio: float = 0.3,  # 压缩比例
        importance_threshold: float = 0.6  # 重要性阈值
    ):
        """
        初始化记忆压缩系统
        
        Args:
            db_path: 数据库路径
            llm_client: LLM客户端
            summary_model: 摘要生成模型
            compression_ratio: 压缩比例 (0.0-1.0)
            importance_threshold: 重要性阈值 (0.0-1.0)
        """
        self.db_path = db_path
        self.llm_client = llm_client or get_llm_client()
        self.summary_model = summary_model
        self.compression_ratio = compression_ratio
        self.importance_threshold = importance_threshold
        
        self._init_db()
        
        logger.info("记忆压缩系统初始化完成")
    
    def _init_db(self) -> None:
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建摘要表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_timestamp TEXT NOT NULL,
            end_timestamp TEXT NOT NULL,
            original_count INTEGER NOT NULL,
            summary TEXT NOT NULL,
            key_points TEXT,
            created_at TEXT NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_conversation_summary(self, conversation: List[Dict[str, Any]]) -> str:
        """
        生成对话摘要
        
        Args:
            conversation: 对话列表，每项包含user_input和assistant_response
            
        Returns:
            对话摘要
        """
        if not conversation:
            return ""
        
        # 构建对话文本
        conversation_text = ""
        for i, item in enumerate(conversation):
            conversation_text += f"用户: {item['user_input']}\n"
            conversation_text += f"助手: {item['assistant_response']}\n\n"
        
        # 生成摘要提示
        prompt = f"""
        请对以下对话生成一个简洁的摘要，提取关键信息和重要观点。摘要应该覆盖对话的主要内容，但长度不超过原对话的{int(self.compression_ratio * 100)}%。

        对话内容:
        {conversation_text}

        摘要:
        """
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.summary_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
        except Exception as e:
            logger.error(f"生成对话摘要失败: {e}")
            return "摘要生成失败"
    
    def extract_key_points(self, conversation: List[Dict[str, Any]]) -> List[str]:
        """
        从对话中提取关键信息点
        
        Args:
            conversation: 对话列表，每项包含user_input和assistant_response
            
        Returns:
            关键信息点列表
        """
        if not conversation:
            return []
        
        # 构建对话文本
        conversation_text = ""
        for i, item in enumerate(conversation):
            conversation_text += f"用户: {item['user_input']}\n"
            conversation_text += f"助手: {item['assistant_response']}\n\n"
        
        # 提取关键点提示
        prompt = f"""
        请从以下对话中提取5-10个关键信息点。每个信息点应该是简洁的一句话，包含对话中的重要事实、决定或见解。
        以JSON格式返回结果，格式为: {{"key_points": ["信息点1", "信息点2", ...]}}.

        对话内容:
        {conversation_text}

        关键信息点:
        """
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.summary_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 解析JSON结果
            try:
                result = json.loads(result_text)
                return result.get("key_points", [])
            except json.JSONDecodeError:
                # 如果无法解析JSON，尝试直接提取列表项
                lines = result_text.split("\n")
                key_points = []
                for line in lines:
                    line = line.strip()
                    if line.startswith(("- ", "* ", "1. ", "2. ", "3. ", "4. ", "5. ", "6. ", "7. ", "8. ", "9. ", "10. ")):
                        key_points.append(line[2:].strip())
                return key_points
                
        except Exception as e:
            logger.error(f"提取关键信息点失败: {e}")
            return []
    
    def compress_conversation(self, conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        压缩对话记忆
        
        Args:
            conversation: 对话列表，每项包含user_input和assistant_response
            
        Returns:
            压缩结果，包含摘要和关键点
        """
        if not conversation:
            return {"summary": "", "key_points": []}
        
        # 生成摘要
        summary = self.generate_conversation_summary(conversation)
        
        # 提取关键点
        key_points = self.extract_key_points(conversation)
        
        # 保存到数据库
        if summary and conversation:
            self._save_summary(conversation, summary, key_points)
        
        return {
            "summary": summary,
            "key_points": key_points,
            "original_count": len(conversation),
            "compression_ratio": self.compression_ratio
        }
    
    def _save_summary(self, conversation: List[Dict[str, Any]], summary: str, key_points: List[str]) -> None:
        """
        保存摘要到数据库
        
        Args:
            conversation: 对话列表
            summary: 生成的摘要
            key_points: 关键信息点
        """
        if not conversation:
            return
            
        start_timestamp = conversation[0]["timestamp"]
        end_timestamp = conversation[-1]["timestamp"]
        original_count = len(conversation)
        created_at = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO memory_summaries 
            (start_timestamp, end_timestamp, original_count, summary, key_points, created_at) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                start_timestamp,
                end_timestamp,
                original_count,
                summary,
                json.dumps(key_points),
                created_at
            )
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"已保存对话摘要，原始对话数量: {original_count}")
    
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT id, start_timestamp, end_timestamp, original_count, summary, key_points, created_at FROM memory_summaries"
        params = []
        
        conditions = []
        if start_time:
            conditions.append("end_timestamp >= ?")
            params.append(start_time)
        
        if end_time:
            conditions.append("start_timestamp <= ?")
            params.append(end_time)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY end_timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        summaries = []
        for row in rows:
            id, start_timestamp, end_timestamp, original_count, summary, key_points_json, created_at = row
            
            try:
                key_points = json.loads(key_points_json) if key_points_json else []
            except json.JSONDecodeError:
                key_points = []
            
            summaries.append({
                "id": id,
                "start_timestamp": start_timestamp,
                "end_timestamp": end_timestamp,
                "original_count": original_count,
                "summary": summary,
                "key_points": key_points,
                "created_at": created_at
            })
        
        return summaries
    
    def compress_long_term_memories(self, days: int = 7, min_count: int = 20) -> Dict[str, Any]:
        """
        压缩长期记忆
        
        Args:
            days: 压缩多少天前的记忆
            min_count: 最小记忆数量，低于此数量不压缩
            
        Returns:
            压缩结果
        """
        # 获取需要压缩的记忆
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - datetime.timedelta(days=days)).isoformat()
        
        cursor.execute(
            """
            SELECT id, timestamp, user_input, assistant_response, importance, metadata
            FROM long_term_memories
            WHERE timestamp < ?
            ORDER BY timestamp ASC
            """,
            (cutoff_date,)
        )
        
        rows = cursor.fetchall()
        
        if len(rows) < min_count:
            conn.close()
            return {"status": "skipped", "reason": f"记忆数量 {len(rows)} 低于最小阈值 {min_count}"}
        
        # 将记录转换为对话格式
        conversation = []
        for row in rows:
            id, timestamp, user_input, assistant_response, importance, metadata_json = row
            
            try:
                metadata = json.loads(metadata_json) if metadata_json else {}
            except json.JSONDecodeError:
                metadata = {}
            
            conversation.append({
                "memory_id": id,
                "timestamp": timestamp,
                "user_input": user_input,
                "assistant_response": assistant_response,
                "importance": importance,
                "metadata": metadata
            })
        
        # 生成压缩结果
        compression_result = self.compress_conversation(conversation)
        
        # 删除原始记忆（仅保留重要的）
        memory_ids = [item["memory_id"] for item in conversation if item["importance"] < self.importance_threshold]
        
        if memory_ids:
            placeholders = ", ".join(["?"] * len(memory_ids))
            cursor.execute(f"DELETE FROM long_term_memories WHERE id IN ({placeholders})", memory_ids)
            
            # 同时删除相关的嵌入
            cursor.execute(f"DELETE FROM memory_embeddings WHERE memory_id IN ({placeholders})", memory_ids)
            
            conn.commit()
        
        conn.close()
        
        compression_result["status"] = "completed"
        compression_result["deleted_count"] = len(memory_ids)
        compression_result["retained_count"] = len(conversation) - len(memory_ids)
        
        return compression_result
