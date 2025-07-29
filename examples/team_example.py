"""
代理团队协作示例应用

该示例展示了如何创建和使用多代理协作系统来解决复杂问题。
"""
import os
import sys
import json
from dotenv import load_dotenv

# 确保可以导入rainbow_agent模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rainbow_agent.agent import RainbowAgent
from rainbow_agent.collaboration.team import AgentTeam, create_expert_agent
from rainbow_agent.memory.memory import SimpleMemory
from rainbow_agent.tools.web_tools import WebSearchTool, WeatherTool
from rainbow_agent.tools.file_tools import FileReadTool, FileWriteTool
from rainbow_agent.config.settings import get_settings
from rainbow_agent.utils.logger import get_logger

# 加载环境变量
load_dotenv()

logger = get_logger(__name__)


def create_agent_team() -> AgentTeam:
    """
    创建一个专家代理团队
    
    Returns:
        配置好的AgentTeam实例
    """
    # 创建团队
    team = AgentTeam(name="专家顾问团")
    
    # 创建并添加专家代理
    
    # 1. 技术专家
    tech_expert = create_expert_agent(
        name="技术专家",
        expertise="软件开发、编程语言、系统架构设计",
        system_prompt="""你是技术专家，精通软件开发、编程语言和系统架构设计。
        
你擅长：
- 编写高质量代码和提供技术解决方案
- 分析系统需求并设计合适的架构
- 解决技术问题和调试困难的代码
- 评估不同技术方案的优缺点

请提供准确、详细的技术建议，并尽可能包含代码示例或实现步骤。
"""
    )
    tech_expert_id = team.add_agent(
        tech_expert,
        skills=["编程", "软件开发", "系统架构", "代码审查", "调试"]
    )
    
    # 2. 数据分析专家
    data_expert = create_expert_agent(
        name="数据分析专家",
        expertise="数据分析、统计学、机器学习、数据可视化",
        system_prompt="""你是数据分析专家，精通数据分析、统计学、机器学习和数据可视化。
        
你擅长：
- 分析和解释复杂数据集
- 设计和评估机器学习模型
- 创建数据可视化和报告
- 提供基于数据的业务洞察

请提供详细的数据分析方法、统计解释和可行的实施步骤。
"""
    )
    data_expert_id = team.add_agent(
        data_expert,
        skills=["数据分析", "统计", "机器学习", "数据可视化", "预测"]
    )
    
    # 3. 商业策略专家
    business_expert = create_expert_agent(
        name="商业策略专家",
        expertise="商业战略、市场分析、产品管理、商业模式",
        system_prompt="""你是商业策略专家，精通商业战略、市场分析、产品管理和商业模式设计。
        
你擅长：
- 制定商业和营销策略
- 分析市场趋势和竞争情况
- 评估商业模式和收入来源
- 提供产品开发和定位建议

请提供实用的商业建议，基于市场现实和行业最佳实践。
"""
    )
    business_expert_id = team.add_agent(
        business_expert,
        skills=["商业策略", "市场分析", "产品管理", "营销", "商业模式"]
    )
    
    # 4. 创意专家
    creative_expert = create_expert_agent(
        name="创意专家",
        expertise="创意思维、内容创作、设计原则",
        system_prompt="""你是创意专家，精通创意思维、内容创作和设计原则。
        
你擅长：
- 生成新颖和有吸引力的创意
- 设计引人入胜的内容和叙事
- 提供视觉和用户体验设计建议
- 解决需要创新思维的问题

请提供独特、引人入胜的创意和设计概念，关注用户体验和美学原则。
"""
    )
    creative_expert_id = team.add_agent(
        creative_expert,
        skills=["创意", "内容创作", "设计", "叙事", "用户体验"]
    )
    
    logger.info(f"专家团队创建完成，共有 {len(team.agents)} 名专家")
    return team


def main():
    """
    主函数 - 运行代理团队示例
    """
    print("\n==========================")
    print("Rainbow Agent 团队协作示例")
    print("==========================\n")
    
    print("初始化专家代理团队...")
    team = create_agent_team()
    
    print("\n团队已准备就绪！")
    print("这个团队包含多名专家代理，可以协同工作来解决复杂问题。")
    print("输入 'exit', 'quit' 或 'q' 退出")
    print("输入 'direct' 在问题前可跳过任务分解，直接由单个代理解答\n")
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\n👤 您的问题: ")
            
            # 检查退出命令
            if user_input.lower() in ["exit", "quit", "q"]:
                print("感谢使用！再见！")
                break
            
            # 检查是否跳过任务分解
            decompose = True
            if user_input.lower().startswith("direct "):
                decompose = False
                user_input = user_input[7:]  # 移除 "direct " 前缀
                print("将直接由单个代理回答，不进行任务分解。")
            
            if not user_input.strip():
                continue
            
            print("\n🤔 专家团队正在思考您的问题...\n")
            
            # 运行代理团队
            result = team.run(user_input, decompose=decompose)
            
            # 提取和显示最终结果
            task = result["task"]
            
            if task["status"] == "completed":
                if decompose:
                    # 显示最终聚合结果
                    final_result = task["result"]["final_result"]
                    print("🌟 专家团队的综合解决方案:\n")
                    print(final_result)
                    
                    # 可选：显示每个子任务的结果
                    print("\n📋 各专家的具体贡献:")
                    for i, subtask in enumerate(task["subtasks"]):
                        if subtask["status"] == "completed":
                            agent_id = subtask["assigned_to"]
                            agent_name = team.agents[agent_id].name if agent_id in team.agents else "未知专家"
                            print(f"\n专家: {agent_name}")
                            print(f"负责: {subtask['description']}")
                            print(f"技能: {', '.join(subtask['requires_skills'])}")
                else:
                    # 直接模式下只显示单个代理的结果
                    print("🤖 专家回应:\n")
                    print(task["result"])
            elif task["status"] == "failed":
                print("❌ 很抱歉，处理您的问题时遇到了困难。")
                print(f"错误信息: {task['result']['error'] if isinstance(task['result'], dict) else task['result']}")
            else:
                print(f"⚠️ 任务状态: {task['status']}")
            
        except KeyboardInterrupt:
            print("\n已中断。输入 'exit' 退出。")
        except Exception as e:
            logger.error(f"错误: {e}")
            print(f"\n抱歉，出现错误: {e}")


if __name__ == "__main__":
    main()
