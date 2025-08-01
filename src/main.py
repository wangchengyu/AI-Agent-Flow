import os
from crewai import Agent, LLM
from agents.agent_manager import AgentManager
from tools.mcp_service import app as mcp_app, registry
from database.db_manager import DatabaseManager
from cli.cli_interface import CLIInterface
import threading
import uvicorn

# 初始化LLM模型（简化实现）
class LLMModel():
    def __init__(self):
        self.llm = LLM(
            model="deepseek-reasoner",
            base_url="https://api.deepseek.com/v1",
            api_key=os.getenv("OPENAI_API_KEY")
        )

    def generate(self, prompt: str) -> str:
        """简化LLM生成"""
        # 实际项目中应集成真实LLM API
        return f"<update_todo_list><todos>[ ] {prompt}</todos></update_todo_list>"

def start_mcp_server():
    """启动MCP服务端"""
    uvicorn.run(mcp_app, host="0.0.0.0", port=8000)

def main():
    # 初始化核心组件
    llm_model = LLMModel()
    db_manager = DatabaseManager()
    agent_manager = AgentManager(llm_model)
    
    # 启动MCP服务端（后台线程）
    mcp_thread = threading.Thread(target=start_mcp_server, daemon=True)
    mcp_thread.start()
    
    # 初始化CLI
    cli = CLIInterface(agent_manager, db_manager)
    
    print("""
    AI Agent Flow System
    --------------------
    MCP Server running at http://localhost:8000
    Type your natural language request or command (use /help for commands)
    """)
    
    # 启动命令行接口
    cli.start()

if __name__ == "__main__":
    main()