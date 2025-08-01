"""
验证报告生成器

负责生成验证报告，
包括报告格式化、报告生成和报告导出等功能。
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable

from ..database.task_history_manager import TaskHistoryManager
from ..utils.exceptions import ReportGenerationError


class ValidationReportGenerator:
    """验证报告生成器，负责生成验证报告"""
    
    def __init__(self, db_manager):
        """
        初始化验证报告生成器
        
        Args:
            db_manager: 数据库管理器
        """
        self.db_manager = db_manager
        self.task_history_manager = TaskHistoryManager(db_manager)
        
        # 报告模板
        self.report_templates = {
            "basic": {
                "description": "基本报告",
                "template": self._generate_basic_report
            },
            "detailed": {
                "description": "详细报告",
                "template": self._generate_detailed_report
            },
            "summary": {
                "description": "摘要报告",
                "template": self._generate_summary_report
            },
            "executive": {
                "description": "执行摘要",
                "template": self._generate_executive_report
            }
        }
        
        # 报告格式
        self.report_formats = {
            "text": {
                "description": "文本格式",
                "generator": self._generate_text_report
            },
            "html": {
                "description": "HTML格式",
                "generator": self._generate_html_report
            },
            "markdown": {
                "description": "Markdown格式",
                "generator": self._generate_markdown_report
            },
            "json": {
                "description": "JSON格式",
                "generator": self._generate_json_report
            }
        }
        
        # 报告配置
        self.config = {
            "include_charts": True,          # 包含图表
            "include_recommendations": True, # 包含建议
            "include_statistics": True,     # 包含统计
            "max_issues_per_report": 20,    # 每个报告最大问题数
            "chart_width": 800,             # 图表宽度
            "chart_height": 400,            # 图表高度
            "report_dir": "reports"          # 报告目录
        }
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("验证报告生成器初始化完成")
    
    async def initialize(self):
        """初始化验证报告生成器"""
        try:
            # 确保报告目录存在
            os.makedirs(self.config["report_dir"], exist_ok=True)
            
            self.logger.info("验证报告生成器初始化完成")
        except Exception as e:
            raise ReportGenerationError(f"初始化验证报告生成器失败: {str(e)}")
    
    async def generate_validation_report(self, task_id: int, template_type: str = "detailed", 
                                      format_type: str = "html") -> str:
        """
        生成验证报告
        
        Args:
            task_id: 任务ID
            template_type: 模板类型
            format_type: 格式类型
            
        Returns:
            报告文件路径
        """
        try:
            self.logger.info(f"开始生成任务 {task_id} 的验证报告")
            
            # 获取任务验证结果
            validation_result = await self.task_history_manager.get_task_validation(task_id)
            if not validation_result:
                raise ReportGenerationError(f"任务 {task_id} 没有验证结果")
            
            # 获取任务信息
            task = await self.task_history_manager.get_task(task_id)
            if not task:
                raise ReportGenerationError(f"任务 {task_id} 不存在")
            
            # 获取任务结果
            task_result = await self.task_history_manager.get_task_result(task_id)
            
            # 生成报告内容
            template = self.report_templates.get(template_type)
            if not template:
                raise ReportGenerationError(f"未知的报告模板类型: {template_type}")
            
            report_content = await template["template"](
                task_id=task_id,
                task=task,
                task_result=task_result,
                validation_result=validation_result
            )
            
            # 格式化报告
            formatter = self.report_formats.get(format_type)
            if not formatter:
                raise ReportGenerationError(f"未知的报告格式类型: {format_type}")
            
            formatted_report = await formatter["generator"](
                task_id=task_id,
                report_content=report_content
            )
            
            # 生成报告文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"validation_report_{task_id}_{timestamp}.{format_type}"
            file_path = os.path.join(self.config["report_dir"], filename)
            
            # 保存报告
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(formatted_report)
            
            self.logger.info(f"任务 {task_id} 的验证报告已生成: {file_path}")
            return file_path
        except Exception as e:
            raise ReportGenerationError(f"生成验证报告失败: {str(e)}")
    
    async def _generate_basic_report(self, task_id: int, task: Dict, task_result: Dict, 
                                   validation_result: Dict) -> Dict:
        """
        生成基本报告内容
        
        Args:
            task_id: 任务ID
            task: 任务信息
            task_result: 任务结果
            validation_result: 验证结果
            
        Returns:
            报告内容
        """
        try:
            # 基本信息
            task_name = task.get("task_name", "未知任务")
            task_description = task.get("description", "无描述")
            created_at = task.get("created_at", "未知")
            start_time = task.get("start_time", "未知")
            end_time = task_result.get("end_time", "未知")
            
            # 验证结果
            is_valid = validation_result.get("is_valid", False)
            overall_score = validation_result.get("overall_score", 0.0)
            validation_results = validation_result.get("validation_results", {})
            issues = validation_result.get("issues", [])
            improvement_suggestions = validation_result.get("improvement_suggestions", [])
            
            # 计算执行时间
            execution_time = "未知"
            if start_time != "未知" and end_time != "未知":
                try:
                    if isinstance(start_time, str):
                        start_time = datetime.fromisoformat(start_time)
                    if isinstance(end_time, str):
                        end_time = datetime.fromisoformat(end_time)
                    
                    execution_time = (end_time - start_time).total_seconds()
                    hours, remainder = divmod(int(execution_time), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    time_parts = []
                    if hours > 0:
                        time_parts.append(f"{hours}小时")
                    if minutes > 0:
                        time_parts.append(f"{minutes}分钟")
                    if seconds > 0:
                        time_parts.append(f"{seconds}秒")
                    
                    execution_time = "".join(time_parts)
                except Exception as e:
                    self.logger.warning(f"计算执行时间失败: {str(e)}")
            
            # 构建报告内容
            report_content = {
                "title": f"任务 {task_id} 验证报告",
                "basic_info": {
                    "task_id": task_id,
                    "task_name": task_name,
                    "task_description": task_description,
                    "created_at": created_at,
                    "start_time": start_time,
                    "end_time": end_time,
                    "execution_time": execution_time
                },
                "validation_summary": {
                    "is_valid": is_valid,
                    "overall_score": overall_score,
                    "validation_results": validation_results
                },
                "issues": issues[:self.config["max_issues_per_report"]],
                "improvement_suggestions": improvement_suggestions
            }
            
            return report_content
        except Exception as e:
            raise ReportGenerationError(f"生成基本报告内容失败: {str(e)}")
    
    async def _generate_detailed_report(self, task_id: int, task: Dict, task_result: Dict, 
                                       validation_result: Dict) -> Dict:
        """
        生成详细报告内容
        
        Args:
            task_id: 任务ID
            task: 任务信息
            task_result: 任务结果
            validation_result: 验证结果
            
        Returns:
            报告内容
        """
        try:
            # 获取基本报告内容
            report_content = await self._generate_basic_report(task_id, task, task_result, validation_result)
            
            # 添加统计信息
            if self.config["include_statistics"]:
                stats = await self._get_validation_statistics(task_id)
                report_content["statistics"] = stats
            
            # 添加子任务验证结果
            sub_tasks = task_result.get("sub_tasks", [])
            if sub_tasks:
                sub_task_validations = []
                
                for sub_task in sub_tasks:
                    sub_task_id = sub_task.get("id")
                    sub_task_name = sub_task.get("name", "未知子任务")
                    sub_task_result = sub_task.get("result", {})
                    
                    # 验证子任务结果
                    sub_task_validation = await self._validate_sub_task_result(sub_task_result)
                    
                    sub_task_validations.append({
                        "sub_task_id": sub_task_id,
                        "sub_task_name": sub_task_name,
                        "validation": sub_task_validation
                    })
                
                report_content["sub_task_validations"] = sub_task_validations
            
            return report_content
        except Exception as e:
            raise ReportGenerationError(f"生成详细报告内容失败: {str(e)}")
    
    async def _generate_summary_report(self, task_id: int, task: Dict, task_result: Dict, 
                                      validation_result: Dict) -> Dict:
        """
        生成摘要报告内容
        
        Args:
            task_id: 任务ID
            task: 任务信息
            task_result: 任务结果
            validation_result: 验证结果
            
        Returns:
            报告内容
        """
        try:
            # 基本信息
            task_name = task.get("task_name", "未知任务")
            
            # 验证结果
            is_valid = validation_result.get("is_valid", False)
            overall_score = validation_result.get("overall_score", 0.0)
            issues = validation_result.get("issues", [])
            
            # 统计问题严重程度
            severity_counts = {"high": 0, "medium": 0, "low": 0}
            for issue in issues:
                severity = issue.get("severity", "medium")
                if severity in severity_counts:
                    severity_counts[severity] += 1
            
            # 构建报告内容
            report_content = {
                "title": f"任务 {task_id} 验证摘要",
                "summary": {
                    "task_id": task_id,
                    "task_name": task_name,
                    "is_valid": is_valid,
                    "overall_score": overall_score,
                    "total_issues": len(issues),
                    "severity_counts": severity_counts
                }
            }
            
            return report_content
        except Exception as e:
            raise ReportGenerationError(f"生成摘要报告内容失败: {str(e)}")
    
    async def _generate_executive_report(self, task_id: int, task: Dict, task_result: Dict, 
                                       validation_result: Dict) -> Dict:
        """
        生成执行摘要报告内容
        
        Args:
            task_id: 任务ID
            task: 任务信息
            task_result: 任务结果
            validation_result: 验证结果
            
        Returns:
            报告内容
        """
        try:
            # 获取摘要报告内容
            report_content = await self._generate_summary_report(task_id, task, task_result, validation_result)
            
            # 添加关键建议
            improvement_suggestions = validation_result.get("improvement_suggestions", [])
            
            # 筛选高优先级建议
            key_suggestions = [
                suggestion for suggestion in improvement_suggestions
                if suggestion.get("priority") == "high"
            ]
            
            report_content["key_suggestions"] = key_suggestions
            
            # 添加总体评估
            overall_score = validation_result.get("overall_score", 0.0)
            
            if overall_score >= 0.9:
                assessment = "优秀"
            elif overall_score >= 0.7:
                assessment = "良好"
            elif overall_score >= 0.5:
                assessment = "一般"
            else:
                assessment = "较差"
            
            report_content["assessment"] = assessment
            
            return report_content
        except Exception as e:
            raise ReportGenerationError(f"生成执行摘要报告内容失败: {str(e)}")
    
    async def _generate_text_report(self, task_id: int, report_content: Dict) -> str:
        """
        生成文本格式报告
        
        Args:
            task_id: 任务ID
            report_content: 报告内容
            
        Returns:
            文本格式报告
        """
        try:
            lines = []
            
            # 添加标题
            title = report_content.get("title", f"任务 {task_id} 验证报告")
            lines.append(title)
            lines.append("=" * len(title))
            lines.append("")
            
            # 添加基本信息
            if "basic_info" in report_content:
                basic_info = report_content["basic_info"]
                lines.append("基本信息:")
                lines.append("-" * 20)
                
                for key, value in basic_info.items():
                    lines.append(f"{key}: {value}")
                
                lines.append("")
            
            # 添加验证摘要
            if "validation_summary" in report_content:
                validation_summary = report_content["validation_summary"]
                lines.append("验证摘要:")
                lines.append("-" * 20)
                
                is_valid = validation_summary.get("is_valid", False)
                overall_score = validation_summary.get("overall_score", 0.0)
                
                lines.append(f"验证状态: {'通过' if is_valid else '未通过'}")
                lines.append(f"总体分数: {overall_score:.2f}")
                lines.append("")
            
            # 添加验证结果
            if "validation_summary" in report_content:
                validation_summary = report_content["validation_summary"]
                validation_results = validation_summary.get("validation_results", {})
                
                if validation_results:
                    lines.append("各项指标验证结果:")
                    lines.append("-" * 30)
                    
                    for metric_name, metric_result in validation_results.items():
                        score = metric_result.get("score", 0.0)
                        is_valid = metric_result.get("is_valid", False)
                        
                        lines.append(f"{metric_name}: {score:.2f} ({'通过' if is_valid else '未通过'})")
                    
                    lines.append("")
            
            # 添加问题
            if "issues" in report_content:
                issues = report_content["issues"]
                
                if issues:
                    lines.append("发现的问题:")
                    lines.append("-" * 20)
                    
                    for i, issue in enumerate(issues):
                        description = issue.get("description", "")
                        severity = issue.get("severity", "medium")
                        
                        lines.append(f"{i+1}. {description} (严重程度: {severity})")
                    
                    lines.append("")
            
            # 添加改进建议
            if "improvement_suggestions" in report_content:
                improvement_suggestions = report_content["improvement_suggestions"]
                
                if improvement_suggestions:
                    lines.append("改进建议:")
                    lines.append("-" * 20)
                    
                    for i, suggestion in enumerate(improvement_suggestions):
                        description = suggestion.get("description", "")
                        priority = suggestion.get("priority", "medium")
                        
                        lines.append(f"{i+1}. {description} (优先级: {priority})")
                    
                    lines.append("")
            
            # 添加统计信息
            if "statistics" in report_content:
                statistics = report_content["statistics"]
                lines.append("统计信息:")
                lines.append("-" * 20)
                
                for key, value in statistics.items():
                    lines.append(f"{key}: {value}")
                
                lines.append("")
            
            # 添加子任务验证结果
            if "sub_task_validations" in report_content:
                sub_task_validations = report_content["sub_task_validations"]
                
                if sub_task_validations:
                    lines.append("子任务验证结果:")
                    lines.append("-" * 30)
                    
                    for sub_task_validation in sub_task_validations:
                        sub_task_name = sub_task_validation.get("sub_task_name", "未知子任务")
                        validation = sub_task_validation.get("validation", {})
                        is_valid = validation.get("is_valid", False)
                        overall_score = validation.get("overall_score", 0.0)
                        
                        lines.append(f"- {sub_task_name}: {overall_score:.2f} ({'通过' if is_valid else '未通过'})")
                    
                    lines.append("")
            
            return "\n".join(lines)
        except Exception as e:
            raise ReportGenerationError(f"生成文本格式报告失败: {str(e)}")
    
    async def _generate_html_report(self, task_id: int, report_content: Dict) -> str:
        """
        生成HTML格式报告
        
        Args:
            task_id: 任务ID
            report_content: 报告内容
            
        Returns:
            HTML格式报告
        """
        try:
            html_lines = []
            
            # 添加HTML头部
            html_lines.append("<!DOCTYPE html>")
            html_lines.append("<html lang=\"zh-CN\">")
            html_lines.append("<head>")
            html_lines.append("    <meta charset=\"UTF-8\">")
            html_lines.append("    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">")
            html_lines.append("    <title>任务验证报告</title>")
            html_lines.append("    <style>")
            html_lines.append("        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }")
            html_lines.append("        .container { max-width: 1200px; margin: 0 auto; }")
            html_lines.append("        h1, h2, h3 { color: #333; }")
            html_lines.append("        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }")
            html_lines.append("        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
            html_lines.append("        th { background-color: #f2f2f2; }")
            html_lines.append("        .valid { color: green; }")
            html_lines.append("        .invalid { color: red; }")
            html_lines.append("        .high { color: red; }")
            html_lines.append("        .medium { color: orange; }")
            html_lines.append("        .low { color: blue; }")
            html_lines.append("        .score-bar { width: 100%; background-color: #f2f2f2; border-radius: 4px; }")
            html_lines.append("        .score-fill { height: 20px; border-radius: 4px; background-color: #4CAF50; }")
            html_lines.append("    </style>")
            html_lines.append("</head>")
            html_lines.append("<body>")
            html_lines.append("    <div class=\"container\">")
            
            # 添加标题
            title = report_content.get("title", f"任务 {task_id} 验证报告")
            html_lines.append(f"        <h1>{title}</h1>")
            
            # 添加基本信息
            if "basic_info" in report_content:
                basic_info = report_content["basic_info"]
                html_lines.append("        <h2>基本信息</h2>")
                html_lines.append("        <table>")
                html_lines.append("            <tr><th>属性</th><th>值</th></tr>")
                
                for key, value in basic_info.items():
                    html_lines.append(f"            <tr><td>{key}</td><td>{value}</td></tr>")
                
                html_lines.append("        </table>")
            
            # 添加验证摘要
            if "validation_summary" in report_content:
                validation_summary = report_content["validation_summary"]
                html_lines.append("        <h2>验证摘要</h2>")
                
                is_valid = validation_summary.get("is_valid", False)
                overall_score = validation_summary.get("overall_score", 0.0)
                
                html_lines.append(f"        <p>验证状态: <span class=\"{'valid' if is_valid else 'invalid'}\">{'通过' if is_valid else '未通过'}</span></p>")
                html_lines.append(f"        <p>总体分数: {overall_score:.2f}</p>")
                html_lines.append("        <div class=\"score-bar\">")
                html_lines.append(f"            <div class=\"score-fill\" style=\"width: {overall_score * 100}%\"></div>")
                html_lines.append("        </div>")
            
            # 添加验证结果
            if "validation_summary" in report_content:
                validation_summary = report_content["validation_summary"]
                validation_results = validation_summary.get("validation_results", {})
                
                if validation_results:
                    html_lines.append("        <h2>各项指标验证结果</h2>")
                    html_lines.append("        <table>")
                    html_lines.append("            <tr><th>指标</th><th>分数</th><th>状态</th></tr>")
                    
                    for metric_name, metric_result in validation_results.items():
                        score = metric_result.get("score", 0.0)
                        is_valid = metric_result.get("is_valid", False)
                        
                        html_lines.append(f"            <tr><td>{metric_name}</td><td>{score:.2f}</td><td><span class=\"{'valid' if is_valid else 'invalid'}\">{'通过' if is_valid else '未通过'}</span></td></tr>")
                    
                    html_lines.append("        </table>")
            
            # 添加问题
            if "issues" in report_content:
                issues = report_content["issues"]
                
                if issues:
                    html_lines.append("        <h2>发现的问题</h2>")
                    html_lines.append("        <table>")
                    html_lines.append("            <tr><th>序号</th><th>描述</th><th>严重程度</th></tr>")
                    
                    for i, issue in enumerate(issues):
                        description = issue.get("description", "")
                        severity = issue.get("severity", "medium")
                        
                        html_lines.append(f"            <tr><td>{i+1}</td><td>{description}</td><td><span class=\"{severity}\">{severity}</span></td></tr>")
                    
                    html_lines.append("        </table>")
            
            # 添加改进建议
            if "improvement_suggestions" in report_content:
                improvement_suggestions = report_content["improvement_suggestions"]
                
                if improvement_suggestions:
                    html_lines.append("        <h2>改进建议</h2>")
                    html_lines.append("        <table>")
                    html_lines.append("            <tr><th>序号</th><th>描述</th><th>优先级</th></tr>")
                    
                    for i, suggestion in enumerate(improvement_suggestions):
                        description = suggestion.get("description", "")
                        priority = suggestion.get("priority", "medium")
                        
                        html_lines.append(f"            <tr><td>{i+1}</td><td>{description}</td><td><span class=\"{priority}\">{priority}</span></td></tr>")
                    
                    html_lines.append("        </table>")
            
            # 添加统计信息
            if "statistics" in report_content:
                statistics = report_content["statistics"]
                html_lines.append("        <h2>统计信息</h2>")
                html_lines.append("        <table>")
                html_lines.append("            <tr><th>指标</th><th>值</th></tr>")
                
                for key, value in statistics.items():
                    html_lines.append(f"            <tr><td>{key}</td><td>{value}</td></tr>")
                
                html_lines.append("        </table>")
            
            # 添加子任务验证结果
            if "sub_task_validations" in report_content:
                sub_task_validations = report_content["sub_task_validations"]
                
                if sub_task_validations:
                    html_lines.append("        <h2>子任务验证结果</h2>")
                    html_lines.append("        <table>")
                    html_lines.append("            <tr><th>子任务</th><th>分数</th><th>状态</th></tr>")
                    
                    for sub_task_validation in sub_task_validations:
                        sub_task_name = sub_task_validation.get("sub_task_name", "未知子任务")
                        validation = sub_task_validation.get("validation", {})
                        is_valid = validation.get("is_valid", False)
                        overall_score = validation.get("overall_score", 0.0)
                        
                        html_lines.append(f"            <tr><td>{sub_task_name}</td><td>{overall_score:.2f}</td><td><span class=\"{'valid' if is_valid else 'invalid'}\">{'通过' if is_valid else '未通过'}</span></td></tr>")
                    
                    html_lines.append("        </table>")
            
            # 添加HTML尾部
            html_lines.append("    </div>")
            html_lines.append("</body>")
            html_lines.append("</html>")
            
            return "\n".join(html_lines)
        except Exception as e:
            raise ReportGenerationError(f"生成HTML格式报告失败: {str(e)}")
    
    async def _generate_markdown_report(self, task_id: int, report_content: Dict) -> str:
        """
        生成Markdown格式报告
        
        Args:
            task_id: 任务ID
            report_content: 报告内容
            
        Returns:
            Markdown格式报告
        """
        try:
            lines = []
            
            # 添加标题
            title = report_content.get("title", f"任务 {task_id} 验证报告")
            lines.append(f"# {title}")
            lines.append("")
            
            # 添加基本信息
            if "basic_info" in report_content:
                basic_info = report_content["basic_info"]
                lines.append("## 基本信息")
                lines.append("")
                
                for key, value in basic_info.items():
                    lines.append(f"- **{key}**: {value}")
                
                lines.append("")
            
            # 添加验证摘要
            if "validation_summary" in report_content:
                validation_summary = report_content["validation_summary"]
                lines.append("## 验证摘要")
                lines.append("")
                
                is_valid = validation_summary.get("is_valid", False)
                overall_score = validation_summary.get("overall_score", 0.0)
                
                lines.append(f"- **验证状态**: {'通过' if is_valid else '未通过'}")
                lines.append(f"- **总体分数**: {overall_score:.2f}")
                lines.append("")
            
            # 添加验证结果
            if "validation_summary" in report_content:
                validation_summary = report_content["validation_summary"]
                validation_results = validation_summary.get("validation_results", {})
                
                if validation_results:
                    lines.append("## 各项指标验证结果")
                    lines.append("")
                    lines.append("| 指标 | 分数 | 状态 |")
                    lines.append("|------|------|------|")
                    
                    for metric_name, metric_result in validation_results.items():
                        score = metric_result.get("score", 0.0)
                        is_valid = metric_result.get("is_valid", False)
                        
                        lines.append(f"| {metric_name} | {score:.2f} | {'通过' if is_valid else '未通过'} |")
                    
                    lines.append("")
            
            # 添加问题
            if "issues" in report_content:
                issues = report_content["issues"]
                
                if issues:
                    lines.append("## 发现的问题")
                    lines.append("")
                    lines.append("| 序号 | 描述 | 严重程度 |")
                    lines.append("|------|------|----------|")
                    
                    for i, issue in enumerate(issues):
                        description = issue.get("description", "")
                        severity = issue.get("severity", "medium")
                        
                        lines.append(f"| {i+1} | {description} | {severity} |")
                    
                    lines.append("")
            
            # 添加改进建议
            if "improvement_suggestions" in report_content:
                improvement_suggestions = report_content["improvement_suggestions"]
                
                if improvement_suggestions:
                    lines.append("## 改进建议")
                    lines.append("")
                    lines.append("| 序号 | 描述 | 优先级 |")
                    lines.append("|------|------|--------|")
                    
                    for i, suggestion in enumerate(improvement_suggestions):
                        description = suggestion.get("description", "")
                        priority = suggestion.get("priority", "medium")
                        
                        lines.append(f"| {i+1} | {description} | {priority} |")
                    
                    lines.append("")
            
            # 添加统计信息
            if "statistics" in report_content:
                statistics = report_content["statistics"]
                lines.append("## 统计信息")
                lines.append("")
                
                for key, value in statistics.items():
                    lines.append(f"- **{key}**: {value}")
                
                lines.append("")
            
            # 添加子任务验证结果
            if "sub_task_validations" in report_content:
                sub_task_validations = report_content["sub_task_validations"]
                
                if sub_task_validations:
                    lines.append("## 子任务验证结果")
                    lines.append("")
                    lines.append("| 子任务 | 分数 | 状态 |")
                    lines.append("|--------|------|------|")
                    
                    for sub_task_validation in sub_task_validations:
                        sub_task_name = sub_task_validation.get("sub_task_name", "未知子任务")
                        validation = sub_task_validation.get("validation", {})
                        is_valid = validation.get("is_valid", False)
                        overall_score = validation.get("overall_score", 0.0)
                        
                        lines.append(f"| {sub_task_name} | {overall_score:.2f} | {'通过' if is_valid else '未通过'} |")
                    
                    lines.append("")
            
            return "\n".join(lines)
        except Exception as e:
            raise ReportGenerationError(f"生成Markdown格式报告失败: {str(e)}")
    
    async def _generate_json_report(self, task_id: int, report_content: Dict) -> str:
        """
        生成JSON格式报告
        
        Args:
            task_id: 任务ID
            report_content: 报告内容
            
        Returns:
            JSON格式报告
        """
        try:
            # 添加生成时间
            report_content["generated_at"] = datetime.now().isoformat()
            
            # 转换为JSON
            json_report = json.dumps(report_content, ensure_ascii=False, indent=2)
            
            return json_report
        except Exception as e:
            raise ReportGenerationError(f"生成JSON格式报告失败: {str(e)}")
    
    async def _validate_sub_task_result(self, sub_task_result: Dict) -> Dict:
        """
        验证子任务结果
        
        Args:
            sub_task_result: 子任务结果
            
        Returns:
            验证结果
        """
        try:
            # 简化的子任务验证逻辑
            # 在实际应用中，这里可能会使用更复杂的验证逻辑
            
            # 检查结果是否为空
            result_content = sub_task_result.get("result", {})
            if not result_content:
                return {
                    "is_valid": False,
                    "overall_score": 0.0,
                    "issues": [{
                        "description": "子任务结果为空",
                        "severity": "high",
                        "suggestion": "请提供子任务结果"
                    }]
                }
            
            # 检查结果长度
            result_text = str(result_content)
            if len(result_text) < 10:
                return {
                    "is_valid": False,
                    "overall_score": 0.3,
                    "issues": [{
                        "description": "子任务结果过短",
                        "severity": "medium",
                        "suggestion": "请提供更详细的子任务结果"
                    }]
                }
            
            # 默认通过验证
            return {
                "is_valid": True,
                "overall_score": 0.8,
                "issues": []
            }
        except Exception as e:
            self.logger.error(f"验证子任务结果失败: {str(e)}")
            return {
                "is_valid": False,
                "overall_score": 0.0,
                "issues": [{
                    "description": f"验证子任务结果时出错: {str(e)}",
                    "severity": "high",
                    "suggestion": "请检查子任务结果"
                }]
            }
    
    async def _get_validation_statistics(self, task_id: int) -> Dict:
        """
        获取验证统计信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            统计信息字典
        """
        try:
            # 获取任务验证统计
            stats = await self.task_history_manager.get_task_validation_statistics(30)
            
            return stats
        except Exception as e:
            self.logger.error(f"获取验证统计信息失败: {str(e)}")
            return {}
    
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
                self.logger.info(f"设置验证报告生成配置: {key} = {value}")
                return True
            else:
                self.logger.warning(f"未知的验证报告生成配置键: {key}")
                return False
        except Exception as e:
            raise ReportGenerationError(f"设置配置失败: {str(e)}")
    
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
            raise ReportGenerationError(f"获取配置失败: {str(e)}")
    
    async def add_report_template(self, name: str, description: str, generator: Callable) -> bool:
        """
        添加报告模板
        
        Args:
            name: 模板名称
            description: 模板描述
            generator: 生成器函数
            
        Returns:
            添加是否成功
        """
        try:
            self.report_templates[name] = {
                "description": description,
                "template": generator
            }
            
            self.logger.info(f"添加报告模板: {name}")
            return True
        except Exception as e:
            raise ReportGenerationError(f"添加报告模板失败: {str(e)}")
    
    async def add_report_format(self, name: str, description: str, generator: Callable) -> bool:
        """
        添加报告格式
        
        Args:
            name: 格式名称
            description: 格式描述
            generator: 生成器函数
            
        Returns:
            添加是否成功
        """
        try:
            self.report_formats[name] = {
                "description": description,
                "generator": generator
            }
            
            self.logger.info(f"添加报告格式: {name}")
            return True
        except Exception as e:
            raise ReportGenerationError(f"添加报告格式失败: {str(e)}")
    
    async def get_report_generation_stats(self, days: int = 30) -> Dict:
        """
        获取报告生成统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        try:
            # 获取报告生成统计
            stats = await self.task_history_manager.get_report_generation_statistics(days)
            
            return stats
        except Exception as e:
            raise ReportGenerationError(f"获取报告生成统计信息失败: {str(e)}")