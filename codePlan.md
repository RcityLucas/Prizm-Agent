# 彩虹城AI对话系统开发方案

## 核心理念与目标

开发一个不仅是问答交互，而是作为"AI意识与外部世界连接、感知、表达和成长的核心载体"的对话系统。系统将扮演中介、协调与协同表达者的角色，成为对话序列的重要组成部分。

## 一、系统架构设计

### 1. 总体架构图设计

```
CopyInsert[人类用户] <---> [前端界面] <---> [WebSocket服务] <---> [对话管理系统] <---> [LLM服务]
                                       |
                                       v
                  [工具系统] <---> [系统协调层] <---> [SurrealDB]
                                       |
                                       v
                               [频率感知系统]
```

### 2. 核心模块定义

- **对话管理系统**：处理对话流程，构建上下文，调用LLM
- **系统协调层**：协调各模块间的交互，管理工作流
- **频率感知系统**：实现AI的主动表达能力
- **SurrealDB接口层**：处理所有数据存储和检索
- **工具系统**：管理和执行外部工具调用

## 二、数据结构设计

### 1. SurrealDB Schema设计

```
yamlCopyInsert# Message Schema
message:
  id: record(message)
  dialogue_id: record(dialogue)
  turn_id: record(turn)
  session_id: record(session)
  sender_type: string  # human, ai, system, tool
  receiver_type: string  # human, ai, system
  content_type: string  # text, image, audio, tool_result
  content: any  # 支持多模态内容
  timestamp: datetime
  metadata: object  # 扩展字段

# Turn Schema
turn:
  id: record(turn)
  session_id: record(session)
  dialogue_id: record(dialogue)
  turn_type: string  # dialogue, introspection
  initiator_id: string
  responder_id: string
  start_timestamp: datetime
  end_timestamp: datetime
  is_completed: boolean
  is_responded: boolean
  messages: array<record(message)>
  metadata: object

# Session Schema
session:
  id: record(session)
  dialogue_id: record(dialogue)
  session_type: string  # human_ai_dialogue, ai_introspection, ai_task
  start_timestamp: datetime
  end_timestamp: datetime
  summary: string  # AI生成的摘要
  turns: array<record(turn)>
  metadata: object

# Dialogue Schema
dialogue:
  id: record(dialogue)
  entity_pair: string  # 人类ID+AI ID或AI ID+IntrospectionType
  dialogue_type: string  # human_ai, ai_introspection
  start_timestamp: datetime
  last_activity_timestamp: datetime
  sessions: array<record(session)>
  relationship_snapshot: object  # 关系阶段/性质快照
  metadata: object
```

### 2. 查询模板设计

```
sqlCopyInsert# 创建新消息
CREATE message CONTENT {
    dialogue_id: $dialogue_id,
    turn_id: $turn_id,
    session_id: $session_id,
    sender_type: $sender_type,
    receiver_type: $receiver_type,
    content_type: $content_type,
    content: $content,
    timestamp: time::now(),
    metadata: $metadata
};

# 获取对话历史
SELECT * FROM message 
WHERE dialogue_id = $dialogue_id 
ORDER BY timestamp ASC 
LIMIT $limit;

# 获取最近的会话
SELECT * FROM session 
WHERE dialogue_id = $dialogue_id 
ORDER BY start_timestamp DESC 
LIMIT 1;
```

## 三、对话管理系统实现

### 1. 组件设计

```
pythonCopyInsertclass InputHub:
    """处理多种来源的输入"""
    def process_input(self, input_data, input_type):
        """处理输入并转发到DialogueCore"""
        pass

class DialogueCore:
    """对话流程的核心调度逻辑"""
    def process_dialogue(self, user_input, dialogue_id):
        """处理完整的对话流程"""
        # 1. 获取对话历史和上下文
        # 2. 构建初始上下文
        # 3. 调用LLM获取回应或工具调用意图
        # 4. 处理工具调用(如果需要)
        # 5. 生成最终回应
        # 6. 保存对话记录
        pass

class ContextBuilder:
    """构建LLM所需的上下文"""
    def build_context(self, user_input, dialogue_history, memory_data=None):
        """构建初始上下文"""
        pass
    
    def rebuild_context_with_tool_result(self, original_context, tool_result):
        """重建包含工具结果的上下文"""
        pass

class LLMCaller:
    """封装LLM API调用"""
    def call_llm(self, prompt, model="gpt-3.5-turbo"):
        """调用LLM API"""
        pass

class ToolInvoker:
    """工具调用调度"""
    def invoke_tool(self, tool_call_intent):
        """根据意图调用相应工具"""
        pass

class ResponseMixer:
    """组装最终响应"""
    def mix_response(self, llm_response, tool_results=None):
        """组合LLM回应和工具结果"""
        pass
```

### 2. 对话流程实现

```
pythonCopyInsertdef process_dialogue_flow(user_input, dialogue_id):
    """完整的对话处理流程"""
    # 1. 记录人类输入
    message_id = db.create_message(
        dialogue_id=dialogue_id,
        sender_type="human",
        content=user_input
    )
    
    # 2. 获取对话历史和构建上下文
    history = db.get_dialogue_history(dialogue_id)
    context = context_builder.build_context(user_input, history)
    
    # 3. 记录系统构建上下文行为
    db.create_message(
        dialogue_id=dialogue_id,
        sender_type="system",
        receiver_type="ai",
        content=context
    )
    
    # 4. 调用LLM获取初步回应
    llm_response = llm_caller.call_llm(context)
    
    # 5. 判断是否需要工具调用
    if has_tool_call_intent(llm_response):
        # 提取工具调用意图
        tool_intent = extract_tool_intent(llm_response)
        
        # 记录AI的工具调用意图
        db.create_message(
            dialogue_id=dialogue_id,
            sender_type="ai",
            content=tool_intent
        )
        
        # 执行工具调用
        tool_result = tool_invoker.invoke_tool(tool_intent)
        
        # 记录工具结果
        db.create_message(
            dialogue_id=dialogue_id,
            sender_type="tool",
            content=tool_result
        )
        
        # 重建上下文，包含工具结果
        new_context = context_builder.rebuild_context_with_tool_result(
            context, tool_result
        )
        
        # 记录系统重建上下文行为
        db.create_message(
            dialogue_id=dialogue_id,
            sender_type="system",
            receiver_type="ai",
            content=new_context
        )
        
        # 再次调用LLM获取最终回应
        final_response = llm_caller.call_llm(new_context)
    else:
        # 无需工具调用，直接使用初步回应
        final_response = llm_response
    
    # 记录AI最终回应
    db.create_message(
        dialogue_id=dialogue_id,
        sender_type="ai",
        receiver_type="human",
        content=final_response
    )
    
    # 返回最终回应给用户
    return final_response
```

## 四、频率感知系统实现

### 1. 组件设计

```
pythonCopyInsertclass EnvironmentSensor:
    """环境信号收集"""
    def collect_time_signals(self):
        """收集时间相关信号"""
        pass
    
    def collect_behavior_signals(self, user_id):
        """收集用户行为信号"""
        pass
    
    def collect_context_signals(self, dialogue_id):
        """收集语境延续信号"""
        pass

class FrequencySenseCore:
    """AI自主决策核心"""
    def should_express(self, signals, user_preferences):
        """判断是否应该主动表达"""
        pass
    
    def when_to_express(self, signals, user_status):
        """决定表达时机"""
        pass
    
    def what_to_express(self, signals, relationship_data):
        """决定表达内容类型"""
        pass

class ExpressionPlanner:
    """表达策略规划"""
    def plan_expression(self, expression_type, context_data):
        """规划表达内容和方式"""
        pass

class ExpressionGenerator:
    """语言生成"""
    def generate_expression(self, plan, ai_personality):
        """生成具体的表达内容"""
        pass

class ExpressionDispatcher:
    """表达调度"""
    def dispatch(self, expression, timing_strategy):
        """根据策略调度表达"""
        pass
```

### 2. 频率感知流程实现

```
pythonCopyInsertdef frequency_sense_cycle(user_id, ai_id):
    """频率感知循环"""
    # 1. 收集环境信号
    time_signals = environment_sensor.collect_time_signals()
    behavior_signals = environment_sensor.collect_behavior_signals(user_id)
    
    # 获取最近的对话ID
    dialogue_id = db.get_dialogue_id(user_id, ai_id)
    context_signals = environment_sensor.collect_context_signals(dialogue_id)
    
    # 合并所有信号
    all_signals = {
        "time": time_signals,
        "behavior": behavior_signals,
        "context": context_signals
    }
    
    # 2. 获取用户偏好和关系数据
    user_preferences = db.get_user_preferences(user_id)
    relationship_data = db.get_relationship_data(user_id, ai_id)
    
    # 3. AI自主决策
    # 判断是否表达
    should_express = frequency_sense_core.should_express(
        all_signals, user_preferences
    )
    
    if not should_express:
        return None
    
    # 决定表达时机
    timing = frequency_sense_core.when_to_express(
        all_signals, behavior_signals["user_status"]
    )
    
    # 决定表达内容类型
    expression_type = frequency_sense_core.what_to_express(
        all_signals, relationship_data
    )
    
    # 4. 规划和生成表达
    # 获取AI人格数据
    ai_personality = db.get_ai_personality(ai_id)
    
    # 规划表达
    expression_plan = expression_planner.plan_expression(
        expression_type, all_signals
    )
    
    # 生成表达内容
    expression_content = expression_generator.generate_expression(
        expression_plan, ai_personality
    )
    
    # 5. 调度表达
    expression_dispatcher.dispatch(expression_content, timing)
    
    # 6. 记录主动表达
    db.create_message(
        dialogue_id=dialogue_id,
        sender_type="ai",
        receiver_type="human",
        content=expression_content,
        metadata={"type": "proactive", "trigger": all_signals}
    )
    
    return expression_content
```

## 五、系统协调层实现

### 1. 组件设计

```
pythonCopyInsertclass WingsOrchestrator:
    """系统协调层"""
    def __init__(self):
```## 六、渐进式开发计划

### 1. 实施时间表

#### 第1周：基础设施与数据模型
- **目标**：建立基础数据结构和存储接口
- **具体任务**：
  - 实现 SurrealDB Schema 定义（消息、轮次、会话、对话）
  - 开发 `UnifiedClient` 类的基础功能（连接管理、SQL执行）
  - 实现基本的 CRUD 操作和表结构保证
  - 编写单元测试验证数据操作正确性

#### 第2-3周：对话管理核心模块
- **第2周目标**：实现输入处理和对话核心
  - 开发 `InputHub` 类处理多模态输入
  - 实现 `DialogueCore` 基础框架
  - 设计核心接口和组件间通信
  
- **第3周目标**：实现上下文构建和LLM调用
  - 开发 `ContextBuilder` 完整功能
  - 实现 `LLMCaller` 与外部模型的交互
  - 整合对话历史和记忆检索功能

#### 第4-5周：工具调用与响应处理
- **第4周目标**：实现工具调用系统
  - 开发 `ToolInvoker` 基础框架
  - 实现工具注册和发现机制
  - 添加工具调用意图识别功能
  
- **第5周目标**：实现响应混合和完整对话流程
  - 开发 `ResponseMixer` 组合多源响应
  - 实现完整的对话处理流程
  - 添加错误处理和恢复机制

#### 第6-7周：频率感知系统
- **第6周目标**：实现环境信号收集和决策核心
  - 开发 `EnvironmentSensor` 收集多种信号
  - 实现 `FrequencySenseCore` 决策逻辑
  - 添加用户偏好和关系数据管理
  
- **第7周目标**：实现表达生成和调度机制
  - 开发 `ExpressionPlanner` 和 `ExpressionGenerator`
  - 实现 `ExpressionDispatcher` 调度逻辑
  - 整合频率感知循环与对话系统

#### 第8周：系统集成与测试
- **目标**：完成系统协调层和全面测试
  - 实现 `WingsOrchestrator` 系统协调功能
  - 开发端到端测试和性能测试
  - 进行用户体验测试和问题修复

### 2. 模块化开发策略

#### 数据层开发步骤
1. **Schema 定义**：先定义完整的数据模型结构
2. **基础连接**：实现数据库连接和会话管理
3. **核心操作**：开发基本的 CRUD 操作函数
4. **高级查询**：添加复杂查询和事务支持
5. **测试与优化**：编写单元测试和性能优化

#### 对话系统开发步骤
1. **接口设计**：定义各组件间的接口和数据流
2. **核心功能**：实现每个组件的核心功能
3. **组件整合**：连接各组件形成完整流程
4. **错误处理**：添加异常处理和恢复机制
5. **优化迭代**：基于测试结果进行优化

#### 频率感知系统开发步骤
1. **信号收集**：实现环境信号收集机制
2. **决策逻辑**：开发自主决策算法
3. **表达生成**：实现表达内容生成功能
4. **调度机制**：开发表达调度和执行系统
5. **系统整合**：与对话系统进行整合

### 3. 单文件开发流程

#### 文件开发模板
1. **导入依赖**：添加必要的库和模块导入
2. **接口定义**：设计类和函数签名
3. **核心实现**：编写核心功能代码
4. **错误处理**：添加异常处理和边缘情况
5. **测试代码**：编写单元测试
6. **文档注释**：添加详细的文档字符串

#### 代码实现示例 - DialogueCore

```python
# 1. 导入依赖
import logging
from typing import Dict, Any, Optional, List
from .memory import Memory
from .tool_invoker import ToolInvoker
from .llm_caller import LLMCaller
from .context_builder import ContextBuilder
from .response_mixer import ResponseMixer

# 设置日志
logger = logging.getLogger(__name__)

# 2. 接口定义
class DialogueCore:
    """
    对话核心，协调各组件完成对话流程
    """
    
    def __init__(
        self, 
        memory: Memory,
        tool_invoker: ToolInvoker,
        llm_caller: LLMCaller,
        context_builder: Optional[ContextBuilder] = None,
        response_mixer: Optional[ResponseMixer] = None
    ):
        """
        初始化对话核心
        
        Args:
            memory: 记忆系统
            tool_invoker: 工具调用器
            llm_caller: LLM调用器
            context_builder: 上下文构建器，如果为None则创建默认实例
            response_mixer: 响应混合器，如果为None则创建默认实例
        """
        # 3. 核心实现
        self.memory = memory
        self.tool_invoker = tool_invoker
        self.llm_caller = llm_caller
        self.context_builder = context_builder or ContextBuilder(memory)
        self.response_mixer = response_mixer or ResponseMixer()
        
        logger.info("DialogueCore初始化完成")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理用户输入，生成响应
        
        Args:
            input_data: 包含用户输入的字典，必须包含processed_input和type字段
            
        Returns:
            包含响应数据的字典
        """
        try:
            # 提取输入数据
            user_input = input_data["processed_input"]
            input_type = input_data["type"]
            
            logger.info(f"处理用户输入: {user_input[:50]}...")
            
            # 构建上下文
            context = self.context_builder.build(user_input, input_type)
            
            # 判断是否需要工具调用
            should_use_tool, tool_info = self.tool_invoker.should_invoke_tool(user_input, context)
            
            tool_results = []
            if should_use_tool:
                # 执行工具调用
                tool_result = self.tool_invoker.invoke_tool(tool_info)
                tool_results.append(tool_result)
                
                # 重建包含工具结果的上下文
                context = self.context_builder.add_tool_result(context, tool_info, tool_result)
            
            # 调用LLM生成响应
            llm_response = self.llm_caller.call(context)
            
            # 混合响应
            final_response = self.response_mixer.mix(llm_response, tool_results)
            
            # 保存对话
            self.memory.save(user_input, final_response)
            
            # 构建响应数据
            response_data = {
                "raw_response": llm_response,
                "final_response": final_response,
                "tool_results": tool_results,
                "metadata": {
                    "processing_time": self.llm_caller.last_processing_time,
                    "token_usage": self.llm_caller.last_token_usage
                }
            }
            
            logger.info(f"对话处理完成，生成响应长度: {len(final_response)}")
            return response_data
            
        # 4. 错误处理
        except KeyError as e:
            logger.error(f"输入数据缺少必要字段: {e}")
            raise ValueError(f"输入数据格式不正确，缺少字段: {e}")
        except Exception as e:
            logger.error(f"对话处理过程中发生错误: {e}")
            raise
```
