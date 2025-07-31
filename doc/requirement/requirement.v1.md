# ai agent flow

## requirement

1. 根据下面的流程图 生成出合适的python程序
    * 架构清晰, 包含如下模块:

        * Agent 以及agent flow管理
        * MCP 注册和管理
        * 大模型交互接口
        * 本地数据管理
        * rag管理
        * 命令行交互
        * 其他

    * 逻辑清晰
    * 可读性强
    * 命令行交互即可, 但是输入输出要完备

2. 使用下面的组件作为基础架构:

    * 使用openai的兼容api通大模型进行对话, 可以修改base_url和模型名还有api_key
    * 使用crewAI 作为agent flow管理 , 设计可以参考代码 finance_crew.py
    * 使用MCP SDK 来管理mcp工具, 客户端用mcp, 服务端用fastMCP 
        * client 参考 mcp_client_for_llm.py
        * server 参考 mcp_server.py
    * RAG使用 参考 rag.py
    * 使用sqlLite3作为本地数据管理

3. 根据生成的脚本生成合适的文档, 文档路径写到doc文件夹下
    * 详细设计文档
    * 系统架构图
    * UML图

4. 请根据需求先计划好作业的步骤

5. 新增功能:
    * 在子任务执行前, 加入大模型推理步骤, 根据推理结果来决定是否同用户进行交互来或取额外的信息.额外信息指的是:
        用户用自然语言补充的信息
        用户提交的数据或者其他信息
        同用户请求当前文件夹的所有文件(使用mcp工具, 询问用户是否同意即可)
        同用户请求打开某个文件(使用mcp工具, 询问用户是否同意即可)
        额外信息的推理可以循环, 因为或取文件夹内容后,一般需要或取文件内容. 但是不超过5次


6. 所有任务完成后, 你要转变为资深系统工程师, 对整个系统的代码进行检查

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
        Agent->>LLM: 请求子任务执行
        activate LLM
        LLM->>LLM: 推理出是否需要额外信息<br>(文件列表,文件,需求补充)
        loop 需要额外信息进行, 但是不能多于n次
            LLM->>Agent: 请求额外信息
            Agent->>User: 请求额外信息批准或者输入
            User->>Agent: 额外信息反馈
            Agent->>Agent: 额外信息加入到子任务需求中
            Agent->>LLM: 额外信息反馈, 并请求LLM是否需要更多
        end
        
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