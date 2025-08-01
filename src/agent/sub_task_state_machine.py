"""
子任务状态机

负责管理子任务的状态转换，
包括状态定义、转换规则和状态事件处理。
"""

import asyncio
import json
import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable

from ..database.task_history_manager import TaskHistoryManager
from ..utils.exceptions import StateMachineError


class SubTaskState(Enum):
    """子任务状态枚举"""
    PENDING = "pending"       # 待执行
    READY = "ready"         # 准备执行
    RUNNING = "running"     # 执行中
    PAUSED = "paused"       # 已暂停
    COMPLETED = "completed" # 已完成
    FAILED = "failed"       # 失败
    STOPPED = "stopped"     # 已停止
    SKIPPED = "skipped"     # 已跳过
    RETRYING = "retrying"   # 重试中


class SubTaskEvent(Enum):
    """子任务事件枚举"""
    START = "start"           # 开始执行
    PAUSE = "pause"           # 暂停执行
    RESUME = "resume"         # 恢复执行
    COMPLETE = "complete"     # 完成执行
    FAIL = "fail"             # 执行失败
    STOP = "stop"             # 停止执行
    SKIP = "skip"             # 跳过执行
    RETRY = "retry"           # 重试执行


class SubTaskStateMachine:
    """子任务状态机，负责管理子任务的状态转换"""
    
    def __init__(self, db_manager):
        """
        初始化子任务状态机
        
        Args:
            db_manager: 数据库管理器
        """
        self.db_manager = db_manager
        self.task_history_manager = TaskHistoryManager(db_manager)
        
        # 状态转换规则
        self.transitions = {
            # 从 PENDING 状态的转换
            SubTaskState.PENDING: {
                SubTaskEvent.START: SubTaskState.READY,
                SubTaskEvent.SKIP: SubTaskState.SKIPPED
            },
            
            # 从 READY 状态的转换
            SubTaskState.READY: {
                SubTaskEvent.START: SubTaskState.RUNNING,
                SubTaskEvent.SKIP: SubTaskState.SKIPPED
            },
            
            # 从 RUNNING 状态的转换
            SubTaskState.RUNNING: {
                SubTaskEvent.PAUSE: SubTaskState.PAUSED,
                SubTaskEvent.COMPLETE: SubTaskState.COMPLETED,
                SubTaskEvent.FAIL: SubTaskState.FAILED,
                SubTaskEvent.STOP: SubTaskState.STOPPED
            },
            
            # 从 PAUSED 状态的转换
            SubTaskState.PAUSED: {
                SubTaskEvent.RESUME: SubTaskState.READY,
                SubTaskEvent.STOP: SubTaskState.STOPPED
            },
            
            # 从 FAILED 状态的转换
            SubTaskState.FAILED: {
                SubTaskEvent.RETRY: SubTaskState.RETRYING,
                SubTaskEvent.STOP: SubTaskState.STOPPED
            },
            
            # 从 RETRYING 状态的转换
            SubTaskState.RETRYING: {
                SubTaskEvent.START: SubTaskState.READY,
                SubTaskEvent.STOP: SubTaskState.STOPPED
            },
            
            # 从 COMPLETED、STOPPED、SKIPPED 状态的转换
            # 这些是最终状态，不允许转换
        }
        
        # 状态转换处理器
        self.transition_handlers = {
            (SubTaskState.PENDING, SubTaskEvent.START): self._handle_pending_to_ready,
            (SubTaskState.PENDING, SubTaskEvent.SKIP): self._handle_pending_to_skipped,
            
            (SubTaskState.READY, SubTaskEvent.START): self._handle_ready_to_running,
            (SubTaskState.READY, SubTaskEvent.SKIP): self._handle_ready_to_skipped,
            
            (SubTaskState.RUNNING, SubTaskEvent.PAUSE): self._handle_running_to_paused,
            (SubTaskState.RUNNING, SubTaskEvent.COMPLETE): self._handle_running_to_completed,
            (SubTaskState.RUNNING, SubTaskEvent.FAIL): self._handle_running_to_failed,
            (SubTaskState.RUNNING, SubTaskEvent.STOP): self._handle_running_to_stopped,
            
            (SubTaskState.PAUSED, SubTaskEvent.RESUME): self._handle_paused_to_ready,
            (SubTaskState.PAUSED, SubTaskEvent.STOP): self._handle_paused_to_stopped,
            
            (SubTaskState.FAILED, SubTaskEvent.RETRY): self._handle_failed_to_retrying,
            (SubTaskState.FAILED, SubTaskEvent.STOP): self._handle_failed_to_stopped,
            
            (SubTaskState.RETRYING, SubTaskEvent.START): self._handle_retrying_to_ready,
            (SubTaskState.RETRYING, SubTaskEvent.STOP): self._handle_retrying_to_stopped
        }
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """初始化子任务状态机"""
        try:
            self.logger.info("子任务状态机初始化完成")
        except Exception as e:
            raise StateMachineError(f"初始化子任务状态机失败: {str(e)}")
    
    async def transition(self, sub_task_id: str, event: SubTaskEvent, 
                        data: Optional[Dict] = None) -> Dict:
        """
        执行状态转换
        
        Args:
            sub_task_id: 子任务ID
            event: 事件
            data: 附加数据
            
        Returns:
            状态转换结果
        """
        try:
            # 获取子任务当前状态
            sub_task = await self.task_history_manager.get_sub_task(sub_task_id)
            if not sub_task:
                raise StateMachineError(f"子任务 {sub_task_id} 不存在")
            
            current_state = SubTaskState(sub_task["status"])
            
            # 检查转换是否有效
            if current_state not in self.transitions:
                raise StateMachineError(f"状态 {current_state.value} 不允许任何转换")
            
            if event not in self.transitions[current_state]:
                raise StateMachineError(f"从状态 {current_state.value} 不允许通过事件 {event.value} 转换")
            
            # 获取目标状态
            target_state = self.transitions[current_state][event]
            
            # 执行状态转换处理器
            handler_key = (current_state, event)
            if handler_key in self.transition_handlers:
                handler_result = await self.transition_handlers[handler_key](
                    sub_task_id, sub_task, data or {}
                )
            else:
                handler_result = {}
            
            # 更新子任务状态
            await self.task_history_manager.update_sub_task_status(
                sub_task_id=sub_task_id,
                status=target_state.value,
                result=data
            )
            
            # 记录状态转换
            await self.task_history_manager.create_state_transition(
                sub_task_id=sub_task_id,
                from_state=current_state.value,
                to_state=target_state.value,
                event=event.value,
                data=data or {}
            )
            
            # 返回转换结果
            result = {
                "sub_task_id": sub_task_id,
                "from_state": current_state.value,
                "to_state": target_state.value,
                "event": event.value,
                "timestamp": time.time(),
                "handler_result": handler_result
            }
            
            self.logger.info(f"子任务 {sub_task_id} 状态转换: {current_state.value} -> {target_state.value} (事件: {event.value})")
            return result
        except Exception as e:
            raise StateMachineError(f"执行状态转换失败: {str(e)}")
    
    async def _handle_pending_to_ready(self, sub_task_id: str, sub_task: Dict, data: Dict) -> Dict:
        """
        处理从 PENDING 到 READY 的转换
        
        Args:
            sub_task_id: 子任务ID
            sub_task: 子任务信息
            data: 附加数据
            
        Returns:
            处理结果
        """
        try:
            # 检查依赖是否满足
            dependencies = sub_task.get("dependencies", [])
            
            if dependencies:
                # 检查所有依赖是否已完成
                for dep_id in dependencies:
                    dep_task = await self.task_history_manager.get_sub_task(dep_id)
                    if not dep_task or dep_task["status"] not in ["completed", "skipped"]:
                        raise StateMachineError(f"依赖 {dep_id} 未满足，无法开始执行")
            
            return {
                "dependencies_checked": True,
                "ready_to_execute": True
            }
        except Exception as e:
            raise StateMachineError(f"处理 PENDING 到 READY 转换失败: {str(e)}")
    
    async def _handle_pending_to_skipped(self, sub_task_id: str, sub_task: Dict, data: Dict) -> Dict:
        """
        处理从 PENDING 到 SKIPPED 的转换
        
        Args:
            sub_task_id: 子任务ID
            sub_task: 子任务信息
            data: 附加数据
            
        Returns:
            处理结果
        """
        try:
            reason = data.get("reason", "未指定原因")
            
            return {
                "skip_reason": reason,
                "skipped_at": time.time()
            }
        except Exception as e:
            raise StateMachineError(f"处理 PENDING 到 SKIPPED 转换失败: {str(e)}")
    
    async def _handle_ready_to_running(self, sub_task_id: str, sub_task: Dict, data: Dict) -> Dict:
        """
        处理从 READY 到 RUNNING 的转换
        
        Args:
            sub_task_id: 子任务ID
            sub_task: 子任务信息
            data: 附加数据
            
        Returns:
            处理结果
        """
        try:
            # 记录开始执行时间
            start_time = time.time()
            
            return {
                "execution_started": True,
                "start_time": start_time
            }
        except Exception as e:
            raise StateMachineError(f"处理 READY 到 RUNNING 转换失败: {str(e)}")
    
    async def _handle_ready_to_skipped(self, sub_task_id: str, sub_task: Dict, data: Dict) -> Dict:
        """
        处理从 READY 到 SKIPPED 的转换
        
        Args:
            sub_task_id: 子任务ID
            sub_task: 子任务信息
            data: 附加数据
            
        Returns:
            处理结果
        """
        try:
            reason = data.get("reason", "未指定原因")
            
            return {
                "skip_reason": reason,
                "skipped_at": time.time()
            }
        except Exception as e:
            raise StateMachineError(f"处理 READY 到 SKIPPED 转换失败: {str(e)}")
    
    async def _handle_running_to_paused(self, sub_task_id: str, sub_task: Dict, data: Dict) -> Dict:
        """
        处理从 RUNNING 到 PAUSED 的转换
        
        Args:
            sub_task_id: 子任务ID
            sub_task: 子任务信息
            data: 附加数据
            
        Returns:
            处理结果
        """
        try:
            # 记录暂停时间
            pause_time = time.time()
            
            # 计算已执行时间
            start_time = sub_task.get("start_time", time.time())
            execution_time = pause_time - start_time
            
            return {
                "execution_paused": True,
                "pause_time": pause_time,
                "execution_time": execution_time
            }
        except Exception as e:
            raise StateMachineError(f"处理 RUNNING 到 PAUSED 转换失败: {str(e)}")
    
    async def _handle_running_to_completed(self, sub_task_id: str, sub_task: Dict, data: Dict) -> Dict:
        """
        处理从 RUNNING 到 COMPLETED 的转换
        
        Args:
            sub_task_id: 子任务ID
            sub_task: 子任务信息
            data: 附加数据
            
        Returns:
            处理结果
        """
        try:
            # 记录完成时间
            end_time = time.time()
            
            # 计算执行时间
            start_time = sub_task.get("start_time", time.time())
            execution_time = end_time - start_time
            
            return {
                "execution_completed": True,
                "end_time": end_time,
                "execution_time": execution_time,
                "result": data.get("result", {})
            }
        except Exception as e:
            raise StateMachineError(f"处理 RUNNING 到 COMPLETED 转换失败: {str(e)}")
    
    async def _handle_running_to_failed(self, sub_task_id: str, sub_task: Dict, data: Dict) -> Dict:
        """
        处理从 RUNNING 到 FAILED 的转换
        
        Args:
            sub_task_id: 子任务ID
            sub_task: 子任务信息
            data: 附加数据
            
        Returns:
            处理结果
        """
        try:
            # 记录失败时间
            fail_time = time.time()
            
            # 计算执行时间
            start_time = sub_task.get("start_time", time.time())
            execution_time = fail_time - start_time
            
            # 获取错误信息
            error = data.get("error", "未知错误")
            
            return {
                "execution_failed": True,
                "fail_time": fail_time,
                "execution_time": execution_time,
                "error": error
            }
        except Exception as e:
            raise StateMachineError(f"处理 RUNNING 到 FAILED 转换失败: {str(e)}")
    
    async def _handle_running_to_stopped(self, sub_task_id: str, sub_task: Dict, data: Dict) -> Dict:
        """
        处理从 RUNNING 到 STOPPED 的转换
        
        Args:
            sub_task_id: 子任务ID
            sub_task: 子任务信息
            data: 附加数据
            
        Returns:
            处理结果
        """
        try:
            # 记录停止时间
            stop_time = time.time()
            
            # 计算执行时间
            start_time = sub_task.get("start_time", time.time())
            execution_time = stop_time - start_time
            
            # 获取停止原因
            reason = data.get("reason", "未指定原因")
            
            return {
                "execution_stopped": True,
                "stop_time": stop_time,
                "execution_time": execution_time,
                "stop_reason": reason
            }
        except Exception as e:
            raise StateMachineError(f"处理 RUNNING 到 STOPPED 转换失败: {str(e)}")
    
    async def _handle_paused_to_ready(self, sub_task_id: str, sub_task: Dict, data: Dict) -> Dict:
        """
        处理从 PAUSED 到 READY 的转换
        
        Args:
            sub_task_id: 子任务ID
            sub_task: 子任务信息
            data: 附加数据
            
        Returns:
            处理结果
        """
        try:
            # 记录恢复时间
            resume_time = time.time()
            
            return {
                "execution_resumed": True,
                "resume_time": resume_time
            }
        except Exception as e:
            raise StateMachineError(f"处理 PAUSED 到 READY 转换失败: {str(e)}")
    
    async def _handle_paused_to_stopped(self, sub_task_id: str, sub_task: Dict, data: Dict) -> Dict:
        """
        处理从 PAUSED 到 STOPPED 的转换
        
        Args:
            sub_task_id: 子任务ID
            sub_task: 子任务信息
            data: 附加数据
            
        Returns:
            处理结果
        """
        try:
            # 记录停止时间
            stop_time = time.time()
            
            # 获取停止原因
            reason = data.get("reason", "未指定原因")
            
            return {
                "execution_stopped": True,
                "stop_time": stop_time,
                "stop_reason": reason
            }
        except Exception as e:
            raise StateMachineError(f"处理 PAUSED 到 STOPPED 转换失败: {str(e)}")
    
    async def _handle_failed_to_retrying(self, sub_task_id: str, sub_task: Dict, data: Dict) -> Dict:
        """
        处理从 FAILED 到 RETRYING 的转换
        
        Args:
            sub_task_id: 子任务ID
            sub_task: 子任务信息
            data: 附加数据
            
        Returns:
            处理结果
        """
        try:
            # 记录重试时间
            retry_time = time.time()
            
            # 获取重试原因
            reason = data.get("reason", "未指定原因")
            
            # 获取重试次数
            retry_count = data.get("retry_count", 1)
            
            return {
                "retry_initiated": True,
                "retry_time": retry_time,
                "retry_reason": reason,
                "retry_count": retry_count
            }
        except Exception as e:
            raise StateMachineError(f"处理 FAILED 到 RETRYING 转换失败: {str(e)}")
    
    async def _handle_failed_to_stopped(self, sub_task_id: str, sub_task: Dict, data: Dict) -> Dict:
        """
        处理从 FAILED 到 STOPPED 的转换
        
        Args:
            sub_task_id: 子任务ID
            sub_task: 子任务信息
            data: 附加数据
            
        Returns:
            处理结果
        """
        try:
            # 记录停止时间
            stop_time = time.time()
            
            # 获取停止原因
            reason = data.get("reason", "未指定原因")
            
            return {
                "execution_stopped": True,
                "stop_time": stop_time,
                "stop_reason": reason
            }
        except Exception as e:
            raise StateMachineError(f"处理 FAILED 到 STOPPED 转换失败: {str(e)}")
    
    async def _handle_retrying_to_ready(self, sub_task_id: str, sub_task: Dict, data: Dict) -> Dict:
        """
        处理从 RETRYING 到 READY 的转换
        
        Args:
            sub_task_id: 子任务ID
            sub_task: 子任务信息
            data: 附加数据
            
        Returns:
            处理结果
        """
        try:
            # 记录重试准备时间
            ready_time = time.time()
            
            return {
                "retry_prepared": True,
                "ready_time": ready_time
            }
        except Exception as e:
            raise StateMachineError(f"处理 RETRYING 到 READY 转换失败: {str(e)}")
    
    async def _handle_retrying_to_stopped(self, sub_task_id: str, sub_task: Dict, data: Dict) -> Dict:
        """
        处理从 RETRYING 到 STOPPED 的转换
        
        Args:
            sub_task_id: 子任务ID
            sub_task: 子任务信息
            data: 附加数据
            
        Returns:
            处理结果
        """
        try:
            # 记录停止时间
            stop_time = time.time()
            
            # 获取停止原因
            reason = data.get("reason", "未指定原因")
            
            return {
                "execution_stopped": True,
                "stop_time": stop_time,
                "stop_reason": reason
            }
        except Exception as e:
            raise StateMachineError(f"处理 RETRYING 到 STOPPED 转换失败: {str(e)}")
    
    async def get_sub_task_state(self, sub_task_id: str) -> Dict:
        """
        获取子任务状态
        
        Args:
            sub_task_id: 子任务ID
            
        Returns:
            子任务状态信息
        """
        try:
            # 获取子任务信息
            sub_task = await self.task_history_manager.get_sub_task(sub_task_id)
            if not sub_task:
                raise StateMachineError(f"子任务 {sub_task_id} 不存在")
            
            # 获取状态转换历史
            transitions = await self.task_history_manager.get_state_transitions(sub_task_id)
            
            return {
                "sub_task_id": sub_task_id,
                "current_state": sub_task["status"],
                "transitions": transitions,
                "created_at": sub_task["created_at"],
                "start_time": sub_task.get("start_time"),
                "end_time": sub_task.get("end_time")
            }
        except Exception as e:
            raise StateMachineError(f"获取子任务状态失败: {str(e)}")
    
    async def get_allowed_transitions(self, sub_task_id: str) -> List[Dict]:
        """
        获取子任务允许的状态转换
        
        Args:
            sub_task_id: 子任务ID
            
        Returns:
            允许的状态转换列表
        """
        try:
            # 获取子任务当前状态
            sub_task = await self.task_history_manager.get_sub_task(sub_task_id)
            if not sub_task:
                raise StateMachineError(f"子任务 {sub_task_id} 不存在")
            
            current_state = SubTaskState(sub_task["status"])
            
            # 获取允许的转换
            allowed_transitions = []
            
            if current_state in self.transitions:
                for event, target_state in self.transitions[current_state].items():
                    allowed_transitions.append({
                        "event": event.value,
                        "from_state": current_state.value,
                        "to_state": target_state.value
                    })
            
            return allowed_transitions
        except Exception as e:
            raise StateMachineError(f"获取允许的状态转换失败: {str(e)}")
    
    async def add_transition_handler(self, from_state: SubTaskState, event: SubTaskEvent, 
                                   handler: Callable) -> bool:
        """
        添加状态转换处理器
        
        Args:
            from_state: 源状态
            event: 事件
            handler: 处理器函数
            
        Returns:
            添加是否成功
        """
        try:
            self.transition_handlers[(from_state, event)] = handler
            self.logger.info(f"添加状态转换处理器: {from_state.value} -> {event.value}")
            return True
        except Exception as e:
            raise StateMachineError(f"添加状态转换处理器失败: {str(e)}")
    
    async def get_state_statistics(self, days: int = 30) -> Dict:
        """
        获取状态统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        try:
            # 获取状态转换统计
            stats = await self.task_history_manager.get_state_transition_statistics(days)
            
            return stats
        except Exception as e:
            raise StateMachineError(f"获取状态统计信息失败: {str(e)}")