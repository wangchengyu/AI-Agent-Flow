# 系统架构图更新

## 1. 更新后的整体架构
```mermaid
graph TD
    A[用户] --> B[命令行交互界面]
    B --> C[Agent执行体]
    C --> D[大模型接口层]
    C --> E[MCP服务层]
    C --> F[数据管理层]
    E --> G[工具集层]
    D --> H[结果验证服务]
    F --> I[持久化存储]
    
    subgraph 用户接口层
        A
        B
    end
    
    subgraph Agent执行层
        C
    end
    
    subgraph 大模型接口层
        D
        H
    end
    
    subgraph MCP服务层
        E
        G
    end
    
    subgraph 数据管理层
        F
        I
    end
```

## 2. 更新的模块交互关系
```mermaid
sequenceDiagram
    participant User as 用户
    participant CLI as 命令行界面
    participant Agent as Agent执行体
    participant LLM as 大模型接口
    participant MCP as MCP服务
    participant Data as 数据管理
    participant Tools as 工具集
    participant Validator as 结果验证
    
    User->>CLI: 输入需求
    CLI->>Agent: 传递需求
    Agent->>LLM: 请求任务分解
    LLM-->>Agent: 返回任务清单
    Agent->>User: 请求确认子任务
    User-->>Agent: 确认子任务
    
    loop 每个子任务
        Agent->>LLM: 请求是否需要额外信息
        LLM-->>Agent: 返回推理结果
        
        alt 需要额外信息
            Agent->>User: 请求额外信息
            User-->>Agent: 提供额外信息
            Agent->>Data: 保存上下文状态
        end
        
        Agent->>LLM: 请求执行模式
        LLM-->>Agent: 返回执行模式
        
        alt 需要工具操作
            Agent->>MCP: 发送工具指令
            MCP->>Tools: 执行具体操作
            Tools-->>MCP: 返回操作结果
            MCP-->>Agent: 返回结构化结果
        else 需要AI生成
            Agent->>LLM: 请求内容生成
            LLM-->>Agent: 返回生成内容
        end
        
        Agent->>Data: 保存执行结果
        Data-->>Agent: 确认保存
        
        Agent->>Validator: 请求结果验证
        Validator-->>Agent: 返回验证报告
        
        Agent->>User: 返回子任务结果
        User-->>Agent: 确认结果
    end
    
    Agent->>LLM: 请求结果整合
    LLM-->>Agent: 返回最终交付包
    Agent->>User: 交付完整解决方案
```

## 3. 更新的类图
```mermaid
classDiagram
    class AgentManager {
        +create_agent(config: Dict) : Agent
        +assign_task(agent_id: str, task: Task) : bool
        +monitor_progress(agent_id: str) : ProgressStatus
    }
    
    class MCPService {
        +register_tool(name: str, func: Callable)
        +execute_tool(name: str, params: Dict) : Result
        +handle_request(request: str) : Response
    }
    
    class LLMClient {
        +chat_completion(messages: List[Dict]) : str
        +decompose_task(task: str) : List[SubTask]
    }
    
    class DatabaseManager {
        +connect() : Connection
        +backup(path: str) : bool
    }
    
    class TaskDAO {
        +create_task(task: Task) : bool
        +get_task(task_id: str) : Task
    }
    
    class CLIInterface {
        +start_interactive() : None
        +handle_command(command: str) : Response
    }
    
    class SessionManager {
        +create_session() : SessionID
        +get_context(session_id: str) : Context
    }
    
    AgentManager --> MCPService : 使用
    AgentManager --> LLMClient : 使用
    LLMClient --> Validator : 使用
    DatabaseManager --> TaskDAO : 包含
    DatabaseManager --> ResultDAO : 包含
    CLIInterface --> SessionManager : 使用
    CLIInterface --> AgentManager : 交互
```

## 4. 更新的数据流图
```mermaid
graph LR
    A[用户需求] --> B[任务分解]
    B --> C[子任务列表]
    C --> D[任务调度]
    
    D --> E[工具操作]
    D --> F[内容生成]
    
    E --> G[工具执行]
    G --> H[执行结果]
    
    F --> I[AI生成]
    I --> J[生成内容]
    
    H --> K[结果整合]
    J --> K[结果整合]
    
    K --> L[最终交付]
    L --> M[用户]
    
    subgraph 输入
        A
    end
    
    subgraph 处理
        B
        C
        D
        E
        F
        G
        H
        I
        J
        K
    end
    
    subgraph 输出
        L
        M
    end
    
    DataFlow[持久化存储] -->|读写| Processing
    Processing -->|状态更新| DataFlow