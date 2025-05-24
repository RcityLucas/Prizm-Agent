"""
团队协作功能测试用例

测试任务分解、代理间通信和结果聚合等核心功能
"""
import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# 确保可以引入rainbow_agent模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rainbow_agent.agent_enhanced import RainbowAgent
from rainbow_agent.collaboration.messaging import MessageBus, Message, MessageType
from rainbow_agent.collaboration.task_decomposer import TaskDecomposer
from rainbow_agent.collaboration.result_aggregator import ResultAggregator, ConsensusBuilder
from rainbow_agent.collaboration.team_manager import TeamManager
from rainbow_agent.collaboration.team_builder import TeamBuilder


class TestMessaging(unittest.TestCase):
    """消息系统测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.message_bus = MessageBus()
    
    def test_message_creation(self):
        """测试创建消息"""
        message = Message(
            content="测试消息",
            msg_type=MessageType.TASK_ASSIGNMENT,
            sender_id="agent1",
            recipient_id="agent2"
        )
        
        self.assertEqual(message.content, "测试消息")
        self.assertEqual(message.msg_type, MessageType.TASK_ASSIGNMENT)
        self.assertEqual(message.sender_id, "agent1")
        self.assertEqual(message.recipient_id, "agent2")
    
    def test_message_subscription(self):
        """测试消息订阅"""
        # 订阅消息
        self.message_bus.subscribe("agent1", [MessageType.TASK_ASSIGNMENT])
        self.message_bus.subscribe("agent2", [MessageType.QUERY, MessageType.RESPONSE])
        
        # 发布消息
        message1 = Message(
            content="任务1",
            msg_type=MessageType.TASK_ASSIGNMENT,
            sender_id="system",
            recipient_id="agent1"
        )
        self.message_bus.publish(message1)
        
        message2 = Message(
            content="查询1",
            msg_type=MessageType.QUERY,
            sender_id="agent1",
            recipient_id="agent2"
        )
        self.message_bus.publish(message2)
        
        # 获取代理的消息
        agent1_messages = self.message_bus.get_messages_for_agent("agent1")
        agent2_messages = self.message_bus.get_messages_for_agent("agent2")
        
        # 验证消息分发
        self.assertEqual(len(agent1_messages), 1)
        self.assertEqual(agent1_messages[0].msg_type, MessageType.TASK_ASSIGNMENT)
        
        self.assertEqual(len(agent2_messages), 1)
        self.assertEqual(agent2_messages[0].msg_type, MessageType.QUERY)


class TestTaskDecomposer(unittest.TestCase):
    """任务分解器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟协调者
        mock_coordinator = MagicMock()
        mock_coordinator.run = MagicMock(return_value="""
```json
[
  {
    "description": "分析电子商务行业趋势",
    "skills": ["市场分析", "数据分析"]
  },
  {
    "description": "评估竞争对手策略",
    "skills": ["竞争分析", "战略思维"]
  },
  {
    "description": "提出改进建议",
    "skills": ["创新", "战略规划"]
  }
]
```
""")
        
        self.task_decomposer = TaskDecomposer(mock_coordinator)
    
    def test_task_decomposition(self):
        """测试任务分解"""
        subtasks = self.task_decomposer.decompose(
            "分析电子商务市场并提出改进建议",
            context={"industry": "retail"}
        )
        
        # 验证分解结果
        self.assertEqual(len(subtasks), 3)
        self.assertEqual(subtasks[0]["description"], "分析电子商务行业趋势")
        self.assertEqual(subtasks[1]["description"], "评估竞争对手策略")
        self.assertEqual(subtasks[2]["description"], "提出改进建议")
        
        # 验证技能映射
        self.assertIn("市场分析", subtasks[0]["skills"])
        self.assertIn("竞争分析", subtasks[1]["skills"])
        self.assertIn("创新", subtasks[2]["skills"])
    
    def test_fallback_decomposition(self):
        """测试分解失败时的回退策略"""
        # 修改模拟协调者返回无效的JSON
        self.task_decomposer.coordinator.run = MagicMock(return_value="无效的JSON格式")
        
        subtasks = self.task_decomposer.decompose("测试任务")
        
        # 验证使用了默认分解
        self.assertEqual(len(subtasks), 3)  # 默认分解为3个子任务
        self.assertIn("分析任务", subtasks[0]["description"])
        self.assertIn("执行任务", subtasks[1]["description"])
        self.assertIn("总结任务", subtasks[2]["description"])


class TestResultAggregator(unittest.TestCase):
    """结果聚合器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟协调者
        mock_coordinator = MagicMock()
        mock_coordinator.run = MagicMock(return_value="""
```json
{
  "final_result": "综合分析表明，电子商务市场持续增长。主要竞争对手正在加强物流基础设施。建议优化供应链并加强客户体验。",
  "team_contributions": [
    {
      "agent_name": "市场分析师",
      "contribution": "提供了市场趋势分析"
    },
    {
      "agent_name": "战略顾问",
      "contribution": "分析了竞争对手策略"
    },
    {
      "agent_name": "创新专家",
      "contribution": "提出了改进建议"
    }
  ],
  "summary": "团队成功分析了市场环境并提出了可行建议"
}
```
""")
        
        self.result_aggregator = ResultAggregator(mock_coordinator)
        self.consensus_builder = ConsensusBuilder(mock_coordinator)
        
        # 准备子任务结果
        self.subtask_results = [
            {
                "task_description": "分析电子商务行业趋势",
                "agent_name": "市场分析师",
                "result": "电子商务市场持续增长，移动支付占比上升。"
            },
            {
                "task_description": "评估竞争对手策略",
                "agent_name": "战略顾问",
                "result": "主要竞争对手正在加强物流基础设施，提高配送效率。"
            },
            {
                "task_description": "提出改进建议",
                "agent_name": "创新专家",
                "result": "建议优化供应链，提高配送速度，加强客户体验。"
            }
        ]
    
    def test_result_aggregation(self):
        """测试结果聚合"""
        aggregated_result = self.result_aggregator.aggregate(
            main_task_description="分析电子商务市场并提出改进建议",
            subtask_results=self.subtask_results
        )
        
        # 验证聚合结果
        self.assertIn("final_result", aggregated_result)
        self.assertIn("team_contributions", aggregated_result)
        
        # 检查内容完整性
        self.assertIn("电子商务市场", aggregated_result["final_result"])
        self.assertEqual(len(aggregated_result["team_contributions"]), 3)
        
        # 验证贡献者信息
        contributors = [c["agent_name"] for c in aggregated_result["team_contributions"]]
        self.assertIn("市场分析师", contributors)
        self.assertIn("战略顾问", contributors)
        self.assertIn("创新专家", contributors)
    
    def test_consensus_building(self):
        """测试共识构建"""
        # 准备不同的观点
        agent_responses = [
            {
                "agent_name": "经济学家",
                "response": "未来10年，人工智能将导致15-20%的工作岗位被自动化取代。",
                "confidence": "高"
            },
            {
                "agent_name": "技术专家",
                "response": "人工智能会创造更多新型工作岗位，总体就业率不会下降。",
                "confidence": "中"
            },
            {
                "agent_name": "社会学家",
                "response": "人工智能将重塑就业市场，部分领域岗位减少，但同时创造新机会。",
                "confidence": "高"
            }
        ]
        
        # 修改模拟协调者返回的共识
        self.consensus_builder.coordinator.run = MagicMock(return_value="""
```json
{
  "consensus": "人工智能将在未来10年重塑就业市场，一些传统工作会被自动化取代（约15-20%），同时会创造新型工作岗位。总体影响将取决于教育系统和劳动力市场的适应速度。",
  "reasoning": "综合考虑了经济学家的数据预测、技术专家对新岗位创造的见解和社会学家的整体观点。",
  "confidence": "中",
  "dissenting_views": ["技术专家认为总体就业率不会下降"],
  "open_questions": ["教育系统如何适应这一变化？", "哪些新型工作会被创造？"]
}
```
""")
        
        consensus_result = self.consensus_builder.build_consensus(
            question="人工智能将如何影响未来10年的就业市场？",
            agent_responses=agent_responses
        )
        
        # 验证共识结果
        self.assertIn("consensus", consensus_result)
        self.assertIn("reasoning", consensus_result)
        self.assertIn("confidence", consensus_result)
        self.assertIn("dissenting_views", consensus_result)
        
        # 检查内容完整性
        self.assertIn("人工智能", consensus_result["consensus"])
        self.assertIn("未来10年", consensus_result["consensus"])
        self.assertIn("就业市场", consensus_result["consensus"])


class TestTeamManager(unittest.TestCase):
    """团队管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟协调者
        self.coordinator = MagicMock(spec=RainbowAgent)
        self.coordinator.name = "协调者"
        self.coordinator.run = MagicMock(return_value="模拟协调者响应")
        
        self.team_manager = TeamManager("测试团队", self.coordinator)
    
    def test_agent_management(self):
        """测试代理管理功能"""
        # 创建模拟代理
        agent1 = MagicMock(spec=RainbowAgent)
        agent1.name = "数据分析师"
        agent1.run = MagicMock(return_value="数据分析结果")
        
        agent2 = MagicMock(spec=RainbowAgent)
        agent2.name = "内容创作者"
        agent2.run = MagicMock(return_value="创作内容")
        
        # 添加代理到团队
        agent1_id = self.team_manager.add_agent(agent1, ["数据分析", "统计"])
        agent2_id = self.team_manager.add_agent(agent2, ["写作", "创意"])
        
        # 验证代理添加成功
        self.assertEqual(len(self.team_manager.agents), 2)
        self.assertIn(agent1_id, self.team_manager.agents)
        self.assertIn(agent2_id, self.team_manager.agents)
        
        # 测试查找合适的代理
        suitable_agents = self.team_manager.find_suitable_agents(["数据分析"])
        self.assertEqual(len(suitable_agents), 1)
        self.assertEqual(suitable_agents[0], agent1_id)
        
        # 移除代理
        result = self.team_manager.remove_agent(agent1_id)
        self.assertTrue(result)
        self.assertEqual(len(self.team_manager.agents), 1)
    
    @patch.object(TaskDecomposer, 'decompose')
    @patch.object(ResultAggregator, 'aggregate')
    def test_task_execution(self, mock_aggregate, mock_decompose):
        """测试任务执行流程"""
        # 设置任务分解的模拟返回值
        mock_decompose.return_value = [
            {"description": "子任务1", "skills": ["分析"]},
            {"description": "子任务2", "skills": ["写作"]}
        ]
        
        # 设置结果聚合的模拟返回值
        mock_aggregate.return_value = {
            "final_result": "最终结果",
            "team_contributions": [
                {"agent_name": "协调者", "contribution": "任务分解与结果聚合"}
            ]
        }
        
        # 添加代理
        agent = MagicMock(spec=RainbowAgent)
        agent.name = "通用代理"
        agent.run = MagicMock(return_value="子任务结果")
        self.team_manager.add_agent(agent, ["分析", "写作"])
        
        # 执行任务
        result = self.team_manager.execute_task(
            task_description="测试任务",
            decompose=True
        )
        
        # 验证任务执行结果
        self.assertEqual(result["result"]["final_result"], "最终结果")
        self.assertEqual(len(result["subtasks"]), 2)
        self.assertEqual(len(result["subtask_results"]), 2)
        
        # 验证调用
        mock_decompose.assert_called_once()
        mock_aggregate.assert_called_once()
        agent.run.assert_called()


class TestTeamBuilder(unittest.TestCase):
    """团队构建器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.team_builder = TeamBuilder()
    
    @patch('rainbow_agent.collaboration.team_builder.RainbowAgent')
    @patch('rainbow_agent.collaboration.team_builder.TeamManager')
    def test_create_general_team(self, MockTeamManager, MockRainbowAgent):
        """测试创建通用团队"""
        # 设置模拟对象
        mock_coordinator = MagicMock()
        MockRainbowAgent.return_value = mock_coordinator
        
        mock_team_manager = MagicMock()
        MockTeamManager.return_value = mock_team_manager
        
        # 调用被测试的方法
        result = TeamBuilder.create_general_team("通用任务团队")
        
        # 验证创建了协调者
        MockRainbowAgent.assert_called()
        
        # 验证初始化了团队管理器
        MockTeamManager.assert_called_once()
        
        # 验证添加了代理
        self.assertGreater(mock_team_manager.add_agent.call_count, 0)
    
    @patch('rainbow_agent.collaboration.team_builder.RainbowAgent')
    @patch('rainbow_agent.collaboration.team_builder.TeamManager')
    def test_create_custom_team(self, MockTeamManager, MockRainbowAgent):
        """测试创建自定义团队"""
        # 设置模拟对象
        mock_coordinator = MagicMock()
        MockRainbowAgent.return_value = mock_coordinator
        
        mock_team_manager = MagicMock()
        MockTeamManager.return_value = mock_team_manager
        
        agents_config = [
            {
                "name": "自定义代理1", 
                "prompt": "你是自定义代理1", 
                "skills": ["技能1", "技能2"]
            },
            {
                "name": "自定义代理2", 
                "prompt": "你是自定义代理2", 
                "skills": ["技能3", "技能4"]
            }
        ]
        
        # 调用被测试的方法
        result = TeamBuilder.create_custom_team(
            team_name="自定义团队",
            coordinator_name="自定义协调者",
            coordinator_prompt="你是协调者",
            agents_config=agents_config
        )
        
        # 验证创建了正确数量的代理
        # 首次调用是为协调者创建，然后是为两个代理创建
        self.assertEqual(MockRainbowAgent.call_count, 3)  # 协调者 + 2个自定义代理
        # 验证两个代理被添加到团队
        self.assertEqual(mock_team_manager.add_agent.call_count, 2)  # 两个自定义代理被添加


if __name__ == "__main__":
    unittest.main()
