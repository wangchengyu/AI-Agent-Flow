"""
Agent管理器

负责管理Agent的整个生命周期，包括任务接收、分解、执行、
验证和结果输出等功能。
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable

from ..database.task_history_manager import TaskHistoryManager
from ..database.user_manager import UserManager
from ..rag.knowledge_manager import KnowledgeManager
from ..mcp_tools.tool_manager import ToolManager
from .task_decomposer import TaskDecomposer
from .sub_task_manager import SubTaskManager
from .info_gathering_loop import InfoGatheringLoop
from .validation_module import ValidationModule
from ..utils.exceptions import AgentManagerError


class AgentManager:
    """Agent管理器，负责管理Agent的整个生命周期"""
    
    def __init__(self, db_manager, user_manager: UserManager, 
                 knowledge_manager: KnowledgeManager, tool_manager: ToolManager):
        """
        初始化Agent管理器
        
        Args:
            db_manager: 数据库管理器
            user_manager: 用户管理器
            knowledge_manager: 知识管理器
            tool_manager: 工具管理器
        """
        self.db_manager = db_manager
        self.user_manager = user_manager
        self.knowledge_manager = knowledge_manager
        self.tool_manager = tool_manager
        
        # 初始化子模块
        self.task_history_manager = TaskHistoryManager(db_manager)
        self.task_decomposer = TaskDecomposer(db_manager, knowledge_manager)
        self.sub_task_manager = SubTaskManager(db_manager, tool_manager)
        self.info_gathering_loop = InfoGatheringLoop(db_manager, knowledge_manager)
        self.validation_module = ValidationModule(db_manager, knowledge_manager)
        
        # Agent状态
        self.status = "idle"  # idle, running, paused, stopped
        self.current_task_id = None
        self.current_user_id = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """初始化Agent管理器"""
        try:
            # 初始化子模块
            await self.task_decomposer.initialize()
            await self.sub_task_manager.initialize()
            await self.info_gathering_loop.initialize()
            await self.validation_module.initialize()
            
            self.logger.info("Agent管理器初始化完成")
        except Exception as e:
            raise AgentManagerError(f"初始化Agent管理器失败: {str(e)}")
    
    async def process_task(self, task_description: str, user_id: Optional[int] = None,
                          context: Optional[Dict] = None) -> Dict:
        """
        处理任务
        
        Args:
            task_description: 任务描述
            user_id: 用户ID
            context: 任务上下文
            
        Returns:
            任务处理结果
        """
        try:
            # 检查Agent状态
            if self.status != "idle":
                raise AgentManagerError(f"Agent当前状态为 {self.status}，无法处理新任务")
            
            # 更新Agent状态
            self.status = "running"
            
            # 记录任务开始
            task_id = await self.task_history_manager.create_task(
                description=task_description,
                user_id=user_id,
                context=context or {}
            )
            
            self.current_task_id = task_id
            self.current_user_id = user_id
            
            self.logger.info(f"开始处理任务 {task_id}: {task_description}")
            
            # 执行任务处理流程
            try:
                # 1. 分解任务
                sub_tasks = await self.task_decomposer.decompose_task(
                    task_id=task_id,
                    task_description=task_description,
                    context=context or {}
                )
                
                # 2. 执行子任务
                results = await self.sub_task_manager.execute_sub_tasks(
                    task_id=task_id,
                    sub_tasks=sub_tasks,
                    user_id=user_id
                )
                
                # 3. 信息补充循环
                final_results = await self.info_gathering_loop.process_results(
                    task_id=task_id,
                    results=results,
                    user_id=user_id
                )
                
                # 4. 验证结果
                validation_result = await self.validation_module.validate_results(
                    task_id=task_id,
                    results=final_results,
                    user_id=user_id
                )
                
                # 5. 生成最终结果
                final_result = {
                    "task_id": task_id,
                    "task_description": task_description,
                    "status": "completed" if validation_result["is_valid"] else "needs_review",
                    "results": final_results,
                    "validation": validation_result,
                    "execution_time": time.time() - self.task_history_manager.tasks[task_id]["start_time"]
                }
                
                # 记录任务完成
                await self.task_history_manager.update_task_status(
                    task_id=task_id,
                    status="completed" if validation_result["is_valid"] else "needs_review",
                    result=final_result
                )
                
                self.logger.info(f"任务 {task_id} 处理完成")
                return final_result
            except Exception as e:
                # 记录任务失败
                await self.task_history_manager.update_task_status(
                    task_id=task_id,
                    status="failed",
                    result={"error": str(e)}
                )
                
                self.logger.error(f"任务 {task_id} 处理失败: {str(e)}")
                raise AgentManagerError(f"处理任务失败: {str(e)}")
            finally:
                # 重置Agent状态
                self.status = "idle"
                self.current_task_id = None
                self.current_user_id = None
        except Exception as e:
            raise AgentManagerError(f"处理任务失败: {str(e)}")
    
    async def pause_task(self, task_id: int) -> bool:
        """
        暂停任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            暂停是否成功
        """
        try:
            # 检查任务是否存在
            task = await self.task_history_manager.get_task(task_id)
            if not task:
                raise AgentManagerError(f"任务 {task_id} 不存在")
            
            # 检查任务状态
            if task["status"] != "running":
                raise AgentManagerError(f"任务 {task_id} 当前状态为 {task['status']}，无法暂停")
            
            # 暂停子任务
            await self.sub_task_manager.pause_sub_tasks(task_id)
            
            # 更新任务状态
            await self.task_history_manager.update_task_status(
                task_id=task_id,
                status="paused"
            )
            
            # 更新Agent状态
            if self.current_task_id == task_id:
                self.status = "paused"
            
            self.logger.info(f"暂停任务 {task_id}")
            return True
        except Exception as e:
            raise AgentManagerError(f"暂停任务失败: {str(e)}")
    
    async def resume_task(self, task_id: int) -> bool:
        """
        恢复任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            恢复是否成功
        """
        try:
            # 检查任务是否存在
            task = await self.task_history_manager.get_task(task_id)
            if not task:
                raise AgentManagerError(f"任务 {task_id} 不存在")
            
            # 检查任务状态
            if task["status"] != "paused":
                raise AgentManagerError(f"任务 {task_id} 当前状态为 {task['status']}，无法恢复")
            
            # 恢复子任务
            await self.sub_task_manager.resume_sub_tasks(task_id)
            
            # 更新任务状态
            await self.task_history_manager.update_task_status(
                task_id=task_id,
                status="running"
            )
            
            # 更新Agent状态
            if self.current_task_id == task_id:
                self.status = "running"
            
            self.logger.info(f"恢复任务 {task_id}")
            return True
        except Exception as e:
            raise AgentManagerError(f"恢复任务失败: {str(e)}")
    
    async def stop_task(self, task_id: int) -> bool:
        """
        停止任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            停止是否成功
        """
        try:
            # 检查任务是否存在
            task = await self.task_history_manager.get_task(task_id)
            if not task:
                raise AgentManagerError(f"任务 {task_id} 不存在")
            
            # 检查任务状态
            if task["status"] not in ["running", "paused"]:
                raise AgentManagerError(f"任务 {task_id} 当前状态为 {task['status']}，无法停止")
            
            # 停止子任务
            await self.sub_task_manager.stop_sub_tasks(task_id)
            
            # 更新任务状态
            await self.task_history_manager.update_task_status(
                task_id=task_id,
                status="stopped"
            )
            
            # 更新Agent状态
            if self.current_task_id == task_id:
                self.status = "idle"
                self.current_task_id = None
                self.current_user_id = None
            
            self.logger.info(f"停止任务 {task_id}")
            return True
        except Exception as e:
            raise AgentManagerError(f"停止任务失败: {str(e)}")
    
    async def get_task_status(self, task_id: int) -> Dict:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        try:
            # 获取任务信息
            task = await self.task_history_manager.get_task(task_id)
            if not task:
                raise AgentManagerError(f"任务 {task_id} 不存在")
            
            # 获取子任务状态
            sub_tasks_status = await self.sub_task_manager.get_sub_tasks_status(task_id)
            
            return {
                "task_id": task_id,
                "status": task["status"],
                "description": task["description"],
                "start_time": task["start_time"],
                "end_time": task["end_time"],
                "sub_tasks": sub_tasks_status
            }
        except Exception as e:
            raise AgentManagerError(f"获取任务状态失败: {str(e)}")
    
    async def get_task_result(self, task_id: int) -> Dict:
        """
        获取任务结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务结果
        """
        try:
            # 获取任务信息
            task = await self.task_history_manager.get_task(task_id)
            if not task:
                raise AgentManagerError(f"任务 {task_id} 不存在")
            
            return {
                "task_id": task_id,
                "status": task["status"],
                "description": task["description"],
                "result": task.get("result", {}),
                "start_time": task["start_time"],
                "end_time": task["end_time"]
            }
        except Exception as e:
            raise AgentManagerError(f"获取任务结果失败: {str(e)}")
    
    async def list_tasks(self, user_id: Optional[int] = None, 
                        status: Optional[str] = None,
                        limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        列出任务
        
        Args:
            user_id: 用户ID，如果为None则列出所有用户的任务
            status: 任务状态，如果为None则列出所有状态的任务
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            任务列表
        """
        try:
            tasks = await self.task_history_manager.list_tasks(
                user_id=user_id,
                status=status,
                limit=limit,
                offset=offset
            )
            
            return tasks
        except Exception as e:
            raise AgentManagerError(f"列出任务失败: {str(e)}")
    
    async def get_agent_status(self) -> Dict:
        """
        获取Agent状态
        
        Returns:
            Agent状态信息
        """
        try:
            return {
                "status": self.status,
                "current_task_id": self.current_task_id,
                "current_user_id": self.current_user_id
            }
        except Exception as e:
            raise AgentManagerError(f"获取Agent状态失败: {str(e)}")
    
    async def get_task_statistics(self, days: int = 30) -> Dict:
        """
        获取任务统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            任务统计信息
        """
        try:
            # 获取任务统计
            task_stats = await self.task_history_manager.get_task_statistics(days)
            
            # 获取子任务统计
            sub_task_stats = await self.sub_task_manager.get_sub_task_statistics(days)
            
            # 获取工具使用统计
            tool_stats = await self.tool_manager.get_tool_usage_stats(days)
            
            return {
                "task_stats": task_stats,
                "sub_task_stats": sub_task_stats,
                "tool_stats": tool_stats
            }
        except Exception as e:
            raise AgentManagerError(f"获取任务统计信息失败: {str(e)}")
    
    async def retry_task(self, task_id: int) -> Dict:
        """
        重试任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            重试结果
        """
        try:
            # 获取任务信息
            task = await self.task_history_manager.get_task(task_id)
            if not task:
                raise AgentManagerError(f"任务 {task_id} 不存在")
            
            # 检查任务状态
            if task["status"] not in ["failed", "stopped", "needs_review"]:
                raise AgentManagerError(f"任务 {task_id} 当前状态为 {task['status']}，无法重试")
            
            # 获取任务描述和上下文
            task_description = task["description"]
            context = task.get("context", {})
            user_id = task.get("user_id")
            
            # 创建新任务
            new_task_id = await self.task_history_manager.create_task(
                description=task_description,
                user_id=user_id,
                context=context
            )
            
            # 记录重试关系
            await self.task_history_manager.create_task_retry(
                original_task_id=task_id,
                new_task_id=new_task_id
            )
            
            # 处理新任务
            result = await self.process_task(
                task_description=task_description,
                user_id=user_id,
                context=context
            )
            
            return result
        except Exception as e:
            raise AgentManagerError(f"重试任务失败: {str(e)}")
    
    async def update_task_context(self, task_id: int, context: Dict) -> bool:
        """
        更新任务上下文
        
        Args:
            task_id: 任务ID
            context: 新的上下文
            
        Returns:
            更新是否成功
        """
        try:
            # 检查任务是否存在
            task = await self.task_history_manager.get_task(task_id)
            if not task:
                raise AgentManagerError(f"任务 {task_id} 不存在")
            
            # 更新任务上下文
            await self.task_history_manager.update_task_context(
                task_id=task_id,
                context=context
            )
            
            self.logger.info(f"更新任务 {task_id} 上下文")
            return True
        except Exception as e:
            raise AgentManagerError(f"更新任务上下文失败: {str(e)}")
    
    async def add_task_feedback(self, task_id: int, feedback: str, 
                             rating: Optional[int] = None) -> bool:
        """
        添加任务反馈
        
        Args:
            task_id: 任务ID
            feedback: 反馈内容
            rating: 评分（1-5）
            
        Returns:
            添加是否成功
        """
        try:
            # 检查任务是否存在
            task = await self.task_history_manager.get_task(task_id)
            if not task:
                raise AgentManagerError(f"任务 {task_id} 不存在")
            
            # 添加任务反馈
            await self.task_history_manager.add_task_feedback(
                task_id=task_id,
                feedback=feedback,
                rating=rating
            )
            
            self.logger.info(f"添加任务 {task_id} 反馈")
            return True
        except Exception as e:
            raise AgentManagerError(f"添加任务反馈失败: {str(e)}")
    
    async def cleanup_old_tasks(self, days: int = 90) -> int:
        """
        清理旧任务
        
        Args:
            days: 保留天数
            
        Returns:
            清理的任务数量
        """
        try:
            # 清理旧任务
            cleaned_count = await self.task_history_manager.cleanup_old_tasks(days)
            
            self.logger.info(f"清理了 {cleaned_count} 个旧任务")
            return cleaned_count
        except Exception as e:
            raise AgentManagerError(f"清理旧任务失败: {str(e)}")