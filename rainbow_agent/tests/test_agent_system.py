"""
代理系统测试 - 测试和优化新实现的代理能力

本脚本测试ReAct代理、工具选择器和工具链的功能，
并提供性能指标和优化建议。
"""
import sys
import os
import time
import json
from typing import Dict, Any, List
import traceback

# 添加项目根目录到路径，以便导入模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from rainbow_agent.core.agent_system import AgentSystem
from rainbow_agent.core.tool_selector import SelectionStrategy
from rainbow_agent.tools.base import BaseTool
from rainbow_agent.tools.tool_chain import ToolChain, ConditionalToolChain, BranchingToolChain
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
                return "关于{query}的搜索结果：找到约100万条相关信息，包括新闻、学术论文、社交媒体讨论等。"
                
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

# 测试用例
test_cases = [
    {
        "name": "简单计算查询",
        "query": "计算 123 + 456 * 2",
        "expected_tool": "calculator",
        "use_react": False
    },
    {
        "name": "天气查询",
        "query": "北京今天天气怎么样？",
        "expected_tool": "weather",
        "use_react": False
    },
    {
        "name": "搜索查询",
        "query": "告诉我关于比特币的最新信息",
        "expected_tool": "search",
        "use_react": False
    },
    {
        "name": "翻译查询",
        "query": "把'人工智能'翻译成英文",
        "expected_tool": "translate",
        "use_react": False
    },
    {
        "name": "模糊查询",
        "query": "最近天气如何？",
        "expected_tool": "weather",
        "use_react": False
    },
    {
        "name": "复杂查询_React",
        "query": "请帮我查询北京和上海的天气，然后告诉我哪个城市更适合户外活动",
        "expected_tool": None,  # 使用ReAct模式，可能会调用多个工具
        "use_react": True
    },
    {
        "name": "计算_React",
        "query": "计算 (123 + 456) * 7 - 42 的结果是多少？",
        "expected_tool": None,  # 使用ReAct模式
        "use_react": True
    },
    {
        "name": "多步查询_React",
        "query": "先查询北京的天气，然后计算今天的最高温度减去最低温度的差值",
        "expected_tool": None,  # 使用ReAct模式，需要多步规划
        "use_react": True
    }
]

# 工具链测试用例
def create_weather_calculator_chain(agent_system):
    """创建天气计算工具链"""
    
    # 创建工具链
    chain = ToolChain(
        name="weather_calculator_chain",
        description="查询天气并进行温度计算",
        tools=[agent_system.tool_invoker.tools_by_name["weather"], 
               agent_system.tool_invoker.tools_by_name["calculator"]]
    )
    
    # 注册工具链
    agent_system.register_tool_chain(chain)
    
    return chain

def create_conditional_weather_chain(agent_system):
    """创建条件天气工具链"""
    
    # 定义条件函数
    def is_beijing_query(input_data, context):
        if isinstance(input_data, str) and "北京" in input_data:
            return True
        return False
    
    # 创建条件工具链
    chain = ConditionalToolChain(
        name="conditional_weather_chain",
        description="当查询北京天气时执行",
        condition_func=is_beijing_query,
        tools=[agent_system.tool_invoker.tools_by_name["weather"]]
    )
    
    # 注册工具链
    agent_system.register_tool_chain(chain)
    
    return chain

def create_branching_chain(agent_system):
    """创建分支工具链"""
    
    # 定义分支条件
    def is_weather_query(input_data, context):
        if isinstance(input_data, str) and ("天气" in input_data or "气温" in input_data):
            return True
        return False
    
    def is_calculation_query(input_data, context):
        if isinstance(input_data, str) and ("计算" in input_data or "+" in input_data or "-" in input_data or "*" in input_data or "/" in input_data):
            return True
        return False
    
    # 创建分支工具链
    branching_chain = BranchingToolChain(
        name="query_type_branch_chain",
        description="根据查询类型选择处理路径"
    )
    
    # 添加分支
    branching_chain.add_branch(
        "weather_branch", 
        is_weather_query, 
        ToolChain(
            name="weather_branch_chain",
            description="处理天气查询",
            tools=[agent_system.tool_invoker.tools_by_name["weather"]]
        )
    )
    
    branching_chain.add_branch(
        "calculator_branch", 
        is_calculation_query, 
        ToolChain(
            name="calculator_branch_chain",
            description="处理计算查询",
            tools=[agent_system.tool_invoker.tools_by_name["calculator"]]
        )
    )
    
    # 设置默认分支
    branching_chain.set_default_branch("weather_branch")
    
    # 注册分支工具链
    agent_system.register_tool_chain(branching_chain)
    
    return branching_chain

# 工具链测试用例
tool_chain_test_cases = [
    {
        "name": "基本工具链测试",
        "chain_name": "weather_calculator_chain",
        "query": "北京的气温差是多少？",
        "expected_result_contains": ["北京", "气温", "计算"]
    },
    {
        "name": "条件工具链测试_满足条件",
        "chain_name": "conditional_weather_chain",
        "query": "北京今天天气如何？",
        "expected_result_contains": ["北京", "天气"]
    },
    {
        "name": "条件工具链测试_不满足条件",
        "chain_name": "conditional_weather_chain",
        "query": "上海今天天气如何？",
        "expected_result_contains": ["条件不满足"]
    },
    {
        "name": "分支工具链测试_天气分支",
        "chain_name": "query_type_branch_chain",
        "query": "今天天气怎么样？",
        "expected_result_contains": ["天气", "weather_branch"]
    },
    {
        "name": "分支工具链测试_计算分支",
        "chain_name": "query_type_branch_chain",
        "query": "计算 10 + 20",
        "expected_result_contains": ["计算", "calculator_branch"]
    }
]

def run_tool_tests(agent_system):
    """运行工具测试"""
    
    print("\n=== 工具选择和调用测试 ===")
    
    results = []
    
    for test_case in test_cases:
        print(f"\n测试: {test_case['name']}")
        print(f"查询: {test_case['query']}")
        
        start_time = time.time()
        
        try:
            # 处理查询
            result = agent_system.process_query(
                test_case["query"], 
                use_react=test_case["use_react"]
            )
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 检查结果
            if test_case["use_react"]:
                print(f"ReAct处理结果: {result['answer'][:100]}..." if len(result['answer']) > 100 else result['answer'])
                if "actions" in result:
                    print(f"执行了 {len(result['actions'])} 个行动")
                if "plan" in result:
                    print(f"使用了规划，共 {len(result['step_results'])} 个步骤")
            else:
                print(f"工具: {result.get('tool_used', 'None')}")
                print(f"结果: {result['answer'][:100]}..." if len(result['answer']) > 100 else result['answer'])
                
                # 检查是否使用了预期的工具
                if test_case["expected_tool"] and result.get("tool_used") != test_case["expected_tool"]:
                    print(f"警告: 预期使用工具 {test_case['expected_tool']}，实际使用了 {result.get('tool_used', 'None')}")
            
            print(f"处理时间: {processing_time:.3f}秒")
            
            # 记录结果
            results.append({
                "test_case": test_case["name"],
                "query": test_case["query"],
                "success": True,
                "processing_time": processing_time,
                "result": result
            })
            
        except Exception as e:
            print(f"错误: {e}")
            traceback.print_exc()
            
            # 记录错误
            results.append({
                "test_case": test_case["name"],
                "query": test_case["query"],
                "success": False,
                "error": str(e)
            })
    
    return results

def run_tool_chain_tests(agent_system):
    """运行工具链测试"""
    
    print("\n=== 工具链测试 ===")
    
    # 创建测试工具链
    create_weather_calculator_chain(agent_system)
    create_conditional_weather_chain(agent_system)
    create_branching_chain(agent_system)
    
    results = []
    
    for test_case in tool_chain_test_cases:
        print(f"\n测试: {test_case['name']}")
        print(f"工具链: {test_case['chain_name']}")
        print(f"查询: {test_case['query']}")
        
        start_time = time.time()
        
        try:
            # 执行工具链
            result = agent_system.tool_invoker.invoke_tool_chain(
                test_case["chain_name"],
                test_case["query"]
            )
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 检查结果
            result_str = str(result)
            print(f"结果: {result_str[:100]}..." if len(result_str) > 100 else result_str)
            
            # 检查结果是否包含预期内容
            all_expected_found = True
            for expected in test_case["expected_result_contains"]:
                if expected not in result_str:
                    print(f"警告: 结果中未找到预期内容 '{expected}'")
                    all_expected_found = False
            
            if all_expected_found:
                print("所有预期内容均已找到")
            
            print(f"处理时间: {processing_time:.3f}秒")
            
            # 记录结果
            results.append({
                "test_case": test_case["name"],
                "chain_name": test_case["chain_name"],
                "query": test_case["query"],
                "success": True,
                "processing_time": processing_time,
                "result": result,
                "all_expected_found": all_expected_found
            })
            
        except Exception as e:
            print(f"错误: {e}")
            traceback.print_exc()
            
            # 记录错误
            results.append({
                "test_case": test_case["name"],
                "chain_name": test_case["chain_name"],
                "query": test_case["query"],
                "success": False,
                "error": str(e)
            })
    
    return results

def run_tool_selector_tests(agent_system):
    """运行工具选择器测试"""
    
    print("\n=== 工具选择器测试 ===")
    
    test_queries = [
        "计算 123 + 456",
        "北京今天天气怎么样？",
        "搜索关于人工智能的最新信息",
        "翻译 'hello world' 到中文",
        "今天气温如何？",
        "帮我做个数学题：23 * 45 是多少？",
        "你能告诉我上海的天气预报吗？",
        "这个问题没有明确的工具需求"
    ]
    
    results = []
    
    for query in test_queries:
        print(f"\n查询: {query}")
        
        start_time = time.time()
        
        try:
            # 选择工具
            selected_tools = agent_system.select_best_tools(query, top_k=2)
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 显示结果
            print("选择的工具:")
            for tool_info in selected_tools:
                print(f"- {tool_info['tool_name']}: 置信度 {tool_info['confidence']:.2f}")
                print(f"  理由: {tool_info['reason']}")
            
            print(f"处理时间: {processing_time:.3f}秒")
            
            # 记录结果
            results.append({
                "query": query,
                "success": True,
                "processing_time": processing_time,
                "selected_tools": selected_tools
            })
            
        except Exception as e:
            print(f"错误: {e}")
            traceback.print_exc()
            
            # 记录错误
            results.append({
                "query": query,
                "success": False,
                "error": str(e)
            })
    
    return results

def analyze_results(tool_results, chain_results, selector_results):
    """分析测试结果，提供优化建议"""
    
    print("\n=== 测试结果分析 ===")
    
    # 工具测试分析
    tool_success_count = sum(1 for r in tool_results if r["success"])
    tool_success_rate = tool_success_count / len(tool_results) if tool_results else 0
    tool_avg_time = sum(r["processing_time"] for r in tool_results if r["success"] and "processing_time" in r) / tool_success_count if tool_success_count else 0
    
    print(f"工具测试成功率: {tool_success_rate:.2%}")
    print(f"工具测试平均处理时间: {tool_avg_time:.3f}秒")
    
    # 工具链测试分析
    chain_success_count = sum(1 for r in chain_results if r["success"])
    chain_success_rate = chain_success_count / len(chain_results) if chain_results else 0
    chain_avg_time = sum(r["processing_time"] for r in chain_results if r["success"] and "processing_time" in r) / chain_success_count if chain_success_count else 0
    
    print(f"工具链测试成功率: {chain_success_rate:.2%}")
    print(f"工具链测试平均处理时间: {chain_avg_time:.3f}秒")
    
    # 工具选择器测试分析
    selector_success_count = sum(1 for r in selector_results if r["success"])
    selector_success_rate = selector_success_count / len(selector_results) if selector_results else 0
    selector_avg_time = sum(r["processing_time"] for r in selector_results if r["success"] and "processing_time" in r) / selector_success_count if selector_success_count else 0
    
    print(f"工具选择器测试成功率: {selector_success_rate:.2%}")
    print(f"工具选择器测试平均处理时间: {selector_avg_time:.3f}秒")
    
    # 优化建议
    print("\n优化建议:")
    
    # 基于处理时间的建议
    if tool_avg_time > 2.0:
        print("- 工具调用处理时间较长，考虑优化工具执行效率或增加缓存")
    
    if chain_avg_time > 3.0:
        print("- 工具链执行时间较长，考虑减少工具链中的工具数量或优化工具执行")
    
    if selector_avg_time > 1.0:
        print("- 工具选择器处理时间较长，考虑使用更轻量级的选择策略或优化LLM调用")
    
    # 基于成功率的建议
    if tool_success_rate < 0.9:
        print("- 工具测试成功率较低，需要改进错误处理和参数解析")
    
    if chain_success_rate < 0.9:
        print("- 工具链测试成功率较低，需要改进工具链执行逻辑和错误处理")
    
    if selector_success_rate < 0.9:
        print("- 工具选择器测试成功率较低，需要改进选择算法和错误处理")
    
    # 其他建议
    react_results = [r for r in tool_results if r["success"] and r.get("result", {}).get("use_react", False)]
    if react_results:
        react_avg_iterations = sum(r.get("result", {}).get("iterations", 0) for r in react_results) / len(react_results)
        if react_avg_iterations > 3:
            print(f"- ReAct代理平均迭代次数为 {react_avg_iterations:.1f}，考虑优化思考-行动-观察循环效率")
    
    # 内存使用建议
    print("- 考虑实现LRU缓存策略，限制缓存大小，避免内存占用过高")
    print("- 对于大型结果，考虑实现结果截断或分页机制")
    
    # 并行处理建议
    print("- 对于独立的工具调用，考虑实现并行执行以提高性能")
    
    return {
        "tool_success_rate": tool_success_rate,
        "tool_avg_time": tool_avg_time,
        "chain_success_rate": chain_success_rate,
        "chain_avg_time": chain_avg_time,
        "selector_success_rate": selector_success_rate,
        "selector_avg_time": selector_avg_time
    }

def main():
    """主函数，运行所有测试"""
    
    print("=== 彩虹城AI Agent代理系统测试 ===")
    
    # 创建测试工具
    calculator = CalculatorTool()
    weather = WeatherTool()
    search = SearchTool()
    translate = TranslationTool()
    
    # 创建代理系统
    agent_system = AgentSystem(
        tools=[calculator, weather, search, translate],
        agent_model="gpt-4",
        decision_model="gpt-3.5-turbo",
        tool_selection_strategy=SelectionStrategy.HYBRID,
        use_cache=True,
        cache_ttl=3600,
        max_iterations=5,
        confidence_threshold=0.6,
        verbose=True
    )
    
    # 运行工具测试
    tool_results = run_tool_tests(agent_system)
    
    # 运行工具链测试
    chain_results = run_tool_chain_tests(agent_system)
    
    # 运行工具选择器测试
    selector_results = run_tool_selector_tests(agent_system)
    
    # 分析结果
    analysis = analyze_results(tool_results, chain_results, selector_results)
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()
