"""
Rainbow Agent 关系网络工具函数

提供关系数据分析和可视化的辅助功能
"""
from typing import Dict, List, Any, Optional, Union, Tuple
import json
from datetime import datetime, timedelta
import math

from .models import RelationshipManager, RelationshipStatus, RelationshipIntensity


def calculate_relationship_stats(relationship_manager: RelationshipManager) -> Dict[str, Any]:
    """
    计算关系统计数据
    
    Args:
        relationship_manager: 关系管理器实例
        
    Returns:
        统计数据字典
    """
    relationships = relationship_manager.get_all_relationships()
    
    # 初始化统计数据
    stats = {
        "total_relationships": len(relationships),
        "status_counts": {status.value: 0 for status in RelationshipStatus},
        "avg_interaction_rounds": 0,
        "avg_relationship_intensity": 0.0,
        "avg_active_days": 0,
        "relationship_level_counts": {
            "stranger": 0,
            "acquaintance": 0,
            "friend": 0,
            "close_friend": 0,
            "intimate": 0
        }
    }
    
    if not relationships:
        return stats
    
    # 计算统计数据
    total_rounds = 0
    total_active_days = 0
    total_ris = 0.0
    
    for rel in relationships:
        # 状态统计
        status = rel.get("status", "")
        if status in stats["status_counts"]:
            stats["status_counts"][status] += 1
            
        # 互动轮次
        rounds = rel.get("total_interaction_rounds", 0)
        total_rounds += rounds
        
        # 活跃天数
        active_days = rel.get("active_days", 0)
        total_active_days += active_days
        
        # 关系强度
        rel_id = rel.get("relationship_id", "")
        intensity = relationship_manager.get_intensity(rel_id)
        if intensity:
            ris = intensity.calculate_ris()
            total_ris += ris
            
            # 关系等级
            level = intensity.get_relationship_level()
            if level in stats["relationship_level_counts"]:
                stats["relationship_level_counts"][level] += 1
    
    # 计算平均值
    stats["avg_interaction_rounds"] = total_rounds / len(relationships)
    stats["avg_active_days"] = total_active_days / len(relationships)
    stats["avg_relationship_intensity"] = total_ris / len(relationships)
    
    return stats


def get_relationship_trend(
    relationship_manager: RelationshipManager,
    relationship_id: str,
    days: int = 30
) -> Dict[str, Any]:
    """
    获取关系发展趋势
    
    Args:
        relationship_manager: 关系管理器实例
        relationship_id: 关系ID
        days: 查看的天数
        
    Returns:
        趋势数据字典
    """
    relationship = relationship_manager.get_relationship(relationship_id)
    if not relationship:
        return {"error": f"关系 {relationship_id} 不存在"}
    
    # 获取关系强度
    intensity = relationship_manager.get_intensity(relationship_id)
    if not intensity:
        return {"error": f"关系 {relationship_id} 未计算强度"}
    
    # 当前数据
    current_ris = intensity.calculate_ris()
    current_status = relationship.status
    
    # 简化的趋势分析（实际应基于历史数据）
    now = datetime.now()
    last_active = relationship.last_active_time
    days_since_last_active = (now - last_active).days
    
    # 根据活跃情况和强度推断趋势
    if days_since_last_active <= 3 and current_ris > 0.6:
        trend = "上升"
        slope = 0.05  # 每天上升0.05
    elif days_since_last_active <= 7 and current_ris > 0.4:
        trend = "稳定"
        slope = 0.01
    elif days_since_last_active <= 14:
        trend = "轻微下降"
        slope = -0.02
    elif days_since_last_active <= 30:
        trend = "下降"
        slope = -0.05
    else:
        trend = "急剧下降"
        slope = -0.1
    
    # 生成趋势数据点
    trend_data = []
    for i in range(days + 1):
        day = now - timedelta(days=days-i)
        
        # 简化模拟历史数据
        if i == days:  # 当前值
            point_ris = current_ris
        else:
            # 基于当前值和斜率的简单线性模型
            days_diff = days - i
            point_ris = max(0, min(1, current_ris - (slope * days_diff)))
            
            # 添加一些随机波动使曲线更自然
            variation = math.sin(i * 0.5) * 0.03
            point_ris = max(0, min(1, point_ris + variation))
        
        trend_data.append({
            "date": day.strftime("%Y-%m-%d"),
            "ris": round(point_ris, 3)
        })
    
    return {
        "relationship_id": relationship_id,
        "entity_id": relationship.entity_id,
        "connected_to_id": relationship.connected_to_id,
        "current_ris": current_ris,
        "current_status": current_status.value,
        "trend": trend,
        "days_since_last_active": days_since_last_active,
        "data": trend_data
    }


def find_similar_relationships(
    relationship_manager: RelationshipManager,
    relationship_id: str,
    threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """
    查找相似的关系
    
    Args:
        relationship_manager: 关系管理器实例
        relationship_id: 基准关系ID
        threshold: 相似度阈值
        
    Returns:
        相似关系列表
    """
    relationship = relationship_manager.get_relationship(relationship_id)
    if not relationship:
        return []
    
    base_intensity = relationship_manager.get_intensity(relationship_id)
    if not base_intensity:
        return []
    
    base_ris = base_intensity.calculate_ris()
    
    # 获取所有关系
    all_relationships = relationship_manager.get_all_relationships()
    
    # 查找相似关系
    similar_relationships = []
    
    for rel in all_relationships:
        rel_id = rel.get("relationship_id", "")
        
        # 跳过基准关系
        if rel_id == relationship_id:
            continue
        
        # 获取关系强度
        intensity = relationship_manager.get_intensity(rel_id)
        if not intensity:
            continue
        
        ris = intensity.calculate_ris()
        
        # 计算相似度（简化为RIS差值）
        similarity = 1 - abs(base_ris - ris)
        
        if similarity >= threshold:
            similar_relationships.append({
                "relationship_id": rel_id,
                "entity_id": rel.get("entity_id", ""),
                "connected_to_id": rel.get("connected_to_id", ""),
                "similarity": round(similarity, 3),
                "ris": ris,
                "status": rel.get("status", "")
            })
    
    # 按相似度排序
    similar_relationships.sort(key=lambda x: x["similarity"], reverse=True)
    
    return similar_relationships


def generate_relationship_report(
    relationship_manager: RelationshipManager,
    entity_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    生成关系报告
    
    Args:
        relationship_manager: 关系管理器实例
        entity_id: 实体ID，如果为None则生成所有关系的报告
        
    Returns:
        关系报告字典
    """
    # 获取关系数据
    if entity_id:
        relationships = []
        all_rels = relationship_manager.get_all_relationships()
        for rel in all_rels:
            if rel.get("entity_id") == entity_id or rel.get("connected_to_id") == entity_id:
                relationships.append(rel)
    else:
        relationships = relationship_manager.get_all_relationships()
    
    if not relationships:
        return {"error": "未找到关系数据"}
    
    # 计算统计数据
    stats = calculate_relationship_stats(relationship_manager)
    
    # 获取活跃关系
    active_relationships = [rel for rel in relationships 
                          if rel.get("status") == RelationshipStatus.ACTIVE.value]
    
    # 获取最高强度的关系
    highest_ris = 0.0
    strongest_relationship = None
    
    for rel in relationships:
        rel_id = rel.get("relationship_id", "")
        intensity = relationship_manager.get_intensity(rel_id)
        if intensity:
            ris = intensity.calculate_ris()
            if ris > highest_ris:
                highest_ris = ris
                strongest_relationship = rel
    
    # 生成报告
    report = {
        "generated_at": datetime.now().isoformat(),
        "entity_id": entity_id,
        "total_relationships": len(relationships),
        "active_relationships": len(active_relationships),
        "statistics": stats,
        "strongest_relationship": strongest_relationship,
        "highest_ris": highest_ris,
        "relationships_by_level": {
            "stranger": [],
            "acquaintance": [],
            "friend": [],
            "close_friend": [],
            "intimate": []
        }
    }
    
    # 按关系等级分类
    for rel in relationships:
        rel_id = rel.get("relationship_id", "")
        intensity = relationship_manager.get_intensity(rel_id)
        if intensity:
            level = intensity.get_relationship_level()
            if level in report["relationships_by_level"]:
                report["relationships_by_level"][level].append(rel)
    
    return report


def export_relationship_data(
    relationship_manager: RelationshipManager,
    format_type: str = "json"
) -> str:
    """
    导出关系数据
    
    Args:
        relationship_manager: 关系管理器实例
        format_type: 导出格式，目前支持json
        
    Returns:
        格式化的数据字符串
    """
    # 获取所有关系
    relationships = relationship_manager.get_all_relationships()
    
    # 为每个关系添加强度数据
    for rel in relationships:
        rel_id = rel.get("relationship_id", "")
        intensity = relationship_manager.get_intensity(rel_id)
        if intensity:
            rel["intensity"] = intensity.to_dict()
    
    # 导出数据
    if format_type == "json":
        return json.dumps({
            "exported_at": datetime.now().isoformat(),
            "total_relationships": len(relationships),
            "relationships": relationships
        }, ensure_ascii=False, indent=2)
    else:
        return f"不支持的导出格式: {format_type}"


def import_relationship_data(
    relationship_manager: RelationshipManager,
    data: str,
    format_type: str = "json"
) -> Tuple[bool, str]:
    """
    导入关系数据
    
    Args:
        relationship_manager: 关系管理器实例
        data: 数据字符串
        format_type: 导入格式，目前支持json
        
    Returns:
        (是否成功, 消息)
    """
    if format_type != "json":
        return False, f"不支持的导入格式: {format_type}"
    
    try:
        # 解析数据
        parsed_data = json.loads(data)
        relationships = parsed_data.get("relationships", [])
        
        # 导入关系
        imported_count = 0
        for rel_data in relationships:
            # 创建关系
            entity_id = rel_data.get("entity_id")
            entity_type = rel_data.get("entity_type")
            connected_to_id = rel_data.get("connected_to_id")
            connected_to_type = rel_data.get("connected_to_type")
            
            if not all([entity_id, entity_type, connected_to_id, connected_to_type]):
                continue
            
            # 检查关系是否已存在
            existing_rel_id = relationship_manager.find_relationship(entity_id, connected_to_id)
            if existing_rel_id:
                continue
            
            # 创建新关系
            relationship_manager.create_relationship(
                entity_id=entity_id,
                entity_type=entity_type,
                connected_to_id=connected_to_id,
                connected_to_type=connected_to_type
            )
            
            imported_count += 1
        
        return True, f"成功导入 {imported_count} 个关系"
        
    except json.JSONDecodeError:
        return False, "导入失败: 无效的JSON数据"
    except Exception as e:
        return False, f"导入失败: {str(e)}"
