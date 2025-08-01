"""
信息需求检测器

负责检测任务执行过程中的信息需求，
包括信息缺失检测、信息质量评估和信息需求生成。
"""

import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable

from ..database.task_history_manager import TaskHistoryManager
from ..rag.knowledge_manager import KnowledgeManager
from ..utils.exceptions import InfoRequirementError


class InfoRequirementDetector:
    """信息需求检测器，负责检测任务执行过程中的信息需求"""
    
    def __init__(self, db_manager, knowledge_manager: KnowledgeManager):
        """
        初始化信息需求检测器
        
        Args:
            db_manager: 数据库管理器
            knowledge_manager: 知识管理器
        """
        self.db_manager = db_manager
        self.knowledge_manager = knowledge_manager
        self.task_history_manager = TaskHistoryManager(db_manager)
        
        # 信息需求模式
        self.info_requirement_patterns = [
            # 缺少具体信息
            {
                "pattern": r"(需要|缺少|缺乏|没有)\s*(具体|详细|明确|相关)\s*(信息|数据|资料|内容)",
                "type": "missing_specific_info",
                "priority": "high"
            },
            # 缺少背景信息
            {
                "pattern": r"(需要|缺少|缺乏|没有)\s*(背景|上下文|环境|场景)\s*(信息|数据|资料)",
                "type": "missing_context_info",
                "priority": "high"
            },
            # 缺少用户偏好
            {
                "pattern": r"(需要|缺少|缺乏|没有)\s*(用户|客户)\s*(偏好|需求|要求|期望)",
                "type": "missing_user_preference",
                "priority": "medium"
            },
            # 缺少技术细节
            {
                "pattern": r"(需要|缺少|缺乏|没有)\s*(技术|实现|具体)\s*(细节|方案|方法)",
                "type": "missing_technical_detail",
                "priority": "medium"
            },
            # 缺少约束条件
            {
                "pattern": r"(需要|缺少|缺乏|没有)\s*(约束|限制|条件|要求)",
                "type": "missing_constraint",
                "priority": "medium"
            },
            # 缺少示例
            {
                "pattern": r"(需要|缺少|缺乏|没有)\s*(示例|样例|案例|参考)",
                "type": "missing_example",
                "priority": "low"
            }
        ]
        
        # 信息质量评估指标
        self.quality_metrics = {
            "completeness": {
                "description": "信息完整性",
                "weight": 0.3
            },
            "accuracy": {
                "description": "信息准确性",
                "weight": 0.3
            },
            "relevance": {
                "description": "信息相关性",
                "weight": 0.2
            },
            "clarity": {
                "description": "信息清晰度",
                "weight": 0.1
            },
            "timeliness": {
                "description": "信息时效性",
                "weight": 0.1
            }
        }
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("信息需求检测器初始化完成")
    
    async def initialize(self):
        """初始化信息需求检测器"""
        try:
            self.logger.info("信息需求检测器初始化完成")
        except Exception as e:
            raise InfoRequirementError(f"初始化信息需求检测器失败: {str(e)}")
    
    async def detect_info_requirements(self, task_id: int, sub_task_results: List[Dict]) -> Dict:
        """
        检测信息需求
        
        Args:
            task_id: 任务ID
            sub_task_results: 子任务结果列表
            
        Returns:
            信息需求检测结果
        """
        try:
            self.logger.info(f"开始检测任务 {task_id} 的信息需求")
            
            # 获取任务信息
            task = await self.task_history_manager.get_task(task_id)
            if not task:
                raise InfoRequirementError(f"任务 {task_id} 不存在")
            
            # 1. 检测信息缺失
            missing_info = await self._detect_missing_info(task, sub_task_results)
            
            # 2. 评估信息质量
            quality_assessment = await self._assess_info_quality(task, sub_task_results)
            
            # 3. 生成信息需求
            info_requirements = await self._generate_info_requirements(
                task, sub_task_results, missing_info, quality_assessment
            )
            
            # 4. 构建检测结果
            detection_result = {
                "task_id": task_id,
                "missing_info": missing_info,
                "quality_assessment": quality_assessment,
                "info_requirements": info_requirements,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # 5. 保存检测结果
            await self.task_history_manager.create_info_requirement_detection(
                task_id=task_id,
                missing_info=missing_info,
                quality_assessment=quality_assessment,
                info_requirements=info_requirements
            )
            
            self.logger.info(f"任务 {task_id} 的信息需求检测完成")
            return detection_result
        except Exception as e:
            raise InfoRequirementError(f"检测信息需求失败: {str(e)}")
    
    async def _detect_missing_info(self, task: Dict, sub_task_results: List[Dict]) -> List[Dict]:
        """
        检测信息缺失
        
        Args:
            task: 任务信息
            sub_task_results: 子任务结果列表
            
        Returns:
            信息缺失列表
        """
        try:
            missing_info = []
            
            # 分析任务描述
            task_description = task.get("description", "")
            
            # 分析子任务结果
            for result in sub_task_results:
                sub_task_id = result.get("sub_task_id", "")
                result_content = result.get("result", {})
                
                # 分析结果文本
                result_text = self._extract_result_text(result_content)
                
                # 检查信息缺失模式
                for pattern_info in self.info_requirement_patterns:
                    pattern = pattern_info["pattern"]
                    info_type = pattern_info["type"]
                    priority = pattern_info["priority"]
                    
                    # 在结果文本中搜索模式
                    matches = re.finditer(pattern, result_text, re.IGNORECASE)
                    
                    for match in matches:
                        missing_info.append({
                            "sub_task_id": sub_task_id,
                            "type": info_type,
                            "priority": priority,
                            "description": match.group(0),
                            "context": self._get_context(result_text, match.start(), match.end())
                        })
            
            return missing_info
        except Exception as e:
            raise InfoRequirementError(f"检测信息缺失失败: {str(e)}")
    
    def _extract_result_text(self, result_content: Dict) -> str:
        """
        提取结果文本
        
        Args:
            result_content: 结果内容
            
        Returns:
            结果文本
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
            
            extract_text(result_content)
            return " ".join(text_parts)
        except Exception as e:
            self.logger.error(f"提取结果文本失败: {str(e)}")
            return ""
    
    def _get_context(self, text: str, start: int, end: int, context_size: int = 50) -> str:
        """
        获取上下文
        
        Args:
            text: 文本
            start: 开始位置
            end: 结束位置
            context_size: 上下文大小
            
        Returns:
            上下文文本
        """
        try:
            # 计算上下文范围
            context_start = max(0, start - context_size)
            context_end = min(len(text), end + context_size)
            
            # 提取上下文
            context = text[context_start:context_end]
            
            # 标记匹配部分
            match_start = start - context_start
            match_end = end - context_start
            marked_context = (
                context[:match_start] +
                "[" +
                context[match_start:match_end] +
                "]" +
                context[match_end:]
            )
            
            return marked_context
        except Exception as e:
            self.logger.error(f"获取上下文失败: {str(e)}")
            return text[start:end]
    
    async def _assess_info_quality(self, task: Dict, sub_task_results: List[Dict]) -> Dict:
        """
        评估信息质量
        
        Args:
            task: 任务信息
            sub_task_results: 子任务结果列表
            
        Returns:
            信息质量评估结果
        """
        try:
            quality_scores = {}
            
            # 获取任务关键词
            task_keywords = await self._extract_task_keywords(task.get("description", ""))
            
            # 评估每个子任务结果的信息质量
            for result in sub_task_results:
                sub_task_id = result.get("sub_task_id", "")
                result_content = result.get("result", {})
                
                # 提取结果文本
                result_text = self._extract_result_text(result_content)
                
                # 评估各个质量指标
                metric_scores = {}
                
                for metric_name, metric_info in self.quality_metrics.items():
                    score = await self._assess_quality_metric(
                        metric_name, result_text, task_keywords
                    )
                    metric_scores[metric_name] = {
                        "score": score,
                        "description": metric_info["description"],
                        "weight": metric_info["weight"]
                    }
                
                # 计算加权总分
                total_score = sum(
                    metric_data["score"] * metric_data["weight"]
                    for metric_data in metric_scores.values()
                )
                
                quality_scores[sub_task_id] = {
                    "total_score": total_score,
                    "metrics": metric_scores
                }
            
            return quality_scores
        except Exception as e:
            raise InfoRequirementError(f"评估信息质量失败: {str(e)}")
    
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
            self.logger.error(f"提取任务关键词失败: {str(e)}")
            return []
    
    async def _assess_quality_metric(self, metric_name: str, text: str, keywords: List[str]) -> float:
        """
        评估质量指标
        
        Args:
            metric_name: 指标名称
            text: 文本
            keywords: 关键词列表
            
        Returns:
            质量分数 (0-1)
        """
        try:
            if metric_name == "completeness":
                # 评估信息完整性
                # 检查是否包含足够的信息
                if len(text) < 50:
                    return 0.3
                elif len(text) < 200:
                    return 0.6
                else:
                    return 0.9
            
            elif metric_name == "accuracy":
                # 评估信息准确性
                # 简化评估：检查是否有明显的错误标记
                error_indicators = ["错误", "失败", "异常", "问题", "不正确"]
                for indicator in error_indicators:
                    if indicator in text:
                        return 0.3
                return 0.8
            
            elif metric_name == "relevance":
                # 评估信息相关性
                # 检查是否包含任务关键词
                if not keywords:
                    return 0.5
                
                matched_keywords = sum(1 for keyword in keywords if keyword in text)
                relevance = matched_keywords / len(keywords)
                return min(1.0, relevance + 0.3)  # 基础分数0.3
            
            elif metric_name == "clarity":
                # 评估信息清晰度
                # 检查文本结构
                sentences = text.split("。")
                if len(sentences) < 2:
                    return 0.4
                
                # 检查是否有结构标记
                structure_indicators = ["首先", "其次", "然后", "最后", "总结", "总之"]
                for indicator in structure_indicators:
                    if indicator in text:
                        return 0.8
                
                return 0.6
            
            elif metric_name == "timeliness":
                # 评估信息时效性
                # 简化评估：检查是否有时间标记
                time_indicators = ["最近", "目前", "当前", "现在", "今天", "昨天"]
                for indicator in time_indicators:
                    if indicator in text:
                        return 0.8
                
                return 0.5
            
            else:
                return 0.5
        except Exception as e:
            self.logger.error(f"评估质量指标失败: {str(e)}")
            return 0.5
    
    async def _generate_info_requirements(self, task: Dict, sub_task_results: List[Dict],
                                        missing_info: List[Dict], quality_assessment: Dict) -> List[Dict]:
        """
        生成信息需求
        
        Args:
            task: 任务信息
            sub_task_results: 子任务结果列表
            missing_info: 信息缺失列表
            quality_assessment: 信息质量评估结果
            
        Returns:
            信息需求列表
        """
        try:
            info_requirements = []
            
            # 基于信息缺失生成需求
            for missing in missing_info:
                sub_task_id = missing["sub_task_id"]
                info_type = missing["type"]
                priority = missing["priority"]
                description = missing["description"]
                context = missing["context"]
                
                # 生成需求描述
                requirement_description = f"需要提供{description}相关的信息"
                
                # 生成需求问题
                requirement_question = self._generate_requirement_question(info_type, context)
                
                info_requirements.append({
                    "sub_task_id": sub_task_id,
                    "type": "missing_info",
                    "priority": priority,
                    "description": requirement_description,
                    "question": requirement_question,
                    "source": "missing_info_detection"
                })
            
            # 基于信息质量评估生成需求
            for sub_task_id, assessment in quality_assessment.items():
                total_score = assessment["total_score"]
                metrics = assessment["metrics"]
                
                # 如果总分低于阈值，生成需求
                if total_score < 0.7:
                    # 找出分数最低的指标
                    lowest_metric = min(
                        metrics.items(),
                        key=lambda x: x[1]["score"]
                    )
                    
                    metric_name = lowest_metric[0]
                    metric_score = lowest_metric[1]["score"]
                    metric_description = lowest_metric[1]["description"]
                    
                    # 生成需求描述
                    requirement_description = f"需要提高{metric_description}，当前分数为{metric_score:.2f}"
                    
                    # 生成需求问题
                    requirement_question = self._generate_quality_question(metric_name, metric_score)
                    
                    # 确定优先级
                    priority = "high" if metric_score < 0.5 else "medium"
                    
                    info_requirements.append({
                        "sub_task_id": sub_task_id,
                        "type": "quality_improvement",
                        "priority": priority,
                        "description": requirement_description,
                        "question": requirement_question,
                        "source": "quality_assessment"
                    })
            
            # 去重和排序
            info_requirements = self._deduplicate_and_sort_requirements(info_requirements)
            
            return info_requirements
        except Exception as e:
            raise InfoRequirementError(f"生成信息需求失败: {str(e)}")
    
    def _generate_requirement_question(self, info_type: str, context: str) -> str:
        """
        生成需求问题
        
        Args:
            info_type: 信息类型
            context: 上下文
            
        Returns:
            需求问题
        """
        try:
            # 根据信息类型生成问题
            if info_type == "missing_specific_info":
                return "请提供更具体的信息，以便更好地完成任务。"
            elif info_type == "missing_context_info":
                return "请提供更多的背景信息或上下文，以便更好地理解任务。"
            elif info_type == "missing_user_preference":
                return "请提供用户偏好或需求，以便更好地满足用户期望。"
            elif info_type == "missing_technical_detail":
                return "请提供更多的技术细节或实现方案，以便更好地执行任务。"
            elif info_type == "missing_constraint":
                return "请提供相关的约束条件或要求，以便更好地限制任务范围。"
            elif info_type == "missing_example":
                return "请提供相关的示例或参考，以便更好地理解期望结果。"
            else:
                return "请提供更多的信息，以便更好地完成任务。"
        except Exception as e:
            self.logger.error(f"生成需求问题失败: {str(e)}")
            return "请提供更多的信息，以便更好地完成任务。"
    
    def _generate_quality_question(self, metric_name: str, metric_score: float) -> str:
        """
        生成质量问题
        
        Args:
            metric_name: 指标名称
            metric_score: 指标分数
            
        Returns:
            质量问题
        """
        try:
            # 根据指标名称生成问题
            if metric_name == "completeness":
                return "信息是否完整？是否有遗漏的重要内容？"
            elif metric_name == "accuracy":
                return "信息是否准确？是否有错误或不准确的内容？"
            elif metric_name == "relevance":
                return "信息是否与任务相关？是否有不相关的内容？"
            elif metric_name == "clarity":
                return "信息是否清晰？是否有模糊或难以理解的内容？"
            elif metric_name == "timeliness":
                return "信息是否及时？是否有过时或不再适用的内容？"
            else:
                return "信息质量是否满足要求？"
        except Exception as e:
            self.logger.error(f"生成质量问题失败: {str(e)}")
            return "信息质量是否满足要求？"
    
    def _deduplicate_and_sort_requirements(self, requirements: List[Dict]) -> List[Dict]:
        """
        去重和排序需求
        
        Args:
            requirements: 需求列表
            
        Returns:
            去重和排序后的需求列表
        """
        try:
            # 去重
            unique_requirements = []
            seen_descriptions = set()
            
            for req in requirements:
                description = req["description"]
                if description not in seen_descriptions:
                    seen_descriptions.add(description)
                    unique_requirements.append(req)
            
            # 排序
            priority_order = {"high": 0, "medium": 1, "low": 2}
            
            sorted_requirements = sorted(
                unique_requirements,
                key=lambda x: priority_order.get(x["priority"], 3)
            )
            
            return sorted_requirements
        except Exception as e:
            self.logger.error(f"去重和排序需求失败: {str(e)}")
            return requirements
    
    async def get_info_requirement_detection(self, task_id: int) -> Dict:
        """
        获取信息需求检测结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            信息需求检测结果
        """
        try:
            detection_result = await self.task_history_manager.get_info_requirement_detection(task_id)
            return detection_result
        except Exception as e:
            raise InfoRequirementError(f"获取信息需求检测结果失败: {str(e)}")
    
    async def add_info_requirement_pattern(self, pattern: str, info_type: str, priority: str = "medium") -> bool:
        """
        添加信息需求模式
        
        Args:
            pattern: 模式正则表达式
            info_type: 信息类型
            priority: 优先级
            
        Returns:
            添加是否成功
        """
        try:
            self.info_requirement_patterns.append({
                "pattern": pattern,
                "type": info_type,
                "priority": priority
            })
            
            self.logger.info(f"添加信息需求模式: {pattern} -> {info_type}")
            return True
        except Exception as e:
            raise InfoRequirementError(f"添加信息需求模式失败: {str(e)}")
    
    async def add_quality_metric(self, name: str, description: str, weight: float) -> bool:
        """
        添加质量指标
        
        Args:
            name: 指标名称
            description: 指标描述
            weight: 权重
            
        Returns:
            添加是否成功
        """
        try:
            self.quality_metrics[name] = {
                "description": description,
                "weight": weight
            }
            
            self.logger.info(f"添加质量指标: {name} (权重: {weight})")
            return True
        except Exception as e:
            raise InfoRequirementError(f"添加质量指标失败: {str(e)}")
    
    async def get_info_requirement_stats(self, days: int = 30) -> Dict:
        """
        获取信息需求统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        try:
            # 获取信息需求检测统计
            stats = await self.task_history_manager.get_info_requirement_statistics(days)
            
            return stats
        except Exception as e:
            raise InfoRequirementError(f"获取信息需求统计信息失败: {str(e)}")