"""
验证模块

负责验证任务执行结果的质量和准确性，
并生成验证报告和改进建议。
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable

from ..database.task_history_manager import TaskHistoryManager
from ..rag.knowledge_manager import KnowledgeManager
from ..utils.exceptions import ValidationError


class ValidationModule:
    """验证模块，负责验证任务执行结果的质量和准确性"""
    
    def __init__(self, db_manager, knowledge_manager: KnowledgeManager):
        """
        初始化验证模块
        
        Args:
            db_manager: 数据库管理器
            knowledge_manager: 知识管理器
        """
        self.db_manager = db_manager
        self.knowledge_manager = knowledge_manager
        self.task_history_manager = TaskHistoryManager(db_manager)
        
        # 验证器
        self.validators = {
            "completeness": self._validate_completeness,
            "accuracy": self._validate_accuracy,
            "consistency": self._validate_consistency,
            "relevance": self._validate_relevance,
            "quality": self._validate_quality
        }
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """初始化验证模块"""
        try:
            self.logger.info("验证模块初始化完成")
        except Exception as e:
            raise ValidationError(f"初始化验证模块失败: {str(e)}")
    
    async def validate_results(self, task_id: int, results: List[Dict], 
                              user_id: Optional[int] = None) -> Dict:
        """
        验证任务结果
        
        Args:
            task_id: 任务ID
            results: 子任务结果列表
            user_id: 用户ID
            
        Returns:
            验证结果字典
        """
        try:
            self.logger.info(f"开始验证任务 {task_id} 的结果")
            
            # 获取任务信息
            task = await self.task_history_manager.get_task(task_id)
            if not task:
                raise ValidationError(f"任务 {task_id} 不存在")
            
            # 1. 执行各种验证
            validation_results = {}
            overall_valid = True
            
            for validator_name, validator_func in self.validators.items():
                try:
                    validator_result = await validator_func(task_id, task, results)
                    validation_results[validator_name] = validator_result
                    
                    # 如果有任何验证失败，整体验证失败
                    if not validator_result["is_valid"]:
                        overall_valid = False
                except Exception as e:
                    self.logger.error(f"验证器 {validator_name} 执行失败: {str(e)}")
                    validation_results[validator_name] = {
                        "is_valid": False,
                        "error": str(e)
                    }
                    overall_valid = False
            
            # 2. 生成验证报告
            validation_report = await self._generate_validation_report(
                task_id, task, results, validation_results
            )
            
            # 3. 生成改进建议
            improvement_suggestions = await self._generate_improvement_suggestions(
                task_id, task, results, validation_results
            )
            
            # 4. 组合最终验证结果
            final_validation_result = {
                "task_id": task_id,
                "is_valid": overall_valid,
                "validation_results": validation_results,
                "validation_report": validation_report,
                "improvement_suggestions": improvement_suggestions,
                "timestamp": time.time()
            }
            
            # 5. 保存验证结果
            await self.task_history_manager.create_validation_result(
                task_id=task_id,
                is_valid=overall_valid,
                validation_results=validation_results,
                validation_report=validation_report,
                improvement_suggestions=improvement_suggestions
            )
            
            self.logger.info(f"任务 {task_id} 的结果验证完成，整体验证: {'通过' if overall_valid else '未通过'}")
            return final_validation_result
        except Exception as e:
            raise ValidationError(f"验证任务结果失败: {str(e)}")
    
    async def _validate_completeness(self, task_id: int, task: Dict, results: List[Dict]) -> Dict:
        """
        验证完整性
        
        Args:
            task_id: 任务ID
            task: 任务信息
            results: 子任务结果列表
            
        Returns:
            验证结果字典
        """
        try:
            # 检查所有子任务是否都有结果
            missing_results = []
            incomplete_results = []
            
            for result in results:
                sub_task_id = result.get("sub_task_id", "")
                
                # 检查是否有结果
                if "result" not in result or not result["result"]:
                    missing_results.append(sub_task_id)
                
                # 检查结果是否完整
                if isinstance(result.get("result"), dict):
                    result_content = result["result"]
                    
                    # 检查是否有明显的缺失字段
                    if "generated_content" in result_content and not result_content["generated_content"]:
                        incomplete_results.append(sub_task_id)
                    
                    if "search_results" in result_content and not result_content["search_results"]:
                        incomplete_results.append(sub_task_id)
            
            # 确定验证结果
            is_valid = len(missing_results) == 0 and len(incomplete_results) == 0
            
            # 生成问题列表
            issues = []
            
            if missing_results:
                issues.append({
                    "type": "missing_results",
                    "description": f"以下子任务缺少结果: {', '.join(missing_results)}",
                    "severity": "high"
                })
            
            if incomplete_results:
                issues.append({
                    "type": "incomplete_results",
                    "description": f"以下子任务结果不完整: {', '.join(incomplete_results)}",
                    "severity": "medium"
                })
            
            return {
                "is_valid": is_valid,
                "score": 1.0 - (len(missing_results) * 0.5 + len(incomplete_results) * 0.2) / max(len(results), 1),
                "issues": issues,
                "details": {
                    "total_sub_tasks": len(results),
                    "missing_results": len(missing_results),
                    "incomplete_results": len(incomplete_results)
                }
            }
        except Exception as e:
            raise ValidationError(f"验证完整性失败: {str(e)}")
    
    async def _validate_accuracy(self, task_id: int, task: Dict, results: List[Dict]) -> Dict:
        """
        验证准确性
        
        Args:
            task_id: 任务ID
            task: 任务信息
            results: 子任务结果列表
            
        Returns:
            验证结果字典
        """
        try:
            # 简化的准确性验证
            # 在实际应用中，这里可能会使用更复杂的验证逻辑，如交叉验证、专家验证等
            
            issues = []
            accuracy_score = 1.0
            
            # 检查结果中的错误
            for result in results:
                sub_task_id = result.get("sub_task_id", "")
                
                # 检查是否有错误
                if "error" in result:
                    issues.append({
                        "type": "execution_error",
                        "description": f"子任务 {sub_task_id} 执行时出现错误: {result['error']}",
                        "severity": "high",
                        "sub_task_id": sub_task_id
                    })
                    accuracy_score -= 0.3
                
                # 检查结果中的警告
                if "warnings" in result:
                    for warning in result["warnings"]:
                        issues.append({
                            "type": "warning",
                            "description": f"子任务 {sub_task_id} 执行时出现警告: {warning}",
                            "severity": "medium",
                            "sub_task_id": sub_task_id
                        })
                        accuracy_score -= 0.1
            
            # 确保分数在0-1之间
            accuracy_score = max(0.0, min(1.0, accuracy_score))
            
            # 确定验证结果
            is_valid = accuracy_score >= 0.7
            
            return {
                "is_valid": is_valid,
                "score": accuracy_score,
                "issues": issues,
                "details": {
                    "accuracy_score": accuracy_score,
                    "error_count": len([issue for issue in issues if issue["severity"] == "high"]),
                    "warning_count": len([issue for issue in issues if issue["severity"] == "medium"])
                }
            }
        except Exception as e:
            raise ValidationError(f"验证准确性失败: {str(e)}")
    
    async def _validate_consistency(self, task_id: int, task: Dict, results: List[Dict]) -> Dict:
        """
        验证一致性
        
        Args:
            task_id: 任务ID
            task: 任务信息
            results: 子任务结果列表
            
        Returns:
            验证结果字典
        """
        try:
            # 检查结果之间的一致性
            issues = []
            consistency_score = 1.0
            
            # 检查结果之间的冲突
            for i, result1 in enumerate(results):
                for j, result2 in enumerate(results[i+1:], i+1):
                    # 检查是否有冲突的结果
                    conflict = await self._check_result_conflict(result1, result2)
                    if conflict:
                        issues.append({
                            "type": "result_conflict",
                            "description": f"子任务 {result1.get('sub_task_id', '')} 和 {result2.get('sub_task_id', '')} 的结果存在冲突: {conflict}",
                            "severity": "high",
                            "sub_task_ids": [result1.get("sub_task_id", ""), result2.get("sub_task_id", "")]
                        })
                        consistency_score -= 0.4
            
            # 检查结果与任务描述的一致性
            task_description = task["description"].lower()
            
            for result in results:
                sub_task_id = result.get("sub_task_id", "")
                
                # 检查结果是否与任务描述一致
                inconsistency = await self._check_task_result_consistency(task_description, result)
                if inconsistency:
                    issues.append({
                        "type": "task_inconsistency",
                        "description": f"子任务 {sub_task_id} 的结果与任务描述不一致: {inconsistency}",
                        "severity": "medium",
                        "sub_task_id": sub_task_id
                    })
                    consistency_score -= 0.2
            
            # 确保分数在0-1之间
            consistency_score = max(0.0, min(1.0, consistency_score))
            
            # 确定验证结果
            is_valid = consistency_score >= 0.7
            
            return {
                "is_valid": is_valid,
                "score": consistency_score,
                "issues": issues,
                "details": {
                    "consistency_score": consistency_score,
                    "conflict_count": len([issue for issue in issues if issue["type"] == "result_conflict"]),
                    "inconsistency_count": len([issue for issue in issues if issue["type"] == "task_inconsistency"])
                }
            }
        except Exception as e:
            raise ValidationError(f"验证一致性失败: {str(e)}")
    
    async def _check_result_conflict(self, result1: Dict, result2: Dict) -> Optional[str]:
        """
        检查两个结果之间是否存在冲突
        
        Args:
            result1: 第一个结果
            result2: 第二个结果
            
        Returns:
            冲突描述，如果没有冲突则返回None
        """
        try:
            # 简化的冲突检测逻辑
            # 在实际应用中，这里可能会有更复杂的冲突检测逻辑
            
            # 检查结果类型
            result1_type = result1.get("type", "")
            result2_type = result2.get("type", "")
            
            # 如果是相同类型的结果，检查内容是否冲突
            if result1_type == result2_type:
                result1_content = result1.get("result", {})
                result2_content = result2.get("result", {})
                
                # 检查生成的内容是否冲突
                if (result1_type == "generation" and 
                    "generated_content" in result1_content and 
                    "generated_content" in result2_content):
                    
                    content1 = result1_content["generated_content"]
                    content2 = result2_content["generated_content"]
                    
                    if content1 and content2 and content1 != content2:
                        return f"生成的内容不一致: '{content1}' vs '{content2}'"
                
                # 检查分析结果是否冲突
                if (result1_type == "analysis" and 
                    "findings" in result1_content and 
                    "findings" in result2_content):
                    
                    findings1 = result1_content["findings"]
                    findings2 = result2_content["findings"]
                    
                    # 检查是否有相反的结论
                    for finding1 in findings1:
                        for finding2 in findings2:
                            if await self._are_opposite_findings(finding1, finding2):
                                return f"分析结果存在相反结论: '{finding1}' vs '{finding2}'"
            
            return None
        except Exception as e:
            raise ValidationError(f"检查结果冲突失败: {str(e)}")
    
    async def _are_opposite_findings(self, finding1: Dict, finding2: Dict) -> bool:
        """
        检查两个发现是否相反
        
        Args:
            finding1: 第一个发现
            finding2: 第二个发现
            
        Returns:
            是否相反
        """
        try:
            # 简化的相反发现检测逻辑
            # 在实际应用中，这里可能会有更复杂的逻辑
            
            # 检查是否有明确的相反关键词
            opposite_pairs = [
                ("是", "否"),
                ("有", "没有"),
                ("存在", "不存在"),
                ("成功", "失败"),
                ("正确", "错误")
            ]
            
            text1 = json.dumps(finding1).lower()
            text2 = json.dumps(finding2).lower()
            
            for pair in opposite_pairs:
                if pair[0] in text1 and pair[1] in text2:
                    return True
                if pair[1] in text1 and pair[0] in text2:
                    return True
            
            return False
        except Exception as e:
            raise ValidationError(f"检查相反发现失败: {str(e)}")
    
    async def _check_task_result_consistency(self, task_description: str, result: Dict) -> Optional[str]:
        """
        检查结果与任务描述的一致性
        
        Args:
            task_description: 任务描述
            result: 子任务结果
            
        Returns:
            不一致描述，如果没有不一致则返回None
        """
        try:
            # 简化的一致性检查逻辑
            # 在实际应用中，这里可能会有更复杂的逻辑
            
            result_content = result.get("result", {})
            result_type = result.get("type", "")
            
            # 检查任务描述中的关键词是否在结果中体现
            if result_type == "generation":
                # 检查是否生成了请求的内容
                if "生成" in task_description or "创建" in task_description:
                    if "generated_content" not in result_content or not result_content["generated_content"]:
                        return "任务要求生成内容，但结果中没有生成内容"
            
            elif result_type == "analysis":
                # 检查是否进行了分析
                if "分析" in task_description:
                    if "findings" not in result_content or not result_content["findings"]:
                        return "任务要求进行分析，但结果中没有分析发现"
            
            elif result_type == "search":
                # 检查是否进行了搜索
                if "搜索" in task_description or "查找" in task_description:
                    if "search_results" not in result_content or not result_content["search_results"]:
                        return "任务要求进行搜索，但结果中没有搜索结果"
            
            return None
        except Exception as e:
            raise ValidationError(f"检查任务结果一致性失败: {str(e)}")
    
    async def _validate_relevance(self, task_id: int, task: Dict, results: List[Dict]) -> Dict:
        """
        验证相关性
        
        Args:
            task_id: 任务ID
            task: 任务信息
            results: 子任务结果列表
            
        Returns:
            验证结果字典
        """
        try:
            # 检查结果与任务的相关性
            issues = []
            relevance_score = 1.0
            
            # 获取任务关键词
            task_keywords = await self._extract_task_keywords(task["description"])
            
            for result in results:
                sub_task_id = result.get("sub_task_id", "")
                result_content = result.get("result", {})
                
                # 检查结果是否包含任务关键词
                result_text = json.dumps(result_content).lower()
                matched_keywords = []
                
                for keyword in task_keywords:
                    if keyword.lower() in result_text:
                        matched_keywords.append(keyword)
                
                # 计算相关性分数
                keyword_relevance = len(matched_keywords) / max(len(task_keywords), 1)
                
                if keyword_relevance < 0.3:
                    issues.append({
                        "type": "low_relevance",
                        "description": f"子任务 {sub_task_id} 的结果与任务相关性较低，匹配的关键词: {matched_keywords}",
                        "severity": "medium",
                        "sub_task_id": sub_task_id
                    })
                    relevance_score -= 0.3
            
            # 确保分数在0-1之间
            relevance_score = max(0.0, min(1.0, relevance_score))
            
            # 确定验证结果
            is_valid = relevance_score >= 0.5
            
            return {
                "is_valid": is_valid,
                "score": relevance_score,
                "issues": issues,
                "details": {
                    "relevance_score": relevance_score,
                    "task_keywords": task_keywords
                }
            }
        except Exception as e:
            raise ValidationError(f"验证相关性失败: {str(e)}")
    
    async def _extract_task_keywords(self, task_description: str) -> List[str]:
        """
        提取任务关键词
        
        Args:
            task_description: 任务描述
            
        Returns:
            关键词列表
        """
        try:
            # 简化的关键词提取逻辑
            # 在实际应用中，这里可能会使用更复杂的NLP技术
            
            # 移除常见停用词
            stop_words = ["的", "了", "和", "是", "在", "我", "有", "要", "这个", "那个", "一个", "一些"]
            
            # 分词（简化处理）
            words = []
            current_word = ""
            
            for char in task_description:
                if char.isalnum() or char in ["_", "-"]:
                    current_word += char
                else:
                    if current_word:
                        if len(current_word) > 1 and current_word not in stop_words:
                            words.append(current_word)
                        current_word = ""
            
            # 添加最后一个词
            if current_word and len(current_word) > 1 and current_word not in stop_words:
                words.append(current_word)
            
            return words
        except Exception as e:
            raise ValidationError(f"提取任务关键词失败: {str(e)}")
    
    async def _validate_quality(self, task_id: int, task: Dict, results: List[Dict]) -> Dict:
        """
        验证质量
        
        Args:
            task_id: 任务ID
            task: 任务信息
            results: 子任务结果列表
            
        Returns:
            验证结果字典
        """
        try:
            # 检查结果的质量
            issues = []
            quality_score = 1.0
            
            for result in results:
                sub_task_id = result.get("sub_task_id", "")
                result_content = result.get("result", {})
                result_type = result.get("type", "")
                
                # 根据结果类型检查质量
                if result_type == "generation":
                    # 检查生成内容的质量
                    if "generated_content" in result_content:
                        content = result_content["generated_content"]
                        
                        # 检查内容长度
                        if len(content) < 10:
                            issues.append({
                                "type": "low_quality",
                                "description": f"子任务 {sub_task_id} 的生成内容过短",
                                "severity": "medium",
                                "sub_task_id": sub_task_id
                            })
                            quality_score -= 0.2
                        
                        # 检查内容结构
                        if not any(char in content for char in [".", "!", "?", "\n"]):
                            issues.append({
                                "type": "low_quality",
                                "description": f"子任务 {sub_task_id} 的生成内容缺乏结构",
                                "severity": "low",
                                "sub_task_id": sub_task_id
                            })
                            quality_score -= 0.1
                
                elif result_type == "analysis":
                    # 检查分析结果的质量
                    if "findings" in result_content:
                        findings = result_content["findings"]
                        
                        # 检查发现数量
                        if len(findings) < 1:
                            issues.append({
                                "type": "low_quality",
                                "description": f"子任务 {sub_task_id} 的分析发现过少",
                                "severity": "medium",
                                "sub_task_id": sub_task_id
                            })
                            quality_score -= 0.2
                
                elif result_type == "search":
                    # 检查搜索结果的质量
                    if "search_results" in result_content:
                        search_results = result_content["search_results"]
                        
                        # 检查搜索结果数量
                        if len(search_results) < 1:
                            issues.append({
                                "type": "low_quality",
                                "description": f"子任务 {sub_task_id} 的搜索结果过少",
                                "severity": "medium",
                                "sub_task_id": sub_task_id
                            })
                            quality_score -= 0.2
            
            # 确保分数在0-1之间
            quality_score = max(0.0, min(1.0, quality_score))
            
            # 确定验证结果
            is_valid = quality_score >= 0.6
            
            return {
                "is_valid": is_valid,
                "score": quality_score,
                "issues": issues,
                "details": {
                    "quality_score": quality_score
                }
            }
        except Exception as e:
            raise ValidationError(f"验证质量失败: {str(e)}")
    
    async def _generate_validation_report(self, task_id: int, task: Dict, results: List[Dict], 
                                        validation_results: Dict) -> str:
        """
        生成验证报告
        
        Args:
            task_id: 任务ID
            task: 任务信息
            results: 子任务结果列表
            validation_results: 验证结果字典
            
        Returns:
            验证报告
        """
        try:
            # 计算总体分数
            total_score = sum(result.get("score", 0) for result in validation_results.values()) / len(validation_results)
            
            # 生成报告
            report_lines = [
                f"# 任务 {task_id} 验证报告",
                f"",
                f"## 任务信息",
                f"- 任务描述: {task['description']}",
                f"- 任务状态: {task['status']}",
                f"- 子任务数量: {len(results)}",
                f"",
                f"## 验证结果",
                f"- 总体验证: {'通过' if all(result.get('is_valid', False) for result in validation_results.values()) else '未通过'}",
                f"- 总体分数: {total_score:.2f}",
                f""
            ]
            
            # 添加各个验证器的结果
            for validator_name, validator_result in validation_results.items():
                report_lines.extend([
                    f"### {validator_name.capitalize()} 验证",
                    f"- 验证结果: {'通过' if validator_result.get('is_valid', False) else '未通过'}",
                    f"- 验证分数: {validator_result.get('score', 0):.2f}",
                    f""
                ])
                
                # 添加问题
                issues = validator_result.get("issues", [])
                if issues:
                    report_lines.append("#### 问题:")
                    for issue in issues:
                        report_lines.append(f"- {issue['description']} (严重程度: {issue['severity']})")
                    report_lines.append("")
            
            # 添加总结
            report_lines.extend([
                f"## 总结",
                f"任务 {task_id} 的执行结果{'满足' if total_score >= 0.7 else '不满足'}质量要求。",
                f"建议{'继续执行' if total_score >= 0.7 else '根据问题进行改进后重新执行'}。"
            ])
            
            return "\n".join(report_lines)
        except Exception as e:
            raise ValidationError(f"生成验证报告失败: {str(e)}")
    
    async def _generate_improvement_suggestions(self, task_id: int, task: Dict, results: List[Dict], 
                                             validation_results: Dict) -> List[Dict]:
        """
        生成改进建议
        
        Args:
            task_id: 任务ID
            task: 任务信息
            results: 子任务结果列表
            validation_results: 验证结果字典
            
        Returns:
            改进建议列表
        """
        try:
            suggestions = []
            
            # 根据验证结果生成建议
            for validator_name, validator_result in validation_results.items():
                if not validator_result.get("is_valid", False):
                    # 根据验证器类型生成建议
                    if validator_name == "completeness":
                        suggestions.append({
                            "type": "completeness",
                            "description": "确保所有子任务都有完整的结果",
                            "priority": "high"
                        })
                    
                    elif validator_name == "accuracy":
                        suggestions.append({
                            "type": "accuracy",
                            "description": "检查并修复执行过程中的错误",
                            "priority": "high"
                        })
                    
                    elif validator_name == "consistency":
                        suggestions.append({
                            "type": "consistency",
                            "description": "解决结果之间的冲突和不一致",
                            "priority": "medium"
                        })
                    
                    elif validator_name == "relevance":
                        suggestions.append({
                            "type": "relevance",
                            "description": "确保结果与任务描述相关",
                            "priority": "medium"
                        })
                    
                    elif validator_name == "quality":
                        suggestions.append({
                            "type": "quality",
                            "description": "提高结果的质量和详细程度",
                            "priority": "medium"
                        })
            
            # 如果没有具体的建议，添加通用建议
            if not suggestions:
                total_score = sum(result.get("score", 0) for result in validation_results.values()) / len(validation_results)
                
                if total_score < 0.9:
                    suggestions.append({
                        "type": "general",
                        "description": "进一步优化任务执行过程以提高结果质量",
                        "priority": "low"
                    })
            
            return suggestions
        except Exception as e:
            raise ValidationError(f"生成改进建议失败: {str(e)}")
    
    async def get_validation_result(self, task_id: int) -> Dict:
        """
        获取任务验证结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            验证结果字典
        """
        try:
            validation_result = await self.task_history_manager.get_validation_result(task_id)
            return validation_result
        except Exception as e:
            raise ValidationError(f"获取验证结果失败: {str(e)}")
    
    async def add_validator(self, name: str, validator_func: Callable) -> bool:
        """
        添加验证器
        
        Args:
            name: 验证器名称
            validator_func: 验证器函数
            
        Returns:
            添加是否成功
        """
        try:
            self.validators[name] = validator_func
            self.logger.info(f"添加验证器: {name}")
            return True
        except Exception as e:
            raise ValidationError(f"添加验证器失败: {str(e)}")
    
    async def get_validation_stats(self, days: int = 30) -> Dict:
        """
        获取验证统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        try:
            # 获取验证结果统计
            validation_stats = await self.task_history_manager.get_validation_statistics(days)
            
            return validation_stats
        except Exception as e:
            raise ValidationError(f"获取验证统计信息失败: {str(e)}")