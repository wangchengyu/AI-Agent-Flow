# ai agent flow

## requirement

1. 根据下面的流程图 生成出合适的python程序
    * 架构清晰, 包含如下模块:

        _Agent 管理
        _MCP 注册和管理, 生成file管理的mcp工具作为示例
        _大模型交互接口
        _本地数据管理
        _命令行交互
        _其他

    * 逻辑清晰
    * 可读性强
    * 命令行交互即可, 但是输入输出要完备

2. 使用下面的组件作为基础架构:

    * 使用openai的兼容api通大模型进行对话, 可以修改base_url和模型名还有api_key
    * 使用crewAI 作为agent管理
    * 使用FastMCP 来管理mcp工具
    * 使用sqlLite3作为本地数据管理

3. 根据生成的脚本生成合适的文档, 文档路径写到doc文件夹下
    * 详细设计文档
    * 系统架构图
    * UML图

4. 请根据需求先计划好作业的步骤



## flow

```mermaid
sequenceDiagram
    participant User as 用户
    participant Agent as Agent执行体
    participant MCPService as MCP服务
    participant Tools as 工具集
    participant LLM as 大模型

    Note over User,LLM: AI驱动的工程实现闭环

    %% 初始需求提交
    User->>Agent: 原始需求<br>（自然语言描述）
    activate Agent

    %% 大模型任务分解
    Agent->>LLM: 请求任务分解<br>（需求Context）
    activate LLM
    LLM->>LLM: 需求分析→任务拆解
    LLM->>Agent: 结构化任务清单<br>（json/xml）
    deactivate LLM

    Agent->>User: 请求子任务确认
    activate User
    User->>User: 子任务重组
    User->>Agent: 确认子任务
    deactivate User

    %% 任务执行循环
    loop 每个子任务
        Agent->>LLM: 请求子任务执行模式
        activate LLM
        LLM->>LLM: 根据需求决定是内容生成还是工具操作
        LLM->>Agent: 返回结构化操作内容
        deactivate LLM

        alt 需要工具操作
            Agent->>Agent: Agent根据生成工具指令

            %% 执行工具操作
            Agent->>MCPService: 发送Protocol指令
            activate MCPService
            MCPService->>Tools: 执行具体操作
            activate Tools
            Tools->>MCPService: 操作结果
            deactivate Tools
            MCPService->>Agent: 结构化结果
            deactivate MCPService

        else 需要AI生成
            %% 大模型生成内容
            Agent->>LLM: 请求内容生成<br>（设计/代码）
            activate LLM
            LLM->>LLM: 基于Context生成<br>(这里的Context可以是上一个子任务的结果)
            LLM-->>Agent: 生成结果<br>（文档/代码）
            deactivate LLM
        end

        %% 结果验证
        Agent->>User: 返回子任务结果
        activate User
        Agent->>User: 请求是否由LLM确认子任务结果
        User->>Agent: 返回是否由LLM确认子任务结果
 
        alt LLM来确认生成结果
            Agent->>LLM: 发送需要确认的子任务结果
            activate LLM
            LLM->>LLM: 结果检测/评估
            LLM->>Agent: 验证报告<br>（通过/需修改）
            Agent->>User: 验证报告<br>（通过/需修改
            deactivate LLM
        end
        User->>Agent: 返回子任务结果是否通过
        deactivate User
    end

    %% 最终交付
    Agent->>LLM: 请求结果整合
    activate LLM
    LLM->>LLM: 组装所有输出
    LLM-->>Agent: 最终交付包
    deactivate LLM
    Agent->>User: 完整解决方案<br>（设计文档+代码）
    deactivate Agent

    Note right of Tools: MCP工具集扩展能力<br>▸ 代码静态分析<br>▸ UML图生成<br>▸ 数据模拟<br>▸ 容器化部署（Docker引擎）
```