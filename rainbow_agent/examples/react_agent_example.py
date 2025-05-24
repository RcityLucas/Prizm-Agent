"""
ReAct代理示例 - 展示如何使用ReAct代理和工具选择器

本示例展示了如何创建和使用ReAct代理，包括基本的思考-行动-观察循环和多步规划能力。
还展示了如何使用工具选择器优化工具选择过程。
"""
import json
import sys
import os
import time

# 添加项目根目录到路径，以便导入模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from rainbow_agent.core.react_agent import ReActAgent
from rainbow_agent.core.tool_selector import ToolSelector, SelectionStrategy
from rainbow_agent.tools.tool_invoker import ToolInvoker
from rainbow_agent.tools.base import BaseTool
from rainbow_agent.utils.logger import get_logger

logger = get_logger(__name__)

# 定义一些简单的工具用于示例
class WebSearchTool(BaseTool):
    """网络搜索工具，用于搜索网络信息"""
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description="搜索网络信息，查找相关内容",
            usage="web_search(query)"
        )
        
    def run(self, args):
        try:
            # 解析参数
            if isinstance(args, str):
                query = args.strip()
            else:
                query = args.get("query", "")
                
            # 模拟搜索结果
            time.sleep(1)  # 模拟网络延迟
            
            if "天气" in query:
                return "今天北京晴朗，气温20-28度，空气质量良好。"
            elif "新闻" in query:
                return "最新新闻：1. 科技创新大会在京召开；2. 新能源汽车销量持续增长；3. 国际合作项目取得重大进展。"
            elif "比特币" in query or "加密货币" in query:
                return "比特币当前价格约为55000美元，24小时涨幅2.3%。以太坊价格约为3200美元，24小时涨幅1.8%。"
            elif "人工智能" in query or "AI" in query:
                return "人工智能最新进展：1. 大型语言模型在医疗领域取得突破；2. AI辅助编程工具效率提升30%；3. 自动驾驶技术在复杂路况测试中表现优异。"
            else:
                return 
                
        except Exception as e:
            return f"搜索错误: {str(e)}"

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
            # 解析参数
            if isinstance(args, str):
                expression = args.strip()
            else:
                expression = args.get("expression", "")
                
            # 安全地执行计算（实际应用中应该使用更安全的方法）
            # 这里仅作为示例，使用eval有安全风险
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
            # 解析参数
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
            # 解析参数
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
            
            # 模拟翻译结果（实际应用中应该调用翻译API）
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

def demonstrate_tool_selector():
    """演示工具选择器的使用"""
    
    print("\n=== 工具选择器示例 ===")
    
    # 创建工具
    web_search = WebSearchTool()
    calculator = CalculatorTool()
    weather = WeatherTool()
    translate = TranslationTool()
    
    # 创建工具选择器
    selector = ToolSelector(
        tools=[web_search, calculator, weather, translate],
        strategy=SelectionStrategy.HYBRID,
        confidence_threshold=0.6,
        verbose=True
    )
    
    # 示例1: 明确的工具选择
    query1 = "计算 23 * 45 + 12"
    tool1, confidence1, reason1 = selector.select_tool(query1)
    print(f"\n查询: {query1}")
    print(f"选择工具: {tool1.name if tool1 else 'None'}")
    print(f"置信度: {confidence1:.2f}")
    print(f"理由: {reason1}")
    
    # 示例2: 模糊的工具选择
    query2 = "北京今天天气怎么样？"
    tool2, confidence2, reason2 = selector.select_tool(query2)
    print(f"\n查询: {query2}")
    print(f"选择工具: {tool2.name if tool2 else 'None'}")
    print(f"置信度: {confidence2:.2f}")
    print(f"理由: {reason2}")
    
    # 示例3: 多工具选择
    query3 = "帮我查询一下最新的人工智能新闻"
    tools3 = selector.select_tools(query3, top_k=2)
    print(f"\n查询: {query3}")
    print("选择的工具:")
    for tool, confidence, reason in tools3:
        print(f"- {tool.name}: 置信度 {confidence:.2f}, 理由: {reason}")
    
    # 示例4: 没有明确工具的查询
    query4 = "你今天感觉怎么样？"
    tool4, confidence4, reason4 = selector.select_tool(query4)
    print(f"\n查询: {query4}")
    print(f"选择工具: {tool4.name if tool4 else 'None'}")
    print(f"置信度: {confidence4:.2f}")
    print(f"理由: {reason4}")

def demonstrate_react_agent():
    """演示ReAct代理的使用"""
    
    print("\n=== ReAct代理示例 ===")
    
    # 创建工具
    web_search = WebSearchTool()
    calculator = CalculatorTool()
    weather = WeatherTool()
    translate = TranslationTool()
    
    # 创建工具调用器
    invoker = ToolInvoker(
        tools=[web_search, calculator, weather, translate],
        use_cache=True
    )
    
    # 创建ReAct代理
    agent = ReActAgent(
        tool_invoker=invoker,
        max_iterations=5,
        verbose=True
    )
    
    # 示例1: 简单查询
    query1 = "北京今天天气怎么样？"
    print(f"\n查询: {query1}")
    result1 = agent.run(query1)
    print(f"回答: {result1['answer']}")
    print(f"执行了 {len(result1['actions'])} 个行动，{result1['iterations']} 次迭代")
    
    # 示例2: 需要计算的查询
    query2 = "计算 (123 + 456) * 7"
    print(f"\n查询: {query2}")
    result2 = agent.run(query2)
    print(f"回答: {result2['answer']}")
    print(f"执行了 {len(result2['actions'])} 个行动，{result2['iterations']} 次迭代")
    
    # 示例3: 多步规划查询
    query3 = "请帮我查询北京和上海的天气，然后比较哪个城市更适合户外活动"
    print(f"\n查询: {query3}")
    result3 = agent.run(query3)
    print(f"回答: {result3['answer']}")
    if 'plan' in result3:
        print(f"使用了规划，共 {len(result3['step_results'])} 个步骤")
    else:
        print(f"执行了 {len(result3['actions'])} 个行动，{result3['iterations']} 次迭代")

def main():
    """主函数，演示工具选择器和ReAct代理的使用"""
    
    # 演示工具选择器
    demonstrate_tool_selector()
    
    # 演示ReAct代理
    demonstrate_react_agent()

if __name__ == "__main__":
    main()
