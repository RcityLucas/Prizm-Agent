# rainbow_agent/frequency/frequency_integrator.py
"""
频率感知系统集成器，负责将频率感知系统与对话系统整合
"""
from typing import Dict, Any, List, Optional, Callable, Awaitable
import asyncio
import time
import uuid
from ..utils.logger import get_logger
from .context_sampler import ContextSampler
from .frequency_sense_core import FrequencySenseCore
from .expression_planner import ExpressionPlanner
from .expression_generator import ExpressionGenerator
from .expression_dispatcher import ExpressionDispatcher
from .memory_sync import MemorySync
from ..memory.memory import Memory

logger = get_logger(__name__)

class FrequencyIntegrator:
    """
    频率感知系统集成器，负责将频率感知系统与对话系统整合，
    使AI能够根据上下文自主决定何时主动表达
    """
    
    def __init__(
        self,
        memory: Memory,
        output_callback: Callable[[str, Dict[str, Any]], Awaitable[bool]],
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化频率感知系统集成器
        
        Args:
            memory: 记忆系统接口
            output_callback: 输出回调函数，接收表达内容和元数据
            config: 配置参数
        """
        self.memory = memory
        self.output_callback = output_callback
        self.config = config or {}
        
        # 创建频率感知系统组件
        self.context_sampler = ContextSampler(self.config.get("context_sampler_config"))
        self.frequency_sense_core = FrequencySenseCore(
            self.context_sampler,
            self.config.get("frequency_sense_core_config")
        )
        self.expression_planner = ExpressionPlanner(
            self.memory,
            self.config.get("expression_planner_config")
        )
        self.expression_generator = ExpressionGenerator(
            self.config.get("expression_generator_config")
        )
        self.expression_dispatcher = ExpressionDispatcher(
            self.config.get("expression_dispatcher_config")
        )
        
        # 检查是否提供了自定义的MemorySync实例
        memory_sync_config = self.config.get("memory_sync_config", {})
        if "memory_sync_instance" in memory_sync_config:
            self.memory_sync = memory_sync_config["memory_sync_instance"]
            logger.info("使用提供的自定义MemorySync实例")
        else:
            self.memory_sync = MemorySync(
                self.memory,
                memory_sync_config
            )
            logger.info("创建新的MemorySync实例")
        
        # 注册输出通道
        self.expression_dispatcher.register_channel("main", self._handle_expression_output)
        
        # 监控任务
        self.monitoring_task = None
        
        # 是否正在运行
        self.is_running = False
        
        # 监控间隔（秒）
        self.monitoring_interval = self.config.get("monitoring_interval", 60)
        
        # 上下文缓存
        self.context_cache = {}
        
        # 会话映射
        self.session_map = {}
        
        logger.info("频率感知系统集成器初始化完成")
    
    async def start(self):
        """
        启动频率感知系统
        """
        if self.is_running:
            logger.warning("频率感知系统已经在运行")
            return
        
        # 启动表达调度器
        await self.expression_dispatcher.start_dispatcher()
        
        # 启动监控任务
        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("频率感知系统已启动")
    
    async def stop(self):
        """
        停止频率感知系统
        """
        if not self.is_running:
            logger.warning("频率感知系统未在运行")
            return
        
        # 停止监控任务
        self.is_running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
        
        # 停止表达调度器
        await self.expression_dispatcher.stop_dispatcher()
        
        logger.info("频率感知系统已停止")
    
    async def update_context(self, session_id: str, context_update: Dict[str, Any]):
        """
        更新会话上下文
        
        Args:
            session_id: 会话ID
            context_update: 上下文更新
        """
        # 获取或创建会话上下文
        if session_id not in self.context_cache:
            self.context_cache[session_id] = {
                "session_id": session_id,
                "last_update_time": time.time(),
                "user_id": context_update.get("user_id", "unknown"),
                "conversation_history": [],
                "recent_topics": [],
                "user_input": None,
                "input_type": None,
                "user_emotion": "neutral",
                "has_open_questions": False,
                "notifications": [],
                "reminders": []
            }
        
        # 更新上下文
        context = self.context_cache[session_id]
        context.update({k: v for k, v in context_update.items() if k in context})
        
        # 更新特定字段
        if "user_input" in context_update:
            context["user_input"] = context_update["user_input"]
            context["last_update_time"] = time.time()
        
        if "conversation_history_item" in context_update:
            if len(context["conversation_history"]) >= 20:
                context["conversation_history"] = context["conversation_history"][-19:]
            context["conversation_history"].append(context_update["conversation_history_item"])
        
        if "topic" in context_update:
            if context_update["topic"] not in context["recent_topics"]:
                if len(context["recent_topics"]) >= 5:
                    context["recent_topics"] = context["recent_topics"][-4:]
                context["recent_topics"].append(context_update["topic"])
        
        logger.debug(f"更新会话上下文，会话ID: {session_id}")
    
    async def register_user_activity(self, session_id: str, user_id: str, activity_type: str = "message"):
        """
        注册用户活动
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            activity_type: 活动类型
        """
        # 映射会话ID和用户ID
        self.session_map[session_id] = user_id
        
        # 更新上下文
        await self.update_context(session_id, {
            "user_id": user_id,
            "last_update_time": time.time(),
            "activity_type": activity_type
        })
        
        # 更新用户互动次数
        await self.memory_sync.update_user_interaction_count(user_id)
        
        logger.debug(f"注册用户活动，会话ID: {session_id}, 用户ID: {user_id}, 活动类型: {activity_type}")
    
    async def process_user_message(self, session_id: str, user_id: str, message: str, input_type: str = None):
        """
        处理用户消息
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            message: 用户消息
            input_type: 输入类型
        """
        # 注册用户活动
        await self.register_user_activity(session_id, user_id, "message")
        
        # 更新上下文
        await self.update_context(session_id, {
            "user_input": message,
            "input_type": input_type,
            "conversation_history_item": f"用户: {message}"
        })
        
        logger.debug(f"处理用户消息，会话ID: {session_id}, 用户ID: {user_id}")
    
    async def process_system_response(self, session_id: str, response: str):
        """
        处理系统响应
        
        Args:
            session_id: 会话ID
            response: 系统响应
        """
        # 更新上下文
        await self.update_context(session_id, {
            "conversation_history_item": f"AI: {response}"
        })
        
        # 检测是否包含问题
        has_question = "?" in response or "？" in response
        if has_question:
            await self.update_context(session_id, {
                "has_open_questions": True
            })
        
        logger.debug(f"处理系统响应，会话ID: {session_id}")
    
    async def add_notification(self, session_id: str, notification: Dict[str, Any]):
        """
        添加通知
        
        Args:
            session_id: 会话ID
            notification: 通知信息
        """
        if session_id not in self.context_cache:
            logger.warning(f"会话不存在，无法添加通知: {session_id}")
            return
        
        # 获取上下文
        context = self.context_cache[session_id]
        
        # 添加通知
        if "notifications" not in context:
            context["notifications"] = []
        
        context["notifications"].append({
            "id": notification.get("id", str(uuid.uuid4())),
            "content": notification["content"],
            "priority": notification.get("priority", "normal"),
            "timestamp": notification.get("timestamp", time.time())
        })
        
        # 限制通知数量
        if len(context["notifications"]) > 10:
            context["notifications"] = context["notifications"][-10:]
        
        logger.debug(f"添加通知，会话ID: {session_id}")
    
    async def add_reminder(self, session_id: str, reminder: Dict[str, Any]):
        """
        添加提醒
        
        Args:
            session_id: 会话ID
            reminder: 提醒信息
        """
        if session_id not in self.context_cache:
            logger.warning(f"会话不存在，无法添加提醒: {session_id}")
            return
        
        # 获取上下文
        context = self.context_cache[session_id]
        
        # 添加提醒
        if "reminders" not in context:
            context["reminders"] = []
        
        context["reminders"].append({
            "id": reminder.get("id", str(uuid.uuid4())),
            "content": reminder["content"],
            "priority": reminder.get("priority", "normal"),
            "due_time": reminder.get("due_time", time.time() + 3600),
            "timestamp": reminder.get("timestamp", time.time())
        })
        
        # 限制提醒数量
        if len(context["reminders"]) > 10:
            context["reminders"] = context["reminders"][-10:]
        
        logger.debug(f"添加提醒，会话ID: {session_id}")
    
    async def trigger_expression(self, session_id: str) -> bool:
        """
        触发表达决策
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否触发了表达
        """
        if session_id not in self.context_cache:
            logger.warning(f"会话不存在，无法触发表达: {session_id}")
            return False
        
        # 获取上下文
        context = self.context_cache[session_id]
        user_id = context.get("user_id", "unknown")
        
        # 决定是否表达
        should_express, expression_info = await self.frequency_sense_core.decide_expression(context)
        
        if not should_express:
            logger.debug(f"决定不表达，会话ID: {session_id}")
            return False
        
        # 规划表达
        planned_expression = await self.expression_planner.plan_expression(expression_info, user_id)
        
        # 生成表达
        generated_expression = await self.expression_generator.generate_expression(planned_expression)
        
        # 将表达加入调度队列
        await self.expression_dispatcher.queue_expression(generated_expression, "main")
        
        # 记录表达到记忆
        await self.memory_sync.record_expression(generated_expression, user_id)
        
        # 记录上下文采样
        signals = self.context_sampler.sample(context)
        await self.memory_sync.record_context_sample(signals, user_id)
        
        logger.info(f"触发表达成功，会话ID: {session_id}, 类型: {generated_expression['content']['type']}")
        return True
    
    async def _monitoring_loop(self):
        """
        监控循环，定期检查各会话是否需要主动表达
        """
        logger.info("频率感知监控循环启动")
        
        while self.is_running:
            try:
                # 当前时间
                current_time = time.time()
                
                # 检查每个会话
                for session_id, context in list(self.context_cache.items()):
                    # 跳过最近更新的会话
                    if current_time - context.get("last_update_time", 0) < self.monitoring_interval:
                        continue
                    
                    # 尝试触发表达
                    await self.trigger_expression(session_id)
                
                # 等待下一次检查
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                logger.info("频率感知监控循环被取消")
                break
            except Exception as e:
                logger.error(f"频率感知监控循环错误: {e}")
                # 出错后短暂等待
                await asyncio.sleep(10)
    
    async def _handle_expression_output(self, expression: Dict[str, Any]) -> bool:
        """
        处理表达输出
        
        Args:
            expression: 表达信息
            
        Returns:
            是否成功处理
        """
        try:
            # 获取表达内容
            content = expression.get("final_content")
            if not content:
                logger.warning("表达内容为空")
                return False
            
            # 获取用户ID
            user_id = expression.get("user_info", {}).get("id") or expression.get("user_info", {}).get("name", "unknown")
            
            # 查找对应的会话ID
            session_id = None
            for sid, uid in self.session_map.items():
                if uid == user_id:
                    session_id = sid
                    break
            
            if not session_id:
                logger.warning(f"找不到用户对应的会话，用户ID: {user_id}")
                # 使用第一个会话
                if self.session_map:
                    session_id = next(iter(self.session_map))
                else:
                    return False
            
            # 构建元数据
            metadata = {
                "type": "frequency_expression",
                "expression_type": expression["content"]["type"],
                "priority": expression.get("priority_score", 0.5),
                "relationship_stage": expression.get("relationship_stage", "unknown"),
                "session_id": session_id,
                "user_id": user_id
            }
            
            # 调用输出回调
            success = await self.output_callback(content, metadata)
            
            if success:
                # 更新上下文
                await self.update_context(session_id, {
                    "conversation_history_item": f"AI: {content}"
                })
                
                logger.info(f"表达输出成功，会话ID: {session_id}, 用户ID: {user_id}")
            else:
                logger.warning(f"表达输出失败，会话ID: {session_id}, 用户ID: {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"处理表达输出错误: {e}")
            return False
