# SurrealDB 集成技术笔记

## 概述

本文档记录了在 Rainbow Agent 项目中集成 SurrealDB 的关键技术点、常见问题及解决方案。这些笔记旨在帮助开发团队更好地理解和使用 SurrealDB，避免重复踩坑。

## SurrealDB 基础配置

```python
# SurrealDB配置
SURREALDB_URL = "http://localhost:8000"
SURREALDB_NAMESPACE = "rainbow"
SURREALDB_DATABASE = "test"
SURREALDB_USERNAME = "root"
SURREALDB_PASSWORD = "root"
```

## 关键技术点

### 1. HTTP API 与 WebSocket API

SurrealDB 提供了两种 API：HTTP API 和 WebSocket API。在我们的项目中，我们选择使用 HTTP API，因为它更稳定，不会出现连接断开的问题。

```python
# 使用 HTTP API 执行 SQL 查询
def execute_sql(self, sql: str) -> List[Dict[str, Any]]:
    url = f"{self.base_url}/sql"
    response = requests.post(url, headers=self.headers, data=sql)
    response.raise_for_status()
    return response.json()
```

### 2. 记录创建的两种方式

#### 方式一：两步法（创建空记录，然后更新字段）

```python
# 创建空记录
self.client.create_record("turns", turn_id)

# 更新记录字段
self.client.update_record("turns", turn_id, turn_data)
```

#### 方式二：直接使用 SQL 创建完整记录（推荐）

```python
# 构建 SQL 语句
columns = ", ".join(turn_data.keys())
values_list = []

for key, value in turn_data.items():
    # 处理不同类型的值
    if isinstance(value, str):
        if value == "time::now()":
            values_list.append("time::now()")
        else:
            escaped_value = value.replace("'", "''")
            values_list.append(f"'{escaped_value}'")
    elif isinstance(value, (int, float, bool)):
        values_list.append(str(value))
    elif value is None:
        values_list.append("NULL")
    elif isinstance(value, (dict, list)):
        import json
        json_value = json.dumps(value)
        values_list.append(json_value)
    else:
        values_list.append(f"'{str(value)}'")

values = ", ".join(values_list)
sql = f"INSERT INTO turns ({columns}) VALUES ({values});"

# 执行 SQL
self.client.execute_sql(sql)
```

### 3. 时间处理

SurrealDB 提供了内置的时间函数 `time::now()`，可以直接在 SQL 语句中使用：

```sql
INSERT INTO turns (id, created_at) VALUES ('turn_id', time::now());
```

在 Python 代码中，我们可以这样处理：

```python
turn_data = {
    "id": turn_id,
    "created_at": "time::now()"  # 作为字符串传递
}
```

然后在构建 SQL 语句时，特殊处理这个值：

```python
if value == "time::now()":
    values_list.append("time::now()")  # 不加引号
```

### 4. 必需字段

SurrealDB 中的表可能有必需字段，如果缺少这些字段，记录创建将失败。在我们的项目中，我们发现：

- `turns` 表必须包含 `metadata` 字段，即使它是一个空对象。

```sql
-- 正确的创建轮次记录的 SQL
INSERT INTO turns (id, session_id, role, content, created_at, metadata) 
VALUES ('turn_id', 'session_id', 'user', 'content', time::now(), {});
```

### 5. 错误处理

SurrealDB 的错误信息通常很明确，例如：

```
Found NONE for field 'metadata', with record 'turns:id', but expected a object
```

这表明 `metadata` 字段是必需的，且应该是一个对象类型。

### 6. 内存缓存

为了提高性能和可靠性，我们在 `EnhancedSessionManager` 和 `EnhancedTurnManager` 类中实现了内存缓存：

```python
# 类级别的缓存
_session_cache = {}  # session_id -> session_data
_turn_cache = {}     # session_id -> {turn_id -> turn_data}

# 将数据添加到缓存
if session_id not in EnhancedTurnManager._turn_cache:
    EnhancedTurnManager._turn_cache[session_id] = {}
EnhancedTurnManager._turn_cache[session_id][turn_id] = turn

# 从缓存中获取数据
if session_id in EnhancedTurnManager._turn_cache:
    cached_turns = list(EnhancedTurnManager._turn_cache[session_id].values())
```

这样，即使数据库查询失败，我们仍然可以从内存缓存中获取数据。

## 常见问题及解决方案

### 1. 创建记录失败：缺少必需字段

**问题**：创建记录时出现错误，提示缺少必需字段。

**解决方案**：确保包含所有必需字段，特别是 `metadata` 字段。

### 2. 查询返回空结果

**问题**：查询返回空结果，即使记录应该存在。

**解决方案**：
- 检查查询条件是否正确
- 尝试使用记录 ID 直接查询
- 检查命名空间和数据库设置是否正确

### 3. 时间字段格式不正确

**问题**：时间字段格式不正确，导致查询或排序问题。

**解决方案**：使用 SurrealDB 的内置时间函数 `time::now()`，或者确保时间字符串符合 ISO 8601 格式。

## 最佳实践

1. **使用直接的 SQL 语法**：直接使用 SQL 语法创建记录，而不是先创建空记录再更新字段。

2. **包含所有必需字段**：确保包含所有必需字段，特别是 `metadata` 字段。

3. **使用内存缓存**：实现内存缓存，提高性能和可靠性。

4. **详细的错误处理和日志记录**：添加详细的错误处理和日志记录，以便更容易诊断和解决问题。

5. **使用 HTTP API**：使用 HTTP API 而不是 WebSocket API，因为它更稳定。

## 参考资料

- [SurrealDB 官方文档](https://surrealdb.com/docs)
- [SurrealDB SQL 语法](https://surrealdb.com/docs/surrealql)
- [SurrealDB HTTP API](https://surrealdb.com/docs/integration/http)