#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接测试SurrealDB连接和会话创建的脚本
"""
import asyncio
import json
import logging
import sys
import uuid
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入SurrealDB客户端
try:
    from surrealdb import Surreal
except ImportError:
    logger.error("缺少surrealdb模块，请安装: pip install surrealdb-python")
    sys.exit(1)

# 从配置文件导入配置
try:
    from rainbow_agent.storage.config import get_surreal_config
except ImportError:
    logger.error("无法导入配置模块")
    sys.exit(1)

async def test_connection():
    """测试SurrealDB连接"""
    config = get_surreal_config()
    logger.info(f"SurrealDB配置: {config}")
    
    # 创建数据库连接
    db = Surreal()
    
    try:
        # 连接
        logger.info(f"正在连接到SurrealDB: {config['url']}")
        await db.connect(config['url'])
        logger.info("SurrealDB连接成功")
        
        # 登录
        await db.signin({
            "user": config['username'],
            "pass": config['password']
        })
        logger.info("SurrealDB登录成功")
        
        # 使用命名空间和数据库
        await db.use(config['namespace'], config['database'])
        logger.info(f"成功使用命名空间和数据库: {config['namespace']}, {config['database']}")
        
        # 测试查询
        info_result = await db.query("INFO FOR DB;")
        logger.info(f"数据库信息: {info_result}")
        
        # 列出表
        tables_result = await db.query("SHOW TABLES;")
        logger.info(f"表列表: {tables_result}")
        
        # 检查sessions表
        sessions_result = await db.query("SELECT * FROM sessions;")
        logger.info(f"Sessions表数据: {sessions_result}")
        
        # 检查turns表
        turns_result = await db.query("SELECT * FROM turns;")
        logger.info(f"Turns表数据: {turns_result}")
        
        return True
    except Exception as e:
        logger.error(f"SurrealDB连接测试失败: {e}")
        return False
    finally:
        # 关闭连接
        await db.close()

async def create_test_session():
    """创建测试会话"""
    config = get_surreal_config()
    db = Surreal()
    
    try:
        # 连接
        await db.connect(config['url'])
        await db.signin({
            "user": config['username'],
            "pass": config['password']
        })
        await db.use(config['namespace'], config['database'])
        
        # 生成唯一ID
        session_id = str(uuid.uuid4()).replace('-', '')
        now = datetime.now().isoformat()
        
        # 创建会话数据
        session_data = {
            "id": session_id,
            "title": f"直接测试会话 {now}",
            "user_id": "test_direct_user",
            "created_at": now,
            "updated_at": now,
            "last_activity_at": now,
            "dialogue_type": "human_to_ai_private",
            "participants": [
                {
                    "id": "test_direct_user",
                    "name": "测试用户",
                    "type": "human"
                },
                {
                    "id": "ai_assistant",
                    "name": "Rainbow助手",
                    "type": "ai"
                }
            ]
        }
        
        # 创建会话
        logger.info(f"正在创建测试会话: {session_data}")
        
        # 方法1: 使用create方法
        try:
            result = await db.create("sessions", session_data)
            logger.info(f"使用create方法创建会话结果: {result}")
        except Exception as e:
            logger.error(f"使用create方法创建会话失败: {e}")
        
        # 方法2: 使用insert语句
        try:
            query = f"""
            INSERT INTO sessions {{
                id: '{session_id}',
                title: '直接测试会话-SQL {now}',
                user_id: 'test_direct_user',
                created_at: '{now}',
                updated_at: '{now}',
                last_activity_at: '{now}'
            }};
            """
            result = await db.query(query)
            logger.info(f"使用SQL插入会话结果: {result}")
        except Exception as e:
            logger.error(f"使用SQL插入会话失败: {e}")
        
        # 方法3: 使用简化数据结构
        try:
            simple_data = {
                "title": f"简化测试会话 {now}",
                "user_id": "test_direct_user",
                "created_at": now
            }
            result = await db.create("sessions", simple_data)
            logger.info(f"使用简化数据创建会话结果: {result}")
        except Exception as e:
            logger.error(f"使用简化数据创建会话失败: {e}")
        
        # 验证创建
        try:
            sessions = await db.query("SELECT * FROM sessions;")
            logger.info(f"创建后查询所有会话: {sessions}")
            
            if sessions and hasattr(sessions, "result") and sessions.result:
                return True
            else:
                logger.warning("创建会话后查询不到数据")
                return False
        except Exception as e:
            logger.error(f"查询会话失败: {e}")
            return False
    except Exception as e:
        logger.error(f"创建测试会话失败: {e}")
        return False
    finally:
        # 关闭连接
        await db.close()

async def test_surreal_schema():
    """测试并创建必要的表结构"""
    config = get_surreal_config()
    db = Surreal()
    
    try:
        # 连接
        await db.connect(config['url'])
        await db.signin({
            "user": config['username'],
            "pass": config['password']
        })
        await db.use(config['namespace'], config['database'])
        
        # 检查是否需要创建表结构
        tables_result = await db.query("SHOW TABLES;")
        
        if tables_result and hasattr(tables_result, "result") and tables_result.result:
            tables = tables_result.result[0]
            logger.info(f"现有表: {tables}")
            
            # 创建会话表
            if "sessions" not in tables:
                logger.info("创建sessions表")
                await db.query("""
                DEFINE TABLE sessions SCHEMAFULL;
                DEFINE FIELD id ON sessions TYPE string;
                DEFINE FIELD title ON sessions TYPE string;
                DEFINE FIELD user_id ON sessions TYPE string;
                DEFINE FIELD created_at ON sessions TYPE datetime;
                DEFINE FIELD updated_at ON sessions TYPE datetime;
                DEFINE FIELD last_activity_at ON sessions TYPE datetime;
                DEFINE FIELD dialogue_type ON sessions TYPE string;
                DEFINE FIELD participants ON sessions TYPE array;
                """)
            
            # 创建轮次表
            if "turns" not in tables:
                logger.info("创建turns表")
                await db.query("""
                DEFINE TABLE turns SCHEMAFULL;
                DEFINE FIELD id ON turns TYPE string;
                DEFINE FIELD session_id ON turns TYPE string;
                DEFINE FIELD index ON turns TYPE int;
                DEFINE FIELD role ON turns TYPE string;
                DEFINE FIELD content ON turns TYPE string;
                DEFINE FIELD timestamp ON turns TYPE datetime;
                DEFINE FIELD metadata ON turns TYPE object;
                """)
            
            # 重新检查表结构
            tables_result = await db.query("SHOW TABLES;")
            if tables_result and hasattr(tables_result, "result") and tables_result.result:
                updated_tables = tables_result.result[0]
                logger.info(f"更新后的表: {updated_tables}")
                
                if "sessions" in updated_tables and "turns" in updated_tables:
                    logger.info("表结构创建成功")
                    return True
                else:
                    logger.warning("表结构创建不完整")
                    return False
        else:
            logger.warning("无法获取表列表")
            return False
    except Exception as e:
        logger.error(f"测试表结构失败: {e}")
        return False
    finally:
        # 关闭连接
        await db.close()

async def run_tests():
    """运行所有测试"""
    logger.info("开始测试SurrealDB...")
    
    # 测试连接
    conn_result = await test_connection()
    if not conn_result:
        logger.error("SurrealDB连接测试失败")
        return
    
    # 测试表结构
    schema_result = await test_surreal_schema()
    if not schema_result:
        logger.warning("SurrealDB表结构测试不完整，继续其他测试")
    
    # 创建测试会话
    session_result = await create_test_session()
    if not session_result:
        logger.error("创建测试会话失败")
        return
    
    logger.info("所有测试完成")

if __name__ == "__main__":
    try:
        # 运行测试
        asyncio.run(run_tests())
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
    except Exception as e:
        logger.error(f"测试失败: {e}")
