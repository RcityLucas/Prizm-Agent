"""
Rainbow Agent 增强型代理团队模块

提供基于关系网络的多代理协作系统
"""
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
import os
import json
from datetime import datetime
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .models import RelationshipManager, RelationshipIntensity, RelationshipStatus
from .tasks import TaskManager, Task
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AgentProfile:
    """代理配置文件"""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        role: str,
        description: str = "",
        capabilities: List[str] = None,
        expertise: List[str] = None,
        personality_traits: List[str] = None,
        system_prompt: str = "",
        metadata: Dict[str, Any] = None
    ):
        """
        初始化代理配置文件
        
        Args:
            agent_id: 代理ID
            name: 代理名称
            role: 代理角色
            description: 代理描述
            capabilities: 代理能力列表
            expertise: 代理专业领域列表
            personality_traits: 代理性格特征列表
            system_prompt: 代理系统提示词
            metadata: 额外元数据
        """
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.description = description
        self.capabilities = capabilities or []
        self.expertise = expertise or []
        self.personality_traits = personality_traits or []
        self.system_prompt = system_prompt
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "capabilities": self.capabilities,
            "expertise": self.expertise,
            "personality_traits": self.personality_traits,
            "system_prompt": self.system_prompt,
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentProfile':
        """从字典创建代理配置文件"""
        return cls(
            agent_id=data.get("agent_id", ""),
            name=data.get("name", ""),
            role=data.get("role", ""),
            description=data.get("description", ""),
            capabilities=data.get("capabilities", []),
            expertise=data.get("expertise", []),
            personality_traits=data.get("personality_traits", []),
            system_prompt=data.get("system_prompt", ""),
            metadata=data.get("metadata", {})
        )


class AgentTask:
    """代理任务"""
    
    def __init__(
        self,
        task_id: str,
        title: str,
        description: str,
        assigned_agent_id: Optional[str] = None,
        status: str = "pending",
        priority: int = 1,
        dependencies: List[str] = None,
        created_at: Optional[datetime] = None,
        deadline: Optional[datetime] = None,
        result: Any = None,
        parent_task_id: Optional[str] = None,
        subtasks: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """
        初始化代理任务
        
        Args:
            task_id: 任务ID
            title: 任务标题
            description: 任务描述
            assigned_agent_id: 分配的代理ID
            status: 任务状态 (pending, in_progress, completed, failed)
            priority: 优先级 (1-5，5为最高)
            dependencies: 依赖的任务ID列表
            created_at: 创建时间
            deadline: 截止时间
            result: 任务结果
            parent_task_id: 父任务ID
            subtasks: 子任务ID列表
            metadata: 额外元数据
        """
        self.task_id = task_id
        self.title = title
        self.description = description
        self.assigned_agent_id = assigned_agent_id
        self.status = status
        self.priority = min(max(priority, 1), 5)
        self.dependencies = dependencies or []
        self.created_at = created_at or datetime.now()
        self.deadline = deadline
        self.result = result
        self.parent_task_id = parent_task_id
        self.subtasks = subtasks or []
        self.metadata = metadata or {}
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "assigned_agent_id": self.assigned_agent_id,
            "status": self.status,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "result": self.result,
            "parent_task_id": self.parent_task_id,
            "subtasks": self.subtasks,
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentTask':
        """从字典创建代理任务"""
        # 处理日期字段
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        deadline = datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None
        start_time = datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None
        end_time = datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None
        
        task = cls(
            task_id=data.get("task_id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            assigned_agent_id=data.get("assigned_agent_id"),
            status=data.get("status", "pending"),
            priority=data.get("priority", 1),
            dependencies=data.get("dependencies", []),
            created_at=created_at,
            deadline=deadline,
            result=data.get("result"),
            parent_task_id=data.get("parent_task_id"),
            subtasks=data.get("subtasks", []),
            metadata=data.get("metadata", {})
        )
        
        # 设置时间字段
        task.start_time = start_time
        task.end_time = end_time
        
        return task
        
    def start(self) -> None:
        """开始任务"""
        self.status = "in_progress"
        self.start_time = datetime.now()
        
    def complete(self, result: Any = None) -> None:
        """完成任务"""
        self.status = "completed"
        self.end_time = datetime.now()
        if result is not None:
            self.result = result
            
    def fail(self, error_message: str = "") -> None:
        """任务失败"""
        self.status = "failed"
        self.end_time = datetime.now()
        self.result = error_message or "Task failed"
        
    def can_start(self, completed_tasks: List[str]) -> bool:
        """
        检查任务是否可以开始
        
        Args:
            completed_tasks: 已完成的任务ID列表
            
        Returns:
            是否可以开始
        """
        # 检查依赖任务是否都已完成
        for dep_id in self.dependencies:
            if dep_id not in completed_tasks:
                return False
        return True


class EnhancedAgentTeam:
    """增强型代理团队"""
    
    def __init__(
        self,
        team_id: Optional[str] = None,
        name: str = "Agent Team",
        description: str = "",
        relationship_manager: Optional[RelationshipManager] = None,
        task_manager: Optional[TaskManager] = None
    ):
        """
        初始化增强型代理团队
        
        Args:
            team_id: 团队ID，如果为None则自动生成
            name: 团队名称
            description: 团队描述
            relationship_manager: 关系管理器实例
            task_manager: 任务管理器实例
        """
        self.team_id = team_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.agents: Dict[str, AgentProfile] = {}
        self.tasks: Dict[str, AgentTask] = {}
        self.relationship_manager = relationship_manager or RelationshipManager()
        self.task_manager = task_manager or TaskManager(self.relationship_manager)
        
        # 任务执行器
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # 任务处理函数映射
        self.task_handlers: Dict[str, Callable] = {}
        
    def add_agent(self, agent: AgentProfile) -> str:
        """
        添加代理
        
        Args:
            agent: 代理配置文件
            
        Returns:
            代理ID
        """
        self.agents[agent.agent_id] = agent
        return agent.agent_id
        
    def remove_agent(self, agent_id: str) -> bool:
        """
        移除代理
        
        Args:
            agent_id: 代理ID
            
        Returns:
            是否移除成功
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False
        
    def get_agent(self, agent_id: str) -> Optional[AgentProfile]:
        """
        获取代理
        
        Args:
            agent_id: 代理ID
            
        Returns:
            代理配置文件
        """
        return self.agents.get(agent_id)
        
    def create_task(self, **kwargs) -> str:
        """
        创建任务
        
        Args:
            **kwargs: 任务参数
            
        Returns:
            任务ID
        """
        task_id = kwargs.get("task_id") or str(uuid.uuid4())
        task = AgentTask(task_id=task_id, **kwargs)
        self.tasks[task_id] = task
        return task_id
        
    def get_task(self, task_id: str) -> Optional[AgentTask]:
        """
        获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务实例
        """
        return self.tasks.get(task_id)
        
    def assign_task(self, task_id: str, agent_id: str) -> bool:
        """
        分配任务
        
        Args:
            task_id: 任务ID
            agent_id: 代理ID
            
        Returns:
            是否分配成功
        """
        task = self.get_task(task_id)
        agent = self.get_agent(agent_id)
        
        if not task or not agent:
            return False
            
        task.assigned_agent_id = agent_id
        return True
        
    def decompose_task(
        self, 
        parent_task_id: str, 
        subtasks: List[Dict[str, Any]]
    ) -> List[str]:
        """
        分解任务
        
        Args:
            parent_task_id: 父任务ID
            subtasks: 子任务参数列表
            
        Returns:
            子任务ID列表
        """
        parent_task = self.get_task(parent_task_id)
        if not parent_task:
            return []
            
        subtask_ids = []
        for subtask_params in subtasks:
            # 设置父任务ID
            subtask_params["parent_task_id"] = parent_task_id
            
            # 创建子任务
            subtask_id = self.create_task(**subtask_params)
            subtask_ids.append(subtask_id)
            
        # 更新父任务的子任务列表
        parent_task.subtasks.extend(subtask_ids)
        
        return subtask_ids
        
    def register_task_handler(self, task_type: str, handler: Callable) -> None:
        """
        注册任务处理函数
        
        Args:
            task_type: 任务类型
            handler: 处理函数，接受任务实例和代理配置文件作为参数
        """
        self.task_handlers[task_type] = handler
        
    def execute_task(self, task_id: str) -> Any:
        """
        执行任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务结果
        """
        task = self.get_task(task_id)
        if not task:
            return None
            
        # 检查任务是否已分配
        if not task.assigned_agent_id:
            return "Task not assigned to any agent"
            
        # 获取代理
        agent = self.get_agent(task.assigned_agent_id)
        if not agent:
            return "Assigned agent not found"
            
        # 检查任务依赖
        completed_tasks = [t_id for t_id, t in self.tasks.items() if t.status == "completed"]
        if not task.can_start(completed_tasks):
            return "Task dependencies not satisfied"
            
        # 开始任务
        task.start()
        
        try:
            # 获取任务类型
            task_type = task.metadata.get("task_type", "default")
            
            # 查找处理函数
            handler = self.task_handlers.get(task_type)
            
            if handler:
                # 使用注册的处理函数
                result = handler(task, agent)
            else:
                # 默认处理逻辑
                result = f"Executed task {task.title} with agent {agent.name}"
                
            # 更新关系数据（如果任务与关系相关）
            if "relationship_id" in task.metadata:
                relationship_id = task.metadata["relationship_id"]
                self.relationship_manager.update_interaction(
                    relationship_id=relationship_id,
                    rounds=1,
                    emotional_resonance="emotional" in task_type
                )
                
            # 完成任务
            task.complete(result)
            return result
            
        except Exception as e:
            # 任务失败
            error_message = f"Task execution failed: {str(e)}"
            task.fail(error_message)
            logger.error(error_message)
            return error_message
            
    async def execute_task_async(self, task_id: str) -> Any:
        """
        异步执行任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.execute_task, task_id)
        
    async def execute_tasks_in_order(self, task_ids: List[str]) -> Dict[str, Any]:
        """
        按顺序执行任务
        
        Args:
            task_ids: 任务ID列表
            
        Returns:
            任务ID到结果的映射
        """
        results = {}
        for task_id in task_ids:
            results[task_id] = await self.execute_task_async(task_id)
        return results
        
    async def execute_tasks_parallel(self, task_ids: List[str]) -> Dict[str, Any]:
        """
        并行执行任务
        
        Args:
            task_ids: 任务ID列表
            
        Returns:
            任务ID到结果的映射
        """
        tasks = [self.execute_task_async(task_id) for task_id in task_ids]
        results = await asyncio.gather(*tasks)
        return dict(zip(task_ids, results))
        
    def select_agent_for_task(self, task: AgentTask) -> Optional[str]:
        """
        为任务选择最合适的代理
        
        Args:
            task: 任务实例
            
        Returns:
            代理ID，如果没有合适的代理则返回None
        """
        if not self.agents:
            return None
            
        # 获取任务所需的能力和专业领域
        required_capabilities = task.metadata.get("required_capabilities", [])
        required_expertise = task.metadata.get("required_expertise", [])
        
        # 计算每个代理的匹配度
        agent_scores = {}
        
        for agent_id, agent in self.agents.items():
            score = 0
            
            # 检查能力匹配度
            for cap in required_capabilities:
                if cap in agent.capabilities:
                    score += 1
                    
            # 检查专业领域匹配度
            for exp in required_expertise:
                if exp in agent.expertise:
                    score += 2  # 专业领域匹配权重更高
                    
            # 考虑代理当前负载
            assigned_tasks = sum(1 for t in self.tasks.values() 
                               if t.assigned_agent_id == agent_id and t.status == "in_progress")
            load_penalty = assigned_tasks * 0.5
            
            # 最终分数
            agent_scores[agent_id] = score - load_penalty
            
        # 选择得分最高的代理
        if not agent_scores:
            return None
            
        return max(agent_scores.items(), key=lambda x: x[1])[0]
        
    def create_relationship_based_task(
        self, 
        relationship_id: str,
        task_type: str,
        title: str,
        description: str,
        priority: int = 3,
        **kwargs
    ) -> Optional[str]:
        """
        基于关系创建任务
        
        Args:
            relationship_id: 关系ID
            task_type: 任务类型
            title: 任务标题
            description: 任务描述
            priority: 优先级
            **kwargs: 其他任务参数
            
        Returns:
            任务ID，如果关系不存在则返回None
        """
        # 检查关系是否存在
        relationship = self.relationship_manager.get_relationship(relationship_id)
        if not relationship:
            return None
            
        # 创建任务
        task_id = self.create_task(
            title=title,
            description=description,
            priority=priority,
            metadata={
                "task_type": task_type,
                "relationship_id": relationship_id,
                "entity_id": relationship.entity_id,
                "connected_to_id": relationship.connected_to_id
            },
            **kwargs
        )
        
        # 选择合适的代理
        agent_id = self.select_agent_for_task(self.get_task(task_id))
        if agent_id:
            self.assign_task(task_id, agent_id)
            
        return task_id
        
    def generate_relationship_tasks(self, relationship_id: str) -> List[str]:
        """
        为关系生成任务
        
        Args:
            relationship_id: 关系ID
            
        Returns:
            生成的任务ID列表
        """
        # 使用任务管理器生成关系任务
        rel_task_ids = self.task_manager.generate_tasks_for_relationship(relationship_id)
        
        # 将关系任务转换为代理任务
        agent_task_ids = []
        
        for rel_task_id in rel_task_ids:
            rel_task = self.task_manager.get_task(rel_task_id)
            if not rel_task:
                continue
                
            # 创建代理任务
            agent_task_id = self.create_relationship_based_task(
                relationship_id=relationship_id,
                task_type=rel_task.task_type,
                title=rel_task.title,
                description=rel_task.description,
                priority=rel_task.priority
            )
            
            if agent_task_id:
                agent_task_ids.append(agent_task_id)
                
        return agent_task_ids
        
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """
        获取待处理的任务
        
        Returns:
            待处理任务列表
        """
        return [task.to_dict() for task in self.tasks.values() 
               if task.status == "pending"]
        
    def get_in_progress_tasks(self) -> List[Dict[str, Any]]:
        """
        获取进行中的任务
        
        Returns:
            进行中任务列表
        """
        return [task.to_dict() for task in self.tasks.values() 
               if task.status == "in_progress"]
        
    def get_completed_tasks(self) -> List[Dict[str, Any]]:
        """
        获取已完成的任务
        
        Returns:
            已完成任务列表
        """
        return [task.to_dict() for task in self.tasks.values() 
               if task.status == "completed"]
        
    def get_failed_tasks(self) -> List[Dict[str, Any]]:
        """
        获取失败的任务
        
        Returns:
            失败任务列表
        """
        return [task.to_dict() for task in self.tasks.values() 
               if task.status == "failed"]
        
    def get_agent_tasks(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        获取代理的任务
        
        Args:
            agent_id: 代理ID
            
        Returns:
            代理任务列表
        """
        return [task.to_dict() for task in self.tasks.values() 
               if task.assigned_agent_id == agent_id]
        
    def get_relationship_tasks(self, relationship_id: str) -> List[Dict[str, Any]]:
        """
        获取关系相关的任务
        
        Args:
            relationship_id: 关系ID
            
        Returns:
            关系任务列表
        """
        return [task.to_dict() for task in self.tasks.values() 
               if task.metadata.get("relationship_id") == relationship_id]
               
    def save_to_file(self, filepath: str) -> None:
        """
        保存团队数据到文件
        
        Args:
            filepath: 文件路径
        """
        data = {
            "team_id": self.team_id,
            "name": self.name,
            "description": self.description,
            "agents": [agent.to_dict() for agent in self.agents.values()],
            "tasks": [task.to_dict() for task in self.tasks.values()]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    @classmethod
    def load_from_file(
        cls, 
        filepath: str,
        relationship_manager: Optional[RelationshipManager] = None,
        task_manager: Optional[TaskManager] = None
    ) -> 'EnhancedAgentTeam':
        """
        从文件加载团队数据
        
        Args:
            filepath: 文件路径
            relationship_manager: 关系管理器实例
            task_manager: 任务管理器实例
            
        Returns:
            团队实例
        """
        if not os.path.exists(filepath):
            return cls(relationship_manager=relationship_manager, task_manager=task_manager)
            
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        team = cls(
            team_id=data.get("team_id"),
            name=data.get("name", "Agent Team"),
            description=data.get("description", ""),
            relationship_manager=relationship_manager,
            task_manager=task_manager
        )
        
        # 加载代理
        for agent_data in data.get("agents", []):
            agent = AgentProfile.from_dict(agent_data)
            team.add_agent(agent)
            
        # 加载任务
        for task_data in data.get("tasks", []):
            task = AgentTask.from_dict(task_data)
            team.tasks[task.task_id] = task
            
        return team
