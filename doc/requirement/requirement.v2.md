### AI Agent Flow 系统需求说明文档

#### 一、系统概述
本系统实现AI驱动的工程实现闭环，通过多智能体协作处理用户自然语言需求。系统基于流程图实现任务分解、工具调用和结果验证的全流程管理，核心能力包括：
- 自然语言需求解析与任务拆解
- 动态工具调用（文件操作/代码生成等）
- 子任务执行前的需求补充机制
- 多阶段结果验证
- RAG增强的知识检索
- 本地数据持久化管理

#### 二、技术栈架构
| 组件 | 技术实现 |
|------|----------|
| **Agent流程引擎** | CrewAI框架 | 
| **工具协议层** | MCP SDK (FastMCP服务端 + MCP客户端) | 
| **大模型交互** | OpenAI兼容API |
| **知识增强** | RAG检索系统 | 
| **本地存储** | SQLite3数据库 | 
| **命令行交互** | Python argparse | 

#### 三、核心功能需求
1. **需求解析与任务拆解**
   - 输入：用户自然语言需求
   - 处理：调用LLM生成结构化任务清单（XML格式）例如:
    ```xml
    <update_todo_list>
        <todos>
        [x] 分析原始requirement.md文件内容
        [x] 识别需求文档中的模糊或缺失细节
        [-] 制定需求完善规范（模块职责/交互规则/文档标准）
        [ ] 创建带日期后缀的新需求文件
        [ ] 实现需求文档结构化改进
        </todos>
    </update_todo_list>
    ```
   - 输出：用户确认后的子任务队列, 发送给LLM的任务清单为markdown格式
    ```markdown
    | # | Content | Status |
    |---|---------|--------|
    | 1 | 分析原始requirement.md文件内容 | Completed |
    | 2 | 识别需求文档中的模糊或缺失细节 | Completed |
    | 3 | 制定需求完善规范（模块职责/交互规则/文档标准） | In Progress |
    | 4 | 创建带日期后缀的新需求文件 | Pending |
    | 5 | 实现需求文档结构化改进 | Pending |
    ```
   - 特殊要求：支持用户手动重组子任务

2. **子任务预处理循环**
   ```mermaid
   graph TD
     A[开始子任务] --> B{LLM判断需补充信息？}
     B -->|是| C[发起信息补充请求]
     C --> D[用户提供自然语言/文件/权限]
     D --> E[信息整合到子任务]
     E --> F{循环次数<5?}
     F -->|是| B
     F -->|否| G[继续执行]
     B -->|否| G
   ```
   - 补充信息类型：
     - 自然语言需求细化
     - 用户提交的数据文件
     - 当前目录文件列表（需用户授权）
     - 特定文件内容（需用户授权）
   - 循环限制：最大5次信息补充

3. **任务执行双路径**
   - **工具操作路径**：
     - 通过MCP协议调用注册工具
     - 支持工具：文件操作/代码生成/UML生成等
     - 工具执行结果结构化返回
   - **AI生成路径**：
     - 直接由LLM生成文档/代码
     - 支持上下文继承（前一任务结果）

4. **结果验证机制**
   - 用户可选择LLM自动验证或人工验证
   - LLM验证流程：
     - 输入：子任务结果
     - 输出：验证报告（通过/需修改）
     - 修改建议反馈给用户

5. **最终交付**
   - 整合所有子任务输出
   - 生成完整解决方案包：
     - 设计文档
     - 可执行代码
     - 可视化结果

#### 四、模块设计规范
1. **Agent流程管理**
   - 使用CrewAI实现 Agent以及Task的管理
   - Task为线性流程,依次执行
   - 新增子任务状态机：
     ```python
     class SubTaskState(Enum):
         PENDING = 0
         INFO_GATHERING = 1
         EXECUTING = 2
         VALIDATING = 3
         COMPLETED = 4
     ```

2. **MCP工具管理**
   - 服务端实现：
     FastMCP
     ```python
     @mcp.tool()
     def list_files(confirm: bool) -> List[str]:
         """获取当前目录文件列表（需用户确认）"""
         if confirm:
             return os.listdir()
     ```
   - 客户端集成
   - 新增工具：
     - 文件浏览器（list_files）
     - 文件阅读器（read_file）
     - SQLite操作接口

3. **RAG知识管理**
   - 知识库存储：
     - 技术文档
     - 代码范例
     - 工具手册
   - 检索流程：
     ```python
     def retrieve_knowledge(query):
         chunks = rag.retrieve(query)  # 基础检索
         return rag.rerank(chunks)     # 相关性重排
     ```

4. **本地数据管理**
   - SQLite3数据库设计：
     ```sql
     CREATE TABLE task_history (
         task_id INTEGER PRIMARY KEY,
         user_input TEXT,
         subtasks JSON,
         results BLOB,
         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
     );
     ```

5. **命令行交互**
   - 交互界面功能：
     - 输入：自然语言需求
     - 处理：调用LLM生成结构化任务清单（JSON/XML格式）
     - 输出：用户确认后的子任务队列
   - 支持命令：
     - `/history` 查看任务历史
     - `/config` 修改LLM参数
     - `/debug` 进入调试模式
   - 输入输出要完备, 保证用户可以直接交互使用

#### 五、特定功能实现
1. ai agent flow 工作流
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
2. **信息补充循环**
   ```python
   async def info_gathering_loop(subtask, max_rounds=5):
       round_count = 0
       while round_count < max_rounds:
           need_more, request = await llm.check_info_need(subtask)
           if not need_more: 
               break
           user_input = cli.prompt(request)
           subtask.context.append(user_input)
           round_count += 1
   ```

#### 六、文档输出要求
1. **文档路径**：`doc/` 目录下
2. **文档内容**：
   - `ARCHITECTURE.md`：系统架构图（mermaid格式）
   - `DESIGN_***.md`：详细设计文档 ***为模块名称
   - `UML_***.md`：类图/序列图（mermaid格式）***为模块名称
3. **架构图示例**：
   ```mermaid
   graph LR
     U[用户] --> CLI[命令行接口]
     CLI --> AM[Agent管理器]
     AM --> TM[任务分解模块]
     TM --> DB[SQLite数据库]
     AM --> RAG[RAG知识库]
     AM --> MCP[MCP工具网关]
     MCP --> FS[文件工具]
     MCP --> AI[生成工具]
     MCP --> VAL[验证工具]
   ```

#### 七、实施计划
1. **阶段一：基础框架搭建**
   - 实现CrewAI任务流水线
   - 集成MCP工具网关
   - 搭建SQLite数据层

2. **阶段二：核心功能开发**
   - 实现信息补充循环
   - 集成RAG检索系统
   - 开发命令行交互界面

3. **阶段三：验证与文档**
   - 实现LLM验证模块
   - 生成架构图/UML图
   - 编写详细设计文档

4. **阶段四：代码审查**
   - 内存泄漏检测
   - 安全审计（特别是文件操作）
   - 性能压测（模拟高并发任务）

附注:
   * 使用crewAI 作为agent flow管理 , 设计可以参考sample代码 finance_crew.py
    * 使用MCP SDK 来管理mcp工具, 客户端用mcp, 服务端用fastMCP 
        * client 参考 mcp_client_for_llm.py
        * server 参考 mcp_server.py
    * RAG使用 参考 rag.py