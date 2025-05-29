"""
测试增强版会话和轮次管理器

验证增强版会话和轮次管理器的功能
"""
import os
import sys
import asyncio
import logging
from datetime import datetime

from rainbow_agent.storage.enhanced_session_manager import EnhancedSessionManager
from rainbow_agent.storage.enhanced_turn_manager import EnhancedTurnManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("enhanced_managers_test")

# 测试配置
TEST_USER_ID = "test_user"
TEST_SESSION_TITLE = "Test Session"

def print_separator(title: str):
    """打印分隔线"""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "="))
    print("=" * 50 + "\n")

async def test_session_creation():
    """测试会话创建"""
    print_separator("测试会话创建")
    
    try:
        # 创建会话管理器
        session_manager = EnhancedSessionManager(
            namespace="rainbow",  # 使用正确的命名空间
            database="test"       # 使用正确的数据库
        )
        
        # 创建测试会话
        print(f"创建测试会话...")
        session = await session_manager.create_session(TEST_USER_ID, TEST_SESSION_TITLE)
        print(f"会话创建结果: {session}")
        
        # 获取会话ID
        session_id = session["id"]
        print(f"会话ID: {session_id}")
        
        # 验证会话是否创建成功
        print("验证会话是否创建成功...")
        retrieved_session = await session_manager.get_session(session_id)
        print(f"获取到的会话: {retrieved_session}")
        
        if retrieved_session and retrieved_session["id"] == session_id:
            print("会话创建成功！")
            return True, session_id
        else:
            print("会话创建失败！")
            return False, None
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"会话创建测试失败: {e}\n{error_traceback}")
        return False, None

async def test_turn_creation(session_id):
    """测试轮次创建"""
    print_separator("测试轮次创建")
    
    try:
        # 创建轮次管理器
        turn_manager = EnhancedTurnManager(
            namespace="rainbow",  # 使用正确的命名空间
            database="test"       # 使用正确的数据库
        )
        
        # 添加用户轮次
        print(f"添加用户轮次...")
        user_turn = await turn_manager.create_turn(session_id, "user", "This is a test message")
        print(f"用户轮次添加结果: {user_turn}")
        
        # 添加AI轮次
        print(f"添加AI轮次...")
        ai_turn = await turn_manager.create_turn(session_id, "assistant", "This is AI response")
        print(f"AI轮次添加结果: {ai_turn}")
        
        # 获取所有轮次
        print("获取所有轮次...")
        turns = await turn_manager.get_turns(session_id)
        print(f"轮次列表: {turns}")
        
        if len(turns) >= 2:
            print("轮次创建成功！")
            return True
        else:
            print("轮次创建失败！")
            return False
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"轮次创建测试失败: {e}\n{error_traceback}")
        return False

async def test_session_update(session_id):
    """测试会话更新"""
    print_separator("测试会话更新")
    
    try:
        # 创建会话管理器
        session_manager = EnhancedSessionManager(
            namespace="rainbow",  # 使用正确的命名空间
            database="test"       # 使用正确的数据库
        )
        
        # 更新会话标题
        print(f"更新会话标题...")
        new_title = f"Updated Session {datetime.now().strftime('%H:%M:%S')}"
        updated_session = await session_manager.update_session(session_id, {"title": new_title})
        print(f"会话更新结果: {updated_session}")
        
        # 验证会话是否更新成功
        print("验证会话是否更新成功...")
        retrieved_session = await session_manager.get_session(session_id)
        print(f"获取到的会话: {retrieved_session}")
        
        if retrieved_session and retrieved_session["title"] == new_title:
            print("会话更新成功！")
            return True
        else:
            print("会话更新失败！")
            return False
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"会话更新测试失败: {e}\n{error_traceback}")
        return False

async def test_turn_update(session_id):
    """测试轮次更新"""
    print_separator("测试轮次更新")
    
    try:
        # 创建轮次管理器
        turn_manager = EnhancedTurnManager(
            namespace="rainbow",  # 使用正确的命名空间
            database="test"       # 使用正确的数据库
        )
        
        # 获取轮次列表
        turns = await turn_manager.get_turns(session_id)
        if not turns:
            print("没有找到轮次，无法测试更新")
            return False
        
        # 获取第一个轮次
        turn_id = turns[0]["id"]
        
        # 更新轮次内容
        print(f"更新轮次内容...")
        new_content = f"Updated content {datetime.now().strftime('%H:%M:%S')}"
        updated_turn = await turn_manager.update_turn(turn_id, {"content": new_content})
        print(f"轮次更新结果: {updated_turn}")
        
        # 验证轮次是否更新成功
        print("验证轮次是否更新成功...")
        retrieved_turn = await turn_manager.get_turn(turn_id)
        print(f"获取到的轮次: {retrieved_turn}")
        
        if retrieved_turn and retrieved_turn["content"] == new_content:
            print("轮次更新成功！")
            return True
        else:
            print("轮次更新失败！")
            return False
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"轮次更新测试失败: {e}\n{error_traceback}")
        return False

async def test_advanced_retrieval(session_id):
    """测试高级检索功能"""
    print_separator("测试高级检索功能")
    
    try:
        # 创建会话和轮次管理器
        session_manager = EnhancedSessionManager(
            namespace="rainbow",
            database="test"
        )
        turn_manager = EnhancedTurnManager(
            namespace="rainbow",
            database="test"
        )
        
        # 1. 测试使用条件查询获取会话
        print("测试使用条件查询获取会话...")
        retrieved_session = await session_manager.get_session(session_id)
        if retrieved_session:
            print(f"条件查询获取会话成功: {retrieved_session['id']}")
        else:
            print("条件查询获取会话失败")
            return False
        
        # 2. 测试获取轮次并使用会话ID进行验证
        print("测试获取轮次并使用会话ID进行验证...")
        turns = await turn_manager.get_turns(session_id)
        if not turns:
            print("没有找到轮次，无法测试高级检索")
            return False
        
        turn_id = turns[0]["id"]
        print(f"使用会话ID {session_id} 获取轮次 {turn_id}")
        retrieved_turn = await turn_manager.get_turn(turn_id, session_id)
        
        if retrieved_turn:
            print(f"使用会话ID获取轮次成功: {retrieved_turn['id']}")
        else:
            print("使用会话ID获取轮次失败")
            return False
        
        # 3. 测试使用无效ID进行检索
        print("测试使用无效ID进行检索...")
        invalid_id = "invalid_id_" + datetime.now().strftime('%H%M%S')
        invalid_session = await session_manager.get_session(invalid_id)
        print(f"无效会话ID检索结果: {invalid_session}")
        
        invalid_turn = await turn_manager.get_turn(invalid_id)
        print(f"无效轮次ID检索结果: {invalid_turn}")
        
        # 测试成功
        print("高级检索功能测试成功！")
        return True
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"高级检索测试失败: {e}\n{error_traceback}")
        return False

async def run_all_tests():
    """运行所有测试"""
    print_separator("开始测试增强版会话和轮次管理器")
    
    # 测试会话创建
    session_success, session_id = await test_session_creation()
    if not session_success or not session_id:
        print("会话创建测试失败，终止后续测试")
        return False
    
    # 测试轮次创建
    turn_success = await test_turn_creation(session_id)
    if not turn_success:
        print("轮次创建测试失败")
        return False
    
    # 测试会话更新
    session_update_success = await test_session_update(session_id)
    if not session_update_success:
        print("会话更新测试失败")
        return False
    
    # 测试轮次更新
    turn_update_success = await test_turn_update(session_id)
    if not turn_update_success:
        print("轮次更新测试失败")
        return False
    
    # 测试高级检索功能
    advanced_retrieval_success = await test_advanced_retrieval(session_id)
    if not advanced_retrieval_success:
        print("高级检索功能测试失败")
        return False
    
    # 总结测试结果
    print_separator("测试结果总结")
    print(f"会话创建测试: {'成功' if session_success else '失败'}")
    print(f"轮次创建测试: {'成功' if turn_success else '失败'}")
    print(f"会话更新测试: {'成功' if session_update_success else '失败'}")
    print(f"轮次更新测试: {'成功' if turn_update_success else '失败'}")
    print(f"高级检索功能测试: {'成功' if advanced_retrieval_success else '失败'}")
    
    # 总体结果
    overall_success = session_success and turn_success and session_update_success and turn_update_success and advanced_retrieval_success
    print(f"\n总体测试结果: {'成功' if overall_success else '失败'}")
    
    return overall_success

def main():
    """主函数"""
    try:
        # 运行所有测试
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生未处理的异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
