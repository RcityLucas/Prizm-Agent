"""
Rainbow Agent 综合测试框架

这个脚本包含了一系列测试，用于验证Rainbow Agent的各个功能模块
"""
import os
import sys
import time
import json
from typing import Dict, Any, List, Optional, Tuple

# 导入Rainbow Agent核心组件
from rainbow_agent.agent import RainbowAgent
from rainbow_agent.collaboration.team import AgentTeam, create_expert_agent
from rainbow_agent.tools.tool_executor import ToolExecutor
from rainbow_agent.tools.base import BaseTool
from rainbow_agent.utils.logger import get_logger

# 设置日志记录器
logger = get_logger(__name__)


class TestResult:
    """测试结果类，用于记录测试结果"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = False
        self.error = None
        self.details = {}
        self.start_time = time.time()
        self.end_time = None
        
    def success(self, **details):
        """标记测试成功"""
        self.passed = True
        self.end_time = time.time()
        self.details.update(details)
        
    def fail(self, error=None, **details):
        """标记测试失败"""
        self.passed = False
        self.error = error
        self.end_time = time.time()
        self.details.update(details)
        
    @property
    def duration(self) -> float:
        """测试持续时间（秒）"""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
        
    def __str__(self) -> str:
        status = "通过" if self.passed else "失败"
        result = f"测试 '{self.test_name}': {status} (耗时: {self.duration:.2f}秒)"
        if self.error:
            result += f"\n错误: {self.error}"
        if self.details:
            result += f"\n详情: {json.dumps(self.details, ensure_ascii=False, indent=2)}"
        return result


class EchoTool(BaseTool):
    """测试用的回显工具"""
    
    def __init__(self):
        super().__init__(
            name="echo",
            description="回显输入的内容。使用格式: '要回显的文本'"
        )
    
    def run(self, args: str) -> str:
        return f"回显结果: {args}"


class CalculatorTool(BaseTool):
    """简单计算器工具"""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="执行简单的数学计算。使用格式: '1 + 2 * 3'"
        )
    
    def run(self, args: str) -> str:
        try:
            # 安全地计算表达式
            result = eval(args, {"__builtins__": {}})
            return f"计算结果: {args} = {result}"
        except Exception as e:
            return f"计算错误: {str(e)}"


class TestSuite:
    """测试套件，包含多个测试"""
    
    def __init__(self):
        self.results = []
        
    def run_test(self, test_func, test_name=None):
        """运行单个测试并记录结果"""
        if test_name is None:
            test_name = test_func.__name__
            
        print(f"\n===== 运行测试: {test_name} =====")
        result = TestResult(test_name)
        
        try:
            test_func(result)
        except Exception as e:
            result.fail(error=str(e))
            logger.error(f"测试 '{test_name}' 发生异常: {e}")
        
        self.results.append(result)
        print(str(result))
        return result
    
    def summary(self):
        """打印测试结果摘要"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        print("\n===== 测试结果摘要 =====")
        print(f"总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        
        if failed > 0:
            print("\n失败的测试:")
            for result in self.results:
                if not result.passed:
                    print(f"- {result.test_name}: {result.error}")


# 1. 工具执行器测试
def test_tool_executor(result):
    """测试工具执行器的功能"""
    executor = ToolExecutor()
    
    # 添加测试工具
    echo_tool = EchoTool()
    calc_tool = CalculatorTool()
    executor.add_tool(echo_tool)
    executor.add_tool(calc_tool)
    
    # 测试工具注册
    if len(executor.tools) != 2:
        result.fail(error=f"工具注册失败，期望2个工具，实际有{len(executor.tools)}个")
        return
        
    # 测试工具调用解析
    test_cases = [
        {
            "input": "我觉得应该使用工具：echo: 测试文本",
            "expected_tool": "echo",
            "expected_args": "测试文本"
        },
        {
            "input": "我需要计算，使用工具: calculator(2 + 3 * 4)",
            "expected_tool": "calculator",
            "expected_args": "2 + 3 * 4" 
        },
        {
            "input": "让我为你计算 calculator(10/2)",
            "expected_tool": "calculator",
            "expected_args": "10/2"
        },
        {
            "input": "这不是工具调用",
            "expected_tool": None,
            "expected_args": None
        }
    ]
    
    parsing_results = []
    for i, case in enumerate(test_cases):
        parsed = executor.parse_tool_call(case["input"])
        
        if case["expected_tool"] is None:
            # 期望没有工具调用
            if parsed is not None:
                result.fail(error=f"案例 {i+1}: 错误地识别了工具调用: {parsed}")
                return
        else:
            # 期望有工具调用
            if parsed is None:
                result.fail(error=f"案例 {i+1}: 未能识别工具调用")
                return
                
            if parsed["tool_name"] != case["expected_tool"]:
                result.fail(error=f"案例 {i+1}: 工具名称识别错误，期望 {case['expected_tool']}，得到 {parsed['tool_name']}")
                return
                
            if case["expected_args"] not in parsed["tool_args"]:
                result.fail(error=f"案例 {i+1}: 参数识别错误，期望包含 {case['expected_args']}，得到 {parsed['tool_args']}")
                return
                
        parsing_results.append({
            "case": i+1,
            "input": case["input"],
            "parsed": parsed
        })
    
    # 测试工具执行
    for tool_name in ["echo", "calculator"]:
        test_args = "测试" if tool_name == "echo" else "1+1"
        success, result_text = executor.execute_tool({"tool_name": tool_name, "tool_args": test_args})
        
        if not success:
            result.fail(error=f"工具 {tool_name} 执行失败: {result_text}")
            return
    
    # 所有测试都通过
    result.success(
        tools_registered=len(executor.tools),
        parsing_results=parsing_results
    )


# 2. 代理基础功能测试
def test_agent_basics(result):
    """测试代理的基础功能"""
    
    # 创建代理
    agent = RainbowAgent(
        name="测试代理",
        system_prompt="你是一个简单的测试助手。",
        model="gpt-3.5-turbo"
    )
    
    # 添加工具
    agent.add_tool(EchoTool())
    
    if len(agent.tool_executor.tools) != 1:
        result.fail(error=f"工具添加失败，期望1个工具，实际有{len(agent.tool_executor.tools)}个")
        return
        
    # 测试简单响应
    try:
        response = agent.run("你好")
        if not isinstance(response, str) or len(response) < 5:
            result.fail(error=f"响应异常: {response}")
            return
    except Exception as e:
        result.fail(error=f"运行代理时出错: {e}")
        return
        
    result.success(
        tools_count=len(agent.tool_executor.tools),
        response_type=type(response).__name__,
        response_length=len(response) if isinstance(response, str) else 0
    )


# 3. 团队协作测试
def test_team_collaboration(result):
    """测试团队协作功能"""
    
    # 创建团队
    team = AgentTeam(name="测试团队")
    
    # 创建两个专家代理
    tech_expert = create_expert_agent("技术专家", "技术、编程和系统架构")
    creative_expert = create_expert_agent("创意专家", "创意、设计和用户体验")
    
    # 添加到团队
    tech_id = team.add_agent(tech_expert, skills=["技术", "编程", "架构"])
    creative_id = team.add_agent(creative_expert, skills=["创意", "设计", "用户体验"])
    
    if len(team.agents) != 2:
        result.fail(error=f"代理添加失败，期望2个代理，实际有{len(team.agents)}个")
        return
        
    # 测试任务创建
    task_id = team.create_task("测试团队协作")
    
    if task_id not in team.tasks:
        result.fail(error=f"任务创建失败，找不到任务ID: {task_id}")
        return
        
    # 测试简单任务
    response = team.run("请用一句话描述什么是人工智能", decompose=False)
    
    if not isinstance(response, dict) or "task" not in response:
        result.fail(error=f"团队响应格式错误: {response}")
        return
        
    task_data = response["task"]
    if not isinstance(task_data, dict) or "result" not in task_data:
        result.fail(error=f"任务数据格式错误: {task_data}")
        return
        
    result.success(
        agents_count=len(team.agents),
        agent_ids=[tech_id, creative_id],
        tasks_count=len(team.tasks),
        response_format="正确" if isinstance(task_data.get("result"), dict) else "错误"
    )


# 主测试函数
def run_tests():
    """运行所有测试"""
    print("开始Rainbow Agent综合测试...\n")
    
    # 检查环境变量
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    
    if not api_key:
        print("警告: 未设置OPENAI_API_KEY环境变量，测试可能会失败")
    else:
        print(f"使用API密钥: {api_key[:5]}...{api_key[-4:]}")
        
    if base_url:
        print(f"使用自定义API URL: {base_url}")
    
    # 创建测试套件
    suite = TestSuite()
    
    # 添加测试
    suite.run_test(test_tool_executor, "工具执行器测试")
    suite.run_test(test_agent_basics, "代理基础功能测试")
    suite.run_test(test_team_collaboration, "团队协作测试")
    
    # 打印测试摘要
    suite.summary()
    
    return suite


if __name__ == "__main__":
    run_tests()
