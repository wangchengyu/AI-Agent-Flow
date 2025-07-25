"""
MCP 服务模块
使用 FastMCP 作为 MCP 框架
"""

from typing import Dict, Any, List, Callable
import json


class MCPService:
    """MCP 服务管理器"""

    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.protocol_handlers: Dict[str, Callable] = {}

    def register_tool(self, name: str, tool_func: Callable, description: str = ""):
        """
        注册一个 MCP 工具
        
        Args:
            name: 工具名称
            tool_func: 工具函数
            description: 工具描述
        """
        self.tools[name] = {
            "function": tool_func,
            "description": description
        }

    def get_tool(self, name: str) -> Dict[str, Any]:
        """
        获取指定名称的工具
        
        Args:
            name: 工具名称
            
        Returns:
            Dict[str, Any]: 工具信息
        """
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        """
        列出所有已注册的工具
        
        Returns:
            List[str]: 工具名称列表
        """
        return list(self.tools.keys())

    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行指定的工具
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        tool = self.tools.get(tool_name)
        if tool is None:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found"
            }
        
        try:
            result = tool["function"](**params)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def register_protocol_handler(self, protocol: str, handler: Callable):
        """
        注册协议处理器
        
        Args:
            protocol: 协议名称
            handler: 处理器函数
        """
        self.protocol_handlers[protocol] = handler

    def handle_protocol_request(self, protocol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理协议请求
        
        Args:
            protocol: 协议名称
            data: 请求数据
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        handler = self.protocol_handlers.get(protocol)
        if handler is None:
            return {
                "success": False,
                "error": f"No handler registered for protocol: {protocol}"
            }
        
        try:
            result = handler(data)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def process_mcp_request(self, request: str) -> str:
        """
        处理 MCP 请求
        
        Args:
            request: MCP 请求（JSON格式字符串）
            
        Returns:
            str: 处理结果（JSON格式字符串）
        """
        try:
            # 解析请求
            request_data = json.loads(request)
            protocol = request_data.get("protocol")
            
            # 处理请求
            result = self.handle_protocol_request(protocol, request_data)
            
            # 返回结果
            return json.dumps(result)
        except json.JSONDecodeError as e:
            return json.dumps({
                "success": False,
                "error": f"Invalid JSON request: {str(e)}"
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e)
            })