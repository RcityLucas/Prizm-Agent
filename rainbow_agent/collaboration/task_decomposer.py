"""
任务分解器

提供更智能的任务分解功能，将复杂任务拆分为多个子任务
"""
from typing import List, Dict, Any, Optional, Tuple
import json

from ..agent import RainbowAgent
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TaskDecomposer:
    """
    任务分解器
    
    通过分析任务的复杂性和领域，将其分解为更小的子任务
    """
    
    def __init__(self, coordinator: RainbowAgent):
        """
        初始化任务分解器
        
        Args:
            coordinator: 协调者代理
        """
        self.coordinator = coordinator
        
    def decompose(self, task_description: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        分解任务
        
        Args:
            task_description: 任务描述
            context: 任务上下文
            
        Returns:
            子任务列表，每个子任务包含描述和所需技能
        """
        # 创建任务分解提示
        prompt = self._create_decomposition_prompt(task_description, context)
        
        # 调用协调者进行任务分解
        logger.info(f"使用协调者分解任务: {task_description[:50]}...")
        response = self.coordinator.run(prompt)
        
        # 解析响应
        subtasks = self._parse_decomposition_response(response)
        
        # 如果解析失败，返回默认分解
        if not subtasks:
            logger.warning("任务分解失败，使用默认分解")
            return self._default_decomposition(task_description)
            
        logger.info(f"任务已分解为 {len(subtasks)} 个子任务")
        return subtasks
    
    def _create_decomposition_prompt(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> str:
        """创建任务分解提示"""
        context_str = ""
        if context:
            context_str = "任务上下文信息:\n"
            for key, value in context.items():
                context_str += f"- {key}: {value}\n"
        
        return f"""作为一个任务协调专家，请将以下复杂任务分解为更小的子任务，以便专业代理处理。

任务描述:
{task_description}

{context_str}

请将这个任务分解为2-5个子任务。对于每个子任务，提供:
1. 子任务描述: 详细说明需要完成什么
2. 所需技能: 完成这个子任务所需的技能列表

返回格式:
```json
[
  {{
    "description": "子任务1描述",
    "skills": ["技能1", "技能2"]
  }},
  {{
    "description": "子任务2描述",
    "skills": ["技能3", "技能4"]
  }}
]
```

注意:
- 确保每个子任务都是自包含的，可以由一个专业代理独立完成
- 子任务应遵循逻辑顺序，前一个任务可能为后一个任务提供输入
- 技能应该具体且相关，如"数据分析"、"文本处理"、"代码生成"等
"""
    
    def _parse_decomposition_response(self, response: str) -> List[Dict[str, Any]]:
        """解析任务分解响应"""
        try:
            # 尝试提取JSON部分
            json_str = None
            
            # 查找并提取JSON块
            if "```json" in response:
                parts = response.split("```json")
                if len(parts) > 1:
                    json_part = parts[1].split("```")[0].strip()
                    json_str = json_part
            elif "```" in response:
                parts = response.split("```")
                if len(parts) > 1:
                    json_part = parts[1].strip()
                    json_str = json_part
            else:
                # 尝试查找可能的JSON数组
                import re
                json_match = re.search(r'\[\s*\{.*\}\s*\]', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
            
            # 如果找到JSON字符串，尝试解析
            if json_str:
                subtasks = json.loads(json_str)
                
                # 验证格式
                valid_subtasks = []
                for subtask in subtasks:
                    if isinstance(subtask, dict) and "description" in subtask and "skills" in subtask:
                        valid_subtasks.append(subtask)
                        
                if valid_subtasks:
                    return valid_subtasks
                    
            return self._extract_fallback_subtasks(response)
                    
        except Exception as e:
            logger.error(f"解析任务分解响应时出错: {e}")
            return []
    
    def _extract_fallback_subtasks(self, response: str) -> List[Dict[str, Any]]:
        """从文本中提取子任务（备选方法）"""
        subtasks = []
        
        try:
            # 寻找可能的子任务标记
            import re
            
            # 寻找数字编号的任务
            task_matches = re.findall(r'(\d+)[\.:\)]\s*(.*?)(?:\n|$)', response)
            
            for _, task_text in task_matches:
                description = task_text.strip()
                if description:
                    # 提取可能的技能
                    skills = ["通用"]  # 默认技能
                    skills_match = re.search(r'技能[：:]\s*(.*?)(?:\n|$)', response)
                    if skills_match:
                        skills_text = skills_match.group(1)
                        skills = [s.strip() for s in skills_text.split(',')]
                    
                    subtasks.append({
                        "description": description,
                        "skills": skills
                    })
            
            # 如果没有找到子任务，查找其他模式
            if not subtasks:
                # 寻找破折号或星号标记的任务
                task_matches = re.findall(r'[-\*]\s*(.*?)(?:\n|$)', response)
                
                for task_text in task_matches:
                    description = task_text.strip()
                    if description:
                        subtasks.append({
                            "description": description,
                            "skills": ["通用"]
                        })
            
            return subtasks
            
        except Exception as e:
            logger.error(f"提取备选子任务时出错: {e}")
            return []
    
    def _default_decomposition(self, task_description: str) -> List[Dict[str, Any]]:
        """创建默认的任务分解"""
        return [
            {
                "description": f"分析任务: 分析并理解以下任务的需求和上下文: '{task_description}'",
                "skills": ["分析", "理解", "规划"]
            },
            {
                "description": f"执行任务: 执行所需的操作来完成任务: '{task_description}'",
                "skills": ["执行", "问题解决", "创造"]
            },
            {
                "description": f"总结任务结果: 汇总所完成工作并提供结论: '{task_description}'",
                "skills": ["总结", "写作", "评估"]
            }
        ]
