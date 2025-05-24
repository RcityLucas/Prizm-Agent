"""
优化工具选择器测试 - 测试优化工具选择器的性能和准确性

本脚本测试优化工具选择器的各种功能，包括缓存、规则选择、LLM选择和集成选择，
并与原始工具选择器进行性能和准确性比较。
"""
import sys
import os
import time
import json
from typing import Dict, Any, List
import traceback
import random

# 添加项目根目录到路径，以便导入模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from rainbow_agent.core.optimized_tool_selector import OptimizedToolSelector, SelectionStrategy
from rainbow_agent.core.tool_selector import ToolSelector
from rainbow_agent.tools.base import BaseTool
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

# 测试用例
test_queries = [
    {"query": "计算 123 + 456 * 2", "expected_tool": "calculator"},
    {"query": "北京今天天气怎么样？", "expected_tool": "weather"},
    {"query": "搜索关于比特币的最新信息", "expected_tool": "search"},
    {"query": "把'人工智能'翻译成英文", "expected_tool": "translate"},
    {"query": "最近天气如何？", "expected_tool": "weather"},
    {"query": "23 * 45 等于多少？", "expected_tool": "calculator"},
    {"query": "查询上海的天气预报", "expected_tool": "weather"},
    {"query": "帮我搜索一下关于人工智能的最新进展", "expected_tool": "search"},
    {"query": "将 'hello world' 翻译成中文", "expected_tool": "translate"},
    {"query": "计算圆周率乘以10", "expected_tool": "calculator"}
]

# 模糊查询测试用例
fuzzy_test_queries = [
    {"query": "今天外面冷不冷？", "expected_tool": "weather"},
    {"query": "帮我算一下这个问题", "expected_tool": "calculator"},
    {"query": "找一下关于这个话题的资料", "expected_tool": "search"},
    {"query": "这句话用英语怎么说", "expected_tool": "translate"},
    {"query": "温度多少度？", "expected_tool": "weather"},
    {"query": "10加20是多少", "expected_tool": "calculator"},
    {"query": "查一下最新消息", "expected_tool": "search"},
    {"query": "这个词的英文是什么", "expected_tool": "translate"}
]

# 无关查询测试用例
irrelevant_test_queries = [
    {"query": "你好，今天过得怎么样？", "expected_tool": None},
    {"query": "讲个笑话", "expected_tool": None},
    {"query": "你是谁开发的？", "expected_tool": None},
    {"query": "彩虹城是什么项目？", "expected_tool": None}
]

def test_cache_performance(selector, queries, iterations=5):
    """测试缓存性能"""
    
    print("\n=== 缓存性能测试 ===")
    
    # 预热
    for query_info in queries:
        selector.select_tool(query_info["query"])
    
    # 测试无缓存性能
    selector.selection_cache.cache.clear()  # 清空缓存
    
    no_cache_times = []
    for _ in range(iterations):
        for query_info in queries:
            start_time = time.time()
            selector.select_tool(query_info["query"])
            end_time = time.time()
            no_cache_times.append(end_time - start_time)
    
    avg_no_cache_time = sum(no_cache_times) / len(no_cache_times)
    print(f"无缓存平均查询时间: {avg_no_cache_time:.6f}秒")
    
    # 测试有缓存性能
    cache_times = []
    for _ in range(iterations):
        for query_info in queries:
            start_time = time.time()
            selector.select_tool(query_info["query"])
            end_time = time.time()
            cache_times.append(end_time - start_time)
    
    avg_cache_time = sum(cache_times) / len(cache_times)
    print(f"有缓存平均查询时间: {avg_cache_time:.6f}秒")
    print(f"缓存加速比: {avg_no_cache_time / avg_cache_time:.2f}x")
    
    return {
        "avg_no_cache_time": avg_no_cache_time,
        "avg_cache_time": avg_cache_time,
        "speedup": avg_no_cache_time / avg_cache_time
    }

def test_selection_accuracy(selector, queries):
    """测试选择准确性"""
    
    print("\n=== 选择准确性测试 ===")
    
    correct = 0
    total = 0
    results = []
    
    for query_info in queries:
        query = query_info["query"]
        expected_tool = query_info["expected_tool"]
        
        print(f"\n查询: {query}")
        print(f"预期工具: {expected_tool}")
        
        start_time = time.time()
        tool, confidence, reason = selector.select_tool(query)
        end_time = time.time()
        
        selected_tool_name = tool.name if tool else None
        print(f"选择工具: {selected_tool_name}")
        print(f"置信度: {confidence:.2f}")
        print(f"理由: {reason}")
        print(f"处理时间: {(end_time - start_time):.6f}秒")
        
        if (expected_tool is None and selected_tool_name is None) or (expected_tool == selected_tool_name):
            correct += 1
            print("✓ 正确")
        else:
            print("✗ 错误")
        
        total += 1
        
        results.append({
            "query": query,
            "expected_tool": expected_tool,
            "selected_tool": selected_tool_name,
            "confidence": confidence,
            "reason": reason,
            "processing_time": end_time - start_time,
            "correct": (expected_tool is None and selected_tool_name is None) or (expected_tool == selected_tool_name)
        })
    
    accuracy = correct / total if total > 0 else 0
    print(f"\n总准确率: {accuracy:.2%} ({correct}/{total})")
    
    return {
        "accuracy": accuracy,
        "correct": correct,
        "total": total,
        "results": results
    }

def test_multi_selection(selector, queries, top_k=2):
    """测试多工具选择"""
    
    print(f"\n=== 多工具选择测试 (top_k={top_k}) ===")
    
    results = []
    
    for query_info in queries:
        query = query_info["query"]
        expected_tool = query_info["expected_tool"]
        
        print(f"\n查询: {query}")
        print(f"预期首选工具: {expected_tool}")
        
        start_time = time.time()
        selected_tools = selector.select_tools(query, top_k=top_k)
        end_time = time.time()
        
        print(f"选择的工具:")
        expected_in_results = False
        for i, (tool, confidence, reason) in enumerate(selected_tools):
            print(f"{i+1}. {tool.name}: 置信度 {confidence:.2f}")
            print(f"   理由: {reason}")
            
            if tool.name == expected_tool:
                expected_in_results = True
        
        print(f"处理时间: {(end_time - start_time):.6f}秒")
        
        if expected_in_results:
            print("✓ 预期工具在结果中")
        elif expected_tool is None:
            print("✓ 正确（无预期工具）")
        else:
            print("✗ 预期工具不在结果中")
        
        results.append({
            "query": query,
            "expected_tool": expected_tool,
            "selected_tools": [(tool.name, confidence) for tool, confidence, reason in selected_tools],
            "processing_time": end_time - start_time,
            "expected_in_results": expected_in_results or expected_tool is None
        })
    
    # 计算有多少查询的预期工具在结果中
    correct = sum(1 for r in results if r["expected_in_results"])
    total = len(results)
    recall = correct / total if total > 0 else 0
    
    print(f"\n召回率: {recall:.2%} ({correct}/{total})")
    
    return {
        "recall": recall,
        "correct": correct,
        "total": total,
        "results": results
    }

def compare_selectors(optimized_selector, original_selector, queries):
    """比较优化选择器和原始选择器"""
    
    print("\n=== 选择器性能比较 ===")
    
    # 清空缓存
    optimized_selector.selection_cache.cache.clear()
    
    optimized_times = []
    original_times = []
    optimized_correct = 0
    original_correct = 0
    total = 0
    
    for query_info in queries:
        query = query_info["query"]
        expected_tool = query_info["expected_tool"]
        
        # 测试优化选择器
        start_time = time.time()
        opt_tool, opt_confidence, opt_reason = optimized_selector.select_tool(query)
        opt_time = time.time() - start_time
        optimized_times.append(opt_time)
        
        opt_tool_name = opt_tool.name if opt_tool else None
        if (expected_tool is None and opt_tool_name is None) or (expected_tool == opt_tool_name):
            optimized_correct += 1
        
        # 测试原始选择器
        start_time = time.time()
        orig_tool, orig_confidence, orig_reason = original_selector.select_tool(query)
        orig_time = time.time() - start_time
        original_times.append(orig_time)
        
        orig_tool_name = orig_tool.name if orig_tool else None
        if (expected_tool is None and orig_tool_name is None) or (expected_tool == orig_tool_name):
            original_correct += 1
        
        total += 1
        
        print(f"\n查询: {query}")
        print(f"预期工具: {expected_tool}")
        print(f"优化选择器: {opt_tool_name}, 置信度: {opt_confidence:.2f}, 时间: {opt_time:.6f}秒")
        print(f"原始选择器: {orig_tool_name}, 置信度: {orig_confidence:.2f}, 时间: {orig_time:.6f}秒")
    
    # 计算平均时间和准确率
    avg_optimized_time = sum(optimized_times) / len(optimized_times) if optimized_times else 0
    avg_original_time = sum(original_times) / len(original_times) if original_times else 0
    optimized_accuracy = optimized_correct / total if total > 0 else 0
    original_accuracy = original_correct / total if total > 0 else 0
    
    print(f"\n优化选择器平均时间: {avg_optimized_time:.6f}秒")
    print(f"原始选择器平均时间: {avg_original_time:.6f}秒")
    print(f"性能提升: {avg_original_time / avg_optimized_time:.2f}x")
    print(f"优化选择器准确率: {optimized_accuracy:.2%} ({optimized_correct}/{total})")
    print(f"原始选择器准确率: {original_accuracy:.2%} ({original_correct}/{total})")
    
    return {
        "avg_optimized_time": avg_optimized_time,
        "avg_original_time": avg_original_time,
        "speedup": avg_original_time / avg_optimized_time,
        "optimized_accuracy": optimized_accuracy,
        "original_accuracy": original_accuracy
    }

def test_strategy_comparison(tools, queries):
    """比较不同选择策略"""
    
    print("\n=== 策略比较测试 ===")
    
    strategies = [
        SelectionStrategy.RULE_BASED,
        SelectionStrategy.LLM_BASED,
        SelectionStrategy.CONFIDENCE,
        SelectionStrategy.HYBRID,
        SelectionStrategy.ENSEMBLE
    ]
    
    results = {}
    
    for strategy in strategies:
        print(f"\n测试策略: {strategy.value}")
        
        selector = OptimizedToolSelector(
            tools=tools,
            strategy=strategy,
            confidence_threshold=0.6,
            cache_capacity=100,
            verbose=True
        )
        
        # 清空缓存
        selector.selection_cache.cache.clear()
        
        strategy_times = []
        strategy_correct = 0
        total = 0
        
        for query_info in queries:
            query = query_info["query"]
            expected_tool = query_info["expected_tool"]
            
            start_time = time.time()
            tool, confidence, reason = selector.select_tool(query)
            end_time = time.time()
            
            tool_name = tool.name if tool else None
            if (expected_tool is None and tool_name is None) or (expected_tool == tool_name):
                strategy_correct += 1
            
            strategy_times.append(end_time - start_time)
            total += 1
            
            print(f"查询: {query}")
            print(f"选择工具: {tool_name}, 置信度: {confidence:.2f}")
            print(f"处理时间: {(end_time - start_time):.6f}秒")
        
        avg_time = sum(strategy_times) / len(strategy_times) if strategy_times else 0
        accuracy = strategy_correct / total if total > 0 else 0
        
        print(f"策略 {strategy.value} 平均时间: {avg_time:.6f}秒")
        print(f"策略 {strategy.value} 准确率: {accuracy:.2%} ({strategy_correct}/{total})")
        
        results[strategy.value] = {
            "avg_time": avg_time,
            "accuracy": accuracy,
            "correct": strategy_correct,
            "total": total
        }
    
    return results

def test_error_handling(selector):
    """测试错误处理"""
    
    print("\n=== 错误处理测试 ===")
    
    # 测试无效查询
    invalid_queries = [
        "",  # 空查询
        "   ",  # 只有空格
        "?",  # 只有标点符号
        "a" * 1000,  # 非常长的查询
        "<script>alert('XSS')</script>"  # 潜在的XSS攻击
    ]
    
    for query in invalid_queries:
        print(f"\n测试无效查询: '{query}'")
        
        try:
            tool, confidence, reason = selector.select_tool(query)
            print(f"处理结果: 工具={tool.name if tool else None}, 置信度={confidence:.2f}")
            print(f"理由: {reason}")
            print("✓ 成功处理无效查询")
        except Exception as e:
            print(f"✗ 错误: {e}")
            traceback.print_exc()
    
    # 测试无效上下文
    invalid_contexts = [
        {"suggested_tool": "不存在的工具"},
        {"domain": 123},  # 非字符串域
        {"previous_tools": "不是列表"}
    ]
    
    for context in invalid_contexts:
        print(f"\n测试无效上下文: {context}")
        
        try:
            tool, confidence, reason = selector.select_tool("测试查询", context)
            print(f"处理结果: 工具={tool.name if tool else None}, 置信度={confidence:.2f}")
            print(f"理由: {reason}")
            print("✓ 成功处理无效上下文")
        except Exception as e:
            print(f"✗ 错误: {e}")
            traceback.print_exc()
    
    return "错误处理测试完成"

def main():
    """主函数，运行所有测试"""
    
    print("=== 优化工具选择器测试 ===")
    
    # 创建测试工具
    calculator = CalculatorTool()
    weather = WeatherTool()
    search = SearchTool()
    translate = TranslationTool()
    
    tools = [calculator, weather, search, translate]
    
    # 创建优化工具选择器
    optimized_selector = OptimizedToolSelector(
        tools=tools,
        strategy=SelectionStrategy.HYBRID,
        confidence_threshold=0.6,
        cache_capacity=100,
        cache_ttl=3600,
        use_batching=True,
        batch_size=5,
        timeout=10,
        verbose=True
    )
    
    # 创建原始工具选择器（用于比较）
    original_selector = ToolSelector(
        tools=tools,
        strategy=SelectionStrategy.HYBRID,
        confidence_threshold=0.6,
        verbose=True
    )
    
    # 测试缓存性能
    cache_results = test_cache_performance(optimized_selector, test_queries)
    
    # 测试选择准确性
    print("\n--- 明确查询测试 ---")
    clear_results = test_selection_accuracy(optimized_selector, test_queries)
    
    print("\n--- 模糊查询测试 ---")
    fuzzy_results = test_selection_accuracy(optimized_selector, fuzzy_test_queries)
    
    print("\n--- 无关查询测试 ---")
    irrelevant_results = test_selection_accuracy(optimized_selector, irrelevant_test_queries)
    
    # 测试多工具选择
    multi_results = test_multi_selection(optimized_selector, test_queries)
    
    # 比较优化选择器和原始选择器
    comparison_results = compare_selectors(optimized_selector, original_selector, test_queries + fuzzy_test_queries)
    
    # 测试不同策略
    strategy_results = test_strategy_comparison(tools, test_queries[:5])  # 使用部分查询以节省时间
    
    # 测试错误处理
    error_handling_results = test_error_handling(optimized_selector)
    
    # 总结测试结果
    print("\n=== 测试结果总结 ===")
    print(f"缓存加速比: {cache_results['speedup']:.2f}x")
    print(f"明确查询准确率: {clear_results['accuracy']:.2%}")
    print(f"模糊查询准确率: {fuzzy_results['accuracy']:.2%}")
    print(f"无关查询准确率: {irrelevant_results['accuracy']:.2%}")
    print(f"多工具选择召回率: {multi_results['recall']:.2%}")
    print(f"优化选择器vs原始选择器性能提升: {comparison_results['speedup']:.2f}x")
    print(f"优化选择器vs原始选择器准确率提升: {(comparison_results['optimized_accuracy'] - comparison_results['original_accuracy']) * 100:.2f}%")
    
    # 输出最佳策略
    best_strategy = max(strategy_results.items(), key=lambda x: x[1]['accuracy'])
    print(f"最佳策略: {best_strategy[0]}, 准确率: {best_strategy[1]['accuracy']:.2%}")
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()
