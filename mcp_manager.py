"""
MCP management module using FastMCP for the AI Agent Flow system.
Handles tool registration and file management operations.
"""

from fastmcp import MCPClient

class MCPManager:
    """Manages MCP tools and their operations."""
    
    def __init__(self):
        """Initialize MCP client and register available tools."""
        self.client = MCPClient()
        self.register_file_tools()
    
    def register_file_tools(self):
        """Register file management tools with the MCP system."""
        self.client.register_tool(
            name="list_files",
            description="List files in a directory",
            parameters={"path": {"type": "string", "description": "Directory path"}}
        )
        
        self.client.register_tool(
            name="read_file",
            description="Read contents of a file",
            parameters={"path": {"type": "string", "description": "File path"}}
        )
        
        self.client.register_tool(
            name="write_file",
            description="Write content to a file",
            parameters={
                "path": {"type": "string", "description": "File path"},
                "content": {"type": "string", "description": "Content to write"}
            }
        )
    
    def execute_file_operation(self, tool_name, parameters):
        """Execute a file management operation through MCP."""
        if tool_name not in ["list_files", "read_file", "write_file"]:
            raise ValueError(f"Unsupported tool: {tool_name}")
            
        return self.client.invoke_tool(tool_name, parameters)

if __name__ == "__main__":
    # Example usage
    mcp_manager = MCPManager()
    
    # List files example
    result = mcp_manager.execute_file_operation("list_files", {"path": "."})
    print(f"Files in current directory: {result}")
    
    # Read file example
    result = mcp_manager.execute_file_operation("read_file", {"path": "README.md"})
    print(f"README.md contents: {result[:200]}...")  # Print first 200 chars