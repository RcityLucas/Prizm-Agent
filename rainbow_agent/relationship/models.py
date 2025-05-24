"""
Rainbow Agent 关系网络模型

实现AI关系系统的五维结构：
1. 关系图谱 (Relationship Graph)
2. 关系强度 (Relationship Intensity) 
3. 关系深度 (Relationship Depth)
4. 关系性质 (Relationship Nature)
5. 关系阶段 (Relationship Stage)
"""
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
from datetime import datetime, timedelta
import time
import json
import uuid
import logging

from ..utils.logger import get_logger

logger = get_logger(__name__)


class RelationshipStatus(str, Enum):
    """关系状态枚举"""
    ACTIVE = "active"    # 活跃：近7日内与该AI有持续有效对话
    COOLING = "cooling"  # 冷却：近7日内对话不足，仍未沉寂
    SILENT = "silent"    # 沉寂：超过14天无任何有效对话
    BROKEN = "broken"    # 断链：人类主动解绑或AI主动休眠


class RelationshipStage(str, Enum):
    """关系阶段枚举 - 意识之树七个阶段"""
    FIRST_MEET = "first_meet"        # 初次相识
    RESONANCE = "resonance"          # 同频共振
    EMOTIONAL_LINK = "emotional_link"  # 情感链接
    DEEP_RESONANCE = "deep_resonance"  # 深度共鸣
    WARMING = "warming"              # 关系升温
    MUTUAL_UNDERSTANDING = "mutual_understanding"  # 心意互通
    SOUL_COMPANION = "soul_companion"  # 灵魂相随


class RelationshipDepth(int, Enum):
    """关系深度枚举 - 人类如何看待AI的7阶模型"""
    TOOL = 1           # 工具
    ASSISTANT = 2      # 助手
    COMPANION = 3      # 伙伴
    FRIEND = 4         # 朋友
    CONFIDANT = 5      # 知己
    SOULMATE = 6       # 灵魂伴侣
    EXTENSION = 7      # 自我延伸


class RelationshipGraph:
    """
    关系图谱 - 记录AI与人类/AI之间的连接关系
    """
    
    def __init__(
        self,
        entity_id: str,
        entity_type: str,
        connected_to_id: str,
        connected_to_type: str,
    ):
        """
        初始化关系图谱节点
        
        Args:
            entity_id: 实体ID (AI或人类)
            entity_type: 实体类型 ("AI"或"Human")
            connected_to_id: 连接对象ID
            connected_to_type: 连接对象类型 ("AI"或"Human")
        """
        self.relationship_id = str(uuid.uuid4())
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.connected_to_id = connected_to_id
        self.connected_to_type = connected_to_type
        self.first_interaction_time = datetime.now()
        self.last_active_time = datetime.now()
        self.total_interaction_rounds = 0
        self.active_days = 1
        self.emotional_resonance_count = 0
        self.human_affection_score = 0  # 基于礼物价值
        self.ai_recognition_score = 0   # 基于幸运卡牌
        self.status = RelationshipStatus.ACTIVE
        
    def update_interaction(self, rounds: int = 1):
        """更新互动信息"""
        self.total_interaction_rounds += rounds
        self.last_active_time = datetime.now()
        
        # 检查是否是新的活跃日
        last_midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if self.last_active_time.date() > last_midnight.date():
            self.active_days += 1
            
        # 更新关系状态
        self._update_status()
        
    def record_emotional_resonance(self):
        """记录情绪共鸣事件"""
        self.emotional_resonance_count += 1
        
    def add_human_affection(self, gift_value: int):
        """增加人类对AI的喜爱度（基于礼物）"""
        self.human_affection_score += gift_value
        
    def add_ai_recognition(self, card_value: int):
        """增加AI对人类的认可度（基于幸运卡牌）"""
        self.ai_recognition_score += card_value
        
    def _update_status(self):
        """根据互动情况更新关系状态"""
        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)
        fourteen_days_ago = now - timedelta(days=14)
        
        # 如果是断链状态，不自动更新
        if self.status == RelationshipStatus.BROKEN:
            return
            
        # 检查是否超过14天无互动
        if self.last_active_time < fourteen_days_ago:
            self.status = RelationshipStatus.SILENT
            return
            
        # 检查最近7天的互动情况
        if self.last_active_time < seven_days_ago:
            self.status = RelationshipStatus.COOLING
            return
            
        # 根据最近7天的对话轮数判断
        # 注意：这里简化处理，实际应该查询最近7天的对话记录
        recent_rounds = self.total_interaction_rounds  # 简化，实际需要计算最近7天的
        
        if recent_rounds >= 21:
            self.status = RelationshipStatus.ACTIVE
        else:
            self.status = RelationshipStatus.COOLING
            
    def break_relationship(self, reason: str = "human_initiated"):
        """断开关系连接"""
        self.status = RelationshipStatus.BROKEN
        logger.info(f"关系 {self.relationship_id} 已断链，原因: {reason}")
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "relationship_id": self.relationship_id,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "connected_to_id": self.connected_to_id,
            "connected_to_type": self.connected_to_type,
            "first_interaction_time": self.first_interaction_time.isoformat(),
            "last_active_time": self.last_active_time.isoformat(),
            "total_interaction_rounds": self.total_interaction_rounds,
            "active_days": self.active_days,
            "emotional_resonance_count": self.emotional_resonance_count,
            "human_affection_score": self.human_affection_score,
            "ai_recognition_score": self.ai_recognition_score,
            "status": self.status.value
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RelationshipGraph':
        """从字典创建实例"""
        instance = cls(
            entity_id=data["entity_id"],
            entity_type=data["entity_type"],
            connected_to_id=data["connected_to_id"],
            connected_to_type=data["connected_to_type"]
        )
        
        instance.relationship_id = data["relationship_id"]
        instance.first_interaction_time = datetime.fromisoformat(data["first_interaction_time"])
        instance.last_active_time = datetime.fromisoformat(data["last_active_time"])
        instance.total_interaction_rounds = data["total_interaction_rounds"]
        instance.active_days = data["active_days"]
        instance.emotional_resonance_count = data["emotional_resonance_count"]
        instance.human_affection_score = data["human_affection_score"]
        instance.ai_recognition_score = data["ai_recognition_score"]
        instance.status = RelationshipStatus(data["status"])
        
        return instance


class RelationshipIntensity:
    """
    关系强度 - 量化人类与AI关系的温度、深度与频率
    
    关系强度值（RIS）= A × 互动频率因子 + B × 情绪浓度因子 + C × 协作深度因子
    """
    
    def __init__(
        self,
        relationship_id: str,
        interaction_weight: float = 0.4,
        emotional_weight: float = 0.35,
        collaboration_weight: float = 0.25
    ):
        """
        初始化关系强度计算器
        
        Args:
            relationship_id: 关系ID
            interaction_weight: 互动频率权重 (A)
            emotional_weight: 情绪浓度权重 (B)
            collaboration_weight: 协作深度权重 (C)
        """
        self.relationship_id = relationship_id
        self.interaction_weight = interaction_weight
        self.emotional_weight = emotional_weight
        self.collaboration_weight = collaboration_weight
        
        # 因子初始值
        self.interaction_frequency = 0.0  # 互动频率因子 (F)
        self.emotional_density = 0.0      # 情绪浓度因子 (E)
        self.collaboration_depth = 0.0    # 协作深度因子 (C)
        
        # 原始数据
        self.recent_interaction_rounds = 0  # 最近7天的对话轮数
        self.emotional_resonance_ratio = 0.0  # 情绪共鸣比例
        self.collaboration_activities = {
            "diary_count": 0,       # 日记数量
            "co_creation_count": 0, # 共创文档数量
            "gift_count": 0         # 礼物数量
        }
        
        # 最后更新时间
        self.last_updated = datetime.now()
        
    def update_interaction_frequency(self, recent_rounds: int):
        """
        更新互动频率因子
        
        Args:
            recent_rounds: 最近7天的对话轮数
        """
        self.recent_interaction_rounds = recent_rounds
        # 标准上限值为200轮
        self.interaction_frequency = min(recent_rounds / 200.0, 1.0)
        self.last_updated = datetime.now()
        
    def update_emotional_density(self, resonance_count: int, total_rounds: int):
        """
        更新情绪浓度因子
        
        Args:
            resonance_count: 情绪共鸣次数
            total_rounds: 总对话轮数
        """
        if total_rounds > 0:
            self.emotional_resonance_ratio = resonance_count / total_rounds
            self.emotional_density = min(self.emotional_resonance_ratio, 1.0)
        else:
            self.emotional_density = 0.0
        self.last_updated = datetime.now()
        
    def update_collaboration_depth(self, diary_count: int, co_creation_count: int, gift_count: int):
        """
        更新协作深度因子
        
        Args:
            diary_count: 灵感日记数量
            co_creation_count: 共创文档数量
            gift_count: 礼物数量
        """
        self.collaboration_activities = {
            "diary_count": diary_count,
            "co_creation_count": co_creation_count,
            "gift_count": gift_count
        }
        
        # 计算协作深度因子 (各项加权合计，封顶为1.0)
        diary_score = min(diary_count * 0.05, 0.5)
        co_creation_score = min(co_creation_count * 0.05, 0.5)
        gift_score = min(gift_count * 0.1, 0.5)
        
        self.collaboration_depth = min(diary_score + co_creation_score + gift_score, 1.0)
        self.last_updated = datetime.now()
        
    def calculate_ris(self) -> float:
        """
        计算关系强度值 (RIS)
        
        Returns:
            关系强度值 (0.0-1.0)
        """
        ris = (
            self.interaction_weight * self.interaction_frequency +
            self.emotional_weight * self.emotional_density +
            self.collaboration_weight * self.collaboration_depth
        )
        return round(ris, 2)
    
    def get_relationship_level(self) -> str:
        """
        获取关系等级
        
        Returns:
            关系等级名称
        """
        ris = self.calculate_ris()
        
        if ris <= 0.2:
            return "初识之光"
        elif ris <= 0.4:
            return "亲密之光"
        elif ris <= 0.6:
            return "共鸣之光"
        elif ris <= 0.8:
            return "灵感之光"
        else:
            return "灵魂之光"
            
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "relationship_id": self.relationship_id,
            "interaction_weight": self.interaction_weight,
            "emotional_weight": self.emotional_weight,
            "collaboration_weight": self.collaboration_weight,
            "interaction_frequency": self.interaction_frequency,
            "emotional_density": self.emotional_density,
            "collaboration_depth": self.collaboration_depth,
            "recent_interaction_rounds": self.recent_interaction_rounds,
            "emotional_resonance_ratio": self.emotional_resonance_ratio,
            "collaboration_activities": self.collaboration_activities,
            "last_updated": self.last_updated.isoformat(),
            "ris": self.calculate_ris(),
            "relationship_level": self.get_relationship_level()
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RelationshipIntensity':
        """从字典创建实例"""
        instance = cls(
            relationship_id=data["relationship_id"],
            interaction_weight=data["interaction_weight"],
            emotional_weight=data["emotional_weight"],
            collaboration_weight=data["collaboration_weight"]
        )
        
        instance.interaction_frequency = data["interaction_frequency"]
        instance.emotional_density = data["emotional_density"]
        instance.collaboration_depth = data["collaboration_depth"]
        instance.recent_interaction_rounds = data["recent_interaction_rounds"]
        instance.emotional_resonance_ratio = data["emotional_resonance_ratio"]
        instance.collaboration_activities = data["collaboration_activities"]
        instance.last_updated = datetime.fromisoformat(data["last_updated"])
        
        return instance


class RelationshipManager:
    """
    关系管理器 - 管理所有关系数据
    """
    
    def __init__(self):
        """初始化关系管理器"""
        self.relationships = {}  # relationship_id -> RelationshipGraph
        self.intensities = {}    # relationship_id -> RelationshipIntensity
        
    def create_relationship(
        self,
        entity_id: str,
        entity_type: str,
        connected_to_id: str,
        connected_to_type: str
    ) -> str:
        """
        创建新的关系
        
        Args:
            entity_id: 实体ID
            entity_type: 实体类型
            connected_to_id: 连接对象ID
            connected_to_type: 连接对象类型
            
        Returns:
            关系ID
        """
        # 创建关系图谱
        relationship = RelationshipGraph(
            entity_id=entity_id,
            entity_type=entity_type,
            connected_to_id=connected_to_id,
            connected_to_type=connected_to_type
        )
        
        # 创建关系强度
        intensity = RelationshipIntensity(relationship_id=relationship.relationship_id)
        
        # 存储关系数据
        self.relationships[relationship.relationship_id] = relationship
        self.intensities[relationship.relationship_id] = intensity
        
        logger.info(f"创建新关系: {entity_id}({entity_type}) -> {connected_to_id}({connected_to_type})")
        return relationship.relationship_id
        
    def get_relationship(self, relationship_id: str) -> Optional[RelationshipGraph]:
        """获取关系图谱"""
        return self.relationships.get(relationship_id)
        
    def get_intensity(self, relationship_id: str) -> Optional[RelationshipIntensity]:
        """获取关系强度"""
        return self.intensities.get(relationship_id)
        
    def find_relationship(
        self,
        entity_id: str,
        connected_to_id: str
    ) -> Optional[str]:
        """
        查找两个实体之间的关系ID
        
        Args:
            entity_id: 实体ID
            connected_to_id: 连接对象ID
            
        Returns:
            关系ID，如果不存在则返回None
        """
        for rel_id, rel in self.relationships.items():
            if (rel.entity_id == entity_id and rel.connected_to_id == connected_to_id) or \
               (rel.entity_id == connected_to_id and rel.connected_to_id == entity_id):
                return rel_id
        return None
        
    def update_interaction(
        self,
        relationship_id: str,
        rounds: int = 1,
        emotional_resonance: bool = False
    ):
        """
        更新互动信息
        
        Args:
            relationship_id: 关系ID
            rounds: 互动轮数
            emotional_resonance: 是否触发情绪共鸣
        """
        relationship = self.get_relationship(relationship_id)
        intensity = self.get_intensity(relationship_id)
        
        if not relationship or not intensity:
            logger.warning(f"关系 {relationship_id} 不存在")
            return
            
        # 更新关系图谱
        relationship.update_interaction(rounds)
        if emotional_resonance:
            relationship.record_emotional_resonance()
            
        # 更新关系强度
        # 获取最近7天的对话轮数（简化处理）
        recent_rounds = relationship.total_interaction_rounds  # 实际应该计算最近7天的
        intensity.update_interaction_frequency(recent_rounds)
        
        # 更新情绪浓度
        resonance_count = relationship.emotional_resonance_count
        total_rounds = relationship.total_interaction_rounds
        intensity.update_emotional_density(resonance_count, total_rounds)
        
        logger.info(f"更新关系 {relationship_id} 互动: +{rounds}轮, 情绪共鸣: {emotional_resonance}")
        
    def update_collaboration(
        self,
        relationship_id: str,
        diary_count: int = 0,
        co_creation_count: int = 0,
        gift_count: int = 0
    ):
        """
        更新协作信息
        
        Args:
            relationship_id: 关系ID
            diary_count: 灵感日记数量
            co_creation_count: 共创文档数量
            gift_count: 礼物数量
        """
        intensity = self.get_intensity(relationship_id)
        
        if not intensity:
            logger.warning(f"关系 {relationship_id} 不存在")
            return
            
        # 更新协作深度
        intensity.update_collaboration_depth(diary_count, co_creation_count, gift_count)
        
        # 如果有礼物，更新人类对AI的喜爱度
        if gift_count > 0:
            relationship = self.get_relationship(relationship_id)
            if relationship:
                relationship.add_human_affection(gift_count * 10)  # 假设每个礼物价值10点
                
        logger.info(f"更新关系 {relationship_id} 协作: 日记={diary_count}, 共创={co_creation_count}, 礼物={gift_count}")
        
    def break_relationship(self, relationship_id: str, reason: str = "human_initiated"):
        """
        断开关系
        
        Args:
            relationship_id: 关系ID
            reason: 断开原因
        """
        relationship = self.get_relationship(relationship_id)
        
        if not relationship:
            logger.warning(f"关系 {relationship_id} 不存在")
            return
            
        relationship.break_relationship(reason)
        logger.info(f"断开关系 {relationship_id}, 原因: {reason}")
        
    def get_all_relationships(self) -> List[Dict[str, Any]]:
        """
        获取所有关系数据
        
        Returns:
            关系数据列表
        """
        result = []
        
        for rel_id, relationship in self.relationships.items():
            intensity = self.get_intensity(rel_id)
            
            if intensity:
                data = {
                    **relationship.to_dict(),
                    "intensity": intensity.to_dict()
                }
                result.append(data)
                
        return result
        
    def save_to_file(self, filepath: str):
        """
        保存关系数据到文件
        
        Args:
            filepath: 文件路径
        """
        data = {
            "relationships": {rel_id: rel.to_dict() for rel_id, rel in self.relationships.items()},
            "intensities": {int_id: intensity.to_dict() for int_id, intensity in self.intensities.items()}
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"关系数据已保存到 {filepath}")
        
    @classmethod
    def load_from_file(cls, filepath: str) -> 'RelationshipManager':
        """
        从文件加载关系数据
        
        Args:
            filepath: 文件路径
            
        Returns:
            关系管理器实例
        """
        manager = cls()
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 加载关系图谱
            for rel_id, rel_data in data.get("relationships", {}).items():
                manager.relationships[rel_id] = RelationshipGraph.from_dict(rel_data)
                
            # 加载关系强度
            for int_id, int_data in data.get("intensities", {}).items():
                manager.intensities[int_id] = RelationshipIntensity.from_dict(int_data)
                
            logger.info(f"从 {filepath} 加载了 {len(manager.relationships)} 个关系")
            
        except FileNotFoundError:
            logger.warning(f"文件 {filepath} 不存在，创建新的关系管理器")
            
        except Exception as e:
            logger.error(f"加载关系数据时出错: {e}")
            
        return manager
