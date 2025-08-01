"""
Agent流程管理模块

负责管理多智能体协作、任务分解、子任务执行和结果验证的全流程。
基于CrewAI框架实现，提供灵活的任务流水线管理能力。
"""

from .agent_manager import AgentManager
from .task_decomposer import TaskDecomposer
from .subtask_manager import SubTaskManager
from .info_gathering_loop import InfoGatheringLoop
from .validation_module import ValidationModule
from .subtask_state import SubTaskState

__all__ = [
    "AgentManager",
    "TaskDecomposer", 
    "SubTaskManager",
    "InfoGatheringLoop",
    "ValidationModule",
    "SubTaskState"
]