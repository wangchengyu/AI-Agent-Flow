"""
MCP服务器

负责实现MCP（Model Context Protocol）服务器功能，
提供工具调用、资源访问和提示管理能力。
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    Resource,
    ResourceContent,
    ListResourcesRequest,
    ReadResourceRequest,
    ResourceTemplate,
    ListResourceTemplatesRequest,
    Prompt,
    ListPromptsRequest,
    GetPromptRequest,
    PromptArgument,
    PromptMessage,
    Role,
)

from ..utils.exceptions import MCPServerError


class MCPServer:
    """MCP服务器，负责实现MCP服务器功能"""
    
    def __init__(self, name: str = "agent-flow-mcp-server", version: str = "1.0.0"):
        """
        初始化MCP服务器
        
        Args:
            name: 服务器名称
            version: 服务器版本
        """
        self.name = name
        self.version = version
        self.server = Server(name)
        self.tools = {}
        self.resources = {}
        self.resource_templates = {}
        self.prompts = {}
        self.tool_handlers = {}
        self.resource_handlers = {}
        self.prompt_handlers = {}
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 注册默认处理程序
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认处理程序"""
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """列出可用工具"""
            return list(self.tools.values())
        
        @self.server.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            """调用工具"""
            tool_name = request.params.name
            arguments = request.params.arguments or {}
            
            if tool_name not in self.tool_handlers:
                raise MCPServerError(f"未知工具: {tool_name}")
            
            try:
                # 调用工具处理程序
                result = await self.tool_handlers[tool_name](arguments)
                
                # 转换结果格式
                if isinstance(result, str):
                    content = [TextContent(type="text", text=result)]
                elif isinstance(result, dict) and "content" in result:
                    content = [TextContent(type="text", text=result["content"])]
                elif isinstance(result, list):
                    content = []
                    for item in result:
                        if isinstance(item, str):
                            content.append(TextContent(type="text", text=item))
                        elif isinstance(item, dict) and "type" in item and "text" in item:
                            if item["type"] == "text":
                                content.append(TextContent(type="text", text=item["text"]))
                            elif item["type"] == "image":
                                content.append(ImageContent(type="image", data=item["data"], mime_type=item.get("mime_type", "image/png")))
                else:
                    content = [TextContent(type="text", text=str(result))]
                
                return CallToolResult(content=content)
            except Exception as e:
                self.logger.error(f"调用工具 {tool_name} 失败: {str(e)}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"错误: {str(e)}")],
                    isError=True
                )
        
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """列出可用资源"""
            return list(self.resources.values())
        
        @self.server.read_resource()
        async def read_resource(request: ReadResourceRequest) -> ResourceContent:
            """读取资源"""
            resource_uri = request.params.uri
            
            if resource_uri not in self.resource_handlers:
                raise MCPServerError(f"未知资源: {resource_uri}")
            
            try:
                # 调用资源处理程序
                result = await self.resource_handlers[resource_uri]()
                
                # 转换结果格式
                if isinstance(result, str):
                    contents = [TextContent(type="text", text=result)]
                elif isinstance(result, list):
                    contents = []
                    for item in result:
                        if isinstance(item, str):
                            contents.append(TextContent(type="text", text=item))
                        elif isinstance(item, dict) and "type" in item and "text" in item:
                            if item["type"] == "text":
                                contents.append(TextContent(type="text", text=item["text"]))
                            elif item["type"] == "image":
                                contents.append(ImageContent(type="image", data=item["data"], mime_type=item.get("mime_type", "image/png")))
                else:
                    contents = [TextContent(type="text", text=str(result))]
                
                return ResourceContent(contents=contents)
            except Exception as e:
                self.logger.error(f"读取资源 {resource_uri} 失败: {str(e)}")
                raise MCPServerError(f"读取资源失败: {str(e)}")
        
        @self.server.list_resource_templates()
        async def list_resource_templates() -> List[ResourceTemplate]:
            """列出可用资源模板"""
            return list(self.resource_templates.values())
        
        @self.server.list_prompts()
        async def list_prompts() -> List[Prompt]:
            """列出可用提示"""
            return list(self.prompts.values())
        
        @self.server.get_prompt()
        async def get_prompt(request: GetPromptRequest) -> PromptMessage:
            """获取提示"""
            prompt_name = request.params.name
            arguments = request.params.arguments or {}
            
            if prompt_name not in self.prompt_handlers:
                raise MCPServerError(f"未知提示: {prompt_name}")
            
            try:
                # 调用提示处理程序
                result = await self.prompt_handlers[prompt_name](arguments)
                
                # 转换结果格式
                if isinstance(result, str):
                    content = TextContent(type="text", text=result)
                elif isinstance(result, dict) and "content" in result:
                    content = TextContent(type="text", text=result["content"])
                else:
                    content = TextContent(type="text", text=str(result))
                
                return PromptMessage(role=Role.user, content=content)
            except Exception as e:
                self.logger.error(f"获取提示 {prompt_name} 失败: {str(e)}")
                raise MCPServerError(f"获取提示失败: {str(e)}")
    
    def register_tool(self, name: str, description: str, input_schema: Dict, 
                     handler: Callable[[Dict], Awaitable[Union[str, Dict, List]]]):
        """
        注册工具
        
        Args:
            name: 工具名称
            description: 工具描述
            input_schema: 输入模式
            handler: 工具处理程序
        """
        try:
            # 创建工具对象
            tool = Tool(
                name=name,
                description=description,
                inputSchema=input_schema
            )
            
            # 注册工具
            self.tools[name] = tool
            self.tool_handlers[name] = handler
            
            self.logger.info(f"注册工具: {name}")
        except Exception as e:
            raise MCPServerError(f"注册工具失败: {str(e)}")
    
    def unregister_tool(self, name: str):
        """
        注销工具
        
        Args:
            name: 工具名称
        """
        try:
            if name in self.tools:
                del self.tools[name]
            
            if name in self.tool_handlers:
                del self.tool_handlers[name]
            
            self.logger.info(f"注销工具: {name}")
        except Exception as e:
            raise MCPServerError(f"注销工具失败: {str(e)}")
    
    def register_resource(self, uri: str, name: str, description: str, 
                         handler: Callable[[], Awaitable[Union[str, Dict, List]]],
                         mime_type: Optional[str] = None):
        """
        注册资源
        
        Args:
            uri: 资源URI
            name: 资源名称
            description: 资源描述
            handler: 资源处理程序
            mime_type: MIME类型
        """
        try:
            # 创建资源对象
            resource = Resource(
                uri=uri,
                name=name,
                description=description,
                mimeType=mime_type
            )
            
            # 注册资源
            self.resources[uri] = resource
            self.resource_handlers[uri] = handler
            
            self.logger.info(f"注册资源: {uri}")
        except Exception as e:
            raise MCPServerError(f"注册资源失败: {str(e)}")
    
    def unregister_resource(self, uri: str):
        """
        注销资源
        
        Args:
            uri: 资源URI
        """
        try:
            if uri in self.resources:
                del self.resources[uri]
            
            if uri in self.resource_handlers:
                del self.resource_handlers[uri]
            
            self.logger.info(f"注销资源: {uri}")
        except Exception as e:
            raise MCPServerError(f"注销资源失败: {str(e)}")
    
    def register_resource_template(self, uri_template: str, name: str, description: str):
        """
        注册资源模板
        
        Args:
            uri_template: URI模板
            name: 模板名称
            description: 模板描述
        """
        try:
            # 创建资源模板对象
            template = ResourceTemplate(
                uriTemplate=uri_template,
                name=name,
                description=description
            )
            
            # 注册资源模板
            self.resource_templates[uri_template] = template
            
            self.logger.info(f"注册资源模板: {uri_template}")
        except Exception as e:
            raise MCPServerError(f"注册资源模板失败: {str(e)}")
    
    def unregister_resource_template(self, uri_template: str):
        """
        注销资源模板
        
        Args:
            uri_template: URI模板
        """
        try:
            if uri_template in self.resource_templates:
                del self.resource_templates[uri_template]
            
            self.logger.info(f"注销资源模板: {uri_template}")
        except Exception as e:
            raise MCPServerError(f"注销资源模板失败: {str(e)}")
    
    def register_prompt(self, name: str, description: str, arguments: List[PromptArgument],
                       handler: Callable[[Dict], Awaitable[Union[str, Dict]]]):
        """
        注册提示
        
        Args:
            name: 提示名称
            description: 提示描述
            arguments: 提示参数列表
            handler: 提示处理程序
        """
        try:
            # 创建提示对象
            prompt = Prompt(
                name=name,
                description=description,
                arguments=arguments
            )
            
            # 注册提示
            self.prompts[name] = prompt
            self.prompt_handlers[name] = handler
            
            self.logger.info(f"注册提示: {name}")
        except Exception as e:
            raise MCPServerError(f"注册提示失败: {str(e)}")
    
    def unregister_prompt(self, name: str):
        """
        注销提示
        
        Args:
            name: 提示名称
        """
        try:
            if name in self.prompts:
                del self.prompts[name]
            
            if name in self.prompt_handlers:
                del self.prompt_handlers[name]
            
            self.logger.info(f"注销提示: {name}")
        except Exception as e:
            raise MCPServerError(f"注销提示失败: {str(e)}")
    
    async def run(self, host: str = "0.0.0.0", port: int = 8000):
        """
        运行服务器
        
        Args:
            host: 主机地址
            port: 端口号
        """
        try:
            self.logger.info(f"启动MCP服务器: {self.name} v{self.version}")
            self.logger.info(f"监听地址: {host}:{port}")
            
            # 创建初始化选项
            init_options = InitializationOptions(
                serverInfo={
                    "name": self.name,
                    "version": self.version
                },
                capabilities={
                    "tools": {},
                    "resources": {},
                    "resourceTemplates": {},
                    "prompts": {}
                }
            )
            
            # 运行服务器
            await self.server.run_stdio(init_options)
        except Exception as e:
            raise MCPServerError(f"运行服务器失败: {str(e)}")
    
    def get_server_info(self) -> Dict:
        """
        获取服务器信息
        
        Returns:
            服务器信息字典
        """
        return {
            "name": self.name,
            "version": self.version,
            "tools_count": len(self.tools),
            "resources_count": len(self.resources),
            "resource_templates_count": len(self.resource_templates),
            "prompts_count": len(self.prompts)
        }
    
    def get_tools_list(self) -> List[Dict]:
        """
        获取工具列表
        
        Returns:
            工具信息列表
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
            for tool in self.tools.values()
        ]
    
    def get_resources_list(self) -> List[Dict]:
        """
        获取资源列表
        
        Returns:
            资源信息列表
        """
        return [
            {
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mime_type": resource.mimeType
            }
            for resource in self.resources.values()
        ]
    
    def get_prompts_list(self) -> List[Dict]:
        """
        获取提示列表
        
        Returns:
            提示信息列表
        """
        return [
            {
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
            }
            for prompt in self.prompts.values()
        ]