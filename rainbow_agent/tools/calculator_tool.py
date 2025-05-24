"""
计算器工具
"""
from typing import Any
from .base import BaseTool
import re
import math

class CalculatorTool(BaseTool):
    """计算器工具，可以执行基本的数学计算"""
    
    def __init__(self):
        super().__init__(
            name="CalculatorTool",
            description="执行基本的数学计算，支持加减乘除、幂运算、三角函数等",
            usage="CalculatorTool <数学表达式>",
            version="1.0.2",
            author="Rainbow Team",
            tags=["计算", "数学", "基础工具"]
        )
        
    def run(self, args: Any) -> str:
        """
        执行数学计算
        
        Args:
            args: 数学表达式
            
        Returns:
            计算结果
        """
        try:
            expression = str(args).strip()
            if not expression:
                return "请提供要计算的数学表达式"
                
            # 安全检查，防止执行危险代码
            if self._is_safe_expression(expression):
                # 使用Python的eval函数计算表达式
                # 提供一些常用的数学函数
                math_context = {
                    'sin': math.sin,
                    'cos': math.cos,
                    'tan': math.tan,
                    'sqrt': math.sqrt,
                    'pow': math.pow,
                    'pi': math.pi,
                    'e': math.e,
                    'abs': abs,
                    'log': math.log,
                    'log10': math.log10,
                    'exp': math.exp,
                    'floor': math.floor,
                    'ceil': math.ceil,
                    'round': round
                }
                
                result = eval(expression, {"__builtins__": {}}, math_context)
                return f"计算结果: {result}"
            else:
                return "不安全的表达式，请仅使用数学运算符和函数"
                
        except Exception as e:
            return f"计算失败: {str(e)}"
            
    def _is_safe_expression(self, expression: str) -> bool:
        """
        检查表达式是否安全
        
        Args:
            expression: 要检查的表达式
            
        Returns:
            如果表达式安全则返回True，否则返回False
        """
        # 只允许数字、基本运算符和一些数学函数
        allowed_pattern = r'^[\d\s\+\-\*\/\(\)\.\,\^\%\=\<\>\!]*$'
        
        # 检查是否包含允许的数学函数
        allowed_functions = [
            'sin', 'cos', 'tan', 'sqrt', 'pow', 'abs', 
            'log', 'log10', 'exp', 'floor', 'ceil', 'round'
        ]
        
        # 移除允许的函数名，然后检查剩余部分
        expression_copy = expression
        for func in allowed_functions:
            expression_copy = expression_copy.replace(func, '')
            
        # 检查剩余表达式是否只包含允许的字符
        return bool(re.match(allowed_pattern, expression_copy))
