"""
工具选择器 - 智能选择最合适的工具

提供基于LLM的智能工具选择功能，优化工具选择过程，
支持上下文感知和多工具比较，提高工具使用效率。
"""
from typing import Dict, Any, List, Tuple, Optional, Union
import json
import re
from enum import Enum

from ..tools.base import BaseTool
from ..utils.llm import get_llm_client
from ..utils.logger import get_logger

logger = get_logger(__name__)

class SelectionStrategy(Enum):
    """工具选择策略枚举"""
    RULE_BASED = "rule_based"         # 基于规则的选择
    LLM_BASED = "llm_based"           # 基于LLM的选择
    HYBRID = "hybrid"                 # 混合策略
    CONFIDENCE = "confidence"         # 置信度策略

class ToolSelector:
    """
    工具选择器，负责智能选择最合适的工具
    
    提供多种选择策略，支持上下文感知和多工具比较
    """
    
    def __init__(
        self,
        tools: List[BaseTool] = None,
        strategy: SelectionStrategy = SelectionStrategy.HYBRID,
        llm_client = None,
        model: str = "gpt-4",
        confidence_threshold: float = 0.7,
        verbose: bool = False
    ):
        """
        初始化工具选择器
        
        Args:
            tools: 可用工具列表
            strategy: 选择策略
            llm_client: LLM客户端
            model: 使用的模型
            confidence_threshold: 置信度阈值
            verbose: 是否输出详细日志
        """
        self.tools = tools or []
        self.strategy = strategy
        self.llm_client = llm_client or get_llm_client()
        self.model = model
        self.confidence_threshold = confidence_threshold
        self.verbose = verbose
        
        # 工具名称到工具对象的映射
        self.tool_map = {tool.name: tool for tool in self.tools}
        
        logger.info(f"ToolSelector初始化完成，策略: {strategy.value}")
    
    def add_tool(self, tool: BaseTool) -> None:
        """
        添加工具
        
        Args:
            tool: 要添加的工具
        """
        self.tools.append(tool)
        self.tool_map[tool.name] = tool
    
    def add_tools(self, tools: List[BaseTool]) -> None:
        """
        批量添加工具
        
        Args:
            tools: 要添加的工具列表
        """
        for tool in tools:
            self.add_tool(tool)
    
    def select_tool(self, query: str, context: Dict[str, Any] = None) -> Tuple[Optional[BaseTool], float, str]:
        """
        根据查询和上下文选择最合适的工具
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            (选择的工具, 置信度, 选择理由)的元组，如果没有合适的工具则工具为None
        """
        context = context or {}
        
        if not self.tools:
            logger.warning("没有可用的工具")
            return None, 0.0, "没有可用的工具"
        
        if self.strategy == SelectionStrategy.RULE_BASED:
            return self._rule_based_selection(query, context)
        elif self.strategy == SelectionStrategy.LLM_BASED:
            return self._llm_based_selection(query, context)
        elif self.strategy == SelectionStrategy.CONFIDENCE:
            return self._confidence_based_selection(query, context)
        else:  # HYBRID
            # 先尝试规则选择，如果置信度不够再使用LLM
            tool, confidence, reason = self._rule_based_selection(query, context)
            if confidence >= self.confidence_threshold:
                return tool, confidence, reason
            else:
                return self._llm_based_selection(query, context)
    
    def select_tools(self, query: str, context: Dict[str, Any] = None, top_k: int = 3) -> List[Tuple[BaseTool, float, str]]:
        """
        选择多个可能合适的工具
        
        Args:
            query: 用户查询
            context: 上下文信息
            top_k: 返回的工具数量
            
        Returns:
            (工具, 置信度, 选择理由)元组的列表，按置信度降序排序
        """
        context = context or {}
        
        if not self.tools:
            logger.warning("没有可用的工具")
            return []
        
        if self.strategy == SelectionStrategy.LLM_BASED or self.strategy == SelectionStrategy.HYBRID:
            return self._llm_based_multi_selection(query, context, top_k)
        else:
            # 对于其他策略，对每个工具单独评估并排序
            results = []
            for tool in self.tools:
                confidence = self._calculate_tool_match_confidence(tool, query, context)
                reason = f"工具 {tool.name} 与查询的匹配度: {confidence:.2f}"
                results.append((tool, confidence, reason))
            
            # 按置信度降序排序并返回top_k个
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
    
    def _rule_based_selection(self, query: str, context: Dict[str, Any]) -> Tuple[Optional[BaseTool], float, str]:
        """
        基于规则的工具选择
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            (选择的工具, 置信度, 选择理由)的元组
        """
        best_tool = None
        best_confidence = 0.0
        best_reason = ""
        
        for tool in self.tools:
            confidence = self._calculate_tool_match_confidence(tool, query, context)
            reason = f"工具 {tool.name} 与查询的匹配度: {confidence:.2f}"
            
            if confidence > best_confidence:
                best_tool = tool
                best_confidence = confidence
                best_reason = reason
        
        if best_confidence < self.confidence_threshold:
            logger.info(f"最佳工具 {best_tool.name if best_tool else 'None'} 的置信度 {best_confidence:.2f} 低于阈值 {self.confidence_threshold}")
            return None, best_confidence, f"没有找到置信度高于阈值的工具，最佳匹配: {best_reason}"
        
        logger.info(f"规则选择的工具: {best_tool.name}, 置信度: {best_confidence:.2f}")
        return best_tool, best_confidence, best_reason
    
    def _llm_based_selection(self, query: str, context: Dict[str, Any]) -> Tuple[Optional[BaseTool], float, str]:
        """
        基于LLM的工具选择
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            (选择的工具, 置信度, 选择理由)的元组
        """
        # 构建工具描述
        tools_description = ""
        for i, tool in enumerate(self.tools):
            tools_description += f"{i+1}. {tool.name}: {tool.description}\n   用法: {tool.usage}\n\n"
        
        prompt = f"""
        你是一个AI助手，负责为用户查询选择最合适的工具。请分析用户查询，并从以下工具中选择最合适的一个:
        
        可用工具:
        {tools_description}
        
        用户查询: {query}
        
        请按以下格式回答:
        
        选择工具: [工具名称]
        置信度: [0-1之间的数字，表示你对这个选择的置信度]
        理由: [选择这个工具的详细理由]
        
        如果没有合适的工具，请回答:
        
        选择工具: none
        置信度: 0
        理由: [没有合适工具的理由]
        
        只输出以上格式，不要包含其他内容。
        """
        
        # 调用LLM
        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        
        # 解析结果
        tool_match = re.search(r'选择工具:\s*(.*?)(?=\n|$)', content)
        confidence_match = re.search(r'置信度:\s*([\d.]+)', content)
        reason_match = re.search(r'理由:\s*(.*?)(?=\n选择工具:|$)', content, re.DOTALL)
        
        tool_name = tool_match.group(1).strip() if tool_match else "none"
        confidence_str = confidence_match.group(1).strip() if confidence_match else "0"
        reason = reason_match.group(1).strip() if reason_match else "未提供理由"
        
        try:
            confidence = float(confidence_str)
            confidence = max(0.0, min(1.0, confidence))  # 确保在0-1之间
        except:
            confidence = 0.0
        
        # 如果选择了none或置信度低于阈值
        if tool_name.lower() == "none" or confidence < self.confidence_threshold:
            logger.info(f"LLM没有选择工具或置信度低于阈值: {confidence:.2f} < {self.confidence_threshold}")
            return None, confidence, reason
        
        # 查找对应的工具对象
        tool = self.tool_map.get(tool_name)
        if not tool:
            logger.warning(f"LLM选择的工具 '{tool_name}' 不存在")
            return None, 0.0, f"选择的工具 '{tool_name}' 不存在"
        
        logger.info(f"LLM选择的工具: {tool.name}, 置信度: {confidence:.2f}")
        return tool, confidence, reason
    
    def _confidence_based_selection(self, query: str, context: Dict[str, Any]) -> Tuple[Optional[BaseTool], float, str]:
        """
        基于置信度的工具选择，使用LLM为每个工具评估置信度
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            (选择的工具, 置信度, 选择理由)的元组
        """
        # 构建工具描述
        tools_description = ""
        for i, tool in enumerate(self.tools):
            tools_description += f"{i+1}. {tool.name}: {tool.description}\n   用法: {tool.usage}\n\n"
        
        prompt = f"""
        你是一个AI助手，负责评估各个工具对用户查询的适用性。请分析用户查询，并为每个工具评估一个置信度分数。
        
        可用工具:
        {tools_description}
        
        用户查询: {query}
        
        请为每个工具评估一个0到1之间的置信度分数，表示该工具对解决用户查询的适用性。
        请按以下JSON格式回答:
        
        {{
            "tool_scores": [
                {{"tool": "工具1名称", "confidence": 0.X, "reason": "评分理由"}},
                {{"tool": "工具2名称", "confidence": 0.Y, "reason": "评分理由"}},
                ...
            ]
        }}
        
        只输出JSON格式，不要包含其他内容。
        """
        
        # 调用LLM
        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        
        # 解析JSON结果
        try:
            # 提取JSON部分
            json_match = re.search(r'({.*})', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)
                tool_scores = data.get("tool_scores", [])
            else:
                logger.warning("无法从LLM响应中提取JSON")
                return None, 0.0, "无法解析工具评分"
                
            if not tool_scores:
                logger.warning("LLM没有返回工具评分")
                return None, 0.0, "没有获取到工具评分"
            
            # 找出置信度最高的工具
            best_score = max(tool_scores, key=lambda x: x.get("confidence", 0))
            tool_name = best_score.get("tool", "")
            confidence = best_score.get("confidence", 0.0)
            reason = best_score.get("reason", "未提供理由")
            
            # 如果置信度低于阈值
            if confidence < self.confidence_threshold:
                logger.info(f"最高置信度 {confidence:.2f} 低于阈值 {self.confidence_threshold}")
                return None, confidence, f"没有找到置信度高于阈值的工具，最佳匹配: {tool_name} ({confidence:.2f}): {reason}"
            
            # 查找对应的工具对象
            tool = self.tool_map.get(tool_name)
            if not tool:
                logger.warning(f"评分最高的工具 '{tool_name}' 不存在")
                return None, 0.0, f"评分最高的工具 '{tool_name}' 不存在"
            
            logger.info(f"置信度选择的工具: {tool.name}, 置信度: {confidence:.2f}")
            return tool, confidence, reason
            
        except Exception as e:
            logger.error(f"解析LLM响应时出错: {e}")
            return None, 0.0, f"解析工具评分时出错: {str(e)}"
    
    def _llm_based_multi_selection(self, query: str, context: Dict[str, Any], top_k: int) -> List[Tuple[BaseTool, float, str]]:
        """
        基于LLM的多工具选择
        
        Args:
            query: 用户查询
            context: 上下文信息
            top_k: 返回的工具数量
            
        Returns:
            (工具, 置信度, 选择理由)元组的列表
        """
        # 构建工具描述
        tools_description = ""
        for i, tool in enumerate(self.tools):
            tools_description += f"{i+1}. {tool.name}: {tool.description}\n   用法: {tool.usage}\n\n"
        
        prompt = f"""
        你是一个AI助手，负责为用户查询选择最合适的多个工具。请分析用户查询，并从以下工具中选择最多{top_k}个合适的工具:
        
        可用工具:
        {tools_description}
        
        用户查询: {query}
        
        请按以下JSON格式回答:
        
        {{
            "selected_tools": [
                {{"tool": "工具1名称", "confidence": 0.X, "reason": "选择理由"}},
                {{"tool": "工具2名称", "confidence": 0.Y, "reason": "选择理由"}},
                ...
            ]
        }}
        
        只选择真正相关的工具，不需要强制选择{top_k}个。对于每个工具，提供一个0到1之间的置信度分数。
        只输出JSON格式，不要包含其他内容。
        """
        
        # 调用LLM
        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        
        # 解析JSON结果
        try:
            # 提取JSON部分
            json_match = re.search(r'({.*})', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)
                selected_tools = data.get("selected_tools", [])
            else:
                logger.warning("无法从LLM响应中提取JSON")
                return []
                
            if not selected_tools:
                logger.warning("LLM没有选择任何工具")
                return []
            
            # 转换为工具对象列表
            result = []
            for item in selected_tools:
                tool_name = item.get("tool", "")
                confidence = item.get("confidence", 0.0)
                reason = item.get("reason", "未提供理由")
                
                tool = self.tool_map.get(tool_name)
                if tool and confidence >= self.confidence_threshold:
                    result.append((tool, confidence, reason))
            
            # 按置信度降序排序
            result.sort(key=lambda x: x[1], reverse=True)
            
            logger.info(f"LLM选择了 {len(result)} 个工具")
            return result[:top_k]
            
        except Exception as e:
            logger.error(f"解析LLM响应时出错: {e}")
            return []
    
    def _calculate_tool_match_confidence(self, tool: BaseTool, query: str, context: Dict[str, Any]) -> float:
        """
        计算工具与查询的匹配置信度
        
        Args:
            tool: 要评估的工具
            query: 用户查询
            context: 上下文信息
            
        Returns:
            匹配置信度，0-1之间的浮点数
        """
        # 简单的关键词匹配
        query_lower = query.lower()
        tool_name_lower = tool.name.lower()
        tool_desc_lower = tool.description.lower()
        
        # 基础分数
        score = 0.0
        
        # 工具名称完全匹配
        if tool_name_lower == query_lower:
            score += 0.8
        # 工具名称部分匹配
        elif tool_name_lower in query_lower:
            score += 0.4
        # 查询中包含工具名称的部分
        elif any(part in query_lower for part in tool_name_lower.split('_')):
            score += 0.2
        
        # 描述匹配
        if tool_desc_lower in query_lower:
            score += 0.3
        # 查询包含描述中的关键词
        else:
            # 提取描述中的关键词（简单实现，可以用更复杂的NLP方法）
            desc_words = set(tool_desc_lower.split())
            query_words = set(query_lower.split())
            common_words = desc_words.intersection(query_words)
            
            # 根据共同词的比例加分
            if desc_words:
                word_match_ratio = len(common_words) / len(desc_words)
                score += 0.3 * word_match_ratio
        
        # 上下文相关性（如果有）
        if context:
            # 如果上下文中指定了工具
            if context.get("suggested_tool") == tool.name:
                score += 0.3
            
            # 如果上下文中有相关领域
            domain = context.get("domain", "")
            if domain and domain.lower() in tool_desc_lower:
                score += 0.2
        
        # 确保分数在0-1之间
        return min(1.0, score)
