import unittest
import asyncio
import logging
from rainbow_agent.storage.dialogue_storage_system import DialogueStorageSystem
from rainbow_agent.storage.models import TurnModel

# 配置测试日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestDialogueStorage")

class TestDialogueStorage(unittest.TestCase):
    def setUp(self):
        try:
            # 使用测试环境配置初始化系统
            self.storage = DialogueStorageSystem(
                url="http://localhost:8000",  # 指向本地测试SurrealDB实例
                namespace="test",
                database="rainbow_test",
                username="test",
                password="test"
            )
            # 创建测试会话以供使用
            session = self.storage.session_manager.create_session(
                user_id="test_user", 
                title="测试会话"
            )
            
            # 提取session_id
            self.session_id = None
            if isinstance(session, dict) and 'id' in session:
                self.session_id = session['id']
            elif hasattr(session, 'id'):
                self.session_id = session.id
            elif isinstance(session, str):
                self.session_id = session
                
            logger.info(f"测试会话创建成功: {self.session_id}")
        except Exception as e:
            logger.error(f"测试过程中出现错误: {e}")
            raise
    
    def tearDown(self):
        try:
            # 清理测试数据
            self.storage.delete_session_turns(self.session_id)
            # 删除会话
            self.storage.session_manager.delete_session(self.session_id)
            logger.info(f"测试清理完成，删除会话: {self.session_id}")
        except Exception as e:
            logger.error(f"清理测试数据时出错: {e}")
    
    def test_create_get_turn(self):
        # 测试创建和获取轮次
        turn_data = self.storage.create_turn(
            session_id=self.session_id,
            role="user",
            content="这是测试消息"
        )
        
        # 提取turn_id
        turn_id = None
        if isinstance(turn_data, dict) and 'id' in turn_data:
            turn_id = turn_data['id']
        elif hasattr(turn_data, 'id'):
            turn_id = turn_data.id
        elif isinstance(turn_data, str):
            turn_id = turn_data
        
        # 获取并验证轮次
        turn = self.storage.get_turn(turn_id)
        self.assertIsNotNone(turn)
        self.assertEqual(turn.content, "这是测试消息")
    
    def test_update_turn(self):
        # 测试更新轮次
        turn_data = self.storage.create_turn(
            session_id=self.session_id,
            role="user",
            content="原始消息"
        )
        
        # 提取turn_id
        turn_id = None
        if isinstance(turn_data, dict) and 'id' in turn_data:
            turn_id = turn_data['id']
        elif hasattr(turn_data, 'id'):
            turn_id = turn_data.id
        elif isinstance(turn_data, str):
            turn_id = turn_data
            
        # 更新轮次
        updated_turn = self.storage.update_turn(
            turn_id=turn_id,
            updates={"content": "更新后的消息"}
        )
        
        # 验证更新
        self.assertIsNotNone(updated_turn)
        turn = self.storage.get_turn(turn_id)
        self.assertEqual(turn.content, "更新后的消息")
    
    def test_delete_turn(self):
        # 测试删除轮次
        turn_data = self.storage.create_turn(
            session_id=self.session_id,
            role="user",
            content="将被删除的消息"
        )
        
        # 提取turn_id
        turn_id = None
        if isinstance(turn_data, dict) and 'id' in turn_data:
            turn_id = turn_data['id']
        elif hasattr(turn_data, 'id'):
            turn_id = turn_data.id
        elif isinstance(turn_data, str):
            turn_id = turn_data
            
        # 删除并验证
        result = self.storage.delete_turn(turn_id)
        self.assertTrue(result)
        
        # 确认已删除
        turn = self.storage.get_turn(turn_id)
        self.assertIsNone(turn)
    
    def test_get_turns_by_session(self):
        # 测试获取会话轮次
        # 创建多个轮次
        for i in range(5):
            self.storage.create_turn(
                session_id=self.session_id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"测试消息 {i}"
            )
        
        # 获取并验证会话轮次列表
        turns = self.storage.get_turns_by_session(self.session_id)
        self.assertGreaterEqual(len(turns), 5)

# 异步测试类
class TestDialogueStorageAsync(unittest.TestCase):
    def setUp(self):
        # 使用测试环境配置初始化系统
        self.storage = DialogueStorageSystem(
            url="http://localhost:8000",
            namespace="test",
            database="rainbow_test",
            username="test",
            password="test"
        )
        # 创建测试会话
        self.loop = asyncio.get_event_loop()
        self.session_id = self.loop.run_until_complete(
            self._create_session()
        )
    
    async def _create_session(self):
        # 异步创建会话
        session = await self.storage.create_session_async(
            user_id="test_user", 
            title="测试会话异步"
        )
        
        # 提取session_id
        session_id = None
        if isinstance(session, dict) and 'id' in session:
            session_id = session['id']
        elif hasattr(session, 'id'):
            session_id = session.id
        elif isinstance(session, str):
            session_id = session
            
        logger.info(f"异步测试会话创建成功: {session_id}")
        return session_id
    
    def tearDown(self):
        # 清理测试数据
        self.loop.run_until_complete(
            self.storage.delete_session_turns_async(self.session_id)
        )
    
    def test_async_operations(self):
        logger.info("开始异步测试操作...")
        # 使用run_until_complete来运行异步测试
        self.loop.run_until_complete(self._test_async_operations())
    
    async def _test_async_operations(self):
        logger.info("测试创建轮次...")
        # 测试创建轮次
        turn_data = await self.storage.create_turn_async(
            session_id=self.session_id,
            role="user",
            content="异步测试消息"
        )
        logger.info(f"轮次创建成功: {turn_data}")
        
        # 提取turn_id
        turn_id = None
        if isinstance(turn_data, dict) and 'id' in turn_data:
            turn_id = turn_data['id']
        elif hasattr(turn_data, 'id'):
            turn_id = turn_data.id
        elif isinstance(turn_data, str):
            turn_id = turn_data
        
        logger.info(f"提取的turn_id: {turn_id}")
        
        # 获取并验证轮次
        logger.info("获取轮次...")
        turn = await self.storage.get_turn_async(turn_id)
        self.assertIsNotNone(turn)
        self.assertEqual(turn.content, "异步测试消息")
        logger.info("轮次验证成功")
        
        # 测试更新轮次
        logger.info("更新轮次...")
        updated_turn = await self.storage.update_turn_async(
            turn_id=turn_id,
            updates={"content": "异步更新后的消息"}
        )
        self.assertIsNotNone(updated_turn)
        logger.info("轮次更新成功")
        
        # 验证更新
        logger.info("验证更新后的轮次...")
        turn = await self.storage.get_turn_async(turn_id)
        self.assertEqual(turn.content, "异步更新后的消息")
        logger.info("更新验证成功")
        
        # 获取会话轮次列表
        logger.info("获取会话轮次列表...")
        turns = await self.storage.get_turns_by_session_async(self.session_id)
        self.assertGreaterEqual(len(turns), 1)
        logger.info("会话轮次列表获取成功")
        
        # 测试删除轮次
        logger.info("删除轮次...")
        result = await self.storage.delete_turn_async(turn_id)
        self.assertTrue(result)
        logger.info("轮次删除成功")
        
        # 确认已删除
        logger.info("确认轮次已删除...")
        turn = await self.storage.get_turn_async(turn_id)
        self.assertIsNone(turn)
        logger.info("轮次已确认删除")

if __name__ == "__main__":
    unittest.main()