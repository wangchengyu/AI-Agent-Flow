"""
用户确认管理器

负责管理用户确认流程，
包括确认请求、确认处理和确认记录等功能。
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable

from ..database.task_history_manager import TaskHistoryManager
from ..cli.interactive_interface import InteractiveInterface
from ..utils.exceptions import UserConfirmationError


class UserConfirmationManager:
    """用户确认管理器，负责管理用户确认流程"""
    
    def __init__(self, db_manager, interface: InteractiveInterface):
        """
        初始化用户确认管理器
        
        Args:
            db_manager: 数据库管理器
            interface: 交互式界面
        """
        self.db_manager = db_manager
        self.interface = interface
        self.task_history_manager = TaskHistoryManager(db_manager)
        
        # 确认类型
        self.confirmation_types = {
            "task_result": {
                "description": "任务结果确认",
                "handler": self._handle_task_result_confirmation
            },
            "validation_report": {
                "description": "验证报告确认",
                "handler": self._handle_validation_report_confirmation
            },
            "improvement_suggestion": {
                "description": "改进建议确认",
                "handler": self._handle_improvement_suggestion_confirmation
            },
            "task_retry": {
                "description": "任务重试确认",
                "handler": self._handle_task_retry_confirmation
            },
            "task_stop": {
                "description": "任务停止确认",
                "handler": self._handle_task_stop_confirmation
            }
        }
        
        # 确认配置
        self.config = {
            "auto_confirm": False,          # 自动确认
            "confirmation_timeout": 300,   # 确认超时时间（秒）
            "max_confirmation_attempts": 3, # 最大确认尝试次数
            "require_reason": False,        # 需要理由
            "save_confirmation_history": True # 保存确认历史
        }
        
        # 确认状态
        self.confirmation_states = {}
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("用户确认管理器初始化完成")
    
    async def initialize(self):
        """初始化用户确认管理器"""
        try:
            self.logger.info("用户确认管理器初始化完成")
        except Exception as e:
            raise UserConfirmationError(f"初始化用户确认管理器失败: {str(e)}")
    
    async def request_confirmation(self, task_id: int, confirmation_type: str, 
                                 data: Dict, message: str = None) -> Dict:
        """
        请求确认
        
        Args:
            task_id: 任务ID
            confirmation_type: 确认类型
            data: 确认数据
            message: 确认消息
            
        Returns:
            确认结果
        """
        try:
            self.logger.info(f"开始请求任务 {task_id} 的确认: {confirmation_type}")
            
            # 获取任务信息
            task = await self.task_history_manager.get_task(task_id)
            if not task:
                raise UserConfirmationError(f"任务 {task_id} 不存在")
            
            # 检查确认类型
            if confirmation_type not in self.confirmation_types:
                raise UserConfirmationError(f"未知的确认类型: {confirmation_type}")
            
            # 获取确认处理器
            handler = self.confirmation_types[confirmation_type]["handler"]
            
            # 生成确认消息
            if not message:
                message = await self._generate_confirmation_message(
                    task_id, confirmation_type, data
                )
            
            # 初始化确认状态
            confirmation_state = {
                "task_id": task_id,
                "confirmation_type": confirmation_type,
                "data": data,
                "message": message,
                "start_time": datetime.now(),
                "attempts": 0,
                "confirmed": False,
                "rejected": False,
                "timeout": False,
                "reason": None,
                "user_input": None
            }
            
            self.confirmation_states[task_id] = confirmation_state
            
            # 处理确认
            confirmation_result = await handler(task_id, confirmation_state)
            
            # 更新确认状态
            confirmation_state.update({
                "end_time": datetime.now(),
                "confirmed": confirmation_result.get("confirmed", False),
                "rejected": confirmation_result.get("rejected", False),
                "timeout": confirmation_result.get("timeout", False),
                "reason": confirmation_result.get("reason"),
                "user_input": confirmation_result.get("user_input")
            })
            
            # 保存确认记录
            if self.config["save_confirmation_history"]:
                await self.task_history_manager.create_user_confirmation(
                    task_id=task_id,
                    confirmation_type=confirmation_type,
                    message=message,
                    data=data,
                    confirmed=confirmation_result.get("confirmed", False),
                    rejected=confirmation_result.get("rejected", False),
                    timeout=confirmation_result.get("timeout", False),
                    reason=confirmation_result.get("reason"),
                    user_input=confirmation_result.get("user_input")
                )
            
            # 清理确认状态
            if task_id in self.confirmation_states:
                del self.confirmation_states[task_id]
            
            self.logger.info(f"任务 {task_id} 的确认请求处理完成")
            return confirmation_result
        except Exception as e:
            # 清理确认状态
            if task_id in self.confirmation_states:
                del self.confirmation_states[task_id]
            
            raise UserConfirmationError(f"请求确认失败: {str(e)}")
    
    async def _handle_task_result_confirmation(self, task_id: int, confirmation_state: Dict) -> Dict:
        """
        处理任务结果确认
        
        Args:
            task_id: 任务ID
            confirmation_state: 确认状态
            
        Returns:
            确认结果
        """
        try:
            # 获取确认数据
            data = confirmation_state.get("data", {})
            task_result = data.get("task_result", {})
            validation_result = data.get("validation_result", {})
            
            # 显示任务结果摘要
            await self.interface.message("任务结果摘要", "info")
            
            # 显示验证结果
            is_valid = validation_result.get("is_valid", False)
            overall_score = validation_result.get("overall_score", 0.0)
            
            await self.interface.message(f"验证状态: {'通过' if is_valid else '未通过'}", "success" if is_valid else "error")
            await self.interface.message(f"总体分数: {overall_score:.2f}", "info")
            
            # 显示问题摘要
            issues = validation_result.get("issues", [])
            if issues:
                await self.interface.message(f"发现 {len(issues)} 个问题", "warning")
                
                # 显示前3个问题
                for i, issue in enumerate(issues[:3]):
                    description = issue.get("description", "")
                    severity = issue.get("severity", "medium")
                    
                    await self.interface.message(f"  {i+1}. {description} (严重程度: {severity})", "warning")
                
                if len(issues) > 3:
                    await self.interface.message(f"  ... 还有 {len(issues) - 3} 个问题", "warning")
            
            # 请求确认
            confirmation_message = confirmation_state.get("message", "是否确认任务结果？")
            
            if self.config["auto_confirm"]:
                confirmed = True
                reason = "自动确认"
                user_input = None
            else:
                confirmed = await self.interface.confirm(confirmation_message)
                
                if confirmed:
                    reason = await self.interface.prompt("请输入确认理由（可选）", default="")
                    user_input = {"reason": reason}
                else:
                    reason = await self.interface.prompt("请输入拒绝理由", default="需要进一步修改")
                    user_input = {"reason": reason}
            
            # 构建确认结果
            result = {
                "confirmed": confirmed,
                "rejected": not confirmed,
                "timeout": False,
                "reason": reason,
                "user_input": user_input
            }
            
            return result
        except Exception as e:
            raise UserConfirmationError(f"处理任务结果确认失败: {str(e)}")
    
    async def _handle_validation_report_confirmation(self, task_id: int, confirmation_state: Dict) -> Dict:
        """
        处理验证报告确认
        
        Args:
            task_id: 任务ID
            confirmation_state: 确认状态
            
        Returns:
            确认结果
        """
        try:
            # 获取确认数据
            data = confirmation_state.get("data", {})
            report_path = data.get("report_path", "")
            report_summary = data.get("report_summary", "")
            
            # 显示验证报告摘要
            await self.interface.message("验证报告摘要", "info")
            
            if report_summary:
                await self.interface.message(report_summary, "info")
            
            if report_path:
                await self.interface.message(f"完整报告已保存到: {report_path}", "info")
            
            # 请求确认
            confirmation_message = confirmation_state.get("message", "是否确认验证报告？")
            
            if self.config["auto_confirm"]:
                confirmed = True
                reason = "自动确认"
                user_input = None
            else:
                confirmed = await self.interface.confirm(confirmation_message)
                
                if confirmed:
                    reason = await self.interface.prompt("请输入确认理由（可选）", default="")
                    user_input = {"reason": reason}
                else:
                    reason = await self.interface.prompt("请输入拒绝理由", default="需要重新生成报告")
                    user_input = {"reason": reason}
            
            # 构建确认结果
            result = {
                "confirmed": confirmed,
                "rejected": not confirmed,
                "timeout": False,
                "reason": reason,
                "user_input": user_input
            }
            
            return result
        except Exception as e:
            raise UserConfirmationError(f"处理验证报告确认失败: {str(e)}")
    
    async def _handle_improvement_suggestion_confirmation(self, task_id: int, confirmation_state: Dict) -> Dict:
        """
        处理改进建议确认
        
        Args:
            task_id: 任务ID
            confirmation_state: 确认状态
            
        Returns:
            确认结果
        """
        try:
            # 获取确认数据
            data = confirmation_state.get("data", {})
            suggestions = data.get("suggestions", [])
            
            # 显示改进建议
            await self.interface.message("改进建议", "info")
            
            if suggestions:
                for i, suggestion in enumerate(suggestions):
                    description = suggestion.get("description", "")
                    priority = suggestion.get("priority", "medium")
                    
                    await self.interface.message(f"{i+1}. {description} (优先级: {priority})", "info")
            else:
                await self.interface.message("没有改进建议", "info")
            
            # 请求确认
            confirmation_message = confirmation_state.get("message", "是否确认改进建议？")
            
            if self.config["auto_confirm"]:
                confirmed = True
                reason = "自动确认"
                user_input = None
            else:
                confirmed = await self.interface.confirm(confirmation_message)
                
                if confirmed:
                    reason = await self.interface.prompt("请输入确认理由（可选）", default="")
                    user_input = {"reason": reason}
                else:
                    reason = await self.interface.prompt("请输入拒绝理由", default="需要其他改进建议")
                    user_input = {"reason": reason}
            
            # 构建确认结果
            result = {
                "confirmed": confirmed,
                "rejected": not confirmed,
                "timeout": False,
                "reason": reason,
                "user_input": user_input
            }
            
            return result
        except Exception as e:
            raise UserConfirmationError(f"处理改进建议确认失败: {str(e)}")
    
    async def _handle_task_retry_confirmation(self, task_id: int, confirmation_state: Dict) -> Dict:
        """
        处理任务重试确认
        
        Args:
            task_id: 任务ID
            confirmation_state: 确认状态
            
        Returns:
            确认结果
        """
        try:
            # 获取确认数据
            data = confirmation_state.get("data", {})
            task_status = data.get("task_status", "")
            error_message = data.get("error_message", "")
            
            # 显示任务状态
            await self.interface.message("任务重试确认", "warning")
            
            await self.interface.message(f"任务状态: {task_status}", "warning")
            
            if error_message:
                await self.interface.message(f"错误信息: {error_message}", "error")
            
            # 请求确认
            confirmation_message = confirmation_state.get("message", "是否确认重试任务？")
            
            if self.config["auto_confirm"]:
                confirmed = True
                reason = "自动确认"
                user_input = None
            else:
                confirmed = await self.interface.confirm(confirmation_message)
                
                if confirmed:
                    reason = await self.interface.prompt("请输入确认理由（可选）", default="")
                    user_input = {"reason": reason}
                else:
                    reason = await self.interface.prompt("请输入拒绝理由", default="不重试任务")
                    user_input = {"reason": reason}
            
            # 构建确认结果
            result = {
                "confirmed": confirmed,
                "rejected": not confirmed,
                "timeout": False,
                "reason": reason,
                "user_input": user_input
            }
            
            return result
        except Exception as e:
            raise UserConfirmationError(f"处理任务重试确认失败: {str(e)}")
    
    async def _handle_task_stop_confirmation(self, task_id: int, confirmation_state: Dict) -> Dict:
        """
        处理任务停止确认
        
        Args:
            task_id: 任务ID
            confirmation_state: 确认状态
            
        Returns:
            确认结果
        """
        try:
            # 获取确认数据
            data = confirmation_state.get("data", {})
            task_status = data.get("task_status", "")
            progress = data.get("progress", 0)
            
            # 显示任务状态
            await self.interface.message("任务停止确认", "warning")
            
            await self.interface.message(f"任务状态: {task_status}", "warning")
            await self.interface.message(f"任务进度: {progress}%", "info")
            
            # 请求确认
            confirmation_message = confirmation_state.get("message", "是否确认停止任务？")
            
            if self.config["auto_confirm"]:
                confirmed = True
                reason = "自动确认"
                user_input = None
            else:
                confirmed = await self.interface.confirm(confirmation_message)
                
                if confirmed:
                    reason = await self.interface.prompt("请输入确认理由（可选）", default="")
                    user_input = {"reason": reason}
                else:
                    reason = await self.interface.prompt("请输入拒绝理由", default="继续执行任务")
                    user_input = {"reason": reason}
            
            # 构建确认结果
            result = {
                "confirmed": confirmed,
                "rejected": not confirmed,
                "timeout": False,
                "reason": reason,
                "user_input": user_input
            }
            
            return result
        except Exception as e:
            raise UserConfirmationError(f"处理任务停止确认失败: {str(e)}")
    
    async def _generate_confirmation_message(self, task_id: int, confirmation_type: str, data: Dict) -> str:
        """
        生成确认消息
        
        Args:
            task_id: 任务ID
            confirmation_type: 确认类型
            data: 确认数据
            
        Returns:
            确认消息
        """
        try:
            # 根据确认类型生成消息
            if confirmation_type == "task_result":
                return f"任务 {task_id} 已完成，是否确认结果？"
            elif confirmation_type == "validation_report":
                return f"任务 {task_id} 的验证报告已生成，是否确认报告？"
            elif confirmation_type == "improvement_suggestion":
                return f"任务 {task_id} 有改进建议，是否确认建议？"
            elif confirmation_type == "task_retry":
                return f"任务 {task_id} 执行失败，是否确认重试？"
            elif confirmation_type == "task_stop":
                return f"任务 {task_id} 正在执行，是否确认停止？"
            else:
                return f"是否确认操作？"
        except Exception as e:
            self.logger.error(f"生成确认消息失败: {str(e)}")
            return "是否确认操作？"
    
    async def get_confirmation_state(self, task_id: int) -> Dict:
        """
        获取确认状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            确认状态
        """
        try:
            return self.confirmation_states.get(task_id, {})
        except Exception as e:
            raise UserConfirmationError(f"获取确认状态失败: {str(e)}")
    
    async def get_user_confirmation(self, task_id: int) -> Dict:
        """
        获取用户确认记录
        
        Args:
            task_id: 任务ID
            
        Returns:
            用户确认记录
        """
        try:
            confirmation_record = await self.task_history_manager.get_user_confirmation(task_id)
            return confirmation_record
        except Exception as e:
            raise UserConfirmationError(f"获取用户确认记录失败: {str(e)}")
    
    def set_config(self, key: str, value: Any) -> bool:
        """
        设置配置
        
        Args:
            key: 配置键
            value: 配置值
            
        Returns:
            设置是否成功
        """
        try:
            if key in self.config:
                self.config[key] = value
                self.logger.info(f"设置用户确认配置: {key} = {value}")
                return True
            else:
                self.logger.warning(f"未知的用户确认配置键: {key}")
                return False
        except Exception as e:
            raise UserConfirmationError(f"设置配置失败: {str(e)}")
    
    def get_config(self, key: str) -> Any:
        """
        获取配置
        
        Args:
            key: 配置键
            
        Returns:
            配置值
        """
        try:
            return self.config.get(key)
        except Exception as e:
            raise UserConfirmationError(f"获取配置失败: {str(e)}")
    
    async def add_confirmation_type(self, name: str, description: str, handler: Callable) -> bool:
        """
        添加确认类型
        
        Args:
            name: 类型名称
            description: 类型描述
            handler: 处理器函数
            
        Returns:
            添加是否成功
        """
        try:
            self.confirmation_types[name] = {
                "description": description,
                "handler": handler
            }
            
            self.logger.info(f"添加确认类型: {name}")
            return True
        except Exception as e:
            raise UserConfirmationError(f"添加确认类型失败: {str(e)}")
    
    async def get_user_confirmation_stats(self, days: int = 30) -> Dict:
        """
        获取用户确认统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        try:
            # 获取用户确认统计
            stats = await self.task_history_manager.get_user_confirmation_statistics(days)
            
            return stats
        except Exception as e:
            raise UserConfirmationError(f"获取用户确认统计信息失败: {str(e)}")
    
    async def cancel_confirmation(self, task_id: int) -> bool:
        """
        取消确认
        
        Args:
            task_id: 任务ID
            
        Returns:
            取消是否成功
        """
        try:
            if task_id in self.confirmation_states:
                confirmation_state = self.confirmation_states[task_id]
                
                # 更新确认状态
                confirmation_state.update({
                    "end_time": datetime.now(),
                    "confirmed": False,
                    "rejected": True,
                    "timeout": False,
                    "reason": "用户取消",
                    "user_input": {"reason": "用户取消"}
                })
                
                # 保存确认记录
                if self.config["save_confirmation_history"]:
                    await self.task_history_manager.create_user_confirmation(
                        task_id=task_id,
                        confirmation_type=confirmation_state.get("confirmation_type"),
                        message=confirmation_state.get("message"),
                        data=confirmation_state.get("data"),
                        confirmed=False,
                        rejected=True,
                        timeout=False,
                        reason="用户取消",
                        user_input={"reason": "用户取消"}
                    )
                
                # 清理确认状态
                del self.confirmation_states[task_id]
                
                self.logger.info(f"已取消任务 {task_id} 的确认请求")
                return True
            else:
                self.logger.warning(f"任务 {task_id} 没有正在进行的确认请求")
                return False
        except Exception as e:
            raise UserConfirmationError(f"取消确认失败: {str(e)}")