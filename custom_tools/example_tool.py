
from rainbow_agent.tools.base import BaseTool

class ExampleTool(BaseTool):
    """ʾ������"""
    
    def __init__(self):
        super().__init__(
            name="example_tool",
            description="����һ��ͨ����̬���ּ��ص�ʾ������",
            usage="example_tool("����")"
        )
    
    def run(self, args):
        """ִ�й����߼�"""
        return f"ʾ������ִ�гɹ���������{args}"
