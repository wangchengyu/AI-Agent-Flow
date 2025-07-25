# AI Agent Flow 系统设计文档

## 1. 系统概述

AI Agent Flow 是一个基于AI驱动的工程实现闭环系统，它能够接收用户的原始需求（自然语言描述），通过大模型进行任务分解，然后执行子任务并最终交付完整的解决方案。

## 2. 系统架构

### 2.1 整体架构

系统采用模块化设计，主要包括以下核心模块：

1. **用户接口层**：提供命令行交互界面，接收用户需求并展示结果
2. **Agent执行层**：负责任务分解、调度和执行
3. **大模型接口层**：与大模型进行交互，处理自然语言理解和生成
4. **MCP服务层**：管理MCP工具集，执行具体的工具操作
5. **数据管理层**：负责本地数据的存储和管理
6. **工具集层**：提供各种具体工具实现

### 2.2 模块详细设计

#### 2.2.1 用户接口层 (CLI)
- 命令行交互界面
- 接收用户原始需求
- 展示任务执行结果
- 用户确认机制

#### 2.2.2 Agent执行层
- 任务分解与调度
- 子任务执行管理
- 结果整合与验证
- 使用crewAI作为Agent管理框架

#### 2.2.3 大模型接口层
- 与大模型API交互
- 自然语言理解与生成
- 支持OpenAI兼容API
- 可配置base_url、模型名和api_key

#### 2.2.4 MCP服务层
- MCP工具注册与管理
- Protocol指令处理
- 使用FastMCP框架
- 文件管理工具示例

#### 2.2.5 数据管理层
- 本地数据存储
- 使用SQLite3数据库
- 数据持久化管理

#### 2.2.6 工具集层
- 具体工具实现
- 代码静态分析
- UML图生成
- 数据模拟
- 容器化部署（Docker引擎）

## 3. 工作流程

### 3.1 任务执行流程
1. 用户提交原始需求（自然语言描述）
2. Agent请求大模型进行任务分解
3. 大模型分析需求并返回结构化任务清单
4. Agent请求用户确认子任务
5. 对每个子任务：
   - 在执行子任务前，Agent请求大模型推理是否需要额外信息
   - 如果需要额外信息，根据信息类型与用户交互获取：
     - natural_language: 用户用自然语言补充的信息
     - user_data: 用户提交的数据或其他信息
     - folder_content: 请求当前文件夹的所有文件（使用MCP工具）
     - open_file: 请求打开某个文件（使用MCP工具）
   - 额外信息的推理可以循环进行，但不超过5次
   - Agent请求大模型确定执行模式（工具操作或AI生成）
   - 如果需要工具操作：
     - Agent生成工具指令
     - MCP服务执行具体操作
     - 返回结果给Agent
   - 如果需要AI生成：
     - Agent请求大模型生成内容
     - 大模型基于上下文生成文档/代码
     - 返回结果给Agent
   - Agent返回子任务结果给用户
   - 用户确认是否由LLM验证结果
   - 如果需要LLM验证：
     - Agent发送结果给大模型验证
     - 大模型返回验证报告
   - 用户确认子任务结果是否通过
6. Agent请求大模型整合所有结果
7. 大模型组装并返回最终交付包
8. Agent向用户交付完整解决方案

## 4. 技术选型

- **Agent管理**：crewAI
- **MCP服务**：FastMCP
- **大模型接口**：OpenAI兼容API
- **数据存储**：SQLite3
- **命令行界面**：Python标准库argparse或click
- **项目构建**：pyproject.toml

## 5. 项目结构

```
ai_agent_flow/
├── main.py                 # 程序入口
├── agent/                  # Agent执行体
│   ├── __init__.py
│   ├── manager.py          # Agent管理
│   └── executor.py         # 任务执行器
├── mcp/                    # MCP服务
│   ├── __init__.py
│   ├── service.py          # MCP服务管理
│   └── tools/              # MCP工具集
│       ├── __init__.py
│       └── file_manager.py # 文件管理工具示例
├── llm/                    # 大模型接口
│   ├── __init__.py
│   └── client.py           # 大模型客户端
├── data/                   # 数据管理
│   ├── __init__.py
│   └── database.py         # SQLite数据库管理
├── cli/                    # 命令行接口
│   ├── __init__.py
│   └── interface.py        # 命令行交互界面
├── utils/                  # 工具函数
│   ├── __init__.py
│   └── helpers.py
├── config/                 # 配置文件
│   ├── __init__.py
│   └── settings.py
├── doc/                    # 文档
│   ├── design_doc.md       # 详细设计文档
│   ├── architecture.md     # 系统架构图
│   └── uml/                # UML图
└── tests/                  # 测试文件
    ├── __init__.py
    └── test_agent.py
```

## 6. 核心类设计

### 6.1 AgentManager (agent/manager.py)
负责Agent的创建、管理和调度

### 6.2 LLMClient (llm/client.py)
负责与大模型API的交互

### 6.3 MCPService (mcp/service.py)
负责MCP服务的管理和工具调度

### 6.4 DatabaseManager (data/database.py)
负责本地数据的存储和查询

### 6.5 CLIInterface (cli/interface.py)
负责命令行交互界面

## 7. 配置管理

系统应支持以下配置：
- 大模型API的base_url、模型名和api_key
- 数据库路径
- 日志级别
- 其他可配置参数

## 8. 数据库设计

使用SQLite3数据库存储以下信息：
- 任务信息（任务ID、状态、创建时间等）
- 子任务信息（父任务ID、描述、状态等）
- 执行结果（子任务ID、结果内容、验证状态等）
- 配置信息（配置项、配置值等）

## 9. 安全考虑

- API密钥的安全存储
- 输入验证和清理
- 错误处理和日志记录