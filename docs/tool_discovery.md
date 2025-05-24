# 动态工具发现系统

本文档详细介绍了Rainbow City AI代理的动态工具发现系统，这是阶段四开发的第二个核心组件。

## 1. 概述

动态工具发现系统允许AI代理在运行时发现、加载和注册新的工具，无需修改核心代码。这大大提高了系统的灵活性和可扩展性，使用户和开发者能够轻松添加新功能。

## 2. 核心组件

### 2.1 工具注册表

`ToolRegistry` 是一个单例类，负责管理已注册的工具和工具提供者：

```python
class ToolRegistry:
    """
    工具注册表
    
    管理已注册的工具和工具提供者
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
```

主要功能包括：
- 注册工具实例和工具类
- 按名称和提供者获取工具
- 管理工具发现路径

### 2.2 工具发现服务

`ToolDiscoveryService` 负责扫描指定路径，发现并加载工具：

```python
class ToolDiscoveryService:
    """
    工具发现服务
    
    提供定期扫描和动态加载工具的功能
    """
    
    def __init__(
        self, 
        registry: ToolRegistry = None,
        scan_interval: int = 300,  # 默认5分钟扫描一次
        auto_scan: bool = True
    ):
        # 初始化...
```

主要功能包括：
- 定期扫描工具变化
- 自动重新加载变化的工具
- 检测文件变化

## 3. 工具发现机制

### 3.1 发现过程

工具发现过程如下：

1. 扫描指定目录中的Python文件
2. 动态导入这些文件作为模块
3. 在模块中查找继承自`BaseTool`的类
4. 注册这些类和它们的实例（如果可以实例化）

```python
def discover_tools(self, auto_register: bool = True) -> Dict[str, List[str]]:
    """
    发现工具
    
    Args:
        auto_register: 是否自动注册发现的工具
        
    Returns:
        发现的工具，按提供者分组
    """
    with self.discovery_lock:
        discovered = {}
        
        for path in self.discovery_paths:
            # 遍历目录...
            # 动态导入模块...
            # 查找工具类...
            # 注册工具...
        
        return discovered
```

### 3.2 文件变化检测

系统使用文件哈希来检测工具文件的变化：

```python
def _check_file_changes(self) -> List[str]:
    """
    检查文件变化
    
    Returns:
        变化的文件列表
    """
    changed_files = []
    
    for path in self.registry.discovery_paths:
        # 遍历目录...
        # 计算文件哈希...
        # 比较哈希值...
    
    return changed_files
```

### 3.3 自动扫描

系统可以配置为定期自动扫描工具变化：

```python
def _scan_loop(self) -> None:
    """扫描循环"""
    while self.scanning:
        try:
            self.scan_for_changes()
        except Exception as e:
            logger.error(f"工具扫描错误: {e}")
        
        # 等待下一次扫描...
```

## 4. 全局实例和初始化

系统提供了全局实例和初始化函数，方便使用：

```python
# 创建全局工具注册表和发现服务实例
global_tool_registry = ToolRegistry()
global_discovery_service = ToolDiscoveryService(registry=global_tool_registry, auto_scan=False)

def initialize_tool_discovery(discovery_paths: List[str] = None, auto_scan: bool = True) -> None:
    """初始化工具发现系统"""
    # 添加发现路径...
    # 初始扫描...
    # 启动自动扫描...
```

## 5. 使用示例

### 5.1 初始化工具发现系统

```python
from rainbow_agent.tools.tool_discovery import initialize_tool_discovery

# 初始化工具发现系统
initialize_tool_discovery(
    discovery_paths=["/path/to/custom/tools"],
    auto_scan=True
)
```

### 5.2 创建自定义工具目录

```python
import os

# 创建自定义工具目录
custom_tools_dir = "/path/to/custom/tools"
os.makedirs(custom_tools_dir, exist_ok=True)

# 创建示例工具文件
with open(os.path.join(custom_tools_dir, "example_tool.py"), "w") as f:
    f.write("""
from rainbow_agent.tools.base import BaseTool

class ExampleTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="example_tool",
            description="这是一个通过动态发现加载的示例工具",
            usage="example_tool(\"参数\")"
        )
    
    def run(self, args):
        return f"示例工具执行成功，参数：{args}"
""")
```

### 5.3 手动扫描工具

```python
from rainbow_agent.tools.tool_discovery import get_discovery_service

# 获取工具发现服务
discovery_service = get_discovery_service()

# 添加工具发现路径
discovery_service.add_discovery_path("/path/to/more/tools")

# 手动扫描工具
discovered = discovery_service.manual_scan()
print(f"发现的工具：{discovered}")
```

## 6. 最佳实践

1. **工具组织**：
   - 使用一致的目录结构组织工具
   - 将相关工具放在同一个模块中
   - 使用有意义的文件名和类名

2. **工具设计**：
   - 确保工具类可以无参数实例化
   - 提供清晰的名称、描述和使用示例
   - 实现适当的错误处理

3. **发现路径**：
   - 避免在工具发现路径中包含非工具的Python文件
   - 使用专门的目录存放自定义工具
   - 考虑使用命名约定（如`*_tool.py`）

4. **性能优化**：
   - 避免过于频繁的扫描
   - 只在必要时启用自动扫描
   - 对大型代码库使用更精细的扫描路径

## 7. 安全注意事项

1. **代码执行风险**：
   - 动态加载的工具代码将在代理的权限下执行
   - 确保只加载来自可信来源的工具
   - 考虑实现工具沙箱或权限控制

2. **验证和审核**：
   - 在生产环境中，考虑添加工具验证机制
   - 记录工具的加载和使用情况
   - 定期审核已发现的工具

## 8. 未来扩展

1. **工具市场**：
   - 实现工具共享和分发机制
   - 支持从远程仓库获取工具

2. **工具依赖管理**：
   - 添加工具依赖声明和检查
   - 自动安装工具所需的依赖

3. **工具热更新**：
   - 实现无需重启代理的工具更新机制
   - 支持工具的热插拔

4. **工具元数据**：
   - 扩展工具元数据，包括作者、版本、许可证等
   - 实现基于元数据的工具筛选和搜索

通过动态工具发现系统，Rainbow City AI代理能够在运行时扩展其功能，适应不断变化的需求，为用户提供更丰富、更灵活的服务。
