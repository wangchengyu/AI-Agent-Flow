# UML图

## 1. 类图

### 1.1 核心类图

```mermaid
classDiagram
    class CLIInterface {
        +llm_client: LLMClient
        +agent_manager: AgentManager
        +task_executor: TaskExecutor
        +mcp_service: MCPService
        +db_manager: DatabaseManager
        +_register_mcp_tools()
        +_setup_argument_parser()
        +_load_config(config_path: str)
        +_get_user_requirement() str
        +_process_requirement(requirement: str)
        +run()
    }
    
    class LLMClient {
        +base_url: str
        +api_key: str
        +model: str
        +client: OpenAI
        +set_config(base_url: str, api_key: str, model: str)
        +chat_completion(messages: List[Dict[str, str]]) Dict[str, Any]
        +task_decomposition(requirement: str) Dict[str, Any]
        +content_generation(context: str, task: str) Dict[str, Any]
        +result_validation(result: str, requirement: str) Dict[str, Any]
        +result_integration(results: List[str]) Dict[str, Any]
    }
    
    class AgentManager {
        +agents: Dict[str, Agent]
        +tasks: List[Task]
        +crew: Crew
        +create_agent(name: str, role: str, goal: str, backstory: str) Agent
        +get_agent(name: str) Agent
        +create_task(description: str, agent: Agent, expected_output: str) Task
        +create_crew(agents: List[Agent], tasks: List[Task]) Crew
        +execute_crew() Dict[str, Any]
    }
    
    class TaskExecutor {
        +agent_manager: AgentManager
        +task_handlers: Dict[str, Callable]
        +register_task_handler(task_type: str, handler: Callable)
        +execute_task(task_type: str, task_data: Dict[str, Any]) Dict[str, Any]
        +execute_task_list(task_list: List[Dict[str, Any]]) List[Dict[str, Any]]
    }
    
    class MCPService {
        +tools: Dict[str, Dict[str, Any]]
        +protocol_handlers: Dict[str, Callable]
        +register_tool(name: str, tool_func: Callable, description: str)
        +get_tool(name: str) Dict[str, Any]
        +list_tools() List[str]
        +execute_tool(tool_name: str, params: Dict[str, Any]) Dict[str, Any]
        +register_protocol_handler(protocol: str, handler: Callable)
        +handle_protocol_request(protocol: str, data: Dict[str, Any]) Dict[str, Any]
        +process_mcp_request(request: str) str
    }
    
    class DatabaseManager {
        +db_path: str
        +init_database()
        +get_connection() ContextManager
        +create_task(task_id: str, description: str, parent_task_id: str) bool
        +update_task_status(task_id: str, status: str) bool
        +get_task(task_id: str) Optional[Dict[str, Any]]
        +get_tasks_by_parent(parent_task_id: str) List[Dict[str, Any]]
        +save_task_result(task_id: str, result_content: str, validation_status: str) bool
        +update_result_validation_status(task_id: str, validation_status: str) bool
        +get_task_result(task_id: str) Optional[Dict[str, Any]]
        +set_config(key: str, value: str, description: str) bool
        +get_config(key: str) Optional[str]
        +get_all_config() Dict[str, str]
        +delete_config(key: str) bool
    }
    
    CLIInterface --> LLMClient
    CLIInterface --> AgentManager
    CLIInterface --> TaskExecutor
    CLIInterface --> MCPService
    CLIInterface --> DatabaseManager
    TaskExecutor --> AgentManager
```

### 1.2 工具类图

```mermaid
classDiagram
    class FileManager {
        +read_file(file_path: str) Dict[str, Any]
        +write_file(file_path: str, content: str) Dict[str, Any]
        +list_files(directory: str) Dict[str, Any]
        +delete_file(file_path: str) Dict[str, Any]
        +create_directory(directory_path: str) Dict[str, Any]
    }
    
    class TOOL_INFO {
        +read_file: Dict[str, Any]
        +write_file: Dict[str, Any]
        +list_files: Dict[str, Any]
        +delete_file: Dict[str, Any]
        +create_directory: Dict[str, Any]
    }
    
    FileManager --> TOOL_INFO
```

## 2. 序列图

### 2.1 任务处理序列图

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant AgentManager
    participant LLMClient
    participant TaskExecutor
    participant MCPService
    participant DatabaseManager
    
    User->>CLI: 输入需求
    CLI->>LLMClient: task_decomposition(需求)
    LLMClient-->>CLI: 返回任务清单
    
    CLI->>AgentManager: create_agent(参数)
    AgentManager-->>CLI: 返回Agent
    
    CLI->>AgentManager: create_task(参数)
    AgentManager-->>CLI: 返回Task
    
    loop 每个任务
        CLI->>TaskExecutor: execute_task(任务类型, 数据)
        
        alt 工具任务
            TaskExecutor->>MCPService: execute_tool(工具名, 参数)
            MCPService-->>TaskExecutor: 返回结果
        else AI生成任务
            TaskExecutor->>LLMClient: content_generation(上下文, 任务)
            LLMClient-->>TaskExecutor: 返回生成内容
        end
        
        TaskExecutor-->>CLI: 返回执行结果
        CLI->>DatabaseManager: save_task_result(任务ID, 结果)
        DatabaseManager-->>CLI: 确认保存
    end
    
    CLI->>LLMClient: result_integration(所有结果)
    LLMClient-->>CLI: 返回最终结果
    CLI->>User: 展示最终结果
```

### 2.2 MCP工具执行序列图

```mermaid
sequenceDiagram
    participant Agent
    participant MCPService
    participant FileManager
    participant Database
    
    Agent->>MCPService: execute_tool("read_file", {"file_path": "test.txt"})
    MCPService->>FileManager: read_file("test.txt")
    FileManager-->>MCPService: 返回文件内容
    MCPService-->>Agent: 返回结果
    
    Agent->>MCPService: execute_tool("write_file", {"file_path": "output.txt", "content": "Hello"})
    MCPService->>FileManager: write_file("output.txt", "Hello")
    FileManager-->>MCPService: 返回写入结果
    MCPService-->>Agent: 返回结果
    
    Agent->>MCPService: execute_tool("list_files", {"directory": "."})
    MCPService->>FileManager: list_files(".")
    FileManager-->>MCPService: 返回文件列表
    MCPService-->>Agent: 返回结果
```

## 3. 状态图

### 3.1 任务状态图

```mermaid
stateDiagram
    [*] --> Pending
    Pending --> InProgress: 开始执行
    InProgress --> Completed: 执行成功
    InProgress --> Failed: 执行失败
    Failed --> InProgress: 重试
    Completed --> [*]
    
    note right of Pending
        任务已创建，等待执行
    end note
    
    note right of InProgress
        任务正在执行中
    end note
    
    note right of Completed
        任务执行完成
    end note
    
    note right of Failed
        任务执行失败
    end note
```

### 3.2 系统状态图

```mermaid
stateDiagram
    [*] --> Initializing
    Initializing --> Ready: 初始化完成
    Ready --> Processing: 接收任务
    Processing --> Ready: 任务完成
    Ready --> Error: 发生错误
    Error --> Ready: 错误恢复
    
    note right of Initializing
        系统初始化中
    end note
    
    note right of Ready
        系统就绪，等待任务
    end note
    
    note right of Processing
        系统正在处理任务
    end note
    
    note right of Error
        系统发生错误
    end note
```

## 4. 活动图

### 4.1 任务处理活动图

```mermaid
flowchart TD
    A[开始] --> B[接收用户需求]
    B --> C[任务分解]
    C --> D[创建Agent和任务]
    D --> E[执行任务]
    
    E --> F{任务类型}
    F -->|工具操作| G[调用MCP工具]
    F -->|AI生成| H[调用大模型生成]
    
    G --> I[保存结果到数据库]
    H --> I
    
    I --> J{是否还有任务}
    J -->|是| E
    J -->|否| K[整合结果]
    
    K --> L[返回给用户]
    L --> M[结束]