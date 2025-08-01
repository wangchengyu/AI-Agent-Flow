# 智能Agent任务管理系统 - 开发指南

## 目录

1. [开发环境设置](#开发环境设置)
2. [代码结构](#代码结构)
3. [开发规范](#开发规范)
4. [模块开发](#模块开发)
5. [测试指南](#测试指南)
6. [调试指南](#调试指南)
7. [性能优化](#性能优化)
8. [部署指南](#部署指南)
9. [贡献指南](#贡献指南)

## 开发环境设置

### 系统要求

- Python 3.8 或更高版本
- Git
- SQLite 3
- 文本编辑器或IDE（推荐VS Code）

### 安装步骤

1. **克隆仓库**：
   ```bash
   git clone https://github.com/your-organization/agent-task-management-system.git
   cd agent-task-management-system
   ```

2. **创建虚拟环境**：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate  # Windows
   ```

3. **安装开发依赖**：
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # 开发依赖
   ```

4. **安装预提交钩子**：
   ```bash
   pre-commit install
   ```

5. **配置环境变量**：
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，设置必要的环境变量
   ```

6. **初始化数据库**：
   ```bash
   python -m src.cli initialize
   ```

### IDE配置

#### VS Code配置

推荐使用VS Code进行开发，安装以下扩展：

- Python
- Pylance
- Black Formatter
- isort
- GitLens
- SQLite

#### 配置文件

在 `.vscode/settings.json` 中添加以下配置：

```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "python.sortImports.args": ["--profile", "black"],
    "files.associations": {
        "*.html": "jinja-html"
    }
}
```

## 代码结构

### 项目结构

```
agent-task-management-system/
├── src/                          # 源代码目录
│   ├── __init__.py
│   ├── cli/                      # 命令行交互模块
│   │   ├── __init__.py
│   │   ├── cli_parser.py        # CLI参数解析器
│   │   ├── interactive_interface.py  # 交互式界面
│   │   ├── progress_display.py   # 进度显示器
│   │   ├── result_formatter.py   # 结果格式化器
│   │   └── cli_application.py    # CLI应用程序
│   ├── agent/                    # Agent流程管理模块
│   │   ├── __init__.py
│   │   ├── agent_manager.py     # Agent管理器
│   │   ├── task_decomposer.py   # 任务分解器
│   │   ├── sub_task_manager.py  # 子任务管理器
│   │   ├── info_gathering_loop.py  # 信息收集循环
│   │   └── validation_module.py # 验证模块
│   ├── database/                 # 数据库管理模块
│   │   ├── __init__.py
│   │   ├── database_manager.py  # 数据库管理器
│   │   ├── task_history_manager.py  # 任务历史管理器
│   │   ├── config_manager.py    # 配置管理器
│   │   ├── user_manager.py      # 用户管理器
│   │   ├── knowledge_source_manager.py  # 知识源管理器
│   │   ├── tool_log_manager.py  # 工具日志管理器
│   │   └── backup_manager.py    # 备份管理器
│   ├── rag/                      # RAG知识管理模块
│   │   ├── __init__.py
│   │   ├── document_processor.py  # 文档处理器
│   │   ├── vector_embedder.py   # 向量嵌入器
│   │   ├── vector_database.py   # 向量数据库
│   │   ├── retriever.py         # 检索器
│   │   ├── reranker.py         # 重排序器
│   │   └── knowledge_manager.py # 知识管理器
│   ├── mcp_tools/               # MCP工具管理模块
│   │   ├── __init__.py
│   │   ├── mcp_server.py        # MCP服务器
│   │   ├── mcp_client.py        # MCP客户端
│   │   ├── tool_manager.py      # 工具管理器
│   │   ├── permission_manager.py  # 权限管理器
│   │   ├── file_tool.py         # 文件操作工具
│   │   ├── code_tool.py         # 代码生成工具
│   │   ├── uml_tool.py          # UML生成工具
│   │   └── db_tool.py           # 数据库操作工具
│   ├── validation/              # LLM验证模块
│   │   ├── __init__.py
│   │   ├── result_validator.py # 结果验证器
│   │   ├── validation_report_generator.py  # 验证报告生成器
│   │   └── user_confirmation_manager.py  # 用户确认管理器
│   ├── info_gathering/         # 信息补充循环
│   │   ├── __init__.py
│   │   ├── info_requirement_detector.py  # 信息需求检测器
│   │   ├── user_input_processor.py  # 用户输入处理器
│   │   ├── info_integration_mechanism.py  # 信息整合机制
│   │   └── loop_control_logic.py  # 循环控制逻辑
│   ├── config/                  # 配置模块
│   │   ├── __init__.py
│   │   ├── settings.py          # 系统设置
│   │   └── config_manager.py    # 配置管理器
│   └── utils/                   # 工具模块
│       ├── __init__.py
│       ├── exceptions.py       # 异常定义
│       ├── logger.py           # 日志工具
│       └── helpers.py          # 辅助函数
├── tests/                       # 测试目录
│   ├── __init__.py
│   ├── test_cli/
│   ├── test_agent/
│   ├── test_database/
│   ├── test_rag/
│   ├── test_mcp_tools/
│   ├── test_validation/
│   ├── test_info_gathering/
│   └── test_utils/
├── docs/                        # 文档目录
│   ├── design/                  # 设计文档
│   ├── api/                     # API文档
│   ├── user/                    # 用户文档
│   └── developer/               # 开发文档
├── diagrams/                    # 图表目录
├── logs/                        # 日志目录
├── data/                        # 数据目录
│   ├── db/                      # 数据库文件
│   └── knowledge/               # 知识库文件
├── requirements.txt             # 依赖列表
├── requirements-dev.txt         # 开发依赖列表
├── setup.py                     # 安装脚本
├── .env.example                 # 环境变量示例
├── .gitignore                   # Git忽略文件
├── .pre-commit-config.yaml      # 预提交钩子配置
└── README.md                    # 项目说明
```

### 模块职责

#### CLI模块
- 负责命令行界面和用户交互
- 解析命令行参数
- 显示进度和结果
- 处理用户输入

#### Agent模块
- 负责任务的整体执行流程
- 协调各个模块的工作
- 管理任务和子任务的状态

#### 数据库模块
- 负责数据的存储和检索
- 提供统一的数据库访问接口
- 管理任务历史、用户信息等

#### RAG模块
- 负责知识库的管理和检索
- 处理文档和生成向量表示
- 提供知识检索和重排序功能

#### MCP工具模块
- 负责工具的注册和管理
- 通过MCP协议与外部工具服务器通信
- 管理工具权限和调用日志

#### 验证模块
- 负责验证任务结果的质量
- 生成验证报告
- 管理用户确认

#### 信息补充循环模块
- 负责在任务执行过程中收集额外信息
- 检测信息需求
- 整合用户输入

## 开发规范

### 代码风格

- 遵循PEP 8 Python代码风格指南
- 使用Black进行代码格式化
- 使用isort进行导入排序
- 使用Pylint进行代码检查

### 命名规范

- 类名使用PascalCase，如 `AgentManager`
- 函数和方法名使用snake_case，如 `execute_task`
- 变量名使用snake_case，如 `task_id`
- 常量名使用UPPER_SNAKE_CASE，如 `MAX_RETRIES`
- 私有方法和变量使用下划线前缀，如 `_private_method`

### 注释规范

- 使用docstring描述类、方法和函数
- 注释应解释为什么，而不是是什么
- 使用类型注解提高代码可读性

#### 类docstring示例

```python
class AgentManager:
    """Agent管理器，负责任务的整体执行流程。
    
    负责协调各个模块的工作，管理任务和子任务的状态，
    确保任务能够高效、准确地完成。
    
    Attributes:
        db_manager: 数据库管理器
        knowledge_manager: 知识管理器
        tool_manager: 工具管理器
    """
```

#### 方法docstring示例

```python
async def execute_task(self, task_data: dict) -> dict:
    """执行任务。
    
    创建任务记录，分解任务为子任务，执行子任务，
    并在必要时收集额外信息，最后验证结果。
    
    Args:
        task_data: 任务数据，包含任务名称、描述等
        
    Returns:
        任务结果，包含任务ID、结果内容等
        
    Raises:
        AgentError: 执行任务失败
        ValidationError: 任务数据验证失败
    """
```

### 错误处理

- 使用自定义异常类
- 异常类应继承自适当的基类
- 提供有意义的错误消息

#### 自定义异常示例

```python
class AgentError(Exception):
    """Agent相关错误的基类。"""
    
    pass


class TaskExecutionError(AgentError):
    """任务执行错误。"""
    
    pass
```

#### 异常处理示例

```python
try:
    result = await self.execute_task(task_data)
except TaskExecutionError as e:
    self.logger.error(f"任务执行失败: {str(e)}")
    raise
```

### 日志记录

- 使用logging模块进行日志记录
- 为每个模块创建单独的logger
- 使用适当的日志级别

#### 日志记录示例

```python
import logging

logger = logging.getLogger(__name__)

class AgentManager:
    async def execute_task(self, task_data: dict) -> dict:
        logger.info(f"开始执行任务: {task_data.get('name')}")
        try:
            # 执行任务
            result = await self._execute_task_flow(task_data)
            logger.info(f"任务执行完成: {task_data.get('name')}")
            return result
        except Exception as e:
            logger.error(f"任务执行失败: {task_data.get('name')}, 错误: {str(e)}")
            raise
```

### 异步编程

- 使用async/await进行异步编程
- 避免阻塞操作
- 使用asyncio.gather并行执行独立操作

#### 异步编程示例

```python
async def execute_sub_tasks(self, sub_tasks: list) -> list:
    """并行执行子任务。"""
    tasks = [self.execute_sub_task(sub_task) for sub_task in sub_tasks]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理结果和异常
    processed_results = []
    for result in results:
        if isinstance(result, Exception):
            self.logger.error(f"子任务执行失败: {str(result)}")
            processed_results.append({"status": "failed", "error": str(result)})
        else:
            processed_results.append(result)
    
    return processed_results
```

## 模块开发

### 添加新模块

1. **创建模块目录**：
   ```bash
   mkdir src/new_module
   touch src/new_module/__init__.py
   ```

2. **实现模块类**：
   ```python
   # src/new_module/module_manager.py
   import logging
    from typing import Any, Dict, List, Optional
    
    logger = logging.getLogger(__name__)
    
    class ModuleManager:
        """模块管理器。"""
        
        def __init__(self, db_manager, config_manager):
            """初始化模块管理器。"""
            self.db_manager = db_manager
            self.config_manager = config_manager
            
        async def initialize(self):
            """初始化模块管理器。"""
            logger.info("模块管理器初始化完成")
            
        async def execute_module_function(self, params: Dict[str, Any]) -> Dict[str, Any]:
            """执行模块功能。"""
            logger.info(f"执行模块功能，参数: {params}")
            # 实现功能逻辑
            result = {"status": "success", "data": {}}
            return result
   ```

3. **注册模块**：
   ```python
   # src/agent/agent_manager.py
   from src.new_module.module_manager import ModuleManager
    
   class AgentManager:
        async def initialize(self):
            # 初始化其他模块
            self.module_manager = ModuleManager(self.db_manager, self.config_manager)
            await self.module_manager.initialize()
   ```

### 添加新工具

1. **实现工具类**：
   ```python
   # src/mcp_tools/new_tool.py
   import logging
    from typing import Any, Dict
    
    logger = logging.getLogger(__name__)
    
    class NewTool:
        """新工具。"""
        
        def __init__(self):
            """初始化新工具。"""
            pass
            
        async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
            """执行工具。"""
            logger.info(f"执行新工具，参数: {parameters}")
            # 实现工具逻辑
            result = {"status": "success", "data": {}}
            return result
   ```

2. **注册工具**：
   ```python
   # src/mcp_tools/tool_manager.py
   from src.mcp_tools.new_tool import NewTool
    
   class ToolManager:
        async def initialize(self):
            # 初始化其他工具
            self.new_tool = NewTool()
            # 注册工具到MCP服务器
            await self.mcp_server.register_tool("new_tool", self.new_tool.execute)
   ```

### 添加新验证指标

1. **扩展验证器**：
   ```python
   # src/validation/result_validator.py
   class ResultValidator:
        async def _validate_new_metric(self, task_id: int, task_result: dict, task: dict) -> dict:
            """验证新指标。"""
            logger.info(f"验证新指标，任务ID: {task_id}")
            # 实现验证逻辑
            score = 0.8  # 计算分数
            issues = []  # 识别问题
            return {"score": score, "issues": issues}
            
        async def validate_task_result(self, task_id: int, task_result: dict) -> dict:
            # 其他验证逻辑
            new_metric_result = await self._validate_new_metric(task_id, task_result, task)
            # 整合验证结果
   ```

2. **更新配置**：
   ```python
   # src/config/settings.py
   VALIDATION_METRICS = {
        "completeness": {"weight": 0.3, "threshold": 0.7},
        "accuracy": {"weight": 0.3, "threshold": 0.7},
        "relevance": {"weight": 0.2, "threshold": 0.7},
        "clarity": {"weight": 0.1, "threshold": 0.7},
        "timeliness": {"weight": 0.1, "threshold": 0.7},
        "new_metric": {"weight": 0.1, "threshold": 0.7},  # 新指标
    }
   ```

## 测试指南

### 测试框架

- 使用pytest作为测试框架
- 使用pytest-asyncio进行异步测试
- 使用pytest-cov进行代码覆盖率测试
- 使用pytest-mock进行模拟测试

### 测试结构

```
tests/
├── __init__.py
├── conftest.py                 # 测试配置
├── test_cli/
│   ├── __init__.py
│   ├── test_cli_parser.py
│   ├── test_interactive_interface.py
│   └── ...
├── test_agent/
│   ├── __init__.py
│   ├── test_agent_manager.py
│   ├── test_task_decomposer.py
│   └── ...
├── test_database/
│   ├── __init__.py
│   ├── test_database_manager.py
│   ├── test_task_history_manager.py
│   └── ...
└── ...
```

### 测试示例

#### 单元测试示例

```python
# tests/test_agent/test_agent_manager.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.agent.agent_manager import AgentManager
from src.database.database_manager import DatabaseManager
from src.rag.knowledge_manager import KnowledgeManager
from src.mcp_tools.tool_manager import ToolManager


@pytest.fixture
async def agent_manager():
    """创建Agent管理器测试实例。"""
    db_manager = MagicMock(spec=DatabaseManager)
    knowledge_manager = MagicMock(spec=KnowledgeManager)
    tool_manager = MagicMock(spec=ToolManager)
    
    agent_manager = AgentManager(db_manager, knowledge_manager, tool_manager)
    await agent_manager.initialize()
    
    return agent_manager


@pytest.mark.asyncio
async def test_execute_task(agent_manager):
    """测试执行任务。"""
    # 设置模拟
    agent_manager.task_decomposer.decompose_task = AsyncMock(return_value=[])
    agent_manager.sub_task_manager.execute_sub_tasks = AsyncMock(return_value=[])
    agent_manager.info_gathering_loop.execute_info_gathering_loop = AsyncMock(return_value={})
    agent_manager.validation_module.validate_task_result = AsyncMock(return_value={"is_valid": True})
    
    # 执行测试
    task_data = {"task_name": "测试任务", "description": "这是一个测试任务"}
    result = await agent_manager.execute_task(task_data)
    
    # 验证结果
    assert "task_id" in result
    assert result["status"] == "completed"
```

#### 集成测试示例

```python
# tests/test_integration/test_task_execution.py
import pytest
import asyncio
from src.cli.cli_application import CLIApplication


@pytest.fixture
async def cli_app():
    """创建CLI应用程序测试实例。"""
    app = CLIApplication()
    await app.initialize()
    return app


@pytest.mark.asyncio
async def test_task_execution_flow(cli_app):
    """测试任务执行流程。"""
    # 执行任务
    task_data = {"task_name": "集成测试任务", "description": "这是一个集成测试任务"}
    result = await cli_app.agent_manager.execute_task(task_data)
    
    # 验证任务创建
    assert "task_id" in result
    task_id = result["task_id"]
    
    # 验证任务状态
    task = await cli_app.task_history_manager.get_task(task_id)
    assert task["status"] == "completed"
    
    # 验证任务结果
    task_result = await cli_app.task_history_manager.get_task_result(task_id)
    assert task_result is not None
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定模块的测试
pytest tests/test_agent/

# 运行特定测试文件
pytest tests/test_agent/test_agent_manager.py

# 运行特定测试函数
pytest tests/test_agent/test_agent_manager.py::test_execute_task

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 测试覆盖率

目标是达到80%以上的代码覆盖率。使用以下命令查看覆盖率报告：

```bash
pytest --cov=src --cov-report=term-missing
```

## 调试指南

### 日志配置

系统使用logging模块进行日志记录，您可以通过配置文件调整日志级别和输出格式。

#### 日志级别

- DEBUG：详细的调试信息
- INFO：一般信息
- WARNING：警告信息
- ERROR：错误信息
- CRITICAL：严重错误信息

#### 日志配置示例

```python
# src/config/settings.py
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
        },
        "file": {
            "level": "DEBUG",
            "formatter": "standard",
            "class": "logging.FileHandler",
            "filename": "logs/app.log",
            "mode": "a",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default", "file"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}
```

### 调试工具

#### VS Code调试

1. 创建调试配置文件 `.vscode/launch.json`：

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": false
        },
        {
            "name": "Python: CLI Application",
            "type": "python",
            "request": "launch",
            "module": "src.cli",
            "console": "integratedTerminal",
            "justMyCode": false,
            "args": ["execute", "--description", "调试任务"]
        }
    ]
}
```

2. 设置断点并启动调试：

   - 在代码行号左侧单击设置断点
   - 按F5启动调试
   - 使用调试工具栏控制执行流程

#### pdb调试

Python内置的pdb调试器可以在代码中插入断点：

```python
import pdb

async def execute_task(self, task_data: dict) -> dict:
    # 执行任务
    pdb.set_trace()  # 插入断点
    result = await self._execute_task_flow(task_data)
    return result
```

### 常见问题调试

#### 任务执行失败

1. 检查任务数据是否正确：
   ```python
   logger.debug(f"任务数据: {task_data}")
   ```

2. 检查任务分解是否正确：
   ```python
   sub_tasks = await self.task_decomposer.decompose_task(task_id, task_description)
   logger.debug(f"子任务: {sub_tasks}")
   ```

3. 检查子任务执行是否正确：
   ```python
   for sub_task in sub_tasks:
       result = await self.sub_task_manager.execute_sub_task(sub_task["id"])
       logger.debug(f"子任务结果: {result}")
   ```

#### 数据库操作失败

1. 检查SQL语句是否正确：
   ```python
   logger.debug(f"SQL语句: {query}")
   logger.debug(f"SQL参数: {params}")
   ```

2. 检查数据库连接是否正常：
   ```python
   try:
       conn = self.db_manager.get_connection()
       cursor = conn.cursor()
       cursor.execute(query, params)
       result = cursor.fetchall()
   except Exception as e:
       logger.error(f"数据库操作失败: {str(e)}")
       raise
   ```

#### 工具调用失败

1. 检查工具参数是否正确：
   ```python
   logger.debug(f"工具参数: {parameters}")
   ```

2. 检查工具权限是否足够：
   ```python
   has_permission = await self.permission_manager.check_permission(user_id, tool_name)
   logger.debug(f"工具权限: {has_permission}")
   ```

3. 检查MCP服务器连接是否正常：
   ```python
   try:
       result = await self.mcp_client.call_tool(tool_name, parameters)
   except Exception as e:
       logger.error(f"工具调用失败: {str(e)}")
       raise
   ```

## 性能优化

### 数据库优化

#### 索引优化

为经常查询的字段添加索引：

```python
# src/database/database_manager.py
async def initialize(self):
    """初始化数据库表结构。"""
    # 创建表
    await self.execute_update("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            task_name TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            user_id INTEGER
        )
    """)
    
    # 创建索引
    await self.execute_update("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status)")
    await self.execute_update("CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks (user_id)")
    await self.execute_update("CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks (created_at)")
```

#### 查询优化

使用EXPLAIN分析查询计划：

```python
async def get_tasks_by_status(self, status: str) -> list:
    """根据状态获取任务列表。"""
    query = "EXPLAIN QUERY PLAN SELECT * FROM tasks WHERE status = ?"
    plan = await self.execute_query(query, (status,))
    logger.debug(f"查询计划: {plan}")
    
    query = "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC"
    tasks = await self.execute_query(query, (status,))
    return tasks
```

### 向量数据库优化

#### 批量处理

使用批量处理提高向量嵌入和检索效率：

```python
# src/rag/vector_embedder.py
async def embed_batch(self, texts: list) -> list:
    """批量嵌入文本。"""
    logger.info(f"批量嵌入 {len(texts)} 个文本")
    
    # 分批处理
    batch_size = 100
    embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = await self._embed_batch_internal(batch)
        embeddings.extend(batch_embeddings)
    
    logger.info(f"批量嵌入完成，共 {len(embeddings)} 个向量")
    return embeddings
```

#### 缓存机制

使用缓存减少重复计算：

```python
# src/rag/retriever.py
from functools import lru_cache

class Retriever:
    @lru_cache(maxsize=1000)
    async def _retrieve_by_embedding(self, query_embedding: tuple, limit: int) -> list:
        """通过嵌入检索文档（带缓存）。"""
        query_embedding = list(query_embedding)  # 转换为列表
        documents = await self.vector_database.search(query_embedding, limit)
        return documents
```

### 异步优化

#### 并行执行

使用asyncio.gather并行执行独立操作：

```python
# src/agent/sub_task_manager.py
async def execute_sub_tasks(self, sub_tasks: list) -> list:
    """并行执行子任务。"""
    logger.info(f"并行执行 {len(sub_tasks)} 个子任务")
    
    # 创建任务列表
    tasks = [self.execute_sub_task(sub_task["id"]) for sub_task in sub_tasks]
    
    # 并行执行
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理结果
    processed_results = []
    for i, result in enumerate(results):
        sub_task_id = sub_tasks[i]["id"]
        if isinstance(result, Exception):
            logger.error(f"子任务 {sub_task_id} 执行失败: {str(result)}")
            processed_results.append({
                "sub_task_id": sub_task_id,
                "status": "failed",
                "error": str(result)
            })
        else:
            processed_results.append(result)
    
    logger.info(f"子任务执行完成，成功 {len([r for r in processed_results if r['status'] == 'completed'])} 个")
    return processed_results
```

#### 限制并发数

使用信号量限制并发数：

```python
# src/agent/sub_task_manager.py
import asyncio

class SubTaskManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.semaphore = asyncio.Semaphore(10)  # 限制并发数为10
        
    async def execute_sub_task(self, sub_task_id: int) -> dict:
        """执行子任务（带并发限制）。"""
        async with self.semaphore:
            logger.info(f"开始执行子任务 {sub_task_id}")
            try:
                # 执行子任务
                result = await self._execute_sub_task_flow(sub_task_id)
                logger.info(f"子任务 {sub_task_id} 执行完成")
                return result
            except Exception as e:
                logger.error(f"子任务 {sub_task_id} 执行失败: {str(e)}")
                raise
```

### 内存优化

#### 流式处理

使用流式处理处理大文件：

```python
# src/rag/document_processor.py
async def process_large_document(self, file_path: str, chunk_size: int = 1024) -> dict:
    """处理大文档（流式处理）。"""
    logger.info(f"开始处理大文档: {file_path}")
    
    # 提取元数据
    metadata = await self._extract_metadata(file_path)
    
    # 流式提取文本
    text_chunks = []
    with open(file_path, 'r', encoding='utf-8') as file:
        buffer = ""
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            buffer += chunk
            
            # 按段落分割
            paragraphs = buffer.split('\n\n')
            buffer = paragraphs.pop()  # 保留最后一个不完整的段落
            
            for paragraph in paragraphs:
                if paragraph.strip():
                    text_chunks.append(paragraph)
    
    # 处理剩余的缓冲区
    if buffer.strip():
        text_chunks.append(buffer)
    
    logger.info(f"文档处理完成，共 {len(text_chunks)} 个文本块")
    return {
        "text": "\n\n".join(text_chunks),
        "metadata": metadata,
        "chunks": text_chunks
    }
```

#### 对象复用

使用对象池减少对象创建和销毁：

```python
# src/mcp_tools/mcp_client.py
class MCPClientPool:
    """MCP客户端连接池。"""
    
    def __init__(self, server_url: str, api_key: str, max_size: int = 10):
        self.server_url = server_url
        self.api_key = api_key
        self.max_size = max_size
        self._pool = asyncio.Queue(maxsize=max_size)
        self._current_size = 0
        
    async def get_client(self) -> MCPClient:
        """获取MCP客户端。"""
        if self._pool.empty() and self._current_size < self.max_size:
            # 创建新客户端
            client = MCPClient(self.server_url, self.api_key)
            await client.initialize()
            self._current_size += 1
            return client
        else:
            # 从池中获取客户端
            return await self._pool.get()
            
    async def return_client(self, client: MCPClient):
        """返回MCP客户端到池中。"""
        try:
            # 检查客户端是否仍然有效
            await client.list_tools()
            await self._pool.put(client)
        except Exception:
            # 客户端无效，创建新客户端替换
            self._current_size -= 1
```

## 部署指南

### 打包应用

#### 使用PyInstaller打包

1. 安装PyInstaller：
   ```bash
   pip install pyinstaller
   ```

2. 创建打包脚本 `build.py`：
   ```python
   import PyInstaller.__main__
   import os
   
   # 获取项目根目录
   root_dir = os.path.dirname(os.path.abspath(__file__))
   
   # 设置打包参数
   PyInstaller.__main__.run([
       'src/cli/__main__.py',  # 入口文件
       '--name=agent-task-management-system',  # 应用名称
       '--onefile',  # 打包为单个文件
       '--windowed',  # 无控制台窗口（GUI应用）
       '--add-data=src/config:src/config',  # 添加配置文件
       '--add-data=src/utils:src/utils',  # 添加工具文件
       '--hidden-import=sqlite3',  # 隐藏导入
       '--hidden-import=aiohttp',  # 隐藏导入
       '--hidden-import=asyncio',  # 隐藏导入
       '--icon=assets/icon.ico',  # 应用图标
       '--distpath=dist',  # 输出目录
       '--workpath=build',  # 工作目录
       '--specpath=build',  # 规范文件目录
   ])
   ```

3. 运行打包脚本：
   ```bash
   python build.py
   ```

4. 打包后的应用将位于 `dist` 目录中。

#### 使用Docker打包

1. 创建Dockerfile：

```dockerfile
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src/
COPY data/ ./data/
COPY logs/ ./logs/

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 设置环境变量
ENV PYTHONPATH=/app/src
ENV DATABASE_PATH=/app/data/db.sqlite
ENV KNOWLEDGE_BASE_PATH=/app/data/knowledge

# 暴露端口（如果需要）
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "src.cli"]
```

2. 构建Docker镜像：
   ```bash
   docker build -t agent-task-management-system .
   ```

3. 运行Docker容器：
   ```bash
   docker run -it --rm -v $(pwd)/data:/app/data -v $(pwd)/logs:/app/logs agent-task-management-system
   ```

### 部署到服务器

#### 使用systemd部署

1. 创建服务文件 `/etc/systemd/system/agent-task-management-system.service`：

```ini
[Unit]
Description=Agent Task Management System
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/agent-task-management-system
Environment=PYTHONPATH=/opt/agent-task-management-system/src
Environment=DATABASE_PATH=/opt/agent-task-management-system/data/db.sqlite
Environment=KNOWLEDGE_BASE_PATH=/opt/agent-task-management-system/data/knowledge
ExecStart=/opt/agent-task-management-system/venv/bin/python -m src.cli
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

2. 启用并启动服务：
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable agent-task-management-system
   sudo systemctl start agent-task-management-system
   ```

3. 查看服务状态：
   ```bash
   sudo systemctl status agent-task-management-system
   ```

#### 使用Docker Compose部署

1. 创建docker-compose.yml文件：

```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: agent-task-management-system
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - PYTHONPATH=/app/src
      - DATABASE_PATH=/app/data/db.sqlite
      - KNOWLEDGE_BASE_PATH=/app/data/knowledge
    restart: unless-stopped
```

2. 启动服务：
   ```bash
   docker-compose up -d
   ```

3. 查看日志：
   ```bash
   docker-compose logs -f app
   ```

### 配置管理

#### 环境变量配置

创建 `.env` 文件：

```ini
# 数据库配置
DATABASE_PATH=/opt/agent-task-management-system/data/db.sqlite

# 知识库配置
KNOWLEDGE_BASE_PATH=/opt/agent-task-management-system/data/knowledge

# LLM配置
LLM_MODEL_NAME=openai/gpt-4
LLM_API_KEY=your-api-key

# MCP服务器配置
MCP_SERVER_URL=https://api.example.com
MCP_API_KEY=your-api-key

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/opt/agent-task-management-system/logs/app.log
```

#### 配置文件覆盖

系统支持通过环境变量覆盖配置文件中的设置，优先级从高到低为：

1. 环境变量
2. 用户配置文件 (~/.agent-task-management-system/config.yaml)
3. 系统配置文件 (/etc/agent-task-management-system/config.yaml)
4. 默认配置文件 (src/config/settings.py)

### 数据备份与恢复

#### 备份脚本

创建备份脚本 `backup.sh`：

```bash
#!/bin/bash

# 设置变量
APP_DIR="/opt/agent-task-management-system"
BACKUP_DIR="/opt/agent-task-management-system/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.tar.gz"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 停止服务
systemctl stop agent-task-management-system

# 创建备份
tar -czf "$BACKUP_FILE" -C "$APP_DIR" data logs

# 启动服务
systemctl start agent-task-management-system

# 保留最近7天的备份
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +7 -delete

echo "备份完成: $BACKUP_FILE"
```

#### 恢复脚本

创建恢复脚本 `restore.sh`：

```bash
#!/bin/bash

# 设置变量
APP_DIR="/opt/agent-task-management-system"
BACKUP_FILE="$1"

# 检查备份文件是否存在
if [ ! -f "$BACKUP_FILE" ]; then
    echo "备份文件不存在: $BACKUP_FILE"
    exit 1
fi

# 停止服务
systemctl stop agent-task-management-system

# 备份当前数据
cp -r "$APP_DIR/data" "$APP_DIR/data_backup_$(date +%Y%m%d_%H%M%S)"
cp -r "$APP_DIR/logs" "$APP_DIR/logs_backup_$(date +%Y%m%d_%H%M%S)"

# 恢复数据
tar -xzf "$BACKUP_FILE" -C "$APP_DIR"

# 启动服务
systemctl start agent-task-management-system

echo "恢复完成: $BACKUP_FILE"
```

#### 定时备份

设置定时任务：

```bash
# 编辑crontab
crontab -e

# 添加以下行，每天凌晨2点备份
0 2 * * * /opt/agent-task-management-system/backup.sh
```

## 贡献指南

### 代码贡献流程

1. **Fork仓库**：
   - 在GitHub上fork项目仓库

2. **克隆本地副本**：
   ```bash
   git clone https://github.com/your-username/agent-task-management-system.git
   cd agent-task-management-system
   ```

3. **创建功能分支**：
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **开发代码**：
   - 遵循开发规范
   - 编写测试
   - 确保代码通过所有测试

5. **提交更改**：
   ```bash
   git add .
   git commit -m "Add your feature description"
   ```

6. **推送分支**：
   ```bash
   git push origin feature/your-feature-name
   ```

7. **创建Pull Request**：
   - 在GitHub上创建Pull Request
   - 描述更改内容和原因
   - 链接相关的问题

### 代码审查

代码审查是确保代码质量的重要环节，请遵循以下准则：

1. **自我审查**：
   - 确保代码符合开发规范
   - 运行所有测试并确保通过
   - 检查代码逻辑和性能

2. **审查他人代码**：
   - 提供建设性的反馈
   - 关注代码质量、安全性和性能
   - 尊重他人的工作

3. **处理审查意见**：
   - 认真考虑所有反馈
   - 及时回应和修改
   - 感谢审查者的贡献

### 文档贡献

文档是项目的重要组成部分，请遵循以下准则：

1. **更新文档**：
   - 添加新功能时更新相关文档
   - 修复文档中的错误
   - 改进文档的清晰度和完整性

2. **文档格式**：
   - 使用Markdown格式
   - 遵循现有的文档结构
   - 提供清晰的示例和说明

3. **文档提交**：
   - 将文档更改与代码更改一起提交
   - 在提交消息中说明文档更改

### 问题报告

如果您发现bug或有功能请求，请按照以下步骤报告：

1. **检查现有问题**：
   - 在GitHub Issues中搜索类似问题
   - 确保问题尚未被报告

2. **创建新问题**：
   - 使用清晰和描述性的标题
   - 提供详细的问题描述
   - 包含复现步骤和预期结果
   - 提供相关日志和错误信息

3. **分类问题**：
   - 使用适当的标签（bug、enhancement、question等）
   - 分配到正确的里程碑

### 社区准则

我们致力于维护一个友好、包容和专业的社区环境：

1. **尊重他人**：
   - 尊重不同的观点和背景
   - 使用礼貌和专业的语言
   - 避免人身攻击和歧视性言论

2. **建设性参与**：
   - 提供建设性的反馈
   - 关注问题而非个人
   - 寻求共识和解决方案

3. **遵守规则**：
   - 遵守项目的行为准则
   - 尊重维护者的决定
   - 报告不当行为

### 发布流程

项目遵循语义化版本控制（SemVer），发布流程如下：

1. **准备发布**：
   - 更新版本号
   - 更新CHANGELOG.md
   - 创建发布分支

2. **测试发布**：
   - 在测试环境中进行全面测试
   - 修复发现的问题

3. **创建发布**：
   - 合并发布分支到主分支
   - 创建发布标签
   - 构建和发布包

4. **发布公告**：
   - 在GitHub上发布公告
   - 更新文档和网站
   - 通知用户和社区

### 联系方式

如果您有任何问题或建议，可以通过以下方式联系我们：

- GitHub Issues：https://github.com/your-organization/agent-task-management-system/issues
- 邮箱：support@example.com
- 社区论坛：https://community.example.com

感谢您对智能Agent任务管理系统的贡献！