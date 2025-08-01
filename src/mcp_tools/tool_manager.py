"""
工具管理器

负责统一管理MCP工具，提供工具的注册、调用、
权限控制和日志记录功能。
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable

from .mcp_server import MCPServer
from .mcp_client import MCPClient
from .permission_manager import PermissionManager
from ..database.tool_log_manager import ToolLogManager
from ..database.user_manager import UserManager
from ..utils.exceptions import ToolManagerError


class ToolManager:
    """工具管理器，负责统一管理MCP工具"""
    
    def __init__(self, db_manager, user_manager: UserManager, 
                 server_name: str = "agent-flow-mcp-server",
                 server_version: str = "1.0.0"):
        """
        初始化工具管理器
        
        Args:
            db_manager: 数据库管理器
            user_manager: 用户管理器
            server_name: MCP服务器名称
            server_version: MCP服务器版本
        """
        self.db_manager = db_manager
        self.user_manager = user_manager
        self.tool_log_manager = ToolLogManager(db_manager)
        self.permission_manager = PermissionManager(db_manager)
        
        # 初始化MCP服务器和客户端
        self.mcp_server = MCPServer(server_name, server_version)
        self.mcp_client = None
        
        # 工具注册表
        self.tools = {}
        self.tool_handlers = {}
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """初始化工具管理器"""
        try:
            # 初始化权限管理器
            await self.permission_manager.initialize()
            
            # 注册默认工具
            self._register_default_tools()
            
            self.logger.info("工具管理器初始化完成")
        except Exception as e:
            raise ToolManagerError(f"初始化工具管理器失败: {str(e)}")
    
    def _register_default_tools(self):
        """注册默认工具"""
        try:
            # 这里可以注册一些默认工具
            # 例如：文件操作工具、代码生成工具等
            pass
        except Exception as e:
            raise ToolManagerError(f"注册默认工具失败: {str(e)}")
    
    def register_tool(self, name: str, description: str, input_schema: Dict,
                     handler: Callable[[Dict], Awaitable[Union[str, Dict, List]]],
                     category: str = "general",
                     require_auth: bool = True,
                     required_permissions: Optional[List[str]] = None):
        """
        注册工具
        
        Args:
            name: 工具名称
            description: 工具描述
            input_schema: 输入模式
            handler: 工具处理程序
            category: 工具类别
            require_auth: 是否需要认证
            required_permissions: 所需权限列表
        """
        try:
            # 注册工具到MCP服务器
            self.mcp_server.register_tool(name, description, input_schema, handler)
            
            # 添加到工具注册表
            self.tools[name] = {
                "name": name,
                "description": description,
                "input_schema": input_schema,
                "category": category,
                "require_auth": require_auth,
                "required_permissions": required_permissions or []
            }
            self.tool_handlers[name] = handler
            
            # 注册权限
            if required_permissions:
                for permission in required_permissions:
                    self.permission_manager.register_permission(permission, f"{name}工具所需权限")
            
            self.logger.info(f"注册工具: {name}")
        except Exception as e:
            raise ToolManagerError(f"注册工具失败: {str(e)}")
    
    def unregister_tool(self, name: str):
        """
        注销工具
        
        Args:
            name: 工具名称
        """
        try:
            # 从MCP服务器注销工具
            self.mcp_server.unregister_tool(name)
            
            # 从工具注册表移除
            if name in self.tools:
                del self.tools[name]
            
            if name in self.tool_handlers:
                del self.tool_handlers[name]
            
            self.logger.info(f"注销工具: {name}")
        except Exception as e:
            raise ToolManagerError(f"注销工具失败: {str(e)}")
    
    async def call_tool(self, name: str, arguments: Optional[Dict] = None,
                      user_id: Optional[int] = None,
                      task_id: Optional[int] = None) -> Dict:
        """
        调用工具
        
        Args:
            name: 工具名称
            arguments: 工具参数
            user_id: 用户ID
            task_id: 任务ID
            
        Returns:
            工具调用结果
        """
        try:
            # 检查工具是否存在
            if name not in self.tools:
                raise ToolManagerError(f"未知工具: {name}")
            
            tool_info = self.tools[name]
            
            # 检查权限
            if tool_info["require_auth"] and user_id is None:
                raise ToolManagerError(f"工具 {name} 需要认证")
            
            if tool_info["required_permissions"] and user_id is not None:
                for permission in tool_info["required_permissions"]:
                    if not await self.permission_manager.check_permission(user_id, permission):
                        raise ToolManagerError(f"用户没有权限 {permission} 来调用工具 {name}")
            
            # 记录开始时间
            start_time = time.time()
            
            # 调用工具
            try:
                # 如果有MCP客户端，尝试通过客户端调用
                if self.mcp_client:
                    result = await self.mcp_client.execute_tool(name, arguments)
                else:
                    # 否则直接调用处理程序
                    handler = self.tool_handlers[name]
                    result = await handler(arguments or {})
                    result = {"success": True, "result": result}
            except Exception as e:
                result = {"success": False, "error": str(e)}
            
            # 记录结束时间
            end_time = time.time()
            execution_time = end_time - start_time
            
            # 记录工具调用日志
            await self.tool_log_manager.log_tool_call(
                tool_name=name,
                arguments=arguments or {},
                status="success" if result["success"] else "error",
                result=result.get("result") if result["success"] else result.get("error"),
                execution_time=execution_time,
                user_id=user_id,
                task_id=task_id
            )
            
            return result
        except Exception as e:
            # 记录错误日志
            await self.tool_log_manager.log_tool_call(
                tool_name=name,
                arguments=arguments or {},
                status="error",
                result=str(e),
                execution_time=0.0,
                user_id=user_id,
                task_id=task_id
            )
            raise ToolManagerError(f"调用工具失败: {str(e)}")
    
    def get_tools_list(self, category: Optional[str] = None) -> List[Dict]:
        """
        获取工具列表
        
        Args:
            category: 工具类别，如果为None则返回所有工具
            
        Returns:
            工具信息列表
        """
        try:
            tools_list = []
            
            for tool_name, tool_info in self.tools.items():
                if category is None or tool_info["category"] == category:
                    tools_list.append({
                        "name": tool_name,
                        "description": tool_info["description"],
                        "category": tool_info["category"],
                        "require_auth": tool_info["require_auth"],
                        "required_permissions": tool_info["required_permissions"],
                        "input_schema": tool_info["input_schema"]
                    })
            
            return tools_list
        except Exception as e:
            raise ToolManagerError(f"获取工具列表失败: {str(e)}")
    
    def get_tool_info(self, name: str) -> Optional[Dict]:
        """
        获取工具信息
        
        Args:
            name: 工具名称
            
        Returns:
            工具信息字典，如果不存在则返回None
        """
        try:
            if name not in self.tools:
                return None
            
            tool_info = self.tools[name]
            return {
                "name": tool_info["name"],
                "description": tool_info["description"],
                "category": tool_info["category"],
                "require_auth": tool_info["require_auth"],
                "required_permissions": tool_info["required_permissions"],
                "input_schema": tool_info["input_schema"]
            }
        except Exception as e:
            raise ToolManagerError(f"获取工具信息失败: {str(e)}")
    
    def get_tool_categories(self) -> List[str]:
        """
        获取工具类别列表
        
        Returns:
            工具类别列表
        """
        try:
            categories = set()
            
            for tool_info in self.tools.values():
                categories.add(tool_info["category"])
            
            return sorted(list(categories))
        except Exception as e:
            raise ToolManagerError(f"获取工具类别失败: {str(e)}")
    
    async def get_tool_usage_stats(self, days: int = 30) -> Dict:
        """
        获取工具使用统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        try:
            # 获取工具调用统计
            tool_stats = await self.tool_log_manager.get_tool_usage_stats(days)
            
            # 获取每个工具的详细信息
            tools_info = {}
            for tool_name in self.tools.keys():
                tools_info[tool_name] = self.get_tool_info(tool_name)
            
            # 合并统计信息
            result = {
                "total_calls": tool_stats.get("total_calls", 0),
                "success_rate": tool_stats.get("success_rate", 0.0),
                "avg_execution_time": tool_stats.get("avg_execution_time", 0.0),
                "tools": {}
            }
            
            for tool_name, stats in tool_stats.get("tool_stats", {}).items():
                if tool_name in tools_info:
                    result["tools"][tool_name] = {
                        **stats,
                        "info": tools_info[tool_name]
                    }
            
            return result
        except Exception as e:
            raise ToolManagerError(f"获取工具使用统计信息失败: {str(e)}")
    
    async def connect_to_mcp_server(self, server_command: List[str]):
        """
        连接到MCP服务器
        
        Args:
            server_command: 启动MCP服务器的命令
        """
        try:
            # 创建MCP客户端
            self.mcp_client = MCPClient(server_command)
            
            # 连接到服务器
            await self.mcp_client.connect()
            
            # 获取服务器信息
            server_info = await self.mcp_client.get_server_info()
            self.logger.info(f"已连接到MCP服务器: {server_info}")
        except Exception as e:
            raise ToolManagerError(f"连接到MCP服务器失败: {str(e)}")
    
    async def disconnect_from_mcp_server(self):
        """断开与MCP服务器的连接"""
        try:
            if self.mcp_client:
                await self.mcp_client.disconnect()
                self.mcp_client = None
                self.logger.info("已断开与MCP服务器的连接")
        except Exception as e:
            raise ToolManagerError(f"断开与MCP服务器连接失败: {str(e)}")
    
    async def start_mcp_server(self, host: str = "0.0.0.0", port: int = 8000):
        """
        启动MCP服务器
        
        Args:
            host: 主机地址
            port: 端口号
        """
        try:
            self.logger.info(f"启动MCP服务器: {host}:{port}")
            await self.mcp_server.run(host, port)
        except Exception as e:
            raise ToolManagerError(f"启动MCP服务器失败: {str(e)}")
    
    async def get_mcp_server_info(self) -> Dict:
        """
        获取MCP服务器信息
        
        Returns:
            服务器信息字典
        """
        try:
            return self.mcp_server.get_server_info()
        except Exception as e:
            raise ToolManagerError(f"获取MCP服务器信息失败: {str(e)}")
    
    async def get_mcp_client_info(self) -> Optional[Dict]:
        """
        获取MCP客户端信息
        
        Returns:
            客户端信息字典，如果未连接则返回None
        """
        try:
            if not self.mcp_client:
                return None
            
            return await self.mcp_client.get_server_info()
        except Exception as e:
            raise ToolManagerError(f"获取MCP客户端信息失败: {str(e)}")
    
    async def grant_tool_permission(self, user_id: int, tool_name: str):
        """
        授予用户工具权限
        
        Args:
            user_id: 用户ID
            tool_name: 工具名称
        """
        try:
            if tool_name not in self.tools:
                raise ToolManagerError(f"未知工具: {tool_name}")
            
            tool_info = self.tools[tool_name]
            
            # 授予所有所需权限
            for permission in tool_info["required_permissions"]:
                await self.permission_manager.grant_permission(user_id, permission)
            
            self.logger.info(f"已授予用户 {user_id} 工具 {tool_name} 的权限")
        except Exception as e:
            raise ToolManagerError(f"授予工具权限失败: {str(e)}")
    
    async def revoke_tool_permission(self, user_id: int, tool_name: str):
        """
        撤销用户工具权限
        
        Args:
            user_id: 用户ID
            tool_name: 工具名称
        """
        try:
            if tool_name not in self.tools:
                raise ToolManagerError(f"未知工具: {tool_name}")
            
            tool_info = self.tools[tool_name]
            
            # 撤销所有权限
            for permission in tool_info["required_permissions"]:
                await self.permission_manager.revoke_permission(user_id, permission)
            
            self.logger.info(f"已撤销用户 {user_id} 工具 {tool_name} 的权限")
        except Exception as e:
            raise ToolManagerError(f"撤销工具权限失败: {str(e)}")
    
    async def check_tool_permission(self, user_id: int, tool_name: str) -> bool:
        """
        检查用户是否有工具权限
        
        Args:
            user_id: 用户ID
            tool_name: 工具名称
            
        Returns:
            是否有权限
        """
        try:
            if tool_name not in self.tools:
                return False
            
            tool_info = self.tools[tool_name]
            
            # 检查所有权限
            for permission in tool_info["required_permissions"]:
                if not await self.permission_manager.check_permission(user_id, permission):
                    return False
            
            return True
        except Exception as e:
            raise ToolManagerError(f"检查工具权限失败: {str(e)}")