"""
结果聚合器

整合多个代理的工作结果，生成最终输出
"""
from typing import List, Dict, Any, Optional
import json

from ..agent import RainbowAgent
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ResultAggregator:
    """
    结果聚合器
    
    汇总多个子任务的结果，生成一致的最终输出
    """
    
    def __init__(self, coordinator: RainbowAgent):
        """
        初始化结果聚合器
        
        Args:
            coordinator: 协调者代理
        """
        self.coordinator = coordinator
    
    def aggregate(self, 
                  main_task_description: str, 
                  subtask_results: List[Dict[str, Any]], 
                  max_output_size: Optional[int] = None) -> Dict[str, Any]:
        """
        汇总子任务结果
        
        Args:
            main_task_description: 主任务描述
            subtask_results: 子任务结果列表，每个元素包含任务描述和结果
            max_output_size: 最大输出大小（字符数）
            
        Returns:
            聚合后的结果
        """
        # 创建聚合提示
        prompt = self._create_aggregation_prompt(main_task_description, subtask_results)
        
        # 调用协调者进行结果聚合
        logger.info(f"使用协调者聚合来自 {len(subtask_results)} 个子任务的结果")
        response = self.coordinator.run(prompt)
        
        # 解析和格式化聚合结果
        aggregated_result = self._format_aggregation_result(response, subtask_results)
        
        # 如果设置了最大输出大小，进行截断
        if max_output_size and isinstance(aggregated_result.get("final_result"), str):
            final_result = aggregated_result["final_result"]
            if len(final_result) > max_output_size:
                truncated_result = final_result[:max_output_size - 100] + "\n\n[注意: 响应因过长已被截断]"
                aggregated_result["final_result"] = truncated_result
                
                # 添加截断说明
                if "team_contributions" not in aggregated_result:
                    aggregated_result["team_contributions"] = []
                aggregated_result["team_contributions"].append({
                    "agent_name": "系统监控",
                    "contribution": "检测到响应过大并进行了截断处理"
                })
        
        return aggregated_result
    
    def _create_aggregation_prompt(self, main_task_description: str, subtask_results: List[Dict[str, Any]]) -> str:
        """创建聚合提示"""
        # 格式化子任务结果
        subtasks_content = ""
        for i, result in enumerate(subtask_results, 1):
            description = result.get("task_description", "未提供描述")
            agent_name = result.get("agent_name", f"代理 {i}")
            task_result = result.get("result", "无结果")
            
            subtasks_content += f"\n## 子任务 {i}: {description}\n"
            subtasks_content += f"执行者: {agent_name}\n"
            subtasks_content += f"结果:\n{task_result}\n"
        
        return f"""作为一个任务协调者，你需要将多个子任务的结果整合为一个连贯、全面的最终结果。

主任务:
{main_task_description}

子任务结果:
{subtasks_content}

请根据以上信息，创建一个综合性的最终结果，确保:
1. 信息的连贯性和一致性
2. 没有重复内容
3. 所有关键点都被涵盖
4. 结果是完整且具有洞察力的

同时，请注意标明每个代理的贡献，以便了解各部分内容的来源。

请使用以下JSON格式提供你的最终聚合结果:

```json
{{
  "final_result": "这里是完整的最终结果文本",
  "team_contributions": [
    {{
      "agent_name": "代理名称",
      "contribution": "该代理的主要贡献"
    }},
    ...
  ],
  "summary": "对团队协作过程的简要总结"
}}
```
"""
    
    def _format_aggregation_result(self, coordinator_response: str, subtask_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """解析和格式化协调者的聚合结果"""
        try:
            # 尝试提取JSON部分
            json_str = None
            
            # 查找并提取JSON块
            if "```json" in coordinator_response:
                parts = coordinator_response.split("```json")
                if len(parts) > 1:
                    json_part = parts[1].split("```")[0].strip()
                    json_str = json_part
            elif "```" in coordinator_response:
                parts = coordinator_response.split("```")
                if len(parts) > 1:
                    json_part = parts[1].strip()
                    json_str = json_part
            
            # 如果找到JSON字符串，尝试解析
            if json_str:
                try:
                    result = json.loads(json_str)
                    
                    # 验证基本结构
                    if "final_result" in result:
                        return result
                except Exception as e:
                    logger.error(f"解析JSON聚合结果时出错: {e}")
            
            # 如果无法提取或解析JSON，使用文本响应作为结果
            contributions = []
            for result in subtask_results:
                agent_name = result.get("agent_name", "未知代理")
                contributions.append({
                    "agent_name": agent_name,
                    "contribution": f"参与了任务执行"
                })
                
            # 构建备选结果结构
            return {
                "final_result": coordinator_response,
                "team_contributions": contributions,
                "summary": f"团队完成了任务，包含{len(subtask_results)}个子任务。"
            }
            
        except Exception as e:
            logger.error(f"格式化聚合结果时出错: {e}")
            
            # 返回最基本的结果格式
            return {
                "final_result": coordinator_response,
                "error": str(e)
            }


class ConsensusBuilder:
    """
    共识构建器
    
    当多个代理对同一问题有不同观点时，寻求共识
    """
    
    def __init__(self, coordinator: RainbowAgent):
        """
        初始化共识构建器
        
        Args:
            coordinator: 协调者代理
        """
        self.coordinator = coordinator
    
    def build_consensus(self, 
                        question: str, 
                        agent_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        构建共识
        
        Args:
            question: 需要达成共识的问题
            agent_responses: 各代理的回应，每个元素包含代理名称和回应
            
        Returns:
            共识结果
        """
        # 创建共识构建提示
        prompt = self._create_consensus_prompt(question, agent_responses)
        
        # 调用协调者构建共识
        logger.info(f"构建共识，涉及 {len(agent_responses)} 个代理的观点")
        response = self.coordinator.run(prompt)
        
        # 解析和格式化共识结果
        consensus_result = self._parse_consensus_response(response, agent_responses)
        
        return consensus_result
    
    def _create_consensus_prompt(self, question: str, agent_responses: List[Dict[str, Any]]) -> str:
        """创建共识构建提示"""
        # 格式化各代理的回应
        responses_content = ""
        for i, response in enumerate(agent_responses, 1):
            agent_name = response.get("agent_name", f"代理 {i}")
            agent_response = response.get("response", "无回应")
            agent_confidence = response.get("confidence", "未指定")
            
            responses_content += f"\n## 代理 {i}: {agent_name}\n"
            responses_content += f"回应:\n{agent_response}\n"
            responses_content += f"置信度: {agent_confidence}\n"
        
        return f"""作为一个共识构建专家，你需要分析多个专业代理对同一问题的不同回应，并找出最准确的共识。

问题:
{question}

各代理回应:
{responses_content}

请分析这些回应，并构建一个合理的共识，考虑:
1. 各代理的专业领域和置信度
2. 回应中的共同点和差异
3. 证据的强度和相关性

请使用以下JSON格式提供你的共识结果:

```json
{{
  "consensus": "这里是最终共识",
  "reasoning": "达成此共识的推理过程",
  "confidence": "高/中/低，表示对共识的置信度",
  "dissenting_views": ["可能存在的重要不同意见"],
  "open_questions": ["仍然存在的未解决问题"]
}}
```
"""
    
    def _parse_consensus_response(self, coordinator_response: str, agent_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """解析共识结果"""
        try:
            # 尝试提取JSON部分
            json_str = None
            
            # 查找并提取JSON块
            if "```json" in coordinator_response:
                parts = coordinator_response.split("```json")
                if len(parts) > 1:
                    json_part = parts[1].split("```")[0].strip()
                    json_str = json_part
            elif "```" in coordinator_response:
                parts = coordinator_response.split("```")
                if len(parts) > 1:
                    json_part = parts[1].strip()
                    json_str = json_part
            
            # 如果找到JSON字符串，尝试解析
            if json_str:
                try:
                    result = json.loads(json_str)
                    
                    # 验证基本结构
                    if "consensus" in result:
                        return result
                except Exception as e:
                    logger.error(f"解析JSON共识结果时出错: {e}")
            
            # 如果无法提取或解析JSON，使用文本响应作为结果
            return {
                "consensus": coordinator_response,
                "reasoning": "直接使用协调者的回应作为共识",
                "confidence": "中",
                "agent_count": len(agent_responses)
            }
            
        except Exception as e:
            logger.error(f"解析共识结果时出错: {e}")
            
            # 返回最基本的结果格式
            return {
                "consensus": coordinator_response,
                "error": str(e)
            }
