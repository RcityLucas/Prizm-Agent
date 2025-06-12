"""
对话处理器模块

负责处理用户输入和生成响应，支持多模态输入和自动会话创建。
整合了原有的dialogue_processor_v2.py功能，提供统一的对话处理接口。
"""
import uuid
import logging
import threading
import sqlite3
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional, Union

from rainbow_agent.utils.logger import get_logger
from rainbow_agent.core.dialogue_manager import DialogueManager
from rainbow_agent.core.session_manager import SessionManager
from rainbow_agent.core.memory_manager import MemoryManager
from rainbow_agent.utils.constants import DIALOGUE_TYPES
from rainbow_agent.api.dialogue_history_integration import DialogueHistoryIntegrator

# 配置日志
logger = get_logger(__name__)

# 线程本地存储，用于管理数据库连接
_connection_local = threading.local()

def get_connection():
    """获取当前线程的数据库连接"""
    if not hasattr(_connection_local, "connection"):
        # 创建新的连接，设置超时和隔离级别
        _connection_local.connection = sqlite3.connect(
            "data/sessions.sqlite", 
            timeout=30.0,
            isolation_level=None  # 自动提交模式
        )
        # 启用WAL模式
        _connection_local.connection.execute("PRAGMA journal_mode=WAL")
    
    return _connection_local.connection

class SessionManager:
    """会话管理器类，负责会话的创建和管理"""
    
    def __init__(self, db_path="data/sessions.sqlite"):
        """
        初始化会话管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._init_db()
        logger.info("会话管理器初始化完成")
    
    def _init_db(self):
        """初始化数据库表结构"""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # 创建会话表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                user_id TEXT NOT NULL,
                dialogue_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_activity_at TEXT NOT NULL,
                metadata TEXT
            )
            ''')
            
            # 创建参与者表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS participants (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
            ''')
            
            logger.info("数据库表结构初始化完成")
        finally:
            conn.close()
    
    def create_session(self, user_id: str, title: Optional[str] = None, 
                      dialogue_type: str = "human_to_ai_private", 
                      participants: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        创建新会话
        
        Args:
            user_id: 用户ID
            title: 会话标题，如果不提供则使用默认标题
            dialogue_type: 对话类型
            participants: 参与者列表
            
        Returns:
            创建的会话数据
        """
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # 生成会话ID
            session_id = str(uuid.uuid4())
            
            # 创建会话时间
            now = datetime.now().isoformat()
            
            # 会话标题
            session_title = title if title else f"新对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # 默认参与者
            if not participants:
                participants = [
                    {
                        "id": user_id,
                        "name": "用户",
                        "type": "human"
                    },
                    {
                        "id": "ai_assistant",
                        "name": "Rainbow助手",
                        "type": "ai"
                    }
                ]
            
            # 插入会话数据
            cursor.execute('''
            INSERT INTO sessions (id, title, user_id, dialogue_type, created_at, updated_at, last_activity_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id, 
                session_title, 
                user_id, 
                dialogue_type, 
                now, 
                now, 
                now, 
                "{}"
            ))
            
            # 插入参与者数据
            for participant in participants:
                participant_id = participant.get("id", str(uuid.uuid4()))
                cursor.execute('''
                INSERT INTO participants (id, session_id, name, type, metadata)
                VALUES (?, ?, ?, ?, ?)
                ''', (
                    participant_id,
                    session_id,
                    participant.get("name", "未命名"),
                    participant.get("type", "unknown"),
                    "{}"
                ))
            
            # 构建返回的会话数据
            session = {
                "id": session_id,
                "title": session_title,
                "user_id": user_id,
                "dialogue_type": dialogue_type,
                "created_at": now,
                "updated_at": now,
                "last_activity_at": now,
                "participants": participants,
                "metadata": {}
            }
            
            logger.info(f"创建会话成功: {session_id}")
            return session
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            raise
        finally:
            conn.close()
    
    def get_sessions(self, user_id: Optional[str] = None, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取会话列表
        
        Args:
            user_id: 用户ID，如果提供则只返回该用户的会话
            limit: 限制返回的会话数
            offset: 跳过的会话数
            
        Returns:
            会话列表
        """
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # 构建查询
            query = "SELECT * FROM sessions"
            params = []
            
            if user_id:
                query += " WHERE user_id = ?"
                params.append(user_id)
            
            query += " ORDER BY last_activity_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            # 执行查询
            cursor.execute(query, params)
            sessions_data = cursor.fetchall()
            
            # 获取列名
            column_names = [description[0] for description in cursor.description]
            
            # 构建会话列表
            sessions = []
            for session_data in sessions_data:
                session = dict(zip(column_names, session_data))
                
                # 获取会话的参与者
                cursor.execute('''
                SELECT * FROM participants WHERE session_id = ?
                ''', (session["id"],))
                
                participants_data = cursor.fetchall()
                participant_columns = [description[0] for description in cursor.description]
                
                participants = []
                for participant_data in participants_data:
                    participant = dict(zip(participant_columns, participant_data))
                    participants.append(participant)
                
                session["participants"] = participants
                sessions.append(session)
            
            return sessions
        except Exception as e:
            logger.error(f"获取会话列表失败: {e}")
            return []
        finally:
            conn.close()
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取特定会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据，如果不存在则返回None
        """
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # 查询会话
            cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            session_data = cursor.fetchone()
            
            if not session_data:
                return None
            
            # 获取列名
            column_names = [description[0] for description in cursor.description]
            
            # 构建会话数据
            session = dict(zip(column_names, session_data))
            
            # 获取会话的参与者
            cursor.execute("SELECT * FROM participants WHERE session_id = ?", (session_id,))
            
            participants_data = cursor.fetchall()
            participant_columns = [description[0] for description in cursor.description]
            
            participants = []
            for participant_data in participants_data:
                participant = dict(zip(participant_columns, participant_data))
                participants.append(participant)
            
            session["participants"] = participants
            
            return session
        except Exception as e:
            logger.error(f"获取会话失败: {e}")
            return None
        finally:
            conn.close()
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        更新会话
        
        Args:
            session_id: 会话ID
            updates: 要更新的字段
            
        Returns:
            更新后的会话，如果会话不存在则返回None
        """
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # 检查会话是否存在
            cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            if not cursor.fetchone():
                return None
            
            # 更新时间
            updates["updated_at"] = datetime.now().isoformat()
            
            # 构建更新语句
            set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
            params = list(updates.values())
            params.append(session_id)
            
            # 执行更新
            cursor.execute(f"UPDATE sessions SET {set_clause} WHERE id = ?", params)
            
            # 返回更新后的会话
            return self.get_session(session_id)
        except Exception as e:
            logger.error(f"更新会话失败: {e}")
            return None
        finally:
            conn.close()
    
    def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # 检查会话是否存在
            cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            if not cursor.fetchone():
                return False
            
            # 删除参与者
            cursor.execute("DELETE FROM participants WHERE session_id = ?", (session_id,))
            
            # 删除会话
            cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            
            return True
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return False
        finally:
            conn.close()
    
    def create_session_if_not_exists(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """
        获取会话，如果不存在则创建新会话
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            会话数据
        """
        session = self.get_session(session_id)
        if session:
            return session
        
        # 创建新会话
        logger.info(f"会话 {session_id} 不存在，创建新会话")
        return self.create_session(user_id)


class DialogueProcessor:
    """对话处理器，负责处理用户输入和生成响应"""
    
    def __init__(self, dialogue_manager: DialogueManager, session_manager: SessionManager, memory_manager: Optional[MemoryManager] = None):
        """
        初始化对话处理器
        
        Args:
            dialogue_manager: 对话管理器
            session_manager: 会话管理器
            memory_manager: 记忆管理器
        """
        self.dialogue_manager = dialogue_manager
        self.session_manager = session_manager
        self.memory_manager = memory_manager
        self.multi_modal_manager = None
        self.has_frequency_system = hasattr(dialogue_manager, 'frequency_integrator')
        self.history_integrator = DialogueHistoryIntegrator(max_history_turns=10)
        
        logger.info(f"对话处理器初始化成功，对话管理器: {dialogue_manager.__class__.__name__}, 会话管理器: {session_manager.__class__.__name__}")
    
    async def process_input(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """
        处理用户输入，生成AI响应
        
        Args:
            data: 请求数据
            
        Returns:
            (response, status_code): 响应数据和状态码
        """
        try:
            logger.info(f"处理用户输入请求数据: {data}")
            
            session_id = data.get('sessionId')
            content = data.get('input')  # 前端使用 input 而不是 content
            role = data.get('role', 'user')
            metadata = data.get('metadata', {})
            user_id = data.get('userId', 'default_user')
            
            logger.info(f"处理用户输入参数: session_id={session_id}, content={content}, role={role}")
            
            # 验证必要参数
            if not session_id or not content:
                logger.warning("缺少必要参数: sessionId 和 input")
                return {
                    "error": "缺少必要参数: sessionId 和 input",
                    "success": False,
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat()
                }, 400
            
            # 获取会话信息或创建新会话
            session = self.session_manager.create_session_if_not_exists(session_id, user_id)
            
            if not session:
                logger.error(f"无法获取或创建会话: {session_id}")
                return {
                    "error": f"会话不存在且无法自动创建: {session_id}",
                    "sessionId": session_id,
                    "input": content,
                    "success": False,
                    "response": f"会话 {session_id} 不存在，请先创建会话",
                    "timestamp": datetime.now().isoformat(),
                    "id": str(uuid.uuid4())
                }, 404
            
            # 如果会话ID变更（自动创建了新会话），返回新会话信息
            if session.get("id") != session_id:
                new_session_id = session.get("id")
                logger.info(f"会话ID变更: {session_id} -> {new_session_id}")
                
                return {
                    "success": True,
                    "message": f"原会话 {session_id} 不存在，已自动创建新会话",
                    "oldSessionId": session_id,
                    "newSessionId": new_session_id,
                    "sessionId": new_session_id,
                    "title": session.get("title"),
                    "createdAt": session.get("created_at"),
                    "input": content,
                    "response": f"原会话不存在，已自动创建新会话。请输入您的问题。",
                    "timestamp": datetime.now().isoformat(),
                    "id": str(uuid.uuid4())
                }, 200
            
            # 处理多模态输入
            if self.multi_modal_manager and metadata:
                self._process_multimodal_input(metadata)
            
            # 创建用户轮次
            turn_id = str(uuid.uuid4())
            
            # 获取对话历史
            turns = self.dialogue_manager.get_turns(session_id)
            
            # 整合对话历史到元数据中
            enhanced_metadata = self.history_integrator.prepare_dialogue_context(
                session_id=session_id,
                turns=turns,
                metadata=metadata
            )
            
            # 调用对话管理器处理输入
            try:
                # 检查是否是异步方法
                if asyncio.iscoroutinefunction(self.dialogue_manager.process_input):
                    # 创建事件循环并运行异步方法
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    ai_response = loop.run_until_complete(self.dialogue_manager.process_input(
                        session_id=session_id,
                        user_id=user_id,
                        content=content,
                        input_type="text",
                        metadata=enhanced_metadata
                    ))
                    loop.close()
                else:
                    # 同步调用
                    ai_response = self.dialogue_manager.process_input(
                        session_id=session_id,
                        user_id=user_id,
                        content=content,
                        input_type="text",
                        metadata=enhanced_metadata
                    )
                
                # 如果启用了频率感知系统，在响应中添加频率相关元数据
                if self.has_frequency_system and hasattr(self.dialogue_manager, 'frequency_integrator'):
                    if 'metadata' not in ai_response:
                        ai_response['metadata'] = {}
                    
                    # 添加频率感知系统相关信息
                    ai_response['metadata']['frequency_aware'] = True
                    
                    # 尝试获取用户的关系阶段
                    try:
                        if asyncio.iscoroutinefunction(self.dialogue_manager.frequency_integrator.get_relationship_stage):
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            relationship_stage = loop.run_until_complete(
                                self.dialogue_manager.frequency_integrator.get_relationship_stage(user_id)
                            )
                            loop.close()
                        else:
                            relationship_stage = self.dialogue_manager.frequency_integrator.get_relationship_stage(user_id)
                        
                        ai_response['metadata']['relationship_stage'] = relationship_stage
                    except Exception as e:
                        logger.warning(f"获取用户关系阶段失败: {e}")
            except Exception as e:
                logger.error(f"调用对话管理器处理输入失败: {e}")
                raise
            
            # 确保响应包含所有必要字段
            response = self._ensure_response_fields(ai_response, session_id, content)
            
            return response, 200
            
        except Exception as e:
            logger.error(f"处理用户输入失败: {e}")
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(error_traceback)
            
            return {
                "error": str(e),
                "traceback": error_traceback,
                "success": False,
                "sessionId": data.get("sessionId", ""),
                "input": data.get("input", ""),
                "response": f"处理输入时出现错误: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "id": str(uuid.uuid4())
            }, 500
    
    def _process_multimodal_input(self, metadata: Dict[str, Any]):
        """
        处理多模态输入
        
        Args:
            metadata: 元数据
        """
        if not self.multi_modal_manager:
            logger.warning("多模态管理器未初始化，跳过多模态处理")
            return
        
        # 处理图像
        if "image" in metadata:
            image_data = metadata.get("image")
            if image_data:
                try:
                    image_result = self.multi_modal_manager.process_image(image_data)
                    metadata["image_analysis"] = image_result
                except Exception as e:
                    logger.error(f"处理图像失败: {e}")
        
        # 处理音频
        if "audio" in metadata:
            audio_data = metadata.get("audio")
            if audio_data:
                try:
                    audio_result = self.multi_modal_manager.process_audio(audio_data)
                    metadata["audio_analysis"] = audio_result
                except Exception as e:
                    logger.error(f"处理音频失败: {e}")
    
    def _ensure_response_fields(self, response: Dict[str, Any], session_id: str, input_content: str) -> Dict[str, Any]:
        """
        确保响应包含必要的字段
        
        Args:
            response: 原始响应
            session_id: 会话ID
            input_content: 用户输入内容
            
        Returns:
            完整的响应数据
        """
        # 确保响应是字典
        if not isinstance(response, dict):
            response = {"response": str(response)}
        
        # 添加必要字段
        if "id" not in response:
            response["id"] = str(uuid.uuid4())
        
        if "timestamp" not in response:
            response["timestamp"] = datetime.now().isoformat()
        
        if "sessionId" not in response:
            response["sessionId"] = session_id
        
        if "input" not in response:
            response["input"] = input_content
        
        if "success" not in response:
            response["success"] = True
        
        # 确保元数据字段存在
        if "metadata" not in response:
            response["metadata"] = {}
        
        # 添加频率感知系统标记
        if self.has_frequency_system:
            response["metadata"]["frequency_aware"] = True
            
            # 如果对话管理器有频率集成器，添加更多元数据
            if hasattr(self.dialogue_manager, 'frequency_integrator'):
                # 获取用户ID
                user_id = response.get("userId", "default_user")
                
                # 添加频率感知系统版本信息
                response["metadata"]["frequency_system_version"] = "1.0"
                
                # 如果响应中没有关系阶段信息，尝试获取
                if "relationship_stage" not in response["metadata"] and user_id:
                    try:
                        if asyncio.iscoroutinefunction(self.dialogue_manager.frequency_integrator.get_relationship_stage):
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            relationship_stage = loop.run_until_complete(
                                self.dialogue_manager.frequency_integrator.get_relationship_stage(user_id)
                            )
                            loop.close()
                        else:
                            relationship_stage = self.dialogue_manager.frequency_integrator.get_relationship_stage(user_id)
                        
                        response["metadata"]["relationship_stage"] = relationship_stage
                    except Exception as e:
                        logger.warning(f"获取用户关系阶段失败: {e}")
        
        return response
    
    def get_turns(self, session_id: str) -> Tuple[Dict[str, Any], int]:
        """
        获取会话的对话轮次
        
        Args:
            session_id: 会话ID
            
        Returns:
            (response, status_code): 响应数据和状态码
        """
        try:
            # 获取会话信息
            session = self.session_manager.get_session(session_id)
            
            if not session:
                logger.warning(f"会话不存在: {session_id}")
                return {
                    "error": f"会话 {session_id} 不存在",
                    "success": False
                }, 404
            
            # 获取对话类型
            dialogue_type = session.get("dialogue_type", DIALOGUE_TYPES["HUMAN_AI_PRIVATE"])
            
            # 获取轮次列表
            turns = self.dialogue_manager.get_turns(session_id)
            
            # 格式化轮次
            formatted_turns = self._format_turns(turns, session_id, dialogue_type)
            
            return {
                "success": True,
                "turns": formatted_turns,
                "total": len(formatted_turns),
                "sessionId": session_id,
                "dialogueType": dialogue_type
            }, 200
            
        except Exception as e:
            logger.error(f"获取会话轮次失败: {e}")
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(error_traceback)
            
            return {
                "error": str(e),
                "traceback": error_traceback,
                "success": False,
                "sessionId": session_id
            }, 500
    
    def _format_turns(self, turns: List[Dict[str, Any]], session_id: str, dialogue_type: str) -> List[Dict[str, Any]]:
        """
        格式化轮次列表，适配前端
        
        Args:
            turns: 轮次列表
            session_id: 会话ID
            dialogue_type: 对话类型
            
        Returns:
            格式化后的轮次列表
        """
        formatted_turns = []
        
        # 根据对话类型进行不同的格式化
        if dialogue_type == DIALOGUE_TYPES.get("HUMAN_AI_PRIVATE", "human_to_ai_private"):
            # 人类与AI私聊类型，按照用户-AI对进行分组
            i = 0
            while i < len(turns):
                # 获取当前轮次
                turn = turns[i]
                role = turn.get("role", "")
                content = turn.get("content", "")
                timestamp = turn.get("created_at", "")
                
                # 如果是用户轮次，尝试找到对应的AI轮次
                if role == "user" and i + 1 < len(turns) and turns[i + 1].get("role") == "assistant":
                    # 用户轮次和AI轮次配对
                    ai_turn = turns[i + 1]
                    
                    formatted_turns.append({
                        "id": turn.get("id"),
                        "sessionId": session_id,
                        "userContent": content,
                        "aiContent": ai_turn.get("content", ""),
                        "timestamp": timestamp,
                        "metadata": turn.get("metadata", {}),
                        "aiMetadata": ai_turn.get("metadata", {}),
                        "dialogueType": dialogue_type
                    })
                    
                    # 跳过已处理的AI轮次
                    i += 2
                else:
                    # 如果是AI轮次但没有对应的人类轮次，则单独添加
                    formatted_turns.append({
                        "id": turn.get("id"),
                        "sessionId": session_id,
                        "role": role,
                        "content": content,
                        "timestamp": timestamp,
                        "metadata": turn.get("metadata", {}),
                        "dialogueType": dialogue_type
                    })
                    i += 1
        elif dialogue_type == DIALOGUE_TYPES.get("AI_AI_DIALOGUE", "ai_ai_dialogue"):
            # AI与AI对话类型，按照AI角色进行分组
            for turn in turns:
                role = turn.get("role", "")
                content = turn.get("content", "")
                timestamp = turn.get("created_at", "")
                metadata = turn.get("metadata", {})
                ai_role = metadata.get("ai_role", "AI")
                
                formatted_turns.append({
                    "id": turn.get("id"),
                    "sessionId": session_id,
                    "content": content,
                    "timestamp": timestamp,
                    "aiRole": ai_role,
                    "dialogueType": dialogue_type
                })
        elif dialogue_type == DIALOGUE_TYPES.get("AI_SELF_REFLECTION", "ai_self_reflection"):
            # AI自我反思类型，直接返回所有轮次
            for turn in turns:
                role = turn.get("role", "")
                content = turn.get("content", "")
                timestamp = turn.get("created_at", "")
                
                formatted_turns.append({
                    "id": turn.get("id"),
                    "sessionId": session_id,
                    "role": role,
                    "content": content,
                    "timestamp": timestamp,
                    "dialogueType": dialogue_type
                })
        else:
            # 其他对话类型，直接返回原始轮次
            for turn in turns:
                formatted_turns.append({
                    "id": turn.get("id"),
                    "sessionId": session_id,
                    "role": turn.get("role", ""),
                    "content": turn.get("content", ""),
                    "timestamp": turn.get("created_at", ""),
                    "metadata": turn.get("metadata", {}),
                    "dialogueType": dialogue_type
                })
        
        return formatted_turns
