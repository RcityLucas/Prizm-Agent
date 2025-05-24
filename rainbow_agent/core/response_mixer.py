# rainbow_agent/core/response_mixer.py
from typing import Dict, Any, List, Optional
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ResponseMixer:
    """
    响应混合器，负责组装最终响应
    """
    
    def __init__(self, plugins=None):
        """
        初始化响应混合器
        
        Args:
            plugins: 响应处理插件列表
        """
        self.plugins = plugins or []
    
    def add_plugin(self, plugin):
        """添加响应处理插件"""
        self.plugins.append(plugin)
    
    def mix(self, llm_response: str, tool_results: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        混合LLM响应和工具结果，生成最终响应
        
        Args:
            llm_response: LLM生成的原始响应
            tool_results: 工具调用结果列表
            
        Returns:
            最终响应文本
        """
        # 如果没有工具结果，直接使用LLM响应
        if not tool_results:
            final_response = llm_response
        else:
            # 默认实现：保留LLM响应，但确保工具结果被正确引用
            final_response = self._ensure_tool_results_referenced(llm_response, tool_results)
        
        # 应用所有响应处理插件
        for plugin in self.plugins:
            try:
                final_response = plugin.process_response(final_response, llm_response, tool_results)
            except Exception as e:
                logger.error(f"插件处理响应错误: {e}")
        
        logger.info(f"响应混合完成，最终长度: {len(final_response)}")
        return final_response
    
    def _ensure_tool_results_referenced(self, llm_response: str, tool_results: List[Dict[str, Any]]) -> str:
        """确保工具结果在最终响应中被正确引用"""
        # 检查是否所有工具都在响应中被引用
        all_referenced = True
        for tool_result in tool_results:
            tool_name = tool_result["tool_name"]
            if tool_name not in llm_response:
                all_referenced = False
                break
        
        # 如果有工具结果未被引用，添加附录
        if not all_referenced:
            appendix = "\n\n**附加信息**:\n"
            for tool_result in tool_results:
                tool_name = tool_result["tool_name"]
                result = tool_result["result"]
                # 只添加未被引用的工具结果
                if tool_name not in llm_response:
                    appendix += f"\n工具 '{tool_name}' 的结果:\n{result}\n"
            
            return llm_response + appendix
        
        return llm_response