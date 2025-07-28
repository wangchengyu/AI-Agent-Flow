from mcp_server import MCPService
from tools.file_manager import FileManager

class MCPManager:
    def __init__(self):
        """初始化MCP管理器"""
        self.mcp_service = MCPService()
        self.file_manager = FileManager()
        
    def register_default_tools(self):
        """注册默认工具"""
        # 注册文件管理工具
        self.mcp_service.register_tool("file_manager", self.file_manager)
        
    def start_mcp_server(self):
        """启动MCP服务"""
        print("启动MCP服务...")
        self.register_default_tools()
        self.mcp_service.start_server()