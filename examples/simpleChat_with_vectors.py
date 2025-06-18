"""
简单聊天示例 - 带向量存储功能

演示如何在聊天过程中生成并存储消息的嵌入向量，使用SurrealDB存储
"""
import os
import sys
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# 添加项目根目录到Python路径，确保能够导入rainbow_agent模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 检查依赖项
def check_dependencies():
    required_packages = [
        ('python-dotenv', 'dotenv'),
        ('openai', 'openai'),
        ('surrealdb', 'surrealdb')
    ]
    
    missing = []
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        print("错误: 缺少必要的依赖包:")
        for package in missing:
            print(f"  - {package}")
        print("\n请使用以下命令安装所需依赖:")
        print(f"pip install {' '.join(missing)}")
        sys.exit(1)

# 检查依赖项
check_dependencies()

# 导入 OpenAI 服务
from rainbow_agent.ai.openai_service import OpenAIService

# 导入 SurrealDB 存储工厂
from rainbow_agent.storage.surreal_factory import SurrealStorageFactory

# 导入 OpenAI 客户端
from openai import OpenAI

# 导入配置系统
from rainbow_agent.config.settings import get_settings

# 配置SurrealDB连接
SURREAL_URL = "ws://localhost:8000/rpc"  # 默认SurrealDB WebSocket RPC URL
SURREAL_NAMESPACE = "rainbow"
SURREAL_DATABASE = "test"  # 使用test数据库
SURREAL_TABLE = "chat_messages"  # 存储消息的表名

def get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """生成文本的嵌入向量
    
    Args:
        text: 需要生成嵌入向量的文本
        model: 使用的嵌入模型，默认为 text-embedding-3-small
        
    Returns:
        嵌入向量，通常是1536维的浮点数列表
        
    Raises:
        Exception: 当API调用失败时抛出异常
    """
    try:
        # 获取配置实例
        settings = get_settings()
        
        # 获取API密钥
        api_key = settings.get("api.api_key")
        
        if not api_key:
            print("警告: 未设置 OpenAI API 密钥，无法生成嵌入向量")
            return [0.0] * 1536  # 返回零向量作为默认值
        
        # 创建 OpenAI 客户端
        client_kwargs = {
            "api_key": api_key,
            "timeout": settings.get("api.timeout", 60)
        }
        
        # 添加代理配置（如果有）
        proxy = settings.get("api.proxy")
        if proxy:
            client_kwargs["http_client"] = {"proxy": proxy}
        
        # 添加自定义基础URL（如果有）
        base_url = settings.get("api.base_url")
        if base_url:
            client_kwargs["base_url"] = base_url
        
        # 创建客户端
        client = OpenAI(**client_kwargs)
        
        print(f"调用 OpenAI API 生成嵌入向量，模型: {model}, 文本长度: {len(text)}")
        
        # 调用 OpenAI 的 embeddings API
        response = client.embeddings.create(
            input=text,
            model=model
        )
        
        # 提取嵌入向量
        embedding = response.data[0].embedding
        print(f"成功生成嵌入向量，维度: {len(embedding)}")
        
        return embedding
    except Exception as e:
        print(f"生成嵌入向量失败: {e}")
        raise

async def init_db() -> None:
    """初始化SurrealDB，创建消息表和向量表"""
    try:
        # 创建SurrealDB存储工厂
        storage_factory = SurrealStorageFactory(SURREAL_URL, SURREAL_NAMESPACE, SURREAL_DATABASE)
        
        # 获取存储实例
        storage = storage_factory.get_storage()
        
        # 连接到SurrealDB
        await storage.connect()
        
        # 创建消息表（如果不存在）
        # SurrealDB会自动创建表，但我们可以定义一些初始化查询
        # 这里我们创建一个表并定义一些索引
        query = f"""
        DEFINE TABLE {SURREAL_TABLE} SCHEMALESS;
        DEFINE FIELD timestamp ON TABLE {SURREAL_TABLE} TYPE datetime;
        DEFINE FIELD role ON TABLE {SURREAL_TABLE} TYPE string;
        DEFINE FIELD content ON TABLE {SURREAL_TABLE} TYPE string;
        DEFINE FIELD embedding ON TABLE {SURREAL_TABLE} TYPE array;
        DEFINE FIELD model ON TABLE {SURREAL_TABLE} TYPE string;
        
        -- 创建索引以加快查询
        DEFINE INDEX idx_timestamp ON TABLE {SURREAL_TABLE} FIELDS timestamp;
        DEFINE INDEX idx_role ON TABLE {SURREAL_TABLE} FIELDS role;
        """
        
        # 执行查询
        result = await storage.query(query)
        print(f"数据库初始化完成: {SURREAL_URL}/{SURREAL_NAMESPACE}/{SURREAL_DATABASE}/{SURREAL_TABLE}")
        print(f"初始化结果: {result}")
        
        return storage
    except Exception as e:
        print(f"初始化数据库失败: {e}")
        import traceback
        print(traceback.format_exc())
        raise

async def save_message(storage, role: str, content: str, embedding: Optional[List[float]] = None, model: Optional[str] = None) -> str:
    """保存消息和嵌入向量到SurrealDB
    
    Args:
        storage: SurrealDB存储实例
        role: 消息发送者角色 ('human' 或 'ai')
        content: 消息内容
        embedding: 消息的嵌入向量
        model: 用于生成嵌入的模型名称
        
    Returns:
        新插入消息的ID
    """
    try:
        # 获取当前时间戳
        # SurrealDB需要datetime对象而不是ISO格式字符串
        timestamp = datetime.now()
        
        # 准备消息数据
        message_data = {
            "timestamp": timestamp,
            "role": role,
            "content": content,
            "embedding": embedding,
            "model": model
        }
        
        # 插入消息记录
        result = await storage.create(SURREAL_TABLE, message_data)
        
        # 从结果中提取ID
        try:
            # 打印结果以便调试
            print(f"创建记录结果类型: {type(result)}, 值: {result}")
            
            # 处理不同的返回格式
            if isinstance(result, list) and len(result) > 0:
                # 如果是列表并且有元素
                if isinstance(result[0], dict) and "id" in result[0]:
                    # 如果第一个元素是字典并且有id字段
                    full_id = result[0]["id"]
                    message_id = full_id.split(":")[-1] if ":" in full_id else full_id
                    print(f"消息已保存，ID: {message_id}")
                    return message_id
                else:
                    # 其他列表格式
                    print(f"消息已保存，但无法提取ID: {result}")
                    return str(result)
            elif isinstance(result, dict) and "id" in result:
                # 如果是字典并且有id字段
                full_id = result["id"]
                message_id = full_id.split(":")[-1] if ":" in full_id else full_id
                print(f"消息已保存，ID: {message_id}")
                return message_id
            else:
                # 其他情况
                print(f"消息已保存，但无法提取ID: {result}")
                return str(result)
        except Exception as e:
            print(f"处理返回结果时出错: {e}")
            return str(result)
    except Exception as e:
        print(f"保存消息失败: {e}")
        import traceback
        print(traceback.format_exc())
        return ""

async def get_messages(storage, limit: int = 10) -> List[Dict[str, Any]]:
    """获取最近的消息记录
    
    Args:
        storage: SurrealDB存储实例
        limit: 返回的消息数量限制
        
    Returns:
        消息记录列表
    """
    try:
        # 查询最近的消息，按时间戳降序排序
        query = f"""
        SELECT * FROM {SURREAL_TABLE}
        ORDER BY timestamp DESC
        LIMIT {limit};
        """
        
        # 执行查询
        result = await storage.query(query)
        
        # 处理结果
        if result and len(result) > 0 and result[0]:
            # SurrealDB查询结果通常在第一个元素的result字段中
            messages = result[0].get("result", [])
            print(f"获取到 {len(messages)} 条消息")
            
            # 返回按时间正序排列的消息
            return list(reversed(messages))
        else:
            print("获取消息失败或没有消息")
            return []
    except Exception as e:
        print(f"获取消息失败: {e}")
        import traceback
        print(traceback.format_exc())
        return []

async def search_similar_messages(storage, query_text: str, embedding_model: str = "text-embedding-3-small", top_k: int = 3) -> List[Dict[str, Any]]:
    """搜索与查询文本语义相似的消息
    
    Args:
        storage: SurrealDB存储实例
        query_text: 查询文本
        embedding_model: 用于生成嵌入向量的模型
        top_k: 返回的最相似消息数量
        
    Returns:
        相似消息列表，按相似度降序排列
    """
    try:
        # 为查询文本生成嵌入向量
        query_embedding = get_embedding(query_text, model=embedding_model)
        
        # 获取所有带有嵌入向量的消息
        query = f"""
        SELECT * FROM {SURREAL_TABLE}
        WHERE embedding != NONE;
        """
        
        # 执行查询
        result = await storage.query(query)
        
        # 处理结果
        messages = []
        if result and len(result) > 0 and result[0]:
            messages = result[0].get("result", [])
        
        # 计算余弦相似度并排序
        results = []
        for message in messages:
            # 确保消息有嵌入向量
            message_embedding = message.get("embedding")
            if not message_embedding:
                continue
            
            # 计算余弦相似度
            similarity = cosine_similarity(query_embedding, message_embedding)
            
            # 添加到结果列表
            results.append({
                "id": message.get("id", "").split(":")[-1] if ":" in message.get("id", "") else message.get("id", ""),
                "timestamp": message.get("timestamp", ""),
                "role": message.get("role", ""),
                "content": message.get("content", ""),
                "similarity": similarity
            })
        
        # 按相似度降序排序并返回前top_k个结果
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
    except Exception as e:
        print(f"搜索相似消息失败: {e}")
        import traceback
        print(traceback.format_exc())
        return []

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """计算两个向量的余弦相似度
    
    Args:
        vec1: 第一个向量
        vec2: 第二个向量
        
    Returns:
        余弦相似度，范围为[-1, 1]
    """
    # 确保向量长度相同
    if len(vec1) != len(vec2):
        raise ValueError(f"向量长度不匹配: {len(vec1)} vs {len(vec2)}")
    
    # 计算点积
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # 计算向量模长
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5
    
    # 避免除以零
    if magnitude1 == 0 or magnitude2 == 0:
        return 0
    
    # 计算余弦相似度
    return dot_product / (magnitude1 * magnitude2)

async def chat_loop() -> None:
    """主聊天循环"""
    print("\n=== 向量存储聊天示例 (SurrealDB) ===")
    print("输入消息开始聊天，输入 'q' 退出，输入 'search:关键词' 搜索相似消息")
    
    # 初始化数据库并获取存储实例
    storage = await init_db()
    
    # 创建OpenAI服务实例
    openai_service = OpenAIService()
    
    # 嵌入模型
    embedding_model = "text-embedding-3-small"
    
    while True:
        # 获取用户输入
        user_input = input("\n用户: ")
        
        # 检查是否退出
        if user_input.lower() == 'q':
            break
        
        # 检查是否为搜索命令
        if user_input.lower().startswith("search:"):
            query = user_input[7:].strip()
            print(f"\n搜索相似消息: '{query}'")
            
            # 搜索相似消息
            similar_messages = await search_similar_messages(storage, query, embedding_model)
            
            # 显示结果
            print("\n搜索结果:")
            for i, msg in enumerate(similar_messages):
                print(f"{i+1}. [{msg['role']}] {msg['content']} (相似度: {msg['similarity']:.4f})")
            
            continue
        
        # 为用户消息生成嵌入向量
        try:
            user_embedding = get_embedding(user_input, model=embedding_model)
            print(f"已生成用户消息的嵌入向量 (维度: {len(user_embedding)})")
        except Exception as e:
            print(f"生成嵌入向量失败: {e}")
            user_embedding = None
        
        # 保存用户消息
        await save_message(storage, "human", user_input, user_embedding, embedding_model)
        
        # 获取AI回复
        # 这里使用简单回复，实际应用中可以使用更复杂的对话管理
        try:
            messages = [{"role": "user", "content": user_input}]
            ai_response = openai_service.generate_response(messages)
        except Exception as e:
            ai_response = f"抱歉，生成回复时出现错误: {str(e)}"
        
        print(f"\nAI: {ai_response}")
        
        # 为AI回复生成嵌入向量
        try:
            ai_embedding = get_embedding(ai_response, model=embedding_model)
            print(f"已生成AI回复的嵌入向量 (维度: {len(ai_embedding)})")
        except Exception as e:
            print(f"生成嵌入向量失败: {e}")
            ai_embedding = None
        
        # 保存AI回复
        await save_message(storage, "ai", ai_response, ai_embedding, embedding_model)

async def main() -> None:
    """主函数"""
    try:
        # 运行聊天循环
        await chat_loop()
    except Exception as e:
        print(f"程序运行出错: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
