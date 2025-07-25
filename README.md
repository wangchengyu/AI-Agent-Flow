# AI Agent Flow

AI驱动的工程实现闭环系统

## 项目概述

AI Agent Flow 是一个基于AI驱动的工程实现闭环系统，它能够接收用户的原始需求（自然语言描述），通过大模型进行任务分解，然后执行子任务并最终交付完整的解决方案。

## 系统架构

系统采用模块化设计，主要包括以下核心模块：

1. **用户接口层**：提供命令行交互界面，接收用户需求并展示结果
2. **Agent执行层**：负责任务分解、调度和执行
3. **大模型接口层**：与大模型进行交互，处理自然语言理解和生成
4. **MCP服务层**：管理MCP工具集，执行具体的工具操作
5. **数据管理层**：负责本地数据的存储和管理
6. **工具集层**：提供各种具体工具实现

## 技术选型

- **Agent管理**：crewAI
- **MCP服务**：FastMCP
- **大模型接口**：OpenAI兼容API
- **数据存储**：SQLite3
- **命令行界面**：Python标准库argparse
- **项目构建**：pyproject.toml

## 项目结构

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
├── doc/                    # 文档
│   ├── design_doc.md       # 详细设计文档
│   ├── architecture.md     # 系统架构图
│   └── uml.md              # UML图
└── tests/                  # 测试文件
    ├── __init__.py
    ├── run_tests.py        # 测试运行器
    ├── test_agent.py       # Agent模块测试
    ├── test_mcp.py         # MCP模块测试
    ├── test_llm.py         # LLM模块测试
    ├── test_database.py    # 数据库模块测试
    └── test_cli.py         # CLI模块测试
```

## 安装和配置

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 配置环境变量或配置文件：
   ```json
   {
     "llm": {
       "base_url": "your_llm_base_url",
       "api_key": "your_api_key",
       "model": "your_model"
     },
     "database": {
       "path": "ai_agent_flow.db"
     }
   }
   ```

## 使用方法

### 命令行模式

```bash
# 直接提供需求
python main.py -r "创建一个Python Web应用"

# 进入交互模式
python main.py -i

# 使用配置文件
python main.py -c config.json

# 显示详细信息
python main.py -r "创建一个Python Web应用" -v
```

### 交互模式

在交互模式下，您可以直接输入需求，系统会自动处理并返回结果。

## 文档

- [详细设计文档](doc/design_doc.md)
- [系统架构图](doc/architecture.md)
- [UML图](doc/uml.md)

## 测试

运行所有测试：

```bash
python tests/run_tests.py
```

或者运行特定模块的测试：

```bash
python tests/test_agent.py
python tests/test_mcp.py
python tests/test_llm.py
python tests/test_database.py
python tests/test_cli.py
```

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

[MIT License](LICENSE)