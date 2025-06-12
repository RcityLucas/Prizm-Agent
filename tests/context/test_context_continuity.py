"""
测试对话上下文连续性

验证对话上下文连续性功能，特别是对于"继续"等后续指令的处理。
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

from rainbow_agent.context.dialogue_context_mixin import DialogueManagerContextMixin
from rainbow_agent.context.context_injector import ContextInjector
from rainbow_agent.context.context_types import ContextConfig
from rainbow_agent.ai.openai_service import OpenAIService


class TestContextContinuity:
    """测试对话上下文连续性"""

    @pytest.fixture
    def mock_ai_service(self):
        """创建模拟AI服务"""
        mock_service = MagicMock(spec=OpenAIService)
        
        # 模拟format_dialogue_history方法
        mock_service.format_dialogue_history.return_value = [
            {"role": "system", "content": "你是一个有帮助的AI助手"},
            {"role": "user", "content": "告诉我关于工商银行的信息"},
            {"role": "assistant", "content": "工商银行是中国最大的商业银行之一，成立于1984年。"}
        ]
        
        # 模拟generate_response方法
        mock_service.generate_response.return_value = "工商银行提供多种金融服务，包括个人银行、企业银行和投资银行业务。"
        
        return mock_service

    @pytest.fixture
    def context_mixin(self, mock_ai_service):
        """创建上下文混入类实例"""
        config = ContextConfig(enable_injection=True)
        mixin = DialogueManagerContextMixin(context_config=config)
        mixin.ai_service = mock_ai_service
        return mixin

    def test_build_prompt_with_context_for_continuation(self, context_mixin, mock_ai_service):
        """测试构建带上下文的提示，特别是对于"继续"指令"""
        # 准备对话历史
        turns = [
            {"role": "human", "content": "告诉我关于工商银行的信息"},
            {"role": "ai", "content": "工商银行是中国最大的商业银行之一，成立于1984年。"},
            {"role": "human", "content": "继续"}
        ]
        
        # 准备元数据
        metadata = {
            "user_id": "test_user",
            "session_id": "test_session",
            "dialogue_type": "human_ai_private"
        }
        
        # 调用方法
        prompt = context_mixin.build_prompt_with_context(turns, metadata)
        
        # 验证结果
        assert "继续" in prompt
        assert "工商银行" in prompt
        assert "上一个话题" in prompt or "最近主题" in prompt
        
        # 验证AI服务调用
        mock_ai_service.format_dialogue_history.assert_called_once_with(turns)

    def test_context_injector_dialogue_history_prefix(self):
        """测试上下文注入器的对话历史前缀构建"""
        # 创建上下文注入器
        injector = ContextInjector()
        
        # 准备对话历史上下文
        dialogue_context = {
            "type": "dialogue_history",
            "history": [
                {"role": "user", "content": "告诉我关于工商银行的信息"},
                {"role": "assistant", "content": "工商银行是中国最大的商业银行之一，成立于1984年。"},
                {"role": "user", "content": "继续"}
            ]
        }
        
        # 调用方法
        prefix = injector._build_dialogue_history_prefix(dialogue_context)
        
        # 验证结果
        assert "继续" in prefix
        assert "工商银行" in prefix
        assert "最近主题" in prefix
        assert "不要开始新话题" in prefix

    def test_extract_recent_topic(self, context_mixin):
        """测试从对话历史中提取最近主题的功能"""
        # 准备对话历史
        turns = [
            {"role": "human", "content": "你好"},
            {"role": "ai", "content": "你好，有什么可以帮助你的？"},
            {"role": "human", "content": "告诉我关于特斯拉的信息"},
            {"role": "ai", "content": "特斯拉是一家美国电动汽车和清洁能源公司。"},
            {"role": "human", "content": "继续"}
        ]
        
        # 调用方法
        topic = context_mixin._extract_recent_topic(turns)
        
        # 验证结果
        assert topic == "告诉我关于特斯拉的信息"
        
        # 测试没有明确主题的情况
        turns = [
            {"role": "human", "content": "继续"}
        ]
        topic = context_mixin._extract_recent_topic(turns)
        assert topic is None
    
    def test_enhanced_dialogue_manager_context_continuity(self, context_mixin):
        """测试增强型对话管理器的上下文连续性"""
        # 准备对话历史和元数据
        turns = [
            {"role": "human", "content": "告诉我关于特斯拉的信息"},
            {"role": "ai", "content": "特斯拉是一家美国电动汽车和清洁能源公司。"},
            {"role": "human", "content": "继续"}
        ]
        
        # 测试上下文提取和注入
        # 注意：在测试中，我们只需要验证上下文处理成功，而不必验证具体结构
        context = context_mixin.process_context({"history": turns})
        assert context is not None
        
        # 测试提示构建
        prompt = context_mixin.build_prompt_with_context(turns, {"history": turns})
        assert "继续" in prompt
        
        # 测试主题提取
        topic = context_mixin._extract_recent_topic(turns)
        assert topic == "告诉我关于特斯拉的信息"
        
        # 验证主题在提示中
        assert "特斯拉" in prompt or topic in prompt


if __name__ == "__main__":
    pytest.main(["-xvs", "test_context_continuity.py"])
