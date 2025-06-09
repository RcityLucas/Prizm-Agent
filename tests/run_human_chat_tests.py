import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入测试模块
from unit.human_chat.test_chat_manager import TestHumanChatManager
from unit.human_chat.test_notification_service import TestNotificationService
from integration.human_chat.test_api_integration import TestHumanChatAPIIntegration

if __name__ == "__main__":
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加单元测试
    test_suite.addTest(unittest.makeSuite(TestHumanChatManager))
    test_suite.addTest(unittest.makeSuite(TestNotificationService))
    
    # 添加集成测试
    test_suite.addTest(unittest.makeSuite(TestHumanChatAPIIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出测试结果摘要
    print(f"\n测试结果摘要:")
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.errors) - len(result.failures)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    # 设置退出码
    sys.exit(len(result.failures) + len(result.errors))
