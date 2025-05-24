"""
优化的工具选择器 - 提高性能和准确性

提供更高效的工具选择功能，包括缓存、批处理和更好的错误处理，
优化工具选择过程，提高性能和准确性。
"""
from typing import Dict, Any, List, Tuple, Optional, Union, Callable
import json
import re
import time
import hashlib
from enum import Enum
from collections import OrderedDict

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
    CACHED = "cached"                 # 缓存策略
    ENSEMBLE = "ensemble"             # 集成策略

class LRUCache:
    """LRU缓存实现，限制缓存大小"""
    
    def __init__(self, capacity: int = 100):
        """
        初始化LRU缓存
        
        Args:
            capacity: 缓存容量
        """
        self.cache = OrderedDict()
        self.capacity = capacity
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回None
        """
        if key not in self.cache:
            return None
        
        # 将访问的项移到末尾（最近使用）
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key: str, value: Any) -> None:
        """
        添加缓存项
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        # 如果键已存在，更新值并移到末尾
        if key in self.cache:
            self.cache.move_to_end(key)
        
        self.cache[key] = value
        
        # 如果超出容量，删除最久未使用的项（队首）
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

class OptimizedToolSelector:
    """
    优化的工具选择器，提供更高效的工具选择功能
    
    包括缓存、批处理和更好的错误处理
    """
    
    def __init__(
        self,
        tools: List[BaseTool] = None,
        strategy: SelectionStrategy = SelectionStrategy.HYBRID,
        llm_client = None,
        model: str = "gpt-4",
        confidence_threshold: float = 0.7,
        cache_capacity: int = 100,
        cache_ttl: int = 3600,
        use_batching: bool = True,
        batch_size: int = 5,
        timeout: int = 10,
        verbose: bool = False
    ):
        """
        初始化优化的工具选择器
        
        Args:
            tools: 可用工具列表
            strategy: 选择策略
            llm_client: LLM客户端
            model: 使用的模型
            confidence_threshold: 置信度阈值
            cache_capacity: 缓存容量
            cache_ttl: 缓存有效期（秒）
            use_batching: 是否使用批处理
            batch_size: 批处理大小
            timeout: 超时时间（秒）
            verbose: 是否输出详细日志
        """
        self.tools = tools or []
        self.strategy = strategy
        self.llm_client = llm_client or get_llm_client()
        self.model = model
        self.confidence_threshold = confidence_threshold
        self.cache_ttl = cache_ttl
        self.use_batching = use_batching
        self.batch_size = batch_size
        self.timeout = timeout
        self.verbose = verbose
        
        # 工具名称到工具对象的映射
        self.tool_map = {tool.name: tool for tool in self.tools}
        
        # 缓存
        self.selection_cache = LRUCache(cache_capacity)
        self.timestamp_cache = {}  # 缓存时间戳
        
        # 关键词索引
        self._build_keyword_index()
        
        logger.info(f"OptimizedToolSelector初始化完成，策略: {strategy.value}")
    
    def _build_keyword_index(self) -> None:
        """构建工具关键词索引，加速基于规则的选择"""
        self.keyword_index = {}
        
        for tool in self.tools:
            # 从工具名称中提取关键词
            name_parts = tool.name.lower().split('_')
            for part in name_parts:
                if part not in self.keyword_index:
                    self.keyword_index[part] = []
                self.keyword_index[part].append(tool)
            
            # 从工具描述中提取关键词
            desc_words = set(tool.description.lower().split())
            for word in desc_words:
                if len(word) > 3:  # 只索引长度大于3的词，避免噪音
                    if word not in self.keyword_index:
                        self.keyword_index[word] = []
                    if tool not in self.keyword_index[word]:
                        self.keyword_index[word].append(tool)
    
    def add_tool(self, tool: BaseTool) -> None:
        """
        添加工具
        
        Args:
            tool: 要添加的工具
        """
        self.tools.append(tool)
        self.tool_map[tool.name] = tool
        
        # 更新关键词索引
        name_parts = tool.name.lower().split('_')
        for part in name_parts:
            if part not in self.keyword_index:
                self.keyword_index[part] = []
            self.keyword_index[part].append(tool)
        
        desc_words = set(tool.description.lower().split())
        for word in desc_words:
            if len(word) > 3:
                if word not in self.keyword_index:
                    self.keyword_index[word] = []
                if tool not in self.keyword_index[word]:
                    self.keyword_index[word].append(tool)
    
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
        
        # 检查缓存
        cache_key = self._generate_cache_key(query, context)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            tool_name, confidence, reason = cached_result
            tool = self.tool_map.get(tool_name)
            if tool:
                logger.info(f"从缓存中获取工具选择结果: {tool.name}")
                return tool, confidence, reason
        
        # 根据策略选择工具
        if self.strategy == SelectionStrategy.RULE_BASED:
            result = self._rule_based_selection(query, context)
        elif self.strategy == SelectionStrategy.LLM_BASED:
            result = self._llm_based_selection(query, context)
        elif self.strategy == SelectionStrategy.CONFIDENCE:
            result = self._confidence_based_selection(query, context)
        elif self.strategy == SelectionStrategy.CACHED:
            # 先尝试规则选择，如果置信度不够再使用LLM
            tool, confidence, reason = self._rule_based_selection(query, context)
            if confidence >= self.confidence_threshold:
                result = (tool, confidence, reason)
            else:
                result = self._llm_based_selection(query, context)
        elif self.strategy == SelectionStrategy.ENSEMBLE:
            result = self._ensemble_selection(query, context)
        else:  # HYBRID
            # 先尝试规则选择，如果置信度不够再使用LLM
            tool, confidence, reason = self._rule_based_selection(query, context)
            if confidence >= self.confidence_threshold:
                result = (tool, confidence, reason)
            else:
                result = self._llm_based_selection(query, context)
        
        # 添加到缓存
        tool, confidence, reason = result
        if tool:
            self._add_to_cache(cache_key, (tool.name, confidence, reason))
        
        return result
    
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
        
        # 检查缓存
        cache_key = self._generate_cache_key(query, context) + f"_top{top_k}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            results = []
            for tool_name, confidence, reason in cached_result:
                tool = self.tool_map.get(tool_name)
                if tool:
                    results.append((tool, confidence, reason))
            
            if results:
                logger.info(f"从缓存中获取多工具选择结果: {len(results)}个工具")
                return results
        
        # 根据策略选择工具
        if self.strategy == SelectionStrategy.LLM_BASED or self.strategy == SelectionStrategy.HYBRID:
            results = self._llm_based_multi_selection(query, context, top_k)
        elif self.strategy == SelectionStrategy.ENSEMBLE:
            results = self._ensemble_multi_selection(query, context, top_k)
        else:
            # 对于其他策略，对每个工具单独评估并排序
            results = []
            for tool in self.tools:
                confidence = self._calculate_tool_match_confidence(tool, query, context)
                reason = f"工具 {tool.name} 与查询的匹配度: {confidence:.2f}"
                results.append((tool, confidence, reason))
            
            # 按置信度降序排序并返回top_k个
            results.sort(key=lambda x: x[1], reverse=True)
            results = results[:top_k]
        
        # 添加到缓存
        if results:
            cache_data = [(tool.name, confidence, reason) for tool, confidence, reason in results]
            self._add_to_cache(cache_key, cache_data)
        
        return results
    
    def _generate_cache_key(self, query: str, context: Dict[str, Any] = None) -> str:
        """
        生成缓存键
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            缓存键
        """
        # 标准化查询（去除多余空格，转小写）
        normalized_query = re.sub(r'\s+', ' ', query.lower()).strip()
        
        # 从上下文中提取相关信息
        context_str = ""
        if context:
            # 只使用可能影响工具选择的上下文键
            relevant_keys = ["domain", "suggested_tool", "previous_tools"]
            relevant_context = {k: v for k, v in context.items() if k in relevant_keys}
            if relevant_context:
                context_str = json.dumps(relevant_context, sort_keys=True)
        
        # 生成哈希值
        key_str = f"{normalized_query}:{context_str}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """
        从缓存中获取结果
        
        Args:
            cache_key: 缓存键
            
        Returns:
            缓存的结果，如果没有缓存或缓存过期则返回None
        """
        # 从LRU缓存中获取
        cached_data = self.selection_cache.get(cache_key)
        if cached_data is None:
            return None
        
        # 检查是否过期
        timestamp = self.timestamp_cache.get(cache_key, 0)
        if time.time() - timestamp > self.cache_ttl:
            # 删除过期缓存
            self.timestamp_cache.pop(cache_key, None)
            return None
        
        return cached_data
    
    def _add_to_cache(self, cache_key: str, result: Any) -> None:
        """
        添加结果到缓存
        
        Args:
            cache_key: 缓存键
            result: 缓存结果
        """
        self.selection_cache.put(cache_key, result)
        self.timestamp_cache[cache_key] = time.time()
    
    def _rule_based_selection(self, query: str, context: Dict[str, Any]) -> Tuple[Optional[BaseTool], float, str]:
        """
        基于规则的工具选择
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            (选择的工具, 置信度, 选择理由)的元组
        """
        # 1. 使用关键词索引快速筛选可能的工具
        query_lower = query.lower()
        candidate_tools = set()
        
        # 从查询中提取词语
        words = query_lower.split()
        for word in words:
            if word in self.keyword_index:
                for tool in self.keyword_index[word]:
                    candidate_tools.add(tool)
        
        # 如果没有候选工具，使用所有工具
        if not candidate_tools:
            candidate_tools = self.tools
        
        # 2. 计算每个候选工具的匹配置信度
        best_tool = None
        best_confidence = 0.0
        best_reason = ""
        
        for tool in candidate_tools:
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
        # 优化的关键词匹配算法
        query_lower = query.lower()
        tool_name_lower = tool.name.lower()
        tool_desc_lower = tool.description.lower()
        
        # 基础分数
        score = 0.0
        
        # 1. 名称匹配（精确匹配权重更高）
        if tool_name_lower == query_lower:
            score += 0.9  # 完全匹配给予很高的分数
        elif tool_name_lower in query_lower:
            score += 0.5  # 部分匹配
        else:
            # 检查工具名称的各部分
            name_parts = tool_name_lower.split('_')
            for part in name_parts:
                if part in query_lower:
                    score += 0.3 / len(name_parts)  # 根据匹配部分数量平均加分
        
        # 2. 描述匹配（使用TF-IDF思想）
        desc_words = set(tool_desc_lower.split())
        query_words = set(query_lower.split())
        
        # 计算共同词的IDF加权分数
        common_words = desc_words.intersection(query_words)
        if desc_words:
            # 给予重要词更高的权重
            important_words = [word for word in common_words if len(word) > 3]  # 长度大于3的词可能更重要
            word_match_score = 0.4 * (len(important_words) / len(desc_words))
            score += word_match_score
        
        # 3. 上下文相关性
        if context:
            # 如果上下文中指定了工具
            if context.get("suggested_tool") == tool.name:
                score += 0.4
            
            # 如果上下文中有相关领域
            domain = context.get("domain", "")
            if domain and domain.lower() in tool_desc_lower:
                score += 0.2
            
            # 如果是最近使用过的工具
            previous_tools = context.get("previous_tools", [])
            if tool.name in previous_tools:
                score += 0.1
        
        # 4. 特殊模式匹配
        if "计算" in query_lower and "calculator" in tool_name_lower:
            score += 0.3
        elif "翻译" in query_lower and "translate" in tool_name_lower:
            score += 0.3
        elif "天气" in query_lower and "weather" in tool_name_lower:
            score += 0.3
        elif "搜索" in query_lower and "search" in tool_name_lower:
            score += 0.3
        
        # 确保分数在0-1之间
        return min(1.0, score)
    
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
        tools_description = self._format_tools_description()
        
        # 构建提示词
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
        
        try:
            # 设置超时
            start_time = time.time()
            
            # 调用LLM
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            # 检查是否超时
            if time.time() - start_time > self.timeout:
                logger.warning(f"LLM工具选择超时: {self.timeout}秒")
                return None, 0.0, f"LLM工具选择超时: {self.timeout}秒"
            
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
            
        except Exception as e:
            logger.error(f"LLM工具选择错误: {e}")
            return None, 0.0, f"LLM工具选择错误: {str(e)}"
    
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
        tools_description = self._format_tools_description()
        
        # 构建提示词
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
        
        try:
            # 设置超时
            start_time = time.time()
            
            # 调用LLM
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            # 检查是否超时
            if time.time() - start_time > self.timeout:
                logger.warning(f"LLM工具评分超时: {self.timeout}秒")
                return None, 0.0, f"LLM工具评分超时: {self.timeout}秒"
            
            content = response.choices[0].message.content
            
            # 解析JSON结果
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
        tools_description = self._format_tools_description()
        
        # 构建提示词
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
        
        try:
            # 设置超时
            start_time = time.time()
            
            # 调用LLM
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            # 检查是否超时
            if time.time() - start_time > self.timeout:
                logger.warning(f"LLM多工具选择超时: {self.timeout}秒")
                return []
            
            content = response.choices[0].message.content
            
            # 解析JSON结果
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
    
    def _ensemble_selection(self, query: str, context: Dict[str, Any]) -> Tuple[Optional[BaseTool], float, str]:
        """
        集成选择方法，结合规则和LLM的结果
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            (选择的工具, 置信度, 选择理由)的元组
        """
        # 1. 使用规则方法
        rule_tool, rule_confidence, rule_reason = self._rule_based_selection(query, context)
        
        # 2. 使用LLM方法
        llm_tool, llm_confidence, llm_reason = self._llm_based_selection(query, context)
        
        # 3. 使用置信度方法
        conf_tool, conf_confidence, conf_reason = self._confidence_based_selection(query, context)
        
        # 收集所有有效结果
        candidates = []
        if rule_tool:
            candidates.append((rule_tool, rule_confidence, f"规则方法: {rule_reason}"))
        if llm_tool:
            candidates.append((llm_tool, llm_confidence, f"LLM方法: {llm_reason}"))
        if conf_tool:
            candidates.append((conf_tool, conf_confidence, f"置信度方法: {conf_reason}"))
        
        if not candidates:
            return None, 0.0, "所有方法都未找到合适的工具"
        
        # 投票机制：如果多个方法选择了同一个工具，增加其权重
        tool_votes = {}
        for tool, confidence, reason in candidates:
            if tool.name not in tool_votes:
                tool_votes[tool.name] = {
                    "tool": tool,
                    "confidence": confidence,
                    "reason": reason,
                    "votes": 1
                }
            else:
                tool_votes[tool.name]["votes"] += 1
                tool_votes[tool.name]["confidence"] = max(tool_votes[tool.name]["confidence"], confidence)
        
        # 找出得票最多或置信度最高的工具
        best_tool_info = max(tool_votes.values(), key=lambda x: (x["votes"], x["confidence"]))
        
        # 如果有多个方法选择了同一个工具，增加置信度
        adjusted_confidence = min(1.0, best_tool_info["confidence"] * (1 + 0.1 * (best_tool_info["votes"] - 1)))
        
        logger.info(f"集成选择的工具: {best_tool_info['tool'].name}, 置信度: {adjusted_confidence:.2f}, 得票: {best_tool_info['votes']}")
        return best_tool_info["tool"], adjusted_confidence, best_tool_info["reason"]
    
    def _ensemble_multi_selection(self, query: str, context: Dict[str, Any], top_k: int) -> List[Tuple[BaseTool, float, str]]:
        """
        集成多工具选择方法
        
        Args:
            query: 用户查询
            context: 上下文信息
            top_k: 返回的工具数量
            
        Returns:
            (工具, 置信度, 选择理由)元组的列表
        """
        # 1. 使用规则方法评估所有工具
        rule_results = []
        for tool in self.tools:
            confidence = self._calculate_tool_match_confidence(tool, query, context)
            if confidence >= self.confidence_threshold / 2:  # 使用较低的阈值以获取更多候选
                reason = f"规则方法: 工具 {tool.name} 与查询的匹配度: {confidence:.2f}"
                rule_results.append((tool, confidence, reason))
        
        # 2. 使用LLM方法
        llm_results = self._llm_based_multi_selection(query, context, top_k)
        
        # 合并结果
        all_results = rule_results + llm_results
        
        # 如果没有结果，返回空列表
        if not all_results:
            return []
        
        # 对每个工具取最高置信度
        tool_scores = {}
        for tool, confidence, reason in all_results:
            if tool.name not in tool_scores or confidence > tool_scores[tool.name]["confidence"]:
                tool_scores[tool.name] = {
                    "tool": tool,
                    "confidence": confidence,
                    "reason": reason,
                    "votes": 1
                }
            else:
                tool_scores[tool.name]["votes"] += 1
        
        # 转换为列表并排序
        results = []
        for info in tool_scores.values():
            # 调整置信度：如果多个方法都选择了这个工具，增加置信度
            adjusted_confidence = min(1.0, info["confidence"] * (1 + 0.1 * (info["votes"] - 1)))
            results.append((info["tool"], adjusted_confidence, info["reason"]))
        
        # 按置信度降序排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
    
    def _format_tools_description(self) -> str:
        """
        格式化工具描述
        
        Returns:
            格式化后的工具描述字符串
        """
        descriptions = []
        for i, tool in enumerate(self.tools):
            descriptions.append(f"{i+1}. {tool.name}: {tool.description}\n   用法: {tool.usage}")
        return "\n\n".join(descriptions)
