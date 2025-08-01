"""
循环控制逻辑

负责控制信息补充循环的执行，
包括循环触发条件、循环执行控制和循环终止条件等功能。
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable

from ..database.task_history_manager import TaskHistoryManager
from ..agent.info_requirement_detector import InfoRequirementDetector
from ..agent.user_input_processor import UserInputProcessor
from ..agent.info_integration_mechanism import InfoIntegrationMechanism
from ..utils.exceptions import LoopControlError


class LoopControlLogic:
    """循环控制逻辑，负责控制信息补充循环的执行"""
    
    def __init__(self, db_manager, info_requirement_detector: InfoRequirementDetector,
                 user_input_processor: UserInputProcessor, info_integration_mechanism: InfoIntegrationMechanism):
        """
        初始化循环控制逻辑
        
        Args:
            db_manager: 数据库管理器
            info_requirement_detector: 信息需求检测器
            user_input_processor: 用户输入处理器
            info_integration_mechanism: 信息整合机制
        """
        self.db_manager = db_manager
        self.info_requirement_detector = info_requirement_detector
        self.user_input_processor = user_input_processor
        self.info_integration_mechanism = info_integration_mechanism
        self.task_history_manager = TaskHistoryManager(db_manager)
        
        # 循环控制配置
        self.config = {
            "max_loops": 5,                    # 最大循环次数
            "min_info_requirements": 1,        # 最小信息需求数量
            "high_priority_threshold": 0.7,    # 高优先级阈值
            "medium_priority_threshold": 0.4,  # 中优先级阈值
            "loop_interval": 1.0,             # 循环间隔（秒）
            "timeout": 300,                   # 超时时间（秒）
            "auto_continue": True             # 自动继续
        }
        
        # 循环状态
        self.loop_states = {}
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("循环控制逻辑初始化完成")
    
    async def initialize(self):
        """初始化循环控制逻辑"""
        try:
            self.logger.info("循环控制逻辑初始化完成")
        except Exception as e:
            raise LoopControlError(f"初始化循环控制逻辑失败: {str(e)}")
    
    async def execute_info_gathering_loop(self, task_id: int, sub_task_results: List[Dict]) -> Dict:
        """
        执行信息补充循环
        
        Args:
            task_id: 任务ID
            sub_task_results: 子任务结果列表
            
        Returns:
            循环执行结果
        """
        try:
            self.logger.info(f"开始执行任务 {task_id} 的信息补充循环")
            
            # 获取任务信息
            task = await self.task_history_manager.get_task(task_id)
            if not task:
                raise LoopControlError(f"任务 {task_id} 不存在")
            
            # 初始化循环状态
            loop_state = {
                "task_id": task_id,
                "loop_count": 0,
                "start_time": datetime.now(),
                "last_loop_time": None,
                "info_requirements": [],
                "user_inputs": [],
                "integrated_info": {},
                "should_continue": True,
                "timeout": False
            }
            
            self.loop_states[task_id] = loop_state
            
            # 循环执行
            while loop_state["should_continue"] and not loop_state["timeout"]:
                # 检查循环条件
                if not await self._check_loop_conditions(loop_state):
                    loop_state["should_continue"] = False
                    break
                
                # 执行循环步骤
                loop_result = await self._execute_loop_step(task_id, sub_task_results, loop_state)
                
                # 更新循环状态
                loop_state["loop_count"] += 1
                loop_state["last_loop_time"] = datetime.now()
                loop_state["info_requirements"] = loop_result.get("info_requirements", [])
                loop_state["user_inputs"] = loop_result.get("user_inputs", [])
                loop_state["integrated_info"] = loop_result.get("integrated_info", {})
                
                # 检查是否应该继续
                loop_state["should_continue"] = await self._should_continue_loop(loop_state)
                
                # 检查超时
                if (datetime.now() - loop_state["start_time"]).total_seconds() > self.config["timeout"]:
                    loop_state["timeout"] = True
                    self.logger.warning(f"任务 {task_id} 的信息补充循环超时")
                
                # 等待循环间隔
                if loop_state["should_continue"] and not loop_state["timeout"]:
                    await asyncio.sleep(self.config["loop_interval"])
            
            # 构建循环执行结果
            execution_result = {
                "task_id": task_id,
                "loop_count": loop_state["loop_count"],
                "start_time": loop_state["start_time"],
                "end_time": datetime.now(),
                "duration": (datetime.now() - loop_state["start_time"]).total_seconds(),
                "info_requirements": loop_state["info_requirements"],
                "user_inputs": loop_state["user_inputs"],
                "integrated_info": loop_state["integrated_info"],
                "timeout": loop_state["timeout"],
                "completed": not loop_state["should_continue"]
            }
            
            # 保存循环执行结果
            await self.task_history_manager.create_info_gathering_loop(
                task_id=task_id,
                loop_count=loop_state["loop_count"],
                info_requirements=loop_state["info_requirements"],
                user_inputs=loop_state["user_inputs"],
                integrated_info=loop_state["integrated_info"],
                timeout=loop_state["timeout"],
                completed=not loop_state["should_continue"]
            )
            
            # 清理循环状态
            if task_id in self.loop_states:
                del self.loop_states[task_id]
            
            self.logger.info(f"任务 {task_id} 的信息补充循环执行完成")
            return execution_result
        except Exception as e:
            # 清理循环状态
            if task_id in self.loop_states:
                del self.loop_states[task_id]
            
            raise LoopControlError(f"执行信息补充循环失败: {str(e)}")
    
    async def _check_loop_conditions(self, loop_state: Dict) -> bool:
        """
        检查循环条件
        
        Args:
            loop_state: 循环状态
            
        Returns:
            是否满足循环条件
        """
        try:
            # 检查最大循环次数
            if loop_state["loop_count"] >= self.config["max_loops"]:
                self.logger.info(f"已达到最大循环次数 {self.config['max_loops']}")
                return False
            
            return True
        except Exception as e:
            raise LoopControlError(f"检查循环条件失败: {str(e)}")
    
    async def _execute_loop_step(self, task_id: int, sub_task_results: List[Dict], loop_state: Dict) -> Dict:
        """
        执行循环步骤
        
        Args:
            task_id: 任务ID
            sub_task_results: 子任务结果列表
            loop_state: 循环状态
            
        Returns:
            循环步骤执行结果
        """
        try:
            self.logger.info(f"执行任务 {task_id} 的信息补充循环步骤 {loop_state['loop_count'] + 1}")
            
            # 1. 检测信息需求
            detection_result = await self.info_requirement_detector.detect_info_requirements(
                task_id=task_id,
                sub_task_results=sub_task_results
            )
            
            info_requirements = detection_result.get("info_requirements", [])
            
            # 2. 检查是否有足够的信息需求
            if len(info_requirements) < self.config["min_info_requirements"]:
                self.logger.info(f"信息需求数量不足 ({len(info_requirements)} < {self.config['min_info_requirements']})")
                return {
                    "info_requirements": info_requirements,
                    "user_inputs": [],
                    "integrated_info": loop_state["integrated_info"]
                }
            
            # 3. 处理用户输入
            user_input_result = await self.user_input_processor.process_user_input(
                task_id=task_id,
                info_requirements=info_requirements
            )
            
            user_inputs = user_input_result.get("user_inputs", [])
            
            # 4. 整合用户输入
            integration_result = await self.info_integration_mechanism.integrate_user_input(
                task_id=task_id,
                user_inputs=user_inputs
            )
            
            integrated_info = integration_result.get("merged_inputs", {})
            
            # 5. 更新子任务结果
            updated_sub_task_results = await self._update_sub_task_results(
                task_id, sub_task_results, integrated_info
            )
            
            # 6. 构建步骤执行结果
            step_result = {
                "info_requirements": info_requirements,
                "user_inputs": user_inputs,
                "integrated_info": integrated_info,
                "updated_sub_task_results": updated_sub_task_results
            }
            
            self.logger.info(f"任务 {task_id} 的信息补充循环步骤 {loop_state['loop_count'] + 1} 执行完成")
            return step_result
        except Exception as e:
            raise LoopControlError(f"执行循环步骤失败: {str(e)}")
    
    async def _update_sub_task_results(self, task_id: int, sub_task_results: List[Dict], 
                                     integrated_info: Dict) -> List[Dict]:
        """
        更新子任务结果
        
        Args:
            task_id: 任务ID
            sub_task_results: 子任务结果列表
            integrated_info: 整合后的信息
            
        Returns:
            更新后的子任务结果列表
        """
        try:
            updated_sub_task_results = []
            
            for sub_task_result in sub_task_results:
                sub_task_id = sub_task_result.get("sub_task_id", "")
                result_content = sub_task_result.get("result", {})
                
                # 根据整合的信息更新结果
                updated_result_content = await self._update_result_content(
                    result_content, integrated_info
                )
                
                # 更新子任务结果
                updated_sub_task_result = dict(sub_task_result)
                updated_sub_task_result["result"] = updated_result_content
                
                updated_sub_task_results.append(updated_sub_task_result)
            
            return updated_sub_task_results
        except Exception as e:
            raise LoopControlError(f"更新子任务结果失败: {str(e)}")
    
    async def _update_result_content(self, result_content: Dict, integrated_info: Dict) -> Dict:
        """
        更新结果内容
        
        Args:
            result_content: 结果内容
            integrated_info: 整合后的信息
            
        Returns:
            更新后的结果内容
        """
        try:
            # 简化实现：将整合的信息添加到结果内容中
            updated_result_content = dict(result_content)
            
            # 添加用户偏好
            user_preferences = integrated_info.get("user_preferences", {})
            if user_preferences:
                updated_result_content["user_preferences"] = user_preferences
            
            # 添加上下文信息
            context_info = integrated_info.get("context_info", {})
            if context_info:
                if "context" not in updated_result_content:
                    updated_result_content["context"] = {}
                updated_result_content["context"].update(context_info)
            
            # 添加约束条件
            constraints = integrated_info.get("constraints", {})
            if constraints:
                if "constraints" not in updated_result_content:
                    updated_result_content["constraints"] = {}
                updated_result_content["constraints"].update(constraints)
            
            # 添加技术细节
            technical_details = integrated_info.get("technical_details", {})
            if technical_details:
                if "technical_details" not in updated_result_content:
                    updated_result_content["technical_details"] = {}
                updated_result_content["technical_details"].update(technical_details)
            
            # 添加示例
            examples = integrated_info.get("examples", {})
            if examples:
                if "examples" not in updated_result_content:
                    updated_result_content["examples"] = {}
                updated_result_content["examples"].update(examples)
            
            # 添加质量改进
            quality_improvements = integrated_info.get("quality_improvements", {})
            if quality_improvements:
                if "quality_improvements" not in updated_result_content:
                    updated_result_content["quality_improvements"] = {}
                updated_result_content["quality_improvements"].update(quality_improvements)
            
            return updated_result_content
        except Exception as e:
            raise LoopControlError(f"更新结果内容失败: {str(e)}")
    
    async def _should_continue_loop(self, loop_state: Dict) -> bool:
        """
        判断是否应该继续循环
        
        Args:
            loop_state: 循环状态
            
        Returns:
            是否应该继续循环
        """
        try:
            # 如果配置为不自动继续，则停止循环
            if not self.config["auto_continue"]:
                return False
            
            # 获取信息需求
            info_requirements = loop_state.get("info_requirements", [])
            
            # 如果没有信息需求，则停止循环
            if not info_requirements:
                return False
            
            # 计算优先级分数
            priority_score = await self._calculate_priority_score(info_requirements)
            
            # 如果优先级分数低于阈值，则停止循环
            if priority_score < self.config["medium_priority_threshold"]:
                return False
            
            return True
        except Exception as e:
            raise LoopControlError(f"判断是否应该继续循环失败: {str(e)}")
    
    async def _calculate_priority_score(self, info_requirements: List[Dict]) -> float:
        """
        计算优先级分数
        
        Args:
            info_requirements: 信息需求列表
            
        Returns:
            优先级分数
        """
        try:
            if not info_requirements:
                return 0.0
            
            # 计算加权优先级分数
            total_weight = 0
            weighted_score = 0
            
            for requirement in info_requirements:
                priority = requirement.get("priority", "medium")
                
                # 根据优先级确定权重
                if priority == "high":
                    weight = 1.0
                    score = 1.0
                elif priority == "medium":
                    weight = 0.7
                    score = 0.5
                else:  # low
                    weight = 0.3
                    score = 0.2
                
                total_weight += weight
                weighted_score += weight * score
            
            # 计算平均分数
            if total_weight > 0:
                return weighted_score / total_weight
            else:
                return 0.0
        except Exception as e:
            raise LoopControlError(f"计算优先级分数失败: {str(e)}")
    
    async def get_loop_state(self, task_id: int) -> Dict:
        """
        获取循环状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            循环状态
        """
        try:
            return self.loop_states.get(task_id, {})
        except Exception as e:
            raise LoopControlError(f"获取循环状态失败: {str(e)}")
    
    async def get_info_gathering_loop(self, task_id: int) -> Dict:
        """
        获取信息补充循环结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            信息补充循环结果
        """
        try:
            loop_result = await self.task_history_manager.get_info_gathering_loop(task_id)
            return loop_result
        except Exception as e:
            raise LoopControlError(f"获取信息补充循环结果失败: {str(e)}")
    
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
                self.logger.info(f"设置循环控制配置: {key} = {value}")
                return True
            else:
                self.logger.warning(f"未知的循环控制配置键: {key}")
                return False
        except Exception as e:
            raise LoopControlError(f"设置配置失败: {str(e)}")
    
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
            raise LoopControlError(f"获取配置失败: {str(e)}")
    
    async def get_loop_control_stats(self, days: int = 30) -> Dict:
        """
        获取循环控制统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        try:
            # 获取信息补充循环统计
            stats = await self.task_history_manager.get_info_gathering_loop_statistics(days)
            
            return stats
        except Exception as e:
            raise LoopControlError(f"获取循环控制统计信息失败: {str(e)}")
    
    async def stop_loop(self, task_id: int) -> bool:
        """
        停止循环
        
        Args:
            task_id: 任务ID
            
        Returns:
            停止是否成功
        """
        try:
            if task_id in self.loop_states:
                loop_state = self.loop_states[task_id]
                loop_state["should_continue"] = False
                self.logger.info(f"已停止任务 {task_id} 的信息补充循环")
                return True
            else:
                self.logger.warning(f"任务 {task_id} 没有正在执行的信息补充循环")
                return False
        except Exception as e:
            raise LoopControlError(f"停止循环失败: {str(e)}")