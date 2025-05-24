"""
代码生成工具
"""
from typing import Any
from .base import BaseTool
import json
import random
import os
from datetime import datetime

class CodeGenerationTool(BaseTool):
    """代码生成工具，可以根据需求描述生成代码"""
    
    def __init__(self):
        super().__init__(
            name="CodeGenerationTool",
            description="根据需求描述生成代码",
            usage="CodeGenerationTool <需求描述> [编程语言]",
            version="1.5.0",
            author="Rainbow Team",
            tags=["生成", "代码", "AI工具"]
        )
        self.output_dir = "generated_code"
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
    def run(self, args: Any) -> str:
        """
        执行代码生成
        
        Args:
            args: 需求描述和可选的编程语言，格式为"需求描述 [语言]"
            
        Returns:
            生成的代码
        """
        try:
            input_text = str(args).strip()
            if not input_text:
                return "请提供需求描述"
                
            # 解析输入，提取需求和语言
            parts = input_text.split("[")
            requirement = parts[0].strip()
            
            # 如果指定了语言，提取它
            language = "python"  # 默认语言
            if len(parts) > 1 and "]" in parts[1]:
                language = parts[1].split("]")[0].strip().lower()
                
            # 模拟代码生成过程
            code_info = self._simulate_code_generation(requirement, language)
            return json.dumps(code_info, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return f"代码生成失败: {str(e)}"
            
    def _simulate_code_generation(self, requirement: str, language: str) -> dict:
        """模拟代码生成过程"""
        # 生成一个随机的代码ID
        code_id = f"code_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
        
        # 代码保存路径
        file_extension = self._get_file_extension(language)
        code_path = os.path.join(self.output_dir, f"{code_id}{file_extension}")
        
        # 根据语言生成示例代码
        code = self._generate_sample_code(requirement, language)
        
        # 在实际实现中，这里会调用代码生成API
        # 并将生成的代码保存到文件
        
        return {
            "success": True,
            "requirement": requirement,
            "language": language,
            "code_path": code_path,
            "code_id": code_id,
            "code": code,
            "message": "代码已成功生成（模拟）"
        }
        
    def _get_file_extension(self, language: str) -> str:
        """根据语言获取文件扩展名"""
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "java": ".java",
            "c": ".c",
            "cpp": ".cpp",
            "c++": ".cpp",
            "csharp": ".cs",
            "c#": ".cs",
            "go": ".go",
            "rust": ".rs",
            "ruby": ".rb",
            "php": ".php",
            "swift": ".swift",
            "kotlin": ".kt",
            "html": ".html",
            "css": ".css",
            "sql": ".sql"
        }
        return extensions.get(language.lower(), ".txt")
        
    def _generate_sample_code(self, requirement: str, language: str) -> str:
        """生成示例代码"""
        # 这里只是生成一些简单的示例代码
        # 在实际实现中，会使用更复杂的代码生成模型
        
        if language.lower() == "python":
            return f'''
# {requirement}
import random

def main():
    """Main function to address the requirement"""
    print("Implementing: {requirement}")
    
    # 示例实现
    result = random.randint(1, 100)
    print(f"Generated result: {result}")
    return result

if __name__ == "__main__":
    main()
'''
        elif language.lower() in ["javascript", "js"]:
            return f'''
// {requirement}
function main() {{
    // Main function to address the requirement
    console.log("Implementing: {requirement}");
    
    // 示例实现
    const result = Math.floor(Math.random() * 100) + 1;
    console.log(`Generated result: ${{result}}`);
    return result;
}}

main();
'''
        elif language.lower() in ["java"]:
            return f'''
/**
 * {requirement}
 */
public class Solution {{
    public static void main(String[] args) {{
        System.out.println("Implementing: {requirement}");
        
        // 示例实现
        int result = (int) (Math.random() * 100) + 1;
        System.out.println("Generated result: " + result);
    }}
}}
'''
        else:
            return f"// {requirement}\n// 这是一个{language}的示例代码\n// 实际实现会根据需求生成更复杂的代码"
