"""
网络搜索工具模块

实现了使用网络搜索API获取实时信息的能力
"""
import os
import json
import requests
from typing import Dict, Any, List, Optional

from .base import BaseTool
from ..utils.logger import get_logger

logger = get_logger(__name__)


class WebSearchTool(BaseTool):
    """
    网络搜索工具，使用搜索API获取实时信息
    
    支持通过Serpapi或Bing搜索API获取网络信息
    """
    
    def __init__(
        self, 
        api_type: str = "serpapi",
        api_key: Optional[str] = None,
        max_results: int = 5
    ):
        """
        初始化网络搜索工具
        
        Args:
            api_type: API类型，'serpapi'或'bing'
            api_key: API密钥，如不提供则尝试从环境变量获取
            max_results: 返回结果数量上限
        """
        super().__init__(
            name="web_search",
            description="搜索互联网获取最新信息。使用格式: '查询内容'"
        )
        self.api_type = api_type.lower()
        self.max_results = max_results
        
        # 设置API密钥
        if api_key:
            self.api_key = api_key
        else:
            if self.api_type == "serpapi":
                self.api_key = os.environ.get("SERPAPI_API_KEY")
            elif self.api_type == "bing":
                self.api_key = os.environ.get("BING_SEARCH_API_KEY")
            else:
                raise ValueError(f"不支持的API类型: {api_type}")
                
        if not self.api_key:
            logger.warning(f"未设置{self.api_type.upper()}_API_KEY，搜索功能可能不可用")
    
    def run(self, args: str) -> str:
        """
        执行网络搜索
        
        Args:
            args: 搜索查询
            
        Returns:
            搜索结果的摘要
        """
        query = args.strip()
        if not query:
            return "错误: 搜索查询不能为空"
            
        if not self.api_key:
            return "错误: 未配置API密钥，无法执行搜索"
            
        try:
            if self.api_type == "serpapi":
                return self._search_with_serpapi(query)
            elif self.api_type == "bing":
                return self._search_with_bing(query)
            else:
                return f"错误: 不支持的API类型 {self.api_type}"
        except Exception as e:
            logger.error(f"搜索执行错误: {e}")
            return f"搜索失败: {str(e)}"
    
    def _search_with_serpapi(self, query: str) -> str:
        """使用SerpAPI执行搜索"""
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": self.api_key,
            "engine": "google",
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return f"API错误 (状态码 {response.status_code}): {response.text}"
            
        data = response.json()
        
        # 提取搜索结果
        results = []
        
        # 添加有机结果
        if "organic_results" in data:
            for result in data["organic_results"][:self.max_results]:
                results.append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", "")
                })
        
        # 格式化结果
        if not results:
            return "没有找到相关结果"
            
        formatted_results = "搜索结果:\n\n"
        for i, result in enumerate(results, 1):
            formatted_results += f"{i}. {result['title']}\n"
            formatted_results += f"   链接: {result['link']}\n"
            formatted_results += f"   摘要: {result['snippet']}\n\n"
            
        return formatted_results
    
    def _search_with_bing(self, query: str) -> str:
        """使用Bing搜索API执行搜索"""
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        params = {"q": query, "count": self.max_results}
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return f"API错误 (状态码 {response.status_code}): {response.text}"
            
        data = response.json()
        
        # 提取搜索结果
        results = []
        if "webPages" in data and "value" in data["webPages"]:
            for result in data["webPages"]["value"]:
                results.append({
                    "title": result.get("name", ""),
                    "link": result.get("url", ""),
                    "snippet": result.get("snippet", "")
                })
        
        # 格式化结果
        if not results:
            return "没有找到相关结果"
            
        formatted_results = "搜索结果:\n\n"
        for i, result in enumerate(results, 1):
            formatted_results += f"{i}. {result['title']}\n"
            formatted_results += f"   链接: {result['link']}\n"
            formatted_results += f"   摘要: {result['snippet']}\n\n"
            
        return formatted_results
