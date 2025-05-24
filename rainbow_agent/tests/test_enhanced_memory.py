"""
增强记忆系统测试脚本

测试分层记忆系统、相关性检索和记忆压缩功能
"""
import os
import sys
import time
from datetime import datetime, timedelta
import json
import sqlite3
import numpy as np

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rainbow_agent.memory.hierarchical_memory import HierarchicalMemory, MemoryLayer
from rainbow_agent.memory.relevance_retrieval import RelevanceRetrieval
from rainbow_agent.memory.memory_compression import MemoryCompression
from rainbow_agent.memory.enhanced_memory import EnhancedMemory
from rainbow_agent.utils.logger import get_logger

logger = get_logger(__name__)

# 测试数据库路径
TEST_DB_PATH = "test_memory.db"


def clean_test_db():
    """清理测试数据库"""
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
        logger.info(f"已删除测试数据库: {TEST_DB_PATH}")


def test_memory_layer():
    """测试记忆层功能"""
    print("\n=== 测试记忆层 ===")
    
    # 创建记忆层
    memory_layer = MemoryLayer(name="test_layer", capacity=5, ttl=10)
    
    # 添加记忆
    for i in range(7):
        timestamp = (datetime.now() - timedelta(seconds=i)).isoformat()
        memory_layer.add({
            "timestamp": timestamp,
            "content": f"测试内容 {i}"
        })
    
    # 验证容量限制
    memories = memory_layer.get()
    assert len(memories) == 5, f"记忆层容量应为5，实际为{len(memories)}"
    print(f"记忆层容量限制测试通过，当前记忆数: {len(memories)}")
    
    # 验证最新的记忆被保留
    latest_content = memories[-1]["content"]
    assert latest_content == "测试内容 6", f"最新记忆应为'测试内容 6'，实际为'{latest_content}'"
    print(f"记忆层保留最新记忆测试通过，最新记忆: {latest_content}")
    
    # 测试TTL
    print("等待记忆过期...")
    time.sleep(11)  # 等待记忆过期
    expired_memories = memory_layer.get()
    assert len(expired_memories) == 0, f"所有记忆应已过期，实际剩余{len(expired_memories)}"
    print("记忆层TTL测试通过，所有记忆已过期")
    
    print("记忆层测试完成")


def test_hierarchical_memory():
    """测试分层记忆系统"""
    print("\n=== 测试分层记忆系统 ===")
    
    clean_test_db()
    
    # 创建分层记忆系统，使用较短的TTL便于测试
    memory = HierarchicalMemory(
        working_memory_capacity=3,
        working_memory_ttl=5,  # 5秒
        short_term_capacity=5,
        short_term_ttl=10,  # 10秒
        long_term_capacity=10,
        db_path=TEST_DB_PATH
    )
    
    # 添加测试数据
    test_data = [
        ("你好，我是小明", "你好小明，我能帮你什么？"),
        ("今天天气怎么样？", "今天天气晴朗，气温25°C"),
        ("我喜欢打篮球", "篮球是一项很好的运动，有助于身体健康"),
        ("推荐一本书", "我推荐《三体》，这是一部优秀的科幻小说"),
        ("谢谢", "不客气，有任何问题随时问我")
    ]
    
    for i, (user_input, assistant_response) in enumerate(test_data):
        importance = 0.5 + i * 0.1  # 逐渐增加重要性
        memory.save(user_input, assistant_response, importance)
        print(f"已保存对话 {i+1}，重要性: {importance:.1f}")
    
    # 测试工作记忆
    working_memories = memory.working_memory.get()
    assert len(working_memories) == 3, f"工作记忆应有3条，实际有{len(working_memories)}"
    print(f"工作记忆测试通过，当前记忆数: {len(working_memories)}")
    
    # 测试短期记忆
    short_term_memories = memory.short_term_memory.get()
    assert len(short_term_memories) == 5, f"短期记忆应有5条，实际有{len(short_term_memories)}"
    print(f"短期记忆测试通过，当前记忆数: {len(short_term_memories)}")
    
    # 测试长期记忆
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM long_term_memories")
    long_term_count = cursor.fetchone()[0]
    conn.close()
    
    # 只有重要性>=0.7的记忆会进入长期记忆
    expected_long_term = sum(1 for i in range(len(test_data)) if 0.5 + i * 0.1 >= 0.7)
    assert long_term_count == expected_long_term, f"长期记忆应有{expected_long_term}条，实际有{long_term_count}"
    print(f"长期记忆测试通过，当前记忆数: {long_term_count}")
    
    # 测试记忆检索
    retrieved = memory.retrieve("天气", limit=2)
    assert len(retrieved) > 0, "应检索到与'天气'相关的记忆"
    print(f"记忆检索测试通过，检索到 {len(retrieved)} 条记忆")
    
    # 测试记忆层检索
    layer_retrieved = memory.retrieve_by_layer("天气", layer="working", limit=2)
    assert len(layer_retrieved) <= 2, f"应从工作记忆层检索到不超过2条记忆，实际检索到{len(layer_retrieved)}条"
    print(f"记忆层检索测试通过，从工作记忆层检索到 {len(layer_retrieved)} 条记忆")
    
    # 测试TTL
    print("等待工作记忆过期...")
    time.sleep(6)  # 等待工作记忆过期
    working_memories_after = memory.working_memory.get()
    assert len(working_memories_after) == 0, f"工作记忆应已过期，实际剩余{len(working_memories_after)}"
    print("工作记忆TTL测试通过，所有工作记忆已过期")
    
    print("等待短期记忆过期...")
    time.sleep(5)  # 再等待5秒，短期记忆也应过期
    short_term_memories_after = memory.short_term_memory.get()
    assert len(short_term_memories_after) == 0, f"短期记忆应已过期，实际剩余{len(short_term_memories_after)}"
    print("短期记忆TTL测试通过，所有短期记忆已过期")
    
    print("分层记忆系统测试完成")


def test_relevance_retrieval():
    """测试相关性检索"""
    print("\n=== 测试相关性检索 ===")
    
    clean_test_db()
    
    # 创建分层记忆系统
    memory = HierarchicalMemory(db_path=TEST_DB_PATH)
    
    # 创建相关性检索系统
    retrieval = RelevanceRetrieval(db_path=TEST_DB_PATH)
    
    # 添加测试数据
    test_data = [
        ("北京今天天气怎么样？", "北京今天天气晴朗，气温25°C，空气质量良好"),
        ("推荐一本科幻小说", "我推荐《三体》，这是一部优秀的中国科幻小说"),
        ("如何学习人工智能", "学习人工智能需要掌握数学、编程和机器学习理论"),
        ("上海有哪些好玩的地方", "上海有外滩、东方明珠、迪士尼乐园等著名景点"),
        ("Python如何处理JSON数据", "Python可以使用json模块处理JSON数据，包括解析和生成")
    ]
    
    # 保存记忆并生成嵌入
    for i, (user_input, assistant_response) in enumerate(test_data):
        # 保存到分层记忆
        memory.save(user_input, assistant_response, importance=0.8)
        
        # 获取最新保存的记忆ID
        conn = sqlite3.connect(TEST_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM long_term_memories")
        memory_id = cursor.fetchone()[0]
        conn.close()
        
        # 为用户输入和助手回复生成嵌入向量
        timestamp = datetime.now().isoformat()
        retrieval.save_embedding(memory_id, user_input, "user_input", timestamp)
        retrieval.save_embedding(memory_id, assistant_response, "assistant_response", timestamp)
        
        print(f"已保存记忆 {i+1} 并生成嵌入向量")
    
    # 测试相关性检索
    test_queries = [
        "北京的天气状况",
        "有什么好的科幻书籍",
        "人工智能学习方法",
        "上海旅游景点",
        "如何用Python处理JSON"
    ]
    
    for i, query in enumerate(test_queries):
        results = retrieval.retrieve_relevant_memories(query, limit=2)
        assert len(results) > 0, f"查询'{query}'应返回相关记忆"
        print(f"查询: '{query}'")
        print(f"  - 找到 {len(results)} 条相关记忆")
        for j, result in enumerate(results):
            print(f"  - 相关度: {result['similarity']:.2f}, 内容: {result['user_input'][:30]}...")
    
    # 测试混合检索
    hybrid_results = retrieval.hybrid_retrieval("天气情况", recency_limit=2, relevance_limit=2)
    assert len(hybrid_results) > 0, "混合检索应返回结果"
    print(f"混合检索测试通过，返回 {len(hybrid_results)} 条结果")
    
    print("相关性检索测试完成")


def test_memory_compression():
    """测试记忆压缩"""
    print("\n=== 测试记忆压缩 ===")
    
    clean_test_db()
    
    # 创建记忆压缩系统
    compression = MemoryCompression(db_path=TEST_DB_PATH)
    
    # 创建测试对话
    conversation = []
    for i in range(10):
        timestamp = (datetime.now() - timedelta(minutes=i)).isoformat()
        if i % 2 == 0:
            user_input = f"这是第{i+1}个问题，关于天气的讨论"
            assistant_response = f"这是第{i+1}个回答，北京今天天气晴朗，气温{20+i}°C"
        else:
            user_input = f"这是第{i+1}个问题，关于科技的讨论"
            assistant_response = f"这是第{i+1}个回答，人工智能技术正在快速发展"
        
        conversation.append({
            "timestamp": timestamp,
            "user_input": user_input,
            "assistant_response": assistant_response,
            "importance": 0.5 + i * 0.05
        })
    
    # 测试对话压缩
    compression_result = compression.compress_conversation(conversation)
    
    assert "summary" in compression_result, "压缩结果应包含摘要"
    assert "key_points" in compression_result, "压缩结果应包含关键点"
    assert len(compression_result["summary"]) > 0, "摘要不应为空"
    
    print("对话压缩测试通过")
    print(f"原始对话: {compression_result['original_count']} 条")
    print(f"压缩比例: {compression_result['compression_ratio']:.2f}")
    print(f"摘要长度: {len(compression_result['summary'])} 字符")
    print(f"关键点数量: {len(compression_result['key_points'])}")
    
    # 测试摘要检索
    summaries = compression.get_summaries(limit=5)
    assert len(summaries) > 0, "应能检索到摘要"
    print(f"摘要检索测试通过，检索到 {len(summaries)} 条摘要")
    
    print("记忆压缩测试完成")


def test_enhanced_memory():
    """测试增强记忆系统"""
    print("\n=== 测试增强记忆系统 ===")
    
    clean_test_db()
    
    # 创建增强记忆系统
    memory = EnhancedMemory(
        db_path=TEST_DB_PATH,
        working_memory_capacity=5,
        working_memory_ttl=3600,
        short_term_capacity=10,
        short_term_ttl=86400,
        long_term_capacity=100,
        auto_compress_threshold=20
    )
    
    # 添加测试数据
    test_data = [
        ("北京今天天气怎么样？", "北京今天天气晴朗，气温25°C，空气质量良好"),
        ("推荐一本科幻小说", "我推荐《三体》，这是一部优秀的中国科幻小说"),
        ("如何学习人工智能", "学习人工智能需要掌握数学、编程和机器学习理论"),
        ("上海有哪些好玩的地方", "上海有外滩、东方明珠、迪士尼乐园等著名景点"),
        ("Python如何处理JSON数据", "Python可以使用json模块处理JSON数据，包括解析和生成"),
        ("人工智能的未来发展趋势", "人工智能未来将更加智能化、个性化，并与各行业深度融合"),
        ("如何保持健康的生活方式", "健康生活需要均衡饮食、规律作息、适当运动和良好心态")
    ]
    
    # 保存记忆
    for i, (user_input, assistant_response) in enumerate(test_data):
        importance = 0.6 + i * 0.05  # 逐渐增加重要性
        memory.save(user_input, assistant_response, importance)
        print(f"已保存对话 {i+1}，重要性: {importance:.2f}")
    
    # 测试基础检索
    basic_results = memory.retrieve("天气", limit=3, use_relevance=False)
    assert len(basic_results) > 0, "基础检索应返回结果"
    print(f"基础检索测试通过，返回 {len(basic_results)} 条结果")
    
    # 测试相关性检索
    relevance_results = memory.retrieve("天气状况", limit=3, use_relevance=True)
    assert len(relevance_results) > 0, "相关性检索应返回结果"
    print(f"相关性检索测试通过，返回 {len(relevance_results)} 条结果")
    for i, result in enumerate(relevance_results):
        print(f"  - 结果 {i+1}: {result.get('user_input', '')[:30]}...")
    
    # 测试记忆层检索
    layer_results = memory.retrieve_by_layer("科幻", layer="working", limit=3)
    print(f"记忆层检索测试通过，从工作记忆层返回 {len(layer_results)} 条结果")
    
    # 测试相关性检索
    relevance_specific = memory.retrieve_by_relevance("人工智能技术", limit=3)
    assert len(relevance_specific) > 0, "特定相关性检索应返回结果"
    print(f"特定相关性检索测试通过，返回 {len(relevance_specific)} 条结果")
    
    # 测试对话压缩
    conversation = []
    for i in range(5):
        conversation.append({
            "timestamp": datetime.now().isoformat(),
            "user_input": test_data[i][0],
            "assistant_response": test_data[i][1]
        })
    
    compression_result = memory.compress_conversation(conversation)
    assert "summary" in compression_result, "压缩结果应包含摘要"
    print("对话压缩测试通过")
    print(f"摘要: {compression_result['summary'][:100]}...")
    
    # 测试记忆统计
    stats = memory.get_memory_stats()
    print("记忆统计:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    print("增强记忆系统测试完成")


def run_all_tests():
    """运行所有测试"""
    print("\n========== 开始测试增强记忆系统 ==========")
    
    try:
        test_memory_layer()
        test_hierarchical_memory()
        test_relevance_retrieval()
        test_memory_compression()
        test_enhanced_memory()
        
        print("\n========== 所有测试通过 ==========")
    except AssertionError as e:
        print(f"\n测试失败: {e}")
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
    finally:
        clean_test_db()


if __name__ == "__main__":
    run_all_tests()
