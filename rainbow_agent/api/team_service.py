"""
团队服务模块

提供团队协作的接口服务，处理与AgentTeam的交互。
"""
from typing import Dict, Any, List, Optional
import json

from ..collaboration.team import AgentTeam, create_expert_agent
from ..utils.logger import get_logger

# 获取日志记录器
logger = get_logger(__name__)

# 全局团队实例
_default_team = None


def get_default_team() -> AgentTeam:
    """
    获取默认团队实例（单例模式）
    
    Returns:
        AgentTeam实例
    """
    global _default_team
    
    if _default_team is None:
        # 创建默认团队
        _default_team = create_rainbow_team()
        logger.info("创建默认Rainbow团队")
    
    return _default_team


def create_rainbow_team() -> AgentTeam:
    """
    创建预配置的Rainbow团队
    
    Returns:
        配置好的AgentTeam实例
    """
    # 创建团队
    team = AgentTeam(name="Rainbow Team", max_output_size=10000)
    
    # 添加各领域专家
    experts = [
        ("通用知识专家", "通用知识、百科信息和事实核查", 
         "你擅长提供准确、全面的一般知识和事实信息。你熟悉各种主题的百科知识，并能清晰地解释复杂概念。"),
        
        ("技术专家", "计算机科学、编程、技术趋势和最佳实践", 
         "你是一位技术领域专家，精通各种编程语言、框架和技术栈。你能解释技术概念，提供代码示例，并讨论技术趋势和最佳实践。"),
        
        ("数学专家", "数学概念、公式和计算", 
         "你专精于数学分析和计算。你能解释复杂的数学概念，解决数学问题，并提供清晰的推导过程和解释。"),
        
        ("创意专家", "创意写作、内容创作和创新思维", 
         "你擅长创意思维和内容创作。你可以提供创意灵感、内容建议，以及创新的问题解决方法。"),
        
        ("批判思维专家", "逻辑分析、论证评估和批判性思考", 
         "你专长于批判性思维和逻辑分析。你能识别论证中的谬误，评估信息可靠性，并提供清晰、逻辑严密的分析。"),
        
        ("对话协调专家", "用户意图理解、对话管理和沟通优化", 
         "你负责理解用户意图，管理对话流程，确保团队的回应连贯、相关且满足用户需求。当用户问题简单时，你可以直接回应。")
    ]
    
    # 注册所有专家
    for name, expertise, prompt in experts:
        agent = create_expert_agent(name, expertise, prompt)
        team.add_agent(agent, skills=[expertise])
        logger.info(f"添加专家: {name} - {expertise}")
    
    return team


def process_query(query: str, system_prompt: Optional[str] = None,
                  max_tokens: Optional[int] = None) -> Dict[str, Any]:
    """
    处理用户查询，调用团队协作系统
    
    Args:
        query: 用户查询内容
        system_prompt: 可选的系统提示，覆盖默认设置
        max_tokens: 最大输出标记数
        
    Returns:
        处理结果，包含内容和团队贡献
    """
    try:
        # 获取默认团队
        team = get_default_team()
        
        # 处理特殊查询：能力介绍
        if query.strip().lower() in ["你会什么", "你能做什么", "你有什么功能"]:
            # 直接返回预设回答
            capabilities_result = {
                "content": (
                    "作为Rainbow AI团队，我拥有多位专业领域专家，可以帮助您完成以下任务：\n\n"
                    "✓ **回答知识问题**：提供准确的百科知识和事实信息\n"
                    "✓ **技术支持**：解释编程概念、技术问题和提供代码建议\n"
                    "✓ **数学计算**：解决数学问题和提供计算步骤\n"
                    "✓ **创意内容**：帮助构思创意、撰写文案和内容创作\n"
                    "✓ **逻辑分析**：提供批判性思维和逻辑推理支持\n"
                    "✓ **多角度分析**：从不同专业视角分析复杂问题\n\n"
                    "请直接向我提问，我会根据问题类型调动合适的专家为您提供专业解答！"
                ),
                "teamContributions": [
                    {
                        "expert": "对话协调专家",
                        "contribution": "提供Rainbow AI团队功能概述"
                    },
                    {
                        "expert": "通用知识专家",
                        "contribution": "整理系统能力清单"
                    }
                ]
            }
            return capabilities_result
        
        # 执行团队协作处理
        response = team.run(query=query, max_tokens=max_tokens)
        
        # 解析结果
        if isinstance(response, dict) and "task" in response:
            task_data = response["task"]
            # 提取任务结果
            if "result" in task_data and task_data["result"]:
                result = task_data["result"]
                
                # 构建标准响应格式
                formatted_response = {
                    "content": result.get("final_result", "抱歉，处理您的请求时出现问题"),
                    "teamContributions": []
                }
                
                # 添加团队贡献
                for contribution in result.get("team_contributions", []):
                    formatted_response["teamContributions"].append({
                        "expert": contribution.get("agent_name", "未知专家"),
                        "contribution": contribution.get("contribution", "提供了专业支持")
                    })
                
                return formatted_response
        
        # 默认响应（如果处理失败）
        return {
            "content": "抱歉，我无法正确处理您的请求。请尝试重新表述您的问题。",
            "teamContributions": [
                {
                    "expert": "对话协调专家",
                    "contribution": "尝试恢复对话流程"
                }
            ]
        }
    
    except Exception as e:
        logger.error(f"处理团队查询时出错: {e}")
        # 返回错误响应
        return {
            "content": f"处理您的请求时遇到了问题: {str(e)}",
            "teamContributions": [
                {
                    "expert": "系统监控",
                    "contribution": "识别并报告处理错误"
                }
            ]
        }
