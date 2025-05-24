"""
ReAct Agent 测试 - 测试 ReAct Agent 的推理和行动能力

本脚本测试 ReAct Agent 的各种功能，包括推理、行动、观察循环，
多步规划能力，以及与工具选择器和工具执行器的集成。
"""
import sys
import os
import time
import json
from typing import Dict, Any, List, Optional, Tuple
import traceback

# 添加项目根目录到路径，以便导入模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from rainbow_agent.core.react_agent import ReActAgent
from rainbow_agent.core.optimized_tool_selector import OptimizedToolSelector, SelectionStrategy
from rainbow_agent.tools.base import BaseTool
from rainbow_agent.tools.tool_invoker import ToolInvoker
from rainbow_agent.utils.logger import get_logger

logger = get_logger(__name__)

# 定义测试工具
class CalculatorTool(BaseTool):
    """计算器工具，用于数学计算"""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="执行数学计算，支持基本运算和函数",
            usage="calculator(expression)"
        )
        
    def run(self, args):
        try:
            if isinstance(args, str):
                expression = args.strip()
            else:
                expression = args.get("expression", "")
                
            # 安全地执行计算（实际应用中应该使用更安全的方法）
            result = eval(expression)
            return f"计算结果: {result}"
                
        except Exception as e:
            return f"计算错误: {str(e)}"

class WeatherTool(BaseTool):
    """天气工具，用于查询天气信息"""
    
    def __init__(self):
        super().__init__(
            name="weather",
            description="查询特定城市的天气信息",
            usage="weather(city)"
        )
        
    def run(self, args):
        try:
            if isinstance(args, str):
                city = args.strip()
            else:
                city = args.get("city", "")
                
            # 模拟天气数据
            weather_data = {
                "北京": {"weather": "晴朗", "temperature": "20-28度", "air_quality": "良好"},
                "上海": {"weather": "多云", "temperature": "22-30度", "air_quality": "良好"},
                "广州": {"weather": "阵雨", "temperature": "25-32度", "air_quality": "中等"},
                "深圳": {"weather": "雷阵雨", "temperature": "26-33度", "air_quality": "中等"},
                "杭州": {"weather": "晴间多云", "temperature": "21-29度", "air_quality": "优"},
                "成都": {"weather": "阴天", "temperature": "18-25度", "air_quality": "良好"},
            }
            
            if city in weather_data:
                data = weather_data[city]
                return f"{city}今天{data['weather']}，气温{data['temperature']}，空气质量{data['air_quality']}。"
            else:
                return f"抱歉，没有找到{city}的天气信息。"
                
        except Exception as e:
            return f"天气查询错误: {str(e)}"

class SearchTool(BaseTool):
    """搜索工具，用于搜索信息"""
    
    def __init__(self):
        super().__init__(
            name="search",
            description="搜索互联网信息",
            usage="search(query)"
        )
        
    def run(self, args):
        try:
            if isinstance(args, str):
                query = args.strip()
            else:
                query = args.get("query", "")
                
            # 模拟搜索结果
            time.sleep(0.5)  # 模拟网络延迟
            
            if "比特币" in query or "加密货币" in query:
                return "比特币当前价格约为55000美元，24小时涨幅2.3%。以太坊价格约为3200美元，24小时涨幅1.8%。"
            elif "人工智能" in query or "AI" in query:
                return "人工智能最新进展：1. 大型语言模型在医疗领域取得突破；2. AI辅助编程工具效率提升30%；3. 自动驾驶技术在复杂路况测试中表现优异。"
            else:
                return f"关于'{query}'的搜索结果：找到约100万条相关信息，包括新闻、学术论文、社交媒体讨论等。"
                
        except Exception as e:
            return f"搜索错误: {str(e)}"

class TranslationTool(BaseTool):
    """翻译工具，用于文本翻译"""
    
    def __init__(self):
        super().__init__(
            name="translate",
            description="将文本从一种语言翻译成另一种语言",
            usage="translate(text, from_lang, to_lang)"
        )
        
    def run(self, args):
        try:
            if isinstance(args, str):
                try:
                    args_dict = json.loads(args)
                except:
                    parts = args.split(",", 2)
                    if len(parts) == 3:
                        text, from_lang, to_lang = parts[0].strip(), parts[1].strip(), parts[2].strip()
                        args_dict = {"text": text, "from_lang": from_lang, "to_lang": to_lang}
                    else:
                        return "错误: 参数格式不正确，应为 'text, from_lang, to_lang' 或 JSON 格式"
            else:
                args_dict = args
                
            text = args_dict.get("text", "")
            from_lang = args_dict.get("from_lang", "").lower()
            to_lang = args_dict.get("to_lang", "").lower()
            
            # 模拟翻译结果
            if from_lang == "中文" and to_lang == "英文":
                translations = {
                    "你好": "Hello",
                    "谢谢": "Thank you",
                    "彩虹城": "Rainbow City",
                    "人工智能": "Artificial Intelligence",
                    "工具链": "Tool Chain"
                }
                
                if text in translations:
                    return translations[text]
                else:
                    return f"[模拟翻译] {text} 的中译英结果"
                    
            elif from_lang == "英文" and to_lang == "中文":
                translations = {
                    "Hello": "你好",
                    "Thank you": "谢谢",
                    "Rainbow City": "彩虹城",
                    "Artificial Intelligence": "人工智能",
                    "Tool Chain": "工具链"
                }
                
                if text in translations:
                    return translations[text]
                else:
                    return f"[模拟翻译] {text} 的英译中结果"
                    
            else:
                return f"[模拟翻译] {text} 从{from_lang}翻译为{to_lang}的结果"
                
        except Exception as e:
            return f"翻译错误: {str(e)}"

class DatabaseTool(BaseTool):
    """数据库工具，用于查询和管理数据库"""
    
    def __init__(self):
        super().__init__(
            name="database",
            description="查询和管理数据库，支持SQL操作",
            usage="database(query_type, query)"
        )
        
    def run(self, args):
        try:
            if isinstance(args, str):
                try:
                    args_dict = json.loads(args)
                except:
                    parts = args.split(",", 1)
                    if len(parts) == 2:
                        query_type, query = parts[0].strip(), parts[1].strip()
                        args_dict = {"query_type": query_type, "query": query}
                    else:
                        return "错误: 参数格式不正确，应为 'query_type, query' 或 JSON 格式"
            else:
                args_dict = args
                
            query_type = args_dict.get("query_type", "").lower()
            query = args_dict.get("query", "")
            
            # 模拟数据库操作
            if query_type == "select":
                if "用户" in query or "users" in query:
                    return "查询结果: 找到10条用户记录，包括ID、姓名、邮箱等信息。"
                elif "产品" in query or "products" in query:
                    return "查询结果: 找到50条产品记录，包括ID、名称、价格、库存等信息。"
                elif "订单" in query or "orders" in query:
                    return "查询结果: 找到100条订单记录，包括订单ID、用户ID、产品ID、订单时间等信息。"
                else:
                    return f"查询结果: 执行查询 '{query}'，返回0条记录。"
            elif query_type == "insert":
                return f"插入成功: 执行插入操作 '{query}'，影响1行。"
            elif query_type == "update":
                return f"更新成功: 执行更新操作 '{query}'，影响5行。"
            elif query_type == "delete":
                return f"删除成功: 执行删除操作 '{query}'，影响2行。"
            else:
                return f"未知操作类型: {query_type}"
                
        except Exception as e:
            return f"数据库操作错误: {str(e)}"

# 测试用例 - 简单查询
simple_test_queries = [
    "计算 123 + 456 * 2",
    "北京今天天气怎么样？",
    "搜索关于比特币的最新信息",
    "把'人工智能'翻译成英文",
    "查询数据库中的用户信息"
]

# 测试用例 - 复杂查询（需要多步规划）
complex_test_queries = [
    "计算北京和上海的平均温度",
    "查找关于人工智能的信息，然后将其翻译成英文",
    "计算 100 * 5，然后查询价格在这个范围内的产品",
    "搜索最新的比特币价格，并计算如果我有10个比特币，价值多少美元",
    "查询上海的天气，如果天气好，推荐一些户外活动"
]

def test_react_agent_simple_queries(agent, queries):
    """测试 ReAct Agent 处理简单查询的能力"""
    
    print("\n=== 简单查询测试 ===")
    
    results = []
    
    for query in queries:
        print(f"\n查询: {query}")
        
        start_time = time.time()
        response = agent.run(query)
        end_time = time.time()
        
        print(f"响应: {response.get('response', '')}")
        print(f"处理时间: {(end_time - start_time):.3f}秒")
        
        # 打印思考过程
        if 'thinking' in response:
            print(f"思考过程: {response['thinking']}")
        
        # 打印执行的步骤
        if 'steps' in response:
            print("\n执行步骤:")
            for i, step in enumerate(response['steps']):
                print(f"步骤 {i+1}: {step.get('action', '')}")
                print(f"  结果: {step.get('result', '')}")
        
        results.append({
            "query": query,
            "response": response.get('response', ''),
            "thinking": response.get('thinking', ''),
            "steps": response.get('steps', []),
            "processing_time": end_time - start_time
        })
    
    return results

def test_react_agent_complex_queries(agent, queries):
    """测试 ReAct Agent 处理复杂查询的能力"""
    
    print("\n=== 复杂查询测试 ===")
    
    results = []
    
    for query in queries:
        print(f"\n查询: {query}")
        
        start_time = time.time()
        response = agent.run(query)
        end_time = time.time()
        
        print(f"响应: {response.get('response', '')}")
        print(f"处理时间: {(end_time - start_time):.3f}秒")
        
        # 打印思考过程
        if 'thinking' in response:
            print(f"思考过程: {response['thinking']}")
        
        # 打印执行的步骤
        if 'steps' in response:
            print("\n执行步骤:")
            for i, step in enumerate(response['steps']):
                print(f"步骤 {i+1}: {step.get('action', '')}")
                print(f"  结果: {step.get('result', '')}")
        
        # 分析步骤数量
        steps_count = len(response.get('steps', []))
        print(f"总步骤数: {steps_count}")
        
        results.append({
            "query": query,
            "response": response.get('response', ''),
            "thinking": response.get('thinking', ''),
            "steps": response.get('steps', []),
            "steps_count": steps_count,
            "processing_time": end_time - start_time
        })
    
    # 计算平均步骤数
    avg_steps = sum(r["steps_count"] for r in results) / len(results) if results else 0
    print(f"\n复杂查询平均步骤数: {avg_steps:.2f}")
    
    return results

def test_react_agent_error_handling(agent):
    """测试 ReAct Agent 的错误处理能力"""
    
    print("\n=== 错误处理测试 ===")
    
    # 测试无效查询
    invalid_queries = [
        "",  # 空查询
        "   ",  # 只有空格
        "这是一个没有明确意图的查询",  # 模糊查询
        "使用一个不存在的工具",  # 请求不存在的工具
        "执行一个复杂的操作但提供不完整的信息"  # 信息不完整
    ]
    
    results = []
    
    for query in invalid_queries:
        print(f"\n测试无效查询: '{query}'")
        
        try:
            start_time = time.time()
            response = agent.run(query)
            end_time = time.time()
            
            print(f"响应: {response.get('response', '')}")
            print(f"处理时间: {(end_time - start_time):.3f}秒")
            
            # 检查是否有错误信息
            error = response.get('error', None)
            if error:
                print(f"错误: {error}")
            
            results.append({
                "query": query,
                "response": response.get('response', ''),
                "error": error,
                "processing_time": end_time - start_time,
                "success": error is None
            })
            
            print("✓ 成功处理无效查询")
        except Exception as e:
            print(f"✗ 未捕获的错误: {e}")
            traceback.print_exc()
            
            results.append({
                "query": query,
                "error": str(e),
                "success": False
            })
    
    # 统计成功处理的无效查询数量
    success_count = sum(1 for r in results if r.get("success", False))
    total_count = len(results)
    
    print(f"\n成功处理无效查询的比例: {success_count}/{total_count} ({success_count/total_count:.2%})")
    
    return results

def test_react_agent_context_handling(agent):
    """测试 ReAct Agent 的上下文处理能力"""
    
    print("\n=== 上下文处理测试 ===")
    
    # 测试上下文相关的查询序列
    context_queries = [
        {
            "query": "北京今天天气怎么样？",
            "context": {}
        },
        {
            "query": "那上海呢？",
            "context": {
                "previous_query": "北京今天天气怎么样？",
                "previous_response": "北京今天晴朗，气温20-28度，空气质量良好。"
            }
        },
        {
            "query": "计算这两个城市的平均最高温度",
            "context": {
                "previous_query": "那上海呢？",
                "previous_response": "上海今天多云，气温22-30度，空气质量良好。",
                "conversation_history": [
                    {"query": "北京今天天气怎么样？", "response": "北京今天晴朗，气温20-28度，空气质量良好。"},
                    {"query": "那上海呢？", "response": "上海今天多云，气温22-30度，空气质量良好。"}
                ]
            }
        }
    ]
    
    results = []
    
    for i, query_info in enumerate(context_queries):
        query = query_info["query"]
        context = query_info["context"]
        
        print(f"\n查询 {i+1}: {query}")
        print(f"上下文: {json.dumps(context, ensure_ascii=False, indent=2)}")
        
        start_time = time.time()
        response = agent.run(query, context)
        end_time = time.time()
        
        print(f"响应: {response.get('response', '')}")
        print(f"处理时间: {(end_time - start_time):.3f}秒")
        
        # 打印执行的步骤
        if 'steps' in response:
            print("\n执行步骤:")
            for i, step in enumerate(response['steps']):
                print(f"步骤 {i+1}: {step.get('action', '')}")
                print(f"  结果: {step.get('result', '')}")
        
        results.append({
            "query": query,
            "context": context,
            "response": response.get('response', ''),
            "steps": response.get('steps', []),
            "processing_time": end_time - start_time
        })
    
    return results

def test_react_agent_performance(agent, queries, iterations=3):
    """测试 ReAct Agent 的性能"""
    
    print("\n=== 性能测试 ===")
    
    processing_times = []
    step_counts = []
    
    for _ in range(iterations):
        for query in queries:
            start_time = time.time()
            response = agent.run(query)
            end_time = time.time()
            
            processing_time = end_time - start_time
            steps = response.get('steps', [])
            step_count = len(steps)
            
            processing_times.append(processing_time)
            step_counts.append(step_count)
            
            print(f"查询: {query}")
            print(f"处理时间: {processing_time:.3f}秒")
            print(f"步骤数: {step_count}")
    
    avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
    avg_step_count = sum(step_counts) / len(step_counts) if step_counts else 0
    
    print(f"\n平均处理时间: {avg_processing_time:.3f}秒")
    print(f"平均步骤数: {avg_step_count:.2f}")
    
    return {
        "avg_processing_time": avg_processing_time,
        "avg_step_count": avg_step_count,
        "processing_times": processing_times,
        "step_counts": step_counts
    }

def main():
    """主函数，运行所有测试"""
    
    print("=== ReAct Agent 测试 ===")
    
    # 创建测试工具
    calculator = CalculatorTool()
    weather = WeatherTool()
    search = SearchTool()
    translate = TranslationTool()
    database = DatabaseTool()
    
    tools = [calculator, weather, search, translate, database]
    
    # 创建工具选择器
    tool_selector = OptimizedToolSelector(
        tools=tools,
        strategy=SelectionStrategy.HYBRID,
        confidence_threshold=0.6,
        cache_capacity=100,
        verbose=True
    )
    
    # 创建工具执行器
    tool_invoker = ToolInvoker(
        tools=tools,
        use_cache=True,
        cache_ttl=3600
    )
    
    # 创建 ReAct Agent
    react_agent = ReActAgent(
        tool_invoker=tool_invoker,
        max_iterations=10,
        verbose=True
    )
    
    # 测试简单查询
    simple_results = test_react_agent_simple_queries(react_agent, simple_test_queries)
    
    # 测试复杂查询
    complex_results = test_react_agent_complex_queries(react_agent, complex_test_queries)
    
    # 测试错误处理
    error_results = test_react_agent_error_handling(react_agent)
    
    # 测试上下文处理
    context_results = test_react_agent_context_handling(react_agent)
    
    # 测试性能
    performance_results = test_react_agent_performance(react_agent, simple_test_queries[:3])
    
    # 总结测试结果
    print("\n=== 测试结果总结 ===")
    
    # 简单查询结果
    simple_avg_time = sum(r["processing_time"] for r in simple_results) / len(simple_results)
    simple_avg_steps = sum(len(r["steps"]) for r in simple_results) / len(simple_results)
    print(f"简单查询平均处理时间: {simple_avg_time:.3f}秒")
    print(f"简单查询平均步骤数: {simple_avg_steps:.2f}")
    
    # 复杂查询结果
    complex_avg_time = sum(r["processing_time"] for r in complex_results) / len(complex_results)
    complex_avg_steps = sum(r["steps_count"] for r in complex_results) / len(complex_results)
    print(f"复杂查询平均处理时间: {complex_avg_time:.3f}秒")
    print(f"复杂查询平均步骤数: {complex_avg_steps:.2f}")
    
    # 错误处理结果
    error_success_rate = sum(1 for r in error_results if r.get("success", False)) / len(error_results)
    print(f"错误处理成功率: {error_success_rate:.2%}")
    
    # 性能测试结果
    print(f"性能测试平均处理时间: {performance_results['avg_processing_time']:.3f}秒")
    print(f"性能测试平均步骤数: {performance_results['avg_step_count']:.2f}")
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()
