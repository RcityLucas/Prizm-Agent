
from rainbow_agent.tools.base import BaseTool

class ExampleTool(BaseTool):
    """示例工具"""
    
    def __init__(self):
        super().__init__(
            name="example_tool",
            description="这是一个通过动态发现加载的示例工具",
            usage="example_tool("参数")"
        )
    
    def run(self, args):
        """执行工具逻辑"""
        return f"示例工具执行成功，参数：{args}"
