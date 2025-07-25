"""
MCP模块测试
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.service import MCPService
from mcp.tools.file_manager import read_file, write_file, list_files


def test_mcp_service():
    """测试MCP服务"""
    print("测试MCP服务...")
    
    # 创建MCP服务
    mcp_service = MCPService()
    
    # 定义一个简单的工具函数
    def simple_tool(param1: str, param2: int):
        return f"工具执行结果: {param1} - {param2}"
    
    # 注册工具
    mcp_service.register_tool("simple_tool", simple_tool, "简单工具示例")
    
    # 列出工具
    tools = mcp_service.list_tools()
    assert "simple_tool" in tools, "工具注册失败"
    
    # 获取工具
    tool = mcp_service.get_tool("simple_tool")
    assert tool is not None, "获取工具失败"
    assert tool["description"] == "简单工具示例", "工具描述不正确"
    
    # 执行工具
    result = mcp_service.execute_tool("simple_tool", {"param1": "测试", "param2": 42})
    assert result["success"], "工具执行失败"
    assert result["result"] == "工具执行结果: 测试 - 42", "工具执行结果不正确"
    
    # 执行不存在的工具
    result = mcp_service.execute_tool("nonexistent_tool", {})
    assert not result["success"], "执行不存在的工具应该失败"
    
    print("MCP服务测试通过")


def test_protocol_handler():
    """测试协议处理器"""
    print("测试协议处理器...")
    
    # 创建MCP服务
    mcp_service = MCPService()
    
    # 定义协议处理器
    def test_protocol_handler(data):
        return {"message": "协议处理成功", "data": data}
    
    # 注册协议处理器
    mcp_service.register_protocol_handler("test_protocol", test_protocol_handler)
    
    # 处理协议请求
    result = mcp_service.handle_protocol_request("test_protocol", {"value": 123})
    assert result["success"], "协议处理失败"
    assert result["result"]["message"] == "协议处理成功", "协议处理结果不正确"
    
    # 处理不存在的协议
    result = mcp_service.handle_protocol_request("unknown_protocol", {})
    assert not result["success"], "处理不存在的协议应该失败"
    
    print("协议处理器测试通过")


def test_mcp_request_processing():
    """测试MCP请求处理"""
    print("测试MCP请求处理...")
    
    # 创建MCP服务
    mcp_service = MCPService()
    
    # 定义协议处理器
    def echo_protocol_handler(data):
        return {"echo": data.get("message", "")}
    
    # 注册协议处理器
    mcp_service.register_protocol_handler("echo", echo_protocol_handler)
    
    # 处理有效的JSON请求
    request = json.dumps({
        "protocol": "echo",
        "message": "Hello, MCP!"
    })
    
    response = mcp_service.process_mcp_request(request)
    response_data = json.loads(response)
    
    assert response_data["success"], "MCP请求处理失败"
    assert response_data["result"]["echo"] == "Hello, MCP!", "MCP请求处理结果不正确"
    
    # 处理无效的JSON请求
    response = mcp_service.process_mcp_request("invalid json")
    response_data = json.loads(response)
    
    assert not response_data["success"], "处理无效JSON请求应该失败"
    
    print("MCP请求处理测试通过")


def test_file_manager_tools():
    """测试文件管理工具"""
    print("测试文件管理工具...")
    
    # 测试写入文件
    result = write_file("test_file.txt", "这是一个测试文件内容")
    assert result["success"], "写入文件失败"
    
    # 测试读取文件
    result = read_file("test_file.txt")
    assert result["success"], "读取文件失败"
    assert result["content"] == "这是一个测试文件内容", "文件内容不正确"
    
    # 测试列出文件
    result = list_files(".")
    assert result["success"], "列出文件失败"
    assert len(result["files"]) > 0, "文件列表为空"
    
    # 清理测试文件
    if os.path.exists("test_file.txt"):
        os.remove("test_file.txt")
    
    print("文件管理工具测试通过")


if __name__ == "__main__":
    print("开始MCP模块测试...")
    
    try:
        test_mcp_service()
        test_protocol_handler()
        test_mcp_request_processing()
        test_file_manager_tools()
        
        print("\n所有MCP模块测试通过!")
    except Exception as e:
        print(f"\n测试失败: {e}")
        sys.exit(1)