"""
LLM模块测试
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.client import LLMClient


def test_llm_client_initialization():
    """测试LLM客户端初始化"""
    print("测试LLM客户端初始化...")
    
    # 创建LLM客户端
    llm_client = LLMClient()
    
    assert llm_client is not None, "LLM客户端创建失败"
    assert llm_client.model == "gpt-3.5-turbo", "默认模型不正确"
    
    # 使用自定义配置创建LLM客户端
    llm_client = LLMClient(
        base_url="http://test-server.com/v1",
        api_key="test-key",
        model="test-model"
    )
    
    assert llm_client.base_url == "http://test-server.com/v1", "基础URL不正确"
    assert llm_client.api_key == "test-key", "API密钥不正确"
    assert llm_client.model == "test-model", "模型名称不正确"
    
    print("LLM客户端初始化测试通过")


def test_llm_client_config():
    """测试LLM客户端配置"""
    print("测试LLM客户端配置...")
    
    # 创建LLM客户端
    llm_client = LLMClient()
    
    # 设置配置
    llm_client.set_config(
        base_url="http://new-server.com/v1",
        api_key="new-key",
        model="new-model"
    )
    
    assert llm_client.base_url == "http://new-server.com/v1", "基础URL更新失败"
    assert llm_client.api_key == "new-key", "API密钥更新失败"
    assert llm_client.model == "new-model", "模型名称更新失败"
    
    # 部分更新配置
    llm_client.set_config(model="partial-update-model")
    
    assert llm_client.model == "partial-update-model", "部分配置更新失败"
    assert llm_client.base_url == "http://new-server.com/v1", "基础URL不应改变"
    
    print("LLM客户端配置测试通过")


def test_task_decomposition():
    """测试任务分解功能"""
    print("测试任务分解功能...")
    
    # 创建LLM客户端
    llm_client = LLMClient()
    
    # 由于我们没有实际的API密钥，这里只测试方法是否存在且能正常调用
    # 实际测试需要有效的API密钥
    assert hasattr(llm_client, "task_decomposition"), "缺少任务分解方法"
    
    # 检查方法签名
    import inspect
    sig = inspect.signature(llm_client.task_decomposition)
    assert "requirement" in sig.parameters, "任务分解方法缺少requirement参数"
    
    print("任务分解功能测试通过")


def test_content_generation():
    """测试内容生成功能"""
    print("测试内容生成功能...")
    
    # 创建LLM客户端
    llm_client = LLMClient()
    
    # 检查方法是否存在
    assert hasattr(llm_client, "content_generation"), "缺少内容生成方法"
    
    # 检查方法签名
    import inspect
    sig = inspect.signature(llm_client.content_generation)
    assert "context" in sig.parameters, "内容生成方法缺少context参数"
    assert "task" in sig.parameters, "内容生成方法缺少task参数"
    
    print("内容生成功能测试通过")


def test_result_validation():
    """测试结果验证功能"""
    print("测试结果验证功能...")
    
    # 创建LLM客户端
    llm_client = LLMClient()
    
    # 检查方法是否存在
    assert hasattr(llm_client, "result_validation"), "缺少结果验证方法"
    
    # 检查方法签名
    import inspect
    sig = inspect.signature(llm_client.result_validation)
    assert "result" in sig.parameters, "结果验证方法缺少result参数"
    assert "requirement" in sig.parameters, "结果验证方法缺少requirement参数"
    
    print("结果验证功能测试通过")


def test_result_integration():
    """测试结果整合功能"""
    print("测试结果整合功能...")
    
    # 创建LLM客户端
    llm_client = LLMClient()
    
    # 检查方法是否存在
    assert hasattr(llm_client, "result_integration"), "缺少结果整合方法"
    
    # 检查方法签名
    import inspect
    sig = inspect.signature(llm_client.result_integration)
    assert "results" in sig.parameters, "结果整合方法缺少results参数"
    
    print("结果整合功能测试通过")


if __name__ == "__main__":
    print("开始LLM模块测试...")
    
    try:
        test_llm_client_initialization()
        test_llm_client_config()
        test_task_decomposition()
        test_content_generation()
        test_result_validation()
        test_result_integration()
        
        print("\n所有LLM模块测试通过!")
    except Exception as e:
        print(f"\n测试失败: {e}")
        sys.exit(1)