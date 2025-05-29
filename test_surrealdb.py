"""
SurrealDB 存储功能测试脚本

这个脚本用于测试 SurrealDB 的存储功能，包括：
1. 连接测试
2. 会话创建测试
3. 轮次添加测试
4. 数据查询测试
5. 数据更新测试
"""
import os
import sys
import asyncio
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("surrealdb_test")

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入必要的模块
from rainbow_agent.storage.surreal_storage import SurrealStorage
from rainbow_agent.storage.session_manager import SessionManager
from rainbow_agent.storage.turn_manager import TurnManager
from rainbow_agent.storage.config import get_surreal_config, DEFAULT_SURREAL_CONFIG
from rainbow_agent.storage.async_utils import run_async

# 测试配置
TEST_USER_ID = "test_user"
TEST_USER_MESSAGE = "这是一条测试消息"
TEST_AI_RESPONSE = "这是AI的回复"

# 全局变量，用于存储会话ID
global TEST_SESSION_ID
TEST_SESSION_ID = None

def print_separator(title: str):
    """打印分隔线"""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "="))
    print("=" * 50 + "\n")

async def test_connection():
    """测试SurrealDB连接"""
    print_separator("测试SurrealDB连接")
    
    # 获取配置
    config = get_surreal_config()
    print(f"SurrealDB配置: {config}")
    
    # 创建存储实例
    storage = SurrealStorage(
        url=config["url"],
        namespace=config["namespace"],
        database=config["database"],
        username=config["username"],
        password=config["password"]
    )
    
    try:
        # 执行简单查询测试连接
        # 注意：现在不需要显式调用connect，因为查询方法会自动确保连接
        print("执行测试查询...")
        result = await storage.query("SELECT * FROM sessions LIMIT 1;")
        print(f"查询结果: {result}")
        print("连接测试成功！")
        
        # 创建一个测试记录来验证写入功能
        print("创建测试记录...")
        test_id = str(uuid.uuid4()).replace('-', '')
        create_query = f"""
        CREATE test_records:{test_id} CONTENT {{
            id: "{test_id}",
            name: "测试记录",
            created_at: "{datetime.now().isoformat()}"
        }};
        """
        
        create_result = await storage.query(create_query)
        print(f"创建测试记录结果: {create_result}")
        
        # 读取创建的记录
        print("读取测试记录...")
        read_query = f"SELECT * FROM test_records WHERE id = '{test_id}';"  
        read_result = await storage.query(read_query)
        print(f"读取测试记录结果: {read_result}")
        
        # 删除测试记录
        print("删除测试记录...")
        delete_query = f"DELETE FROM test_records WHERE id = '{test_id}';"  
        delete_result = await storage.query(delete_query)
        print(f"删除测试记录结果: {delete_result}")
        
        print("测试完成！")
        return True
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"连接测试失败: {e}\n{error_traceback}")
        return False

async def test_session_creation():
    """测试会话创建"""
    print_separator("测试会话创建")
    
    global TEST_SESSION_ID
    
    # 获取配置
    config = get_surreal_config()
    
    # 创建会话管理器
    session_manager = SessionManager(
        url=config["url"],
        namespace=config["namespace"],
        database=config["database"],
        username=config["username"],
        password=config["password"]
    )
    
    try:
        # 创建测试会话
        print(f"使用SessionManager.create_session方法创建会话...")
        result = await session_manager.create_session(TEST_USER_ID, "测试会话")
        
        # 将生成的会话 ID 保存下来，以便后续测试使用
        if result and isinstance(result, dict) and "id" in result:
            TEST_SESSION_ID = result["id"]
            print(f"会话 ID: {TEST_SESSION_ID}")
            print(f"会话创建结果: {result}")
            
            # 验证会话是否创建成功
            print("验证会话是否创建成功...")
            session = await session_manager.get_session(TEST_SESSION_ID)
            print(f"获取到的会话: {session}")
            
            if session and isinstance(session, dict) and "id" in session:
                print("会话创建成功！")
                success = True
            else:
                print("会话创建失败或无法获取！")
                success = False
        else:
            print("无法获取会话ID")
            success = False
            TEST_SESSION_ID = None
        
        return success, TEST_SESSION_ID
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"会话创建测试失败: {e}\n{error_traceback}")
        return False, None

async def test_turn_creation(session_id):
    """测试轮次创建"""
    print_separator("测试轮次创建")
    
    # 获取配置
    config = get_surreal_config()
    
    # 创建轮次管理器
    turn_manager = TurnManager(
        url=config["url"],
        namespace=config["namespace"],
        database=config["database"],
        username=config["username"],
        password=config["password"]
    )
    
    try:
        # 连接到数据库
        print("连接到SurrealDB...")
        await turn_manager.connect()
        
        # 创建用户轮次
        print(f"为会话 {session_id} 创建用户轮次...")
        user_turn_id = str(uuid.uuid4()).replace("-", "")
        user_turn_data = {
            "id": user_turn_id,
            "session_id": session_id,
            "role": "user",
            "content": TEST_USER_MESSAGE,
            "created_at": datetime.now().isoformat(),
            "metadata": {
                "test": True
            }
        }
        
        user_turn_result = await turn_manager.create_turn(user_turn_data)
        print(f"用户轮次创建结果: {user_turn_result}")
        
        # 创建AI轮次
        print(f"为会话 {session_id} 创建AI轮次...")
        ai_turn_id = str(uuid.uuid4()).replace("-", "")
        ai_turn_data = {
            "id": ai_turn_id,
            "session_id": session_id,
            "role": "assistant",
            "content": TEST_AI_RESPONSE,
            "created_at": datetime.now().isoformat(),
            "metadata": {
                "test": True
            }
        }
        
        ai_turn_result = await turn_manager.create_turn(ai_turn_data)
        print(f"AI轮次创建结果: {ai_turn_result}")
        
        # 验证轮次是否创建成功
        print("获取会话的所有轮次...")
        turns = await turn_manager.get_session_turns(session_id)
        print(f"获取到的轮次: {turns}")
        
        if turns and len(turns.get("turns", [])) >= 2:
            print("轮次创建成功！")
            success = True
        else:
            print("轮次创建失败或无法获取！")
            success = False
        
        # 断开连接
        await turn_manager.disconnect()
        return success
    except Exception as e:
        print(f"轮次创建测试失败: {e}")
        return False

async def test_data_update(session_id):
    """测试数据更新"""
    print_separator("测试数据更新")
    
    # 获取配置
    config = get_surreal_config()
    
    # 创建会话管理器
    session_manager = SessionManager(
        url=config["url"],
        namespace=config["namespace"],
        database=config["database"],
        username=config["username"],
        password=config["password"]
    )
    
    try:
        # 连接到数据库
        print("连接到SurrealDB...")
        await session_manager.connect()
        
        # 更新会话标题
        print(f"更新会话 {session_id} 的标题...")
        new_title = f"更新的测试会话 {datetime.now().isoformat()}"
        update_result = await session_manager.update_session(
            session_id, 
            {"title": new_title}
        )
        print(f"更新结果: {update_result}")
        
        # 验证更新是否成功
        print("验证更新是否成功...")
        session = await session_manager.get_session(session_id)
        print(f"更新后的会话: {session}")
        
        if session and session.get("title") == new_title:
            print("会话更新成功！")
            success = True
        else:
            print("会话更新失败或无法验证！")
            success = False
        
        # 断开连接
        await session_manager.disconnect()
        return success, session_id
    except Exception as e:
        print(f"数据更新测试失败: {e}")
        return False, None

async def test_data_cleanup(session_id):
    """清理测试数据"""
    print_separator("清理测试数据")
    
    # 获取配置
    config = get_surreal_config()
    
    # 创建管理器
    session_manager = SessionManager(
        url=config["url"],
        namespace=config["namespace"],
        database=config["database"],
        username=config["username"],
        password=config["password"]
    )
    
    turn_manager = TurnManager(
        url=config["url"],
        namespace=config["namespace"],
        database=config["database"],
        username=config["username"],
        password=config["password"]
    )
    
    try:
        # 连接到数据库
        print("连接到SurrealDB...")
        await session_manager.connect()
        await turn_manager.connect()
        
        # 删除测试轮次
        print(f"删除会话 {session_id} 的所有轮次...")
        turns_delete_result = await turn_manager.delete_session_turns(session_id)
        print(f"轮次删除结果: {turns_delete_result}")
        
        # 删除测试会话
        print(f"删除测试会话 {session_id}...")
        session_delete_result = await session_manager.delete_session(session_id)
        print(f"会话删除结果: {session_delete_result}")
        
        # 验证删除是否成功
        print("验证删除是否成功...")
        session = await session_manager.get_session(session_id)
        
        if not session:
            print("测试数据清理成功！")
            success = True
        else:
            print("测试数据清理失败！")
            success = False
        
        # 断开连接
        await session_manager.disconnect()
        await turn_manager.disconnect()
        return success
    except Exception as e:
        print(f"数据清理测试失败: {e}")
        return False

async def run_all_tests():
    """运行所有测试"""
    print_separator("开始SurrealDB存储功能测试")
    
    # 测试连接
    connection_success = await test_connection()
    if not connection_success:
        print("连接测试失败，终止后续测试")
        return False
    
    # 测试会话创建
    session_success, session_id = await test_session_creation()
    if not session_success or not session_id:
        print("会话创建测试失败，终止后续测试")
        return False
    
    # 总结测试结果
    print_separator("测试结果总结")
    print(f"连接测试: {'\u6210\u529f' if connection_success else '\u5931\u8d25'}")
    print(f"会话创建测试: {'\u6210\u529f' if session_success else '\u5931\u8d25'}")
    
    # 总体结果
    overall_success = connection_success and session_success
    print(f"\n总体测试结果: {'\u6210\u529f' if overall_success else '\u5931\u8d25'}")
    
    return overall_success

def main():
    """主函数"""
    try:
        # 运行所有测试
        success = asyncio.run(run_all_tests())
        
        # 根据测试结果设置退出码
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生未处理的异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
