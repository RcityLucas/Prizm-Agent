"""
高级工具集 - 提供数据分析、翻译和AI功能增强工具
"""
from typing import Dict, Any, List, Optional, Union
import json
import re
import time
import os
import requests
from datetime import datetime
import logging

from ..utils.logger import get_logger
from .base import BaseTool

logger = get_logger(__name__)

class TranslationTool(BaseTool):
    """翻译工具，支持多种语言之间的翻译"""
    
    def __init__(self):
        super().__init__(
            name="translate",
            description="将文本从一种语言翻译到另一种语言。格式: '文本|目标语言'，例如 'Hello world|中文'",
        )
        # 支持的语言代码
        self.languages = {
            "中文": "zh", "英文": "en", "日文": "ja", "韩文": "ko",
            "法文": "fr", "德文": "de", "西班牙文": "es", "俄文": "ru",
            "意大利文": "it", "葡萄牙文": "pt", "阿拉伯文": "ar"
        }
        
    def run(self, args: str) -> str:
        try:
            # 解析参数
            if "|" not in args:
                return "错误: 参数格式不正确，应为 '文本|目标语言'"
                
            text, target_lang = args.split("|", 1)
            text = text.strip()
            target_lang = target_lang.strip()
            
            # 检查目标语言
            if target_lang not in self.languages and target_lang not in self.languages.values():
                return f"错误: 不支持的目标语言 '{target_lang}'。支持的语言: {', '.join(self.languages.keys())}"
            
            # 获取语言代码
            lang_code = target_lang if target_lang in self.languages.values() else self.languages[target_lang]
            
            # 使用LLM进行翻译（实际应用中可以替换为专门的翻译API）
            from ..utils.llm import get_llm_client
            llm_client = get_llm_client()
            
            response = llm_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"你是一个专业翻译，请将以下文本翻译成{target_lang}，只返回翻译结果，不要添加任何解释。"},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
            )
            
            translation = response.choices[0].message.content.strip()
            return f"翻译结果 ({target_lang}):\n{translation}"
            
        except Exception as e:
            logger.error(f"翻译错误: {e}")
            return f"翻译过程中发生错误: {str(e)}"


class DataAnalysisTool(BaseTool):
    """数据分析工具，支持简单的数据分析任务"""
    
    def __init__(self):
        super().__init__(
            name="analyze_data",
            description="分析数据并提供统计信息。输入应为JSON格式的数据数组或CSV格式的数据。",
        )
        
    def run(self, args: str) -> str:
        try:
            # 尝试解析为JSON
            try:
                data = json.loads(args)
            except json.JSONDecodeError:
                # 尝试解析为CSV
                lines = args.strip().split("\n")
                if len(lines) < 2:
                    return "错误: 数据格式不正确，应为JSON数组或至少包含标题行的CSV"
                
                headers = [h.strip() for h in lines[0].split(",")]
                data = []
                for i in range(1, len(lines)):
                    values = [v.strip() for v in lines[i].split(",")]
                    if len(values) == len(headers):
                        row = {headers[j]: values[j] for j in range(len(headers))}
                        data.append(row)
            
            # 检查数据是否为列表
            if not isinstance(data, list):
                return "错误: 数据必须是列表/数组格式"
                
            if len(data) == 0:
                return "错误: 数据为空"
                
            # 基本统计分析
            result = "数据分析结果:\n"
            result += f"- 数据条目数: {len(data)}\n"
            
            # 如果是字典列表，分析每个字段
            if all(isinstance(item, dict) for item in data):
                # 获取所有字段
                all_fields = set()
                for item in data:
                    all_fields.update(item.keys())
                
                result += f"- 字段数: {len(all_fields)}\n"
                result += "- 字段列表: " + ", ".join(all_fields) + "\n\n"
                
                # 对数值型字段进行统计分析
                for field in all_fields:
                    # 收集字段值
                    values = [item.get(field) for item in data if field in item]
                    numeric_values = [v for v in values if isinstance(v, (int, float))]
                    
                    if numeric_values:
                        # 数值型字段统计
                        avg = sum(numeric_values) / len(numeric_values)
                        min_val = min(numeric_values)
                        max_val = max(numeric_values)
                        
                        result += f"字段 '{field}' 统计 (数值型):\n"
                        result += f"  - 平均值: {avg:.2f}\n"
                        result += f"  - 最小值: {min_val}\n"
                        result += f"  - 最大值: {max_val}\n"
                        result += f"  - 数据点数: {len(numeric_values)}\n\n"
                    else:
                        # 非数值型字段统计
                        unique_values = set(values)
                        result += f"字段 '{field}' 统计 (非数值型):\n"
                        result += f"  - 唯一值数量: {len(unique_values)}\n"
                        
                        # 如果唯一值不多，显示每个值的计数
                        if len(unique_values) <= 10:
                            value_counts = {val: values.count(val) for val in unique_values}
                            result += "  - 值分布:\n"
                            for val, count in value_counts.items():
                                result += f"    - {val}: {count} ({count/len(values)*100:.1f}%)\n"
                        result += "\n"
            
            return result
            
        except Exception as e:
            logger.error(f"数据分析错误: {e}")
            return f"数据分析过程中发生错误: {str(e)}"


class SummarizationTool(BaseTool):
    """文本摘要工具，用于总结长文本"""
    
    def __init__(self):
        super().__init__(
            name="summarize",
            description="生成长文本的摘要。输入应为需要总结的文本。",
        )
        
    def run(self, args: str) -> str:
        try:
            text = args.strip()
            
            if len(text) < 100:
                return "文本太短，不需要摘要。"
                
            # 使用LLM生成摘要
            from ..utils.llm import get_llm_client
            llm_client = get_llm_client()
            
            response = llm_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的文本摘要工具。请为以下文本生成一个简洁、全面的摘要，捕捉主要观点和关键信息。"},
                    {"role": "user", "content": text}
                ],
                temperature=0.5,
            )
            
            summary = response.choices[0].message.content.strip()
            return f"摘要:\n{summary}"
            
        except Exception as e:
            logger.error(f"摘要生成错误: {e}")
            return f"摘要生成过程中发生错误: {str(e)}"
