import logging
import sys
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from rainbow_agent.storage.unified_session_manager import UnifiedSessionManager

def main():
    """检查会话记录"""
    try:
        # 初始化会话管理器
        sm = UnifiedSessionManager()
        
        # 查询所有会话
        print("\n=== 所有会话 ===")
        all_sessions = sm.client.execute_sql('SELECT id, user_id FROM sessions;')
        print(f"总共找到 {len(all_sessions)} 条会话记录")
        
        # 显示前5条会话记录
        print("\n=== 前5条会话记录 ===")
        for i, session in enumerate(all_sessions[:5]):
            print(f"{i+1}. ID: {session.get('id', 'unknown')}, user_id: {session.get('user_id', 'none')}")
        
        # 检查不同的user_id
        user_ids = set(session.get('user_id', 'none') for session in all_sessions)
        print(f"\n=== 发现 {len(user_ids)} 个不同的user_id ===")
        for i, user_id in enumerate(user_ids):
            print(f"{i+1}. {user_id}")
            
        # 测试按user_id过滤
        if user_ids:
            test_user_id = next(iter(user_ids))
            print(f"\n=== 测试按user_id={test_user_id}过滤 ===")
            
            # 使用execute_sql直接执行SQL查询
            sql_query = f"SELECT id, user_id FROM sessions WHERE user_id = '{test_user_id}';"
            print(f"执行SQL: {sql_query}")
            filtered_sessions = sm.client.execute_sql(sql_query)
            print(f"SQL查询返回 {len(filtered_sessions)} 条记录")
            
            # 使用get_user_sessions方法
            print(f"\n使用get_user_sessions方法过滤user_id={test_user_id}")
            user_sessions = sm.get_user_sessions(test_user_id)
            print(f"get_user_sessions返回 {len(user_sessions)} 条记录")
            
            # 比较结果
            if len(filtered_sessions) != len(user_sessions):
                print(f"警告: 直接SQL查询和get_user_sessions返回的结果数量不一致!")
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
