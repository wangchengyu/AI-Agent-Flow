"""
任务执行器模块
负责执行具体的任务
"""

from typing import Dict, Any, List, Callable
from .manager import AgentManager


class TaskExecutor:
    """任务执行器"""

    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager
        self.task_handlers: Dict[str, Callable] = {}

    def register_task_handler(self, task_type: str, handler: Callable):
        """
        注册任务处理器
        
        Args:
            task_type: 任务类型
            handler: 处理器函数
        """
        self.task_handlers[task_type] = handler

    def execute_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行指定类型的任务
        
        Args:
            task_type: 任务类型
            task_data: 任务数据
            
        Returns:
            Dict[str, Any]: 任务执行结果
        """
        handler = self.task_handlers.get(task_type)
        if handler is None:
            raise ValueError(f"No handler registered for task type: {task_type}")
        
        return handler(task_data)

    def execute_task_list(self, task_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        执行任务列表
        
        Args:
            task_list: 任务列表
            
        Returns:
            List[Dict[str, Any]]: 任务执行结果列表
        """
        results = []
        for task in task_list:
            task_type = task.get("type")
            task_data = task.get("data", {})
            try:
                result = self.execute_task(task_type, task_data)
                results.append({
                    "task": task,
                    "result": result,
                    "status": "success"
                })
            except Exception as e:
                results.append({
                    "task": task,
                    "result": str(e),
                    "status": "error"
                })
        
        return results