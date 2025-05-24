"""
团队管理器

协调团队中的代理，管理任务分配和协作流程
"""
from typing import List, Dict, Any, Optional, Tuple
import uuid
import time

from ..agent import RainbowAgent
from .task_decomposer import TaskDecomposer
from .messaging import MessageBus, Message, MessageType
from .result_aggregator import ResultAggregator, ConsensusBuilder
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TeamManager:
    """
    团队管理器
    
    管理代理团队的协作流程，包括任务分解、分配和结果聚合
    """
    
    def __init__(self, team_name: str, coordinator: RainbowAgent):
        """
        初始化团队管理器
        
        Args:
            team_name: 团队名称
            coordinator: 协调者代理
        """
        self.team_name = team_name
        self.coordinator = coordinator
        self.agents: Dict[str, Dict[str, Any]] = {}  # agent_id -> agent信息
        self.message_bus = MessageBus()
        self.task_decomposer = TaskDecomposer(coordinator)
        self.result_aggregator = ResultAggregator(coordinator)
        self.consensus_builder = ConsensusBuilder(coordinator)
    
    def add_agent(self, agent: RainbowAgent, skills: List[str], agent_id: Optional[str] = None) -> str:
        """
        添加代理到团队
        
        Args:
            agent: 代理实例
            skills: 代理的技能列表
            agent_id: 可选的代理ID，如不提供则自动生成
            
        Returns:
            代理ID
        """
        # 生成或使用提供的代理ID
        agent_id = agent_id or str(uuid.uuid4())
        
        # 注册代理信息
        self.agents[agent_id] = {
            "agent": agent,
            "name": agent.name,
            "skills": skills,
            "last_active": time.time()
        }
        
        # 订阅消息
        self.message_bus.subscribe(agent_id, [
            MessageType.TASK_ASSIGNMENT,
            MessageType.QUERY,
            MessageType.FEEDBACK,
            MessageType.SYSTEM
        ])
        
        logger.info(f"代理 '{agent.name}' (ID: {agent_id}) 已添加到团队 '{self.team_name}'")
        
        # 发送欢迎消息
        welcome_msg = Message(
            content=f"欢迎加入团队 '{self.team_name}'",
            msg_type=MessageType.SYSTEM,
            sender_id="system",
            recipient_id=agent_id
        )
        self.message_bus.publish(welcome_msg)
        
        return agent_id
    
    def remove_agent(self, agent_id: str) -> bool:
        """
        从团队中移除代理
        
        Args:
            agent_id: 要移除的代理ID
            
        Returns:
            是否成功移除
        """
        if agent_id in self.agents:
            agent_name = self.agents[agent_id]["name"]
            del self.agents[agent_id]
            
            # 取消消息订阅
            self.message_bus.unsubscribe(agent_id)
            
            logger.info(f"代理 '{agent_name}' (ID: {agent_id}) 已从团队 '{self.team_name}' 移除")
            return True
        else:
            logger.warning(f"无法移除代理: ID {agent_id} 不存在")
            return False
    
    def find_suitable_agents(self, required_skills: List[str], count: int = 1) -> List[str]:
        """
        查找适合的代理
        
        Args:
            required_skills: 所需技能列表
            count: 需要的代理数量
            
        Returns:
            最适合的代理ID列表
        """
        # 计算每个代理的技能匹配度
        matches = []
        for agent_id, agent_info in self.agents.items():
            agent_skills = set(agent_info["skills"])
            required = set(required_skills)
            
            # 计算匹配度 (0-1之间)
            if not required:  # 如果没有明确要求技能
                match_score = 1.0
            else:
                # 计算交集大小与所需技能数量的比值
                match_score = len(agent_skills.intersection(required)) / len(required)
            
            matches.append((agent_id, match_score))
        
        # 按匹配度排序
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # 返回最匹配的前N个代理ID
        return [agent_id for agent_id, _ in matches[:count]]
    
    def execute_task(self, 
                     task_description: str, 
                     decompose: bool = True,
                     context: Optional[Dict[str, Any]] = None,
                     max_output_size: Optional[int] = None) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            task_description: 任务描述
            decompose: 是否分解任务
            context: 任务上下文
            max_output_size: 最大输出大小（字符数）
            
        Returns:
            任务执行结果
        """
        task_id = str(uuid.uuid4())
        start_time = time.time()
        
        # 记录任务
        logger.info(f"任务 {task_id}: {task_description[:50]}...")
        
        # 1. 如果不需要分解，直接使用协调者执行
        if not decompose:
            logger.info(f"任务 {task_id} 不分解，直接执行")
            result = self.coordinator.run(task_description)
            
            execution_time = time.time() - start_time
            logger.info(f"任务 {task_id} 完成，耗时 {execution_time:.2f}秒")
            
            return {
                "task_id": task_id,
                "description": task_description,
                "decomposed": False,
                "result": {
                    "final_result": result,
                    "team_contributions": [
                        {
                            "agent_name": self.coordinator.name,
                            "contribution": "执行了整个任务"
                        }
                    ]
                },
                "execution_time": execution_time
            }
        
        # 2. 任务分解
        logger.info(f"任务 {task_id} 开始分解")
        subtasks = self.task_decomposer.decompose(task_description, context)
        
        if not subtasks:
            # 分解失败，退回到单一执行
            logger.warning(f"任务 {task_id} 分解失败，退回到单一执行")
            return self.execute_task(task_description, decompose=False, context=context)
        
        logger.info(f"任务 {task_id} 已分解为 {len(subtasks)} 个子任务")
        
        # 3. 执行子任务
        subtask_results = []
        
        for i, subtask in enumerate(subtasks):
            subtask_desc = subtask["description"]
            subtask_skills = subtask["skills"]
            
            # 查找适合的代理
            suitable_agents = self.find_suitable_agents(subtask_skills)
            
            if not suitable_agents:
                logger.warning(f"子任务 {i+1} 未找到合适的代理，使用协调者")
                agent = self.coordinator
                agent_id = "coordinator"
            else:
                agent_id = suitable_agents[0]
                agent = self.agents[agent_id]["agent"]
            
            # 创建并发布任务分配消息
            task_msg = Message(
                content=subtask_desc,
                msg_type=MessageType.TASK_ASSIGNMENT,
                sender_id="system",
                recipient_id=agent_id,
                related_task_id=task_id,
                metadata={"subtask_index": i}
            )
            self.message_bus.publish(task_msg)
            
            # 执行子任务
            logger.info(f"子任务 {i+1} 由代理 '{agent.name}' 执行")
            subtask_result = agent.run(subtask_desc)
            
            # 记录和发布结果
            result_msg = Message(
                content="子任务完成",
                msg_type=MessageType.TASK_RESULT,
                sender_id=agent_id,
                recipient_id="system",
                related_task_id=task_id,
                metadata={"result": subtask_result, "subtask_index": i}
            )
            self.message_bus.publish(result_msg)
            
            # 添加到结果列表
            subtask_results.append({
                "task_description": subtask_desc,
                "agent_id": agent_id,
                "agent_name": agent.name,
                "result": subtask_result
            })
        
        # 4. 聚合结果
        logger.info(f"任务 {task_id} 开始聚合结果")
        aggregated_result = self.result_aggregator.aggregate(
            main_task_description=task_description,
            subtask_results=subtask_results,
            max_output_size=max_output_size
        )
        
        execution_time = time.time() - start_time
        logger.info(f"任务 {task_id} 完成，耗时 {execution_time:.2f}秒")
        
        # 5. 返回结果
        return {
            "task_id": task_id,
            "description": task_description,
            "decomposed": True,
            "subtasks": subtasks,
            "subtask_results": subtask_results,
            "result": aggregated_result,
            "execution_time": execution_time
        }
    
    def build_team_consensus(self, question: str) -> Dict[str, Any]:
        """
        构建团队共识
        
        让所有代理对同一问题回答，然后构建共识
        
        Args:
            question: 需要达成共识的问题
            
        Returns:
            共识结果
        """
        logger.info(f"开始构建团队共识: {question[:50]}...")
        
        # 收集各代理的回应
        agent_responses = []
        
        for agent_id, agent_info in self.agents.items():
            agent = agent_info["agent"]
            
            # 让代理回答问题
            logger.info(f"向代理 '{agent.name}' 询问")
            response = agent.run(question)
            
            # 添加到回应列表
            agent_responses.append({
                "agent_id": agent_id,
                "agent_name": agent.name,
                "response": response,
                "confidence": "中"  # 默认置信度
            })
        
        # 构建共识
        logger.info(f"收集了 {len(agent_responses)} 个代理的回应，开始构建共识")
        consensus = self.consensus_builder.build_consensus(
            question=question,
            agent_responses=agent_responses
        )
        
        return {
            "question": question,
            "agent_responses": agent_responses,
            "consensus": consensus
        }
    
    def get_team_stats(self) -> Dict[str, Any]:
        """
        获取团队统计信息
        
        Returns:
            团队统计数据
        """
        # 统计技能分布
        skills_count = {}
        for agent_info in self.agents.values():
            for skill in agent_info["skills"]:
                skills_count[skill] = skills_count.get(skill, 0) + 1
        
        return {
            "team_name": self.team_name,
            "agent_count": len(self.agents),
            "skills_distribution": skills_count,
            "message_count": len(self.message_bus.messages)
        }
