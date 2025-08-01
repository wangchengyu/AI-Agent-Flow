"""
信息整合机制

负责整合用户输入和任务信息，
包括信息映射、信息合并和信息更新等功能。
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable

from ..database.task_history_manager import TaskHistoryManager
from ..rag.knowledge_manager import KnowledgeManager
from ..utils.exceptions import InfoIntegrationError


class InfoIntegrationMechanism:
    """信息整合机制，负责整合用户输入和任务信息"""
    
    def __init__(self, db_manager, knowledge_manager: KnowledgeManager):
        """
        初始化信息整合机制
        
        Args:
            db_manager: 数据库管理器
            knowledge_manager: 知识管理器
        """
        self.db_manager = db_manager
        self.knowledge_manager = knowledge_manager
        self.task_history_manager = TaskHistoryManager(db_manager)
        
        # 信息映射规则
        self.info_mapping_rules = {
            "user_preference": {
                "description": "用户偏好",
                "mapper": self._map_user_preference
            },
            "context_info": {
                "description": "上下文信息",
                "mapper": self._map_context_info
            },
            "constraint": {
                "description": "约束条件",
                "mapper": self._map_constraint
            },
            "technical_detail": {
                "description": "技术细节",
                "mapper": self._map_technical_detail
            },
            "example": {
                "description": "示例",
                "mapper": self._map_example
            },
            "quality_improvement": {
                "description": "质量改进",
                "mapper": self._map_quality_improvement
            }
        }
        
        # 信息合并策略
        self.info_merge_strategies = {
            "replace": {
                "description": "替换",
                "merger": self._merge_replace
            },
            "append": {
                "description": "追加",
                "merger": self._merge_append
            },
            "prepend": {
                "description": "前置",
                "merger": self._merge_prepend
            },
            "merge": {
                "description": "合并",
                "merger": self._merge_merge
            },
            "update": {
                "description": "更新",
                "merger": self._merge_update
            }
        }
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("信息整合机制初始化完成")
    
    async def initialize(self):
        """初始化信息整合机制"""
        try:
            self.logger.info("信息整合机制初始化完成")
        except Exception as e:
            raise InfoIntegrationError(f"初始化信息整合机制失败: {str(e)}")
    
    async def integrate_user_input(self, task_id: int, user_inputs: List[Dict]) -> Dict:
        """
        整合用户输入
        
        Args:
            task_id: 任务ID
            user_inputs: 用户输入列表
            
        Returns:
            信息整合结果
        """
        try:
            self.logger.info(f"开始整合任务 {task_id} 的用户输入")
            
            # 获取任务信息
            task = await self.task_history_manager.get_task(task_id)
            if not task:
                raise InfoIntegrationError(f"任务 {task_id} 不存在")
            
            # 1. 映射用户输入
            mapped_inputs = await self._map_user_inputs(user_inputs)
            
            # 2. 合并用户输入
            merged_inputs = await self._merge_user_inputs(mapped_inputs)
            
            # 3. 更新任务信息
            updated_task = await self._update_task_info(task_id, merged_inputs)
            
            # 4. 更新子任务信息
            updated_sub_tasks = await self._update_sub_task_info(task_id, merged_inputs)
            
            # 5. 构建整合结果
            integration_result = {
                "task_id": task_id,
                "mapped_inputs": mapped_inputs,
                "merged_inputs": merged_inputs,
                "updated_task": updated_task,
                "updated_sub_tasks": updated_sub_tasks,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # 6. 保存整合结果
            await self.task_history_manager.create_info_integration(
                task_id=task_id,
                mapped_inputs=mapped_inputs,
                merged_inputs=merged_inputs,
                updated_task=updated_task,
                updated_sub_tasks=updated_sub_tasks
            )
            
            self.logger.info(f"任务 {task_id} 的用户输入整合完成")
            return integration_result
        except Exception as e:
            raise InfoIntegrationError(f"整合用户输入失败: {str(e)}")
    
    async def _map_user_inputs(self, user_inputs: List[Dict]) -> List[Dict]:
        """
        映射用户输入
        
        Args:
            user_inputs: 用户输入列表
            
        Returns:
            映射后的用户输入列表
        """
        try:
            mapped_inputs = []
            
            for user_input in user_inputs:
                requirement_type = user_input.get("requirement_type", "")
                formatted_value = user_input.get("formatted_value", "")
                
                # 根据需求类型确定映射规则
                mapping_rule = self._determine_mapping_rule(requirement_type)
                
                # 应用映射规则
                if mapping_rule:
                    mapper = mapping_rule["mapper"]
                    mapped_value = await mapper(formatted_value, user_input)
                else:
                    # 默认映射
                    mapped_value = {
                        "type": "general_info",
                        "value": formatted_value,
                        "source": "user_input"
                    }
                
                # 添加映射结果
                user_input["mapped_value"] = mapped_value
                mapped_inputs.append(user_input)
            
            return mapped_inputs
        except Exception as e:
            raise InfoIntegrationError(f"映射用户输入失败: {str(e)}")
    
    def _determine_mapping_rule(self, requirement_type: str) -> Optional[Dict]:
        """
        确定映射规则
        
        Args:
            requirement_type: 需求类型
            
        Returns:
            映射规则
        """
        try:
            # 根据需求类型确定映射规则
            if "user_preference" in requirement_type:
                return self.info_mapping_rules["user_preference"]
            elif "context_info" in requirement_type or "background" in requirement_type:
                return self.info_mapping_rules["context_info"]
            elif "constraint" in requirement_type or "limit" in requirement_type:
                return self.info_mapping_rules["constraint"]
            elif "technical_detail" in requirement_type or "implementation" in requirement_type:
                return self.info_mapping_rules["technical_detail"]
            elif "example" in requirement_type or "reference" in requirement_type:
                return self.info_mapping_rules["example"]
            elif "quality_improvement" in requirement_type:
                return self.info_mapping_rules["quality_improvement"]
            else:
                return None
        except Exception as e:
            self.logger.error(f"确定映射规则失败: {str(e)}")
            return None
    
    async def _map_user_preference(self, value: Any, user_input: Dict) -> Dict:
        """
        映射用户偏好
        
        Args:
            value: 值
            user_input: 用户输入
            
        Returns:
            映射后的值
        """
        try:
            question = user_input.get("question", "")
            
            # 根据问题确定偏好类型
            if "风格" in question:
                preference_type = "style"
            elif "颜色" in question:
                preference_type = "color"
            elif "大小" in question:
                preference_type = "size"
            elif "格式" in question:
                preference_type = "format"
            else:
                preference_type = "general"
            
            return {
                "type": "user_preference",
                "preference_type": preference_type,
                "value": value,
                "source": "user_input"
            }
        except Exception as e:
            self.logger.error(f"映射用户偏好失败: {str(e)}")
            return {
                "type": "user_preference",
                "preference_type": "general",
                "value": value,
                "source": "user_input"
            }
    
    async def _map_context_info(self, value: Any, user_input: Dict) -> Dict:
        """
        映射上下文信息
        
        Args:
            value: 值
            user_input: 用户_input
            
        Returns:
            映射后的值
        """
        try:
            question = user_input.get("question", "")
            
            # 根据问题确定上下文类型
            if "背景" in question:
                context_type = "background"
            elif "环境" in question:
                context_type = "environment"
            elif "场景" in question:
                context_type = "scenario"
            else:
                context_type = "general"
            
            return {
                "type": "context_info",
                "context_type": context_type,
                "value": value,
                "source": "user_input"
            }
        except Exception as e:
            self.logger.error(f"映射上下文信息失败: {str(e)}")
            return {
                "type": "context_info",
                "context_type": "general",
                "value": value,
                "source": "user_input"
            }
    
    async def _map_constraint(self, value: Any, user_input: Dict) -> Dict:
        """
        映射约束条件
        
        Args:
            value: 值
            user_input: 用户输入
            
        Returns:
            映射后的值
        """
        try:
            question = user_input.get("question", "")
            
            # 根据问题确定约束类型
            if "时间" in question:
                constraint_type = "time"
            elif "预算" in question or "成本" in question:
                constraint_type = "budget"
            elif "资源" in question:
                constraint_type = "resource"
            elif "技术" in question:
                constraint_type = "technical"
            else:
                constraint_type = "general"
            
            return {
                "type": "constraint",
                "constraint_type": constraint_type,
                "value": value,
                "source": "user_input"
            }
        except Exception as e:
            self.logger.error(f"映射约束条件失败: {str(e)}")
            return {
                "type": "constraint",
                "constraint_type": "general",
                "value": value,
                "source": "user_input"
            }
    
    async def _map_technical_detail(self, value: Any, user_input: Dict) -> Dict:
        """
        映射技术细节
        
        Args:
            value: 值
            user_input: 用户输入
            
        Returns:
            映射后的值
        """
        try:
            question = user_input.get("question", "")
            
            # 根据问题确定技术细节类型
            if "架构" in question:
                detail_type = "architecture"
            elif "算法" in question:
                detail_type = "algorithm"
            elif "数据结构" in question:
                detail_type = "data_structure"
            elif "接口" in question:
                detail_type = "interface"
            else:
                detail_type = "general"
            
            return {
                "type": "technical_detail",
                "detail_type": detail_type,
                "value": value,
                "source": "user_input"
            }
        except Exception as e:
            self.logger.error(f"映射技术细节失败: {str(e)}")
            return {
                "type": "technical_detail",
                "detail_type": "general",
                "value": value,
                "source": "user_input"
            }
    
    async def _map_example(self, value: Any, user_input: Dict) -> Dict:
        """
        映射示例
        
        Args:
            value: 值
            user_input: 用户输入
            
        Returns:
            映射后的值
        """
        try:
            question = user_input.get("question", "")
            
            # 根据问题确定示例类型
            if "输入" in question:
                example_type = "input"
            elif "输出" in question:
                example_type = "output"
            elif "用例" in question:
                example_type = "use_case"
            else:
                example_type = "general"
            
            return {
                "type": "example",
                "example_type": example_type,
                "value": value,
                "source": "user_input"
            }
        except Exception as e:
            self.logger.error(f"映射示例失败: {str(e)}")
            return {
                "type": "example",
                "example_type": "general",
                "value": value,
                "source": "user_input"
            }
    
    async def _map_quality_improvement(self, value: Any, user_input: Dict) -> Dict:
        """
        映射质量改进
        
        Args:
            value: 值
            user_input: 用户输入
            
        Returns:
            映射后的值
        """
        try:
            question = user_input.get("question", "")
            
            # 根据问题确定质量改进类型
            if "完整性" in question:
                improvement_type = "completeness"
            elif "准确性" in question:
                improvement_type = "accuracy"
            elif "相关性" in question:
                improvement_type = "relevance"
            elif "清晰度" in question:
                improvement_type = "clarity"
            else:
                improvement_type = "general"
            
            return {
                "type": "quality_improvement",
                "improvement_type": improvement_type,
                "value": value,
                "source": "user_input"
            }
        except Exception as e:
            self.logger.error(f"映射质量改进失败: {str(e)}")
            return {
                "type": "quality_improvement",
                "improvement_type": "general",
                "value": value,
                "source": "user_input"
            }
    
    async def _merge_user_inputs(self, mapped_inputs: List[Dict]) -> Dict:
        """
        合并用户输入
        
        Args:
            mapped_inputs: 映射后的用户输入列表
            
        Returns:
            合并后的用户输入
        """
        try:
            merged_inputs = {
                "user_preferences": {},
                "context_info": {},
                "constraints": {},
                "technical_details": {},
                "examples": {},
                "quality_improvements": {},
                "general_info": []
            }
            
            for user_input in mapped_inputs:
                mapped_value = user_input.get("mapped_value", {})
                info_type = mapped_value.get("type", "general_info")
                
                # 根据信息类型合并
                if info_type == "user_preference":
                    preference_type = mapped_value.get("preference_type", "general")
                    merged_inputs["user_preferences"][preference_type] = mapped_value["value"]
                
                elif info_type == "context_info":
                    context_type = mapped_value.get("context_type", "general")
                    merged_inputs["context_info"][context_type] = mapped_value["value"]
                
                elif info_type == "constraint":
                    constraint_type = mapped_value.get("constraint_type", "general")
                    merged_inputs["constraints"][constraint_type] = mapped_value["value"]
                
                elif info_type == "technical_detail":
                    detail_type = mapped_value.get("detail_type", "general")
                    merged_inputs["technical_details"][detail_type] = mapped_value["value"]
                
                elif info_type == "example":
                    example_type = mapped_value.get("example_type", "general")
                    if example_type not in merged_inputs["examples"]:
                        merged_inputs["examples"][example_type] = []
                    merged_inputs["examples"][example_type].append(mapped_value["value"])
                
                elif info_type == "quality_improvement":
                    improvement_type = mapped_value.get("improvement_type", "general")
                    merged_inputs["quality_improvements"][improvement_type] = mapped_value["value"]
                
                else:
                    merged_inputs["general_info"].append({
                        "value": mapped_value["value"],
                        "source": mapped_value["source"]
                    })
            
            return merged_inputs
        except Exception as e:
            raise InfoIntegrationError(f"合并用户输入失败: {str(e)}")
    
    async def _update_task_info(self, task_id: int, merged_inputs: Dict) -> Dict:
        """
        更新任务信息
        
        Args:
            task_id: 任务ID
            merged_inputs: 合并后的用户输入
            
        Returns:
            更新后的任务信息
        """
        try:
            # 获取任务信息
            task = await self.task_history_manager.get_task(task_id)
            if not task:
                raise InfoIntegrationError(f"任务 {task_id} 不存在")
            
            # 获取任务上下文
            context = task.get("context", {})
            
            # 更新上下文
            updated_context = await self._update_context(context, merged_inputs)
            
            # 更新任务
            updated_task = await self.task_history_manager.update_task_context(
                task_id=task_id,
                context=updated_context
            )
            
            return updated_task
        except Exception as e:
            raise InfoIntegrationError(f"更新任务信息失败: {str(e)}")
    
    async def _update_context(self, context: Dict, merged_inputs: Dict) -> Dict:
        """
        更新上下文
        
        Args:
            context: 上下文
            merged_inputs: 合并后的用户输入
            
        Returns:
            更新后的上下文
        """
        try:
            # 确保上下文存在
            if not context:
                context = {}
            
            # 更新用户偏好
            user_preferences = merged_inputs.get("user_preferences", {})
            if user_preferences:
                if "user_preferences" not in context:
                    context["user_preferences"] = {}
                
                for pref_type, pref_value in user_preferences.items():
                    context["user_preferences"][pref_type] = pref_value
            
            # 更新上下文信息
            context_info = merged_inputs.get("context_info", {})
            if context_info:
                if "context_info" not in context:
                    context["context_info"] = {}
                
                for info_type, info_value in context_info.items():
                    context["context_info"][info_type] = info_value
            
            # 更新约束条件
            constraints = merged_inputs.get("constraints", {})
            if constraints:
                if "constraints" not in context:
                    context["constraints"] = {}
                
                for constraint_type, constraint_value in constraints.items():
                    context["constraints"][constraint_type] = constraint_value
            
            # 更新技术细节
            technical_details = merged_inputs.get("technical_details", {})
            if technical_details:
                if "technical_details" not in context:
                    context["technical_details"] = {}
                
                for detail_type, detail_value in technical_details.items():
                    context["technical_details"][detail_type] = detail_value
            
            # 更新示例
            examples = merged_inputs.get("examples", {})
            if examples:
                if "examples" not in context:
                    context["examples"] = {}
                
                for example_type, example_values in examples.items():
                    if example_type not in context["examples"]:
                        context["examples"][example_type] = []
                    
                    for example_value in example_values:
                        if example_value not in context["examples"][example_type]:
                            context["examples"][example_type].append(example_value)
            
            # 更新质量改进
            quality_improvements = merged_inputs.get("quality_improvements", {})
            if quality_improvements:
                if "quality_improvements" not in context:
                    context["quality_improvements"] = {}
                
                for improvement_type, improvement_value in quality_improvements.items():
                    context["quality_improvements"][improvement_type] = improvement_value
            
            # 更新一般信息
            general_info = merged_inputs.get("general_info", [])
            if general_info:
                if "general_info" not in context:
                    context["general_info"] = []
                
                for info in general_info:
                    if info not in context["general_info"]:
                        context["general_info"].append(info)
            
            return context
        except Exception as e:
            raise InfoIntegrationError(f"更新上下文失败: {str(e)}")
    
    async def _update_sub_task_info(self, task_id: int, merged_inputs: Dict) -> List[Dict]:
        """
        更新子任务信息
        
        Args:
            task_id: 任务ID
            merged_inputs: 合并后的用户输入
            
        Returns:
            更新后的子任务信息列表
        """
        try:
            # 获取子任务列表
            sub_tasks = await self.task_history_manager.get_sub_tasks(task_id)
            
            updated_sub_tasks = []
            
            # 更新每个子任务
            for sub_task in sub_tasks:
                sub_task_id = sub_task.get("id")
                
                # 获取子任务上下文
                context = sub_task.get("context", {})
                
                # 更新上下文
                updated_context = await self._update_context(context, merged_inputs)
                
                # 更新子任务
                updated_sub_task = await self.task_history_manager.update_sub_task_context(
                    sub_task_id=sub_task_id,
                    context=updated_context
                )
                
                updated_sub_tasks.append(updated_sub_task)
            
            return updated_sub_tasks
        except Exception as e:
            raise InfoIntegrationError(f"更新子任务信息失败: {str(e)}")
    
    # 信息合并方法
    async def _merge_replace(self, original: Any, new: Any) -> Any:
        """
        替换合并
        
        Args:
            original: 原始值
            new: 新值
            
        Returns:
            合并后的值
        """
        return new
    
    async def _merge_append(self, original: Any, new: Any) -> Any:
        """
        追加合并
        
        Args:
            original: 原始值
            new: 新值
            
        Returns:
            合并后的值
        """
        if isinstance(original, str) and isinstance(new, str):
            return original + "\n" + new
        elif isinstance(original, list):
            if isinstance(new, list):
                return original + new
            else:
                return original + [new]
        else:
            return new
    
    async def _merge_prepend(self, original: Any, new: Any) -> Any:
        """
        前置合并
        
        Args:
            original: 原始值
            new: 新值
            
        Returns:
            合并后的值
        """
        if isinstance(original, str) and isinstance(new, str):
            return new + "\n" + original
        elif isinstance(original, list):
            if isinstance(new, list):
                return new + original
            else:
                return [new] + original
        else:
            return new
    
    async def _merge_merge(self, original: Any, new: Any) -> Any:
        """
        合并合并
        
        Args:
            original: 原始值
            new: 新值
            
        Returns:
            合并后的值
        """
        if isinstance(original, dict) and isinstance(new, dict):
            result = dict(original)
            result.update(new)
            return result
        elif isinstance(original, list) and isinstance(new, list):
            return list(set(original + new))
        else:
            return new
    
    async def _merge_update(self, original: Any, new: Any) -> Any:
        """
        更新合并
        
        Args:
            original: 原始值
            new: 新值
            
        Returns:
            合并后的值
        """
        if isinstance(original, dict) and isinstance(new, dict):
            result = dict(original)
            for key, value in new.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = await self._merge_update(result[key], value)
                else:
                    result[key] = value
            return result
        else:
            return new
    
    async def get_info_integration(self, task_id: int) -> Dict:
        """
        获取信息整合结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            信息整合结果
        """
        try:
            integration_result = await self.task_history_manager.get_info_integration(task_id)
            return integration_result
        except Exception as e:
            raise InfoIntegrationError(f"获取信息整合结果失败: {str(e)}")
    
    async def add_info_mapping_rule(self, name: str, mapper: Callable, description: str) -> bool:
        """
        添加信息映射规则
        
        Args:
            name: 规则名称
            mapper: 映射器函数
            description: 规则描述
            
        Returns:
            添加是否成功
        """
        try:
            self.info_mapping_rules[name] = {
                "description": description,
                "mapper": mapper
            }
            
            self.logger.info(f"添加信息映射规则: {name}")
            return True
        except Exception as e:
            raise InfoIntegrationError(f"添加信息映射规则失败: {str(e)}")
    
    async def add_info_merge_strategy(self, name: str, merger: Callable, description: str) -> bool:
        """
        添加信息合并策略
        
        Args:
            name: 策略名称
            merger: 合并器函数
            description: 策略描述
            
        Returns:
            添加是否成功
        """
        try:
            self.info_merge_strategies[name] = {
                "description": description,
                "merger": merger
            }
            
            self.logger.info(f"添加信息合并策略: {name}")
            return True
        except Exception as e:
            raise InfoIntegrationError(f"添加信息合并策略失败: {str(e)}")
    
    async def get_info_integration_stats(self, days: int = 30) -> Dict:
        """
        获取信息整合统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        try:
            # 获取信息整合统计
            stats = await self.task_history_manager.get_info_integration_statistics(days)
            
            return stats
        except Exception as e:
            raise InfoIntegrationError(f"获取信息整合统计信息失败: {str(e)}")