"""
信息补充循环

负责在任务执行过程中检测信息需求，
向用户请求补充信息，并整合用户输入到任务执行中。
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable

from ..database.task_history_manager import TaskHistoryManager
from ..rag.knowledge_manager import KnowledgeManager
from ..utils.exceptions import InfoGatheringLoopError


class InfoGatheringLoop:
    """信息补充循环，负责处理信息需求检测和用户输入整合"""
    
    def __init__(self, db_manager, knowledge_manager: KnowledgeManager):
        """
        初始化信息补充循环
        
        Args:
            db_manager: 数据库管理器
            knowledge_manager: 知识管理器
        """
        self.db_manager = db_manager
        self.knowledge_manager = knowledge_manager
        self.task_history_manager = TaskHistoryManager(db_manager)
        
        # 信息需求检测器
        self.info_detectors = {
            "missing_data": self._detect_missing_data,
            "ambiguous_request": self._detect_ambiguous_request,
            "insufficient_context": self._detect_insufficient_context,
            "unclear_goal": self._detect_unclear_goal
        }
        
        # 用户输入处理器
        self.input_processors = {
            "clarification": self._process_clarification,
            "additional_data": self._process_additional_data,
            "preference": self._process_preference,
            "correction": self._process_correction
        }
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """初始化信息补充循环"""
        try:
            self.logger.info("信息补充循环初始化完成")
        except Exception as e:
            raise InfoGatheringLoopError(f"初始化信息补充循环失败: {str(e)}")
    
    async def process_results(self, task_id: int, results: List[Dict], 
                            user_id: Optional[int] = None) -> List[Dict]:
        """
        处理任务结果，检测信息需求并请求补充信息
        
        Args:
            task_id: 任务ID
            results: 子任务结果列表
            user_id: 用户ID
            
        Returns:
            处理后的结果列表
        """
        try:
            self.logger.info(f"开始处理任务 {task_id} 的结果")
            
            # 1. 检测信息需求
            info_needs = await self._detect_information_needs(task_id, results)
            
            # 2. 如果有信息需求，请求用户补充信息
            if info_needs:
                self.logger.info(f"检测到 {len(info_needs)} 个信息需求")
                
                # 请求用户补充信息
                user_inputs = await self._request_user_input(task_id, info_needs, user_id)
                
                # 3. 整合用户输入到结果中
                results = await self._integrate_user_input(task_id, results, user_inputs)
            
            self.logger.info(f"任务 {task_id} 的结果处理完成")
            return results
        except Exception as e:
            raise InfoGatheringLoopError(f"处理任务结果失败: {str(e)}")
    
    async def _detect_information_needs(self, task_id: int, results: List[Dict]) -> List[Dict]:
        """
        检测信息需求
        
        Args:
            task_id: 任务ID
            results: 子任务结果列表
            
        Returns:
            信息需求列表
        """
        try:
            info_needs = []
            
            # 获取任务信息
            task = await self.task_history_manager.get_task(task_id)
            if not task:
                raise InfoGatheringLoopError(f"任务 {task_id} 不存在")
            
            # 对每个结果应用信息需求检测器
            for result in results:
                for detector_name, detector_func in self.info_detectors.items():
                    need = await detector_func(task_id, task, result)
                    if need:
                        need["detector"] = detector_name
                        need["result_id"] = result.get("sub_task_id", "")
                        info_needs.append(need)
            
            # 去重
            unique_needs = []
            seen = set()
            
            for need in info_needs:
                # 创建唯一标识
                need_key = (need["type"], need["result_id"], need.get("field", ""))
                
                if need_key not in seen:
                    seen.add(need_key)
                    unique_needs.append(need)
            
            return unique_needs
        except Exception as e:
            raise InfoGatheringLoopError(f"检测信息需求失败: {str(e)}")
    
    async def _detect_missing_data(self, task_id: int, task: Dict, result: Dict) -> Optional[Dict]:
        """
        检测缺失数据
        
        Args:
            task_id: 任务ID
            task: 任务信息
            result: 子任务结果
            
        Returns:
            信息需求字典，如果没有需求则返回None
        """
        try:
            # 检查结果中是否有缺失数据
            if "error" in result:
                # 如果是错误，检查是否是数据缺失导致的
                error_msg = result["error"].lower()
                
                if any(keyword in error_msg for keyword in ["not found", "missing", "required", "empty"]):
                    return {
                        "type": "missing_data",
                        "description": f"执行子任务时发现缺失数据: {result['error']}",
                        "priority": "high",
                        "question": f"请提供缺失的数据: {result['error']}"
                    }
            
            # 检查结果内容是否为空
            if "result" in result and not result["result"]:
                return {
                    "type": "missing_data",
                    "description": "子任务结果为空，可能需要更多输入数据",
                    "priority": "medium",
                    "question": "请提供更多输入数据以生成结果"
                }
            
            return None
        except Exception as e:
            raise InfoGatheringLoopError(f"检测缺失数据失败: {str(e)}")
    
    async def _detect_ambiguous_request(self, task_id: int, task: Dict, result: Dict) -> Optional[Dict]:
        """
        检测模糊请求
        
        Args:
            task_id: 任务ID
            task: 任务信息
            result: 子任务结果
            
        Returns:
            信息需求字典，如果没有需求则返回None
        """
        try:
            # 检查任务描述是否模糊
            task_description = task["description"].lower()
            
            # 检查模糊关键词
            ambiguous_keywords = ["某些", "一些", "可能", "大概", "大约", "类似"]
            
            for keyword in ambiguous_keywords:
                if keyword in task_description:
                    return {
                        "type": "ambiguous_request",
                        "description": f"任务描述中包含模糊词语 '{keyword}'",
                        "priority": "medium",
                        "question": f"请澄清任务描述中的 '{keyword}' 具体指什么"
                    }
            
            # 检查结果中是否有模糊内容
            if "result" in result and isinstance(result["result"], dict):
                result_str = json.dumps(result["result"]).lower()
                
                for keyword in ambiguous_keywords:
                    if keyword in result_str:
                        return {
                            "type": "ambiguous_request",
                            "description": f"子任务结果中包含模糊词语 '{keyword}'",
                            "priority": "medium",
                            "question": f"请澄清结果中的 '{keyword}' 具体指什么"
                        }
            
            return None
        except Exception as e:
            raise InfoGatheringLoopError(f"检测模糊请求失败: {str(e)}")
    
    async def _detect_insufficient_context(self, task_id: int, task: Dict, result: Dict) -> Optional[Dict]:
        """
        检测上下文不足
        
        Args:
            task_id: 任务ID
            task: 任务信息
            result: 子任务结果
            
        Returns:
            信息需求字典，如果没有需求则返回None
        """
        try:
            # 检查任务上下文是否足够
            context = task.get("context", {})
            
            # 如果上下文为空或很小，可能需要更多信息
            if not context or len(context) < 3:
                return {
                    "type": "insufficient_context",
                    "description": "任务上下文信息不足",
                    "priority": "medium",
                    "question": "请提供更多任务上下文信息"
                }
            
            # 检查结果中是否有上下文不足的提示
            if "result" in result and isinstance(result["result"], dict):
                result_str = json.dumps(result["result"]).lower()
                
                if any(keyword in result_str for keyword in ["context", "background", "more information"]):
                    return {
                        "type": "insufficient_context",
                        "description": "子任务结果提示需要更多上下文信息",
                        "priority": "medium",
                        "question": "请提供更多任务上下文信息"
                    }
            
            return None
        except Exception as e:
            raise InfoGatheringLoopError(f"检测上下文不足失败: {str(e)}")
    
    async def _detect_unclear_goal(self, task_id: int, task: Dict, result: Dict) -> Optional[Dict]:
        """
        检测目标不明确
        
        Args:
            task_id: 任务ID
            task: 任务信息
            result: 子任务结果
            
        Returns:
            信息需求字典，如果没有需求则返回None
        """
        try:
            # 检查任务目标是否明确
            task_description = task["description"].lower()
            
            # 检查是否缺少明确的目标关键词
            goal_keywords = ["目标", "目的", "输出", "结果", "交付"]
            
            has_goal = any(keyword in task_description for keyword in goal_keywords)
            
            if not has_goal:
                return {
                    "type": "unclear_goal",
                    "description": "任务描述中缺少明确的目标或期望结果",
                    "priority": "high",
                    "question": "请明确任务的目标或期望结果是什么"
                }
            
            # 检查结果中是否有目标不明确的提示
            if "result" in result and isinstance(result["result"], dict):
                result_str = json.dumps(result["result"]).lower()
                
                if any(keyword in result_str for keyword in ["unclear", "not sure", "goal", "objective"]):
                    return {
                        "type": "unclear_goal",
                        "description": "子任务结果提示目标不明确",
                        "priority": "high",
                        "question": "请明确任务的目标或期望结果是什么"
                    }
            
            return None
        except Exception as e:
            raise InfoGatheringLoopError(f"检测目标不明确失败: {str(e)}")
    
    async def _request_user_input(self, task_id: int, info_needs: List[Dict], 
                                user_id: Optional[int] = None) -> List[Dict]:
        """
        请求用户补充信息
        
        Args:
            task_id: 任务ID
            info_needs: 信息需求列表
            user_id: 用户ID
            
        Returns:
            用户输入列表
        """
        try:
            user_inputs = []
            
            # 按优先级排序信息需求
            sorted_needs = sorted(info_needs, key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x["priority"], 2))
            
            # 记录信息需求
            for need in sorted_needs:
                await self.task_history_manager.create_info_need(
                    task_id=task_id,
                    need_type=need["type"],
                    description=need["description"],
                    priority=need["priority"],
                    question=need["question"]
                )
            
            # 在实际应用中，这里应该通过UI或其他方式向用户请求输入
            # 这里我们模拟用户输入
            for need in sorted_needs:
                # 模拟用户输入
                user_input = {
                    "need_id": need.get("id", ""),
                    "need_type": need["type"],
                    "question": need["question"],
                    "user_response": f"这是对 '{need['question']}' 的模拟回答",
                    "timestamp": time.time()
                }
                
                user_inputs.append(user_input)
                
                # 记录用户输入
                await self.task_history_manager.create_user_input(
                    task_id=task_id,
                    need_type=need["type"],
                    question=need["question"],
                    response=user_input["user_response"]
                )
            
            return user_inputs
        except Exception as e:
            raise InfoGatheringLoopError(f"请求用户补充信息失败: {str(e)}")
    
    async def _integrate_user_input(self, task_id: int, results: List[Dict], 
                                   user_inputs: List[Dict]) -> List[Dict]:
        """
        整合用户输入到结果中
        
        Args:
            task_id: 任务ID
            results: 子任务结果列表
            user_inputs: 用户输入列表
            
        Returns:
            整合后的结果列表
        """
        try:
            # 创建用户输入映射
            input_map = {}
            for user_input in user_inputs:
                need_type = user_input["need_type"]
                result_id = user_input.get("result_id", "")
                
                key = (need_type, result_id)
                input_map[key] = user_input
            
            # 整合用户输入到结果中
            integrated_results = []
            
            for result in results:
                result_id = result.get("sub_task_id", "")
                
                # 检查是否有相关的用户输入
                relevant_inputs = []
                for (need_type, input_result_id), user_input in input_map.items():
                    if input_result_id == result_id or input_result_id == "":
                        relevant_inputs.append(user_input)
                
                # 如果有相关输入，处理它们
                if relevant_inputs:
                    for user_input in relevant_inputs:
                        need_type = user_input["need_type"]
                        user_response = user_input["user_response"]
                        
                        # 根据输入类型应用相应的处理器
                        if need_type in self.input_processors:
                            result = await self.input_processors[need_type](result, user_response)
                        else:
                            # 默认处理：将用户输入添加到结果中
                            if "user_inputs" not in result:
                                result["user_inputs"] = []
                            
                            result["user_inputs"].append({
                                "type": need_type,
                                "question": user_input["question"],
                                "response": user_response
                            })
                
                integrated_results.append(result)
            
            return integrated_results
        except Exception as e:
            raise InfoGatheringLoopError(f"整合用户输入失败: {str(e)}")
    
    async def _process_clarification(self, result: Dict, user_response: str) -> Dict:
        """
        处理澄清类用户输入
        
        Args:
            result: 子任务结果
            user_response: 用户响应
            
        Returns:
            处理后的结果
        """
        try:
            # 将澄清信息添加到结果中
            if "clarifications" not in result:
                result["clarifications"] = []
            
            result["clarifications"].append(user_response)
            
            # 如果之前有错误，尝试重新处理
            if "error" in result:
                # 在实际应用中，这里可能会重新执行子任务
                # 这里我们只是标记错误已解决
                result["error_resolved"] = True
            
            return result
        except Exception as e:
            raise InfoGatheringLoopError(f"处理澄清类用户输入失败: {str(e)}")
    
    async def _process_additional_data(self, result: Dict, user_response: str) -> Dict:
        """
        处理附加数据类用户输入
        
        Args:
            result: 子任务结果
            user_response: 用户响应
            
        Returns:
            处理后的结果
        """
        try:
            # 将附加数据添加到结果中
            if "additional_data" not in result:
                result["additional_data"] = []
            
            result["additional_data"].append(user_response)
            
            # 如果之前结果为空，尝试使用附加数据生成结果
            if "result" in result and not result["result"]:
                # 在实际应用中，这里可能会使用附加数据重新生成结果
                # 这里我们只是标记已添加附加数据
                result["data_added"] = True
            
            return result
        except Exception as e:
            raise InfoGatheringLoopError(f"处理附加数据类用户输入失败: {str(e)}")
    
    async def _process_preference(self, result: Dict, user_response: str) -> Dict:
        """
        处理偏好类用户输入
        
        Args:
            result: 子任务结果
            user_response: 用户响应
            
        Returns:
            处理后的结果
        """
        try:
            # 将偏好信息添加到结果中
            if "preferences" not in result:
                result["preferences"] = []
            
            result["preferences"].append(user_response)
            
            # 在实际应用中，这里可能会根据用户偏好调整结果
            # 这里我们只是标记已添加偏好
            result["preferences_applied"] = True
            
            return result
        except Exception as e:
            raise InfoGatheringLoopError(f"处理偏好类用户输入失败: {str(e)}")
    
    async def _process_correction(self, result: Dict, user_response: str) -> Dict:
        """
        处理纠正类用户输入
        
        Args:
            result: 子任务结果
            user_response: 用户响应
            
        Returns:
            处理后的结果
        """
        try:
            # 将纠正信息添加到结果中
            if "corrections" not in result:
                result["corrections"] = []
            
            result["corrections"].append(user_response)
            
            # 在实际应用中，这里可能会根据用户纠正重新生成结果
            # 这里我们只是标记已添加纠正
            result["corrections_applied"] = True
            
            return result
        except Exception as e:
            raise InfoGatheringLoopError(f"处理纠正类用户输入失败: {str(e)}")
    
    async def get_info_needs(self, task_id: int) -> List[Dict]:
        """
        获取任务的信息需求
        
        Args:
            task_id: 任务ID
            
        Returns:
            信息需求列表
        """
        try:
            info_needs = await self.task_history_manager.get_info_needs(task_id)
            return info_needs
        except Exception as e:
            raise InfoGatheringLoopError(f"获取信息需求失败: {str(e)}")
    
    async def get_user_inputs(self, task_id: int) -> List[Dict]:
        """
        获取任务的用户输入
        
        Args:
            task_id: 任务ID
            
        Returns:
            用户输入列表
        """
        try:
            user_inputs = await self.task_history_manager.get_user_inputs(task_id)
            return user_inputs
        except Exception as e:
            raise InfoGatheringLoopError(f"获取用户输入失败: {str(e)}")
    
    async def add_info_detector(self, name: str, detector_func: Callable) -> bool:
        """
        添加信息需求检测器
        
        Args:
            name: 检测器名称
            detector_func: 检测器函数
            
        Returns:
            添加是否成功
        """
        try:
            self.info_detectors[name] = detector_func
            self.logger.info(f"添加信息需求检测器: {name}")
            return True
        except Exception as e:
            raise InfoGatheringLoopError(f"添加信息需求检测器失败: {str(e)}")
    
    async def add_input_processor(self, name: str, processor_func: Callable) -> bool:
        """
        添加用户输入处理器
        
        Args:
            name: 处理器名称
            processor_func: 处理器函数
            
        Returns:
            添加是否成功
        """
        try:
            self.input_processors[name] = processor_func
            self.logger.info(f"添加用户输入处理器: {name}")
            return True
        except Exception as e:
            raise InfoGatheringLoopError(f"添加用户输入处理器失败: {str(e)}")
    
    async def get_info_gathering_stats(self, days: int = 30) -> Dict:
        """
        获取信息补充统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        try:
            # 获取信息需求统计
            info_needs_stats = await self.task_history_manager.get_info_needs_statistics(days)
            
            # 获取用户输入统计
            user_inputs_stats = await self.task_history_manager.get_user_inputs_statistics(days)
            
            return {
                "info_needs_stats": info_needs_stats,
                "user_inputs_stats": user_inputs_stats
            }
        except Exception as e:
            raise InfoGatheringLoopError(f"获取信息补充统计信息失败: {str(e)}")