"""
MCP客户端

负责实现MCP（Model Context Protocol）客户端功能，
提供与MCP服务器交互的能力。
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from mcp.types import (
    CallToolRequestParams,
    CallToolResult,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    Resource,
    ListResourcesResult,
    ReadResourceRequestParams,
    ReadResourceResult,
    ResourceContent,
    ResourceTemplate,
    ListResourceTemplatesResult,
    Prompt,
    ListPromptsResult,
    GetPromptRequestParams,
    GetPromptResult,
    PromptMessage,
    Role,
)

from ..utils.exceptions import MCPClientError


class MCPClient:
    """MCP客户端，负责与MCP服务器交互"""
    
    def __init__(self, server_command: List[str]):
        """
        初始化MCP客户端
        
        Args:
            server_command: 启动MCP服务器的命令
        """
        self.server_command = server_command
        self.session = None
        self.client = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def connect(self):
        """连接到MCP服务器"""
        try:
            self.logger.info(f"连接到MCP服务器: {' '.join(self.server_command)}")
            
            # 创建stdio客户端
            self.client = stdio_client(self.server_command)
            
            # 创建会话
            read, write = await self.client.connect()
            self.session = ClientSession(read, write)
            
            # 初始化会话
            await self.session.initialize()
            
            self.logger.info("成功连接到MCP服务器")
        except Exception as e:
            raise MCPClientError(f"连接MCP服务器失败: {str(e)}")
    
    async def disconnect(self):
        """断开与MCP服务器的连接"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            
            if self.client:
                await self.client.disconnect()
                self.client = None
            
            self.logger.info("已断开与MCP服务器的连接")
        except Exception as e:
            raise MCPClientError(f"断开MCP服务器连接失败: {str(e)}")
    
    async def list_tools(self) -> List[Tool]:
        """
        列出可用工具
        
        Returns:
            工具列表
        """
        try:
            if not self.session:
                raise MCPClientError("未连接到MCP服务器")
            
            # 调用list_tools方法
            result = await self.session.list_tools()
            
            if isinstance(result, ListToolsResult):
                return result.tools
            else:
                raise MCPClientError(f"意外的结果类型: {type(result)}")
        except Exception as e:
            raise MCPClientError(f"列出工具失败: {str(e)}")
    
    async def call_tool(self, name: str, arguments: Optional[Dict] = None) -> CallToolResult:
        """
        调用工具
        
        Args:
            name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具调用结果
        """
        try:
            if not self.session:
                raise MCPClientError("未连接到MCP服务器")
            
            # 准备请求参数
            params = CallToolRequestParams(name=name, arguments=arguments or {})
            
            # 调用call_tool方法
            result = await self.session.call_tool(params)
            
            if isinstance(result, CallToolResult):
                return result
            else:
                raise MCPClientError(f"意外的结果类型: {type(result)}")
        except Exception as e:
            raise MCPClientError(f"调用工具失败: {str(e)}")
    
    async def list_resources(self) -> List[Resource]:
        """
        列出可用资源
        
        Returns:
            资源列表
        """
        try:
            if not self.session:
                raise MCPClientError("未连接到MCP服务器")
            
            # 调用list_resources方法
            result = await self.session.list_resources()
            
            if isinstance(result, ListResourcesResult):
                return result.resources
            else:
                raise MCPClientError(f"意外的结果类型: {type(result)}")
        except Exception as e:
            raise MCPClientError(f"列出资源失败: {str(e)}")
    
    async def read_resource(self, uri: str) -> ResourceContent:
        """
        读取资源
        
        Args:
            uri: 资源URI
            
        Returns:
            资源内容
        """
        try:
            if not self.session:
                raise MCPClientError("未连接到MCP服务器")
            
            # 准备请求参数
            params = ReadResourceRequestParams(uri=uri)
            
            # 调用read_resource方法
            result = await self.session.read_resource(params)
            
            if isinstance(result, ReadResourceResult):
                return result.contents[0] if result.contents else None
            else:
                raise MCPClientError(f"意外的结果类型: {type(result)}")
        except Exception as e:
            raise MCPClientError(f"读取资源失败: {str(e)}")
    
    async def list_resource_templates(self) -> List[ResourceTemplate]:
        """
        列出可用资源模板
        
        Returns:
            资源模板列表
        """
        try:
            if not self.session:
                raise MCPClientError("未连接到MCP服务器")
            
            # 调用list_resource_templates方法
            result = await self.session.list_resource_templates()
            
            if isinstance(result, ListResourceTemplatesResult):
                return result.resourceTemplates
            else:
                raise MCPClientError(f"意外的结果类型: {type(result)}")
        except Exception as e:
            raise MCPClientError(f"列出资源模板失败: {str(e)}")
    
    async def list_prompts(self) -> List[Prompt]:
        """
        列出可用提示
        
        Returns:
            提示列表
        """
        try:
            if not self.session:
                raise MCPClientError("未连接到MCP服务器")
            
            # 调用list_prompts方法
            result = await self.session.list_prompts()
            
            if isinstance(result, ListPromptsResult):
                return result.prompts
            else:
                raise MCPClientError(f"意外的结果类型: {type(result)}")
        except Exception as e:
            raise MCPClientError(f"列出提示失败: {str(e)}")
    
    async def get_prompt(self, name: str, arguments: Optional[Dict] = None) -> PromptMessage:
        """
        获取提示
        
        Args:
            name: 提示名称
            arguments: 提示参数
            
        Returns:
            提示消息
        """
        try:
            if not self.session:
                raise MCPClientError("未连接到MCP服务器")
            
            # 准备请求参数
            params = GetPromptRequestParams(name=name, arguments=arguments or {})
            
            # 调用get_prompt方法
            result = await self.session.get_prompt(params)
            
            if isinstance(result, GetPromptResult):
                return result.description if result.description else None
            else:
                raise MCPClientError(f"意外的结果类型: {type(result)}")
        except Exception as e:
            raise MCPClientError(f"获取提示失败: {str(e)}")
    
    async def get_tools_info(self) -> List[Dict]:
        """
        获取工具信息
        
        Returns:
            工具信息列表
        """
        try:
            # 获取工具列表
            tools = await self.list_tools()
            
            # 转换为信息字典
            tools_info = []
            for tool in tools:
                tools_info.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })
            
            return tools_info
        except Exception as e:
            raise MCPClientError(f"获取工具信息失败: {str(e)}")
    
    async def get_resources_info(self) -> List[Dict]:
        """
        获取资源信息
        
        Returns:
            资源信息列表
        """
        try:
            # 获取资源列表
            resources = await self.list_resources()
            
            # 转换为信息字典
            resources_info = []
            for resource in resources:
                resources_info.append({
                    "uri": resource.uri,
                    "name": resource.name,
                    "description": resource.description,
                    "mime_type": resource.mimeType
                })
            
            return resources_info
        except Exception as e:
            raise MCPClientError(f"获取资源信息失败: {str(e)}")
    
    async def get_prompts_info(self) -> List[Dict]:
        """
        获取提示信息
        
        Returns:
            提示信息列表
        """
        try:
            # 获取提示列表
            prompts = await self.list_prompts()
            
            # 转换为信息字典
            prompts_info = []
            for prompt in prompts:
                prompts_info.append({
                    "name": prompt.name,
                    "description": prompt.description,
                    "arguments": [
                        {
                            "name": arg.name,
                            "description": arg.description,
                            "required": arg.required
                        }
                        for arg in prompt.arguments
                    ]
                })
            
            return prompts_info
        except Exception as e:
            raise MCPClientError(f"获取提示信息失败: {str(e)}")
    
    async def get_server_info(self) -> Dict:
        """
        获取服务器信息
        
        Returns:
            服务器信息字典
        """
        try:
            # 获取工具、资源和提示信息
            tools_info = await self.get_tools_info()
            resources_info = await self.get_resources_info()
            prompts_info = await self.get_prompts_info()
            
            return {
                "server_command": self.server_command,
                "tools_count": len(tools_info),
                "resources_count": len(resources_info),
                "prompts_count": len(prompts_info),
                "tools": tools_info,
                "resources": resources_info,
                "prompts": prompts_info
            }
        except Exception as e:
            raise MCPClientError(f"获取服务器信息失败: {str(e)}")
    
    async def execute_tool(self, name: str, arguments: Optional[Dict] = None) -> Dict:
        """
        执行工具并返回解析后的结果
        
        Args:
            name: 工具名称
            arguments: 工具参数
            
        Returns:
            解析后的工具结果
        """
        try:
            # 调用工具
            result = await self.call_tool(name, arguments)
            
            # 解析结果
            if result.isError:
                return {
                    "success": False,
                    "error": self._extract_text_from_content(result.content)
                }
            else:
                return {
                    "success": True,
                    "result": self._extract_content(result.content)
                }
        except Exception as e:
            raise MCPClientError(f"执行工具失败: {str(e)}")
    
    def _extract_text_from_content(self, content) -> str:
        """
        从内容中提取文本
        
        Args:
            content: 内容对象
            
        Returns:
            提取的文本
        """
        try:
            if isinstance(content, list) and len(content) > 0:
                first_item = content[0]
                if hasattr(first_item, 'text'):
                    return first_item.text
                elif isinstance(first_item, dict) and 'text' in first_item:
                    return first_item['text']
            
            return str(content)
        except Exception as e:
            self.logger.error(f"提取文本失败: {str(e)}")
            return str(content)
    
    def _extract_content(self, content) -> Union[str, List]:
        """
        提取内容
        
        Args:
            content: 内容对象
            
        Returns:
            提取的内容
        """
        try:
            if isinstance(content, list):
                if len(content) == 1:
                    return self._extract_text_from_content(content)
                else:
                    result = []
                    for item in content:
                        if hasattr(item, 'text'):
                            result.append(item.text)
                        elif isinstance(item, dict) and 'text' in item:
                            result.append(item['text'])
                        else:
                            result.append(str(item))
                    return result
            else:
                return self._extract_text_from_content(content)
        except Exception as e:
            self.logger.error(f"提取内容失败: {str(e)}")
            return str(content)