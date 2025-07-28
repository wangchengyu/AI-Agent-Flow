from fastmcp import MCP
from config.config import load_config

class MCPService:
    def __init__(self):
        self.config = load_config()
        self.mcp = MCP()
        
    def register_tool(self, tool_name, tool_instance):
        """注册MCP工具"""
        self.mcp.register_tool(tool_name, tool_instance)
        
    def start_server(self, host='0.0.0.0', port=5000):
        """启动MCP服务"""
        self.mcp.run(host=host, port=port)