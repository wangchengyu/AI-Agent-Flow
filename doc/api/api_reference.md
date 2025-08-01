# 智能Agent任务管理系统 - API参考文档

## 目录

1. [数据库管理模块API](#数据库管理模块api)
2. [RAG知识管理模块API](#rag知识管理模块api)
3. [MCP工具管理模块API](#mcp工具管理模块api)
4. [Agent流程管理模块API](#agent流程管理模块api)
5. [命令行交互模块API](#命令行交互模块api)
6. [信息补充循环API](#信息补充循环api)
7. [LLM验证模块API](#llm验证模块api)

## 数据库管理模块API

### DatabaseManager

#### 初始化

```python
async def initialize()
```

**描述**：初始化数据库管理器，创建数据库表结构

**参数**：无

**返回值**：无

**异常**：
- `DatabaseError`: 数据库初始化失败

#### 获取连接

```python
def get_connection() -> sqlite3.Connection
```

**描述**：获取数据库连接

**参数**：无

**返回值**：
- `sqlite3.Connection`: 数据库连接对象

**异常**：
- `DatabaseError`: 获取连接失败

#### 执行查询

```python
async def execute_query(query: str, params: tuple = None) -> list
```

**描述**：执行查询操作

**参数**：
- `query` (str): SQL查询语句
- `params` (tuple, optional): 查询参数，默认为None

**返回值**：
- `list`: 查询结果列表

**异常**：
- `DatabaseError`: 查询执行失败

#### 执行更新

```python
async def execute_update(query: str, params: tuple = None) -> int
```

**描述**：执行更新操作

**参数**：
- `query` (str): SQL更新语句
- `params` (tuple, optional): 更新参数，默认为None

**返回值**：
- `int`: 受影响的行数

**异常**：
- `DatabaseError`: 更新执行失败

#### 备份数据库

```python
async def backup(backup_path: str) -> bool
```

**描述**：备份数据库

**参数**：
- `backup_path` (str): 备份文件路径

**返回值**：
- `bool`: 备份是否成功

**异常**：
- `DatabaseError`: 备份失败

#### 恢复数据库

```python
async def restore(backup_path: str) -> bool
```

**描述**：恢复数据库

**参数**：
- `backup_path` (str): 备份文件路径

**返回值**：
- `bool`: 恢复是否成功

**异常**：
- `DatabaseError`: 恢复失败

### TaskHistoryManager

#### 创建任务

```python
async def create_task(task_data: dict) -> int
```

**描述**：创建任务记录

**参数**：
- `task_data` (dict): 任务数据，包含以下字段：
  - `task_name` (str): 任务名称
  - `description` (str): 任务描述
  - `user_id` (int, optional): 用户ID，默认为None

**返回值**：
- `int`: 任务ID

**异常**：
- `DatabaseError`: 创建任务失败
- `ValidationError`: 任务数据验证失败

#### 获取任务

```python
async def get_task(task_id: int) -> dict
```

**描述**：获取任务信息

**参数**：
- `task_id` (int): 任务ID

**返回值**：
- `dict`: 任务信息，包含以下字段：
  - `id` (int): 任务ID
  - `task_name` (str): 任务名称
  - `description` (str): 任务描述
  - `status` (str): 任务状态
  - `created_at` (str): 创建时间
  - `start_time` (str): 开始时间
  - `end_time` (str): 结束时间
  - `user_id` (int): 用户ID

**异常**：
- `DatabaseError`: 获取任务失败
- `NotFoundError`: 任务不存在

#### 更新任务

```python
async def update_task(task_id: int, task_data: dict) -> bool
```

**描述**：更新任务信息

**参数**：
- `task_id` (int): 任务ID
- `task_data` (dict): 任务数据，包含以下字段：
  - `task_name` (str, optional): 任务名称
  - `description` (str, optional): 任务描述
  - `status` (str, optional): 任务状态
  - `start_time` (str, optional): 开始时间
  - `end_time` (str, optional): 结束时间

**返回值**：
- `bool`: 更新是否成功

**异常**：
- `DatabaseError`: 更新任务失败
- `NotFoundError`: 任务不存在
- `ValidationError`: 任务数据验证失败

#### 创建子任务

```python
async def create_sub_task(sub_task_data: dict) -> int
```

**描述**：创建子任务记录

**参数**：
- `sub_task_data` (dict): 子任务数据，包含以下字段：
  - `task_id` (int): 任务ID
  - `name` (str): 子任务名称
  - `description` (str): 子任务描述

**返回值**：
- `int`: 子任务ID

**异常**：
- `DatabaseError`: 创建子任务失败
- `ValidationError`: 子任务数据验证失败

#### 获取子任务列表

```python
async def get_sub_tasks(task_id: int) -> list
```

**描述**：获取子任务列表

**参数**：
- `task_id` (int): 任务ID

**返回值**：
- `list`: 子任务列表，每个子任务包含以下字段：
  - `id` (int): 子任务ID
  - `task_id` (int): 任务ID
  - `name` (str): 子任务名称
  - `description` (str): 子任务描述
  - `status` (str): 子任务状态
  - `result` (str): 子任务结果
  - `created_at` (str): 创建时间
  - `start_time` (str): 开始时间
  - `end_time` (str): 结束时间

**异常**：
- `DatabaseError`: 获取子任务列表失败

#### 创建任务结果

```python
async def create_task_result(task_id: int, result_data: dict) -> int
```

**描述**：创建任务结果记录

**参数**：
- `task_id` (int): 任务ID
- `result_data` (dict): 结果数据，包含以下字段：
  - `result` (str): 结果内容

**返回值**：
- `int`: 结果ID

**异常**：
- `DatabaseError`: 创建任务结果失败
- `ValidationError`: 结果数据验证失败

#### 获取任务结果

```python
async def get_task_result(task_id: int) -> dict
```

**描述**：获取任务结果

**参数**：
- `task_id` (int): 任务ID

**返回值**：
- `dict`: 任务结果，包含以下字段：
  - `id` (int): 结果ID
  - `task_id` (int): 任务ID
  - `result` (str): 结果内容
  - `created_at` (str): 创建时间

**异常**：
- `DatabaseError`: 获取任务结果失败
- `NotFoundError`: 任务结果不存在

#### 创建任务验证

```python
async def create_task_validation(task_id: int, validation_data: dict) -> int
```

**描述**：创建任务验证记录

**参数**：
- `task_id` (int): 任务ID
- `validation_data` (dict): 验证数据，包含以下字段：
  - `is_valid` (bool): 是否有效
  - `overall_score` (float): 总体分数
  - `validation_results` (dict): 验证结果
  - `issues` (list): 问题列表
  - `improvement_suggestions` (list): 改进建议
  - `validation_report` (str): 验证报告

**返回值**：
- `int`: 验证ID

**异常**：
- `DatabaseError`: 创建任务验证失败
- `ValidationError`: 验证数据验证失败

#### 获取任务验证

```python
async def get_task_validation(task_id: int) -> dict
```

**描述**：获取任务验证

**参数**：
- `task_id` (int): 任务ID

**返回值**：
- `dict`: 任务验证，包含以下字段：
  - `id` (int): 验证ID
  - `task_id` (int): 任务ID
  - `is_valid` (bool): 是否有效
  - `overall_score` (float): 总体分数
  - `validation_results` (dict): 验证结果
  - `issues` (list): 问题列表
  - `improvement_suggestions` (list): 改进建议
  - `validation_report` (str): 验证报告
  - `created_at` (str): 创建时间

**异常**：
- `DatabaseError`: 获取任务验证失败
- `NotFoundError`: 任务验证不存在

#### 创建用户确认

```python
async def create_user_confirmation(task_id: int, confirmation_data: dict) -> int
```

**描述**：创建用户确认记录

**参数**：
- `task_id` (int): 任务ID
- `confirmation_data` (dict): 确认数据，包含以下字段：
  - `confirmation_type` (str): 确认类型
  - `message` (str): 确认消息
  - `data` (dict): 确认数据
  - `confirmed` (bool): 是否确认
  - `rejected` (bool): 是否拒绝
  - `timeout` (bool): 是否超时
  - `reason` (str): 理由
  - `user_input` (dict): 用户输入

**返回值**：
- `int`: 确认ID

**异常**：
- `DatabaseError`: 创建用户确认失败
- `ValidationError`: 确认数据验证失败

#### 获取用户确认

```python
async def get_user_confirmation(task_id: int) -> dict
```

**描述**：获取用户确认

**参数**：
- `task_id` (int): 任务ID

**返回值**：
- `dict`: 用户确认，包含以下字段：
  - `id` (int): 确认ID
  - `task_id` (int): 任务ID
  - `confirmation_type` (str): 确认类型
  - `message` (str): 确认消息
  - `data` (dict): 确认数据
  - `confirmed` (bool): 是否确认
  - `rejected` (bool): 是否拒绝
  - `timeout` (bool): 是否超时
  - `reason` (str): 理由
  - `user_input` (dict): 用户输入
  - `created_at` (str): 创建时间

**异常**：
- `DatabaseError`: 获取用户确认失败
- `NotFoundError`: 用户确认不存在

### ConfigManager

#### 初始化

```python
async def initialize()
```

**描述**：初始化配置管理器

**参数**：无

**返回值**：无

**异常**：
- `ConfigError`: 配置初始化失败

#### 加载配置

```python
def load_config() -> dict
```

**描述**：加载配置

**参数**：无

**返回值**：
- `dict`: 配置数据

**异常**：
- `ConfigError`: 加载配置失败

#### 保存配置

```python
def save_config() -> bool
```

**描述**：保存配置

**参数**：无

**返回值**：
- `bool`: 保存是否成功

**异常**：
- `ConfigError`: 保存配置失败

#### 获取配置值

```python
def get(key: str, default=None) -> Any
```

**描述**：获取配置值

**参数**：
- `key` (str): 配置键
- `default` (Any, optional): 默认值，默认为None

**返回值**：
- `Any`: 配置值

**异常**：无

#### 设置配置值

```python
def set(key: str, value: Any) -> bool
```

**描述**：设置配置值

**参数**：
- `key` (str): 配置键
- `value` (Any): 配置值

**返回值**：
- `bool`: 设置是否成功

**异常**：
- `ConfigError`: 设置配置失败

### UserManager

#### 初始化

```python
async def initialize()
```

**描述**：初始化用户管理器

**参数**：无

**返回值**：无

**异常**：
- `DatabaseError`: 用户管理器初始化失败

#### 创建用户

```python
async def create_user(user_data: dict) -> int
```

**描述**：创建用户

**参数**：
- `user_data` (dict): 用户数据，包含以下字段：
  - `username` (str): 用户名
  - `password` (str): 密码
  - `email` (str, optional): 电子邮件
  - `role` (str, optional): 角色

**返回值**：
- `int`: 用户ID

**异常**：
- `DatabaseError`: 创建用户失败
- `ValidationError`: 用户数据验证失败

#### 获取用户

```python
async def get_user(user_id: int) -> dict
```

**描述**：获取用户信息

**参数**：
- `user_id` (int): 用户ID

**返回值**：
- `dict`: 用户信息，包含以下字段：
  - `id` (int): 用户ID
  - `username` (str): 用户名
  - `email` (str): 电子邮件
  - `role` (str): 角色
  - `created_at` (str): 创建时间

**异常**：
- `DatabaseError`: 获取用户失败
- `NotFoundError`: 用户不存在

#### 根据用户名获取用户

```python
async def get_user_by_username(username: str) -> dict
```

**描述**：根据用户名获取用户

**参数**：
- `username` (str): 用户名

**返回值**：
- `dict`: 用户信息，包含以下字段：
  - `id` (int): 用户ID
  - `username` (str): 用户名
  - `email` (str): 电子邮件
  - `role` (str): 角色
  - `created_at` (str): 创建时间

**异常**：
- `DatabaseError`: 获取用户失败
- `NotFoundError`: 用户不存在

#### 验证用户身份

```python
async def authenticate_user(username: str, password: str) -> dict
```

**描述**：验证用户身份

**参数**：
- `username` (str): 用户名
- `password` (str): 密码

**返回值**：
- `dict`: 用户信息，如果验证失败则返回None

**异常**：
- `DatabaseError`: 验证用户身份失败

### KnowledgeSourceManager

#### 初始化

```python
async def initialize()
```

**描述**：初始化知识源管理器

**参数**：无

**返回值**：无

**异常**：
- `DatabaseError`: 知识源管理器初始化失败

#### 创建知识源

```python
async def create_knowledge_source(source_data: dict) -> int
```

**描述**：创建知识源

**参数**：
- `source_data` (dict): 知识源数据，包含以下字段：
  - `name` (str): 知识源名称
  - `description` (str): 知识源描述
  - `type` (str): 知识源类型
  - `path` (str): 知识源路径

**返回值**：
- `int`: 知识源ID

**异常**：
- `DatabaseError`: 创建知识源失败
- `ValidationError`: 知识源数据验证失败

#### 获取知识源

```python
async def get_knowledge_source(source_id: int) -> dict
```

**描述**：获取知识源

**参数**：
- `source_id` (int): 知识源ID

**返回值**：
- `dict`: 知识源信息，包含以下字段：
  - `id` (int): 知识源ID
  - `name` (str): 知识源名称
  - `description` (str): 知识源描述
  - `type` (str): 知识源类型
  - `path` (str): 知识源路径
  - `created_at` (str): 创建时间
  - `updated_at` (str): 更新时间

**异常**：
- `DatabaseError`: 获取知识源失败
- `NotFoundError`: 知识源不存在

#### 更新知识源

```python
async def update_knowledge_source(source_id: int, source_data: dict) -> bool
```

**描述**：更新知识源

**参数**：
- `source_id` (int): 知识源ID
- `source_data` (dict): 知识源数据，包含以下字段：
  - `name` (str, optional): 知识源名称
  - `description` (str, optional): 知识源描述
  - `type` (str, optional): 知识源类型
  - `path` (str, optional): 知识源路径

**返回值**：
- `bool`: 更新是否成功

**异常**：
- `DatabaseError`: 更新知识源失败
- `NotFoundError`: 知识源不存在
- `ValidationError`: 知识源数据验证失败

#### 删除知识源

```python
async def delete_knowledge_source(source_id: int) -> bool
```

**描述**：删除知识源

**参数**：
- `source_id` (int): 知识源ID

**返回值**：
- `bool`: 删除是否成功

**异常**：
- `DatabaseError`: 删除知识源失败
- `NotFoundError`: 知识源不存在

#### 列出知识源

```python
async def list_knowledge_sources() -> list
```

**描述**：列出所有知识源

**参数**：无

**返回值**：
- `list`: 知识源列表，每个知识源包含以下字段：
  - `id` (int): 知识源ID
  - `name` (str): 知识源名称
  - `description` (str): 知识源描述
  - `type` (str): 知识源类型
  - `path` (str): 知识源路径
  - `created_at` (str): 创建时间
  - `updated_at` (str): 更新时间

**异常**：
- `DatabaseError`: 列出知识源失败

### ToolLogManager

#### 初始化

```python
async def initialize()
```

**描述**：初始化工具日志管理器

**参数**：无

**返回值**：无

**异常**：
- `DatabaseError`: 工具日志管理器初始化失败

#### 创建工具日志

```python
async def create_tool_log(log_data: dict) -> int
```

**描述**：创建工具日志

**参数**：
- `log_data` (dict): 日志数据，包含以下字段：
  - `task_id` (int): 任务ID
  - `sub_task_id` (int, optional): 子任务ID
  - `tool_name` (str): 工具名称
  - `parameters` (dict): 参数
  - `result` (dict): 结果
  - `execution_time` (float): 执行时间

**返回值**：
- `int`: 日志ID

**异常**：
- `DatabaseError`: 创建工具日志失败
- `ValidationError`: 日志数据验证失败

#### 获取工具日志

```python
async def get_tool_logs(task_id: int = None, tool_name: str = None) -> list
```

**描述**：获取工具日志

**参数**：
- `task_id` (int, optional): 任务ID，默认为None
- `tool_name` (str, optional): 工具名称，默认为None

**返回值**：
- `list`: 工具日志列表，每个日志包含以下字段：
  - `id` (int): 日志ID
  - `task_id` (int): 任务ID
  - `sub_task_id` (int): 子任务ID
  - `tool_name` (str): 工具名称
  - `parameters` (dict): 参数
  - `result` (dict): 结果
  - `execution_time` (float): 执行时间
  - `created_at` (str): 创建时间

**异常**：
- `DatabaseError`: 获取工具日志失败

#### 获取工具日志统计

```python
async def get_tool_log_stats(days: int = 30) -> dict
```

**描述**：获取工具日志统计

**参数**：
- `days` (int, optional): 统计天数，默认为30

**返回值**：
- `dict`: 统计信息，包含以下字段：
  - `total_calls` (int): 总调用次数
  - `success_rate` (float): 成功率
  - `average_execution_time` (float): 平均执行时间
  - `tool_usage` (dict): 工具使用情况

**异常**：
- `DatabaseError`: 获取工具日志统计失败

### BackupManager

#### 初始化

```python
async def initialize()
```

**描述**：初始化备份管理器

**参数**：无

**返回值**：无

**异常**：
- `DatabaseError`: 备份管理器初始化失败

#### 创建备份

```python
async def create_backup() -> str
```

**描述**：创建备份

**参数**：无

**返回值**：
- `str`: 备份文件路径

**异常**：
- `DatabaseError`: 创建备份失败

#### 恢复备份

```python
async def restore_backup(backup_path: str) -> bool
```

**描述**：恢复备份

**参数**：
- `backup_path` (str): 备份文件路径

**返回值**：
- `bool`: 恢复是否成功

**异常**：
- `DatabaseError`: 恢复备份失败
- `FileNotFoundError`: 备份文件不存在

#### 列出备份

```python
async def list_backups() -> list
```

**描述**：列出所有备份

**参数**：无

**返回值**：
- `list`: 备份列表，每个备份包含以下字段：
  - `path` (str): 备份文件路径
  - `size` (int): 备份文件大小
  - `created_at` (str): 创建时间

**异常**：
- `DatabaseError`: 列出备份失败

#### 删除备份

```python
async def delete_backup(backup_path: str) -> bool
```

**描述**：删除备份

**参数**：
- `backup_path` (str): 备份文件路径

**返回值**：
- `bool`: 删除是否成功

**异常**：
- `DatabaseError`: 删除备份失败
- `FileNotFoundError`: 备份文件不存在

#### 定时备份

```python
async def schedule_backup(interval: int) -> bool
```

**描述**：定时备份

**参数**：
- `interval` (int): 备份间隔（秒）

**返回值**：
- `bool`: 设置是否成功

**异常**：
- `DatabaseError`: 设置定时备份失败

## RAG知识管理模块API

### DocumentProcessor

#### 初始化

```python
async def initialize()
```

**描述**：初始化文档处理器

**参数**：无

**返回值**：无

**异常**：
- `ProcessingError`: 文档处理器初始化失败

#### 处理文档

```python
async def process_document(file_path: str) -> dict
```

**描述**：处理文档，提取文本和元数据

**参数**：
- `file_path` (str): 文档文件路径

**返回值**：
- `dict`: 处理结果，包含以下字段：
  - `text` (str): 提取的文本
  - `metadata` (dict): 元数据
  - `chunks` (list): 文本块列表

**异常**：
- `ProcessingError`: 文档处理失败
- `FileNotFoundError`: 文档文件不存在

### VectorEmbedder

#### 初始化

```python
async def initialize()
```

**描述**：初始化向量嵌入器

**参数**：无

**返回值**：无

**异常**：
- `EmbeddingError`: 向量嵌入器初始化失败

#### 嵌入文本

```python
async def embed(text: str) -> list
```

**描述**：将文本转换为向量表示

**参数**：
- `text` (str): 文本

**返回值**：
- `list`: 向量表示

**异常**：
- `EmbeddingError`: 文本嵌入失败

#### 批量嵌入文本

```python
async def embed_batch(texts: list) -> list
```

**描述**：批量将文本转换为向量表示

**参数**：
- `texts` (list): 文本列表

**返回值**：
- `list`: 向量表示列表

**异常**：
- `EmbeddingError`: 文本嵌入失败

### VectorDatabase

#### 初始化

```python
async def initialize()
```

**描述**：初始化向量数据库

**参数**：无

**返回值**：无

**异常**：
- `DatabaseError`: 向量数据库初始化失败

#### 添加文档

```python
async def add_document(doc_id: str, embeddings: list, metadata: dict) -> bool
```

**描述**：添加文档到向量数据库

**参数**：
- `doc_id` (str): 文档ID
- `embeddings` (list): 向量表示列表
- `metadata` (dict): 元数据

**返回值**：
- `bool`: 添加是否成功

**异常**：
- `DatabaseError`: 添加文档失败
- `ValidationError`: 参数验证失败

#### 搜索文档

```python
async def search(query_embedding: list, limit: int = 10) -> list
```

**描述**：搜索相似文档

**参数**：
- `query_embedding` (list): 查询向量
- `limit` (int, optional): 返回结果数量限制，默认为10

**返回值**：
- `list`: 搜索结果列表，每个结果包含以下字段：
  - `doc_id` (str): 文档ID
  - `score` (float): 相似度分数
  - `metadata` (dict): 元数据

**异常**：
- `DatabaseError`: 搜索文档失败
- `ValidationError`: 参数验证失败

#### 删除文档

```python
async def delete_document(doc_id: str) -> bool
```

**描述**：从向量数据库中删除文档

**参数**：
- `doc_id` (str): 文档ID

**返回值**：
- `bool`: 删除是否成功

**异常**：
- `DatabaseError`: 删除文档失败

#### 获取文档

```python
async def get_document(doc_id: str) -> dict
```

**描述**：获取文档信息

**参数**：
- `doc_id` (str): 文档ID

**返回值**：
- `dict`: 文档信息，包含以下字段：
  - `doc_id` (str): 文档ID
  - `embeddings` (list): 向量表示列表
  - `metadata` (dict): 元数据

**异常**：
- `DatabaseError`: 获取文档失败
- `NotFoundError`: 文档不存在

### Retriever

#### 初始化

```python
async def initialize()
```

**描述**：初始化检索器

**参数**：无

**返回值**：无

**异常**：
- `RetrievalError`: 检索器初始化失败

#### 检索知识

```python
async def retrieve(query: str, limit: int = 10) -> list
```

**描述**：检索相关知识

**参数**：
- `query` (str): 查询文本
- `limit` (int, optional): 返回结果数量限制，默认为10

**返回值**：
- `list`: 检索结果列表，每个结果包含以下字段：
  - `doc_id` (str): 文档ID
  - `text` (str): 文本内容
  - `score` (float): 相关性分数
  - `metadata` (dict): 元数据

**异常**：
- `RetrievalError`: 检索知识失败

### Reranker

#### 初始化

```python
async def initialize()
```

**描述**：初始化重排序器

**参数**：无

**返回值**：无

**异常**：
- `RerankingError`: 重排序器初始化失败

#### 重排序文档

```python
async def rerank(query: str, documents: list, limit: int = 10) -> list
```

**描述**：对检索结果进行重排序

**参数**：
- `query` (str): 查询文本
- `documents` (list): 文档列表
- `limit` (int, optional): 返回结果数量限制，默认为10

**返回值**：
- `list`: 重排序后的文档列表，每个文档包含以下字段：
  - `doc_id` (str): 文档ID
  - `text` (str): 文本内容
  - `score` (float): 相关性分数
  - `metadata` (dict): 元数据

**异常**：
- `RerankingError`: 重排序文档失败

### KnowledgeManager

#### 初始化

```python
async def initialize()
```

**描述**：初始化知识管理器

**参数**：无

**返回值**：无

**异常**：
- `KnowledgeError`: 知识管理器初始化失败

#### 添加文档

```python
async def add_document(file_path: str, metadata: dict = None) -> str
```

**描述**：添加文档到知识库

**参数**：
- `file_path` (str): 文档文件路径
- `metadata` (dict, optional): 元数据，默认为None

**返回值**：
- `str`: 文档ID

**异常**：
- `KnowledgeError`: 添加文档失败
- `FileNotFoundError`: 文档文件不存在

#### 搜索知识

```python
async def search_knowledge(query: str, limit: int = 10) -> list
```

**描述**：搜索知识

**参数**：
- `query` (str): 查询文本
- `limit` (int, optional): 返回结果数量限制，默认为10

**返回值**：
- `list`: 搜索结果列表，每个结果包含以下字段：
  - `doc_id` (str): 文档ID
  - `text` (str): 文本内容
  - `score` (float): 相关性分数
  - `metadata` (dict): 元数据

**异常**：
- `KnowledgeError`: 搜索知识失败

#### 删除文档

```python
async def delete_document(doc_id: str) -> bool
```

**描述**：从知识库中删除文档

**参数**：
- `doc_id` (str): 文档ID

**返回值**：
- `bool`: 删除是否成功

**异常**：
- `KnowledgeError`: 删除文档失败
- `NotFoundError`: 文档不存在

#### 列出文档

```python
async def list_documents() -> list
```

**描述**：列出知识库中的所有文档

**参数**：无

**返回值**：
- `list`: 文档列表，每个文档包含以下字段：
  - `doc_id` (str): 文档ID
  - `metadata` (dict): 元数据

**异常**：
- `KnowledgeError`: 列出文档失败

## MCP工具管理模块API

### MCPServer

#### 初始化

```python
async def initialize()
```

**描述**：初始化MCP服务器

**参数**：无

**返回值**：无

**异常**：
- `ServerError`: MCP服务器初始化失败

#### 注册工具

```python
async def register_tool(tool_name: str, tool_handler: callable) -> bool
```

**描述**：注册工具

**参数**：
- `tool_name` (str): 工具名称
- `tool_handler` (callable): 工具处理函数

**返回值**：
- `bool`: 注册是否成功

**异常**：
- `ServerError`: 注册工具失败

#### 注销工具

```python
async def unregister_tool(tool_name: str) -> bool
```

**描述**：注销工具

**参数**：
- `tool_name` (str): 工具名称

**返回值**：
- `bool`: 注销是否成功

**异常**：
- `ServerError`: 注销工具失败

#### 列出工具

```python
async def list_tools() -> list
```

**描述**：列出所有工具

**参数**：无

**返回值**：
- `list`: 工具列表，每个工具包含以下字段：
  - `name` (str): 工具名称
  - `description` (str): 工具描述
  - `parameters` (dict): 参数定义

**异常**：
- `ServerError`: 列出工具失败

### MCPClient

#### 初始化

```python
async def initialize()
```

**描述**：初始化MCP客户端

**参数**：无

**返回值**：无

**异常**：
- `ClientError`: MCP客户端初始化失败

#### 调用工具

```python
async def call_tool(tool_name: str, parameters: dict) -> dict
```

**描述**：调用工具

**参数**：
- `tool_name` (str): 工具名称
- `parameters` (dict): 参数

**返回值**：
- `dict`: 工具调用结果

**异常**：
- `ClientError`: 调用工具失败
- `ToolError`: 工具执行失败

#### 列出工具

```python
async def list_tools() -> list
```

**描述**：列出所有工具

**参数**：无

**返回值**：
- `list`: 工具列表，每个工具包含以下字段：
  - `name` (str): 工具名称
  - `description` (str): 工具描述
  - `parameters` (dict): 参数定义

**异常**：
- `ClientError`: 列出工具失败

### ToolManager

#### 初始化

```python
async def initialize()
```

**描述**：初始化工具管理器

**参数**：无

**返回值**：无

**异常**：
- `ToolError`: 工具管理器初始化失败

#### 注册MCP服务器

```python
async def register_mcp_server(server_name: str, server_url: str, api_key: str) -> bool
```

**描述**：注册MCP服务器

**参数**：
- `server_name` (str): 服务器名称
- `server_url` (str): 服务器URL
- `api_key` (str): API密钥

**返回值**：
- `bool`: 注册是否成功

**异常**：
- `ToolError`: 注册MCP服务器失败

#### 注销MCP服务器

```python
async def unregister_mcp_server(server_name: str) -> bool
```

**描述**：注销MCP服务器

**参数**：
- `server_name` (str): 服务器名称

**返回值**：
- `bool`: 注销是否成功

**异常**：
- `ToolError`: 注销MCP服务器失败

#### 调用工具

```python
async def call_tool(tool_name: str, parameters: dict, user_id: int) -> dict
```

**描述**：调用工具

**参数**：
- `tool_name` (str): 工具名称
- `parameters` (dict): 参数
- `user_id` (int): 用户ID

**返回值**：
- `dict`: 工具调用结果

**异常**：
- `ToolError`: 调用工具失败
- `PermissionError`: 权限不足
- `ToolExecutionError`: 工具执行失败

#### 列出工具

```python
async def list_tools() -> list
```

**描述**：列出所有工具

**参数**：无

**返回值**：
- `list`: 工具列表，每个工具包含以下字段：
  - `name` (str): 工具名称
  - `description` (str): 工具描述
  - `server_name` (str): 服务器名称
  - `parameters` (dict): 参数定义

**异常**：
- `ToolError`: 列出工具失败

### PermissionManager

#### 初始化

```python
async def initialize()
```

**描述**：初始化权限管理器

**参数**：无

**返回值**：无

**异常**：
- `PermissionError`: 权限管理器初始化失败

#### 检查权限

```python
async def check_permission(user_id: int, tool_name: str) -> bool
```

**描述**：检查用户是否有工具使用权限

**参数**：
- `user_id` (int): 用户ID
- `tool_name` (str): 工具名称

**返回值**：
- `bool`: 是否有权限

**异常**：
- `PermissionError`: 检查权限失败

#### 授予权限

```python
async def grant_permission(user_id: int, tool_name: str) -> bool
```

**描述**：授予用户工具使用权限

**参数**：
- `user_id` (int): 用户ID
- `tool_name` (str): 工具名称

**返回值**：
- `bool`: 授予是否成功

**异常**：
- `PermissionError`: 授予权限失败

#### 撤销权限

```python
async def revoke_permission(user_id: int, tool_name: str) -> bool
```

**描述**：撤销用户工具使用权限

**参数**：
- `user_id` (int): 用户ID
- `tool_name` (str): 工具名称

**返回值**：
- `bool`: 撤销是否成功

**异常**：
- `PermissionError`: 撤销权限失败

#### 列出权限

```python
async def list_permissions(user_id: int) -> list
```

**描述**：列出用户的所有权限

**参数**：
- `user_id` (int): 用户ID

**返回值**：
- `list`: 权限列表，每个权限包含以下字段：
  - `tool_name` (str): 工具名称
  - `granted_at` (str): 授予时间

**异常**：
- `PermissionError`: 列出权限失败

## Agent流程管理模块API

### AgentManager

#### 初始化

```python
async def initialize()
```

**描述**：初始化Agent管理器

**参数**：无

**返回值**：无

**异常**：
- `AgentError`: Agent管理器初始化失败

#### 执行任务

```python
async def execute_task(task_data: dict) -> dict
```

**描述**：执行任务

**参数**：
- `task_data` (dict): 任务数据，包含以下字段：
  - `task_name` (str): 任务名称
  - `description` (str): 任务描述
  - `user_id` (int, optional): 用户ID，默认为None

**返回值**：
- `dict`: 任务结果，包含以下字段：
  - `task_id` (int): 任务ID
  - `result` (dict): 任务结果
  - `status` (str): 任务状态

**异常**：
- `AgentError`: 执行任务失败
- `ValidationError`: 任务数据验证失败

### TaskDecomposer

#### 初始化

```python
async def initialize()
```

**描述**：初始化任务分解器

**参数**：无

**返回值**：无

**异常**：
- `DecompositionError`: 任务分解器初始化失败

#### 分解任务

```python
async def decompose_task(task_id: int, task_description: str) -> list
```

**描述**：将任务分解为子任务

**参数**：
- `task_id` (int): 任务ID
- `task_description` (str): 任务描述

**返回值**：
- `list`: 子任务列表，每个子任务包含以下字段：
  - `name` (str): 子任务名称
  - `description` (str): 子任务描述
  - `dependencies` (list): 依赖的子任务ID列表

**异常**：
- `DecompositionError`: 分解任务失败

### SubTaskManager

#### 初始化

```python
async def initialize()
```

**描述**：初始化子任务管理器

**参数**：无

**返回值**：无

**异常**：
- `SubTaskError`: 子任务管理器初始化失败

#### 执行子任务

```python
async def execute_sub_task(sub_task_id: int) -> dict
```

**描述**：执行子任务

**参数**：
- `sub_task_id` (int): 子任务ID

**返回值**：
- `dict`: 子任务结果，包含以下字段：
  - `sub_task_id` (int): 子任务ID
  - `result` (dict): 子任务结果
  - `status` (str): 子任务状态

**异常**：
- `SubTaskError`: 执行子任务失败
- `NotFoundError`: 子任务不存在

#### 获取子任务状态

```python
async def get_sub_task_status(sub_task_id: int) -> str
```

**描述**：获取子任务状态

**参数**：
- `sub_task_id` (int): 子任务ID

**返回值**：
- `str`: 子任务状态

**异常**：
- `SubTaskError`: 获取子任务状态失败
- `NotFoundError`: 子任务不存在

#### 更新子任务状态

```python
async def update_sub_task_status(sub_task_id: int, status: str) -> bool
```

**描述**：更新子任务状态

**参数**：
- `sub_task_id` (int): 子任务ID
- `status` (str): 子任务状态

**返回值**：
- `bool`: 更新是否成功

**异常**：
- `SubTaskError`: 更新子任务状态失败
- `NotFoundError`: 子任务不存在
- `ValidationError`: 状态值无效

### InfoGatheringLoop

#### 初始化

```python
async def initialize()
```

**描述**：初始化信息收集循环

**参数**：无

**返回值**：无

**异常**：
- `InfoGatheringError`: 信息收集循环初始化失败

#### 执行信息收集循环

```python
async def execute_info_gathering_loop(task_id: int, sub_task_results: list) -> dict
```

**描述**：执行信息收集循环

**参数**：
- `task_id` (int): 任务ID
- `sub_task_results` (list): 子任务结果列表

**返回值**：
- `dict`: 循环结果，包含以下字段：
  - `completed` (bool): 是否完成
  - `info_requirements` (list): 信息需求列表
  - `user_inputs` (list): 用户输入列表
  - `integrated_info` (dict): 整合信息

**异常**：
- `InfoGatheringError`: 执行信息收集循环失败

### ValidationModule

#### 初始化

```python
async def initialize()
```

**描述**：初始化验证模块

**参数**：无

**返回值**：无

**异常**：
- `ValidationError`: 验证模块初始化失败

#### 验证任务结果

```python
async def validate_task_result(task_id: int, task_result: dict) -> dict
```

**描述**：验证任务结果

**参数**：
- `task_id` (int): 任务ID
- `task_result` (dict): 任务结果

**返回值**：
- `dict`: 验证结果，包含以下字段：
  - `is_valid` (bool): 是否有效
  - `overall_score` (float): 总体分数
  - `validation_results` (dict): 各项验证结果
  - `issues` (list): 问题列表
  - `improvement_suggestions` (list): 改进建议

**异常**：
- `ValidationError`: 验证任务结果失败

## 命令行交互模块API

### CLIParser

#### 初始化

```python
async def initialize()
```

**描述**：初始化CLI解析器

**参数**：无

**返回值**：无

**异常**：
- `CLIError`: CLI解析器初始化失败

#### 解析参数

```python
def parse_args(args: list) -> dict
```

**描述**：解析命令行参数

**参数**：
- `args` (list): 命令行参数列表

**返回值**：
- `dict`: 解析结果，包含以下字段：
  - `command` (str): 命令
  - `args` (dict): 命令参数

**异常**：
- `CLIError`: 解析参数失败

### InteractiveInterface

#### 初始化

```python
async def initialize()
```

**描述**：初始化交互式界面

**参数**：无

**返回值**：无

**异常**：
- `InterfaceError`: 交互式界面初始化失败

#### 显示消息

```python
async def message(message: str, level: str = "info")
```

**描述**：显示消息

**参数**：
- `message` (str): 消息内容
- `level` (str, optional): 消息级别，可选值为"info"、"warning"、"error"、"success"，默认为"info"

**返回值**：无

**异常**：
- `InterfaceError`: 显示消息失败

#### 提示输入

```python
async def prompt(message: str, default: str = "") -> str
```

**描述**：提示用户输入

**参数**：
- `message` (str): 提示消息
- `default` (str, optional): 默认值，默认为空字符串

**返回值**：
- `str`: 用户输入

**异常**：
- `InterfaceError`: 提示输入失败

#### 确认操作

```python
async def confirm(message: str) -> bool
```

**描述**：确认操作

**参数**：
- `message` (str): 确认消息

**返回值**：
- `bool`: 用户是否确认

**异常**：
- `InterfaceError`: 确认操作失败

#### 选择选项

```python
async def select(message: str, options: list) -> str
```

**描述**：选择选项

**参数**：
- `message` (str): 选择消息
- `options` (list): 选项列表

**返回值**：
- `str`: 选择的选项

**异常**：
- `InterfaceError`: 选择选项失败

### ProgressDisplay

#### 初始化

```python
async def initialize()
```

**描述**：初始化进度显示器

**参数**：无

**返回值**：无

**异常**：
- `ProgressError`: 进度显示器初始化失败

#### 开始进度

```python
async def start_progress(message: str, total: int)
```

**描述**：开始显示进度

**参数**：
- `message` (str): 进度消息
- `total` (int): 总数

**返回值**：无

**异常**：
- `ProgressError`: 开始进度失败

#### 更新进度

```python
async def update_progress(current: int)
```

**描述**：更新进度

**参数**：
- `current` (int): 当前进度

**返回值**：无

**异常**：
- `ProgressError`: 更新进度失败

#### 完成进度

```python
async def finish_progress()
```

**描述**：完成进度显示

**参数**：无

**返回值**：无

**异常**：
- `ProgressError`: 完成进度失败

### ResultFormatter

#### 初始化

```python
async def initialize()
```

**描述**：初始化结果格式化器

**参数**：无

**返回值**：无

**异常**：
- `FormatError`: 结果格式化器初始化失败

#### 格式化结果

```python
async def format_result(result: dict, format_type: str = "text") -> str
```

**描述**：格式化结果

**参数**：
- `result` (dict): 结果数据
- `format_type` (str, optional): 格式类型，可选值为"text"、"json"、"table"，默认为"text"

**返回值**：
- `str`: 格式化后的结果

**异常**：
- `FormatError`: 格式化结果失败
- `ValueError`: 不支持的格式类型

### CLIApplication

#### 初始化

```python
async def initialize()
```

**描述**：初始化CLI应用程序

**参数**：无

**返回值**：无

**异常**：
- `ApplicationError`: CLI应用程序初始化失败

#### 运行应用程序

```python
async def run()
```

**描述**：运行CLI应用程序

**参数**：无

**返回值**：无

**异常**：
- `ApplicationError`: 运行应用程序失败

#### 执行任务

```python
async def _execute_task(task_description: str)
```

**描述**：执行任务（内部方法）

**参数**：
- `task_description` (str): 任务描述

**返回值**：无

**异常**：
- `ApplicationError`: 执行任务失败

#### 列出任务

```python
async def _list_tasks()
```

**描述**：列出任务（内部方法）

**参数**：无

**返回值**：无

**异常**：
- `ApplicationError`: 列出任务失败

#### 显示任务

```python
async def _show_task(task_id: int)
```

**描述**：显示任务详情（内部方法）

**参数**：
- `task_id` (int): 任务ID

**返回值**：无

**异常**：
- `ApplicationError`: 显示任务失败

#### 显示任务结果

```python
async def _show_task_result(task_id: int)
```

**描述**：显示任务结果（内部方法）

**参数**：
- `task_id` (int): 任务ID

**返回值**：无

**异常**：
- `ApplicationError`: 显示任务结果失败

## 信息补充循环API

### InfoRequirementDetector

#### 初始化

```python
async def initialize()
```

**描述**：初始化信息需求检测器

**参数**：无

**返回值**：无

**异常**：
- `DetectionError`: 信息需求检测器初始化失败

#### 检测信息需求

```python
async def detect_info_requirements(task_id: int, sub_task_results: list) -> list
```

**描述**：检测信息需求

**参数**：
- `task_id` (int): 任务ID
- `sub_task_results` (list): 子任务结果列表

**返回值**：
- `list`: 信息需求列表，每个需求包含以下字段：
  - `id` (str): 需求ID
  - `description` (str): 需求描述
  - `priority` (str): 优先级
  - `type` (str): 需求类型

**异常**：
- `DetectionError`: 检测信息需求失败

### UserInputProcessor

#### 初始化

```python
async def initialize()
```

**描述**：初始化用户输入处理器

**参数**：无

**返回值**：无

**异常**：
- `ProcessingError`: 用户输入处理器初始化失败

#### 处理用户输入

```python
async def process_user_input(task_id: int, info_requirements: list) -> list
```

**描述**：处理用户输入

**参数**：
- `task_id` (int): 任务ID
- `info_requirements` (list): 信息需求列表

**返回值**：
- `list`: 用户输入列表，每个输入包含以下字段：
  - `requirement_id` (str): 需求ID
  - `value` (str): 输入值
  - `confidence` (float): 置信度

**异常**：
- `ProcessingError`: 处理用户输入失败

### InfoIntegrationMechanism

#### 初始化

```python
async def initialize()
```

**描述**：初始化信息整合机制

**参数**：无

**返回值**：无

**异常**：
- `IntegrationError`: 信息整合机制初始化失败

#### 整合用户输入

```python
async def integrate_user_input(task_id: int, user_inputs: list) -> dict
```

**描述**：整合用户输入

**参数**：
- `task_id` (int): 任务ID
- `user_inputs` (list): 用户输入列表

**返回值**：
- `dict`: 整合结果，包含以下字段：
  - `task_info` (dict): 任务信息
  - `sub_task_info` (list): 子任务信息列表

**异常**：
- `IntegrationError`: 整合用户输入失败

### LoopControlLogic

#### 初始化

```python
async def initialize()
```

**描述**：初始化循环控制逻辑

**参数**：无

**返回值**：无

**异常**：
- `ControlError`: 循环控制逻辑初始化失败

#### 执行信息收集循环

```python
async def execute_info_gathering_loop(task_id: int, sub_task_results: list) -> dict
```

**描述**：执行信息收集循环

**参数**：
- `task_id` (int): 任务ID
- `sub_task_results` (list): 子任务结果列表

**返回值**：
- `dict`: 循环结果，包含以下字段：
  - `completed` (bool): 是否完成
  - `loop_count` (int): 循环次数
  - `info_requirements` (list): 信息需求列表
  - `user_inputs` (list): 用户输入列表
  - `integrated_info` (dict): 整合信息

**异常**：
- `ControlError`: 执行信息收集循环失败

## LLM验证模块API

### ResultValidator

#### 初始化

```python
async def initialize()
```

**描述**：初始化结果验证器

**参数**：无

**返回值**：无

**异常**：
- `ValidationError`: 结果验证器初始化失败

#### 验证任务结果

```python
async def validate_task_result(task_id: int, task_result: dict) -> dict
```

**描述**：验证任务结果

**参数**：
- `task_id` (int): 任务ID
- `task_result` (dict): 任务结果

**返回值**：
- `dict`: 验证结果，包含以下字段：
  - `is_valid` (bool): 是否有效
  - `overall_score` (float): 总体分数
  - `validation_results` (dict): 各项验证结果
  - `issues` (list): 问题列表
  - `improvement_suggestions` (list): 改进建议

**异常**：
- `ValidationError`: 验证任务结果失败

### ValidationReportGenerator

#### 初始化

```python
async def initialize()
```

**描述**：初始化验证报告生成器

**参数**：无

**返回值**：无

**异常**：
- `ReportError`: 验证报告生成器初始化失败

#### 生成验证报告

```python
async def generate_validation_report(task_id: int, template_type: str = "detailed", format_type: str = "html") -> str
```

**描述**：生成验证报告

**参数**：
- `task_id` (int): 任务ID
- `template_type` (str, optional): 报告模板类型，可选值为"basic"、"detailed"、"summary"、"executive"，默认为"detailed"
- `format_type` (str, optional): 报告格式类型，可选值为"text"、"html"、"markdown"、"json"，默认为"html"

**返回值**：
- `str`: 报告文件路径

**异常**：
- `ReportError`: 生成验证报告失败
- `ValueError`: 不支持的模板类型或格式类型

### UserConfirmationManager

#### 初始化

```python
async def initialize()
```

**描述**：初始化用户确认管理器

**参数**：无

**返回值**：无

**异常**：
- `ConfirmationError`: 用户确认管理器初始化失败

#### 请求确认

```python
async def request_confirmation(task_id: int, confirmation_type: str, data: dict, message: str = None) -> dict
```

**描述**：请求用户确认

**参数**：
- `task_id` (int): 任务ID
- `confirmation_type` (str): 确认类型，可选值为"task_result"、"validation_report"、"improvement_suggestion"、"task_retry"、"task_stop"
- `data` (dict): 确认数据
- `message` (str, optional): 确认消息，默认为None

**返回值**：
- `dict`: 确认结果，包含以下字段：
  - `confirmed` (bool): 是否确认
  - `rejected` (bool): 是否拒绝
  - `timeout` (bool): 是否超时
  - `reason` (str): 理由
  - `user_input` (dict): 用户输入

**异常**：
- `ConfirmationError`: 请求确认失败
- `ValueError`: 不支持的确认类型