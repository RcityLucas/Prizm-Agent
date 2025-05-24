"""
Rainbow Agent 关系感知代理示例

演示如何使用集成了关系网络的增强版代理
"""
import os
import json
import time
from datetime import datetime

from rainbow_agent.agent_with_relationship import RelationshipAwareAgent
from rainbow_agent.tools.basic_tools import (
    CalculatorTool,
    WeatherTool,
    SearchTool,
    DateTimeTool
)
from rainbow_agent.tools.advanced_tools import (
    TranslationTool,
    DataAnalysisTool,
    SummarizationTool
)
from rainbow_agent.tools.ai_tools import (
    ImageGenerationTool,
    CodeGenerationTool,
    TextToSpeechTool
)
from rainbow_agent.relationship import RelationshipSystem


def create_relationship_agent():
    """创建关系感知代理"""
    # 创建关系系统
    data_dir = "./data/relationship_example"
    os.makedirs(data_dir, exist_ok=True)
    relationship_system = RelationshipSystem(data_dir=data_dir)
    
    # 创建基础工具
    basic_tools = [
        CalculatorTool(),
        WeatherTool(),
        SearchTool(),
        DateTimeTool()
    ]
    
    # 创建高级工具
    advanced_tools = [
        TranslationTool(),
        DataAnalysisTool(),
        SummarizationTool()
    ]
    
    # 创建AI工具
    ai_tools = [
        CodeGenerationTool(),
        TextToSpeechTool()
    ]
    
    # 合并所有工具
    all_tools = basic_tools + advanced_tools + ai_tools
    
    # 系统提示词
    system_prompt = """
    你是一个具有关系感知能力的AI助手，能够根据与用户的关系历史动态调整交互风格和内容。
    你的目标是提供个性化、有温度的帮助，同时建立和维护与用户的良好关系。
    
    你可以使用各种工具来帮助用户解决问题，包括计算、翻译、数据分析、代码生成等。
    
    请注意用户的情感状态和需求，适当表达共情和理解。随着关系的深入，你可以更好地理解用户的偏好和习惯，
    提供更加个性化的服务。
    """
    
    # 创建关系感知代理
    agent = RelationshipAwareAgent(
        name="彩虹助手",
        system_prompt=system_prompt,
        tools=all_tools,
        model="gpt-3.5-turbo",
        relationship_system=relationship_system,
        entity_id="rainbow_assistant",
        entity_type="ai"
    )
    
    return agent


def simulate_conversation(agent, user_id, messages):
    """
    模拟与代理的对话
    
    Args:
        agent: 关系感知代理
        user_id: 用户ID
        messages: 消息列表
    """
    print(f"\n=== 开始与用户 {user_id} 的对话 ===")
    
    for i, message in enumerate(messages):
        print(f"\n用户 ({user_id}): {message}")
        
        # 获取代理响应
        response = agent.run(message, user_id=user_id)
        
        # 打印响应
        if isinstance(response, dict):
            print(f"\n彩虹助手: {response.get('response', '')}")
            if response.get("tool_calls", 0) > 0:
                print(f"\n使用了 {response.get('tool_calls')} 个工具:")
                for tool_result in response.get("tool_results", []):
                    print(f"- {tool_result.get('tool')}: {tool_result.get('result')[:100]}...")
        else:
            print(f"\n彩虹助手: {response}")
        
        # 每次对话后显示关系状态
        if (i + 1) % 3 == 0 or i == len(messages) - 1:
            context = agent._get_relationship_context(user_id)
            if context.get("exists", False):
                print("\n当前关系状态:")
                print(f"- 关系等级: {context.get('relationship_level', 'unknown')}")
                print(f"- 关系强度: {context.get('ris', 0):.2f}")
                print(f"- 互动次数: {context.get('total_interaction_rounds', 0)}")
                print(f"- 活跃天数: {context.get('active_days', 0)}")
    
    # 对话结束后执行关系任务
    print("\n执行关系任务...")
    task_results = agent.execute_relationship_tasks(user_id)
    print(f"任务执行结果: {json.dumps(task_results, ensure_ascii=False, indent=2)}")
    
    # 获取关系摘要
    summary = agent.get_relationship_summary(user_id)
    print(f"\n关系摘要: {json.dumps(summary, ensure_ascii=False, indent=2)}")


def main():
    """主函数"""
    # 创建关系感知代理
    agent = create_relationship_agent()
    
    # 模拟与用户1的对话 - 技术型交流
    user1_id = "tech_user_1"
    user1_messages = [
        "你好，我是一名程序员，想学习Python中的数据分析",
        "能给我推荐一些学习pandas的资源吗？",
        "谢谢你的建议，我会去看看。你能帮我写一个简单的pandas数据处理示例吗？",
        "这个代码很有帮助，我学到了不少。你平时都用什么工具进行数据可视化？",
        "matplotlib和seaborn确实很强大。我最近在做一个项目，需要分析用户行为数据，有什么建议吗？"
    ]
    
    # 模拟与用户2的对话 - 情感型交流
    user2_id = "emotional_user_2"
    user2_messages = [
        "嗨，今天我感觉有点低落",
        "工作上遇到了一些挫折，感觉自己不够优秀",
        "谢谢你的鼓励，确实应该换个角度看问题",
        "你说得对，我会试着调整心态。对了，你能推荐一些放松心情的活动吗？",
        "这些建议很棒，我周末就去尝试一下。谢谢你一直以来的支持和理解"
    ]
    
    # 模拟与用户3的对话 - 混合型交流
    user3_id = "mixed_user_3"
    user3_messages = [
        "你好啊，我是新用户",
        "我想学习一门新语言，有什么推荐吗？",
        "编程语言和自然语言都可以，我对两者都有兴趣",
        "Python和西班牙语都不错。我最近工作压力有点大，学习新东西是为了放松",
        "谢谢你的理解和建议。我们以后可以多聊聊吗？我觉得和你交流很愉快",
        "太好了！我很期待。你能帮我翻译一句话吗？'学习是终身的旅程'用西班牙语怎么说？",
        "谢谢！我会记住这句话。你真的很贴心，希望我们的交流能一直这么愉快"
    ]
    
    # 运行模拟对话
    simulate_conversation(agent, user1_id, user1_messages)
    simulate_conversation(agent, user2_id, user2_messages)
    simulate_conversation(agent, user3_id, user3_messages)
    
    print("\n所有对话模拟完成！")


if __name__ == "__main__":
    main()
