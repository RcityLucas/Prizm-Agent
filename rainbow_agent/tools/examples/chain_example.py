"""
工具链示例 - 展示如何使用工具链功能

本示例展示了如何创建和使用工具链，包括基本工具链、条件工具链和分支工具链。
"""
import json
import sys
import os

# 添加项目根目录到路径，以便导入模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from rainbow_agent.tools.base import BaseTool
from rainbow_agent.tools.tool_chain import ToolChain, ConditionalToolChain, BranchingToolChain
from rainbow_agent.tools.tool_invoker import ToolInvoker
from rainbow_agent.utils.logger import get_logger

logger = get_logger(__name__)

# 定义一些简单的工具用于示例
class TextProcessingTool(BaseTool):
    """文本处理工具，用于处理文本"""
    
    def __init__(self):
        super().__init__(
            name="text_processor",
            description="处理文本，例如转换大小写、计算长度等",
            usage="text_processor(text, operation)"
        )
        
    def run(self, args):
        try:
            # 解析参数
            if isinstance(args, str):
                try:
                    args_dict = json.loads(args)
                except:
                    # 如果不是JSON，尝试解析为文本和操作
                    parts = args.split(",", 1)
                    if len(parts) == 2:
                        text, operation = parts[0].strip(), parts[1].strip()
                        args_dict = {"text": text, "operation": operation}
                    else:
                        return "错误: 参数格式不正确，应为 'text, operation' 或 JSON 格式"
            else:
                args_dict = args
                
            text = args_dict.get("text", "")
            operation = args_dict.get("operation", "").lower()
            
            # 执行操作
            if operation == "uppercase":
                return text.upper()
            elif operation == "lowercase":
                return text.lower()
            elif operation == "length":
                return str(len(text))
            elif operation == "reverse":
                return text[::-1]
            else:
                return f"错误: 不支持的操作 '{operation}'"
                
        except Exception as e:
            return f"文本处理错误: {str(e)}"

class DataAnalysisTool(BaseTool):
    """数据分析工具，用于分析数据"""
    
    def __init__(self):
        super().__init__(
            name="data_analyzer",
            description="分析数据，例如计算平均值、最大值、最小值等",
            usage="data_analyzer(data, operation)"
        )
        
    def run(self, args):
        try:
            # 解析参数
            if isinstance(args, str):
                try:
                    args_dict = json.loads(args)
                except:
                    return "错误: 参数必须是JSON格式"
            else:
                args_dict = args
                
            data = args_dict.get("data", [])
            operation = args_dict.get("operation", "").lower()
            
            # 验证数据
            if not isinstance(data, list) or len(data) == 0:
                return "错误: 数据必须是非空列表"
                
            # 确保数据是数值型
            try:
                data = [float(x) for x in data]
            except:
                return "错误: 数据必须是数值型"
                
            # 执行操作
            if operation == "average":
                return str(sum(data) / len(data))
            elif operation == "max":
                return str(max(data))
            elif operation == "min":
                return str(min(data))
            elif operation == "sum":
                return str(sum(data))
            else:
                return f"错误: 不支持的操作 '{operation}'"
                
        except Exception as e:
            return f"数据分析错误: {str(e)}"

class FormatOutputTool(BaseTool):
    """格式化输出工具，用于格式化输出结果"""
    
    def __init__(self):
        super().__init__(
            name="format_output",
            description="格式化输出结果，例如转换为JSON、HTML等",
            usage="format_output(data, format)"
        )
        
    def run(self, args):
        try:
            # 解析参数
            if isinstance(args, str):
                try:
                    args_dict = json.loads(args)
                except:
                    # 如果不是JSON，尝试解析为数据和格式
                    parts = args.split(",", 1)
                    if len(parts) == 2:
                        data, format_type = parts[0].strip(), parts[1].strip()
                        args_dict = {"data": data, "format": format_type}
                    else:
                        return "错误: 参数格式不正确，应为 'data, format' 或 JSON 格式"
            else:
                args_dict = args
                
            data = args_dict.get("data", "")
            format_type = args_dict.get("format", "").lower()
            
            # 执行格式化
            if format_type == "json":
                try:
                    # 尝试解析数据为JSON
                    if isinstance(data, str):
                        try:
                            data_obj = json.loads(data)
                        except:
                            data_obj = {"result": data}
                    else:
                        data_obj = data
                        
                    return json.dumps(data_obj, ensure_ascii=False, indent=2)
                except:
                    return json.dumps({"result": str(data)}, ensure_ascii=False, indent=2)
            elif format_type == "html":
                return f"<div><pre>{data}</pre></div>"
            elif format_type == "markdown":
                return f"```\n{data}\n```"
            else:
                return f"错误: 不支持的格式 '{format_type}'"
                
        except Exception as e:
            return f"格式化输出错误: {str(e)}"

def main():
    """主函数，演示工具链的使用"""
    
    # 创建工具
    text_processor = TextProcessingTool()
    data_analyzer = DataAnalysisTool()
    format_output = FormatOutputTool()
    
    # 创建工具调用器
    invoker = ToolInvoker(
        tools=[text_processor, data_analyzer, format_output],
        use_cache=True
    )
    
    # 示例1: 基本工具链
    # 文本处理 -> 格式化输出
    basic_chain = ToolChain(
        name="text_processing_chain",
        description="处理文本并格式化输出",
        tools=[text_processor, format_output]
    )
    
    # 注册工具链
    invoker.register_tool_chain(basic_chain)
    
    # 示例2: 条件工具链
    # 只有当输入文本长度大于10时才执行
    def text_length_condition(input_data, context):
        if isinstance(input_data, str) and len(input_data) > 10:
            return True
        return False
        
    conditional_chain = ConditionalToolChain(
        name="conditional_text_chain",
        description="当文本长度大于10时处理文本",
        condition_func=text_length_condition,
        tools=[text_processor]
    )
    
    # 注册条件工具链
    invoker.register_tool_chain(conditional_chain)
    
    # 示例3: 分支工具链
    # 根据输入类型选择不同的处理路径
    def is_text_data(input_data, context):
        return isinstance(input_data, str)
        
    def is_numeric_data(input_data, context):
        try:
            if isinstance(input_data, list):
                # 尝试将列表中的所有元素转换为浮点数
                [float(x) for x in input_data]
                return True
            return False
        except:
            return False
    
    # 文本处理分支
    text_branch_chain = ToolChain(
        name="text_branch",
        description="处理文本数据",
        tools=[text_processor, format_output]
    )
    
    # 数据分析分支
    data_branch_chain = ToolChain(
        name="data_branch",
        description="分析数值数据",
        tools=[data_analyzer, format_output]
    )
    
    # 创建分支工具链
    branching_chain = BranchingToolChain(
        name="data_type_branch_chain",
        description="根据数据类型选择处理路径"
    )
    
    # 添加分支
    branching_chain.add_branch("text_branch", is_text_data, text_branch_chain)
    branching_chain.add_branch("numeric_branch", is_numeric_data, data_branch_chain)
    
    # 设置默认分支
    branching_chain.set_default_branch("text_branch")
    
    # 注册分支工具链
    invoker.register_tool_chain(branching_chain)
    
    # 执行工具链示例
    print("\n=== 基本工具链示例 ===")
    result1 = invoker.invoke_tool_chain(
        "text_processing_chain", 
        {"text": "Hello World", "operation": "uppercase"}
    )
    print(f"结果: {result1}")
    
    # 再次执行相同的工具链，应该会使用缓存
    print("\n=== 缓存示例 ===")
    result1_cached = invoker.invoke_tool_chain(
        "text_processing_chain", 
        {"text": "Hello World", "operation": "uppercase"}
    )
    print(f"缓存结果: {result1_cached}")
    
    print("\n=== 条件工具链示例 ===")
    # 满足条件的情况
    result2 = invoker.invoke_tool_chain(
        "conditional_text_chain", 
        "This is a long text that should be processed"
    )
    print(f"满足条件结果: {result2}")
    
    # 不满足条件的情况
    result3 = invoker.invoke_tool_chain(
        "conditional_text_chain", 
        "Short"
    )
    print(f"不满足条件结果: {result3}")
    
    print("\n=== 分支工具链示例 ===")
    # 文本分支
    result4 = invoker.invoke_tool_chain(
        "data_type_branch_chain", 
        "This is a text input"
    )
    print(f"文本分支结果: {result4}")
    
    # 数值分支
    result5 = invoker.invoke_tool_chain(
        "data_type_branch_chain", 
        [1, 2, 3, 4, 5]
    )
    print(f"数值分支结果: {result5}")

if __name__ == "__main__":
    main()
