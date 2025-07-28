# 详细设计文档

## 1. 系统模块说明

### 1.1 配置管理模块
- **功能**: 负责加载和管理OpenAI API配置
- **核心类**: `config.py`中的`load_config`函数
- **输入**: `config.json`配置文件
- **输出**: 配置参数字典
- **异常处理**: 
  - 文件不存在异常
  - JSON格式错误异常

### 1.2 Agent管理模块
- **功能**: 基于CrewAI创建和管理Agent、任务、团队
- **核心类**: `AgentManager`
- **主要方法**:
  - `create_agent()`: 创建新Agent
  - `create_task()`: 创建新任务
  - `create_crew()`: 创建团队
  - `run_crew()`: 运行团队
- **数据结构**:
  - `agents`: 存储Agent实例的字典
  - `tasks`: 存储任务实例的字典

### 1.3 MCP工具管理模块
- **功能**: 管理MCP工具的注册和调用
- **核心类**: 
  - `MCPService`: MCP服务管理
  - `MCPManager`: 工具注册管理
  - `FileManager`: 文件管理工具
- **交互流程**:
  1. 初始化MCP服务
  2. 注册工具
  3. 启动MCP服务

### 1.4 大模型交互模块
- **功能**: 与大模型交互并记录日志
- **核心类**: `LLMClient`
- **主要方法**: `send_request()`
- **日志记录**:
  - 请求时间
  - 请求内容
  - 上下文信息
  - 响应内容

### 1.5 本地数据管理模块
- **功能**: 使用SQLite3管理本地数据
- **核心类**: `Database`
- **数据表**:
  - `tasks`: 任务表
  - `agents`: Agent表
- **主要操作**:
  - 数据库连接
  - 表创建
  - 数据持久化

### 1.6 命令行交互模块
- **功能**: 提供CLI接口
- **核心类**: `CLI`
- **支持命令**:
  - `agent create`: 创建Agent
  - `task create`: 创建任务
  - `file list/read`: 文件管理
  - `llm`: 大模型交互

## 2. 系统交互流程

### 2.1 主流程
1. 用户通过CLI提交需求
2. Agent管理模块分解任务
3. 大模型交互模块处理任务
4. 根据需要调用MCP工具
5. 结果验证和反馈
6. 最终交付

### 2.2 子任务执行流程
1. 大模型推理是否需要额外信息
2. 如果需要:
   - 请求用户批准
   - 获取额外信息
   - 更新任务需求
3. 执行工具操作或生成内容
4. 结果验证

## 3. 数据结构设计

### 3.1 配置数据结构
```json
{
  "openai": {
    "api_key": "your-api-key-here",
    "base_url": "https://api.openai.com/v1",
    "model_name": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

### 3.2 数据库表结构

#### tasks表
| 列名         | 类型         | 说明           |
|--------------|--------------|----------------|
| id           | INTEGER      | 主键           |
| task_id      | TEXT         | 任务ID         |
| description  | TEXT         | 任务描述       |
| status       | TEXT         | 任务状态       |
| created_at   | TIMESTAMP    | 创建时间       |
| updated_at   | TIMESTAMP    | 更新时间       |

#### agents表
| 列名         | 类型         | 说明           |
|--------------|--------------|----------------|
| id           | INTEGER      | 主键           |
| agent_id     | TEXT         | AgentID        |
| role         | TEXT         | Agent角色      |
| goal         | TEXT         | Agent目标      |
| status       | TEXT         | Agent状态      |
| created_at   | TIMESTAMP    | 创建时间       |

## 4. 异常处理设计
- 配置模块: 
  - 文件不存在异常
  - JSON格式错误异常
- 数据库模块:
  - 数据库连接异常
  - SQL执行异常
- 网络请求:
  - API请求失败
  - 网络超时
- 文件操作:
  - 文件不存在
  - 权限不足

## 5. 日志设计
- 日志位置: `ai_agent_flow/logs/`
- 日志格式: 
  - 时间戳
  - 模块名称
  - 日志级别
  - 日志内容
- 日志级别:
  - INFO: 正常操作
  - ERROR: 错误信息