# 系统架构图

## 1. 整体架构

```mermaid
graph TD
    A[用户] --> B[命令行交互界面]
    B --> C[Agent执行体]
    C --> D[大模型接口层]
    C --> E[MCP服务层]
    C --> F[数据管理层]
    E --> G[工具集层]
    
    subgraph 用户接口层
        A
        B
    end
    
    subgraph Agent执行层
        C
    end
    
    subgraph 大模型接口层
        D
    end
    
    subgraph MCP服务层
        E
    end
    
    subgraph 数据管理层
        F
    end
    
    subgraph 工具集层
        G
    end
```

## 2. 模块间交互关系

```mermaid
sequenceDiagram
    participant User as 用户
    participant CLI as 命令行界面
    participant Agent as Agent执行体
    participant LLM as 大模型接口
    participant MCP as MCP服务
    participant Data as 数据管理
    participant Tools as 工具集
    
    User->>CLI: 输入需求
    CLI->>Agent: 传递需求
    Agent->>LLM: 请求任务分解
    LLM-->>Agent: 返回任务清单
    Agent->>User: 请求确认子任务
    User-->>Agent: 确认子任务
    
    loop 每个子任务
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
        
        Agent->>User: 返回子任务结果
        User-->>Agent: 确认结果
    end
    
    Agent->>LLM: 请求结果整合
    LLM-->>Agent: 返回最终交付包
    Agent->>User: 交付完整解决方案
```

## 3. 数据流图

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
```

## 4. 各模块详细架构

### 4.1 命令行交互界面

```mermaid
graph TD
    A[CLI主类] --> B[参数解析]
    A --> C[配置加载]
    A --> D[需求处理]
    A --> E[结果展示]
    
    D --> F[任务分解请求]
    D --> G[任务执行]
    D --> H[结果生成]
    
    G --> I[Agent管理器]
    G --> J[任务执行器]
    G --> K[MCP服务]
    G --> L[数据库管理]
```

### 4.2 Agent执行层

```mermaid
graph TD
    A[Agent管理器] --> B[Agent创建]
    A --> C[任务创建]
    A --> D[任务调度]
    A --> E[Crew管理]
    
    F[任务执行器] --> G[任务注册]
    F --> H[任务执行]
    F --> I[结果处理]
```

### 4.3 大模型接口层

```mermaid
graph TD
    A[LLM客户端] --> B[配置管理]
    A --> C[聊天完成]
    A --> D[任务分解]
    A --> E[内容生成]
    A --> F[结果验证]
    A --> G[结果整合]
```

### 4.4 MCP服务层

```mermaid
graph TD
    A[MCP服务] --> B[工具注册]
    A --> C[工具执行]
    A --> D[协议处理]
    A --> E[请求处理]
    
    B --> F[文件管理工具]
    B --> G[其他工具]
```

### 4.5 数据管理层

```mermaid
graph TD
    A[数据库管理器] --> B[连接管理]
    A --> C[任务管理]
    A --> D[结果管理]
    A --> E[配置管理]
    
    C --> F[任务创建]
    C --> G[任务查询]
    C --> H[任务更新]
    
    D --> I[结果保存]
    D --> J[结果查询]
    D --> K[结果更新]
    
    E --> L[配置设置]
    E --> M[配置查询]
    E --> N[配置删除]