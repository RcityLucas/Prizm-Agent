"""
Rainbow Agent 关系网络模块

提供AI与人类/AI之间关系的管理、分析和演化功能
"""
from .models import (
    RelationshipManager, 
    RelationshipGraph, 
    RelationshipIntensity,
    RelationshipStatus
)
from .tools import RelationshipTool, RelationshipAnalysisTool
from .tasks import TaskManager, Task, RelationshipTask
from .agent_team import EnhancedAgentTeam, AgentProfile, AgentTask
from .utils import (
    calculate_relationship_stats,
    get_relationship_trend,
    find_similar_relationships,
    generate_relationship_report
)
from .integration import RelationshipSystem, get_relationship_system

# 导出默认关系系统实例
default_system = get_relationship_system()

__all__ = [
    'RelationshipManager',
    'RelationshipGraph',
    'RelationshipIntensity',
    'RelationshipStatus',
    'RelationshipTool',
    'RelationshipAnalysisTool',
    'TaskManager',
    'Task',
    'RelationshipTask',
    'EnhancedAgentTeam',
    'AgentProfile',
    'AgentTask',
    'RelationshipSystem',
    'get_relationship_system',
    'default_system',
    'calculate_relationship_stats',
    'get_relationship_trend',
    'find_similar_relationships',
    'generate_relationship_report'
]
