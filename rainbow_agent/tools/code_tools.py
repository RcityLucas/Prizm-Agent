"""
代码处理工具

提供代码生成、分析和执行功能
"""
import os
import subprocess
import tempfile
from typing import Dict, Any, List, Optional, Union
import time

from .base import BaseTool
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CodeExecutionTool(BaseTool):
    """
    代码执行工具
    
    执行Python代码片段并返回结果
    """
    category = "代码工具"
    
    def __init__(self, 
                 workspace_dir: Optional[str] = None,
                 allowed_modules: Optional[List[str]] = None,
                 timeout: int = 10):
        """
        初始化代码执行工具
        
        Args:
            workspace_dir: 代码执行的工作目录
            allowed_modules: 允许导入的模块列表，为None则不限制
            timeout: 执行超时时间(秒)
        """
        super().__init__(
            name="execute_python",
            description="执行Python代码并返回结果",
            usage="[Python代码片段]"
        )
        self.workspace_dir = workspace_dir or tempfile.gettempdir()
        self.allowed_modules = allowed_modules
        self.timeout = timeout
        
    def run(self, args: str) -> str:
        """
        执行Python代码
        
        Args:
            args: 要执行的Python代码
            
        Returns:
            执行结果或错误信息
        """
        try:
            code = args.strip()
            if not code:
                return "错误: 代码片段为空"
                
            # 检查是否包含禁止的模块
            if self.allowed_modules is not None:
                import ast
                try:
                    parsed = ast.parse(code)
                    for node in ast.walk(parsed):
                        if isinstance(node, ast.Import):
                            for name in node.names:
                                if name.name not in self.allowed_modules:
                                    return f"安全错误: 不允许导入模块 '{name.name}'"
                        elif isinstance(node, ast.ImportFrom):
                            if node.module not in self.allowed_modules:
                                return f"安全错误: 不允许导入模块 '{node.module}'"
                except SyntaxError as e:
                    return f"语法错误: {str(e)}"
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(
                mode='w+',
                suffix='.py',
                delete=False,
                dir=self.workspace_dir,
                encoding='utf-8'
            ) as tmp_file:
                # 添加重定向输出的代码
                wrapped_code = f"""
import sys
from io import StringIO

# 捕获标准输出
stdout_capture = StringIO()
stderr_capture = StringIO()
original_stdout = sys.stdout
original_stderr = sys.stderr
sys.stdout = stdout_capture
sys.stderr = stderr_capture

try:
    # 用户代码开始
{code}
    # 用户代码结束
    
    # 返回捕获的输出
    result = {{"stdout": stdout_capture.getvalue(), "stderr": stderr_capture.getvalue()}}
    print("\\n==== 执行结果 ====")
    print(result)
except Exception as e:
    print(f"执行错误: {{type(e).__name__}}: {{str(e)}}", file=sys.stderr)
finally:
    # 恢复标准输出
    sys.stdout = original_stdout
    sys.stderr = original_stderr
"""
                tmp_file.write(wrapped_code)
                tmp_file.flush()
                file_path = tmp_file.name
            
            # 执行代码
            logger.info(f"执行Python代码（文件：{file_path}）")
            
            # 使用子进程执行代码，设置超时
            try:
                result = subprocess.run(
                    ['python', file_path],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=self.workspace_dir
                )
                
                # 删除临时文件
                try:
                    os.unlink(file_path)
                except:
                    pass
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    return f"代码执行成功:\n\n{output}"
                else:
                    error = result.stderr.strip()
                    return f"代码执行错误:\n\n{error}"
                    
            except subprocess.TimeoutExpired:
                return f"执行超时: 代码执行时间超过{self.timeout}秒"
                
        except Exception as e:
            logger.error(f"代码执行工具错误: {e}")
            return f"工具执行错误: {str(e)}"


class CodeAnalysisTool(BaseTool):
    """
    代码分析工具
    
    分析代码质量、复杂度和潜在问题
    """
    category = "代码工具"
    
    def __init__(self):
        """初始化代码分析工具"""
        super().__init__(
            name="analyze_code",
            description="分析代码质量和复杂度",
            usage="[语言]|[代码片段]"
        )
        
    def run(self, args: str) -> str:
        """
        分析代码
        
        Args:
            args: 格式为 "语言|代码片段"，语言可以是python, javascript等
            
        Returns:
            分析结果
        """
        try:
            if "|" not in args:
                return "错误: 参数格式应为 '语言|代码片段'"
                
            language, code = args.split("|", 1)
            language = language.strip().lower()
            code = code.strip()
            
            if not code:
                return "错误: 代码片段为空"
            
            # 根据不同语言进行分析
            if language == "python":
                return self._analyze_python(code)
            elif language in ["javascript", "js"]:
                return self._analyze_javascript(code)
            else:
                return f"尚不支持分析{language}语言，目前支持的语言: python, javascript"
                
        except Exception as e:
            logger.error(f"代码分析错误: {e}")
            return f"分析代码时出错: {str(e)}"
    
    def _analyze_python(self, code: str) -> str:
        """分析Python代码"""
        try:
            import ast
            
            # 解析代码
            try:
                parsed = ast.parse(code)
            except SyntaxError as e:
                return f"Python语法错误: {str(e)}"
            
            # 分析结构
            functions = []
            classes = []
            imports = []
            variables = []
            
            for node in ast.walk(parsed):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(f"{node.module}")
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            variables.append(target.id)
            
            # 计算复杂度
            class ComplexityVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.complexity = 1  # 基础复杂度
                
                def visit_If(self, node):
                    self.complexity += 1
                    self.generic_visit(node)
                
                def visit_For(self, node):
                    self.complexity += 1
                    self.generic_visit(node)
                    
                def visit_While(self, node):
                    self.complexity += 1
                    self.generic_visit(node)
                    
                def visit_FunctionDef(self, node):
                    self.complexity += 1
                    self.generic_visit(node)
            
            complexity_visitor = ComplexityVisitor()
            complexity_visitor.visit(parsed)
            
            # 组织结果
            result = ["Python代码分析结果:"]
            result.append(f"\n代码复杂度: {complexity_visitor.complexity}")
            
            if classes:
                result.append(f"\n类定义 ({len(classes)}):")
                for cls in classes:
                    result.append(f"- {cls}")
                    
            if functions:
                result.append(f"\n函数定义 ({len(functions)}):")
                for func in functions:
                    result.append(f"- {func}")
            
            if imports:
                result.append(f"\n导入模块 ({len(imports)}):")
                for imp in imports:
                    result.append(f"- {imp}")
            
            # 添加潜在问题的建议
            suggestions = []
            
            # 检查过长的函数
            for node in ast.walk(parsed):
                if isinstance(node, ast.FunctionDef):
                    if len(node.body) > 15:  # 假设超过15行的函数体可能过长
                        suggestions.append(f"函数 '{node.name}' 可能过长，考虑拆分为更小的函数。")
            
            # 检查嵌套控制流
            class NestingVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.max_depth = 0
                    self.current_depth = 0
                    self.deep_constructs = []
                
                def visit_If(self, node):
                    self.current_depth += 1
                    if self.current_depth > self.max_depth:
                        self.max_depth = self.current_depth
                    if self.current_depth >= 3:  # 嵌套深度≥3可能是问题
                        lineno = getattr(node, "lineno", "未知")
                        self.deep_constructs.append(f"行{lineno}的嵌套if语句")
                    self.generic_visit(node)
                    self.current_depth -= 1
                
                def visit_For(self, node):
                    self.current_depth += 1
                    if self.current_depth > self.max_depth:
                        self.max_depth = self.current_depth
                    if self.current_depth >= 3:
                        lineno = getattr(node, "lineno", "未知")
                        self.deep_constructs.append(f"行{lineno}的嵌套循环")
                    self.generic_visit(node)
                    self.current_depth -= 1
                    
                def visit_While(self, node):
                    self.current_depth += 1
                    if self.current_depth > self.max_depth:
                        self.max_depth = self.current_depth
                    if self.current_depth >= 3:
                        lineno = getattr(node, "lineno", "未知")
                        self.deep_constructs.append(f"行{lineno}的嵌套循环")
                    self.generic_visit(node)
                    self.current_depth -= 1
            
            nesting_visitor = NestingVisitor()
            nesting_visitor.visit(parsed)
            
            if nesting_visitor.max_depth >= 3:
                suggestions.append(f"控制流嵌套深度达到{nesting_visitor.max_depth}，可能导致代码难以理解。")
                for construct in nesting_visitor.deep_constructs:
                    suggestions.append(f"- {construct}")
            
            if suggestions:
                result.append("\n改进建议:")
                result.extend(suggestions)
                
            return "\n".join(result)
            
        except ImportError:
            return "无法进行深入分析: 需要ast模块"
            
    def _analyze_javascript(self, code: str) -> str:
        """分析JavaScript代码（简化版）"""
        # 简单的文本分析，实际项目中可以集成专业的JS解析器如esprima
        result = ["JavaScript代码分析结果 (基础分析):"]
        
        # 代码长度
        lines = code.split("\n")
        result.append(f"\n代码行数: {len(lines)}")
        
        # 简单模式匹配
        function_count = code.count("function ")
        function_count += sum(1 for line in lines if "=> {" in line)  # 箭头函数
        
        class_count = code.count("class ")
        import_count = sum(1 for line in lines if line.strip().startswith("import "))
        
        result.append(f"\n大致统计:")
        result.append(f"- 函数: 约 {function_count} 个")
        result.append(f"- 类: 约 {class_count} 个")
        result.append(f"- 导入: 约 {import_count} 个")
        
        # 检查潜在问题
        suggestions = []
        
        # 检查嵌套回调
        if code.count(".then(") > 2:
            suggestions.append("可能存在回调嵌套问题，考虑使用async/await简化代码。")
        
        # 检查过长函数
        bracket_counts = []
        current_count = 0
        for char in code:
            if char == '{':
                current_count += 1
            elif char == '}':
                current_count -= 1
            bracket_counts.append(current_count)
        
        max_nesting = max(bracket_counts) if bracket_counts else 0
        if max_nesting > 3:
            suggestions.append(f"代码嵌套深度达到{max_nesting}级，可能导致难以理解。")
        
        if suggestions:
            result.append("\n改进建议:")
            result.extend(suggestions)
        
        return "\n".join(result)


class CodeGenerationTool(BaseTool):
    """
    代码生成工具
    
    根据描述生成代码片段
    """
    category = "代码工具"
    
    def __init__(self):
        """初始化代码生成工具"""
        super().__init__(
            name="generate_code",
            description="根据描述生成代码片段",
            usage="[语言]|[描述]"
        )
    
    def run(self, args: str) -> str:
        """
        生成代码
        
        这个工具实际上会通过向LLM发送提示来生成代码，但在这个简化实现中，
        我们只返回一个解释说明。实际项目中，应该使用代理本身的能力生成代码。
        
        Args:
            args: 格式为 "语言|描述"，如 "python|实现冒泡排序"
            
        Returns:
            说明信息
        """
        try:
            if "|" not in args:
                return "错误: 参数格式应为 '语言|描述'"
                
            language, description = args.split("|", 1)
            language = language.strip().lower()
            description = description.strip()
            
            return (f"代码生成请求已收到:\n\n"
                    f"语言: {language}\n"
                    f"描述: {description}\n\n"
                    f"注意: 这个工具只是一个占位符。在实际使用中，代理会直接生成代码，"
                    f"而不是调用特定的代码生成工具。你可以简单地请求代理生成代码，"
                    f"而不需要使用这个特定工具。")
            
        except Exception as e:
            logger.error(f"代码生成错误: {e}")
            return f"生成代码时出错: {str(e)}"
