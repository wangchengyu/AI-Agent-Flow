"""
结果验证器

负责验证任务执行结果，
包括完整性验证、准确性验证、相关性验证等功能。
"""

import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable

from ..database.task_history_manager import TaskHistoryManager
from ..rag.knowledge_manager import KnowledgeManager
from ..utils.exceptions import ResultValidationError


class ResultValidator:
    """结果验证器，负责验证任务执行结果"""
    
    def __init__(self, db_manager, knowledge_manager: KnowledgeManager):
        """
        初始化结果验证器
        
        Args:
            db_manager: 数据库管理器
            knowledge_manager: 知识管理器
        """
        self.db_manager = db_manager
        self.knowledge_manager = knowledge_manager
        self.task_history_manager = TaskHistoryManager(db_manager)
        
        # 验证器配置
        self.config = {
            "completeness_threshold": 0.7,    # 完整性阈值
            "accuracy_threshold": 0.7,        # 准确性阈值
            "relevance_threshold": 0.7,       # 相关性阈值
            "clarity_threshold": 0.7,         # 清晰度阈值
            "timeliness_threshold": 0.7,      # 时效性阈值
            "overall_threshold": 0.7,         # 总体验证阈值
            "enable_knowledge_check": True,   # 启用知识库检查
            "max_validation_attempts": 3      # 最大验证尝试次数
        }
        
        # 验证指标
        self.validation_metrics = {
            "completeness": {
                "description": "完整性",
                "weight": 0.3,
                "validator": self._validate_completeness
            },
            "accuracy": {
                "description": "准确性",
                "weight": 0.3,
                "validator": self._validate_accuracy
            },
            "relevance": {
                "description": "相关性",
                "weight": 0.2,
                "validator": self._validate_relevance
            },
            "clarity": {
                "description": "清晰度",
                "weight": 0.1,
                "validator": self._validate_clarity
            },
            "timeliness": {
                "description": "时效性",
                "weight": 0.1,
                "validator": self._validate_timeliness
            }
        }
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("结果验证器初始化完成")
    
    async def initialize(self):
        """初始化结果验证器"""
        try:
            self.logger.info("结果验证器初始化完成")
        except Exception as e:
            raise ResultValidationError(f"初始化结果验证器失败: {str(e)}")
    
    async def validate_task_result(self, task_id: int, task_result: Dict) -> Dict:
        """
        验证任务结果
        
        Args:
            task_id: 任务ID
            task_result: 任务结果
            
        Returns:
            验证结果
        """
        try:
            self.logger.info(f"开始验证任务 {task_id} 的结果")
            
            # 获取任务信息
            task = await self.task_history_manager.get_task(task_id)
            if not task:
                raise ResultValidationError(f"任务 {task_id} 不存在")
            
            # 初始化验证结果
            validation_results = {}
            issues = []
            total_score = 0.0
            total_weight = 0.0
            
            # 执行各项验证
            for metric_name, metric_info in self.validation_metrics.items():
                validator = metric_info["validator"]
                weight = metric_info["weight"]
                
                # 执行验证
                metric_result = await validator(task_id, task_result, task)
                
                # 记录验证结果
                validation_results[metric_name] = metric_result
                
                # 计算加权总分
                score = metric_result.get("score", 0.0)
                total_score += score * weight
                total_weight += weight
                
                # 收集问题
                metric_issues = metric_result.get("issues", [])
                for issue in metric_issues:
                    issues.append({
                        "metric": metric_name,
                        "description": issue.get("description", ""),
                        "severity": issue.get("severity", "medium"),
                        "suggestion": issue.get("suggestion", "")
                    })
            
            # 计算总分
            if total_weight > 0:
                overall_score = total_score / total_weight
            else:
                overall_score = 0.0
            
            # 判断是否通过验证
            is_valid = overall_score >= self.config["overall_threshold"]
            
            # 生成改进建议
            improvement_suggestions = await self._generate_improvement_suggestions(
                validation_results, issues
            )
            
            # 生成验证报告
            validation_report = await self._generate_validation_report(
                task_result, validation_results, issues
            )
            
            # 构建验证结果
            result = {
                "task_id": task_id,
                "is_valid": is_valid,
                "overall_score": overall_score,
                "validation_results": validation_results,
                "issues": issues,
                "improvement_suggestions": improvement_suggestions,
                "validation_report": validation_report,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # 保存验证结果
            await self.task_history_manager.create_task_validation(
                task_id=task_id,
                is_valid=is_valid,
                overall_score=overall_score,
                validation_results=validation_results,
                issues=issues,
                improvement_suggestions=improvement_suggestions,
                validation_report=validation_report
            )
            
            self.logger.info(f"任务 {task_id} 的结果验证完成，总分: {overall_score:.2f}")
            return result
        except Exception as e:
            raise ResultValidationError(f"验证任务结果失败: {str(e)}")
    
    async def _validate_completeness(self, task_id: int, task_result: Dict, task: Dict) -> Dict:
        """
        验证完整性
        
        Args:
            task_id: 任务ID
            task_result: 任务结果
            task: 任务信息
            
        Returns:
            验证结果
        """
        try:
            issues = []
            score = 1.0
            
            # 获取任务描述
            task_description = task.get("description", "")
            
            # 获取结果内容
            result_content = self._extract_result_content(task_result)
            
            # 检查结果是否为空
            if not result_content:
                score -= 0.5
                issues.append({
                    "description": "结果内容为空",
                    "severity": "high",
                    "suggestion": "请提供完整的结果内容"
                })
            
            # 检查结果长度
            if len(result_content) < 50:
                score -= 0.3
                issues.append({
                    "description": "结果内容过短",
                    "severity": "medium",
                    "suggestion": "请提供更详细的结果内容"
                })
            
            # 检查是否包含任务关键词
            task_keywords = self._extract_keywords(task_description)
            if task_keywords:
                matched_keywords = sum(1 for keyword in task_keywords if keyword in result_content)
                keyword_ratio = matched_keywords / len(task_keywords)
                
                if keyword_ratio < 0.5:
                    score -= 0.2 * (1 - keyword_ratio)
                    issues.append({
                        "description": f"结果中缺少任务关键词（匹配率: {keyword_ratio:.2%}）",
                        "severity": "medium",
                        "suggestion": "请在结果中包含更多任务相关的关键词"
                    })
            
            # 检查子任务结果
            sub_tasks = task_result.get("sub_tasks", [])
            if sub_tasks:
                completed_sub_tasks = sum(1 for st in sub_tasks if st.get("status") == "completed")
                sub_task_ratio = completed_sub_tasks / len(sub_tasks)
                
                if sub_task_ratio < 1.0:
                    score -= 0.2 * (1 - sub_task_ratio)
                    issues.append({
                        "description": f"部分子任务未完成（完成率: {sub_task_ratio:.2%}）",
                        "severity": "medium",
                        "suggestion": "请确保所有子任务都已完成"
                    })
            
            # 确保分数在0-1之间
            score = max(0.0, min(1.0, score))
            
            return {
                "score": score,
                "issues": issues,
                "threshold": self.config["completeness_threshold"],
                "is_valid": score >= self.config["completeness_threshold"]
            }
        except Exception as e:
            self.logger.error(f"验证完整性失败: {str(e)}")
            return {
                "score": 0.0,
                "issues": [{
                    "description": f"验证完整性时出错: {str(e)}",
                    "severity": "high",
                    "suggestion": "请检查结果内容"
                }],
                "threshold": self.config["completeness_threshold"],
                "is_valid": False
            }
    
    async def _validate_accuracy(self, task_id: int, task_result: Dict, task: Dict) -> Dict:
        """
        验证准确性
        
        Args:
            task_id: 任务ID
            task_result: 任务结果
            task: 任务信息
            
        Returns:
            验证结果
        """
        try:
            issues = []
            score = 1.0
            
            # 获取结果内容
            result_content = self._extract_result_content(task_result)
            
            # 检查是否有明显的错误标记
            error_indicators = ["错误", "失败", "异常", "问题", "不正确", "无法", "不能"]
            for indicator in error_indicators:
                if indicator in result_content:
                    score -= 0.1
                    issues.append({
                        "description": f"结果中包含错误标记: {indicator}",
                        "severity": "medium",
                        "suggestion": "请检查并修正结果中的错误"
                    })
            
            # 检查是否有矛盾信息
            contradiction_patterns = [
                r"既是.*又是.*",
                r"一方面.*另一方面.*",
                r"虽然.*但是.*"
            ]
            
            for pattern in contradiction_patterns:
                matches = re.findall(pattern, result_content)
                if matches:
                    score -= 0.1
                    issues.append({
                        "description": "结果中可能包含矛盾信息",
                        "severity": "medium",
                        "suggestion": "请检查并修正结果中的矛盾信息"
                    })
            
            # 检查是否有不确定的表达
            uncertainty_indicators = ["可能", "也许", "大概", "或许", "应该", "估计"]
            uncertainty_count = sum(1 for indicator in uncertainty_indicators if indicator in result_content)
            
            if uncertainty_count > 3:
                score -= 0.1 * min(uncertainty_count / 3, 1.0)
                issues.append({
                    "description": "结果中包含过多不确定的表达",
                    "severity": "low",
                    "suggestion": "请尽量提供确定的信息，或明确指出不确定性"
                })
            
            # 如果启用知识库检查，进行知识验证
            if self.config["enable_knowledge_check"]:
                knowledge_score = await self._validate_with_knowledge(task_id, result_content)
                score *= knowledge_score
                
                if knowledge_score < 0.8:
                    issues.append({
                        "description": "结果与知识库中的信息不一致",
                        "severity": "medium",
                        "suggestion": "请确保结果与已知信息一致"
                    })
            
            # 确保分数在0-1之间
            score = max(0.0, min(1.0, score))
            
            return {
                "score": score,
                "issues": issues,
                "threshold": self.config["accuracy_threshold"],
                "is_valid": score >= self.config["accuracy_threshold"]
            }
        except Exception as e:
            self.logger.error(f"验证准确性失败: {str(e)}")
            return {
                "score": 0.0,
                "issues": [{
                    "description": f"验证准确性时出错: {str(e)}",
                    "severity": "high",
                    "suggestion": "请检查结果内容"
                }],
                "threshold": self.config["accuracy_threshold"],
                "is_valid": False
            }
    
    async def _validate_relevance(self, task_id: int, task_result: Dict, task: Dict) -> Dict:
        """
        验证相关性
        
        Args:
            task_id: 任务ID
            task_result: 任务结果
            task: 任务信息
            
        Returns:
            验证结果
        """
        try:
            issues = []
            score = 1.0
            
            # 获取任务描述
            task_description = task.get("description", "")
            
            # 获取结果内容
            result_content = self._extract_result_content(task_result)
            
            # 提取任务关键词
            task_keywords = self._extract_keywords(task_description)
            
            if not task_keywords:
                # 如果没有关键词，给予中等分数
                score = 0.5
                issues.append({
                    "description": "无法提取任务关键词进行相关性验证",
                    "severity": "low",
                    "suggestion": "请确保结果与任务相关"
                })
            else:
                # 计算关键词匹配度
                matched_keywords = sum(1 for keyword in task_keywords if keyword in result_content)
                keyword_ratio = matched_keywords / len(task_keywords)
                
                if keyword_ratio < 0.3:
                    score -= 0.5 * (1 - keyword_ratio / 0.3)
                    issues.append({
                        "description": f"结果与任务相关性较低（关键词匹配率: {keyword_ratio:.2%}）",
                        "severity": "high",
                        "suggestion": "请在结果中包含更多任务相关的关键词"
                    })
                elif keyword_ratio < 0.7:
                    score -= 0.2 * (1 - (keyword_ratio - 0.3) / 0.4)
                    issues.append({
                        "description": f"结果与任务相关性一般（关键词匹配率: {keyword_ratio:.2%}）",
                        "severity": "medium",
                        "suggestion": "请在结果中包含更多任务相关的关键词"
                    })
            
            # 检查是否有不相关的内容
            irrelevant_indicators = [
                "顺便说一下",
                "另外",
                "顺便提一下",
                "与此无关"
            ]
            
            for indicator in irrelevant_indicators:
                if indicator in result_content:
                    score -= 0.1
                    issues.append({
                        "description": "结果中可能包含不相关的内容",
                        "severity": "low",
                        "suggestion": "请移除与任务不相关的内容"
                    })
            
            # 确保分数在0-1之间
            score = max(0.0, min(1.0, score))
            
            return {
                "score": score,
                "issues": issues,
                "threshold": self.config["relevance_threshold"],
                "is_valid": score >= self.config["relevance_threshold"]
            }
        except Exception as e:
            self.logger.error(f"验证相关性失败: {str(e)}")
            return {
                "score": 0.0,
                "issues": [{
                    "description": f"验证相关性时出错: {str(e)}",
                    "severity": "high",
                    "suggestion": "请检查结果内容"
                }],
                "threshold": self.config["relevance_threshold"],
                "is_valid": False
            }
    
    async def _validate_clarity(self, task_id: int, task_result: Dict, task: Dict) -> Dict:
        """
        验证清晰度
        
        Args:
            task_id: 任务ID
            task_result: 任务结果
            task: 任务信息
            
        Returns:
            验证结果
        """
        try:
            issues = []
            score = 1.0
            
            # 获取结果内容
            result_content = self._extract_result_content(task_result)
            
            # 检查文本结构
            sentences = result_content.split("。")
            if len(sentences) < 3:
                score -= 0.2
                issues.append({
                    "description": "结果结构不够清晰，句子数量较少",
                    "severity": "medium",
                    "suggestion": "请使用更多的句子来组织结果，使其更清晰"
                })
            
            # 检查平均句子长度
            if sentences:
                avg_sentence_length = sum(len(s) for s in sentences) / len(sentences)
                if avg_sentence_length > 100:
                    score -= 0.2
                    issues.append({
                        "description": "结果中句子过长，可能不够清晰",
                        "severity": "medium",
                        "suggestion": "请使用更短的句子，提高结果的可读性"
                    })
            
            # 检查是否有结构标记
            structure_indicators = ["首先", "其次", "然后", "最后", "总结", "总之", "第一", "第二", "第三"]
            structure_count = sum(1 for indicator in structure_indicators if indicator in result_content)
            
            if structure_count == 0:
                score -= 0.1
                issues.append({
                    "description": "结果缺乏结构标记，可能不够清晰",
                    "severity": "low",
                    "suggestion": "请使用结构标记（如首先、其次、最后）来组织结果"
                })
            
            # 检查是否有模糊表达
            vague_indicators = ["某些", "一些", "大概", "可能", "左右", "上下"]
            vague_count = sum(1 for indicator in vague_indicators if indicator in result_content)
            
            if vague_count > 3:
                score -= 0.1 * min(vague_count / 3, 1.0)
                issues.append({
                    "description": "结果中包含过多模糊表达",
                    "severity": "low",
                    "suggestion": "请尽量使用明确的表达，减少模糊词汇"
                })
            
            # 确保分数在0-1之间
            score = max(0.0, min(1.0, score))
            
            return {
                "score": score,
                "issues": issues,
                "threshold": self.config["clarity_threshold"],
                "is_valid": score >= self.config["clarity_threshold"]
            }
        except Exception as e:
            self.logger.error(f"验证清晰度失败: {str(e)}")
            return {
                "score": 0.0,
                "issues": [{
                    "description": f"验证清晰度时出错: {str(e)}",
                    "severity": "high",
                    "suggestion": "请检查结果内容"
                }],
                "threshold": self.config["clarity_threshold"],
                "is_valid": False
            }
    
    async def _validate_timeliness(self, task_id: int, task_result: Dict, task: Dict) -> Dict:
        """
        验证时效性
        
        Args:
            task_id: 任务ID
            task_result: 任务结果
            task: 任务信息
            
        Returns:
            验证结果
        """
        try:
            issues = []
            score = 1.0
            
            # 获取结果内容
            result_content = self._extract_result_content(task_result)
            
            # 检查是否有时间标记
            time_indicators = ["最近", "目前", "当前", "现在", "今天", "昨天", "今年", "去年"]
            time_count = sum(1 for indicator in time_indicators if indicator in result_content)
            
            if time_count == 0:
                score -= 0.3
                issues.append({
                    "description": "结果中缺乏时间标记，无法确定时效性",
                    "severity": "medium",
                    "suggestion": "请在结果中包含时间信息，如'最近'、'目前'等"
                })
            
            # 检查是否有过时信息
            outdated_indicators = ["过去", "以前", "曾经", "旧", "老"]
            outdated_count = sum(1 for indicator in outdated_indicators if indicator in result_content)
            
            if outdated_count > time_count:
                score -= 0.3
                issues.append({
                    "description": "结果中可能包含过时信息",
                    "severity": "medium",
                    "suggestion": "请尽量使用最新的信息，避免过时内容"
                })
            
            # 检查任务执行时间
            start_time = task.get("start_time")
            end_time = task_result.get("end_time")
            
            if start_time and end_time:
                try:
                    # 计算执行时间
                    if isinstance(start_time, str):
                        start_time = datetime.fromisoformat(start_time)
                    if isinstance(end_time, str):
                        end_time = datetime.fromisoformat(end_time)
                    
                    execution_time = (end_time - start_time).total_seconds()
                    
                    # 如果执行时间过长，可能影响时效性
                    if execution_time > 3600:  # 超过1小时
                        score -= 0.2
                        issues.append({
                            "description": "任务执行时间过长，可能影响结果时效性",
                            "severity": "low",
                            "suggestion": "请尽量优化任务执行时间，提高结果时效性"
                        })
                except Exception as e:
                    self.logger.warning(f"计算任务执行时间失败: {str(e)}")
            
            # 确保分数在0-1之间
            score = max(0.0, min(1.0, score))
            
            return {
                "score": score,
                "issues": issues,
                "threshold": self.config["timeliness_threshold"],
                "is_valid": score >= self.config["timeliness_threshold"]
            }
        except Exception as e:
            self.logger.error(f"验证时效性失败: {str(e)}")
            return {
                "score": 0.0,
                "issues": [{
                    "description": f"验证时效性时出错: {str(e)}",
                    "severity": "high",
                    "suggestion": "请检查结果内容"
                }],
                "threshold": self.config["timeliness_threshold"],
                "is_valid": False
            }
    
    async def _validate_with_knowledge(self, task_id: int, result_content: str) -> float:
        """
        使用知识库验证结果
        
        Args:
            task_id: 任务ID
            result_content: 结果内容
            
        Returns:
            验证分数
        """
        try:
            # 提取结果中的关键信息
            key_info = self._extract_key_info(result_content)
            
            if not key_info:
                # 如果无法提取关键信息，返回中等分数
                return 0.5
            
            # 在知识库中搜索相关信息
            search_results = await self.knowledge_manager.search_knowledge(
                query=" ".join(key_info),
                limit=5
            )
            
            if not search_results:
                # 如果知识库中没有相关信息，无法验证，返回中等分数
                return 0.5
            
            # 计算知识匹配度
            total_score = 0.0
            count = 0
            
            for result in search_results:
                knowledge_content = result.get("content", "")
                knowledge_score = result.get("score", 0.0)
                
                # 检查知识内容与结果内容的一致性
                consistency_score = self._calculate_consistency(result_content, knowledge_content)
                
                # 综合分数
                combined_score = knowledge_score * 0.5 + consistency_score * 0.5
                total_score += combined_score
                count += 1
            
            if count > 0:
                return total_score / count
            else:
                return 0.5
        except Exception as e:
            self.logger.error(f"使用知识库验证失败: {str(e)}")
            return 0.5
    
    def _extract_key_info(self, text: str) -> List[str]:
        """
        提取关键信息
        
        Args:
            text: 文本
            
        Returns:
            关键信息列表
        """
        try:
            # 简化的关键信息提取逻辑
            # 在实际应用中，这里可能会使用更复杂的NLP技术
            
            # 移除常见停用词
            stop_words = ["的", "了", "和", "是", "在", "我", "有", "要", "这个", "那个", "一个", "一些", "是", "的", "了", "和", "在", "有"]
            
            # 分词（简化处理）
            words = []
            current_word = ""
            
            for char in text:
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
            
            # 返回前10个词作为关键信息
            return words[:10]
        except Exception as e:
            self.logger.error(f"提取关键信息失败: {str(e)}")
            return []
    
    def _calculate_consistency(self, text1: str, text2: str) -> float:
        """
        计算两个文本的一致性
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            一致性分数
        """
        try:
            # 提取关键词
            words1 = set(self._extract_key_info(text1))
            words2 = set(self._extract_key_info(text2))
            
            if not words1 or not words2:
                return 0.5
            
            # 计算交集
            intersection = words1.intersection(words2)
            
            # 计算并集
            union = words1.union(words2)
            
            # 计算Jaccard相似度
            if len(union) > 0:
                jaccard_similarity = len(intersection) / len(union)
            else:
                jaccard_similarity = 0.0
            
            return jaccard_similarity
        except Exception as e:
            self.logger.error(f"计算一致性失败: {str(e)}")
            return 0.5
    
    async def _generate_improvement_suggestions(self, validation_results: Dict, issues: List[Dict]) -> List[Dict]:
        """
        生成改进建议
        
        Args:
            validation_results: 验证结果
            issues: 问题列表
            
        Returns:
            改进建议列表
        """
        try:
            suggestions = []
            
            # 基于问题生成建议
            for issue in issues:
                metric = issue.get("metric", "")
                description = issue.get("description", "")
                severity = issue.get("severity", "medium")
                suggestion = issue.get("suggestion", "")
                
                # 确定优先级
                if severity == "high":
                    priority = "high"
                elif severity == "medium":
                    priority = "medium"
                else:
                    priority = "low"
                
                suggestions.append({
                    "metric": metric,
                    "description": description,
                    "suggestion": suggestion,
                    "priority": priority
                })
            
            # 基于验证结果生成额外建议
            for metric_name, metric_result in validation_results.items():
                score = metric_result.get("score", 1.0)
                threshold = metric_result.get("threshold", 0.7)
                
                # 如果分数接近阈值，给出改进建议
                if threshold - score < 0.1 and score < threshold:
                    metric_description = self.validation_metrics[metric_name]["description"]
                    
                    suggestions.append({
                        "metric": metric_name,
                        "description": f"{metric_description}接近阈值，需要改进",
                        "suggestion": self._get_metric_improvement_suggestion(metric_name),
                        "priority": "medium"
                    })
            
            # 去重
            unique_suggestions = []
            seen_descriptions = set()
            
            for suggestion in suggestions:
                description = suggestion["description"]
                if description not in seen_descriptions:
                    seen_descriptions.add(description)
                    unique_suggestions.append(suggestion)
            
            return unique_suggestions
        except Exception as e:
            raise ResultValidationError(f"生成改进建议失败: {str(e)}")
    
    def _get_metric_improvement_suggestion(self, metric_name: str) -> str:
        """
        获取指标改进建议
        
        Args:
            metric_name: 指标名称
            
        Returns:
            改进建议
        """
        try:
            if metric_name == "completeness":
                return "请提供更完整的结果内容，确保涵盖所有必要的方面"
            elif metric_name == "accuracy":
                return "请检查并修正结果中的错误，确保信息准确无误"
            elif metric_name == "relevance":
                return "请确保结果与任务高度相关，包含更多任务关键词"
            elif metric_name == "clarity":
                return "请使用更清晰的结构和表达，提高结果的可读性"
            elif metric_name == "timeliness":
                return "请使用最新的信息，并在结果中包含时间标记"
            else:
                return "请改进结果质量，提高各项指标"
        except Exception as e:
            self.logger.error(f"获取指标改进建议失败: {str(e)}")
            return "请改进结果质量"
    
    async def _generate_validation_report(self, task_result: Dict, validation_results: Dict, issues: List[Dict]) -> str:
        """
        生成验证报告
        
        Args:
            task_result: 任务结果
            validation_results: 验证结果
            issues: 问题列表
            
        Returns:
            验证报告
        """
        try:
            report_lines = []
            
            # 添加标题
            task_id = task_result.get("task_id", "未知")
            report_lines.append(f"任务 {task_id} 结果验证报告")
            report_lines.append("=" * 50)
            report_lines.append("")
            
            # 添加总体评估
            total_score = 0.0
            total_weight = 0.0
            
            for metric_name, metric_result in validation_results.items():
                score = metric_result.get("score", 0.0)
                weight = self.validation_metrics[metric_name]["weight"]
                
                total_score += score * weight
                total_weight += weight
            
            if total_weight > 0:
                overall_score = total_score / total_weight
            else:
                overall_score = 0.0
            
            is_valid = overall_score >= self.config["overall_threshold"]
            
            report_lines.append(f"总体评估: {'通过' if is_valid else '未通过'}")
            report_lines.append(f"总体分数: {overall_score:.2f}")
            report_lines.append(f"阈值: {self.config['overall_threshold']:.2f}")
            report_lines.append("")
            
            # 添加各项指标评估
            report_lines.append("各项指标评估:")
            report_lines.append("-" * 30)
            
            for metric_name, metric_result in validation_results.items():
                metric_description = self.validation_metrics[metric_name]["description"]
                score = metric_result.get("score", 0.0)
                threshold = metric_result.get("threshold", 0.7)
                is_valid = score >= threshold
                
                report_lines.append(f"- {metric_description}: {score:.2f} ({'通过' if is_valid else '未通过'}, 阈值: {threshold:.2f})")
            
            report_lines.append("")
            
            # 添加问题列表
            if issues:
                report_lines.append("发现的问题:")
                report_lines.append("-" * 30)
                
                for i, issue in enumerate(issues):
                    metric = issue.get("metric", "")
                    description = issue.get("description", "")
                    severity = issue.get("severity", "medium")
                    
                    report_lines.append(f"{i+1}. [{metric}] {description} (严重程度: {severity})")
            
            return "\n".join(report_lines)
        except Exception as e:
            raise ResultValidationError(f"生成验证报告失败: {str(e)}")
    
    def _extract_result_content(self, task_result: Dict) -> str:
        """
        提取结果内容
        
        Args:
            task_result: 任务结果
            
        Returns:
            结果内容
        """
        try:
            text_parts = []
            
            # 递归提取文本
            def extract_text(obj):
                if isinstance(obj, str):
                    text_parts.append(obj)
                elif isinstance(obj, dict):
                    for value in obj.values():
                        extract_text(value)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_text(item)
            
            extract_text(task_result)
            return " ".join(text_parts)
        except Exception as e:
            self.logger.error(f"提取结果内容失败: {str(e)}")
            return ""
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词
        
        Args:
            text: 文本
            
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
            
            for char in text:
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
            self.logger.error(f"提取关键词失败: {str(e)}")
            return []
    
    async def get_task_validation(self, task_id: int) -> Dict:
        """
        获取任务验证结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务验证结果
        """
        try:
            validation_result = await self.task_history_manager.get_task_validation(task_id)
            return validation_result
        except Exception as e:
            raise ResultValidationError(f"获取任务验证结果失败: {str(e)}")
    
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
                self.logger.info(f"设置结果验证配置: {key} = {value}")
                return True
            else:
                self.logger.warning(f"未知的结果验证配置键: {key}")
                return False
        except Exception as e:
            raise ResultValidationError(f"设置配置失败: {str(e)}")
    
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
            raise ResultValidationError(f"获取配置失败: {str(e)}")
    
    async def add_validation_metric(self, name: str, description: str, weight: float, validator: Callable) -> bool:
        """
        添加验证指标
        
        Args:
            name: 指标名称
            description: 指标描述
            weight: 权重
            validator: 验证器函数
            
        Returns:
            添加是否成功
        """
        try:
            self.validation_metrics[name] = {
                "description": description,
                "weight": weight,
                "validator": validator
            }
            
            self.logger.info(f"添加验证指标: {name} (权重: {weight})")
            return True
        except Exception as e:
            raise ResultValidationError(f"添加验证指标失败: {str(e)}")
    
    async def get_validation_stats(self, days: int = 30) -> Dict:
        """
        获取验证统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        try:
            # 获取任务验证统计
            stats = await self.task_history_manager.get_task_validation_statistics(days)
            
            return stats
        except Exception as e:
            raise ResultValidationError(f"获取验证统计信息失败: {str(e)}")