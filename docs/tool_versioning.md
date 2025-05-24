# 工具版本管理系统

本文档详细介绍了Rainbow City AI代理的工具版本管理系统，这是阶段四开发的第三个核心组件。

## 1. 概述

工具版本管理系统允许AI代理管理工具的不同版本，提供版本选择、兼容性检查和版本迁移功能。这使得工具可以安全地演进，同时保持向后兼容性，确保系统的稳定性和可靠性。

## 2. 核心组件

### 2.1 版本化工具基类

`VersionedTool` 是一个继承自 `BaseTool` 的基类，为工具添加版本控制功能：

```python
class VersionedTool(BaseTool):
    """
    带版本控制的工具基类
    
    支持版本号、兼容性检查和版本迁移
    """
    
    def __init__(
        self, 
        name: str, 
        description: str, 
        usage: str = None,
        version: str = "1.0.0",
        min_compatible_version: str = "1.0.0",
        deprecated: bool = False,
        deprecation_message: str = None
    ):
        # 初始化...
```

主要特性包括：
- 语义化版本号管理
- 最低兼容版本声明
- 弃用状态和消息

### 2.2 版本状态枚举

`VersionStatus` 枚举定义了工具版本的不同状态：

```python
class VersionStatus(Enum):
    """工具版本状态枚举"""
    ACTIVE = "active"  # 活跃版本
    DEPRECATED = "deprecated"  # 已弃用版本
    EXPERIMENTAL = "experimental"  # 实验性版本
    STABLE = "stable"  # 稳定版本
    LEGACY = "legacy"  # 遗留版本
```

### 2.3 工具版本管理器

`ToolVersionManager` 是一个单例类，负责管理工具的不同版本：

```python
class ToolVersionManager:
    """
    工具版本管理器
    
    管理工具的不同版本，提供版本选择和兼容性检查
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolVersionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
```

主要功能包括：
- 注册工具版本
- 获取指定版本的工具
- 设置默认版本
- 查找兼容版本
- 迁移工具参数

## 3. 版本控制机制

### 3.1 语义化版本

系统使用语义化版本规范（[SemVer](https://semver.org/)）来管理工具版本：

- **主版本号**：不兼容的API变更
- **次版本号**：向后兼容的功能性新增
- **修订号**：向后兼容的问题修正

```python
# 验证版本号格式
try:
    semver.VersionInfo.parse(version)
    semver.VersionInfo.parse(min_compatible_version)
except ValueError as e:
    logger.warning(f"工具 {name} 的版本号格式无效: {e}，将使用默认版本号 1.0.0")
    version = "1.0.0"
    min_compatible_version = "1.0.0"
```

### 3.2 兼容性检查

系统提供了版本兼容性检查功能：

```python
def is_compatible_with(self, other_version: str) -> bool:
    """
    检查是否与指定版本兼容
    
    Args:
        other_version: 要检查的版本号
        
    Returns:
        是否兼容
    """
    try:
        return semver.VersionInfo.parse(other_version) >= semver.VersionInfo.parse(self.min_compatible_version)
    except ValueError:
        return False
```

### 3.3 版本迁移

系统支持在不同版本之间迁移工具参数：

```python
def migrate_args(self, tool_name: str, from_version: str, to_version: str, args: Any) -> Any:
    """
    迁移工具参数
    
    Args:
        tool_name: 工具名称
        from_version: 源版本号
        to_version: 目标版本号
        args: 工具参数
        
    Returns:
        迁移后的参数
    """
    # 获取工具实例...
    # 执行迁移...
```

工具可以实现 `migrate_args_from` 方法来定义自己的参数迁移逻辑：

```python
def migrate_args_from(self, from_version: str, args: Any) -> Any:
    """
    从旧版本迁移参数
    
    Args:
        from_version: 源版本号
        args: 工具参数
        
    Returns:
        迁移后的参数
    """
    # 迁移逻辑...
```

## 4. 弃用管理

系统提供了工具版本弃用的管理功能：

```python
def deprecate_version(self, tool_name: str, version: str, message: str = None) -> bool:
    """
    将工具版本标记为已弃用
    
    Args:
        tool_name: 工具名称
        version: 版本号
        message: 弃用消息
        
    Returns:
        是否标记成功
    """
    # 更新状态...
    # 更新工具实例...
    # 更新默认版本...
```

当使用已弃用的工具版本时，系统会发出警告：

```python
def run(self, args: Any) -> str:
    """执行工具逻辑"""
    # 检查是否已弃用
    if self.deprecated:
        warning = f"警告：工具 {self.name} (v{self.version}) 已弃用"
        if self.deprecation_message:
            warning += f"。{self.deprecation_message}"
        logger.warning(warning)
    
    # 执行实际工具逻辑...
```

## 5. 示例工具

### 5.1 计算器工具 v1

```python
class CalculatorToolV1(VersionedTool):
    """
    计算器工具 v1.0.0
    
    执行基本数学计算
    """
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="执行基本数学计算",
            usage="calculator(表达式)",
            version="1.0.0",
            min_compatible_version="1.0.0"
        )
    
    def _run_versioned(self, args: Any) -> str:
        """执行计算"""
        try:
            # 安全的eval实现
            result = eval(str(args), {"__builtins__": {}}, {"abs": abs, "round": round})
            return f"计算结果: {result}"
        except Exception as e:
            return f"计算错误: {str(e)}"
```

### 5.2 计算器工具 v2

```python
class CalculatorToolV2(VersionedTool):
    """
    计算器工具 v2.0.0
    
    执行高级数学计算，支持更多函数
    """
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="执行高级数学计算，支持更多函数",
            usage="calculator({\"expression\": \"表达式\", \"precision\": 精度})",
            version="2.0.0",
            min_compatible_version="1.0.0"  # 向后兼容v1
        )
    
    def _run_versioned(self, args: Any) -> str:
        """执行计算"""
        # 解析参数...
        # 执行计算...
        # 格式化结果...
    
    def migrate_args_from(self, from_version: str, args: Any) -> Any:
        """
        从旧版本迁移参数
        
        Args:
            from_version: 源版本号
            args: 工具参数
            
        Returns:
            迁移后的参数
        """
        # 如果是v1版本，将字符串参数转换为字典格式
        if from_version.startswith("1."):
            if isinstance(args, str):
                return {"expression": args, "precision": 2}
        
        return args
```

## 6. 使用示例

### 6.1 注册版本化工具

```python
from rainbow_agent.tools.tool_versioning import (
    CalculatorToolV1, CalculatorToolV2, VersionStatus, get_version_manager
)

# 获取版本管理器
manager = get_version_manager()

# 注册不同版本的工具
manager.register_tool_version(
    CalculatorToolV1(),
    status=VersionStatus.STABLE,
    set_as_default=True
)

manager.register_tool_version(
    CalculatorToolV2(),
    status=VersionStatus.EXPERIMENTAL
)
```

### 6.2 获取和使用工具版本

```python
# 获取默认版本
calc = manager.get_tool_version("calculator")
result1 = calc.run("1 + 2 * 3")

# 获取特定版本
calc_v2 = manager.get_tool_version("calculator", "2.0.0")
result2 = calc_v2.run({"expression": "sin(pi/2)", "precision": 4})

# 获取所有版本
versions = manager.get_all_versions("calculator")
print(f"计算器工具的版本：{versions}")

# 获取最新版本
latest = manager.get_latest_version("calculator", include_experimental=False)
```

### 6.3 弃用工具版本

```python
# 弃用版本
manager.deprecate_version(
    "calculator",
    "1.0.0",
    "请使用v2版本，它提供更多数学函数"
)
```

## 7. 最佳实践

1. **版本号管理**：
   - 遵循语义化版本规范
   - 在引入不兼容变更时增加主版本号
   - 在添加向后兼容的新功能时增加次版本号
   - 在进行向后兼容的修复时增加修订号

2. **兼容性声明**：
   - 明确声明工具的最低兼容版本
   - 尽可能保持向后兼容性
   - 在必须破坏兼容性时提供迁移路径

3. **参数迁移**：
   - 为版本化工具实现参数迁移方法
   - 确保迁移逻辑能处理各种边缘情况
   - 提供清晰的迁移错误消息

4. **弃用策略**：
   - 在弃用版本前添加新版本
   - 提供明确的弃用消息，指导用户迁移
   - 给用户足够的时间迁移到新版本

## 8. 未来扩展

1. **版本策略**：
   - 实现更复杂的版本选择策略
   - 支持版本范围声明（如`>=1.0.0,<2.0.0`）
   - 添加版本依赖管理

2. **版本迁移**：
   - 提供自动迁移功能
   - 支持批量迁移工具调用
   - 实现迁移验证和回滚机制

3. **版本历史**：
   - 记录版本变更历史
   - 提供版本比较和差异分析
   - 实现版本使用统计

4. **版本测试**：
   - 添加版本兼容性测试框架
   - 自动验证迁移逻辑
   - 提供版本性能比较

通过工具版本管理系统，Rainbow City AI代理能够安全地演进其工具集，同时保持系统的稳定性和可靠性，为用户提供一致的体验。
