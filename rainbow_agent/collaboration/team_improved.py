"""
改进的多代理协作团队系统

提供增强的代理协作机制，支持更灵活的任务分解、动态团队组建和并行执行。
支持异步操作、任务依赖管理和自动错误恢复。
"""
from typing import List, Dict, Any, Optional, Callable, Tuple, Set, Union
import uuid
import time
import json
import asyncio
import threading
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..agent import RainbowAgent
from ..agent_updated import RainbowAgent as EnhancedAgent
from ..utils.logger import get_logger
from ..memory.memory import Memory, SimpleMemory

logger = get_logger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待处理
    ASSIGNED = "assigned"    # 已分配给代理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    BLOCKED = "blocked"      # 被阻塞（等待其他任务完成）


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class Task:
    """
    增强的任务类，表示需要代理协作完成的具体任务
    """
    
    def __init__(
        self,
        task_id: str,
        description: str,
        parent_id: Optional[str] = None,
        assigned_to: Optional[str] = None,
        requires_skills: List[str] = None,
        dependencies: List[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        context: Dict[str, Any] = None,
    ):
        """
        初始化任务
        
        Args:
            task_id: 任务ID
            description: 任务描述
            parent_id: 父任务ID (如果是子任务)
            assigned_to: 分配给的代理ID
            requires_skills: 所需技能列表
            dependencies: 依赖的其他任务ID列表
            priority: 任务优先级
            context: 任务上下文信息
        """
        self.task_id = task_id
        self.description = description
        self.parent_id = parent_id
        self.assigned_to = assigned_to
        self.requires_skills = requires_skills or []
        self.dependencies = dependencies or []
        self.priority = priority
        self.context = context or {}
        self.status = TaskStatus.PENDING
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.subtasks = []
        self.error = None
        self.attempts = 0
        self.max_attempts = 2  # 最大尝试次数
    
    def start(self) -> None:
        """标记任务开始处理"""
        self.status = TaskStatus.PROCESSING
        self.started_at = time.time()
        logger.info(f"任务 {self.task_id} 开始处理")
    
    def complete(self, result: Any) -> None:
        """
        完成任务
        
        Args:
            result: 任务结果
        """
        self.status = TaskStatus.COMPLETED
        self.completed_at = time.time()
        self.result = result
        duration = self.completed_at - (self.started_at or self.created_at)
        logger.info(f"任务 {self.task_id} 已完成，用时 {duration:.2f}秒")
    
    def fail(self, reason: str) -> None:
        """
        标记任务失败
        
        Args:
            reason: 失败原因
        """
        self.attempts += 1
        self.error = reason
        
        # 如果未达到最大尝试次数，重置为待处理状态
        if self.attempts < self.max_attempts:
            self.status = TaskStatus.PENDING
            logger.warning(f"任务 {self.task_id} 失败: {reason}，将重试 (尝试 {self.attempts}/{self.max_attempts})")
        else:
            self.status = TaskStatus.FAILED
            self.completed_at = time.time()
            self.result = {"error": reason}
            logger.error(f"任务 {self.task_id} 最终失败: {reason} (尝试 {self.attempts}/{self.max_attempts})")
    
    def block(self, reason: str) -> None:
        """
        标记任务被阻塞
        
        Args:
            reason: 阻塞原因
        """
        self.status = TaskStatus.BLOCKED
        self.error = reason
        logger.warning(f"任务 {self.task_id} 被阻塞: {reason}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典表示
        
        Returns:
            任务的字典表示
        """
        return {
            "task_id": self.task_id,
            "description": self.description,
            "parent_id": self.parent_id,
            "assigned_to": self.assigned_to,
            "requires_skills": self.requires_skills,
            "dependencies": self.dependencies,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "subtasks": [subtask.to_dict() for subtask in self.subtasks],
            "error": self.error,
            "attempts": self.attempts,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """
        从字典创建任务
        
        Args:
            data: 任务数据字典
            
        Returns:
            Task实例
        """
        task = cls(
            task_id=data["task_id"],
            description=data["description"],
            parent_id=data.get("parent_id"),
            assigned_to=data.get("assigned_to"),
            requires_skills=data.get("requires_skills", []),
            dependencies=data.get("dependencies", []),
            priority=TaskPriority(data.get("priority", 1)),
            context=data.get("context", {}),
        )
        
        task.status = TaskStatus(data["status"])
        task.created_at = data["created_at"]
        task.started_at = data.get("started_at")
        task.completed_at = data.get("completed_at")
        task.result = data.get("result")
        task.error = data.get("error")
        task.attempts = data.get("attempts", 0)
        
        # 递归创建子任务
        for subtask_data in data.get("subtasks", []):
            subtask = cls.from_dict(subtask_data)
            task.subtasks.append(subtask)
        
        return task


class EnhancedAgentTeam:
    """
    改进的代理团队，协调多个代理协同工作
    
    支持并行任务执行、任务依赖管理和异步操作
    """
    
    def __init__(
        self,
        name: str,
        coordinator: Optional[EnhancedAgent] = None,
        max_output_size: int = 50000,
        max_execution_time: int = 120,
        max_decomposition_depth: int = 3,
        memory: Optional[Memory] = None,
        parallel_execution: bool = True,
        max_parallel_tasks: int = 5,
    ):
        """
        初始化代理团队
        
        Args:
            name: 团队名称
            coordinator: 协调者代理，如果为None则创建默认协调者
            max_output_size: 最大输出大小（字符数）
            max_execution_time: 最大执行时间（秒）
            max_decomposition_depth: 最大任务分解深度
            memory: 团队共享记忆系统
            parallel_execution: 是否并行执行任务
            max_parallel_tasks: 最大并行任务数
        """
        self.name = name
        self.coordinator = coordinator or self._create_default_coordinator()
        self.max_output_size = max_output_size
        self.max_execution_time = max_execution_time
        self.max_decomposition_depth = max_decomposition_depth
        self.memory = memory or SimpleMemory()
        self.parallel_execution = parallel_execution
        self.max_parallel_tasks = max_parallel_tasks
        
        # 代理和任务存储
        self.agents = {}  # 代理ID -> 代理实例
        self.agent_skills = {}  # 代理ID -> 技能列表
        self.tasks = {}  # 任务ID -> 任务实例
        
        # 执行状态跟踪
        self.start_time = None
        self.executor = ThreadPoolExecutor(max_workers=max_parallel_tasks)
        self.task_locks = {}  # 任务ID -> 锁，用于并发控制
        
        logger.info(f"增强型代理团队 '{name}' 已初始化，最大并行任务数: {max_parallel_tasks}")
    
    def _create_default_coordinator(self) -> EnhancedAgent:
        """
        创建默认的协调者代理
        
        Returns:
            EnhancedAgent实例
        """
        system_prompt = f"""你是{self.name}的协调者，负责分解和协调复杂任务。

你的主要职责是：
1. 将复杂问题分解为可管理的子任务
2. 确定每个子任务所需的技能
3. 并在所有子任务完成后整合结果

当分解任务时，请考虑以下因素：
- 每个子任务应该有明确的目标和范围
- 子任务应该相对独立，但可以有依赖关系
- 每个子任务应该指定所需的技能或专业知识

在整合结果时，请确保：
- 综合所有子任务的贡献
- 解决任何冲突或不一致
- 提供全面、连贯的最终答案
"""
        
        return EnhancedAgent(
            name=f"{self.name}的协调者",
            system_prompt=system_prompt,
            model="gpt-3.5-turbo",
            memory=self.memory,
            temperature=0.2,  # 使用低温度以提高确定性
        )
    
    def add_agent(self, agent: Union[RainbowAgent, EnhancedAgent], skills: List[str]) -> str:
        """
        添加代理到团队
        
        Args:
            agent: 要添加的代理
            skills: 代理的技能列表
            
        Returns:
            代理ID
        """
        # 生成唯一的代理ID
        agent_id = str(uuid.uuid4())
        
        # 如果是原始的RainbowAgent，将其升级为EnhancedAgent
        if isinstance(agent, RainbowAgent) and not isinstance(agent, EnhancedAgent):
            logger.info(f"将代理 '{agent.name}' 升级为增强型代理")
            enhanced_agent = EnhancedAgent(
                name=agent.name,
                system_prompt=agent.system_prompt,
                tools=agent.tools,
                memory=agent.memory,
                model=agent.model,
                temperature=0.7,
            )
            self.agents[agent_id] = enhanced_agent
        else:
            self.agents[agent_id] = agent
        
        # 存储代理技能
        self.agent_skills[agent_id] = skills
        
        logger.info(f"代理 '{agent.name}' 添加到团队，技能: {', '.join(skills)}")
        return agent_id
    
    def create_task(self, description: str, context: Dict[str, Any] = None, parent_id: Optional[str] = None,
                   priority: TaskPriority = TaskPriority.NORMAL, dependencies: List[str] = None) -> str:
        """
        创建新任务
        
        Args:
            description: 任务描述
            context: 任务上下文信息
            parent_id: 父任务ID (如果是子任务)
            priority: 任务优先级
            dependencies: 依赖的其他任务ID列表
            
        Returns:
            任务ID
        """
        # 生成唯一的任务ID
        task_id = str(uuid.uuid4())
        
        # 创建任务
        task = Task(
            task_id=task_id,
            description=description,
            parent_id=parent_id,
            dependencies=dependencies,
            priority=priority,
            context=context or {}
        )
        
        # 如果有父任务，将子任务添加到父任务
        if parent_id and parent_id in self.tasks:
            self.tasks[parent_id].subtasks.append(task)
        
        # 存储任务
        self.tasks[task_id] = task
        
        # 创建任务锁，用于并发控制
        self.task_locks[task_id] = threading.Lock()
        
        logger.info(f"任务 '{task_id}' 已创建: {description[:50]}{'...' if len(description) > 50 else ''}")
        return task_id
    
    def _decompose_task(self, task_id: str) -> List[str]:
        """
        使用协调者分解任务
        
        Args:
            task_id: 要分解的任务ID
            
        Returns:
            子任务ID列表
        """
        # 获取任务
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"找不到任务 {task_id}")
            return []
            
        # 如果任务已经有子任务，直接返回
        if task.subtasks:
            return [subtask.task_id for subtask in task.subtasks]
            
        logger.info(f"开始分解任务 '{task_id}'")
        
        # 准备协调者提示
        available_skills = set()
        for skills in self.agent_skills.values():
            available_skills.update(skills)
            
        prompt = f"""请分解以下任务为子任务，并为每个子任务指定所需的技能。

任务描述: {task.description}

团队可用的技能: {', '.join(sorted(available_skills))}

请将任务分解为3-5个子任务。对每个子任务，提供以下信息:
1. 子任务描述: 简要描述该子任务的目标和范围
2. 所需技能: 列出完成该子任务所需的技能（从上面的可用技能中选择）
3. 依赖关系: 如果该子任务依赖于其他子任务，请指出依赖的子任务编号

请以JSON格式返回结果，如下所示:
```json
{{
  "subtasks": [
    {{
      "description": "子任务1的描述",
      "required_skills": ["技能1", "技能2"],
      "dependencies": []
    }},
    {{
      "description": "子任务2的描述",
      "required_skills": ["技能3"],
      "dependencies": [0]
    }}
  ]
}}
```
其中dependencies中的数字表示依赖的子任务的索引。
"""
        
        try:
            # 调用协调者代理
            response = self.coordinator.run(prompt)
            
            # 如果返回的是字典，提取response字段
            if isinstance(response, dict) and "response" in response:
                response = response["response"]
                
            # 尝试从响应中提取JSON
            json_match = re.search(r'```json\s*({.*?})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 如果没有找到JSON块，尝试直接解析整个响应
                json_str = response
                
            # 解析JSON
            subtasks_data = json.loads(json_str)
            
            # 创建子任务
            subtask_ids = []
            subtask_index_to_id = {}  # 用于跟踪依赖关系
            
            for i, subtask_info in enumerate(subtasks_data.get("subtasks", [])):
                # 创建子任务，暂时不设置依赖
                subtask_id = self.create_task(
                    description=subtask_info["description"],
                    context=task.context,
                    parent_id=task_id,
                    requires_skills=subtask_info.get("required_skills", [])
                )
                
                subtask_ids.append(subtask_id)
                subtask_index_to_id[i] = subtask_id
            
            # 设置依赖关系
            for i, subtask_info in enumerate(subtasks_data.get("subtasks", [])):
                dependencies = []
                for dep_index in subtask_info.get("dependencies", []):
                    if dep_index < len(subtask_ids):
                        dependencies.append(subtask_index_to_id[dep_index])
                        
                if dependencies and subtask_ids[i] in self.tasks:
                    self.tasks[subtask_ids[i]].dependencies = dependencies
            
            logger.info(f"任务 '{task_id}' 分解为 {len(subtask_ids)} 个子任务")
            return subtask_ids
            
        except Exception as e:
            logger.error(f"分解任务 '{task_id}' 时出错: {e}")
            return []
    
    def _assign_task(self, task_id: str) -> bool:
        """
        分配任务给合适的代理
        
        Args:
            task_id: 要分配的任务ID
            
        Returns:
            是否成功分配
        """
        # 获取任务
        task = self.tasks.get(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return False
            
        # 如果任务已经分配，返回成功
        if task.assigned_to:
            task.status = TaskStatus.ASSIGNED
            return True
            
        # 检查依赖是否满足
        for dep_id in task.dependencies:
            if dep_id in self.tasks and self.tasks[dep_id].status != TaskStatus.COMPLETED:
                task.block(f"等待依赖任务 {dep_id} 完成")
                return False
        
        # 找到最合适的代理
        best_agent_id = None
        best_match_score = -1
        
        for agent_id, skills in self.agent_skills.items():
            # 计算技能匹配分数
            required_skills = set(task.requires_skills)
            agent_skills = set(skills)
            
            if not required_skills:  # 如果没有指定所需技能，任何代理都可以处理
                match_score = 1
            else:
                # 计算代理技能覆盖率
                matching_skills = required_skills.intersection(agent_skills)
                match_score = len(matching_skills) / len(required_skills) if required_skills else 0
            
            if match_score > best_match_score:
                best_match_score = match_score
                best_agent_id = agent_id
        
        # 如果找到合适的代理，分配任务
        if best_agent_id:
            task.assigned_to = best_agent_id
            task.status = TaskStatus.ASSIGNED
            logger.info(f"任务 '{task_id}' 分配给代理 '{self.agents[best_agent_id].name}' (匹配分数: {best_match_score:.2f})")
            return True
        else:
            logger.warning(f"找不到合适的代理来处理任务 '{task_id}'")
            return False

