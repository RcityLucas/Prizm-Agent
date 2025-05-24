"""
Rainbow Agent 关系网络工具

提供用于管理和分析AI与人类关系的工具类
"""
from typing import Dict, List, Any, Optional, Union
import os
import json
from datetime import datetime

from ..tools.base import BaseTool
from .models import RelationshipManager, RelationshipStatus
from ..utils.logger import get_logger

logger = get_logger(__name__)


class RelationshipTool(BaseTool):
    """关系管理基础工具"""
    
    def __init__(self, relationship_manager: Optional[RelationshipManager] = None):
        """
        初始化关系工具
        
        Args:
            relationship_manager: 关系管理器实例，如果为None则创建新实例
        """
        super().__init__(
            name="relationship",
            description="管理和分析AI与人类之间的关系"
        )
        self.manager = relationship_manager or RelationshipManager()
        
    def run(self, args: str) -> str:
        """
        执行关系工具
        
        Args:
            args: 工具参数，格式为JSON字符串
            
        Returns:
            执行结果
        """
        try:
            # 解析参数
            params = json.loads(args)
            action = params.get("action", "")
            
            # 根据操作类型执行不同的功能
            if action == "create":
                return self._create_relationship(params)
            elif action == "update":
                return self._update_relationship(params)
            elif action == "query":
                return self._query_relationship(params)
            elif action == "break":
                return self._break_relationship(params)
            else:
                return f"不支持的操作: {action}"
                
        except json.JSONDecodeError:
            return "参数格式错误，请提供有效的JSON字符串"
        except Exception as e:
            logger.error(f"执行关系工具时出错: {e}")
            return f"执行关系工具时出错: {str(e)}"
            
    def _create_relationship(self, params: Dict[str, Any]) -> str:
        """创建关系"""
        entity_id = params.get("entity_id")
        entity_type = params.get("entity_type")
        connected_to_id = params.get("connected_to_id")
        connected_to_type = params.get("connected_to_type")
        
        if not all([entity_id, entity_type, connected_to_id, connected_to_type]):
            return "创建关系失败: 缺少必要参数"
            
        # 检查关系是否已存在
        existing_rel_id = self.manager.find_relationship(entity_id, connected_to_id)
        if existing_rel_id:
            return f"关系已存在，ID: {existing_rel_id}"
            
        # 创建新关系
        rel_id = self.manager.create_relationship(
            entity_id=entity_id,
            entity_type=entity_type,
            connected_to_id=connected_to_id,
            connected_to_type=connected_to_type
        )
        
        return f"成功创建关系，ID: {rel_id}"
        
    def _update_relationship(self, params: Dict[str, Any]) -> str:
        """更新关系"""
        relationship_id = params.get("relationship_id")
        update_type = params.get("update_type")
        
        if not relationship_id or not update_type:
            return "更新关系失败: 缺少必要参数"
            
        # 检查关系是否存在
        relationship = self.manager.get_relationship(relationship_id)
        if not relationship:
            return f"关系 {relationship_id} 不存在"
            
        # 根据更新类型执行不同的更新操作
        if update_type == "interaction":
            rounds = params.get("rounds", 1)
            emotional_resonance = params.get("emotional_resonance", False)
            self.manager.update_interaction(
                relationship_id=relationship_id,
                rounds=rounds,
                emotional_resonance=emotional_resonance
            )
            return f"成功更新关系互动: +{rounds}轮, 情绪共鸣: {emotional_resonance}"
            
        elif update_type == "collaboration":
            diary_count = params.get("diary_count", 0)
            co_creation_count = params.get("co_creation_count", 0)
            gift_count = params.get("gift_count", 0)
            self.manager.update_collaboration(
                relationship_id=relationship_id,
                diary_count=diary_count,
                co_creation_count=co_creation_count,
                gift_count=gift_count
            )
            return f"成功更新关系协作: 日记={diary_count}, 共创={co_creation_count}, 礼物={gift_count}"
            
        else:
            return f"不支持的更新类型: {update_type}"
            
    def _query_relationship(self, params: Dict[str, Any]) -> str:
        """查询关系"""
        query_type = params.get("query_type", "single")
        
        if query_type == "single":
            relationship_id = params.get("relationship_id")
            if not relationship_id:
                return "查询关系失败: 缺少关系ID"
                
            relationship = self.manager.get_relationship(relationship_id)
            intensity = self.manager.get_intensity(relationship_id)
            
            if not relationship:
                return f"关系 {relationship_id} 不存在"
                
            result = {
                "relationship": relationship.to_dict(),
                "intensity": intensity.to_dict() if intensity else None
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        elif query_type == "find":
            entity_id = params.get("entity_id")
            connected_to_id = params.get("connected_to_id")
            
            if not entity_id or not connected_to_id:
                return "查询关系失败: 缺少实体ID"
                
            rel_id = self.manager.find_relationship(entity_id, connected_to_id)
            
            if not rel_id:
                return f"未找到 {entity_id} 和 {connected_to_id} 之间的关系"
                
            return self._query_relationship({"query_type": "single", "relationship_id": rel_id})
            
        elif query_type == "all":
            relationships = self.manager.get_all_relationships()
            return json.dumps(relationships, ensure_ascii=False, indent=2)
            
        else:
            return f"不支持的查询类型: {query_type}"
            
    def _break_relationship(self, params: Dict[str, Any]) -> str:
        """断开关系"""
        relationship_id = params.get("relationship_id")
        reason = params.get("reason", "human_initiated")
        
        if not relationship_id:
            return "断开关系失败: 缺少关系ID"
            
        relationship = self.manager.get_relationship(relationship_id)
        
        if not relationship:
            return f"关系 {relationship_id} 不存在"
            
        self.manager.break_relationship(relationship_id, reason)
        return f"成功断开关系 {relationship_id}, 原因: {reason}"
        
    def save_data(self, filepath: str) -> str:
        """保存关系数据到文件"""
        try:
            self.manager.save_to_file(filepath)
            return f"关系数据已保存到 {filepath}"
        except Exception as e:
            logger.error(f"保存关系数据时出错: {e}")
            return f"保存关系数据时出错: {str(e)}"
            
    def load_data(self, filepath: str) -> str:
        """从文件加载关系数据"""
        try:
            self.manager = RelationshipManager.load_from_file(filepath)
            return f"已从 {filepath} 加载关系数据"
        except Exception as e:
            logger.error(f"加载关系数据时出错: {e}")
            return f"加载关系数据时出错: {str(e)}"


class RelationshipAnalysisTool(BaseTool):
    """关系分析工具"""
    
    def __init__(self, relationship_manager: Optional[RelationshipManager] = None):
        """
        初始化关系分析工具
        
        Args:
            relationship_manager: 关系管理器实例，如果为None则创建新实例
        """
        super().__init__(
            name="relationship_analysis",
            description="分析AI与人类之间的关系状态和发展趋势"
        )
        self.manager = relationship_manager or RelationshipManager()
        
    def run(self, args: str) -> str:
        """
        执行关系分析
        
        Args:
            args: 工具参数，格式为JSON字符串
            
        Returns:
            分析结果
        """
        try:
            # 解析参数
            params = json.loads(args)
            analysis_type = params.get("analysis_type", "")
            
            # 根据分析类型执行不同的功能
            if analysis_type == "status":
                return self._analyze_status(params)
            elif analysis_type == "intensity":
                return self._analyze_intensity(params)
            elif analysis_type == "trend":
                return self._analyze_trend(params)
            elif analysis_type == "summary":
                return self._generate_summary(params)
            else:
                return f"不支持的分析类型: {analysis_type}"
                
        except json.JSONDecodeError:
            return "参数格式错误，请提供有效的JSON字符串"
        except Exception as e:
            logger.error(f"执行关系分析时出错: {e}")
            return f"执行关系分析时出错: {str(e)}"
            
    def _analyze_status(self, params: Dict[str, Any]) -> str:
        """分析关系状态"""
        relationship_id = params.get("relationship_id")
        
        if not relationship_id:
            return "分析关系状态失败: 缺少关系ID"
            
        relationship = self.manager.get_relationship(relationship_id)
        
        if not relationship:
            return f"关系 {relationship_id} 不存在"
            
        # 分析关系状态
        status = relationship.status
        status_desc = {
            RelationshipStatus.ACTIVE: "活跃 - 近期有频繁互动的健康关系",
            RelationshipStatus.COOLING: "冷却 - 互动减少但仍有联系",
            RelationshipStatus.SILENT: "沉寂 - 长期无互动",
            RelationshipStatus.BROKEN: "断链 - 关系已终止"
        }.get(status, "未知状态")
        
        # 计算关系持续时间
        start_time = relationship.first_interaction_time
        duration_days = (datetime.now() - start_time).days
        
        result = {
            "relationship_id": relationship_id,
            "status": status.value,
            "status_description": status_desc,
            "duration_days": duration_days,
            "total_interaction_rounds": relationship.total_interaction_rounds,
            "active_days": relationship.active_days,
            "emotional_resonance_count": relationship.emotional_resonance_count,
            "last_active_time": relationship.last_active_time.isoformat()
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    def _analyze_intensity(self, params: Dict[str, Any]) -> str:
        """分析关系强度"""
        relationship_id = params.get("relationship_id")
        
        if not relationship_id:
            return "分析关系强度失败: 缺少关系ID"
            
        intensity = self.manager.get_intensity(relationship_id)
        
        if not intensity:
            return f"关系 {relationship_id} 不存在或未计算强度"
            
        # 计算关系强度值
        ris = intensity.calculate_ris()
        relationship_level = intensity.get_relationship_level()
        
        # 分析各因子贡献
        interaction_contribution = intensity.interaction_weight * intensity.interaction_frequency
        emotional_contribution = intensity.emotional_weight * intensity.emotional_density
        collaboration_contribution = intensity.collaboration_weight * intensity.collaboration_depth
        
        result = {
            "relationship_id": relationship_id,
            "relationship_intensity_score": ris,
            "relationship_level": relationship_level,
            "factor_details": {
                "interaction_frequency": {
                    "value": intensity.interaction_frequency,
                    "weight": intensity.interaction_weight,
                    "contribution": interaction_contribution,
                    "recent_rounds": intensity.recent_interaction_rounds
                },
                "emotional_density": {
                    "value": intensity.emotional_density,
                    "weight": intensity.emotional_weight,
                    "contribution": emotional_contribution,
                    "resonance_ratio": intensity.emotional_resonance_ratio
                },
                "collaboration_depth": {
                    "value": intensity.collaboration_depth,
                    "weight": intensity.collaboration_weight,
                    "contribution": collaboration_contribution,
                    "activities": intensity.collaboration_activities
                }
            },
            "last_updated": intensity.last_updated.isoformat()
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    def _analyze_trend(self, params: Dict[str, Any]) -> str:
        """分析关系发展趋势 (简化版，实际应该基于历史数据)"""
        relationship_id = params.get("relationship_id")
        
        if not relationship_id:
            return "分析关系趋势失败: 缺少关系ID"
            
        relationship = self.manager.get_relationship(relationship_id)
        intensity = self.manager.get_intensity(relationship_id)
        
        if not relationship or not intensity:
            return f"关系 {relationship_id} 不存在"
            
        # 简化版趋势分析，基于当前状态推断
        status = relationship.status
        ris = intensity.calculate_ris()
        
        # 根据状态和强度推断趋势
        if status == RelationshipStatus.ACTIVE and ris > 0.6:
            trend = "上升"
            suggestion = "关系发展良好，可以尝试更深层次的互动"
        elif status == RelationshipStatus.ACTIVE and ris <= 0.6:
            trend = "稳定"
            suggestion = "关系稳定发展，可以增加情感共鸣和协作深度"
        elif status == RelationshipStatus.COOLING:
            trend = "下降"
            suggestion = "关系有冷却趋势，建议增加互动频率"
        elif status == RelationshipStatus.SILENT:
            trend = "休眠"
            suggestion = "关系处于沉寂状态，需要主动唤醒"
        else:
            trend = "终止"
            suggestion = "关系已断链，可以考虑建立新的关系"
            
        result = {
            "relationship_id": relationship_id,
            "trend": trend,
            "suggestion": suggestion,
            "current_status": status.value,
            "current_ris": ris,
            "relationship_level": intensity.get_relationship_level()
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    def _generate_summary(self, params: Dict[str, Any]) -> str:
        """生成关系摘要"""
        entity_id = params.get("entity_id")
        
        if not entity_id:
            return "生成关系摘要失败: 缺少实体ID"
            
        # 获取所有关系
        all_relationships = self.manager.get_all_relationships()
        
        # 筛选与指定实体相关的关系
        entity_relationships = []
        for rel_data in all_relationships:
            if rel_data["entity_id"] == entity_id or rel_data["connected_to_id"] == entity_id:
                entity_relationships.append(rel_data)
                
        if not entity_relationships:
            return f"未找到与 {entity_id} 相关的关系"
            
        # 统计关系状态分布
        status_counts = {status.value: 0 for status in RelationshipStatus}
        for rel in entity_relationships:
            status_counts[rel["status"]] += 1
            
        # 计算平均关系强度
        total_ris = 0.0
        for rel in entity_relationships:
            if "intensity" in rel and "ris" in rel["intensity"]:
                total_ris += rel["intensity"]["ris"]
                
        avg_ris = total_ris / len(entity_relationships) if entity_relationships else 0
        
        result = {
            "entity_id": entity_id,
            "total_relationships": len(entity_relationships),
            "status_distribution": status_counts,
            "average_relationship_intensity": avg_ris,
            "active_relationships": status_counts[RelationshipStatus.ACTIVE.value],
            "relationships": entity_relationships
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
