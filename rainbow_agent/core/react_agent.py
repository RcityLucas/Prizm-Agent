"""
ReAct代理 - 实现Reasoning + Acting模式

提供更强大的代理能力，支持思考、行动、观察的循环，以及多步规划。
借鉴LangChain和Agno的设计理念，增强代理的推理和决策能力。
"""
from typing import Dict, Any, List, Tuple, Optional, Union, Callable
import json
import re
import time
from enum import Enum

from ..tools.tool_invoker import ToolInvoker
from ..tools.base import BaseTool
from ..utils.llm import get_llm_client
from ..utils.logger import get_logger

logger = get_logger(__name__)

class AgentState(Enum):
    """代理状态枚举"""
    IDLE = "idle"                 # 空闲状态
    THINKING = "thinking"         # 思考状态
    ACTING = "acting"             # 行动状态
    OBSERVING = "observing"       # 观察状态
    PLANNING = "planning"         # 规划状态
    EXECUTING = "executing"       # 执行状态
    FINISHED = "finished"         # 完成状态
    ERROR = "error"               # 错误状态

class AgentAction:
    """代理行动类，表示代理的一个行动"""
    
    def __init__(self, tool_name: str, tool_args: Any, thought: str = ""):
        """
        初始化代理行动
        
        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            thought: 行动前的思考过程
        """
        self.tool_name = tool_name
        self.tool_args = tool_args
        self.thought = thought
        self.result = None
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "thought": self.thought,
            "result": self.result,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentAction':
        """从字典创建行动对象"""
        action = cls(
            tool_name=data["tool_name"],
            tool_args=data["tool_args"],
            thought=data.get("thought", "")
        )
        action.result = data.get("result")
        action.timestamp = data.get("timestamp", time.time())
        return action

class AgentPlan:
    """代理计划类，表示代理的一个多步计划"""
    
    def __init__(self, goal: str, steps: List[str] = None):
        """
        初始化代理计划
        
        Args:
            goal: 计划目标
            steps: 计划步骤列表
        """
        self.goal = goal
        self.steps = steps or []
        self.current_step_index = 0
        self.completed_steps = []
        self.timestamp = time.time()
    
    def add_step(self, step: str) -> None:
        """添加计划步骤"""
        self.steps.append(step)
    
    def get_current_step(self) -> Optional[str]:
        """获取当前步骤"""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
    
    def advance_step(self) -> bool:
        """前进到下一步骤，返回是否还有下一步"""
        if self.current_step_index < len(self.steps):
            self.completed_steps.append(self.steps[self.current_step_index])
            self.current_step_index += 1
            return self.current_step_index < len(self.steps)
        return False
    
    def is_completed(self) -> bool:
        """检查计划是否已完成"""
        return self.current_step_index >= len(self.steps)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "goal": self.goal,
            "steps": self.steps,
            "current_step_index": self.current_step_index,
            "completed_steps": self.completed_steps,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentPlan':
        """从字典创建计划对象"""
        plan = cls(
            goal=data["goal"],
            steps=data.get("steps", [])
        )
        plan.current_step_index = data.get("current_step_index", 0)
        plan.completed_steps = data.get("completed_steps", [])
        plan.timestamp = data.get("timestamp", time.time())
        return plan

class ReActAgent:
    """
    ReAct代理，实现Reasoning + Acting模式
    
    提供思考、行动、观察的循环，以及多步规划能力
    """
    
    def __init__(
        self,
        tool_invoker: ToolInvoker = None,
        llm_client = None,
        agent_model: str = "gpt-4",
        planning_model: str = "gpt-4",
        max_iterations: int = 10,
        verbose: bool = False
    ):
        """
        初始化ReAct代理
        
        Args:
            tool_invoker: 工具调用器
            llm_client: LLM客户端
            agent_model: 代理使用的模型
            planning_model: 规划使用的模型
            max_iterations: 最大迭代次数
            verbose: 是否输出详细日志
        """
        self.tool_invoker = tool_invoker or ToolInvoker()
        self.llm_client = llm_client or get_llm_client()
        self.agent_model = agent_model
        self.planning_model = planning_model
        self.max_iterations = max_iterations
        self.verbose = verbose
        
        self.state = AgentState.IDLE
        self.actions = []
        self.current_plan = None
        
        logger.info("ReActAgent初始化完成")
    
    def run(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        运行代理处理查询
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            处理结果
        """
        context = context or {}
        self.state = AgentState.THINKING
        self.actions = []
        
        # 判断是否需要规划
        if self._needs_planning(query):
            logger.info("查询需要多步规划")
            return self._run_with_planning(query, context)
        else:
            logger.info("查询使用ReAct模式处理")
            return self._run_react(query, context)
    
    def _needs_planning(self, query: str) -> bool:
        """
        判断查询是否需要多步规划
        
        Args:
            query: 用户查询
            
        Returns:
            是否需要规划
        """
        # 使用简单启发式规则判断
        complex_indicators = [
            "分步", "步骤", "依次", "首先", "然后", "接着", "最后",
            "step by step", "multiple steps", "sequence", "first", "then", "finally",
            "计划", "规划", "流程", "过程",
            "plan", "process", "workflow", "procedure"
        ]
        
        # 检查查询中是否包含复杂任务指示词
        for indicator in complex_indicators:
            if indicator in query.lower():
                return True
        
        # 检查查询长度，较长的查询可能需要规划
        if len(query) > 100:
            return True
            
        return False
    
    def _run_react(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用ReAct模式运行代理
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            处理结果
        """
        iteration = 0
        final_answer = None
        
        # 初始化思考-行动-观察循环
        while iteration < self.max_iterations and self.state != AgentState.FINISHED:
            iteration += 1
            logger.info(f"ReAct迭代 {iteration}/{self.max_iterations}")
            
            if self.state == AgentState.THINKING:
                # 思考阶段：决定下一步行动
                action = self._think(query, context, self.actions)
                
                if action.tool_name.lower() == "final_answer":
                    # 如果决定给出最终答案，结束循环
                    final_answer = action.tool_args
                    self.state = AgentState.FINISHED
                    logger.info("ReAct代理决定给出最终答案")
                else:
                    # 否则执行工具调用
                    self.actions.append(action)
                    self.state = AgentState.ACTING
            
            elif self.state == AgentState.ACTING:
                # 行动阶段：执行工具调用
                if not self.actions:
                    self.state = AgentState.THINKING
                    continue
                    
                current_action = self.actions[-1]
                logger.info(f"执行工具: {current_action.tool_name}")
                
                try:
                    result = self.tool_invoker.invoke_tool({
                        "tool_name": current_action.tool_name,
                        "tool_args": current_action.tool_args
                    })
                    current_action.result = result
                    self.state = AgentState.OBSERVING
                except Exception as e:
                    logger.error(f"工具执行错误: {e}")
                    current_action.result = f"错误: {str(e)}"
                    self.state = AgentState.OBSERVING
            
            elif self.state == AgentState.OBSERVING:
                # 观察阶段：分析工具执行结果，决定下一步
                self.state = AgentState.THINKING
        
        # 如果达到最大迭代次数但没有最终答案，生成一个
        if not final_answer:
            final_answer = self._generate_final_answer(query, context, self.actions)
            
        return {
            "answer": final_answer,
            "actions": [action.to_dict() for action in self.actions],
            "iterations": iteration
        }
    
    def _run_with_planning(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用多步规划运行代理
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            处理结果
        """
        # 生成计划
        self.state = AgentState.PLANNING
        plan = self._create_plan(query, context)
        self.current_plan = plan
        
        logger.info(f"生成计划: {plan.goal}")
        for i, step in enumerate(plan.steps):
            logger.info(f"步骤 {i+1}: {step}")
        
        # 执行计划
        self.state = AgentState.EXECUTING
        step_results = []
        
        while not plan.is_completed() and len(step_results) < self.max_iterations:
            current_step = plan.get_current_step()
            logger.info(f"执行计划步骤: {current_step}")
            
            # 将当前步骤作为查询执行ReAct循环
            step_context = {
                **context,
                "plan": plan.to_dict(),
                "previous_results": step_results
            }
            
            step_result = self._run_react(current_step, step_context)
            step_results.append({
                "step": current_step,
                "result": step_result
            })
            
            # 前进到下一步
            plan.advance_step()
        
        # 生成最终答案
        final_answer = self._synthesize_plan_results(query, plan, step_results)
        
        return {
            "answer": final_answer,
            "plan": plan.to_dict(),
            "step_results": step_results
        }
    
    def _think(self, query: str, context: Dict[str, Any], actions: List[AgentAction]) -> AgentAction:
        """
        思考阶段：决定下一步行动
        
        Args:
            query: 用户查询
            context: 上下文信息
            actions: 已执行的行动列表
            
        Returns:
            下一步行动
        """
        # 构建提示词
        tools_description = self.tool_invoker._format_tools_description()
        
        # 构建行动历史
        action_history = ""
        for i, action in enumerate(actions):
            action_history += f"\n思考 {i+1}: {action.thought}\n"
            action_history += f"行动 {i+1}: {action.tool_name}({action.tool_args})\n"
            action_history += f"观察 {i+1}: {action.result}\n"
        
        prompt = f"""
        你是一个能够思考和行动的AI助手，使用ReAct（思考-行动-观察）方法解决问题。
        
        用户查询: {query}
        
        可用工具:
        {tools_description}
        
        特殊工具:
        - final_answer: 当你已经有了问题的答案，使用这个工具给出最终回答
          用法: final_answer(你的最终回答)
        
        历史行动:
        {action_history}
        
        请按照以下格式思考并决定下一步行动:
        
        思考: 分析当前情况，考虑需要什么信息，以及如何获取这些信息
        行动: 选择一个工具并提供参数，格式为 工具名(参数)
        
        如果你已经有了问题的答案，使用 final_answer 工具:
        行动: final_answer(你的最终回答)
        
        只输出思考和行动部分，不要输出其他内容。
        """
        
        # 调用LLM
        response = self.llm_client.chat.completions.create(
            model=self.agent_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        content = response.choices[0].message.content
        
        # 解析思考和行动
        thought_match = re.search(r'思考:(.*?)行动:', content, re.DOTALL)
        action_match = re.search(r'行动:(.*?)($|思考:)', content, re.DOTALL)
        
        thought = thought_match.group(1).strip() if thought_match else ""
        action_text = action_match.group(1).strip() if action_match else ""
        
        # 解析工具调用
        tool_match = re.search(r'(\w+)\((.*)\)', action_text, re.DOTALL)
        
        if tool_match:
            tool_name = tool_match.group(1).strip()
            tool_args = tool_match.group(2).strip()
        else:
            # 如果无法解析，默认为final_answer
            tool_name = "final_answer"
            tool_args = action_text
        
        return AgentAction(tool_name, tool_args, thought)
    
    def _generate_final_answer(self, query: str, context: Dict[str, Any], actions: List[AgentAction]) -> str:
        """
        生成最终答案
        
        Args:
            query: 用户查询
            context: 上下文信息
            actions: 已执行的行动列表
            
        Returns:
            最终答案
        """
        # 构建行动历史
        action_history = ""
        for i, action in enumerate(actions):
            action_history += f"\n思考 {i+1}: {action.thought}\n"
            action_history += f"行动 {i+1}: {action.tool_name}({action.tool_args})\n"
            action_history += f"观察 {i+1}: {action.result}\n"
        
        prompt = f"""
        你是一个能够思考和行动的AI助手，现在需要基于已执行的行动生成最终答案。
        
        用户查询: {query}
        
        行动历史:
        {action_history}
        
        请基于以上信息，生成一个全面、准确的最终答案。答案应该直接回答用户的查询，
        并整合从工具调用中获得的所有相关信息。
        """
        
        # 调用LLM
        response = self.llm_client.chat.completions.create(
            model=self.agent_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        return response.choices[0].message.content.strip()
    
    def _create_plan(self, query: str, context: Dict[str, Any]) -> AgentPlan:
        """
        创建多步计划
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            代理计划
        """
        # 构建工具描述
        tools_description = self.tool_invoker._format_tools_description()
        
        prompt = f"""
        你是一个AI规划专家，需要为复杂任务创建一个详细的步骤计划。
        
        用户查询: {query}
        
        可用工具:
        {tools_description}
        
        请创建一个分步计划来解决这个查询。计划应该:
        1. 将复杂任务分解为简单、可执行的步骤
        2. 确保步骤是线性的，每一步都建立在前一步的基础上
        3. 考虑可能的依赖关系和前提条件
        4. 使每一步都足够具体，能够独立执行
        
        请按以下格式输出:
        
        目标: [总体目标]
        
        步骤:
        1. [第一步]
        2. [第二步]
        3. [第三步]
        ...
        
        只输出目标和步骤，不要包含其他内容。
        """
        
        # 调用LLM
        response = self.llm_client.chat.completions.create(
            model=self.planning_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        content = response.choices[0].message.content
        
        # 解析目标和步骤
        goal_match = re.search(r'目标:(.*?)步骤:', content, re.DOTALL)
        steps_match = re.findall(r'\d+\.\s+(.*?)(?=\d+\.|$)', content, re.DOTALL)
        
        goal = goal_match.group(1).strip() if goal_match else query
        steps = [step.strip() for step in steps_match if step.strip()]
        
        # 如果没有解析出步骤，尝试其他格式
        if not steps:
            steps_match = re.findall(r'步骤\s+\d+:(.*?)(?=步骤\s+\d+:|$)', content, re.DOTALL)
            steps = [step.strip() for step in steps_match if step.strip()]
        
        # 如果仍然没有步骤，使用整个内容作为单个步骤
        if not steps:
            steps = [query]
        
        return AgentPlan(goal, steps)
    
    def _synthesize_plan_results(self, query: str, plan: AgentPlan, step_results: List[Dict[str, Any]]) -> str:
        """
        综合计划执行结果生成最终答案
        
        Args:
            query: 用户查询
            plan: 执行的计划
            step_results: 每个步骤的执行结果
            
        Returns:
            最终答案
        """
        # 构建步骤结果
        steps_summary = ""
        for i, result in enumerate(step_results):
            steps_summary += f"\n步骤 {i+1}: {result['step']}\n"
            steps_summary += f"结果: {result['result']['answer']}\n"
        
        prompt = f"""
        你是一个AI综合专家，需要基于多步计划的执行结果生成最终答案。
        
        用户查询: {query}
        
        计划目标: {plan.goal}
        
        步骤执行结果:
        {steps_summary}
        
        请综合所有步骤的执行结果，生成一个全面、连贯的最终答案。答案应该:
        1. 直接回答用户的查询
        2. 整合所有步骤的关键信息
        3. 保持逻辑连贯性
        4. 避免重复信息
        
        最终答案:
        """
        
        # 调用LLM
        response = self.llm_client.chat.completions.create(
            model=self.agent_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        return response.choices[0].message.content.strip()
