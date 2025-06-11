# rainbow_agent/frequency/prompt_log.py
"""
提示日志组件，负责记录和分析系统使用的各种提示模板和它们的效果
"""
from typing import Dict, Any, List, Optional
import time
import json
import os
import asyncio
from ..utils.logger import get_logger

logger = get_logger(__name__)

class PromptLog:
    """
    提示日志组件，负责记录和分析系统使用的各种提示模板和它们的效果，
    用于优化频率感知系统的表达生成
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化提示日志组件
        
        Args:
            config: 配置参数，包含日志存储路径、分析策略等
        """
        self.config = config or {}
        
        # 日志存储路径
        self.log_dir = self.config.get("log_dir", "logs/prompts")
        
        # 确保日志目录存在
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 提示模板记录
        self.prompt_templates = {}
        
        # 提示使用记录
        self.prompt_usage = []
        
        # 最大记录数
        self.max_usage_records = self.config.get("max_usage_records", 1000)
        
        # 自动保存间隔（秒）
        self.autosave_interval = self.config.get("autosave_interval", 3600)  # 默认1小时
        
        # 上次保存时间
        self.last_save_time = time.time()
        
        # 加载已有的提示模板和使用记录
        self._load_data()
        
        logger.info("提示日志组件初始化完成")
    
    def register_template(self, template_id: str, template_content: str, template_metadata: Dict[str, Any] = None) -> bool:
        """
        注册提示模板
        
        Args:
            template_id: 模板ID
            template_content: 模板内容
            template_metadata: 模板元数据
            
        Returns:
            是否成功注册
        """
        if template_id in self.prompt_templates:
            logger.warning(f"提示模板已存在: {template_id}")
            return False
        
        # 创建模板记录
        template_record = {
            "id": template_id,
            "content": template_content,
            "metadata": template_metadata or {},
            "created_at": time.time(),
            "usage_count": 0,
            "success_count": 0,
            "average_rating": 0.0,
            "ratings": []
        }
        
        # 注册模板
        self.prompt_templates[template_id] = template_record
        
        logger.info(f"注册提示模板: {template_id}")
        
        # 检查是否需要自动保存
        self._check_autosave()
        
        return True
    
    def update_template(self, template_id: str, template_content: str = None, template_metadata: Dict[str, Any] = None) -> bool:
        """
        更新提示模板
        
        Args:
            template_id: 模板ID
            template_content: 新的模板内容，如果为None则不更新
            template_metadata: 新的模板元数据，如果为None则不更新
            
        Returns:
            是否成功更新
        """
        if template_id not in self.prompt_templates:
            logger.warning(f"提示模板不存在: {template_id}")
            return False
        
        # 获取现有模板
        template = self.prompt_templates[template_id]
        
        # 更新内容
        if template_content is not None:
            template["content"] = template_content
        
        # 更新元数据
        if template_metadata is not None:
            template["metadata"].update(template_metadata)
        
        # 更新时间戳
        template["updated_at"] = time.time()
        
        logger.info(f"更新提示模板: {template_id}")
        
        # 检查是否需要自动保存
        self._check_autosave()
        
        return True
    
    def log_usage(
        self, 
        template_id: str, 
        generated_content: str, 
        context: Dict[str, Any],
        success: bool = True,
        rating: float = None,
        feedback: str = None
    ) -> bool:
        """
        记录提示模板使用情况
        
        Args:
            template_id: 模板ID
            generated_content: 生成的内容
            context: 使用上下文
            success: 是否成功生成
            rating: 评分（0-1）
            feedback: 反馈信息
            
        Returns:
            是否成功记录
        """
        if template_id not in self.prompt_templates:
            logger.warning(f"提示模板不存在: {template_id}")
            return False
        
        # 更新模板使用统计
        template = self.prompt_templates[template_id]
        template["usage_count"] += 1
        
        if success:
            template["success_count"] += 1
        
        if rating is not None:
            template["ratings"].append(rating)
            # 更新平均评分
            template["average_rating"] = sum(template["ratings"]) / len(template["ratings"])
        
        # 创建使用记录
        usage_record = {
            "template_id": template_id,
            "timestamp": time.time(),
            "generated_content": generated_content,
            "context_summary": self._summarize_context(context),
            "success": success,
            "rating": rating,
            "feedback": feedback
        }
        
        # 添加使用记录
        self.prompt_usage.append(usage_record)
        
        # 限制记录数量
        if len(self.prompt_usage) > self.max_usage_records:
            self.prompt_usage = self.prompt_usage[-self.max_usage_records:]
        
        logger.debug(f"记录提示模板使用: {template_id}")
        
        # 检查是否需要自动保存
        self._check_autosave()
        
        return True
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        获取提示模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            提示模板记录，如果不存在则返回None
        """
        return self.prompt_templates.get(template_id)
    
    def get_templates_by_type(self, template_type: str) -> List[Dict[str, Any]]:
        """
        按类型获取提示模板
        
        Args:
            template_type: 模板类型
            
        Returns:
            符合类型的模板列表
        """
        return [
            template for template in self.prompt_templates.values()
            if template.get("metadata", {}).get("type") == template_type
        ]
    
    def get_best_templates(self, template_type: str = None, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        获取最佳提示模板
        
        Args:
            template_type: 模板类型，如果为None则不限类型
            top_n: 返回的模板数量
            
        Returns:
            评分最高的模板列表
        """
        # 筛选符合类型的模板
        if template_type:
            templates = self.get_templates_by_type(template_type)
        else:
            templates = list(self.prompt_templates.values())
        
        # 按平均评分排序
        sorted_templates = sorted(
            templates,
            key=lambda t: t.get("average_rating", 0),
            reverse=True
        )
        
        return sorted_templates[:top_n]
    
    def analyze_template_performance(self, template_id: str = None) -> Dict[str, Any]:
        """
        分析提示模板性能
        
        Args:
            template_id: 模板ID，如果为None则分析所有模板
            
        Returns:
            性能分析结果
        """
        if template_id:
            # 分析单个模板
            if template_id not in self.prompt_templates:
                logger.warning(f"提示模板不存在: {template_id}")
                return {}
            
            template = self.prompt_templates[template_id]
            
            # 获取该模板的使用记录
            template_usage = [
                record for record in self.prompt_usage
                if record["template_id"] == template_id
            ]
            
            # 计算成功率
            success_rate = template["success_count"] / template["usage_count"] if template["usage_count"] > 0 else 0
            
            # 计算平均评分
            avg_rating = template["average_rating"]
            
            return {
                "template_id": template_id,
                "usage_count": template["usage_count"],
                "success_count": template["success_count"],
                "success_rate": success_rate,
                "average_rating": avg_rating,
                "recent_usage": template_usage[-5:] if template_usage else []
            }
        else:
            # 分析所有模板
            results = {}
            for tid, template in self.prompt_templates.items():
                # 计算成功率
                success_rate = template["success_count"] / template["usage_count"] if template["usage_count"] > 0 else 0
                
                results[tid] = {
                    "usage_count": template["usage_count"],
                    "success_rate": success_rate,
                    "average_rating": template["average_rating"],
                    "type": template.get("metadata", {}).get("type", "unknown")
                }
            
            return results
    
    def save_data(self) -> bool:
        """
        保存提示模板和使用记录
        
        Returns:
            是否成功保存
        """
        try:
            # 保存提示模板
            templates_path = os.path.join(self.log_dir, "prompt_templates.json")
            with open(templates_path, "w", encoding="utf-8") as f:
                json.dump(self.prompt_templates, f, ensure_ascii=False, indent=2)
            
            # 保存使用记录
            usage_path = os.path.join(self.log_dir, "prompt_usage.json")
            with open(usage_path, "w", encoding="utf-8") as f:
                json.dump(self.prompt_usage, f, ensure_ascii=False, indent=2)
            
            # 更新保存时间
            self.last_save_time = time.time()
            
            logger.info("提示日志数据保存成功")
            return True
            
        except Exception as e:
            logger.error(f"保存提示日志数据错误: {e}")
            return False
    
    def _load_data(self) -> bool:
        """
        加载提示模板和使用记录
        
        Returns:
            是否成功加载
        """
        try:
            # 加载提示模板
            templates_path = os.path.join(self.log_dir, "prompt_templates.json")
            if os.path.exists(templates_path):
                with open(templates_path, "r", encoding="utf-8") as f:
                    self.prompt_templates = json.load(f)
            
            # 加载使用记录
            usage_path = os.path.join(self.log_dir, "prompt_usage.json")
            if os.path.exists(usage_path):
                with open(usage_path, "r", encoding="utf-8") as f:
                    self.prompt_usage = json.load(f)
                    
                    # 限制记录数量
                    if len(self.prompt_usage) > self.max_usage_records:
                        self.prompt_usage = self.prompt_usage[-self.max_usage_records:]
            
            logger.info(f"提示日志数据加载成功，{len(self.prompt_templates)}个模板，{len(self.prompt_usage)}条使用记录")
            return True
            
        except Exception as e:
            logger.error(f"加载提示日志数据错误: {e}")
            return False
    
    def _check_autosave(self):
        """
        检查是否需要自动保存
        """
        if time.time() - self.last_save_time >= self.autosave_interval:
            asyncio.create_task(self._async_save())
    
    async def _async_save(self):
        """
        异步保存数据
        """
        self.save_data()
    
    def _summarize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        总结上下文信息，避免存储过大的数据
        
        Args:
            context: 原始上下文
            
        Returns:
            总结后的上下文
        """
        # 创建上下文摘要
        summary = {}
        
        # 复制基本字段
        for key in ["expression_type", "relationship_stage", "priority_score"]:
            if key in context:
                summary[key] = context[key]
        
        # 如果有用户信息，提取关键字段
        if "user_info" in context:
            user_info = context["user_info"]
            summary["user_info"] = {
                "name": user_info.get("name", "用户"),
                "interaction_count": user_info.get("interaction_count", 0)
            }
        
        # 如果有时间信息，提取关键字段
        if "timestamp" in context:
            summary["timestamp"] = context["timestamp"]
        
        return summary
