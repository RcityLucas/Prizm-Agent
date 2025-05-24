"""
Rainbow Agent团队协作测试模块

该模块包含一系列测试，用于验证Agent团队协作系统的正确性和性能。
"""

import unittest
import sys
import os
import io
import time
from unittest.mock import MagicMock, patch

# Fix encoding issues for Windows systems
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加父目录到sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rainbow_agent.agent import RainbowAgent
from rainbow_agent.collaboration.team import AgentTeam, Task, TaskStatus

class MockAgent(MagicMock):
    """模拟RainbowAgent的类，用于测试"""
    def run(self, prompt):
        # 根据输入返回不同响应
        if "你好" in prompt.lower() or "hello" in prompt.lower():
            return "您好，有什么我可以帮您的？"
        elif "分解" in prompt:
            return """
我将任务分解为以下子任务:

子任务1: 分析当前数据情况
所需技能: 数据分析

子任务2: 提供创意解决方案
所需技能: 创意思考

子任务3: 制定执行计划
所需技能: 项目规划
"""
        elif "执行" in prompt:
            return f"执行结果: 已完成'{prompt[:20]}...'的处理"
        elif "聚合" in prompt:
            return "综合解决方案: 根据各个子任务的结果，我们建议..."
        else:
            return f"处理: {prompt[:30]}..."


class TestAgentTeam(unittest.TestCase):
    """测试AgentTeam类的功能"""

    def setUp(self):
        """测试前的准备工作"""
        # 确保所有测试字符串使用UTF-8编码
        self.sorry_text = "抱歉"  # 确保这个字符串是UTF-8编码的
        self.greeting_response = "您好，有什么我可以帮您的？"
        
        # 创建模拟协调者
        mock_coordinator = MockAgent(spec=RainbowAgent)
        mock_coordinator.name = "MockCoordinator"

        # 创建AgentTeam实例
        self.team = AgentTeam(
            name="TestTeam", 
            coordinator=mock_coordinator,
            max_output_size=1000,  # 较小的大小以便触发限制
            max_execution_time=5,  # 较短的时间以便触发超时
            max_decomposition_depth=2  # 有限的深度以便测试递归限制
        )

        # 添加一些模拟代理
        data_agent = MockAgent(spec=RainbowAgent)
        data_agent.name = "DataAnalyst"
        self.team.add_agent(data_agent, ["数据分析", "统计"])

        creative_agent = MockAgent(spec=RainbowAgent)
        creative_agent.name = "Creative"
        self.team.add_agent(creative_agent, ["创意思考", "内容创作"])

        planning_agent = MockAgent(spec=RainbowAgent)
        planning_agent.name = "Planner"
        self.team.add_agent(planning_agent, ["项目规划", "任务管理"])

    def test_simple_greeting(self):
        """测试简单问候的快速响应路径"""
        result = self.team.run("你好")
        self.assertIn("task", result)
        self.assertIn("result", result["task"])
        self.assertIn("final_result", result["task"]["result"])
        self.assertIn("您好", result["task"]["result"]["final_result"])
        # 验证没有走分解任务的路径
        self.assertEqual(len(self.team.tasks), 1, "对于简单问候不应该创建多个任务")

    def test_task_decomposition(self):
        """测试任务分解功能"""
        # Monkey patch the coordinator's response for this specific test
        original_run = self.team.coordinator.run
        
        def mock_decompose(prompt):
            if "分解" in prompt:
                return """
我将任务分解为以下子任务:

子任务1: 分析当前数据情况
所需技能: 数据分析

子任务2: 提供创意解决方案
所需技能: 创意思考
"""
            return original_run(prompt)
        
        # Replace the coordinator's run method temporarily
        self.team.coordinator.run = mock_decompose
        
        try:
            # Now run the test with our mocked response
            result = self.team.run("特意让分解生效的测试用例")
            self.assertIn("task", result)
            
            # 获取主任务ID
            task_id = result["task"]["task_id"]
            task = self.team.tasks[task_id]
            
            # 验证任务分解
            self.assertTrue(len(task.subtasks) > 0, "应该创建子任务")
            self.assertEqual(task.status, TaskStatus.COMPLETED, "主任务应该标记为已完成")
        finally:
            # Restore the original method
            self.team.coordinator.run = original_run

    def test_output_size_limit(self):
        """测试输出大小限制"""
        # 创建一个会生成大量输出的查询
        long_query = "详细描述一下人工智能在医疗、金融、教育、农业、制造业、零售业、物流、能源、环保和城市管理等十个领域的应用，" * 5
        
        result = self.team.run(long_query)
        
        # 验证输出是否被截断
        self.assertIn("task", result)
        if "result" in result["task"] and "final_result" in result["task"]["result"]:
            output = result["task"]["result"]["final_result"]
            self.assertLessEqual(len(output), self.team.max_output_size, "输出应该被限制在最大大小内")
            self.assertIn("截断", output, "应该包含截断提示")

    def test_execution_time_limit(self):
        """测试执行时间限制"""
        # 模拟一个耗时的查询
        with patch.object(self.team.coordinator, 'run', side_effect=lambda x: time.sleep(3) or "响应"):
            result = self.team.run("需要很长时间处理的查询", max_tokens=100)

            # 验证是否有执行时间相关的消息
            self.assertIn("task", result)
            if "result" in result["task"]:
                self.assertIn("final_result", result["task"]["result"])
                # 检查结果是否包含截断或超时的信息（更通用的检查）
                self.assertTrue(
                    "截断" in result["task"]["result"]["final_result"] or 
                    "超时" in result["task"]["result"]["final_result"] or
                    "时间" in result["task"]["result"]["final_result"] or
                    self.sorry_text in result["task"]["result"]["final_result"].lower(),
                    f"执行时间限制消息未找到，实际结果: {result['task']['result']['final_result']}"
                )

    def test_recursion_depth_limit(self):
        """测试递归深度限制"""
        # 修改mock协调者的行为，使其总是返回需要进一步分解的响应
        def mock_run(prompt):
            return """
我将进一步分解这个任务:

子任务1: 需要更多分解的子任务
所需技能: 数据分析

子任务2: 另一个需要分解的子任务
所需技能: 创意思考
"""
        
        with patch.object(self.team.coordinator, 'run', side_effect=mock_run):
            # 设置较低的分解深度限制
            original_depth = self.team.max_decomposition_depth
            self.team.max_decomposition_depth = 2
            
            result = self.team.run("这是一个需要多层分解的复杂任务")
            
            # 恢复原始设置
            self.team.max_decomposition_depth = original_depth
            
            # 验证分解深度是否被限制
            # 我们期望总任务数量有限制
            task_count = len(self.team.tasks)
            self.assertLessEqual(task_count, 10, f"任务数量应该有限制，实际为{task_count}")


if __name__ == "__main__":
    unittest.main()
