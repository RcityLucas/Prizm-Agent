"""
集成代理系统测试 - 测试所有组件的集成功能

本脚本测试整个代理系统的集成功能，包括ReAct代理、优化工具选择器、工具链和工具执行器
如何协同工作以处理各种查询和任务。
"""
import sys
import os
import time
import json
from typing import Dict, Any, List, Optional, Tuple
import traceback
import random

# 添加项目根目录到路径，以便导入模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from rainbow_agent.core.react_agent import ReActAgent
from rainbow_agent.core.optimized_tool_selector import OptimizedToolSelector, SelectionStrategy
from rainbow_agent.core.agent_system import AgentSystem
from rainbow_agent.tools.base import BaseTool
from rainbow_agent.tools.tool_invoker import ToolInvoker
from rainbow_agent.tools.tool_chain import ToolChain, ConditionalToolChain
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
            time.sleep(0.2)  # 模拟网络延迟
            
            if "比特币" in query or "加密货币" in query:
                return f"比特币当前价格约为55000美元，24小时涨幅2.3%。以太坊价格约为3200美元，24小时涨幅1.8%。"
            elif "人工智能" in query or "AI" in query:
                return f"人工智能最新进展：1. 大型语言模型在医疗领域取得突破；2. AI辅助编程工具效率提升30%；3. 自动驾驶技术在复杂路况测试中表现优异。"
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

class SummarizationTool(BaseTool):
    """摘要工具，用于生成文本摘要"""
    
    def __init__(self):
        super().__init__(
            name="summarize",
            description="生成文本摘要，提取关键信息",
            usage="summarize(text)"
        )
        
    def run(self, args):
        try:
            if isinstance(args, str):
                text = args.strip()
            else:
                text = args.get("text", "")
                
            # 模拟摘要生成
            if len(text) < 50:
                return f"摘要: {text}"
            else:
                # 简单模拟，实际应用中应使用更复杂的摘要算法
                words = text.split()
                if len(words) > 20:
                    summary = " ".join(words[:10]) + "..." + " ".join(words[-10:])
                    return f"摘要: {summary}"
                else:
                    return f"摘要: {text}"
                
        except Exception as e:
            return f"摘要错误: {str(e)}"

# 创建工具链
def create_weather_summary_chain(tools):
    """创建天气摘要工具链"""
    weather_tool = next((t for t in tools if t.name == "weather"), None)
    summarize_tool = next((t for t in tools if t.name == "summarize"), None)
    
    if not weather_tool or not summarize_tool:
        raise ValueError("无法找到所需的工具")
    
    return ToolChain(
        name="weather_summary",
        description="查询天气并生成摘要",
        tools=[weather_tool, summarize_tool]
    )

def create_search_translate_chain(tools):
    """创建搜索翻译工具链"""
    search_tool = next((t for t in tools if t.name == "search"), None)
    translate_tool = next((t for t in tools if t.name == "translate"), None)
    
    if not search_tool or not translate_tool:
        raise ValueError("无法找到所需的工具")
    
    return ToolChain(
        name="search_translate",
        description="搜索信息并翻译结果",
        tools=[search_tool, translate_tool]
    )

def create_conditional_weather_chain(tools):
    """创建条件天气工具链"""
    weather_tool = next((t for t in tools if t.name == "weather"), None)
    
    if not weather_tool:
        raise ValueError("无法找到所需的工具")
    
    # 创建一个基本的工具链
    weather_chain = ToolChain(
        name="weather_chain",
        description="查询天气信息",
        tools=[weather_tool]
    )
    
    # 定义条件函数
    def condition_func(input_data, context):
        # 简单的条件，始终执行
        return True
    
    return ConditionalToolChain(
        name="conditional_weather",
        description="根据天气情况提供建议",
        condition_func=condition_func,
        tools=[weather_tool]
    )

# 测试用例
test_queries = [
    # 简单查询
    "计算 123 + 456 * 2",
    "北京今天天气怎么样？",
    "搜索关于比特币的最新信息",
    "把'人工智能'翻译成英文",
    "查询数据库中的用户信息",
    
    # 工具链查询
    "查询北京的天气并生成摘要",
    "搜索关于人工智能的信息并翻译成英文",
    "查询上海的天气，并根据天气情况给出建议",
    
    # 复杂查询
    "计算北京和上海的平均温度",
    "查找关于人工智能的信息，然后将其翻译成英文",
    "计算 100 * 5，然后查询价格在这个范围内的产品",
    "搜索最新的比特币价格，并计算如果我有10个比特币，价值多少美元"
]

def test_agent_system(agent_system, queries):
    """测试代理系统的功能"""
    
    print("\n=== 代理系统功能测试 ===")
    
    results = []
    
    for query in queries:
        print(f"\n查询: {query}")
        
        start_time = time.time()
        response = agent_system.process_query(query)
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
        
        # 打印使用的工具
        if 'tools_used' in response:
            print("\n使用的工具:")
            for tool in response['tools_used']:
                print(f"- {tool}")
        
        results.append({
            "query": query,
            "response": response.get('response', ''),
            "thinking": response.get('thinking', ''),
            "steps": response.get('steps', []),
            "tools_used": response.get('tools_used', []),
            "processing_time": end_time - start_time
        })
    
    return results

def test_tool_chain_execution(agent_system, tool_chains):
    """测试工具链执行"""
    
    print("\n=== 工具链执行测试 ===")
    
    results = []
    
    for chain in tool_chains:
        print(f"\n测试工具链: {chain.name}")
        
        # 根据工具链类型准备测试参数
        if chain.name == "weather_summary":
            test_args = "北京"
            print(f"测试参数: {test_args}")
        elif chain.name == "search_translate":
            test_args = {"query": "人工智能最新进展", "from_lang": "中文", "to_lang": "英文"}
            print(f"测试参数: {json.dumps(test_args, ensure_ascii=False)}")
        elif chain.name == "conditional_weather":
            test_args = "上海"
            print(f"测试参数: {test_args}")
        else:
            test_args = {}
            print(f"测试参数: {test_args}")
        
        start_time = time.time()
        try:
            result = agent_system.tool_invoker.invoke_tool_chain(chain, test_args)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
            traceback.print_exc()
        end_time = time.time()
        
        if success:
            print(f"执行结果: {result}")
        else:
            print(f"执行错误: {error}")
        
        print(f"处理时间: {(end_time - start_time):.3f}秒")
        
        results.append({
            "chain_name": chain.name,
            "test_args": test_args,
            "result": result,
            "success": success,
            "error": error,
            "processing_time": end_time - start_time
        })
    
    # 计算成功率
    success_rate = sum(1 for r in results if r["success"]) / len(results) if results else 0
    print(f"\n工具链执行成功率: {success_rate:.2%}")
    
    return results

def test_agent_system_performance(agent_system, queries, iterations=3):
    """测试代理系统的性能"""
    
    print("\n=== 性能测试 ===")
    
    processing_times = []
    
    for _ in range(iterations):
        for query in queries:
            start_time = time.time()
            response = agent_system.process_query(query)
            end_time = time.time()
            
            processing_time = end_time - start_time
            processing_times.append(processing_time)
            
            print(f"查询: {query}")
            print(f"处理时间: {processing_time:.3f}秒")
    
    avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
    
    print(f"\n平均处理时间: {avg_processing_time:.3f}秒")
    
    return {
        "avg_processing_time": avg_processing_time,
        "processing_times": processing_times
    }

def test_caching_efficiency(agent_system, queries):
    """测试缓存效率"""
    
    print("\n=== 缓存效率测试 ===")
    
    # 清空缓存
    agent_system.tool_invoker.results_cache.clear()
    
    # 测试无缓存性能
    no_cache_times = []
    
    for query in queries:
        start_time = time.time()
        agent_system.process_query(query)
        end_time = time.time()
        no_cache_times.append(end_time - start_time)
    
    avg_no_cache_time = sum(no_cache_times) / len(no_cache_times) if no_cache_times else 0
    print(f"无缓存平均处理时间: {avg_no_cache_time:.3f}秒")
    
    # 测试有缓存性能
    cache_times = []
    
    for query in queries:
        start_time = time.time()
        agent_system.process_query(query)
        end_time = time.time()
        cache_times.append(end_time - start_time)
    
    avg_cache_time = sum(cache_times) / len(cache_times) if cache_times else 0
    print(f"有缓存平均处理时间: {avg_cache_time:.3f}秒")
    
    # 计算缓存加速比
    speedup = avg_no_cache_time / avg_cache_time if avg_cache_time > 0 else 0
    print(f"缓存加速比: {speedup:.2f}x")
    
    return {
        "avg_no_cache_time": avg_no_cache_time,
        "avg_cache_time": avg_cache_time,
        "speedup": speedup
    }

def test_error_recovery(agent_system):
    """测试错误恢复能力"""
    
    print("\n=== 错误恢复测试 ===")
    
    # 创建一个会失败的工具
    class FailingTool(BaseTool):
        def __init__(self, fail_probability=0.5):
            super().__init__(
                name="failing_tool",
                description="一个可能会失败的工具",
                usage="failing_tool(args)"
            )
            self.fail_probability = fail_probability
            
        def run(self, args):
            if random.random() < self.fail_probability:
                raise Exception("工具执行失败")
            return "工具执行成功"
    
    # 添加失败工具
    failing_tool = FailingTool(fail_probability=0.7)
    agent_system.tool_invoker.tools.append(failing_tool)
    
    # 测试查询
    test_queries = [
        "使用failing_tool执行操作",
        "先计算 100 + 200，然后使用failing_tool",
        "使用failing_tool，如果失败则查询北京天气"
    ]
    
    results = []
    
    for query in test_queries:
        print(f"\n查询: {query}")
        
        try:
            start_time = time.time()
            response = agent_system.process_query(query)
            end_time = time.time()
            
            print(f"响应: {response.get('response', '')}")
            print(f"处理时间: {(end_time - start_time):.3f}秒")
            
            # 检查是否有错误信息
            error = response.get('error', None)
            if error:
                print(f"错误: {error}")
                
            # 检查是否有恢复步骤
            if 'recovery_steps' in response:
                print("\n恢复步骤:")
                for i, step in enumerate(response['recovery_steps']):
                    print(f"步骤 {i+1}: {step.get('action', '')}")
                    print(f"  结果: {step.get('result', '')}")
            
            results.append({
                "query": query,
                "response": response.get('response', ''),
                "error": error,
                "recovery_steps": response.get('recovery_steps', []),
                "processing_time": end_time - start_time,
                "success": error is None
            })
            
            print("✓ 成功处理查询")
        except Exception as e:
            print(f"✗ 未捕获的错误: {e}")
            traceback.print_exc()
            
            results.append({
                "query": query,
                "error": str(e),
                "success": False
            })
    
    # 计算成功处理的查询比例
    success_count = sum(1 for r in results if r.get("success", False))
    total_count = len(results)
    
    print(f"\n成功处理查询的比例: {success_count}/{total_count} ({success_count/total_count:.2%})")
    
    # 移除失败工具
    agent_system.tool_invoker.tools = [t for t in agent_system.tool_invoker.tools if t.name != "failing_tool"]
    
    return results

def main():
    """主函数，运行所有测试"""
    
    print("=== 集成代理系统测试 ===")
    
    # 创建测试工具
    calculator = CalculatorTool()
    weather = WeatherTool()
    search = SearchTool()
    translate = TranslationTool()
    database = DatabaseTool()
    summarize = SummarizationTool()
    
    tools = [calculator, weather, search, translate, database, summarize]
    
    # 创建工具链
    weather_summary_chain = create_weather_summary_chain(tools)
    search_translate_chain = create_search_translate_chain(tools)
    conditional_weather_chain = create_conditional_weather_chain(tools)
    
    tool_chains = [weather_summary_chain, search_translate_chain, conditional_weather_chain]
    
    # 创建工具选择器
    tool_selector = OptimizedToolSelector(
        tools=tools + tool_chains,  # 包含工具和工具链
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
    
    # 注册工具链
    for chain in tool_chains:
        tool_invoker.register_tool_chain(chain)
    
    # 创建 ReAct Agent
    react_agent = ReActAgent(
        tool_invoker=tool_invoker,
        max_iterations=10,
        verbose=True
    )
    
    # 创建代理系统
    agent_system = AgentSystem(
        tools=tools,
        use_cache=True,
        cache_ttl=3600,
        max_iterations=10,
        confidence_threshold=0.6,
        verbose=True
    )
    
    # 注册工具链
    for chain in tool_chains:
        agent_system.register_tool_chain(chain)
    
    # 测试代理系统功能
    system_results = test_agent_system(agent_system, test_queries)
    
    # 测试工具链执行
    chain_results = test_tool_chain_execution(agent_system, tool_chains)
    
    # 测试缓存效率
    cache_results = test_caching_efficiency(agent_system, test_queries[:5])
    
    # 测试错误恢复
    error_results = test_error_recovery(agent_system)
    
    # 测试性能
    performance_results = test_agent_system_performance(agent_system, test_queries[:5])
    
    # 总结测试结果
    print("\n=== 测试结果总结 ===")
    
    # 系统功能测试结果
    avg_time = sum(r["processing_time"] for r in system_results) / len(system_results) if system_results else 0
    avg_steps = sum(len(r["steps"]) for r in system_results) / len(system_results) if system_results else 0
    print(f"平均查询处理时间: {avg_time:.3f}秒")
    print(f"平均执行步骤数: {avg_steps:.2f}")
    
    # 工具链测试结果
    chain_success_rate = sum(1 for r in chain_results if r["success"]) / len(chain_results) if chain_results else 0
    print(f"工具链执行成功率: {chain_success_rate:.2%}")
    
    # 缓存效率测试结果
    print(f"缓存加速比: {cache_results['speedup']:.2f}x")
    
    # 错误恢复测试结果
    error_success_rate = sum(1 for r in error_results if r.get("success", False)) / len(error_results) if error_results else 0
    print(f"错误恢复成功率: {error_success_rate:.2%}")
    
    # 性能测试结果
    print(f"性能测试平均处理时间: {performance_results['avg_processing_time']:.3f}秒")
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()
