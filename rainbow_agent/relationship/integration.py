"""
Rainbow Agent 关系系统集成模块

将关系管理系统与主代理系统集成
"""
from typing import Dict, List, Any, Optional, Union, Callable
import os
import json
from datetime import datetime
import asyncio

from .models import RelationshipManager, RelationshipStatus, RelationshipIntensity
from .tools import RelationshipTool, RelationshipAnalysisTool
from .tasks import TaskManager, Task
from .agent_team import EnhancedAgentTeam, AgentProfile
from .utils import calculate_relationship_stats, generate_relationship_report
from ..utils.logger import get_logger

logger = get_logger(__name__)


class RelationshipSystem:
    """关系系统集成类"""
    
    def __init__(
        self,
        data_dir: str = "./data/relationships",
        auto_save: bool = True,
        save_interval: int = 60  # 60秒自动保存一次
    ):
        """
        初始化关系系统
        
        Args:
            data_dir: 数据保存目录
            auto_save: 是否自动保存
            save_interval: 自动保存间隔（秒）
        """
        self.data_dir = data_dir
        self.auto_save = auto_save
        self.save_interval = save_interval
        
        # 创建数据目录
        os.makedirs(data_dir, exist_ok=True)
        
        # 初始化组件
        self.relationship_manager = self._load_relationship_manager()
        self.task_manager = self._load_task_manager()
        self.agent_team = self._load_agent_team()
        
        # 初始化工具
        self.relationship_tool = RelationshipTool(self.relationship_manager)
        self.analysis_tool = RelationshipAnalysisTool(self.relationship_manager)
        
        # 自动保存任务
        self._save_task = None
        if auto_save:
            self._start_auto_save()
    
    def _load_relationship_manager(self) -> RelationshipManager:
        """加载关系管理器"""
        filepath = os.path.join(self.data_dir, "relationships.json")
        if os.path.exists(filepath):
            try:
                return RelationshipManager.load_from_file(filepath)
            except Exception as e:
                logger.error(f"加载关系数据失败: {e}")
        return RelationshipManager()
    
    def _load_task_manager(self) -> TaskManager:
        """加载任务管理器"""
        filepath = os.path.join(self.data_dir, "tasks.json")
        if os.path.exists(filepath):
            try:
                return TaskManager.load_from_file(filepath, self.relationship_manager)
            except Exception as e:
                logger.error(f"加载任务数据失败: {e}")
        return TaskManager(self.relationship_manager)
    
    def _load_agent_team(self) -> EnhancedAgentTeam:
        """加载代理团队"""
        filepath = os.path.join(self.data_dir, "agent_team.json")
        if os.path.exists(filepath):
            try:
                return EnhancedAgentTeam.load_from_file(
                    filepath, 
                    self.relationship_manager,
                    self.task_manager
                )
            except Exception as e:
                logger.error(f"加载代理团队数据失败: {e}")
        return EnhancedAgentTeam(
            relationship_manager=self.relationship_manager,
            task_manager=self.task_manager
        )
    
    def _start_auto_save(self) -> None:
        """启动自动保存"""
        async def auto_save_task():
            while True:
                await asyncio.sleep(self.save_interval)
                try:
                    self.save_data()
                    logger.info(f"自动保存关系系统数据成功")
                except Exception as e:
                    logger.error(f"自动保存关系系统数据失败: {e}")
        
        # 创建异步任务
        loop = asyncio.get_event_loop()
        self._save_task = loop.create_task(auto_save_task())
    
    def save_data(self) -> None:
        """保存所有数据"""
        # 保存关系数据
        rel_filepath = os.path.join(self.data_dir, "relationships.json")
        self.relationship_manager.save_to_file(rel_filepath)
        
        # 保存任务数据
        task_filepath = os.path.join(self.data_dir, "tasks.json")
        self.task_manager.save_to_file(task_filepath)
        
        # 保存代理团队数据
        team_filepath = os.path.join(self.data_dir, "agent_team.json")
        self.agent_team.save_to_file(team_filepath)
    
    def get_tools(self) -> List[Any]:
        """获取关系系统工具"""
        return [self.relationship_tool, self.analysis_tool]
    
    def process_message(
        self, 
        message: str, 
        sender_id: str, 
        sender_type: str, 
        receiver_id: str, 
        receiver_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        处理消息，更新关系数据
        
        Args:
            message: 消息内容
            sender_id: 发送者ID
            sender_type: 发送者类型
            receiver_id: 接收者ID
            receiver_type: 接收者类型
            metadata: 消息元数据
            
        Returns:
            处理结果
        """
        # 查找或创建关系
        rel_id = self.relationship_manager.find_relationship(sender_id, receiver_id)
        
        if not rel_id:
            # 创建新关系
            rel_id = self.relationship_manager.create_relationship(
                entity_id=sender_id,
                entity_type=sender_type,
                connected_to_id=receiver_id,
                connected_to_type=receiver_type
            )
            logger.info(f"创建新关系: {sender_id} -> {receiver_id}, ID: {rel_id}")
        
        # 更新互动数据
        metadata = metadata or {}
        emotional_resonance = metadata.get("emotional_resonance", False)
        
        self.relationship_manager.update_interaction(
            relationship_id=rel_id,
            rounds=1,
            emotional_resonance=emotional_resonance
        )
        
        # 更新协作数据
        if "collaboration" in metadata:
            collab_data = metadata["collaboration"]
            self.relationship_manager.update_collaboration(
                relationship_id=rel_id,
                diary_count=collab_data.get("diary_count", 0),
                co_creation_count=collab_data.get("co_creation_count", 0),
                gift_count=collab_data.get("gift_count", 0)
            )
        
        # 获取更新后的关系数据
        relationship = self.relationship_manager.get_relationship(rel_id)
        intensity = self.relationship_manager.get_intensity(rel_id)
        
        # 生成关系任务
        task_ids = self.task_manager.generate_tasks_for_relationship(rel_id)
        agent_task_ids = self.agent_team.generate_relationship_tasks(rel_id)
        
        # 返回处理结果
        return {
            "relationship_id": rel_id,
            "relationship": relationship.to_dict() if relationship else None,
            "intensity": intensity.to_dict() if intensity else None,
            "generated_tasks": len(task_ids) + len(agent_task_ids),
            "message_processed": True
        }
    
    def get_relationship_context(
        self, 
        entity_id: str, 
        connected_to_id: str
    ) -> Dict[str, Any]:
        """
        获取关系上下文信息
        
        Args:
            entity_id: 实体ID
            connected_to_id: 关联实体ID
            
        Returns:
            关系上下文信息
        """
        # 查找关系
        rel_id = self.relationship_manager.find_relationship(entity_id, connected_to_id)
        
        if not rel_id:
            return {
                "exists": False,
                "message": f"未找到 {entity_id} 和 {connected_to_id} 之间的关系"
            }
        
        # 获取关系数据
        relationship = self.relationship_manager.get_relationship(rel_id)
        intensity = self.relationship_manager.get_intensity(rel_id)
        
        if not relationship:
            return {
                "exists": False,
                "message": f"关系 {rel_id} 数据不存在"
            }
        
        # 获取关系任务
        tasks = self.task_manager.get_tasks_by_relationship(rel_id)
        agent_tasks = self.agent_team.get_relationship_tasks(rel_id)
        
        # 构建上下文
        context = {
            "exists": True,
            "relationship_id": rel_id,
            "relationship": relationship.to_dict(),
            "intensity": intensity.to_dict() if intensity else None,
            "relationship_level": intensity.get_relationship_level() if intensity else "unknown",
            "ris": intensity.calculate_ris() if intensity else 0.0,
            "status": relationship.status.value,
            "total_interaction_rounds": relationship.total_interaction_rounds,
            "active_days": relationship.active_days,
            "first_interaction": relationship.first_interaction_time.isoformat(),
            "last_active": relationship.last_active_time.isoformat(),
            "pending_tasks": [t for t in tasks if t["status"] == "pending"],
            "agent_tasks": agent_tasks
        }
        
        return context
    
    def get_relationship_prompt(
        self, 
        entity_id: str, 
        connected_to_id: str
    ) -> str:
        """
        生成关系提示词
        
        Args:
            entity_id: 实体ID
            connected_to_id: 关联实体ID
            
        Returns:
            关系提示词
        """
        context = self.get_relationship_context(entity_id, connected_to_id)
        
        if not context["exists"]:
            return """
            您正在与一个新的实体建立联系。这是您们的首次互动，尚未建立关系网络。
            请以友好、开放的态度进行交流，了解对方的需求和期望。
            """
        
        # 获取关系数据
        rel_level = context.get("relationship_level", "unknown")
        status = context.get("status", "UNKNOWN")
        rounds = context.get("total_interaction_rounds", 0)
        ris = context.get("ris", 0.0)
        
        # 根据关系状态和强度生成提示词
        if status == "ACTIVE":
            if rel_level == "stranger":
                prompt = f"""
                您正在与一个初步接触的实体交流。您们已经有了 {rounds} 轮互动，但关系仍处于初始阶段。
                建议保持友好、礼貌的态度，逐步了解对方的兴趣和需求。
                """
            elif rel_level == "acquaintance":
                prompt = f"""
                您正在与一个熟人交流。您们已经有了 {rounds} 轮互动，建立了基本的了解。
                可以适当展示更多个性化的交流，参考之前的互动内容，但仍需保持一定的礼貌距离。
                """
            elif rel_level == "friend":
                prompt = f"""
                您正在与一个朋友交流。您们已经有了 {rounds} 轮深入互动，建立了良好的关系基础。
                可以使用更加轻松、自然的交流方式，适当使用幽默，并主动提供帮助和支持。
                """
            elif rel_level == "close_friend":
                prompt = f"""
                您正在与一个密友交流。您们已经有了 {rounds} 轮深度互动，建立了深厚的信任关系。
                可以使用亲密的称呼，分享更深层次的想法，主动关心对方的状态和需求。
                """
            elif rel_level == "intimate":
                prompt = f"""
                您正在与一个亲密伙伴交流。您们已经有了 {rounds} 轮紧密互动，建立了极高的信任和理解。
                可以完全展示真实的自我，使用专属的表达方式，主动预判对方的需求并提供支持。
                """
            else:
                prompt = f"""
                您正在与一个活跃联系人交流。您们已经有了 {rounds} 轮互动，建立了一定的关系基础。
                请根据之前的互动历史，保持一致的交流风格和态度。
                """
        elif status == "COOLING":
            prompt = f"""
            您正在与一个冷却中的联系人交流。您们之间的互动频率正在降低，但仍有 {rounds} 轮历史互动。
            建议温和地重新建立联系，可以回顾之前的共同话题，但不要过于强势或急切。
            """
        elif status == "SILENT":
            prompt = f"""
            您正在与一个长期沉默的联系人重新建立联系。您们之间已经有很长时间没有互动了。
            建议以全新的态度开始对话，温和地询问近况，不要假设对方记得所有之前的互动细节。
            """
        else:
            prompt = f"""
            您正在与一个联系人交流。您们之间已经有了 {rounds} 轮互动。
            请保持友好、专业的态度，根据对方的反应调整交流方式。
            """
        
        # 添加关系强度提示
        if ris < 0.3:
            prompt += "\n关系强度较低，建议保持适当距离，以专业和礼貌为主。"
        elif ris < 0.6:
            prompt += "\n关系强度中等，可以适当展示个性，但仍需注意专业边界。"
        else:
            prompt += "\n关系强度较高，可以使用更加个性化和亲近的交流方式。"
        
        return prompt.strip()
    
    def register_agent(
        self,
        agent_id: str,
        name: str,
        role: str,
        description: str = "",
        capabilities: List[str] = None,
        expertise: List[str] = None
    ) -> str:
        """
        注册代理
        
        Args:
            agent_id: 代理ID
            name: 代理名称
            role: 代理角色
            description: 代理描述
            capabilities: 代理能力列表
            expertise: 代理专业领域列表
            
        Returns:
            代理ID
        """
        agent = AgentProfile(
            agent_id=agent_id,
            name=name,
            role=role,
            description=description,
            capabilities=capabilities,
            expertise=expertise
        )
        
        return self.agent_team.add_agent(agent)
    
    def register_task_handler(
        self,
        task_type: str,
        handler: Callable
    ) -> None:
        """
        注册任务处理函数
        
        Args:
            task_type: 任务类型
            handler: 处理函数
        """
        self.agent_team.register_task_handler(task_type, handler)
    
    def get_relationship_summary(
        self,
        entity_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取关系摘要
        
        Args:
            entity_id: 实体ID，如果为None则获取所有关系的摘要
            
        Returns:
            关系摘要
        """
        return generate_relationship_report(self.relationship_manager, entity_id)
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """
        获取待处理的任务
        
        Returns:
            待处理任务列表
        """
        # 合并关系任务和代理任务
        rel_tasks = self.task_manager.get_tasks_by_status("pending")
        agent_tasks = self.agent_team.get_pending_tasks()
        
        return rel_tasks + agent_tasks
    
    def get_executable_tasks(self) -> List[Dict[str, Any]]:
        """
        获取可执行的任务
        
        Returns:
            可执行任务列表
        """
        return self.task_manager.get_executable_tasks()
    
    async def execute_tasks(self) -> Dict[str, Any]:
        """
        执行所有可执行的任务
        
        Returns:
            执行结果
        """
        # 获取可执行的任务
        executable_tasks = self.task_manager.get_executable_tasks()
        
        # 转换为代理任务
        agent_task_ids = []
        for task_data in executable_tasks:
            # 创建代理任务
            task_id = self.agent_team.create_task(
                title=task_data.get("title", ""),
                description=task_data.get("description", ""),
                priority=task_data.get("priority", 1),
                metadata={
                    "task_type": task_data.get("task_type", "general"),
                    "relationship_id": task_data.get("relationship_id"),
                    "original_task_id": task_data.get("task_id")
                }
            )
            
            if task_id:
                agent_task_ids.append(task_id)
                
                # 为任务选择合适的代理
                task = self.agent_team.get_task(task_id)
                agent_id = self.agent_team.select_agent_for_task(task)
                if agent_id:
                    self.agent_team.assign_task(task_id, agent_id)
        
        # 执行任务
        results = {}
        if agent_task_ids:
            results = await self.agent_team.execute_tasks_parallel(agent_task_ids)
            
            # 更新原始任务状态
            for task_id, result in results.items():
                task = self.agent_team.get_task(task_id)
                if task and task.status == "completed" and "original_task_id" in task.metadata:
                    original_task_id = task.metadata["original_task_id"]
                    self.task_manager.complete_task(original_task_id)
        
        return {
            "executed_tasks": len(results),
            "results": results
        }


# 创建默认关系系统实例
default_relationship_system = RelationshipSystem()


def get_relationship_system() -> RelationshipSystem:
    """获取默认关系系统实例"""
    return default_relationship_system
