import os
import json
from typing import Dict, Any, List, Callable, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import inspect

app = FastAPI()

class ToolInput(BaseModel):
    params: Dict[str, Any]

class ToolResult(BaseModel):
    success: bool
    content: Any
    error: Optional[str] = None

class MCPRegistry:
    def __init__(self):
        self.tools = {}
        
    def register(self, tool_func: Callable):
        """注册工具函数"""
        tool_name = tool_func.__name__
        self.tools[tool_name] = {
            'function': tool_func,
            'description': tool_func.__doc__ or "",
            'input_schema': self._get_input_schema(tool_func)
        }
        return tool_func
        
    def _get_input_schema(self, func: Callable) -> Dict:
        """获取工具函数的输入参数schema"""
        params = inspect.signature(func).parameters
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for name, param in params.items():
            if name == 'self':
                continue
                
            param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
            schema['properties'][name] = {"type": param_type.__name__}
            
            if param.default == inspect.Parameter.empty:
                schema['required'].append(name)
                
        return schema
        
    def get_tool(self, name: str) -> Optional[Dict]:
        """获取指定工具"""
        return self.tools.get(name)
        
    def list_tools(self) -> List[Dict]:
        """列出所有注册的工具"""
        return [{
            'name': name,
            'description': info['description'],
            'input_schema': info['input_schema']
        } for name, info in self.tools.items()]

class ToolExecutor:
    def __init__(self, registry: MCPRegistry):
        self.registry = registry
        
    def execute(self, tool_name: str, params: Dict) -> ToolResult:
        """执行工具调用"""
        tool_info = self.registry.get_tool(tool_name)
        if not tool_info:
            return ToolResult(success=False, content=None, error=f"Tool {tool_name} not found")
            
        try:
            result = tool_info['function'](**params)
            return ToolResult(success=True, content=result)
        except Exception as e:
            return ToolResult(success=False, content=None, error=str(e))

# 初始化工具注册表
registry = MCPRegistry()
executor = ToolExecutor(registry)

# 注册核心工具
@registry.register
def list_files(confirm: bool) -> List[str]:
    """获取当前目录文件列表（需用户确认）"""
    if confirm:
        return os.listdir()
    return []

@registry.register
def read_file(file_path: str) -> str:
    """读取文件内容"""
    with open(file_path, 'r') as f:
        return f.read()

# API端点
@app.post("/tools/{tool_name}")
def call_tool(tool_name: str, input: ToolInput):
    result = executor.execute(tool_name, input.params)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result

@app.get("/tools")
def list_tools():
    return registry.list_tools()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)