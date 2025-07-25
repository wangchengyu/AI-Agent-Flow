"""
Agent模块测试
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.manager import AgentManager
from agent.executor import TaskExecutor


def test_agent_manager():
    """测试Agent管理器"""
    print("测试Agent管理器...")
    
    # 创建Agent管理器
    agent_manager = AgentManager()
    
    # 创建一个测试Agent
    agent = agent_manager.create_agent(
        name="测试Agent",
        role="测试角色",
        goal="测试目标",
        backstory="测试背景故事"
    )
    
    assert agent is not None, "Agent创建失败"
    assert agent.name == "测试Agent", "Agent名称不正确"
    
    # 获取Agent
    retrieved_agent = agent_manager.get_agent("测试Agent")
    assert retrieved_agent is not None, "获取Agent失败"
    assert retrieved_agent.name == "测试Agent", "获取的Agent名称不正确"
    
    print("Agent管理器测试通过")


def test_task_creation():
    """测试任务创建"""
    print("测试任务创建...")
    
    # 创建Agent管理器
    agent_manager = AgentManager()
    
    # 创建一个测试Agent
    agent = agent_manager.create_agent(
        name="任务测试Agent",
        role="任务测试角色",
        goal="任务测试目标",
        backstory="任务测试背景故事"
    )
    
    # 创建任务
    task = agent_manager.create_task(
        description="这是一个测试任务",
        agent=agent,
        expected_output="任务完成"
    )
    
    assert task is not None, "任务创建失败"
    assert task.description == "这是一个测试任务", "任务描述不正确"
    
    print("任务创建测试通过")


def test_task_executor():
    """测试任务执行器"""
    print("测试任务执行器...")
    
    # 创建Agent管理器和任务执行器
    agent_manager = AgentManager()
    task_executor = TaskExecutor(agent_manager)
    
    # 定义一个简单的任务处理函数
    def simple_task_handler(task_data):
        return {
            "result": "任务处理成功",
            "data": task_data
        }
    
    # 注册任务处理器
    task_executor.register_task_handler("simple_task", simple_task_handler)
    
    # 执行任务
    result = task_executor.execute_task("simple_task", {"value": 42})
    
    assert result is not None, "任务执行失败"
    assert result["result"] == "任务处理成功", "任务执行结果不正确"
    assert result["data"]["value"] == 42, "任务数据不正确"
    
    print("任务执行器测试通过")


def test_task_list_execution():
    """测试任务列表执行"""
    print("测试任务列表执行...")
    
    # 创建Agent管理器和任务执行器
    agent_manager = AgentManager()
    task_executor = TaskExecutor(agent_manager)
    
    # 定义任务处理函数
    def add_task_handler(task_data):
        a = task_data.get("a", 0)
        b = task_data.get("b", 0)
        return {"result": a + b}
    
    def multiply_task_handler(task_data):
        a = task_data.get("a", 0)
        b = task_data.get("b", 0)
        return {"result": a * b}
    
    # 注册任务处理器
    task_executor.register_task_handler("add", add_task_handler)
    task_executor.register_task_handler("multiply", multiply_task_handler)
    
    # 创建任务列表
    task_list = [
        {"type": "add", "data": {"a": 2, "b": 3}},
        {"type": "multiply", "data": {"a": 4, "b": 5}},
        {"type": "unknown", "data": {"x": 1}}  # 这个任务会失败
    ]
    
    # 执行任务列表
    results = task_executor.execute_task_list(task_list)
    
    assert len(results) == 3, "任务列表执行结果数量不正确"
    assert results[0]["status"] == "success", "第一个任务执行失败"
    assert results[0]["result"]["result"] == 5, "第一个任务执行结果不正确"
    assert results[1]["status"] == "success", "第二个任务执行失败"
    assert results[1]["result"]["result"] == 20, "第二个任务执行结果不正确"
    assert results[2]["status"] == "error", "第三个任务应该失败但没有"
    
    print("任务列表执行测试通过")


if __name__ == "__main__":
    print("开始Agent模块测试...")
    
    try:
        test_agent_manager()
        test_task_creation()
        test_task_executor()
        test_task_list_execution()
        
        print("\n所有Agent模块测试通过!")
    except Exception as e:
        print(f"\n测试失败: {e}")
        sys.exit(1)