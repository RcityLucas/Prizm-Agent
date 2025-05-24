"""
团队构建器

提供预定义的代理团队模板和构建功能
"""
from typing import List, Dict, Any, Optional
import os

from ..agent import RainbowAgent
from .team_manager import TeamManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TeamBuilder:
    """
    团队构建器
    
    创建预定义的代理团队配置
    """
    
    @staticmethod
    def create_general_team(team_name: str, model: str = "gpt-3.5-turbo") -> TeamManager:
        """
        创建通用任务处理团队
        
        Args:
            team_name: 团队名称
            model: 使用的模型名称
            
        Returns:
            配置好的TeamManager实例
        """
        # 创建协调者
        coordinator = RainbowAgent(
            name="团队协调者",
            system_prompt="""你是一个专业的团队协调者，负责分解任务、分配工作和整合结果。
你擅长理解复杂问题，并将其分解为可管理的部分。
作为协调者，你需要确保团队成员协作顺畅，并产生高质量的综合结果。""",
            model=model
        )
        
        # 创建团队管理器
        team_manager = TeamManager(team_name=team_name, coordinator=coordinator)
        
        # 添加核心代理
        researcher = RainbowAgent(
            name="研究专家",
            system_prompt="""你是一个专业的研究专家，擅长分析信息、收集数据和提供深入见解。
你的优势在于全面理解复杂主题，发现模式和关联，并提供基于证据的结论。
在团队中，你负责深入研究任务相关的背景信息和事实。""",
            model=model
        )
        team_manager.add_agent(researcher, skills=["研究", "分析", "信息收集", "批判性思维"])
        
        writer = RainbowAgent(
            name="内容创作者",
            system_prompt="""你是一个专业的内容创作者，擅长撰写清晰、连贯和引人入胜的文本。
你的优势在于将复杂概念转化为易于理解的内容，适应不同风格和受众需求。
在团队中，你负责生成高质量的文字内容，包括报告、文案和创意写作。""",
            model=model
        )
        team_manager.add_agent(writer, skills=["写作", "编辑", "内容创作", "沟通"])
        
        problem_solver = RainbowAgent(
            name="问题解决者",
            system_prompt="""你是一个专业的问题解决者，擅长分析复杂问题并找出创新解决方案。
你的优势在于逻辑思维、创新思考和实用主义方法。
在团队中，你负责处理挑战性问题，提出解决方案和优化现有流程。""",
            model=model
        )
        team_manager.add_agent(problem_solver, skills=["问题解决", "创新", "逻辑分析", "策略思维"])
        
        return team_manager

    @staticmethod
    def create_development_team(team_name: str, model: str = "gpt-3.5-turbo") -> TeamManager:
        """
        创建软件开发团队
        
        Args:
            team_name: 团队名称
            model: 使用的模型名称
            
        Returns:
            配置好的TeamManager实例
        """
        # 创建协调者
        coordinator = RainbowAgent(
            name="项目经理",
            system_prompt="""你是一个专业的软件项目经理，负责协调开发流程和团队协作。
你擅长理解技术需求，分解任务，并确保团队成员高效协作。
作为项目经理，你需要平衡技术质量、时间限制和资源约束。""",
            model=model
        )
        
        # 创建团队管理器
        team_manager = TeamManager(team_name=team_name, coordinator=coordinator)
        
        # 添加核心代理
        architect = RainbowAgent(
            name="软件架构师",
            system_prompt="""你是一个专业的软件架构师，擅长设计可扩展、高性能的系统架构。
你的优势在于理解系统整体结构，做出关键技术决策，并确保代码质量和可维护性。
在团队中，你负责制定技术方案，解决架构级问题，并指导开发实践。""",
            model=model
        )
        team_manager.add_agent(architect, skills=["系统设计", "架构", "技术规划", "性能优化"])
        
        backend_dev = RainbowAgent(
            name="后端开发者",
            system_prompt="""你是一个专业的后端开发者，擅长构建服务器端应用程序和APIs。
你的优势在于数据处理、业务逻辑实现和服务器性能优化。
在团队中，你负责开发和维护后端系统，确保数据安全和系统稳定性。""",
            model=model
        )
        team_manager.add_agent(backend_dev, skills=["后端开发", "数据库", "API设计", "服务器管理"])
        
        frontend_dev = RainbowAgent(
            name="前端开发者",
            system_prompt="""你是一个专业的前端开发者，擅长创建响应式、用户友好的界面。
你的优势在于用户体验设计、交互实现和前端性能优化。
在团队中，你负责开发网页和应用界面，确保良好的用户体验和视觉效果。""",
            model=model
        )
        team_manager.add_agent(frontend_dev, skills=["前端开发", "UI实现", "用户体验", "响应式设计"])
        
        qa_engineer = RainbowAgent(
            name="测试工程师",
            system_prompt="""你是一个专业的软件测试工程师，擅长发现和报告软件缺陷。
你的优势在于系统性测试方法、质量保证流程和自动化测试。
在团队中，你负责验证软件功能，发现潜在问题，并确保产品质量。""",
            model=model
        )
        team_manager.add_agent(qa_engineer, skills=["软件测试", "质量保证", "自动化测试", "Bug追踪"])
        
        return team_manager

    @staticmethod
    def create_data_analysis_team(team_name: str, model: str = "gpt-3.5-turbo") -> TeamManager:
        """
        创建数据分析团队
        
        Args:
            team_name: 团队名称
            model: 使用的模型名称
            
        Returns:
            配置好的TeamManager实例
        """
        # 创建协调者
        coordinator = RainbowAgent(
            name="数据项目协调者",
            system_prompt="""你是一个专业的数据项目协调者，负责管理数据分析流程和团队协作。
你擅长理解数据需求，分配分析任务，并确保高质量的数据洞察。
作为协调者，你需要平衡分析深度、时间限制和业务需求。""",
            model=model
        )
        
        # 创建团队管理器
        team_manager = TeamManager(team_name=team_name, coordinator=coordinator)
        
        # 添加核心代理
        data_scientist = RainbowAgent(
            name="数据科学家",
            system_prompt="""你是一个专业的数据科学家，擅长应用高级分析和机器学习技术解决复杂问题。
你的优势在于模型构建、预测分析和实验设计。
在团队中，你负责开发高级分析方法，构建预测模型，并提供数据驱动的解决方案。""",
            model=model
        )
        team_manager.add_agent(data_scientist, skills=["机器学习", "统计分析", "预测建模", "实验设计"])
        
        data_analyst = RainbowAgent(
            name="数据分析师",
            system_prompt="""你是一个专业的数据分析师，擅长处理和分析数据以提取有价值的见解。
你的优势在于数据探索、描述性统计和业务分析。
在团队中，你负责进行数据探索，识别趋势和模式，并创建数据可视化。""",
            model=model
        )
        team_manager.add_agent(data_analyst, skills=["数据分析", "数据可视化", "商业智能", "报表创建"])
        
        data_engineer = RainbowAgent(
            name="数据工程师",
            system_prompt="""你是一个专业的数据工程师，擅长构建和维护数据管道和存储系统。
你的优势在于数据集成、ETL流程和数据架构设计。
在团队中，你负责确保数据可靠性、可访问性和一致性。""",
            model=model
        )
        team_manager.add_agent(data_engineer, skills=["数据工程", "ETL开发", "数据架构", "数据质量"])
        
        domain_expert = RainbowAgent(
            name="领域专家",
            system_prompt="""你是一个专业的领域专家，具备特定业务领域的深入知识和经验。
你的优势在于理解业务上下文，提出相关问题，并解释分析结果的实际意义。
在团队中，你负责提供业务背景，引导分析方向，并验证结果的实用性。""",
            model=model
        )
        team_manager.add_agent(domain_expert, skills=["业务分析", "领域知识", "问题定义", "结果解读"])
        
        return team_manager

    @staticmethod
    def create_custom_team(
        team_name: str,
        coordinator_name: str,
        coordinator_prompt: str,
        agents_config: List[Dict[str, Any]],
        model: str = "gpt-3.5-turbo"
    ) -> TeamManager:
        """
        创建自定义代理团队
        
        Args:
            team_name: 团队名称
            coordinator_name: 协调者名称
            coordinator_prompt: 协调者系统提示
            agents_config: 代理配置列表，每个包含name, prompt和skills
            model: 使用的模型名称
            
        Returns:
            配置好的TeamManager实例
        """
        # 创建协调者
        coordinator = RainbowAgent(
            name=coordinator_name,
            system_prompt=coordinator_prompt,
            model=model
        )
        
        # 创建团队管理器
        team_manager = TeamManager(team_name=team_name, coordinator=coordinator)
        
        # 添加自定义代理
        for config in agents_config:
            agent = RainbowAgent(
                name=config["name"],
                system_prompt=config["prompt"],
                model=model
            )
            team_manager.add_agent(agent, skills=config["skills"])
        
        return team_manager
