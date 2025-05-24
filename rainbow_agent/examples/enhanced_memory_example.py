"""
增强记忆系统使用示例

展示如何在代理系统中集成和使用增强记忆系统
"""
import os
import sys
import time
from datetime import datetime
import json

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rainbow_agent.memory.enhanced_memory import EnhancedMemory
from rainbow_agent.core.agent_system import AgentSystem
from rainbow_agent.tools.base import BaseTool
from rainbow_agent.utils.logger import get_logger

logger = get_logger(__name__)


class WeatherTool(BaseTool):
    """天气查询工具"""
    
    def __init__(self):
        super().__init__(
            name="weather",
            description="获取指定城市的天气信息",
            usage="weather(city)"
        )
    
    def run(self, args):
        """模拟天气查询"""
        city = args
        if not isinstance(city, str):
            return "请提供城市名称"
        
        # 模拟天气数据
        weather_data = {
            "北京": {"temp": "25°C", "condition": "晴朗", "humidity": "40%"},
            "上海": {"temp": "28°C", "condition": "多云", "humidity": "65%"},
            "广州": {"temp": "32°C", "condition": "阵雨", "humidity": "80%"},
            "深圳": {"temp": "30°C", "condition": "晴间多云", "humidity": "75%"}
        }
        
        if city in weather_data:
            data = weather_data[city]
            return f"{city}的天气：{data['condition']}，温度{data['temp']}，湿度{data['humidity']}"
        else:
            return f"抱歉，没有找到{city}的天气信息"


class CalculatorTool(BaseTool):
    """计算器工具"""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="执行数学计算",
            usage="calculator(expression)"
        )
    
    def run(self, args):
        """执行数学计算"""
        expression = args
        if not isinstance(expression, str):
            return "请提供有效的数学表达式"
        
        try:
            # 安全的eval实现
            result = eval(expression, {"__builtins__": {}}, {"abs": abs, "round": round, "max": max, "min": min})
            return f"计算结果: {result}"
        except Exception as e:
            return f"计算错误: {str(e)}"


def simulate_conversation_with_memory():
    """模拟使用增强记忆系统的对话"""
    print("\n=== 模拟使用增强记忆系统的对话 ===\n")
    
    # 创建增强记忆系统
    memory = EnhancedMemory(
        db_path="example_memory.db",
        working_memory_capacity=5,
        working_memory_ttl=3600,  # 1小时
        short_term_capacity=20,
        short_term_ttl=86400,  # 1天
        long_term_capacity=1000,
        auto_compress_threshold=50
    )
    
    # 创建工具
    tools = [WeatherTool(), CalculatorTool()]
    
    # 创建代理系统
    agent = AgentSystem(tools=tools)
    
    # 模拟对话
    conversations = [
        # 第一轮对话：询问天气
        {
            "user": "北京今天天气怎么样？",
            "system_response": "我来查询一下北京的天气信息。",
            "tool_name": "weather",
            "tool_args": "北京",
            "tool_result": "北京的天气：晴朗，温度25°C，湿度40%",
            "assistant": "根据最新数据，北京今天天气晴朗，温度25°C，湿度40%，是个不错的天气。"
        },
        # 第二轮对话：数学计算
        {
            "user": "帮我计算一下123乘以456",
            "system_response": "我来帮你计算这个表达式。",
            "tool_name": "calculator",
            "tool_args": "123 * 456",
            "tool_result": "计算结果: 56088",
            "assistant": "123乘以456的结果是56088。"
        },
        # 第三轮对话：询问上海天气
        {
            "user": "上海呢？那里天气怎么样？",
            "system_response": "我来查询一下上海的天气信息。",
            "tool_name": "weather",
            "tool_args": "上海",
            "tool_result": "上海的天气：多云，温度28°C，湿度65%",
            "assistant": "上海目前天气多云，温度28°C，湿度65%，比北京稍微热一些。"
        },
        # 第四轮对话：引用之前的信息
        {
            "user": "北京和上海的温差是多少？",
            "system_response": "我需要计算北京和上海的温差。",
            "tool_name": "calculator",
            "tool_args": "28 - 25",
            "tool_result": "计算结果: 3",
            "assistant": "根据之前查询的信息，北京温度是25°C，上海温度是28°C，两地温差是3°C，上海比北京温度高。"
        },
        # 第五轮对话：询问之前未提及的城市
        {
            "user": "广州的天气怎么样？",
            "system_response": "我来查询一下广州的天气信息。",
            "tool_name": "weather",
            "tool_args": "广州",
            "tool_result": "广州的天气：阵雨，温度32°C，湿度80%",
            "assistant": "广州目前天气状况是阵雨，温度32°C，湿度80%，比北京和上海都要热，而且湿度较高。"
        },
        # 第六轮对话：询问之前对话的总结
        {
            "user": "总结一下我们刚才讨论的各个城市的天气情况",
            "system_response": "我将总结之前讨论的天气信息。",
            "tool_name": None,
            "tool_args": None,
            "tool_result": None,
            "assistant": "我们刚才讨论了三个城市的天气情况：\n1. 北京：晴朗，温度25°C，湿度40%\n2. 上海：多云，温度28°C，湿度65%\n3. 广州：阵雨，温度32°C，湿度80%\n\n从温度上看，广州最热(32°C)，其次是上海(28°C)，北京最凉爽(25°C)。从湿度来看，广州湿度最高(80%)，其次是上海(65%)，北京最干燥(40%)。"
        }
    ]
    
    # 执行模拟对话
    for i, conv in enumerate(conversations):
        print(f"\n--- 对话轮次 {i+1} ---")
        print(f"用户: {conv['user']}")
        print(f"系统思考: {conv['system_response']}")
        
        # 记录用户输入
        user_input = conv['user']
        
        # 如果有工具调用
        if conv['tool_name']:
            print(f"调用工具: {conv['tool_name']}({conv['tool_args']})")
            print(f"工具结果: {conv['tool_result']}")
        
        # 记录助手回复
        assistant_response = conv['assistant']
        print(f"助手: {assistant_response}")
        
        # 保存到记忆系统
        importance = 0.6 + i * 0.05  # 逐渐增加重要性
        metadata = {
            "turn_id": i + 1,
            "tool_used": conv['tool_name'],
            "topic": "天气" if "天气" in user_input else "计算" if "计算" in user_input else "其他"
        }
        
        memory.save(user_input, assistant_response, importance, metadata)
        print(f"记忆已保存，重要性: {importance:.2f}")
        
        # 如果是最后一轮，展示记忆检索能力
        if i == len(conversations) - 1:
            # 等待一秒，确保记忆已保存
            time.sleep(1)
            
            print("\n--- 记忆检索演示 ---")
            
            # 基础检索
            print("\n1. 基础检索 (查询'天气'):")
            basic_results = memory.retrieve("天气", limit=3, use_relevance=False)
            for j, result in enumerate(basic_results):
                print(f"  结果 {j+1}: {result.get('user_input', '')}")
                print(f"  回复: {result.get('assistant_response', '')[:50]}...")
            
            # 相关性检索
            print("\n2. 相关性检索 (查询'各个城市温度比较'):")
            relevance_results = memory.retrieve("各个城市温度比较", limit=3, use_relevance=True)
            for j, result in enumerate(relevance_results):
                print(f"  结果 {j+1}: {result.get('user_input', '')}")
                print(f"  回复: {result.get('assistant_response', '')[:50]}...")
            
            # 记忆层检索
            print("\n3. 工作记忆层检索:")
            layer_results = memory.retrieve_by_layer("", layer="working", limit=3)
            for j, result in enumerate(layer_results):
                print(f"  结果 {j+1}: {result.get('user_input', '')}")
            
            # 对话压缩
            print("\n4. 对话摘要生成:")
            conversation_data = [
                {
                    "user_input": conv["user"],
                    "assistant_response": conv["assistant"],
                    "timestamp": datetime.now().isoformat()
                }
                for conv in conversations
            ]
            summary_result = memory.compress_conversation(conversation_data)
            print(f"  摘要: {summary_result['summary']}")
            print("\n  关键点:")
            for point in summary_result['key_points']:
                print(f"  - {point}")
            
            # 记忆统计
            print("\n5. 记忆系统统计:")
            stats = memory.get_memory_stats()
            for key, value in stats.items():
                print(f"  {key}: {value}")
    
    print("\n=== 模拟对话结束 ===")


def integrate_with_agent_system():
    """展示如何将增强记忆系统集成到代理系统中"""
    print("\n=== 增强记忆系统与代理系统集成示例 ===\n")
    
    # 创建增强记忆系统
    memory = EnhancedMemory(db_path="agent_memory.db")
    
    # 创建工具
    tools = [WeatherTool(), CalculatorTool()]
    
    # 创建代理系统
    agent = AgentSystem(tools=tools)
    
    # 模拟代理处理查询
    def process_query(query):
        print(f"用户查询: {query}")
        
        # 1. 从记忆中检索相关上下文
        relevant_memories = memory.retrieve(query, limit=3, use_relevance=True)
        
        context = ""
        if relevant_memories:
            context = "相关上下文:\n"
            for i, mem in enumerate(relevant_memories):
                context += f"{i+1}. 用户: {mem.get('user_input', '')}\n"
                context += f"   助手: {mem.get('assistant_response', '')}\n"
        
        print(f"检索到 {len(relevant_memories)} 条相关记忆")
        
        # 2. 使用代理系统处理查询
        # 这里简化处理，实际应将上下文传入代理系统
        result = {
            "answer": f"这是对'{query}'的回答，基于 {len(relevant_memories)} 条相关记忆。",
            "tool_calls": []
        }
        
        # 3. 保存到记忆系统
        memory.save(query, result["answer"], importance=0.7)
        
        return result
    
    # 模拟几个查询
    queries = [
        "北京今天天气怎么样？",
        "上海的天气呢？",
        "哪个城市更热一些？"
    ]
    
    for query in queries:
        result = process_query(query)
        print(f"代理回答: {result['answer']}")
        print()
    
    print("=== 集成示例结束 ===")


if __name__ == "__main__":
    print("增强记忆系统示例程序")
    print("=====================")
    
    # 运行模拟对话示例
    simulate_conversation_with_memory()
    
    # 运行代理系统集成示例
    # integrate_with_agent_system()
