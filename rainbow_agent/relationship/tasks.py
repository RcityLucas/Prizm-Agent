"""
Rainbow Agent 关系任务管理模块

提供基于关系状态的动态任务管理功能
"""
from typing import Dict, List, Any, Optional, Union, Callable
import os
import json
from datetime import datetime, timedelta
import uuid

from .models import RelationshipManager, RelationshipStatus, RelationshipIntensity
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Task:
    """任务基类"""
    
    def __init__(
        self,
        task_id: Optional[str] = None,
        title: str = "",
        description: str = "",
        task_type: str = "general",
        priority: int = 1,
        status: str = "pending",
        due_date: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        related_entity_id: Optional[str] = None,
        relationship_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        初始化任务
        
        Args:
            task_id: 任务ID，如果为None则自动生成
            title: 任务标题
            description: 任务描述
            task_type: 任务类型
            priority: 优先级 (1-5，5为最高)
            status: 任务状态 (pending, in_progress, completed, cancelled)
            due_date: 截止日期
            created_at: 创建时间
            completed_at: 完成时间
            related_entity_id: 相关实体ID
            relationship_id: 相关关系ID
            metadata: 额外元数据
        """
        self.task_id = task_id or str(uuid.uuid4())
        self.title = title
        self.description = description
        self.task_type = task_type
        self.priority = min(max(priority, 1), 5)  # 确保优先级在1-5之间
        self.status = status
        self.due_date = due_date
        self.created_at = created_at or datetime.now()
        self.completed_at = completed_at
        self.related_entity_id = related_entity_id
        self.relationship_id = relationship_id
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "task_type": self.task_type,
            "priority": self.priority,
            "status": self.status,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "related_entity_id": self.related_entity_id,
            "relationship_id": self.relationship_id,
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """从字典创建任务"""
        # 处理日期字段
        due_date = datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        completed_at = datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        
        return cls(
            task_id=data.get("task_id"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            task_type=data.get("task_type", "general"),
            priority=data.get("priority", 1),
            status=data.get("status", "pending"),
            due_date=due_date,
            created_at=created_at,
            completed_at=completed_at,
            related_entity_id=data.get("related_entity_id"),
            relationship_id=data.get("relationship_id"),
            metadata=data.get("metadata", {})
        )
        
    def complete(self) -> None:
        """完成任务"""
        self.status = "completed"
        self.completed_at = datetime.now()
        
    def cancel(self) -> None:
        """取消任务"""
        self.status = "cancelled"
        
    def start(self) -> None:
        """开始任务"""
        self.status = "in_progress"
        
    def is_overdue(self) -> bool:
        """检查任务是否逾期"""
        if not self.due_date:
            return False
        return datetime.now() > self.due_date and self.status not in ["completed", "cancelled"]


class RelationshipTask(Task):
    """关系相关任务"""
    
    def __init__(
        self,
        relationship_id: str,
        relationship_intensity_threshold: float = 0.0,
        relationship_status_requirement: Optional[RelationshipStatus] = None,
        **kwargs
    ):
        """
        初始化关系任务
        
        Args:
            relationship_id: 关系ID
            relationship_intensity_threshold: 关系强度阈值，只有当关系强度超过此值时才会触发任务
            relationship_status_requirement: 关系状态要求，只有当关系处于指定状态时才会触发任务
            **kwargs: 传递给Task的其他参数
        """
        super().__init__(relationship_id=relationship_id, **kwargs)
        self.relationship_intensity_threshold = relationship_intensity_threshold
        self.relationship_status_requirement = relationship_status_requirement
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = super().to_dict()
        data.update({
            "relationship_intensity_threshold": self.relationship_intensity_threshold,
            "relationship_status_requirement": self.relationship_status_requirement.value if self.relationship_status_requirement else None
        })
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RelationshipTask':
        """从字典创建关系任务"""
        # 处理关系状态
        status_req = None
        if data.get("relationship_status_requirement"):
            try:
                status_req = RelationshipStatus(data["relationship_status_requirement"])
            except ValueError:
                pass
                
        # 提取关系特定字段
        relationship_id = data.get("relationship_id", "")
        intensity_threshold = data.get("relationship_intensity_threshold", 0.0)
        
        # 移除关系特定字段，以便传递其余字段给父类
        task_data = {k: v for k, v in data.items() 
                    if k not in ["relationship_intensity_threshold", "relationship_status_requirement"]}
        
        return cls(
            relationship_id=relationship_id,
            relationship_intensity_threshold=intensity_threshold,
            relationship_status_requirement=status_req,
            **task_data
        )
        
    def can_execute(self, relationship_manager: RelationshipManager) -> bool:
        """
        检查任务是否可以执行
        
        Args:
            relationship_manager: 关系管理器实例
            
        Returns:
            是否可以执行
        """
        # 检查关系是否存在
        relationship = relationship_manager.get_relationship(self.relationship_id)
        if not relationship:
            return False
            
        # 检查关系状态要求
        if (self.relationship_status_requirement and 
            relationship.status != self.relationship_status_requirement):
            return False
            
        # 检查关系强度要求
        if self.relationship_intensity_threshold > 0:
            intensity = relationship_manager.get_intensity(self.relationship_id)
            if not intensity:
                return False
                
            ris = intensity.calculate_ris()
            if ris < self.relationship_intensity_threshold:
                return False
                
        return True


class TaskManager:
    """任务管理器"""
    
    def __init__(self, relationship_manager: Optional[RelationshipManager] = None):
        """
        初始化任务管理器
        
        Args:
            relationship_manager: 关系管理器实例，如果为None则创建新实例
        """
        self.tasks: Dict[str, Task] = {}
        self.relationship_manager = relationship_manager or RelationshipManager()
        self.task_templates: Dict[str, Dict[str, Any]] = self._load_default_templates()
        
    def _load_default_templates(self) -> Dict[str, Dict[str, Any]]:
        """加载默认任务模板"""
        return {
            "daily_check_in": {
                "title": "每日问候",
                "description": "向用户发送每日问候，询问近况",
                "task_type": "interaction",
                "priority": 3,
                "relationship_intensity_threshold": 0.2,
                "relationship_status_requirement": RelationshipStatus.ACTIVE
            },
            "emotional_support": {
                "title": "情感支持",
                "description": "提供情感支持和鼓励",
                "task_type": "emotional",
                "priority": 4,
                "relationship_intensity_threshold": 0.4,
                "relationship_status_requirement": RelationshipStatus.ACTIVE
            },
            "relationship_revival": {
                "title": "关系唤醒",
                "description": "尝试重新激活沉寂的关系",
                "task_type": "revival",
                "priority": 2,
                "relationship_intensity_threshold": 0.0,
                "relationship_status_requirement": RelationshipStatus.SILENT
            },
            "deep_conversation": {
                "title": "深度对话",
                "description": "发起有深度的话题讨论",
                "task_type": "depth",
                "priority": 3,
                "relationship_intensity_threshold": 0.6,
                "relationship_status_requirement": RelationshipStatus.ACTIVE
            },
            "collaboration_project": {
                "title": "协作项目",
                "description": "邀请用户参与协作项目",
                "task_type": "collaboration",
                "priority": 4,
                "relationship_intensity_threshold": 0.7,
                "relationship_status_requirement": RelationshipStatus.ACTIVE
            },
            "cooling_prevention": {
                "title": "防止关系冷却",
                "description": "增加互动频率，防止关系冷却",
                "task_type": "prevention",
                "priority": 3,
                "relationship_intensity_threshold": 0.3,
                "relationship_status_requirement": RelationshipStatus.COOLING
            }
        }
        
    def add_task(self, task: Task) -> str:
        """
        添加任务
        
        Args:
            task: 任务实例
            
        Returns:
            任务ID
        """
        self.tasks[task.task_id] = task
        return task.task_id
        
    def create_task(self, **kwargs) -> str:
        """
        创建并添加任务
        
        Args:
            **kwargs: 任务参数
            
        Returns:
            任务ID
        """
        task = Task(**kwargs)
        return self.add_task(task)
        
    def create_relationship_task(self, **kwargs) -> str:
        """
        创建并添加关系任务
        
        Args:
            **kwargs: 关系任务参数
            
        Returns:
            任务ID
        """
        task = RelationshipTask(**kwargs)
        return self.add_task(task)
        
    def create_task_from_template(
        self, 
        template_name: str, 
        relationship_id: str,
        override_params: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        从模板创建任务
        
        Args:
            template_name: 模板名称
            relationship_id: 关系ID
            override_params: 覆盖模板的参数
            
        Returns:
            任务ID，如果模板不存在则返回None
        """
        if template_name not in self.task_templates:
            return None
            
        # 获取模板参数
        template = self.task_templates[template_name].copy()
        
        # 应用覆盖参数
        if override_params:
            template.update(override_params)
            
        # 添加关系ID
        template["relationship_id"] = relationship_id
        
        # 创建任务
        return self.create_relationship_task(**template)
        
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务实例，如果不存在则返回None
        """
        return self.tasks.get(task_id)
        
    def update_task(self, task_id: str, **kwargs) -> bool:
        """
        更新任务
        
        Args:
            task_id: 任务ID
            **kwargs: 要更新的字段
            
        Returns:
            是否更新成功
        """
        task = self.get_task(task_id)
        if not task:
            return False
            
        # 更新字段
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
                
        return True
        
    def delete_task(self, task_id: str) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否删除成功
        """
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False
        
    def complete_task(self, task_id: str) -> bool:
        """
        完成任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否操作成功
        """
        task = self.get_task(task_id)
        if not task:
            return False
            
        task.complete()
        return True
        
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        获取所有任务
        
        Returns:
            任务列表
        """
        return [task.to_dict() for task in self.tasks.values()]
        
    def get_tasks_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        按状态获取任务
        
        Args:
            status: 任务状态
            
        Returns:
            任务列表
        """
        return [task.to_dict() for task in self.tasks.values() if task.status == status]
        
    def get_tasks_by_relationship(self, relationship_id: str) -> List[Dict[str, Any]]:
        """
        按关系获取任务
        
        Args:
            relationship_id: 关系ID
            
        Returns:
            任务列表
        """
        return [task.to_dict() for task in self.tasks.values() if task.relationship_id == relationship_id]
        
    def get_tasks_by_entity(self, entity_id: str) -> List[Dict[str, Any]]:
        """
        按实体获取任务
        
        Args:
            entity_id: 实体ID
            
        Returns:
            任务列表
        """
        return [task.to_dict() for task in self.tasks.values() if task.related_entity_id == entity_id]
        
    def get_executable_tasks(self) -> List[Dict[str, Any]]:
        """
        获取可执行的任务
        
        Returns:
            可执行的任务列表
        """
        executable_tasks = []
        
        for task in self.tasks.values():
            # 只考虑未完成和未取消的任务
            if task.status in ["completed", "cancelled"]:
                continue
                
            # 检查是否为关系任务
            if isinstance(task, RelationshipTask):
                if task.can_execute(self.relationship_manager):
                    executable_tasks.append(task.to_dict())
            else:
                # 普通任务直接添加
                executable_tasks.append(task.to_dict())
                
        return executable_tasks
        
    def generate_tasks_for_relationship(self, relationship_id: str) -> List[str]:
        """
        为关系生成任务
        
        Args:
            relationship_id: 关系ID
            
        Returns:
            生成的任务ID列表
        """
        relationship = self.relationship_manager.get_relationship(relationship_id)
        if not relationship:
            return []
            
        intensity = self.relationship_manager.get_intensity(relationship_id)
        if not intensity:
            return []
            
        ris = intensity.calculate_ris()
        status = relationship.status
        
        # 根据关系状态和强度选择合适的任务模板
        task_ids = []
        
        if status == RelationshipStatus.ACTIVE:
            # 活跃关系的任务
            task_ids.append(self.create_task_from_template("daily_check_in", relationship_id))
            
            # 根据关系强度添加更深层次的任务
            if ris >= 0.4:
                task_ids.append(self.create_task_from_template("emotional_support", relationship_id))
                
            if ris >= 0.6:
                task_ids.append(self.create_task_from_template("deep_conversation", relationship_id))
                
            if ris >= 0.7:
                task_ids.append(self.create_task_from_template("collaboration_project", relationship_id))
                
        elif status == RelationshipStatus.COOLING:
            # 冷却关系的任务
            task_ids.append(self.create_task_from_template("cooling_prevention", relationship_id))
            
        elif status == RelationshipStatus.SILENT:
            # 沉寂关系的任务
            task_ids.append(self.create_task_from_template("relationship_revival", relationship_id))
            
        # 过滤None值（模板不存在的情况）
        return [task_id for task_id in task_ids if task_id]
        
    def save_to_file(self, filepath: str) -> None:
        """
        保存任务数据到文件
        
        Args:
            filepath: 文件路径
        """
        data = {
            "tasks": self.get_all_tasks(),
            "templates": self.task_templates
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    @classmethod
    def load_from_file(cls, filepath: str, relationship_manager: Optional[RelationshipManager] = None) -> 'TaskManager':
        """
        从文件加载任务数据
        
        Args:
            filepath: 文件路径
            relationship_manager: 关系管理器实例
            
        Returns:
            任务管理器实例
        """
        manager = cls(relationship_manager)
        
        if not os.path.exists(filepath):
            return manager
            
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 加载任务模板
        if "templates" in data:
            manager.task_templates = data["templates"]
            
        # 加载任务
        if "tasks" in data:
            for task_data in data["tasks"]:
                # 根据任务类型创建不同的任务实例
                if "relationship_intensity_threshold" in task_data:
                    task = RelationshipTask.from_dict(task_data)
                else:
                    task = Task.from_dict(task_data)
                    
                manager.add_task(task)
                
        return manager
