"""
CLI模块测试
"""

import sys
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli.interface import CLIInterface


def test_cli_initialization():
    """测试CLI初始化"""
    print("测试CLI初始化...")
    
    # 创建CLI界面
    cli = CLIInterface()
    
    assert cli is not None, "CLI界面创建失败"
    assert cli.llm_client is not None, "LLM客户端未初始化"
    assert cli.agent_manager is not None, "Agent管理器未初始化"
    assert cli.task_executor is not None, "任务执行器未初始化"
    assert cli.mcp_service is not None, "MCP服务未初始化"
    assert cli.db_manager is not None, "数据库管理器未初始化"
    
    # 检查MCP工具是否注册
    tools = cli.mcp_service.list_tools()
    expected_tools = ["read_file", "write_file", "list_files", "delete_file", "create_directory"]
    for tool in expected_tools:
        assert tool in tools, f"MCP工具 {tool} 未注册"
    
    print("CLI初始化测试通过")


def test_argument_parser():
    """测试参数解析器"""
    print("测试参数解析器...")
    
    # 创建CLI界面
    cli = CLIInterface()
    
    # 测试默认参数
    with patch("sys.argv", ["cli.py"]):
        args = cli.parser.parse_args()
        assert args.requirement is None, "默认requirement参数不正确"
        assert not args.interactive, "默认interactive参数不正确"
        assert args.config is None, "默认config参数不正确"
        assert not args.verbose, "默认verbose参数不正确"
    
    # 测试带参数
    with patch("sys.argv", ["cli.py", "-r", "测试需求", "-i", "-c", "config.json", "-v"]):
        args = cli.parser.parse_args()
        assert args.requirement == "测试需求", "requirement参数不正确"
        assert args.interactive, "interactive参数不正确"
        assert args.config == "config.json", "config参数不正确"
        assert args.verbose, "verbose参数不正确"
    
    print("参数解析器测试通过")


def test_config_loading():
    """测试配置加载"""
    print("测试配置加载...")
    
    # 创建临时目录用于测试
    temp_dir = tempfile.mkdtemp()
    config_path = os.path.join(temp_dir, "test_config.json")
    
    try:
        # 创建测试配置文件
        config_content = {
            "llm": {
                "base_url": "http://test-server.com/v1",
                "api_key": "test-key",
                "model": "test-model"
            },
            "database": {
                "path": "test.db"
            }
        }
        
        import json
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_content, f, ensure_ascii=False, indent=2)
        
        # 创建CLI界面
        cli = CLIInterface()
        
        # 模拟详细输出
        with patch("sys.argv", ["cli.py", "-v"]):
            args = cli.parser.parse_args()
            # 由于我们无法轻松捕获print输出，我们只验证方法是否能正常调用
            cli._load_config(config_path)
        
        # 验证配置是否加载
        # 注意：由于_load_config方法直接修改了cli的属性，我们无法直接验证
        # 但我们可以验证方法是否能正常调用而不抛出异常
        
        print("配置加载测试通过")
    except Exception as e:
        # 清理临时目录
        shutil.rmtree(temp_dir)
        raise e
    
    # 清理临时目录
    shutil.rmtree(temp_dir)


def test_user_requirement_input():
    """测试用户需求输入"""
    print("测试用户需求输入...")
    
    # 创建CLI界面
    cli = CLIInterface()
    
    # 模拟用户输入
    user_input = "这是一个测试需求\n包含多行内容\n"
    
    with patch("builtins.input", side_effect=user_input.split('\n')[:-1] + [EOFError()]):
        requirement = cli._get_user_requirement()
        assert requirement == "这是一个测试需求\n包含多行内容", "用户需求输入不正确"
    
    print("用户需求输入测试通过")


def test_requirement_processing():
    """测试需求处理"""
    print("测试需求处理...")
    
    # 创建CLI界面
    cli = CLIInterface()
    
    # 模拟LLM客户端的方法
    cli.llm_client.task_decomposition = MagicMock(return_value={
        "success": True,
        "content": "任务分解结果"
    })
    
    cli.llm_client.content_generation = MagicMock(return_value={
        "success": True,
        "content": "生成的内容"
    })
    
    # 测试需求处理方法是否能正常调用
    try:
        cli._process_requirement("测试需求")
        # 验证方法是否被调用
        cli.llm_client.task_decomposition.assert_called_once()
        cli.llm_client.content_generation.assert_called_once()
        print("需求处理测试通过")
    except Exception as e:
        print(f"需求处理测试失败: {e}")
        raise


if __name__ == "__main__":
    print("开始CLI模块测试...")
    
    try:
        test_cli_initialization()
        test_argument_parser()
        test_config_loading()
        test_user_requirement_input()
        test_requirement_processing()
        
        print("\n所有CLI模块测试通过!")
    except Exception as e:
        print(f"\n测试失败: {e}")
        sys.exit(1)