# rainbow_agent/frequency/expression_planner.py
"""
表达规划器，负责规划表达策略，基于关系阶段调整表达方式
"""
from typing import Dict, Any, List, Optional
import random
from ..utils.logger import get_logger
from ..memory.memory import Memory

logger = get_logger(__name__)

class ExpressionPlanner:
    """
    表达规划器，负责规划表达策略，基于关系阶段调整表达方式
    """
    
    def __init__(
        self, 
        memory: Optional[Memory] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化表达规划器
        
        Args:
            memory: 记忆系统，用于获取用户偏好和关系历史
            config: 配置参数，包含表达模板、关系阶段定义等
        """
        self.memory = memory
        self.config = config or {}
        
        # 关系阶段定义
        self.relationship_stages = self.config.get("relationship_stages", {
            "stranger": {
                "description": "初次接触，彼此不熟悉",
                "interaction_count": (0, 5),
                "formality_level": "high",
                "personal_info_sharing": "minimal",
                "expression_frequency": "low"
            },
            "acquaintance": {
                "description": "初步了解，有基本互动",
                "interaction_count": (6, 20),
                "formality_level": "medium-high",
                "personal_info_sharing": "basic",
                "expression_frequency": "medium-low"
            },
            "familiar": {
                "description": "相对熟悉，有一定了解",
                "interaction_count": (21, 50),
                "formality_level": "medium",
                "personal_info_sharing": "moderate",
                "expression_frequency": "medium"
            },
            "friend": {
                "description": "建立友谊，互相了解较多",
                "interaction_count": (51, 100),
                "formality_level": "medium-low",
                "personal_info_sharing": "substantial",
                "expression_frequency": "medium-high"
            },
            "close_friend": {
                "description": "亲密朋友，深入了解",
                "interaction_count": (101, float('inf')),
                "formality_level": "low",
                "personal_info_sharing": "extensive",
                "expression_frequency": "high"
            }
        })
        
        # 表达模板
        self.expression_templates = self.config.get("expression_templates", {
            "greeting": {
                "stranger": [
                    "您好，有什么可以帮助您的吗？",
                    "欢迎，请问需要什么帮助？"
                ],
                "acquaintance": [
                    "您好，今天有什么需要帮助的吗？",
                    "很高兴再次见到您，有什么我可以做的？"
                ],
                "familiar": [
                    "你好，今天过得怎么样？",
                    "嗨，有什么新鲜事吗？"
                ],
                "friend": [
                    "嘿，最近怎么样？",
                    "好久不见，近况如何？"
                ],
                "close_friend": [
                    "嘿，想你了！",
                    "又见面啦，有什么好消息要分享吗？"
                ]
            },
            "question": {
                "stranger": [
                    "请问您对哪些话题感兴趣？",
                    "您平时有什么爱好吗？"
                ],
                "acquaintance": [
                    "我记得您之前提到过{topic}，能多聊聊吗？",
                    "您对{topic}有什么看法？"
                ],
                "familiar": [
                    "你对{topic}怎么看？我很好奇你的想法。",
                    "最近有没有了解过{topic}？"
                ],
                "friend": [
                    "话说回来，你最近有没有想过{topic}这个问题？",
                    "老实说，你觉得{topic}怎么样？"
                ],
                "close_friend": [
                    "我一直在想，你对{topic}到底是什么感觉？",
                    "说真的，{topic}这事你怎么看？"
                ]
            },
            # 其他类型的模板...
        })
        
        # 表达风格调整参数
        self.style_adjustments = self.config.get("style_adjustments", {
            "formality": {
                "high": {
                    "honorifics": True,
                    "contractions": False,
                    "slang": False,
                    "emoji": False
                },
                "medium-high": {
                    "honorifics": True,
                    "contractions": False,
                    "slang": False,
                    "emoji": True
                },
                "medium": {
                    "honorifics": False,
                    "contractions": True,
                    "slang": False,
                    "emoji": True
                },
                "medium-low": {
                    "honorifics": False,
                    "contractions": True,
                    "slang": True,
                    "emoji": True
                },
                "low": {
                    "honorifics": False,
                    "contractions": True,
                    "slang": True,
                    "emoji": True
                }
            }
        })
        
        logger.info("表达规划器初始化完成")
    
    async def plan_expression(self, expression_info: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        规划表达策略
        
        Args:
            expression_info: 表达信息，包含类型、内容等
            user_id: 用户ID，用于获取用户相关信息
            
        Returns:
            规划后的表达信息
        """
        # 获取用户信息和关系阶段
        user_info = await self._get_user_info(user_id)
        relationship_stage = self._determine_relationship_stage(user_info)
        
        # 调整表达内容
        adjusted_content = self._adjust_expression_content(
            expression_info["content"],
            expression_info["content"]["type"],
            relationship_stage,
            user_info
        )
        
        # 调整表达风格
        styled_content = self._adjust_expression_style(
            adjusted_content,
            relationship_stage,
            user_info
        )
        
        # 更新表达信息
        planned_expression = expression_info.copy()
        planned_expression["content"]["content"] = styled_content
        planned_expression["relationship_stage"] = relationship_stage
        planned_expression["user_info"] = {
            "name": user_info.get("name", "用户"),
            "interaction_count": user_info.get("interaction_count", 0),
            "preferences": user_info.get("preferences", {})
        }
        
        logger.info(f"表达规划完成，关系阶段: {relationship_stage}")
        return planned_expression
    
    async def _get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息字典
        """
        # 如果没有记忆系统，返回默认信息
        if self.memory is None:
            return {
                "id": user_id,
                "name": "用户",
                "interaction_count": 0,
                "preferences": {},
                "topics_of_interest": []
            }
        
        try:
            # 从记忆中检索用户信息
            # 注意：这里假设记忆系统有一个特定的查询方法来获取用户信息
            # 实际实现可能需要根据记忆系统的API进行调整
            user_memories = await self.memory.retrieve(f"user_info:{user_id}", limit=1)
            
            if user_memories and len(user_memories) > 0:
                # 解析记忆中的用户信息
                user_info = user_memories[0]
                if isinstance(user_info, str):
                    # 如果是字符串，尝试解析JSON
                    import json
                    try:
                        user_info = json.loads(user_info)
                    except:
                        user_info = {"name": "用户"}
                
                return user_info
            else:
                # 没有找到用户信息，返回默认值
                return {
                    "id": user_id,
                    "name": "用户",
                    "interaction_count": 0,
                    "preferences": {},
                    "topics_of_interest": []
                }
                
        except Exception as e:
            logger.error(f"获取用户信息错误: {e}")
            # 出错时返回默认信息
            return {
                "id": user_id,
                "name": "用户",
                "interaction_count": 0,
                "preferences": {},
                "topics_of_interest": []
            }
    
    def _determine_relationship_stage(self, user_info: Dict[str, Any]) -> str:
        """
        确定与用户的关系阶段
        
        Args:
            user_info: 用户信息
            
        Returns:
            关系阶段名称
        """
        # 获取交互次数
        interaction_count = user_info.get("interaction_count", 0)
        
        # 根据交互次数确定关系阶段
        for stage, info in self.relationship_stages.items():
            min_count, max_count = info["interaction_count"]
            if min_count <= interaction_count <= max_count:
                return stage
        
        # 默认为陌生人阶段
        return "stranger"
    
    def _adjust_expression_content(
        self, 
        content: Dict[str, Any], 
        expression_type: str, 
        relationship_stage: str,
        user_info: Dict[str, Any]
    ) -> str:
        """
        调整表达内容
        
        Args:
            content: 原始表达内容
            expression_type: 表达类型
            relationship_stage: 关系阶段
            user_info: 用户信息
            
        Returns:
            调整后的表达内容
        """
        # 获取原始内容
        original_content = content.get("content", "")
        
        # 检查是否有对应的模板
        if expression_type in self.expression_templates and relationship_stage in self.expression_templates[expression_type]:
            templates = self.expression_templates[expression_type][relationship_stage]
            
            # 随机选择一个模板
            if templates and random.random() < 0.3:  # 30%的概率使用模板
                template = random.choice(templates)
                
                # 替换模板中的占位符
                topics = user_info.get("topics_of_interest", ["一般话题"])
                topic = random.choice(topics) if topics else "一般话题"
                
                return template.format(
                    name=user_info.get("name", "用户"),
                    topic=topic
                )
        
        # 如果没有合适的模板或不使用模板，返回原始内容
        return original_content
    
    def _adjust_expression_style(
        self, 
        content: str, 
        relationship_stage: str,
        user_info: Dict[str, Any]
    ) -> str:
        """
        调整表达风格
        
        Args:
            content: 表达内容
            relationship_stage: 关系阶段
            user_info: 用户信息
            
        Returns:
            调整风格后的表达内容
        """
        # 获取关系阶段对应的正式程度
        formality_level = self.relationship_stages[relationship_stage]["formality_level"]
        
        # 获取风格调整参数
        style = self.style_adjustments["formality"][formality_level]
        
        # 应用风格调整
        adjusted_content = content
        
        # 添加敬语
        if style["honorifics"] and "您" not in adjusted_content:
            adjusted_content = adjusted_content.replace("你", "您")
        
        # 添加表情符号
        if style["emoji"] and random.random() < 0.5:  # 50%的概率添加表情
            emojis = ["😊", "👍", "🙂", "✨", "🌟"]
            adjusted_content = f"{adjusted_content} {random.choice(emojis)}"
        
        # 用户偏好调整
        adjusted_content = self._apply_user_preferences(adjusted_content, user_info)
        
        return adjusted_content
    
    def _apply_user_preferences(self, content: str, user_info: Dict[str, Any]) -> str:
        """
        应用用户偏好调整
        
        Args:
            content: 表达内容
            user_info: 用户信息
            
        Returns:
            调整后的表达内容
        """
        # 获取用户偏好
        preferences = user_info.get("preferences", {})
        
        # 根据用户偏好调整内容
        adjusted_content = content
        
        # 示例：根据用户喜欢的表情符号调整
        if "preferred_emojis" in preferences and random.random() < 0.7:  # 70%的概率应用
            emojis = preferences["preferred_emojis"]
            if emojis and isinstance(emojis, list) and len(emojis) > 0:
                adjusted_content = f"{adjusted_content} {random.choice(emojis)}"
        
        # 示例：根据用户喜欢的称呼调整
        if "preferred_name" in preferences:
            preferred_name = preferences["preferred_name"]
            if preferred_name and isinstance(preferred_name, str):
                adjusted_content = adjusted_content.replace("用户", preferred_name)
        
        return adjusted_content
