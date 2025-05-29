"""
对话存储系统测试脚本

测试重构后的对话存储系统的主要功能
"""
import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rainbow_agent.storage.dialogue_storage_system import DialogueStorageSystem
from rainbow_agent.storage.models import SessionModel, TurnModel

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestDialogueStorage")

async def test_session_operations():
    """测试会话操作"""
    logger.info("开始测试会话操作...")
    
    # 初始化对话存储系统
    storage = DialogueStorageSystem()
    
    # 测试创建会话
    user_id = "test_user"
    session = await storage.create_session(
        user_id=user_id,
        title="测试会话",
        dialogue_type="human_to_ai_private",
        summary="这是一个测试会话",
        topics=["测试", "对话"],
        sentiment="neutral",
        metadata={"test_key": "test_value"}
    )
    
    session_id = session.get('id') if isinstance(session, dict) else session.id
    logger.info(f"创建会话成功: {session_id}")
    
    # 测试获取会话
    retrieved_session = await storage.get_session(session_id)
    if retrieved_session:
        logger.info(f"获取会话成功: {session_id}")
    else:
        logger.error(f"获取会话失败: {session_id}")
    
    # 返回会话ID供后续测试使用
    return session_id

def test_turn_operations(session_id: str):
    """测试轮次操作"""
    logger.info("开始测试轮次操作...")
    
    # 初始化对话存储系统
    storage = DialogueStorageSystem()
    
    # 测试创建轮次
    turn1 = storage.create_turn(
        session_id=session_id,
        role="user",
        content="你好，这是一个测试消息",
        metadata={"test_key": "test_value"}
    )
    
    turn1_id = turn1.get('id') if isinstance(turn1, dict) else turn1.id
    logger.info(f"创建用户轮次成功: {turn1_id}")
    
    # 测试创建轮次
    turn2 = storage.create_turn(
        session_id=session_id,
        role="assistant",
        content="你好！我是AI助手，很高兴为你服务。",
        metadata={"test_key": "test_value"}
    )
    
    turn2_id = turn2.get('id') if isinstance(turn2, dict) else turn2.id
    logger.info(f"创建助手轮次成功: {turn2_id}")
    
    # 测试获取轮次
    retrieved_turn = storage.get_turn(turn1_id)
    if retrieved_turn:
        logger.info(f"获取轮次成功: {turn1_id}")
    else:
        logger.error(f"获取轮次失败: {turn1_id}")
    
    # 测试获取会话的所有轮次
    turns = storage.get_turns_by_session(session_id)
    logger.info(f"获取会话 {session_id} 的轮次列表成功，共 {len(turns)} 条")
    
    # 返回轮次ID供后续测试使用
    return turn1_id, turn2_id

async def test_context_operations(session_id: str):
    """测试上下文操作"""
    logger.info("开始测试上下文操作...")
    
    # 初始化对话存储系统
    storage = DialogueStorageSystem()
    
    # 测试获取会话上下文
    context = await storage.get_context(session_id)
    logger.info(f"获取会话 {session_id} 的上下文成功，共 {len(context)} 条")
    
    # 测试更新会话摘要
    success = await storage.update_session_summary(session_id, "这是更新后的会话摘要")
    if success:
        logger.info(f"更新会话 {session_id} 的摘要成功")
    else:
        logger.error(f"更新会话 {session_id} 的摘要失败")
    
    # 测试更新会话主题
    success = await storage.update_session_topics(session_id, ["更新", "测试", "对话"])
    if success:
        logger.info(f"更新会话 {session_id} 的主题成功")
    else:
        logger.error(f"更新会话 {session_id} 的主题失败")

async def run_tests():
    """运行所有测试"""
    try:
        # 测试会话操作
        session_id = await test_session_operations()
        
        # 测试轮次操作
        turn1_id, turn2_id = test_turn_operations(session_id)
        
        # 测试上下文操作
        await test_context_operations(session_id)
        
        logger.info("所有测试完成！")
    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(run_tests())
