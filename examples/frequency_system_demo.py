# examples/frequency_system_demo.py
"""
频率感知系统演示脚本，展示如何将频率感知系统与对话系统整合
"""
import asyncio
import time
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rainbow_agent.frequency import (
    ContextSampler,
    FrequencySenseCore,
    ExpressionPlanner,
    ExpressionGenerator,
    ExpressionDispatcher,
    FrequencyIntegrator
)
from rainbow_agent.memory.memory import Memory
from examples.mock_memory_sync import MockMemorySync
from rainbow_agent.utils.logger import get_logger, setup_logger

# 设置日志
setup_logger(level="INFO")
logger = get_logger(__name__)

class MockMemory(Memory):
    """模拟记忆系统，用于演示"""
    
    def __init__(self):
        """初始化模拟记忆系统"""
        self.memories = []
        self.data = {}  # 用于扩展功能
    
    def save(self, user_input: str, assistant_response: str) -> None:
        """保存对话记录到记忆系统"""
        timestamp = datetime.now().isoformat()
        memory_item = {
            "timestamp": timestamp,
            "user_input": user_input,
            "assistant_response": assistant_response
        }
        
        self.memories.append(memory_item)
        logger.info(f"保存对话记录: {user_input} -> {assistant_response}")
    
    def retrieve(self, query: str, limit: int = 5) -> List[str]:
        """从记忆系统中检索相关记忆"""
        # 简单实现：返回最近的n条记忆
        recent_memories = self.memories[-limit:] if self.memories else []
        
        # 格式化返回的记忆
        formatted_memories = []
        for memory in recent_memories:
            formatted = (
                f"时间: {memory['timestamp']}\n"
                f"用户: {memory['user_input']}\n"
                f"助手: {memory['assistant_response']}"
            )
            formatted_memories.append(formatted)
        
        logger.info(f"检索记忆，查询: {query}, 结果数: {len(formatted_memories)}")
        return formatted_memories
    
    # 扩展方法，用于频率感知系统
    async def store(self, collection: str, data: Dict[str, Any]) -> bool:
        """存储数据到指定集合"""
        if collection not in self.data:
            self.data[collection] = []
        
        # 添加ID如果没有
        if "_id" not in data:
            data["_id"] = f"{collection}:{len(self.data[collection])}"
        
        self.data[collection].append(data)
        logger.info(f"存储数据到集合 {collection}: {data}")
        return True
    
    async def retrieve_data(self, collection: str, query: Dict[str, Any] = None) -> list:
        """从指定集合检索数据"""
        if collection not in self.data:
            return []
        
        if not query:
            return self.data[collection]
        
        # 简单查询匹配
        results = []
        for item in self.data[collection]:
            match = True
            for k, v in query.items():
                if k not in item or item[k] != v:
                    match = False
                    break
            
            if match:
                results.append(item)
        
        logger.info(f"从集合 {collection} 检索数据，查询: {query}, 结果数: {len(results)}")
        return results
    
    async def update(self, collection: str, id_value: str, data: Dict[str, Any]) -> bool:
        """更新指定集合中的数据"""
        if collection not in self.data:
            return False
        
        for i, item in enumerate(self.data[collection]):
            if item.get("_id") == id_value:
                self.data[collection][i].update(data)
                logger.info(f"更新集合 {collection} 中的数据，ID: {id_value}")
                return True
        
        return False
    
    async def delete(self, collection: str, id_value: str) -> bool:
        """删除指定集合中的数据"""
        if collection not in self.data:
            return False
        
        for i, item in enumerate(self.data[collection]):
            if item.get("_id") == id_value:
                del self.data[collection][i]
                logger.info(f"删除集合 {collection} 中的数据，ID: {id_value}")
                return True
        
        return False


class DialogueSystemSimulator:
    """对话系统模拟器，用于演示频率感知系统的集成"""
    
    def __init__(self):
        """初始化对话系统模拟器"""
        # 创建模拟记忆系统
        self.memory = MockMemory()
        
        # 创建记忆同步组件
        self.memory_sync = MockMemorySync(self.memory)
        
        # 创建频率感知系统集成器
        self.frequency_integrator = FrequencyIntegrator(
            self.memory,
            self._handle_expression_output,
            {"memory_sync_config": {"memory_sync_instance": self.memory_sync}}
        )
        
        # 会话ID
        self.session_id = "demo_session"
        
        # 用户ID
        self.user_id = "demo_user"
        
        # 对话历史
        self.conversation_history = []
        
        # 监控任务
        self.monitoring_task = None
    
    async def _init_user_data(self):
        """初始化用户数据"""
        # 存储用户信息
        await self.memory.store("users", {
            "_id": self.user_id,
            "name": "演示用户",
            "interaction_count": 5,
            "preferences": {
                "topics": ["技术", "音乐", "电影"],
                "communication_style": "friendly"
            },
            "created_at": time.time()
        })
    
    async def initialize(self):
        """初始化对话系统模拟器"""
        # 初始化用户数据
        await self._init_user_data()
        
        logger.info("对话系统模拟器初始化完成")
    
    async def start_monitoring(self):
        """启动频率感知系统监控"""
        # 启动频率感知系统
        await self.frequency_integrator.start()
        
        # 注册用户活动
        await self.frequency_integrator.register_user_activity(
            self.session_id,
            self.user_id,
            "login"
        )
        
        logger.info("频率感知系统监控已启动")
        
    async def start(self):
        """启动对话系统模拟器（兼容旧接口）"""
        # 初始化
        await self.initialize()
        
        # 启动监控
        await self.start_monitoring()
        
        logger.info("对话系统模拟器启动完成")
    
    async def stop(self):
        """停止对话系统模拟器"""
        # 停止频率感知系统
        await self.frequency_integrator.stop()
        
        logger.info("对话系统模拟器已停止")
    
    async def process_user_input(self, message: str):
        """处理用户输入"""
        logger.info(f"用户输入: {message}")
        
        # 添加到对话历史
        self.conversation_history.append(f"用户: {message}")
        
        # 更新频率感知系统上下文
        await self.frequency_integrator.process_user_message(
            self.session_id,
            self.user_id,
            message
        )
        
        # 模拟系统响应
        response = await self._generate_response(message)
        
        # 添加到对话历史
        self.conversation_history.append(f"系统: {response}")
        
        # 更新频率感知系统上下文
        await self.frequency_integrator.process_system_response(
            self.session_id,
            response
        )
        
        # 尝试触发频率表达
        await self.frequency_integrator.trigger_expression(self.session_id)
        
        return response
    
    async def _generate_response(self, message: str) -> str:
        """生成系统响应"""
        # 增强的响应逻辑，处理更多类型的用户输入
        if "你好" in message or "您好" in message:
            return "你好！很高兴见到你。有什么我可以帮助你的吗？"
        elif "天气" in message:
            return "今天天气晴朗，温度适宜，是个出门的好日子。"
        elif "名字" in message:
            return "我是彩虹城AI助手，你可以叫我小彩。"
        elif "介绍" in message and ("你自己" in message or "自己" in message):
            return "我是彩虹城AI助手，一个融合了频率感知系统的智能对话助手。我能够根据对话上下文和用户活动，主动进行表达和互动，让对话更加自然流畅。"
        elif "音乐" in message:
            return "我也喜欢音乐！不同类型的音乐能带给人不同的情绪体验。你喜欢什么风格的音乐呢？"
        elif "电影" in message:
            if "星际穿越" in message:
                return "《星际穿越》是一部非常精彩的科幻电影，探讨了时间、爱与人性的主题。你对电影中的哪个部分印象最深刻？"
            else:
                return "电影是一种很好的艺术形式，能够带我们进入不同的世界。你最近看的电影怎么样？"
        elif "谢谢" in message:
            return "不客气，随时为你服务！"
        elif "再见" in message or "拜拜" in message:
            return "再见！期待下次与你交流。"
        elif "爱好" in message or "兴趣" in message:
            return "作为AI助手，我喜欢学习新知识、解决问题和与人交流。你有什么特别的爱好吗？"
        elif "工作" in message or "职业" in message:
            return "我的工作是协助用户，提供信息和支持。你是做什么工作的呢？"
        elif "学习" in message or "教育" in message:
            return "学习是一个持续的过程，我也在不断学习新知识。你最近在学习什么新东西吗？"
        else:
            # 分析消息关键词，尝试给出更相关的回复
            if any(word in message for word in ["什么", "如何", "为什么", "怎么"]):
                return "这是个很好的问题。作为演示系统，我的知识有限，但在实际应用中，我会根据上下文提供更详细的回答。"
            elif any(word in message for word in ["想", "认为", "觉得", "感觉"]):
                return "谢谢分享你的想法。在实际对话中，我会根据你的观点展开更深入的讨论。"
            else:
                return "我明白了。你还有其他想聊的话题吗？我很乐意继续我们的对话。"
    
    async def _handle_expression_output(self, content: str, metadata: Dict[str, Any]) -> bool:
        """处理表达输出"""
        logger.info(f"频率表达: {content}")
        logger.info(f"表达元数据: {json.dumps(metadata, ensure_ascii=False)}")
        
        # 添加到对话历史
        self.conversation_history.append(f"系统(主动): {content}")
        
        return True
    
    def print_conversation(self):
        """打印对话历史"""
        print("\n===== 对话历史 =====")
        for message in self.conversation_history:
            print(message)
        print("====================\n")
        
        # 刷新输出缓冲区，确保内容立即显示
        import sys
        sys.stdout.flush()


async def auto_demo():
    """自动演示模式"""
    try:
        # 创建对话系统模拟器
        dialogue_system = DialogueSystemSimulator()
        
        # 初始化频率感知系统
        await dialogue_system.initialize()
        
        # 启动频率感知系统监控
        await dialogue_system.start_monitoring()
        
        print("=== 彩虹城AI对话系统自动演示 ===\n")
        print("这个演示将展示频率感知系统的功能，包括上下文感知、自主表达和记忆同步。\n")
        
        # 预设对话
        demo_conversations = [
            "你好，我是小明",
            "今天天气怎么样？",
            "你能介绍一下你自己吗？",
            "我喜欢听音乐，你呢？",
            "我最近看了一部电影，叫《星际穿越》"
        ]
        
        # 模拟对话
        for i, user_input in enumerate(demo_conversations):
            print(f"\n[用户输入] {user_input}")
            
            # 处理用户输入
            await dialogue_system.process_user_input(user_input)
            
            # 打印对话历史
            dialogue_system.print_conversation()
            
            # 等待一段时间，让频率感知系统有机会触发表达
            if i < len(demo_conversations) - 1:
                print("\n[系统正在思考...]")
                await asyncio.sleep(3)
        
        # 等待一段较长时间，让频率感知系统有更多机会触发自主表达
        print("\n[等待系统自主表达...]")
        await asyncio.sleep(5)
        
        # 停止频率感知系统
        await dialogue_system.stop()
        
        print("\n=== 演示结束 ===")
        print("频率感知系统已经完成了对话模拟，展示了上下文感知和自主表达能力。")
        print("系统会根据用户活动、时间流逝和对话上下文来决定何时主动表达。")
        print("所有的交互都被记录到了记忆系统中，用于未来的频率感知决策。")
        
    except Exception as e:
        logger.error(f"自动演示运行出错: {e}")
        import traceback
        traceback.print_exc()

async def interactive_demo():
    """交互式演示模式"""
    try:
        # 创建对话系统模拟器
        dialogue_system = DialogueSystemSimulator()
        
        # 初始化频率感知系统
        await dialogue_system.initialize()
        
        # 启动频率感知系统监控
        await dialogue_system.start_monitoring()
        
        # 模拟用户输入
        print("欢迎使用彩虹城AI对话系统演示！")
        print("输入 'exit' 退出\n")
        
        while True:
            try:
                user_input = input("\n> ")
                
                if user_input.lower() == "exit":
                    break
                
                # 处理用户输入
                await dialogue_system.process_user_input(user_input)
                
                # 打印对话历史
                dialogue_system.print_conversation()
            except EOFError:
                logger.warning("输入流结束，退出循环")
                break
            except KeyboardInterrupt:
                logger.info("用户中断，退出循环")
                break
            except Exception as e:
                logger.error(f"处理用户输入时出错: {e}")
        
        # 停止频率感知系统
        await dialogue_system.stop()
        
        print("\n感谢使用彩虹城AI对话系统演示！")
    except Exception as e:
        logger.error(f"交互式演示运行出错: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    try:
        # 默认使用自动演示模式
        demo_mode = "auto"
        
        # 检查命令行参数
        if len(sys.argv) > 1 and sys.argv[1] == "interactive":
            demo_mode = "interactive"
        
        if demo_mode == "auto":
            await auto_demo()
        else:
            await interactive_demo()
            
    except Exception as e:
        logger.error(f"主程序运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())
