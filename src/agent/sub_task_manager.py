"""
子任务管理器

负责管理子任务的执行，包括子任务的状态管理、
执行顺序控制和结果收集等功能。
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable

from ..database.task_history_manager import TaskHistoryManager
from ..mcp_tools.tool_manager import ToolManager
from ..utils.exceptions import SubTaskManagerError


class SubTaskManager:
    """子任务管理器，负责管理子任务的执行"""
    
    def __init__(self, db_manager, tool_manager: ToolManager):
        """
        初始化子任务管理器
        
        Args:
            db_manager: 数据库管理器
            tool_manager: 工具管理器
        """
        self.db_manager = db_manager
        self.tool_manager = tool_manager
        self.task_history_manager = TaskHistoryManager(db_manager)
        
        # 子任务执行状态
        self.execution_status = {}  # task_id -> status
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """初始化子任务管理器"""
        try:
            self.logger.info("子任务管理器初始化完成")
        except Exception as e:
            raise SubTaskManagerError(f"初始化子任务管理器失败: {str(e)}")
    
    async def execute_sub_tasks(self, task_id: int, sub_tasks: List[Dict], 
                              user_id: Optional[int] = None) -> List[Dict]:
        """
        执行子任务
        
        Args:
            task_id: 任务ID
            sub_tasks: 子任务列表
            user_id: 用户ID
            
        Returns:
            子任务结果列表
        """
        try:
            self.logger.info(f"开始执行任务 {task_id} 的子任务")
            
            # 初始化执行状态
            self.execution_status[task_id] = {
                "status": "running",
                "start_time": time.time(),
                "completed_sub_tasks": 0,
                "total_sub_tasks": len(sub_tasks),
                "results": []
            }
            
            # 按顺序执行子任务
            results = []
            for sub_task in sub_tasks:
                # 检查子任务依赖
                if not await self._check_dependencies(task_id, sub_task):
                    # 如果依赖不满足，跳过该子任务
                    self.logger.warning(f"子任务 {sub_task['id']} 的依赖不满足，跳过执行")
                    await self.task_history_manager.update_sub_task_status(
                        sub_task_id=sub_task["id"],
                        status="skipped",
                        result={"error": "依赖不满足"}
                    )
                    continue
                
                # 执行子任务
                result = await self._execute_sub_task(task_id, sub_task, user_id)
                results.append(result)
                
                # 更新执行状态
                self.execution_status[task_id]["completed_sub_tasks"] += 1
                self.execution_status[task_id]["results"].append(result)
            
            # 更新执行状态
            self.execution_status[task_id]["status"] = "completed"
            self.execution_status[task_id]["end_time"] = time.time()
            
            self.logger.info(f"任务 {task_id} 的子任务执行完成")
            return results
        except Exception as e:
            # 更新执行状态
            if task_id in self.execution_status:
                self.execution_status[task_id]["status"] = "failed"
                self.execution_status[task_id]["end_time"] = time.time()
                self.execution_status[task_id]["error"] = str(e)
            
            raise SubTaskManagerError(f"执行子任务失败: {str(e)}")
    
    async def _check_dependencies(self, task_id: int, sub_task: Dict) -> bool:
        """
        检查子任务依赖
        
        Args:
            task_id: 任务ID
            sub_task: 子任务信息
            
        Returns:
            依赖是否满足
        """
        try:
            dependencies = sub_task.get("dependencies", [])
            
            # 如果没有依赖，返回True
            if not dependencies:
                return True
            
            # 检查每个依赖是否已完成
            for dep_id in dependencies:
                dep_sub_task = await self.task_history_manager.get_sub_task(dep_id)
                if not dep_sub_task or dep_sub_task["status"] not in ["completed", "skipped"]:
                    return False
            
            return True
        except Exception as e:
            raise SubTaskManagerError(f"检查子任务依赖失败: {str(e)}")
    
    async def _execute_sub_task(self, task_id: int, sub_task: Dict, 
                              user_id: Optional[int] = None) -> Dict:
        """
        执行单个子任务
        
        Args:
            task_id: 任务ID
            sub_task: 子任务信息
            user_id: 用户ID
            
        Returns:
            子任务结果
        """
        try:
            sub_task_id = sub_task["id"]
            sub_task_name = sub_task["name"]
            sub_task_description = sub_task["description"]
            required_tools = sub_task.get("required_tools", [])
            
            self.logger.info(f"执行子任务 {sub_task_id}: {sub_task_name}")
            
            # 更新子任务状态为运行中
            await self.task_history_manager.update_sub_task_status(
                sub_task_id=sub_task_id,
                status="running"
            )
            
            # 根据子任务类型执行相应的操作
            sub_task_type = sub_task.get("type", "general")
            
            if sub_task_type == "analysis":
                result = await self._execute_analysis_sub_task(sub_task, user_id)
            elif sub_task_type == "generation":
                result = await self._execute_generation_sub_task(sub_task, user_id)
            elif sub_task_type == "modification":
                result = await self._execute_modification_sub_task(sub_task, user_id)
            elif sub_task_type == "search":
                result = await self._execute_search_sub_task(sub_task, user_id)
            elif sub_task_type == "transformation":
                result = await self._execute_transformation_sub_task(sub_task, user_id)
            elif sub_task_type == "validation":
                result = await self._execute_validation_sub_task(sub_task, user_id)
            else:
                result = await self._execute_general_sub_task(sub_task, user_id)
            
            # 更新子任务状态为已完成
            await self.task_history_manager.update_sub_task_status(
                sub_task_id=sub_task_id,
                status="completed",
                result=result
            )
            
            self.logger.info(f"子任务 {sub_task_id} 执行完成")
            return {
                "sub_task_id": sub_task_id,
                "name": sub_task_name,
                "description": sub_task_description,
                "type": sub_task_type,
                "status": "completed",
                "result": result
            }
        except Exception as e:
            # 更新子任务状态为失败
            await self.task_history_manager.update_sub_task_status(
                sub_task_id=sub_task["id"],
                status="failed",
                result={"error": str(e)}
            )
            
            self.logger.error(f"子任务 {sub_task['id']} 执行失败: {str(e)}")
            return {
                "sub_task_id": sub_task["id"],
                "name": sub_task["name"],
                "description": sub_task["description"],
                "type": sub_task.get("type", "general"),
                "status": "failed",
                "error": str(e)
            }
    
    async def _execute_analysis_sub_task(self, sub_task: Dict, 
                                       user_id: Optional[int] = None) -> Dict:
        """
        执行分析类子任务
        
        Args:
            sub_task: 子任务信息
            user_id: 用户ID
            
        Returns:
            子任务结果
        """
        try:
            required_tools = sub_task.get("required_tools", [])
            
            # 简化的分析逻辑
            result = {
                "type": "analysis",
                "summary": "分析完成",
                "findings": [],
                "recommendations": []
            }
            
            # 如果需要使用工具
            if required_tools:
                for tool_name in required_tools:
                    try:
                        # 调用工具
                        tool_result = await self.tool_manager.call_tool(
                            name=tool_name,
                            arguments={"action": "analyze", "target": sub_task["description"]},
                            user_id=user_id,
                            task_id=int(sub_task["id"].split("_")[0])
                        )
                        
                        if tool_result["success"]:
                            result["findings"].append({
                                "tool": tool_name,
                                "result": tool_result["result"]
                            })
                        else:
                            result["findings"].append({
                                "tool": tool_name,
                                "error": tool_result["error"]
                            })
                    except Exception as e:
                        result["findings"].append({
                            "tool": tool_name,
                            "error": str(e)
                        })
            
            return result
        except Exception as e:
            raise SubTaskManagerError(f"执行分析类子任务失败: {str(e)}")
    
    async def _execute_generation_sub_task(self, sub_task: Dict, 
                                         user_id: Optional[int] = None) -> Dict:
        """
        执行生成类子任务
        
        Args:
            sub_task: 子任务信息
            user_id: 用户ID
            
        Returns:
            子任务结果
        """
        try:
            required_tools = sub_task.get("required_tools", [])
            
            # 简化的生成逻辑
            result = {
                "type": "generation",
                "generated_content": "",
                "metadata": {}
            }
            
            # 如果需要使用工具
            if required_tools:
                for tool_name in required_tools:
                    try:
                        # 调用工具
                        tool_result = await self.tool_manager.call_tool(
                            name=tool_name,
                            arguments={"action": "generate", "target": sub_task["description"]},
                            user_id=user_id,
                            task_id=int(sub_task["id"].split("_")[0])
                        )
                        
                        if tool_result["success"]:
                            result["generated_content"] = tool_result["result"]
                            result["metadata"]["tool"] = tool_name
                        else:
                            result["metadata"]["error"] = tool_result["error"]
                    except Exception as e:
                        result["metadata"]["error"] = str(e)
            
            return result
        except Exception as e:
            raise SubTaskManagerError(f"执行生成类子任务失败: {str(e)}")
    
    async def _execute_modification_sub_task(self, sub_task: Dict, 
                                           user_id: Optional[int] = None) -> Dict:
        """
        执行修改类子任务
        
        Args:
            sub_task: 子任务信息
            user_id: 用户ID
            
        Returns:
            子任务结果
        """
        try:
            required_tools = sub_task.get("required_tools", [])
            
            # 简化的修改逻辑
            result = {
                "type": "modification",
                "modified_content": "",
                "changes": [],
                "metadata": {}
            }
            
            # 如果需要使用工具
            if required_tools:
                for tool_name in required_tools:
                    try:
                        # 调用工具
                        tool_result = await self.tool_manager.call_tool(
                            name=tool_name,
                            arguments={"action": "modify", "target": sub_task["description"]},
                            user_id=user_id,
                            task_id=int(sub_task["id"].split("_")[0])
                        )
                        
                        if tool_result["success"]:
                            result["modified_content"] = tool_result["result"]
                            result["metadata"]["tool"] = tool_name
                        else:
                            result["metadata"]["error"] = tool_result["error"]
                    except Exception as e:
                        result["metadata"]["error"] = str(e)
            
            return result
        except Exception as e:
            raise SubTaskManagerError(f"执行修改类子任务失败: {str(e)}")
    
    async def _execute_search_sub_task(self, sub_task: Dict, 
                                      user_id: Optional[int] = None) -> Dict:
        """
        执行搜索类子任务
        
        Args:
            sub_task: 子任务信息
            user_id: 用户ID
            
        Returns:
            子任务结果
        """
        try:
            required_tools = sub_task.get("required_tools", [])
            
            # 简化的搜索逻辑
            result = {
                "type": "search",
                "search_results": [],
                "summary": "",
                "metadata": {}
            }
            
            # 如果需要使用工具
            if required_tools:
                for tool_name in required_tools:
                    try:
                        # 调用工具
                        tool_result = await self.tool_manager.call_tool(
                            name=tool_name,
                            arguments={"action": "search", "target": sub_task["description"]},
                            user_id=user_id,
                            task_id=int(sub_task["id"].split("_")[0])
                        )
                        
                        if tool_result["success"]:
                            result["search_results"] = tool_result["result"]
                            result["metadata"]["tool"] = tool_name
                        else:
                            result["metadata"]["error"] = tool_result["error"]
                    except Exception as e:
                        result["metadata"]["error"] = str(e)
            
            return result
        except Exception as e:
            raise SubTaskManagerError(f"执行搜索类子任务失败: {str(e)}")
    
    async def _execute_transformation_sub_task(self, sub_task: Dict, 
                                             user_id: Optional[int] = None) -> Dict:
        """
        执行转换类子任务
        
        Args:
            sub_task: 子任务信息
            user_id: 用户ID
            
        Returns:
            子任务结果
        """
        try:
            required_tools = sub_task.get("required_tools", [])
            
            # 简化的转换逻辑
            result = {
                "type": "transformation",
                "transformed_content": "",
                "transformation_details": [],
                "metadata": {}
            }
            
            # 如果需要使用工具
            if required_tools:
                for tool_name in required_tools:
                    try:
                        # 调用工具
                        tool_result = await self.tool_manager.call_tool(
                            name=tool_name,
                            arguments={"action": "transform", "target": sub_task["description"]},
                            user_id=user_id,
                            task_id=int(sub_task["id"].split("_")[0])
                        )
                        
                        if tool_result["success"]:
                            result["transformed_content"] = tool_result["result"]
                            result["metadata"]["tool"] = tool_name
                        else:
                            result["metadata"]["error"] = tool_result["error"]
                    except Exception as e:
                        result["metadata"]["error"] = str(e)
            
            return result
        except Exception as e:
            raise SubTaskManagerError(f"执行转换类子任务失败: {str(e)}")
    
    async def _execute_validation_sub_task(self, sub_task: Dict, 
                                         user_id: Optional[int] = None) -> Dict:
        """
        执行验证类子任务
        
        Args:
            sub_task: 子任务信息
            user_id: 用户ID
            
        Returns:
            子任务结果
        """
        try:
            required_tools = sub_task.get("required_tools", [])
            
            # 简化的验证逻辑
            result = {
                "type": "validation",
                "is_valid": True,
                "validation_details": [],
                "issues": [],
                "recommendations": []
            }
            
            # 如果需要使用工具
            if required_tools:
                for tool_name in required_tools:
                    try:
                        # 调用工具
                        tool_result = await self.tool_manager.call_tool(
                            name=tool_name,
                            arguments={"action": "validate", "target": sub_task["description"]},
                            user_id=user_id,
                            task_id=int(sub_task["id"].split("_")[0])
                        )
                        
                        if tool_result["success"]:
                            validation_result = tool_result["result"]
                            result["validation_details"].append({
                                "tool": tool_name,
                                "result": validation_result
                            })
                            
                            # 更新验证结果
                            if isinstance(validation_result, dict):
                                if "is_valid" in validation_result:
                                    result["is_valid"] = result["is_valid"] and validation_result["is_valid"]
                                
                                if "issues" in validation_result:
                                    result["issues"].extend(validation_result["issues"])
                                
                                if "recommendations" in validation_result:
                                    result["recommendations"].extend(validation_result["recommendations"])
                        else:
                            result["validation_details"].append({
                                "tool": tool_name,
                                "error": tool_result["error"]
                            })
                            result["is_valid"] = False
                    except Exception as e:
                        result["validation_details"].append({
                            "tool": tool_name,
                            "error": str(e)
                        })
                        result["is_valid"] = False
            
            return result
        except Exception as e:
            raise SubTaskManagerError(f"执行验证类子任务失败: {str(e)}")
    
    async def _execute_general_sub_task(self, sub_task: Dict, 
                                       user_id: Optional[int] = None) -> Dict:
        """
        执行通用类子任务
        
        Args:
            sub_task: 子任务信息
            user_id: 用户ID
            
        Returns:
            子任务结果
        """
        try:
            required_tools = sub_task.get("required_tools", [])
            
            # 简化的通用逻辑
            result = {
                "type": "general",
                "result": "",
                "metadata": {}
            }
            
            # 如果需要使用工具
            if required_tools:
                for tool_name in required_tools:
                    try:
                        # 调用工具
                        tool_result = await self.tool_manager.call_tool(
                            name=tool_name,
                            arguments={"action": "execute", "target": sub_task["description"]},
                            user_id=user_id,
                            task_id=int(sub_task["id"].split("_")[0])
                        )
                        
                        if tool_result["success"]:
                            result["result"] = tool_result["result"]
                            result["metadata"]["tool"] = tool_name
                        else:
                            result["metadata"]["error"] = tool_result["error"]
                    except Exception as e:
                        result["metadata"]["error"] = str(e)
            
            return result
        except Exception as e:
            raise SubTaskManagerError(f"执行通用类子任务失败: {str(e)}")
    
    async def pause_sub_tasks(self, task_id: int) -> bool:
        """
        暂停子任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            暂停是否成功
        """
        try:
            # 检查任务是否在执行中
            if task_id not in self.execution_status:
                raise SubTaskManagerError(f"任务 {task_id} 不在执行中")
            
            status = self.execution_status[task_id]
            if status["status"] != "running":
                raise SubTaskManagerError(f"任务 {task_id} 当前状态为 {status['status']}，无法暂停")
            
            # 更新执行状态
            self.execution_status[task_id]["status"] = "paused"
            
            # 更新数据库中的子任务状态
            sub_tasks = await self.task_history_manager.get_sub_tasks(task_id)
            for sub_task in sub_tasks:
                if sub_task["status"] == "running":
                    await self.task_history_manager.update_sub_task_status(
                        sub_task_id=sub_task["id"],
                        status="paused"
                    )
            
            self.logger.info(f"暂停任务 {task_id} 的子任务")
            return True
        except Exception as e:
            raise SubTaskManagerError(f"暂停子任务失败: {str(e)}")
    
    async def resume_sub_tasks(self, task_id: int) -> bool:
        """
        恢复子任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            恢复是否成功
        """
        try:
            # 检查任务是否已暂停
            if task_id not in self.execution_status:
                raise SubTaskManagerError(f"任务 {task_id} 不在执行中")
            
            status = self.execution_status[task_id]
            if status["status"] != "paused":
                raise SubTaskManagerError(f"任务 {task_id} 当前状态为 {status['status']}，无法恢复")
            
            # 更新执行状态
            self.execution_status[task_id]["status"] = "running"
            
            # 更新数据库中的子任务状态
            sub_tasks = await self.task_history_manager.get_sub_tasks(task_id)
            for sub_task in sub_tasks:
                if sub_task["status"] == "paused":
                    await self.task_history_manager.update_sub_task_status(
                        sub_task_id=sub_task["id"],
                        status="pending"
                    )
            
            self.logger.info(f"恢复任务 {task_id} 的子任务")
            return True
        except Exception as e:
            raise SubTaskManagerError(f"恢复子任务失败: {str(e)}")
    
    async def stop_sub_tasks(self, task_id: int) -> bool:
        """
        停止子任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            停止是否成功
        """
        try:
            # 检查任务是否在执行中
            if task_id not in self.execution_status:
                raise SubTaskManagerError(f"任务 {task_id} 不在执行中")
            
            status = self.execution_status[task_id]
            if status["status"] not in ["running", "paused"]:
                raise SubTaskManagerError(f"任务 {task_id} 当前状态为 {status['status']}，无法停止")
            
            # 更新执行状态
            self.execution_status[task_id]["status"] = "stopped"
            
            # 更新数据库中的子任务状态
            sub_tasks = await self.task_history_manager.get_sub_tasks(task_id)
            for sub_task in sub_tasks:
                if sub_task["status"] in ["running", "paused", "pending"]:
                    await self.task_history_manager.update_sub_task_status(
                        sub_task_id=sub_task["id"],
                        status="stopped"
                    )
            
            self.logger.info(f"停止任务 {task_id} 的子任务")
            return True
        except Exception as e:
            raise SubTaskManagerError(f"停止子任务失败: {str(e)}")
    
    async def get_sub_tasks_status(self, task_id: int) -> List[Dict]:
        """
        获取子任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            子任务状态列表
        """
        try:
            # 从数据库获取子任务
            sub_tasks = await self.task_history_manager.get_sub_tasks(task_id)
            
            # 添加执行状态信息
            if task_id in self.execution_status:
                execution_status = self.execution_status[task_id]
                
                for sub_task in sub_tasks:
                    sub_task["execution_progress"] = {
                        "completed": execution_status["completed_sub_tasks"],
                        "total": execution_status["total_sub_tasks"]
                    }
            
            return sub_tasks
        except Exception as e:
            raise SubTaskManagerError(f"获取子任务状态失败: {str(e)}")
    
    async def get_sub_task_result(self, sub_task_id: str) -> Dict:
        """
        获取子任务结果
        
        Args:
            sub_task_id: 子任务ID
            
        Returns:
            子任务结果
        """
        try:
            # 从数据库获取子任务
            sub_task = await self.task_history_manager.get_sub_task(sub_task_id)
            
            if not sub_task:
                raise SubTaskManagerError(f"子任务 {sub_task_id} 不存在")
            
            return {
                "sub_task_id": sub_task_id,
                "name": sub_task["name"],
                "description": sub_task["description"],
                "status": sub_task["status"],
                "result": sub_task.get("result", {}),
                "start_time": sub_task["start_time"],
                "end_time": sub_task["end_time"]
            }
        except Exception as e:
            raise SubTaskManagerError(f"获取子任务结果失败: {str(e)}")
    
    async def get_sub_task_statistics(self, days: int = 30) -> Dict:
        """
        获取子任务统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            子任务统计信息
        """
        try:
            # 从数据库获取子任务统计
            stats = await self.task_history_manager.get_sub_task_statistics(days)
            
            return stats
        except Exception as e:
            raise SubTaskManagerError(f"获取子任务统计信息失败: {str(e)}")