"""
Rainbow Agent 关系系统使用示例

演示如何在应用中集成和使用关系管理系统
"""
import os
import json
import asyncio
from datetime import datetime, timedelta

from rainbow_agent.relationship import (
    default_system,
    RelationshipSystem,
    RelationshipStatus,
    EnhancedAgentTeam,
    AgentProfile
)


async def basic_relationship_example():
    """基础关系管理示例"""
    print("\n=== 基础关系管理示例 ===")
    
    # 使用默认关系系统
    rs = default_system
    
    # 创建关系
    human_id = "user123"
    ai_id = "assistant456"
    
    # 处理消息并更新关系
    message = "你好，我需要你帮我分析一些数据"
    result = rs.process_message(
        message=message,
        sender_id=human_id,
        sender_type="human",
        receiver_id=ai_id,
        receiver_type="ai",
        metadata={
            "emotional_resonance": False
        }
    )
    
    print(f"处理消息结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # 获取关系上下文
    context = rs.get_relationship_context(human_id, ai_id)
    print(f"\n关系上下文: {json.dumps(context, ensure_ascii=False, indent=2)}")
    
    # 获取关系提示词
    prompt = rs.get_relationship_prompt(human_id, ai_id)
    print(f"\n关系提示词:\n{prompt}")
    
    # 模拟多次互动
    print("\n模拟多次互动...")
    for i in range(10):
        rs.process_message(
            message=f"这是第 {i+1} 条消息",
            sender_id=human_id,
            sender_type="human",
            receiver_id=ai_id,
            receiver_type="ai",
            metadata={
                "emotional_resonance": i % 3 == 0,  # 每3条消息有一次情感共鸣
                "collaboration": {
                    "diary_count": i % 5 == 0,  # 每5条消息有一次日记协作
                    "co_creation_count": i % 7 == 0,  # 每7条消息有一次共创
                    "gift_count": 0
                }
            }
        )
    
    # 再次获取关系上下文
    context = rs.get_relationship_context(human_id, ai_id)
    print(f"\n更新后的关系上下文: {json.dumps(context, ensure_ascii=False, indent=2)}")
    
    # 获取关系提示词
    prompt = rs.get_relationship_prompt(human_id, ai_id)
    print(f"\n更新后的关系提示词:\n{prompt}")


async def relationship_team_example():
    """关系团队示例"""
    print("\n=== 关系团队示例 ===")
    
    # 创建新的关系系统实例
    data_dir = "./data/team_example"
    os.makedirs(data_dir, exist_ok=True)
    rs = RelationshipSystem(data_dir=data_dir)
    
    # 注册代理
    rs.register_agent(
        agent_id="assistant001",
        name="数据分析师",
        role="analyst",
        description="专门处理数据分析任务的AI助手",
        capabilities=["data_analysis", "visualization", "statistics"],
        expertise=["pandas", "numpy", "matplotlib"]
    )
    
    rs.register_agent(
        agent_id="assistant002",
        name="创意顾问",
        role="creative",
        description="专门处理创意和内容生成的AI助手",
        capabilities=["content_creation", "storytelling", "brainstorming"],
        expertise=["writing", "marketing", "design"]
    )
    
    rs.register_agent(
        agent_id="assistant003",
        name="情感顾问",
        role="emotional",
        description="专门处理情感支持和心理咨询的AI助手",
        capabilities=["emotional_support", "active_listening", "empathy"],
        expertise=["psychology", "counseling", "mental_health"]
    )
    
    # 注册任务处理函数
    def handle_data_analysis_task(task, agent):
        print(f"代理 '{agent.name}' 正在执行数据分析任务: {task.title}")
        return "数据分析完成，发现了3个关键趋势"
    
    def handle_creative_task(task, agent):
        print(f"代理 '{agent.name}' 正在执行创意任务: {task.title}")
        return "创意内容生成完成，提供了5个创意方案"
    
    def handle_emotional_task(task, agent):
        print(f"代理 '{agent.name}' 正在执行情感支持任务: {task.title}")
        return "情感支持对话完成，提供了积极的反馈和建议"
    
    rs.register_task_handler("data_analysis", handle_data_analysis_task)
    rs.register_task_handler("creative", handle_creative_task)
    rs.register_task_handler("emotional", handle_emotional_task)
    
    # 创建人类用户与代理之间的关系
    human_id = "user789"
    
    # 处理与数据分析师的消息
    print("\n与数据分析师互动...")
    for i in range(5):
        rs.process_message(
            message=f"我需要分析这些数据 {i+1}",
            sender_id=human_id,
            sender_type="human",
            receiver_id="assistant001",
            receiver_type="ai"
        )
    
    # 处理与创意顾问的消息
    print("\n与创意顾问互动...")
    for i in range(3):
        rs.process_message(
            message=f"我需要一些创意想法 {i+1}",
            sender_id=human_id,
            sender_type="human",
            receiver_id="assistant002",
            receiver_type="ai",
            metadata={"emotional_resonance": True}
        )
    
    # 处理与情感顾问的消息
    print("\n与情感顾问互动...")
    for i in range(7):
        rs.process_message(
            message=f"我今天感觉不太好 {i+1}",
            sender_id=human_id,
            sender_type="human",
            receiver_id="assistant003",
            receiver_type="ai",
            metadata={"emotional_resonance": True}
        )
    
    # 获取关系摘要
    summary = rs.get_relationship_summary(human_id)
    print(f"\n用户关系摘要: {json.dumps(summary, ensure_ascii=False, indent=2)}")
    
    # 获取可执行任务
    executable_tasks = rs.get_executable_tasks()
    print(f"\n可执行任务数量: {len(executable_tasks)}")
    
    # 执行任务
    print("\n执行任务...")
    results = await rs.execute_tasks()
    print(f"执行结果: {json.dumps(results, ensure_ascii=False, indent=2)}")
    
    # 保存数据
    rs.save_data()
    print("\n关系数据已保存")


async def relationship_analysis_example():
    """关系分析示例"""
    print("\n=== 关系分析示例 ===")
    
    # 使用默认关系系统
    rs = default_system
    
    # 创建多个关系
    users = [f"user{i}" for i in range(1, 6)]
    assistants = [f"assistant{i}" for i in range(1, 4)]
    
    # 模拟多个用户与多个助手的互动
    print("\n模拟多用户互动...")
    for user_id in users:
        for assistant_id in assistants:
            # 随机互动次数
            interaction_count = (ord(user_id[-1]) + ord(assistant_id[-1])) % 10 + 1
            
            for i in range(interaction_count):
                rs.process_message(
                    message=f"消息 {i+1}",
                    sender_id=user_id,
                    sender_type="human",
                    receiver_id=assistant_id,
                    receiver_type="ai",
                    metadata={
                        "emotional_resonance": i % 2 == 0
                    }
                )
    
    # 获取全局关系统计
    stats = rs.get_relationship_summary()
    print(f"\n全局关系统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    
    # 查找相似关系
    # 首先找到一个关系ID
    context = rs.get_relationship_context(users[0], assistants[0])
    if context["exists"]:
        rel_id = context["relationship_id"]
        
        # 使用工具分析关系状态
        analysis_tool = rs.analysis_tool
        status_analysis = analysis_tool.run(json.dumps({
            "analysis_type": "status",
            "relationship_id": rel_id
        }))
        print(f"\n关系状态分析: {status_analysis}")
        
        # 分析关系强度
        intensity_analysis = analysis_tool.run(json.dumps({
            "analysis_type": "intensity",
            "relationship_id": rel_id
        }))
        print(f"\n关系强度分析: {intensity_analysis}")
        
        # 分析关系趋势
        trend_analysis = analysis_tool.run(json.dumps({
            "analysis_type": "trend",
            "relationship_id": rel_id
        }))
        print(f"\n关系趋势分析: {trend_analysis}")


async def main():
    """主函数"""
    # 运行基础关系示例
    await basic_relationship_example()
    
    # 运行关系团队示例
    await relationship_team_example()
    
    # 运行关系分析示例
    await relationship_analysis_example()


if __name__ == "__main__":
    asyncio.run(main())
