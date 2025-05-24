# tests/test_performance.py
import unittest
import time
from rainbow_agent.agent import RainbowAgent
from rainbow_agent.tools.base import BaseTool

class MockTool(BaseTool):
    def __init__(self):
        super().__init__("mock_tool", "Mock tool for testing")
        
    def run(self, args):
        # 模拟工具执行时间
        time.sleep(0.01)
        return f"Mock result for: {args}"

class TestPerformance(unittest.TestCase):
    def setUp(self):
        self.agent = RainbowAgent(
            name="性能测试代理",
            system_prompt="你是一个测试助手",
            tools=[MockTool()],
            model="gpt-3.5-turbo"
        )
    
    @unittest.skip("耗时测试，仅在需要时运行")
    def test_concurrent_requests(self):
        """测试并发请求处理"""
        import concurrent.futures
        
        # 模拟多个并发请求
        queries = [f"测试查询 {i}" for i in range(10)]
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.agent.run, query) for query in queries]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        elapsed_time = time.time() - start_time
        
        # 验证所有请求都成功处理
        self.assertEqual(len(results), 10)
        print(f"处理10个并发请求耗时: {elapsed_time:.2f}秒")

if __name__ == "__main__":
    unittest.main()