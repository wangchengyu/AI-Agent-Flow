# 大模型接口模块详细设计文档

## 1. 模块职责
- 提供统一的大模型交互接口
- 支持多模型供应商（OpenAI兼容接口）
- 实现任务分解与内容生成能力
- 维护模型配置管理
- 处理API请求与错误恢复

## 2. 核心组件设计

### 2.1 LLMClient
```mermaid
classDiagram
    class LLMClient {
        +__init__(api_key: str, base_url: str, model: str)
        +chat_completion(messages: List[Dict]) : str
        +decompose_task(task: str) : List[SubTask]
        +generate_content(prompt: str) : str
        +validate_result(result: str) : ValidationReport
    }
```

### 2.2 ModelAdapterManager
```mermaid
classDiagram
    class ModelAdapterManager {
        +register_adapter(model_type: str, adapter: ModelAdapter)
        +get_adapter(model_type: str) : ModelAdapter
        +adapt_request(model_type: str, request: Dict) : Dict
    }
```

## 3. 交互流程设计
```mermaid
sequenceDiagram
    participant Agent
    participant LLMClient
    participant ModelAPI
    participant MCPService

    Agent->>LLMClient: 请求任务分解
    LLMClient->>ModelAPI: 发送分解请求
    ModelAPI-->>LLMClient: 返回子任务列表
    LLMClient-->>Agent: 返回分解结果

    Agent->>LLMClient: 请求工具调用
    LLMClient->>ModelAPI: 发送工具调用请求
    ModelAPI-->>LLMClient: 返回工具参数
    LLMClient->>MCPService: 调用MCP工具
    MCPService-->>LLMClient: 返回执行结果
    LLMClient-->>Agent: 返回完整响应
```

## 4. 配置管理
```python
# llm/client.py
import os
from typing import Dict, Any

class LLMConfig:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.timeout = int(os.getenv("LLM_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("LLM_RETRIES", "3"))

class LLMClient:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.session = self._init_session()
        
    def _init_session(self):
        # 初始化API会话
        return requests.Session()
```

## 5. 错误处理策略
```mermaid
graph TD
    A[API请求] --> B{响应状态}
    B -->|200| C[返回结果]
    B -->|4xx| D[客户端错误处理]
    D --> E[记录错误日志]
    D --> F[返回用户提示]
    B -->|5xx| G[服务端错误处理]
    G --> H[自动重试机制]
    H -->|达到重试次数| I[返回服务错误]
    H -->|未达到重试次数| A
```

## 6. 安全机制
- API密钥隔离：通过环境变量注入，不硬编码在代码中
- 请求签名：对敏感请求进行数字签名验证
- 速率限制：客户端和服务端双重重试控制
- 内容过滤：输入输出内容的安全检查
- 审计日志：记录所有API调用和响应结果