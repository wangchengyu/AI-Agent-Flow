"""
结果格式化器

负责格式化任务执行结果，
包括文本、表格、JSON等多种输出格式。
"""

import json
import logging
import os
import textwrap
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Tuple

from ..utils.exceptions import ResultFormatterError


class ResultFormatter:
    """结果格式化器，负责格式化任务执行结果"""
    
    def __init__(self, interactive_interface):
        """
        初始化结果格式化器
        
        Args:
            interactive_interface: 交互式界面
        """
        self.interface = interactive_interface
        
        # 格式化配置
        self.config = {
            "max_width": 80,          # 最大宽度
            "indent": 2,              # 缩进
            "table_max_col_width": 30, # 表格最大列宽
            "json_indent": 2,         # JSON缩进
            "show_timestamp": True,   # 显示时间戳
            "color_output": True,      # 彩色输出
            "wrap_text": True         # 自动换行
        }
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("结果格式化器初始化完成")
    
    async def initialize(self):
        """初始化结果格式化器"""
        try:
            self.logger.info("结果格式化器初始化完成")
        except Exception as e:
            raise ResultFormatterError(f"初始化结果格式化器失败: {str(e)}")
    
    async def format_task_result(self, task_result: Dict[str, Any], 
                               format_type: str = "text") -> str:
        """
        格式化任务结果
        
        Args:
            task_result: 任务结果
            format_type: 格式类型 (text, table, json)
            
        Returns:
            格式化后的结果字符串
        """
        try:
            if format_type == "json":
                return await self._format_json(task_result)
            elif format_type == "table":
                return await self._format_task_result_table(task_result)
            else:
                return await self._format_task_result_text(task_result)
        except Exception as e:
            raise ResultFormatterError(f"格式化任务结果失败: {str(e)}")
    
    async def _format_task_result_text(self, task_result: Dict[str, Any]) -> str:
        """
        以文本格式格式化任务结果
        
        Args:
            task_result: 任务结果
            
        Returns:
            格式化后的结果字符串
        """
        try:
            lines = []
            
            # 添加标题
            task_id = task_result.get("task_id", "未知")
            lines.append(f"任务结果 (ID: {task_id})")
            lines.append("=" * self.config["max_width"])
            lines.append("")
            
            # 添加基本信息
            task_name = task_result.get("task_name", "未知任务")
            status = task_result.get("status", "未知")
            
            # 根据状态选择颜色
            status_color = {
                "pending": "yellow",
                "running": "blue",
                "paused": "yellow",
                "completed": "green",
                "failed": "red",
                "stopped": "yellow"
            }.get(status, "white")
            
            lines.append(f"任务名称: {task_name}")
            lines.append(f"状态: {self._colorize(status, status_color)}")
            
            # 添加时间信息
            if self.config["show_timestamp"]:
                created_at = task_result.get("created_at")
                if created_at:
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at)
                    lines.append(f"创建时间: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
                start_time = task_result.get("start_time")
                if start_time:
                    if isinstance(start_time, str):
                        start_time = datetime.fromisoformat(start_time)
                    lines.append(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                end_time = task_result.get("end_time")
                if end_time:
                    if isinstance(end_time, str):
                        end_time = datetime.fromisoformat(end_time)
                    lines.append(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 计算执行时间
                if start_time and end_time:
                    execution_time = (end_time - start_time).total_seconds()
                    lines.append(f"执行时间: {self._format_time(execution_time)}")
            
            lines.append("")
            
            # 添加任务描述
            description = task_result.get("description", "")
            if description:
                lines.append("任务描述:")
                lines.append(self._indent_text(description, self.config["indent"]))
                lines.append("")
            
            # 添加子任务结果
            sub_tasks = task_result.get("sub_tasks", [])
            if sub_tasks:
                lines.append("子任务结果:")
                lines.append("-" * self.config["max_width"])
                
                for i, sub_task in enumerate(sub_tasks):
                    sub_task_id = sub_task.get("id", f"sub_task_{i}")
                    sub_task_name = sub_task.get("name", f"子任务 {i+1}")
                    sub_task_status = sub_task.get("status", "未知")
                    sub_task_result = sub_task.get("result", {})
                    
                    # 根据状态选择颜色
                    sub_task_status_color = {
                        "pending": "yellow",
                        "running": "blue",
                        "paused": "yellow",
                        "completed": "green",
                        "failed": "red",
                        "stopped": "yellow"
                    }.get(sub_task_status, "white")
                    
                    lines.append(f"{i+1}. {sub_task_name} (ID: {sub_task_id})")
                    lines.append(f"   状态: {self._colorize(sub_task_status, sub_task_status_color)}")
                    
                    # 添加子任务结果
                    if sub_task_result:
                        result_text = self._format_sub_task_result(sub_task_result)
                        if result_text:
                            lines.append(f"   结果: {result_text}")
                    
                    lines.append("")
            
            # 添加验证结果
            validation_result = task_result.get("validation_result")
            if validation_result:
                lines.append("验证结果:")
                lines.append("-" * self.config["max_width"])
                
                is_valid = validation_result.get("is_valid", False)
                validation_status = "通过" if is_valid else "未通过"
                validation_color = "green" if is_valid else "red"
                
                lines.append(f"总体验证: {self._colorize(validation_status, validation_color)}")
                
                # 添加验证报告
                validation_report = validation_result.get("validation_report", "")
                if validation_report:
                    lines.append("")
                    lines.append("验证报告:")
                    lines.append(self._indent_text(validation_report, self.config["indent"]))
                
                # 添加改进建议
                improvement_suggestions = validation_result.get("improvement_suggestions", [])
                if improvement_suggestions:
                    lines.append("")
                    lines.append("改进建议:")
                    for i, suggestion in enumerate(improvement_suggestions):
                        suggestion_text = suggestion.get("description", "")
                        if suggestion_text:
                            lines.append(f"{i+1}. {suggestion_text}")
                
                lines.append("")
            
            # 添加错误信息
            error = task_result.get("error")
            if error:
                lines.append("错误信息:")
                lines.append("-" * self.config["max_width"])
                lines.append(self._colorize(error, "red"))
                lines.append("")
            
            return "\n".join(lines)
        except Exception as e:
            raise ResultFormatterError(f"以文本格式格式化任务结果失败: {str(e)}")
    
    async def _format_task_result_table(self, task_result: Dict[str, Any]) -> str:
        """
        以表格格式格式化任务结果
        
        Args:
            task_result: 任务结果
            
        Returns:
            格式化后的结果字符串
        """
        try:
            lines = []
            
            # 添加标题
            task_id = task_result.get("task_id", "未知")
            lines.append(f"任务结果 (ID: {task_id})")
            lines.append("=" * self.config["max_width"])
            lines.append("")
            
            # 构建基本信息表格
            basic_info = []
            
            task_name = task_result.get("task_name", "未知任务")
            status = task_result.get("status", "未知")
            basic_info.append(["任务名称", task_name])
            basic_info.append(["状态", status])
            
            # 添加时间信息
            if self.config["show_timestamp"]:
                created_at = task_result.get("created_at")
                if created_at:
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at)
                    basic_info.append(["创建时间", created_at.strftime('%Y-%m-%d %H:%M:%S')])
                
                start_time = task_result.get("start_time")
                if start_time:
                    if isinstance(start_time, str):
                        start_time = datetime.fromisoformat(start_time)
                    basic_info.append(["开始时间", start_time.strftime('%Y-%m-%d %H:%M:%S')])
                
                end_time = task_result.get("end_time")
                if end_time:
                    if isinstance(end_time, str):
                        end_time = datetime.fromisoformat(end_time)
                    basic_info.append(["结束时间", end_time.strftime('%Y-%m-%d %H:%M:%S')])
                
                # 计算执行时间
                if start_time and end_time:
                    execution_time = (end_time - start_time).total_seconds()
                    basic_info.append(["执行时间", self._format_time(execution_time)])
            
            # 显示基本信息表格
            if basic_info:
                headers = ["属性", "值"]
                await self.interface.table(headers, basic_info, "基本信息")
                lines.append("")
            
            # 添加任务描述
            description = task_result.get("description", "")
            if description:
                lines.append("任务描述:")
                lines.append(self._indent_text(description, self.config["indent"]))
                lines.append("")
            
            # 添加子任务结果表格
            sub_tasks = task_result.get("sub_tasks", [])
            if sub_tasks:
                lines.append("子任务结果:")
                lines.append("-" * self.config["max_width"])
                
                # 构建子任务表格
                sub_task_table = []
                for i, sub_task in enumerate(sub_tasks):
                    sub_task_id = sub_task.get("id", f"sub_task_{i}")
                    sub_task_name = sub_task.get("name", f"子任务 {i+1}")
                    sub_task_status = sub_task.get("status", "未知")
                    sub_task_result = sub_task.get("result", {})
                    
                    # 格式化子任务结果
                    result_text = self._format_sub_task_result(sub_task_result)
                    if result_text:
                        # 限制结果长度
                        if len(result_text) > self.config["table_max_col_width"]:
                            result_text = result_text[:self.config["table_max_col_width"]-3] + "..."
                    
                    sub_task_table.append([
                        str(i+1),
                        sub_task_name,
                        sub_task_status,
                        result_text or ""
                    ])
                
                # 显示子任务表格
                headers = ["序号", "名称", "状态", "结果"]
                await self.interface.table(headers, sub_task_table, "子任务结果")
                lines.append("")
            
            # 添加验证结果
            validation_result = task_result.get("validation_result")
            if validation_result:
                lines.append("验证结果:")
                lines.append("-" * self.config["max_width"])
                
                is_valid = validation_result.get("is_valid", False)
                validation_status = "通过" if is_valid else "未通过"
                
                # 构建验证结果表格
                validation_table = [
                    ["总体验证", validation_status]
                ]
                
                # 添加验证分数
                validation_results = validation_result.get("validation_results", {})
                if validation_results:
                    for validator_name, validator_result in validation_results.items():
                        score = validator_result.get("score", 0)
                        validator_status = "通过" if validator_result.get("is_valid", False) else "未通过"
                        validation_table.append([
                            f"{validator_name} 验证",
                            f"{validator_status} (分数: {score:.2f})"
                        ])
                
                # 显示验证结果表格
                headers = ["属性", "值"]
                await self.interface.table(headers, validation_table, "验证结果")
                lines.append("")
                
                # 添加改进建议
                improvement_suggestions = validation_result.get("improvement_suggestions", [])
                if improvement_suggestions:
                    lines.append("改进建议:")
                    
                    # 构建改进建议表格
                    suggestion_table = []
                    for i, suggestion in enumerate(improvement_suggestions):
                        suggestion_text = suggestion.get("description", "")
                        priority = suggestion.get("priority", "medium")
                        suggestion_table.append([
                            str(i+1),
                            suggestion_text,
                            priority
                        ])
                    
                    # 显示改进建议表格
                    headers = ["序号", "建议", "优先级"]
                    await self.interface.table(headers, suggestion_table, "改进建议")
                    lines.append("")
            
            # 添加错误信息
            error = task_result.get("error")
            if error:
                lines.append("错误信息:")
                lines.append("-" * self.config["max_width"])
                lines.append(self._colorize(error, "red"))
                lines.append("")
            
            return "\n".join(lines)
        except Exception as e:
            raise ResultFormatterError(f"以表格格式格式化任务结果失败: {str(e)}")
    
    async def _format_json(self, data: Any) -> str:
        """
        以JSON格式格式化数据
        
        Args:
            data: 要格式化的数据
            
        Returns:
            格式化后的JSON字符串
        """
        try:
            # 处理时间对象
            def json_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            return json.dumps(data, indent=self.config["json_indent"], ensure_ascii=False, default=json_serializer)
        except Exception as e:
            raise ResultFormatterError(f"以JSON格式格式化数据失败: {str(e)}")
    
    def _format_sub_task_result(self, sub_task_result: Dict[str, Any]) -> str:
        """
        格式化子任务结果
        
        Args:
            sub_task_result: 子任务结果
            
        Returns:
            格式化后的结果字符串
        """
        try:
            # 根据子任务类型格式化结果
            result_type = sub_task_result.get("type", "general")
            
            if result_type == "generation":
                generated_content = sub_task_result.get("generated_content", "")
                return generated_content if generated_content else "无生成内容"
            
            elif result_type == "analysis":
                findings = sub_task_result.get("findings", [])
                if findings:
                    return f"发现 {len(findings)} 个分析结果"
                else:
                    return "无分析发现"
            
            elif result_type == "search":
                search_results = sub_task_result.get("search_results", [])
                if search_results:
                    return f"找到 {len(search_results)} 个搜索结果"
                else:
                    return "无搜索结果"
            
            elif result_type == "validation":
                is_valid = sub_task_result.get("is_valid", False)
                return "验证通过" if is_valid else "验证未通过"
            
            elif result_type == "transformation":
                transformed_content = sub_task_result.get("transformed_content", "")
                return transformed_content if transformed_content else "无转换内容"
            
            else:
                # 通用格式化
                if "result" in sub_task_result:
                    result = sub_task_result["result"]
                    if isinstance(result, dict):
                        return json.dumps(result, ensure_ascii=False)
                    else:
                        return str(result)
                else:
                    return "无结果"
        except Exception as e:
            return f"格式化子任务结果时出错: {str(e)}"
    
    def _colorize(self, text: str, color: str) -> str:
        """
        为文本添加颜色
        
        Args:
            text: 文本
            color: 颜色名称
            
        Returns:
            带颜色的文本
        """
        if not self.config["color_output"] or not hasattr(self.interface, "colorize"):
            return text
        
        return self.interface.colorize(text, color)
    
    def _indent_text(self, text: str, indent: int) -> str:
        """
        缩进文本
        
        Args:
            text: 文本
            indent: 缩进空格数
            
        Returns:
            缩进后的文本
        """
        try:
            if not text:
                return ""
            
            # 分割文本为行
            lines = text.split("\n")
            
            # 缩进每一行
            indent_str = " " * indent
            indented_lines = [indent_str + line for line in lines]
            
            # 重新组合
            return "\n".join(indented_lines)
        except Exception as e:
            return text
    
    def _wrap_text(self, text: str, width: int) -> str:
        """
        自动换行
        
        Args:
            text: 文本
            width: 宽度
            
        Returns:
            换行后的文本
        """
        try:
            if not self.config["wrap_text"] or not text:
                return text
            
            # 使用textwrap进行换行
            return textwrap.fill(text, width=width)
        except Exception as e:
            return text
    
    def _format_time(self, seconds: float) -> str:
        """
        格式化时间
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化后的时间字符串
        """
        try:
            if seconds < 0:
                return "未知"
            
            # 计算时间单位
            hours, remainder = divmod(int(seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            # 构建时间字符串
            time_parts = []
            
            if hours > 0:
                time_parts.append(f"{hours}小时")
            
            if minutes > 0:
                time_parts.append(f"{minutes}分钟")
            
            if seconds > 0 or not time_parts:
                time_parts.append(f"{seconds}秒")
            
            return "".join(time_parts)
        except Exception as e:
            return "未知"
    
    async def format_sub_task_result(self, sub_task_result: Dict[str, Any], 
                                   format_type: str = "text") -> str:
        """
        格式化子任务结果
        
        Args:
            sub_task_result: 子任务结果
            format_type: 格式类型 (text, table, json)
            
        Returns:
            格式化后的结果字符串
        """
        try:
            if format_type == "json":
                return await self._format_json(sub_task_result)
            elif format_type == "table":
                return await self._format_sub_task_result_table(sub_task_result)
            else:
                return await self._format_sub_task_result_text(sub_task_result)
        except Exception as e:
            raise ResultFormatterError(f"格式化子任务结果失败: {str(e)}")
    
    async def _format_sub_task_result_text(self, sub_task_result: Dict[str, Any]) -> str:
        """
        以文本格式格式化子任务结果
        
        Args:
            sub_task_result: 子任务结果
            
        Returns:
            格式化后的结果字符串
        """
        try:
            lines = []
            
            # 添加基本信息
            sub_task_id = sub_task_result.get("id", "未知")
            sub_task_name = sub_task_result.get("name", "未知子任务")
            sub_task_type = sub_task_result.get("type", "general")
            sub_task_status = sub_task_result.get("status", "未知")
            
            # 根据状态选择颜色
            status_color = {
                "pending": "yellow",
                "running": "blue",
                "paused": "yellow",
                "completed": "green",
                "failed": "red",
                "stopped": "yellow"
            }.get(sub_task_status, "white")
            
            lines.append(f"子任务结果 (ID: {sub_task_id})")
            lines.append("=" * self.config["max_width"])
            lines.append("")
            lines.append(f"名称: {sub_task_name}")
            lines.append(f"类型: {sub_task_type}")
            lines.append(f"状态: {self._colorize(sub_task_status, status_color)}")
            
            # 添加时间信息
            if self.config["show_timestamp"]:
                start_time = sub_task_result.get("start_time")
                if start_time:
                    if isinstance(start_time, str):
                        start_time = datetime.fromisoformat(start_time)
                    lines.append(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                end_time = sub_task_result.get("end_time")
                if end_time:
                    if isinstance(end_time, str):
                        end_time = datetime.fromisoformat(end_time)
                    lines.append(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 计算执行时间
                if start_time and end_time:
                    execution_time = (end_time - start_time).total_seconds()
                    lines.append(f"执行时间: {self._format_time(execution_time)}")
            
            lines.append("")
            
            # 添加结果
            result = sub_task_result.get("result", {})
            if result:
                lines.append("结果:")
                lines.append("-" * self.config["max_width"])
                
                # 根据类型格式化结果
                result_text = self._format_sub_task_result(sub_task_result)
                lines.append(self._indent_text(result_text, self.config["indent"]))
                lines.append("")
            
            # 添加错误信息
            error = sub_task_result.get("error")
            if error:
                lines.append("错误信息:")
                lines.append("-" * self.config["max_width"])
                lines.append(self._colorize(error, "red"))
                lines.append("")
            
            return "\n".join(lines)
        except Exception as e:
            raise ResultFormatterError(f"以文本格式格式化子任务结果失败: {str(e)}")
    
    async def _format_sub_task_result_table(self, sub_task_result: Dict[str, Any]) -> str:
        """
        以表格格式格式化子任务结果
        
        Args:
            sub_task_result: 子任务结果
            
        Returns:
            格式化后的结果字符串
        """
        try:
            lines = []
            
            # 添加标题
            sub_task_id = sub_task_result.get("id", "未知")
            lines.append(f"子任务结果 (ID: {sub_task_id})")
            lines.append("=" * self.config["max_width"])
            lines.append("")
            
            # 构建基本信息表格
            basic_info = []
            
            sub_task_name = sub_task_result.get("name", "未知子任务")
            sub_task_type = sub_task_result.get("type", "general")
            sub_task_status = sub_task_result.get("status", "未知")
            
            basic_info.append(["名称", sub_task_name])
            basic_info.append(["类型", sub_task_type])
            basic_info.append(["状态", sub_task_status])
            
            # 添加时间信息
            if self.config["show_timestamp"]:
                start_time = sub_task_result.get("start_time")
                if start_time:
                    if isinstance(start_time, str):
                        start_time = datetime.fromisoformat(start_time)
                    basic_info.append(["开始时间", start_time.strftime('%Y-%m-%d %H:%M:%S')])
                
                end_time = sub_task_result.get("end_time")
                if end_time:
                    if isinstance(end_time, str):
                        end_time = datetime.fromisoformat(end_time)
                    basic_info.append(["结束时间", end_time.strftime('%Y-%m-%d %H:%M:%S')])
                
                # 计算执行时间
                if start_time and end_time:
                    execution_time = (end_time - start_time).total_seconds()
                    basic_info.append(["执行时间", self._format_time(execution_time)])
            
            # 显示基本信息表格
            if basic_info:
                headers = ["属性", "值"]
                await self.interface.table(headers, basic_info, "基本信息")
                lines.append("")
            
            # 添加结果
            result = sub_task_result.get("result", {})
            if result:
                lines.append("结果:")
                lines.append("-" * self.config["max_width"])
                
                # 根据类型格式化结果
                result_text = self._format_sub_task_result(sub_task_result)
                lines.append(self._indent_text(result_text, self.config["indent"]))
                lines.append("")
            
            # 添加错误信息
            error = sub_task_result.get("error")
            if error:
                lines.append("错误信息:")
                lines.append("-" * self.config["max_width"])
                lines.append(self._colorize(error, "red"))
                lines.append("")
            
            return "\n".join(lines)
        except Exception as e:
            raise ResultFormatterError(f"以表格格式格式化子任务结果失败: {str(e)}")
    
    async def format_validation_result(self, validation_result: Dict[str, Any], 
                                     format_type: str = "text") -> str:
        """
        格式化验证结果
        
        Args:
            validation_result: 验证结果
            format_type: 格式类型 (text, table, json)
            
        Returns:
            格式化后的结果字符串
        """
        try:
            if format_type == "json":
                return await self._format_json(validation_result)
            elif format_type == "table":
                return await self._format_validation_result_table(validation_result)
            else:
                return await self._format_validation_result_text(validation_result)
        except Exception as e:
            raise ResultFormatterError(f"格式化验证结果失败: {str(e)}")
    
    async def _format_validation_result_text(self, validation_result: Dict[str, Any]) -> str:
        """
        以文本格式格式化验证结果
        
        Args:
            validation_result: 验证结果
            
        Returns:
            格式化后的结果字符串
        """
        try:
            lines = []
            
            # 添加标题
            task_id = validation_result.get("task_id", "未知")
            lines.append(f"验证结果 (任务ID: {task_id})")
            lines.append("=" * self.config["max_width"])
            lines.append("")
            
            # 添加基本信息
            is_valid = validation_result.get("is_valid", False)
            validation_status = "通过" if is_valid else "未通过"
            validation_color = "green" if is_valid else "red"
            
            lines.append(f"总体验证: {self._colorize(validation_status, validation_color)}")
            
            # 添加时间戳
            if self.config["show_timestamp"]:
                timestamp = validation_result.get("timestamp")
                if timestamp:
                    if isinstance(timestamp, (int, float)):
                        timestamp = datetime.fromtimestamp(timestamp)
                    elif isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp)
                    
                    lines.append(f"验证时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            
            lines.append("")
            
            # 添加验证结果详情
            validation_results = validation_result.get("validation_results", {})
            if validation_results:
                lines.append("验证详情:")
                lines.append("-" * self.config["max_width"])
                
                for validator_name, validator_result in validation_results.items():
                    validator_is_valid = validator_result.get("is_valid", False)
                    validator_status = "通过" if validator_is_valid else "未通过"
                    validator_color = "green" if validator_is_valid else "red"
                    score = validator_result.get("score", 0)
                    
                    lines.append(f"{validator_name} 验证: {self._colorize(validator_status, validator_color)} (分数: {score:.2f})")
                    
                    # 添加问题
                    issues = validator_result.get("issues", [])
                    if issues:
                        lines.append("  问题:")
                        for issue in issues:
                            description = issue.get("description", "")
                            severity = issue.get("severity", "medium")
                            severity_color = {
                                "high": "red",
                                "medium": "yellow",
                                "low": "blue"
                            }.get(severity, "white")
                            
                            lines.append(f"  - {self._colorize(description, severity_color)} (严重程度: {severity})")
                    
                    lines.append("")
            
            # 添加验证报告
            validation_report = validation_result.get("validation_report", "")
            if validation_report:
                lines.append("验证报告:")
                lines.append("-" * self.config["max_width"])
                lines.append(self._indent_text(validation_report, self.config["indent"]))
                lines.append("")
            
            # 添加改进建议
            improvement_suggestions = validation_result.get("improvement_suggestions", [])
            if improvement_suggestions:
                lines.append("改进建议:")
                lines.append("-" * self.config["max_width"])
                
                for i, suggestion in enumerate(improvement_suggestions):
                    suggestion_text = suggestion.get("description", "")
                    priority = suggestion.get("priority", "medium")
                    priority_color = {
                        "high": "red",
                        "medium": "yellow",
                        "low": "blue"
                    }.get(priority, "white")
                    
                    lines.append(f"{i+1}. {self._colorize(suggestion_text, priority_color)} (优先级: {priority})")
                
                lines.append("")
            
            return "\n".join(lines)
        except Exception as e:
            raise ResultFormatterError(f"以文本格式格式化验证结果失败: {str(e)}")
    
    async def _format_validation_result_table(self, validation_result: Dict[str, Any]) -> str:
        """
        以表格格式格式化验证结果
        
        Args:
            validation_result: 验证结果
            
        Returns:
            格式化后的结果字符串
        """
        try:
            lines = []
            
            # 添加标题
            task_id = validation_result.get("task_id", "未知")
            lines.append(f"验证结果 (任务ID: {task_id})")
            lines.append("=" * self.config["max_width"])
            lines.append("")
            
            # 构建基本信息表格
            basic_info = []
            
            is_valid = validation_result.get("is_valid", False)
            validation_status = "通过" if is_valid else "未通过"
            basic_info.append(["总体验证", validation_status])
            
            # 添加时间戳
            if self.config["show_timestamp"]:
                timestamp = validation_result.get("timestamp")
                if timestamp:
                    if isinstance(timestamp, (int, float)):
                        timestamp = datetime.fromtimestamp(timestamp)
                    elif isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp)
                    
                    basic_info.append(["验证时间", timestamp.strftime('%Y-%m-%d %H:%M:%S')])
            
            # 显示基本信息表格
            if basic_info:
                headers = ["属性", "值"]
                await self.interface.table(headers, basic_info, "基本信息")
                lines.append("")
            
            # 添加验证结果详情
            validation_results = validation_result.get("validation_results", {})
            if validation_results:
                lines.append("验证详情:")
                lines.append("-" * self.config["max_width"])
                
                # 构建验证结果表格
                validation_table = []
                for validator_name, validator_result in validation_results.items():
                    validator_is_valid = validator_result.get("is_valid", False)
                    validator_status = "通过" if validator_is_valid else "未通过"
                    score = validator_result.get("score", 0)
                    
                    validation_table.append([
                        validator_name,
                        validator_status,
                        f"{score:.2f}"
                    ])
                
                # 显示验证结果表格
                headers = ["验证器", "状态", "分数"]
                await self.interface.table(headers, validation_table, "验证详情")
                lines.append("")
                
                # 添加问题
                issues_table = []
                for validator_name, validator_result in validation_results.items():
                    issues = validator_result.get("issues", [])
                    for issue in issues:
                        description = issue.get("description", "")
                        severity = issue.get("severity", "medium")
                        
                        # 限制描述长度
                        if len(description) > self.config["table_max_col_width"]:
                            description = description[:self.config["table_max_col_width"]-3] + "..."
                        
                        issues_table.append([
                            validator_name,
                            description,
                            severity
                        ])
                
                if issues_table:
                    # 显示问题表格
                    headers = ["验证器", "问题", "严重程度"]
                    await self.interface.table(headers, issues_table, "问题")
                    lines.append("")
            
            # 添加验证报告
            validation_report = validation_result.get("validation_report", "")
            if validation_report:
                lines.append("验证报告:")
                lines.append("-" * self.config["max_width"])
                lines.append(self._indent_text(validation_report, self.config["indent"]))
                lines.append("")
            
            # 添加改进建议
            improvement_suggestions = validation_result.get("improvement_suggestions", [])
            if improvement_suggestions:
                lines.append("改进建议:")
                lines.append("-" * self.config["max_width"])
                
                # 构建改进建议表格
                suggestion_table = []
                for i, suggestion in enumerate(improvement_suggestions):
                    suggestion_text = suggestion.get("description", "")
                    priority = suggestion.get("priority", "medium")
                    
                    # 限制建议长度
                    if len(suggestion_text) > self.config["table_max_col_width"]:
                        suggestion_text = suggestion_text[:self.config["table_max_col_width"]-3] + "..."
                    
                    suggestion_table.append([
                        str(i+1),
                        suggestion_text,
                        priority
                    ])
                
                # 显示改进建议表格
                headers = ["序号", "建议", "优先级"]
                await self.interface.table(headers, suggestion_table, "改进建议")
                lines.append("")
            
            return "\n".join(lines)
        except Exception as e:
            raise ResultFormatterError(f"以表格格式格式化验证结果失败: {str(e)}")
    
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
                self.logger.info(f"设置结果格式化配置: {key} = {value}")
                return True
            else:
                self.logger.warning(f"未知的结果格式化配置键: {key}")
                return False
        except Exception as e:
            raise ResultFormatterError(f"设置配置失败: {str(e)}")
    
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
            raise ResultFormatterError(f"获取配置失败: {str(e)}")
    
    async def save_result(self, result: Dict[str, Any], file_path: str, 
                         format_type: str = "json") -> bool:
        """
        保存结果到文件
        
        Args:
            result: 结果数据
            file_path: 文件路径
            format_type: 格式类型
            
        Returns:
            保存是否成功
        """
        try:
            # 格式化结果
            if format_type == "json":
                formatted_result = await self._format_json(result)
            elif format_type == "text":
                formatted_result = await self._format_task_result_text(result)
            elif format_type == "table":
                formatted_result = await self._format_task_result_table(result)
            else:
                raise ResultFormatterError(f"不支持的格式类型: {format_type}")
            
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # 写入文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(formatted_result)
            
            self.logger.info(f"保存结果到 {file_path}")
            return True
        except Exception as e:
            raise ResultFormatterError(f"保存结果失败: {str(e)}")