"""
用户输入处理器

负责处理用户输入，包括输入验证、
输入解析和输入格式化等功能。
"""

import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable

from ..database.task_history_manager import TaskHistoryManager
from ..cli.interactive_interface import InteractiveInterface
from ..utils.exceptions import UserInputError


class UserInputProcessor:
    """用户输入处理器，负责处理用户输入"""
    
    def __init__(self, db_manager, interface: InteractiveInterface):
        """
        初始化用户输入处理器
        
        Args:
            db_manager: 数据库管理器
            interface: 交互式界面
        """
        self.db_manager = db_manager
        self.interface = interface
        self.task_history_manager = TaskHistoryManager(db_manager)
        
        # 输入验证规则
        self.validation_rules = {
            "required": {
                "description": "必填项",
                "validator": self._validate_required
            },
            "min_length": {
                "description": "最小长度",
                "validator": self._validate_min_length
            },
            "max_length": {
                "description": "最大长度",
                "validator": self._validate_max_length
            },
            "pattern": {
                "description": "正则表达式",
                "validator": self._validate_pattern
            },
            "numeric": {
                "description": "数字",
                "validator": self._validate_numeric
            },
            "integer": {
                "description": "整数",
                "validator": self._validate_integer
            },
            "float": {
                "description": "浮点数",
                "validator": self._validate_float
            },
            "boolean": {
                "description": "布尔值",
                "validator": self._validate_boolean
            },
            "email": {
                "description": "电子邮件",
                "validator": self._validate_email
            },
            "url": {
                "description": "URL",
                "validator": self._validate_url
            },
            "json": {
                "description": "JSON",
                "validator": self._validate_json
            }
        }
        
        # 输入解析器
        self.input_parsers = {
            "text": self._parse_text,
            "number": self._parse_number,
            "boolean": self._parse_boolean,
            "json": self._parse_json,
            "list": self._parse_list,
            "choice": self._parse_choice
        }
        
        # 输入格式化器
        self.input_formatters = {
            "text": self._format_text,
            "number": self._format_number,
            "boolean": self._format_boolean,
            "json": self._format_json,
            "list": self._format_list
        }
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("用户输入处理器初始化完成")
    
    async def initialize(self):
        """初始化用户输入处理器"""
        try:
            self.logger.info("用户输入处理器初始化完成")
        except Exception as e:
            raise UserInputError(f"初始化用户输入处理器失败: {str(e)}")
    
    async def process_user_input(self, task_id: int, info_requirements: List[Dict]) -> Dict:
        """
        处理用户输入
        
        Args:
            task_id: 任务ID
            info_requirements: 信息需求列表
            
        Returns:
            用户输入处理结果
        """
        try:
            self.logger.info(f"开始处理任务 {task_id} 的用户输入")
            
            # 获取任务信息
            task = await self.task_history_manager.get_task(task_id)
            if not task:
                raise UserInputError(f"任务 {task_id} 不存在")
            
            # 1. 收集用户输入
            user_inputs = await self._collect_user_inputs(task_id, info_requirements)
            
            # 2. 验证用户输入
            validated_inputs = await self._validate_user_inputs(user_inputs)
            
            # 3. 解析用户输入
            parsed_inputs = await self._parse_user_inputs(validated_inputs)
            
            # 4. 格式化用户输入
            formatted_inputs = await self._format_user_inputs(parsed_inputs)
            
            # 5. 构建处理结果
            processing_result = {
                "task_id": task_id,
                "user_inputs": formatted_inputs,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # 6. 保存处理结果
            await self.task_history_manager.create_user_input_processing(
                task_id=task_id,
                user_inputs=formatted_inputs
            )
            
            self.logger.info(f"任务 {task_id} 的用户输入处理完成")
            return processing_result
        except Exception as e:
            raise UserInputError(f"处理用户输入失败: {str(e)}")
    
    async def _collect_user_inputs(self, task_id: int, info_requirements: List[Dict]) -> List[Dict]:
        """
        收集用户输入
        
        Args:
            task_id: 任务ID
            info_requirements: 信息需求列表
            
        Returns:
            用户输入列表
        """
        try:
            user_inputs = []
            
            # 显示欢迎信息
            await self.interface.message(f"任务 {task_id} 需要更多信息才能继续执行", "info")
            await self.interface.message("请根据以下问题提供相关信息", "info")
            print()
            
            # 为每个信息需求收集用户输入
            for i, requirement in enumerate(info_requirements):
                requirement_id = f"req_{i}"
                sub_task_id = requirement.get("sub_task_id", "")
                requirement_type = requirement.get("type", "")
                priority = requirement.get("priority", "medium")
                description = requirement.get("description", "")
                question = requirement.get("question", "")
                
                # 显示问题
                print(f"{i+1}. {description}")
                print(f"   问题: {question}")
                
                # 根据需求类型确定输入类型
                input_type = self._determine_input_type(requirement_type, question)
                
                # 根据输入类型收集用户输入
                if input_type == "text":
                    user_input = await self.interface.prompt("   请输入您的回答")
                elif input_type == "number":
                    user_input = await self.interface.prompt("   请输入数字")
                elif input_type == "boolean":
                    user_input = await self.interface.confirm("   请选择是或否")
                elif input_type == "choice":
                    # 提供选项
                    options = self._generate_options(requirement_type, question)
                    user_input = await self.interface.select(
                        "   请选择选项",
                        options
                    )
                elif input_type == "json":
                    user_input = await self.interface.prompt(
                        "   请输入JSON格式数据",
                        default="{}"
                    )
                else:
                    user_input = await self.interface.prompt("   请输入您的回答")
                
                # 记录用户输入
                user_inputs.append({
                    "requirement_id": requirement_id,
                    "sub_task_id": sub_task_id,
                    "requirement_type": requirement_type,
                    "priority": priority,
                    "description": description,
                    "question": question,
                    "input_type": input_type,
                    "raw_input": user_input
                })
                
                print()
            
            return user_inputs
        except Exception as e:
            raise UserInputError(f"收集用户输入失败: {str(e)}")
    
    def _determine_input_type(self, requirement_type: str, question: str) -> str:
        """
        确定输入类型
        
        Args:
            requirement_type: 需求类型
            question: 问题
            
        Returns:
            输入类型
        """
        try:
            # 根据需求类型和问题确定输入类型
            if requirement_type == "missing_user_preference":
                # 用户偏好通常使用选择或布尔值
                if "是否" in question or "有没有" in question:
                    return "boolean"
                else:
                    return "choice"
            elif requirement_type == "missing_constraint":
                # 约束条件通常使用文本或选择
                if "范围" in question or "级别" in question:
                    return "choice"
                else:
                    return "text"
            elif requirement_type == "missing_example":
                # 示例通常使用文本
                return "text"
            elif requirement_type == "quality_improvement":
                # 质量改进通常使用文本或选择
                if "程度" in question or "级别" in question:
                    return "choice"
                else:
                    return "text"
            else:
                # 默认使用文本
                return "text"
        except Exception as e:
            self.logger.error(f"确定输入类型失败: {str(e)}")
            return "text"
    
    def _generate_options(self, requirement_type: str, question: str) -> List[str]:
        """
        生成选项
        
        Args:
            requirement_type: 需求类型
            question: 问题
            
        Returns:
            选项列表
        """
        try:
            # 根据需求类型和问题生成选项
            if requirement_type == "missing_user_preference":
                if "风格" in question:
                    return ["简洁", "详细", "正式", "非正式"]
                elif "颜色" in question:
                    return ["红色", "蓝色", "绿色", "黄色", "黑色", "白色"]
                elif "大小" in question:
                    return ["小", "中", "大"]
                else:
                    return ["是", "否"]
            elif requirement_type == "missing_constraint":
                if "优先级" in question:
                    return ["高", "中", "低"]
                elif "权限" in question:
                    return ["只读", "读写", "管理员"]
                else:
                    return ["是", "否"]
            elif requirement_type == "quality_improvement":
                if "程度" in question:
                    return ["轻微", "中等", "严重"]
                else:
                    return ["是", "否"]
            else:
                return ["是", "否"]
        except Exception as e:
            self.logger.error(f"生成选项失败: {str(e)}")
            return ["是", "否"]
    
    async def _validate_user_inputs(self, user_inputs: List[Dict]) -> List[Dict]:
        """
        验证用户输入
        
        Args:
            user_inputs: 用户输入列表
            
        Returns:
            验证后的用户输入列表
        """
        try:
            validated_inputs = []
            
            for user_input in user_inputs:
                input_type = user_input.get("input_type", "text")
                raw_input = user_input.get("raw_input", "")
                
                # 根据输入类型验证
                validation_result = {
                    "is_valid": True,
                    "errors": []
                }
                
                # 应用验证规则
                if input_type == "text":
                    # 文本验证
                    if not raw_input:
                        validation_result["is_valid"] = False
                        validation_result["errors"].append("输入不能为空")
                
                elif input_type == "number":
                    # 数字验证
                    if not self._is_numeric(raw_input):
                        validation_result["is_valid"] = False
                        validation_result["errors"].append("请输入有效的数字")
                
                elif input_type == "boolean":
                    # 布尔值验证
                    if raw_input not in [True, False]:
                        validation_result["is_valid"] = False
                        validation_result["errors"].append("请选择是或否")
                
                elif input_type == "json":
                    # JSON验证
                    try:
                        json.loads(raw_input)
                    except json.JSONDecodeError:
                        validation_result["is_valid"] = False
                        validation_result["errors"].append("请输入有效的JSON格式数据")
                
                # 如果验证失败，提示用户重新输入
                if not validation_result["is_valid"]:
                    await self.interface.message("输入验证失败，请重新输入", "error")
                    for error in validation_result["errors"]:
                        await self.interface.message(f"  - {error}", "error")
                    
                    # 重新收集输入
                    if input_type == "text":
                        new_input = await self.interface.prompt("   请重新输入您的回答")
                    elif input_type == "number":
                        new_input = await self.interface.prompt("   请重新输入数字")
                    elif input_type == "boolean":
                        new_input = await self.interface.confirm("   请重新选择是或否")
                    elif input_type == "choice":
                        options = self._generate_options(
                            user_input.get("requirement_type", ""),
                            user_input.get("question", "")
                        )
                        new_input = await self.interface.select(
                            "   请重新选择选项",
                            options
                        )
                    elif input_type == "json":
                        new_input = await self.interface.prompt(
                            "   请重新输入JSON格式数据",
                            default="{}"
                        )
                    else:
                        new_input = await self.interface.prompt("   请重新输入您的回答")
                    
                    # 更新输入
                    user_input["raw_input"] = new_input
                
                # 添加验证结果
                user_input["validation_result"] = validation_result
                validated_inputs.append(user_input)
            
            return validated_inputs
        except Exception as e:
            raise UserInputError(f"验证用户输入失败: {str(e)}")
    
    async def _parse_user_inputs(self, user_inputs: List[Dict]) -> List[Dict]:
        """
        解析用户输入
        
        Args:
            user_inputs: 用户输入列表
            
        Returns:
            解析后的用户输入列表
        """
        try:
            parsed_inputs = []
            
            for user_input in user_inputs:
                input_type = user_input.get("input_type", "text")
                raw_input = user_input.get("raw_input", "")
                
                # 根据输入类型解析
                parser = self.input_parsers.get(input_type, self._parse_text)
                parsed_value = await parser(raw_input)
                
                # 添加解析结果
                user_input["parsed_value"] = parsed_value
                parsed_inputs.append(user_input)
            
            return parsed_inputs
        except Exception as e:
            raise UserInputError(f"解析用户输入失败: {str(e)}")
    
    async def _format_user_inputs(self, user_inputs: List[Dict]) -> List[Dict]:
        """
        格式化用户输入
        
        Args:
            user_inputs: 用户输入列表
            
        Returns:
            格式化后的用户输入列表
        """
        try:
            formatted_inputs = []
            
            for user_input in user_inputs:
                input_type = user_input.get("input_type", "text")
                parsed_value = user_input.get("parsed_value", "")
                
                # 根据输入类型格式化
                formatter = self.input_formatters.get(input_type, self._format_text)
                formatted_value = await formatter(parsed_value)
                
                # 构建格式化输入
                formatted_input = {
                    "requirement_id": user_input.get("requirement_id"),
                    "sub_task_id": user_input.get("sub_task_id"),
                    "requirement_type": user_input.get("requirement_type"),
                    "priority": user_input.get("priority"),
                    "description": user_input.get("description"),
                    "question": user_input.get("question"),
                    "input_type": input_type,
                    "raw_input": user_input.get("raw_input"),
                    "parsed_value": parsed_value,
                    "formatted_value": formatted_value
                }
                
                formatted_inputs.append(formatted_input)
            
            return formatted_inputs
        except Exception as e:
            raise UserInputError(f"格式化用户输入失败: {str(e)}")
    
    # 输入验证方法
    def _validate_required(self, value: Any, params: Dict) -> Dict:
        """
        验证必填项
        
        Args:
            value: 值
            params: 参数
            
        Returns:
            验证结果
        """
        try:
            is_valid = value is not None and value != ""
            return {
                "is_valid": is_valid,
                "errors": ["值不能为空"] if not is_valid else []
            }
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"验证失败: {str(e)}"]
            }
    
    def _validate_min_length(self, value: Any, params: Dict) -> Dict:
        """
        验证最小长度
        
        Args:
            value: 值
            params: 参数
            
        Returns:
            验证结果
        """
        try:
            min_length = params.get("min_length", 0)
            is_valid = len(str(value)) >= min_length
            
            return {
                "is_valid": is_valid,
                "errors": [f"长度不能小于 {min_length}"] if not is_valid else []
            }
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"验证失败: {str(e)}"]
            }
    
    def _validate_max_length(self, value: Any, params: Dict) -> Dict:
        """
        验证最大长度
        
        Args:
            value: 值
            params: 参数
            
        Returns:
            验证结果
        """
        try:
            max_length = params.get("max_length", 1000)
            is_valid = len(str(value)) <= max_length
            
            return {
                "is_valid": is_valid,
                "errors": [f"长度不能大于 {max_length}"] if not is_valid else []
            }
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"验证失败: {str(e)}"]
            }
    
    def _validate_pattern(self, value: Any, params: Dict) -> Dict:
        """
        验证正则表达式
        
        Args:
            value: 值
            params: 参数
            
        Returns:
            验证结果
        """
        try:
            pattern = params.get("pattern", "")
            is_valid = re.match(pattern, str(value)) is not None
            
            return {
                "is_valid": is_valid,
                "errors": [f"格式不匹配"] if not is_valid else []
            }
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"验证失败: {str(e)}"]
            }
    
    def _validate_numeric(self, value: Any, params: Dict) -> Dict:
        """
        验证数字
        
        Args:
            value: 值
            params: 参数
            
        Returns:
            验证结果
        """
        try:
            is_valid = self._is_numeric(value)
            
            return {
                "is_valid": is_valid,
                "errors": ["请输入有效的数字"] if not is_valid else []
            }
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"验证失败: {str(e)}"]
            }
    
    def _validate_integer(self, value: Any, params: Dict) -> Dict:
        """
        验证整数
        
        Args:
            value: 值
            params: 参数
            
        Returns:
            验证结果
        """
        try:
            is_valid = str(value).isdigit()
            
            return {
                "is_valid": is_valid,
                "errors": ["请输入有效的整数"] if not is_valid else []
            }
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"验证失败: {str(e)}"]
            }
    
    def _validate_float(self, value: Any, params: Dict) -> Dict:
        """
        验证浮点数
        
        Args:
            value: 值
            params: 参数
            
        Returns:
            验证结果
        """
        try:
            try:
                float(value)
                is_valid = True
            except ValueError:
                is_valid = False
            
            return {
                "is_valid": is_valid,
                "errors": ["请输入有效的浮点数"] if not is_valid else []
            }
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"验证失败: {str(e)}"]
            }
    
    def _validate_boolean(self, value: Any, params: Dict) -> Dict:
        """
        验证布尔值
        
        Args:
            value: 值
            params: 参数
            
        Returns:
            验证结果
        """
        try:
            is_valid = isinstance(value, bool) or str(value).lower() in ["true", "false", "yes", "no", "1", "0"]
            
            return {
                "is_valid": is_valid,
                "errors": ["请输入有效的布尔值"] if not is_valid else []
            }
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"验证失败: {str(e)}"]
            }
    
    def _validate_email(self, value: Any, params: Dict) -> Dict:
        """
        验证电子邮件
        
        Args:
            value: 值
            params: 参数
            
        Returns:
            验证结果
        """
        try:
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            is_valid = re.match(pattern, str(value)) is not None
            
            return {
                "is_valid": is_valid,
                "errors": ["请输入有效的电子邮件地址"] if not is_valid else []
            }
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"验证失败: {str(e)}"]
            }
    
    def _validate_url(self, value: Any, params: Dict) -> Dict:
        """
        验证URL
        
        Args:
            value: 值
            params: 参数
            
        Returns:
            验证结果
        """
        try:
            pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            is_valid = re.match(pattern, str(value)) is not None
            
            return {
                "is_valid": is_valid,
                "errors": ["请输入有效的URL"] if not is_valid else []
            }
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"验证失败: {str(e)}"]
            }
    
    def _validate_json(self, value: Any, params: Dict) -> Dict:
        """
        验证JSON
        
        Args:
            value: 值
            params: 参数
            
        Returns:
            验证结果
        """
        try:
            json.loads(str(value))
            is_valid = True
            
            return {
                "is_valid": is_valid,
                "errors": [] if is_valid else ["请输入有效的JSON格式数据"]
            }
        except json.JSONDecodeError:
            return {
                "is_valid": False,
                "errors": ["请输入有效的JSON格式数据"]
            }
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"验证失败: {str(e)}"]
            }
    
    # 输入解析方法
    async def _parse_text(self, value: Any) -> str:
        """
        解析文本
        
        Args:
            value: 值
            
        Returns:
            解析后的文本
        """
        return str(value)
    
    async def _parse_number(self, value: Any) -> Union[int, float]:
        """
        解析数字
        
        Args:
            value: 值
            
        Returns:
            解析后的数字
        """
        if str(value).isdigit():
            return int(value)
        else:
            return float(value)
    
    async def _parse_boolean(self, value: Any) -> bool:
        """
        解析布尔值
        
        Args:
            value: 值
            
        Returns:
            解析后的布尔值
        """
        if isinstance(value, bool):
            return value
        
        str_value = str(value).lower()
        return str_value in ["true", "yes", "1"]
    
    async def _parse_json(self, value: Any) -> Any:
        """
        解析JSON
        
        Args:
            value: 值
            
        Returns:
            解析后的JSON
        """
        return json.loads(str(value))
    
    async def _parse_list(self, value: Any) -> List[Any]:
        """
        解析列表
        
        Args:
            value: 值
            
        Returns:
            解析后的列表
        """
        if isinstance(value, list):
            return value
        
        if isinstance(value, str):
            try:
                # 尝试解析JSON
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                # 如果不是JSON，按逗号分割
                return [item.strip() for item in value.split(",") if item.strip()]
        
        return [value]
    
    async def _parse_choice(self, value: Any) -> str:
        """
        解析选择
        
        Args:
            value: 值
            
        Returns:
            解析后的选择
        """
        return str(value)
    
    # 输入格式化方法
    async def _format_text(self, value: Any) -> str:
        """
        格式化文本
        
        Args:
            value: 值
            
        Returns:
            格式化后的文本
        """
        return str(value).strip()
    
    async def _format_number(self, value: Any) -> Union[int, float]:
        """
        格式化数字
        
        Args:
            value: 值
            
        Returns:
            格式化后的数字
        """
        if isinstance(value, (int, float)):
            return value
        
        if str(value).isdigit():
            return int(value)
        else:
            return float(value)
    
    async def _format_boolean(self, value: Any) -> bool:
        """
        格式化布尔值
        
        Args:
            value: 值
            
        Returns:
            格式化后的布尔值
        """
        if isinstance(value, bool):
            return value
        
        str_value = str(value).lower()
        return str_value in ["true", "yes", "1"]
    
    async def _format_json(self, value: Any) -> Any:
        """
        格式化JSON
        
        Args:
            value: 值
            
        Returns:
            格式化后的JSON
        """
        if isinstance(value, str):
            return json.loads(value)
        
        return value
    
    async def _format_list(self, value: Any) -> List[Any]:
        """
        格式化列表
        
        Args:
            value: 值
            
        Returns:
            格式化后的列表
        """
        if isinstance(value, list):
            return value
        
        if isinstance(value, str):
            try:
                # 尝试解析JSON
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                # 如果不是JSON，按逗号分割
                return [item.strip() for item in value.split(",") if item.strip()]
        
        return [value]
    
    # 辅助方法
    def _is_numeric(self, value: Any) -> bool:
        """
        检查是否为数字
        
        Args:
            value: 值
            
        Returns:
            是否为数字
        """
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    async def get_user_input_processing(self, task_id: int) -> Dict:
        """
        获取用户输入处理结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            用户输入处理结果
        """
        try:
            processing_result = await self.task_history_manager.get_user_input_processing(task_id)
            return processing_result
        except Exception as e:
            raise UserInputError(f"获取用户输入处理结果失败: {str(e)}")
    
    async def add_validation_rule(self, name: str, validator: Callable, description: str) -> bool:
        """
        添加验证规则
        
        Args:
            name: 规则名称
            validator: 验证器函数
            description: 规则描述
            
        Returns:
            添加是否成功
        """
        try:
            self.validation_rules[name] = {
                "description": description,
                "validator": validator
            }
            
            self.logger.info(f"添加验证规则: {name}")
            return True
        except Exception as e:
            raise UserInputError(f"添加验证规则失败: {str(e)}")
    
    async def add_input_parser(self, name: str, parser: Callable) -> bool:
        """
        添加输入解析器
        
        Args:
            name: 解析器名称
            parser: 解析器函数
            
        Returns:
            添加是否成功
        """
        try:
            self.input_parsers[name] = parser
            self.logger.info(f"添加输入解析器: {name}")
            return True
        except Exception as e:
            raise UserInputError(f"添加输入解析器失败: {str(e)}")
    
    async def add_input_formatter(self, name: str, formatter: Callable) -> bool:
        """
        添加输入格式化器
        
        Args:
            name: 格式化器名称
            formatter: 格式化器函数
            
        Returns:
            添加是否成功
        """
        try:
            self.input_formatters[name] = formatter
            self.logger.info(f"添加输入格式化器: {name}")
            return True
        except Exception as e:
            raise UserInputError(f"添加输入格式化器失败: {str(e)}")
    
    async def get_user_input_stats(self, days: int = 30) -> Dict:
        """
        获取用户输入统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        try:
            # 获取用户输入处理统计
            stats = await self.task_history_manager.get_user_input_statistics(days)
            
            return stats
        except Exception as e:
            raise UserInputError(f"获取用户输入统计信息失败: {str(e)}")