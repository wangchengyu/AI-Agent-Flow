"""
任务分解器

负责将复杂任务分解为可执行的子任务，
并管理子任务的依赖关系和执行顺序。
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union, Tuple

from ..database.task_history_manager import TaskHistoryManager
from ..rag.knowledge_manager import KnowledgeManager
from ..utils.exceptions import TaskDecomposerError


class TaskDecomposer:
    """任务分解器，负责将复杂任务分解为可执行的子任务"""
    
    def __init__(self, db_manager, knowledge_manager: KnowledgeManager):
        """
        初始化任务分解器
        
        Args:
            db_manager: 数据库管理器
            knowledge_manager: 知识管理器
        """
        self.db_manager = db_manager
        self.knowledge_manager = knowledge_manager
        self.task_history_manager = TaskHistoryManager(db_manager)
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """初始化任务分解器"""
        try:
            self.logger.info("任务分解器初始化完成")
        except Exception as e:
            raise TaskDecomposerError(f"初始化任务分解器失败: {str(e)}")
    
    async def decompose_task(self, task_id: int, task_description: str, 
                           context: Dict) -> List[Dict]:
        """
        分解任务
        
        Args:
            task_id: 任务ID
            task_description: 任务描述
            context: 任务上下文
            
        Returns:
            子任务列表
        """
        try:
            self.logger.info(f"开始分解任务 {task_id}: {task_description}")
            
            # 1. 分析任务类型和复杂度
            task_analysis = await self._analyze_task(task_description, context)
            
            # 2. 检索相关知识
            relevant_knowledge = await self._retrieve_relevant_knowledge(task_analysis)
            
            # 3. 生成子任务
            sub_tasks = await self._generate_sub_tasks(task_id, task_analysis, relevant_knowledge)
            
            # 4. 确定子任务依赖关系
            sub_tasks = await self._determine_dependencies(sub_tasks)
            
            # 5. 优化子任务执行顺序
            sub_tasks = await self._optimize_execution_order(sub_tasks)
            
            # 6. 保存子任务到数据库
            await self._save_sub_tasks(task_id, sub_tasks)
            
            self.logger.info(f"任务 {task_id} 分解完成，生成 {len(sub_tasks)} 个子任务")
            return sub_tasks
        except Exception as e:
            raise TaskDecomposerError(f"分解任务失败: {str(e)}")
    
    async def _analyze_task(self, task_description: str, context: Dict) -> Dict:
        """
        分析任务
        
        Args:
            task_description: 任务描述
            context: 任务上下文
            
        Returns:
            任务分析结果
        """
        try:
            # 分析任务类型
            task_type = await self._identify_task_type(task_description)
            
            # 分析任务复杂度
            complexity = await self._assess_complexity(task_description, context)
            
            # 提取关键信息
            key_info = await self._extract_key_information(task_description, context)
            
            # 识别所需工具
            required_tools = await self._identify_required_tools(task_description, context)
            
            return {
                "description": task_description,
                "type": task_type,
                "complexity": complexity,
                "key_info": key_info,
                "required_tools": required_tools,
                "context": context
            }
        except Exception as e:
            raise TaskDecomposerError(f"分析任务失败: {str(e)}")
    
    async def _identify_task_type(self, task_description: str) -> str:
        """
        识别任务类型
        
        Args:
            task_description: 任务描述
            
        Returns:
            任务类型
        """
        try:
            # 简化的任务类型识别逻辑
            task_description_lower = task_description.lower()
            
            if any(keyword in task_description_lower for keyword in ["生成", "创建", "编写"]):
                return "generation"
            elif any(keyword in task_description_lower for keyword in ["分析", "检查", "评估"]):
                return "analysis"
            elif any(keyword in task_description_lower for keyword in ["修改", "更新", "调整"]):
                return "modification"
            elif any(keyword in task_description_lower for keyword in ["搜索", "查找", "检索"]):
                return "search"
            elif any(keyword in task_description_lower for keyword in ["转换", "格式化", "处理"]):
                return "transformation"
            else:
                return "general"
        except Exception as e:
            raise TaskDecomposerError(f"识别任务类型失败: {str(e)}")
    
    async def _assess_complexity(self, task_description: str, context: Dict) -> str:
        """
        评估任务复杂度
        
        Args:
            task_description: 任务描述
            context: 任务上下文
            
        Returns:
            任务复杂度（low, medium, high）
        """
        try:
            # 简化的复杂度评估逻辑
            complexity_score = 0
            
            # 基于任务长度
            if len(task_description) > 200:
                complexity_score += 1
            
            # 基于上下文复杂度
            if len(context) > 5:
                complexity_score += 1
            
            # 基于关键词
            complex_keywords = ["多步骤", "多个", "复杂", "详细", "全面"]
            for keyword in complex_keywords:
                if keyword in task_description.lower():
                    complexity_score += 1
            
            # 确定复杂度级别
            if complexity_score <= 1:
                return "low"
            elif complexity_score == 2:
                return "medium"
            else:
                return "high"
        except Exception as e:
            raise TaskDecomposerError(f"评估任务复杂度失败: {str(e)}")
    
    async def _extract_key_information(self, task_description: str, context: Dict) -> Dict:
        """
        提取关键信息
        
        Args:
            task_description: 任务描述
            context: 任务上下文
            
        Returns:
            关键信息字典
        """
        try:
            # 简化的关键信息提取逻辑
            key_info = {
                "entities": [],
                "actions": [],
                "objects": [],
                "constraints": []
            }
            
            # 提取实体（简化处理）
            import re
            entity_pattern = r"([A-Z][a-z]+|[a-z]+(?:_[a-z]+)*)"
            entities = re.findall(entity_pattern, task_description)
            key_info["entities"] = list(set(entities))
            
            # 提取动作（简化处理）
            action_keywords = ["创建", "生成", "分析", "修改", "搜索", "转换", "处理", "检查", "评估"]
            for keyword in action_keywords:
                if keyword in task_description:
                    key_info["actions"].append(keyword)
            
            # 提取对象（简化处理）
            object_keywords = ["文件", "代码", "数据", "报告", "图表", "文档", "数据库", "表"]
            for keyword in object_keywords:
                if keyword in task_description:
                    key_info["objects"].append(keyword)
            
            # 提取约束（简化处理）
            constraint_keywords = ["必须", "需要", "应该", "要求", "限制", "条件"]
            for keyword in constraint_keywords:
                if keyword in task_description:
                    key_info["constraints"].append(keyword)
            
            return key_info
        except Exception as e:
            raise TaskDecomposerError(f"提取关键信息失败: {str(e)}")
    
    async def _identify_required_tools(self, task_description: str, context: Dict) -> List[str]:
        """
        识别所需工具
        
        Args:
            task_description: 任务描述
            context: 任务上下文
            
        Returns:
            所需工具列表
        """
        try:
            # 简化的工具识别逻辑
            required_tools = []
            
            # 基于任务描述识别工具
            if any(keyword in task_description.lower() for keyword in ["文件", "目录", "路径"]):
                required_tools.append("file_operations")
            
            if any(keyword in task_description.lower() for keyword in ["代码", "类", "函数", "方法"]):
                required_tools.append("code_generator")
            
            if any(keyword in task_description.lower() for keyword in ["uml", "图", "图表", "类图", "序列图"]):
                required_tools.append("uml_generator")
            
            if any(keyword in task_description.lower() for keyword in ["数据库", "表", "查询", "sql"]):
                required_tools.append("database_operations")
            
            # 基于上下文识别工具
            if "tools" in context:
                for tool in context["tools"]:
                    if tool not in required_tools:
                        required_tools.append(tool)
            
            return required_tools
        except Exception as e:
            raise TaskDecomposerError(f"识别所需工具失败: {str(e)}")
    
    async def _retrieve_relevant_knowledge(self, task_analysis: Dict) -> List[Dict]:
        """
        检索相关知识
        
        Args:
            task_analysis: 任务分析结果
            
        Returns:
            相关知识列表
        """
        try:
            # 构建查询
            query_terms = []
            
            # 添加任务类型
            query_terms.append(task_analysis["type"])
            
            # 添加关键信息
            for category in ["entities", "actions", "objects"]:
                for item in task_analysis["key_info"][category]:
                    query_terms.append(item)
            
            # 构建查询字符串
            query = " ".join(query_terms)
            
            # 检索相关知识
            relevant_knowledge = await self.knowledge_manager.search_knowledge(
                query=query,
                limit=10
            )
            
            return relevant_knowledge
        except Exception as e:
            raise TaskDecomposerError(f"检索相关知识失败: {str(e)}")
    
    async def _generate_sub_tasks(self, task_id: int, task_analysis: Dict, 
                                relevant_knowledge: List[Dict]) -> List[Dict]:
        """
        生成子任务
        
        Args:
            task_id: 任务ID
            task_analysis: 任务分析结果
            relevant_knowledge: 相关知识
            
        Returns:
            子任务列表
        """
        try:
            sub_tasks = []
            
            # 基于任务类型生成子任务
            task_type = task_analysis["type"]
            complexity = task_analysis["complexity"]
            
            if task_type == "generation":
                sub_tasks = await self._generate_generation_sub_tasks(task_analysis, relevant_knowledge)
            elif task_type == "analysis":
                sub_tasks = await self._generate_analysis_sub_tasks(task_analysis, relevant_knowledge)
            elif task_type == "modification":
                sub_tasks = await self._generate_modification_sub_tasks(task_analysis, relevant_knowledge)
            elif task_type == "search":
                sub_tasks = await self._generate_search_sub_tasks(task_analysis, relevant_knowledge)
            elif task_type == "transformation":
                sub_tasks = await self._generate_transformation_sub_tasks(task_analysis, relevant_knowledge)
            else:
                sub_tasks = await self._generate_general_sub_tasks(task_analysis, relevant_knowledge)
            
            # 根据复杂度调整子任务
            if complexity == "low" and len(sub_tasks) > 3:
                # 合并一些子任务
                sub_tasks = await self._merge_sub_tasks(sub_tasks, target_count=3)
            elif complexity == "high" and len(sub_tasks) < 5:
                # 拆分一些子任务
                sub_tasks = await self._split_sub_tasks(sub_tasks, target_count=5)
            
            # 为每个子任务添加基本信息
            for i, sub_task in enumerate(sub_tasks):
                sub_task["id"] = f"{task_id}_{i+1}"
                sub_task["task_id"] = task_id
                sub_task["status"] = "pending"
                sub_task["order"] = i + 1
                sub_task["created_at"] = time.time()
            
            return sub_tasks
        except Exception as e:
            raise TaskDecomposerError(f"生成子任务失败: {str(e)}")
    
    async def _generate_generation_sub_tasks(self, task_analysis: Dict, 
                                           relevant_knowledge: List[Dict]) -> List[Dict]:
        """
        生成生成类任务的子任务
        
        Args:
            task_analysis: 任务分析结果
            relevant_knowledge: 相关知识
            
        Returns:
            子任务列表
        """
        try:
            sub_tasks = []
            
            # 子任务1: 分析需求
            sub_tasks.append({
                "name": "分析需求",
                "description": "分析生成任务的具体需求和约束条件",
                "type": "analysis",
                "required_tools": []
            })
            
            # 子任务2: 准备资源
            sub_tasks.append({
                "name": "准备资源",
                "description": "收集和准备生成所需的资源和参考材料",
                "type": "preparation",
                "required_tools": ["file_operations"]
            })
            
            # 子任务3: 生成内容
            sub_tasks.append({
                "name": "生成内容",
                "description": "根据需求和资源生成目标内容",
                "type": "generation",
                "required_tools": task_analysis["required_tools"]
            })
            
            # 子任务4: 验证结果
            sub_tasks.append({
                "name": "验证结果",
                "description": "验证生成的内容是否符合需求和预期",
                "type": "validation",
                "required_tools": []
            })
            
            return sub_tasks
        except Exception as e:
            raise TaskDecomposerError(f"生成生成类子任务失败: {str(e)}")
    
    async def _generate_analysis_sub_tasks(self, task_analysis: Dict, 
                                         relevant_knowledge: List[Dict]) -> List[Dict]:
        """
        生成分析类任务的子任务
        
        Args:
            task_analysis: 任务分析结果
            relevant_knowledge: 相关知识
            
        Returns:
            子任务列表
        """
        try:
            sub_tasks = []
            
            # 子任务1: 收集数据
            sub_tasks.append({
                "name": "收集数据",
                "description": "收集分析所需的数据和信息",
                "type": "collection",
                "required_tools": ["file_operations", "database_operations"]
            })
            
            # 子任务2: 预处理数据
            sub_tasks.append({
                "name": "预处理数据",
                "description": "对收集的数据进行清洗和预处理",
                "type": "preprocessing",
                "required_tools": ["file_operations"]
            })
            
            # 子任务3: 执行分析
            sub_tasks.append({
                "name": "执行分析",
                "description": "对预处理后的数据执行分析操作",
                "type": "analysis",
                "required_tools": task_analysis["required_tools"]
            })
            
            # 子任务4: 生成报告
            sub_tasks.append({
                "name": "生成报告",
                "description": "根据分析结果生成分析报告",
                "type": "generation",
                "required_tools": ["file_operations"]
            })
            
            return sub_tasks
        except Exception as e:
            raise TaskDecomposerError(f"生成分析类子任务失败: {str(e)}")
    
    async def _generate_modification_sub_tasks(self, task_analysis: Dict, 
                                            relevant_knowledge: List[Dict]) -> List[Dict]:
        """
        生成修改类任务的子任务
        
        Args:
            task_analysis: 任务分析结果
            relevant_knowledge: 相关知识
            
        Returns:
            子任务列表
        """
        try:
            sub_tasks = []
            
            # 子任务1: 理解现有内容
            sub_tasks.append({
                "name": "理解现有内容",
                "description": "分析和理解需要修改的现有内容",
                "type": "analysis",
                "required_tools": ["file_operations", "code_generator"]
            })
            
            # 子任务2: 确定修改方案
            sub_tasks.append({
                "name": "确定修改方案",
                "description": "根据需求确定具体的修改方案",
                "type": "planning",
                "required_tools": []
            })
            
            # 子任务3: 执行修改
            sub_tasks.append({
                "name": "执行修改",
                "description": "按照修改方案执行具体的修改操作",
                "type": "modification",
                "required_tools": task_analysis["required_tools"]
            })
            
            # 子任务4: 验证修改
            sub_tasks.append({
                "name": "验证修改",
                "description": "验证修改后的内容是否符合预期",
                "type": "validation",
                "required_tools": []
            })
            
            return sub_tasks
        except Exception as e:
            raise TaskDecomposerError(f"生成修改类子任务失败: {str(e)}")
    
    async def _generate_search_sub_tasks(self, task_analysis: Dict, 
                                       relevant_knowledge: List[Dict]) -> List[Dict]:
        """
        生成搜索类任务的子任务
        
        Args:
            task_analysis: 任务分析结果
            relevant_knowledge: 相关知识
            
        Returns:
            子任务列表
        """
        try:
            sub_tasks = []
            
            # 子任务1: 明确搜索目标
            sub_tasks.append({
                "name": "明确搜索目标",
                "description": "明确搜索的具体目标和范围",
                "type": "planning",
                "required_tools": []
            })
            
            # 子任务2: 选择搜索策略
            sub_tasks.append({
                "name": "选择搜索策略",
                "description": "根据搜索目标选择合适的搜索策略",
                "type": "planning",
                "required_tools": []
            })
            
            # 子任务3: 执行搜索
            sub_tasks.append({
                "name": "执行搜索",
                "description": "按照选择的策略执行搜索操作",
                "type": "search",
                "required_tools": task_analysis["required_tools"]
            })
            
            # 子任务4: 整理搜索结果
            sub_tasks.append({
                "name": "整理搜索结果",
                "description": "对搜索结果进行整理和分类",
                "type": "organization",
                "required_tools": ["file_operations"]
            })
            
            return sub_tasks
        except Exception as e:
            raise TaskDecomposerError(f"生成搜索类子任务失败: {str(e)}")
    
    async def _generate_transformation_sub_tasks(self, task_analysis: Dict, 
                                               relevant_knowledge: List[Dict]) -> List[Dict]:
        """
        生成转换类任务的子任务
        
        Args:
            task_analysis: 任务分析结果
            relevant_knowledge: 相关知识
            
        Returns:
            子任务列表
        """
        try:
            sub_tasks = []
            
            # 子任务1: 分析源数据
            sub_tasks.append({
                "name": "分析源数据",
                "description": "分析需要转换的源数据的结构和内容",
                "type": "analysis",
                "required_tools": ["file_operations", "database_operations"]
            })
            
            # 子任务2: 设计转换方案
            sub_tasks.append({
                "name": "设计转换方案",
                "description": "根据转换需求设计具体的转换方案",
                "type": "planning",
                "required_tools": []
            })
            
            # 子任务3: 执行转换
            sub_tasks.append({
                "name": "执行转换",
                "description": "按照转换方案执行数据转换操作",
                "type": "transformation",
                "required_tools": task_analysis["required_tools"]
            })
            
            # 子任务4: 验证转换结果
            sub_tasks.append({
                "name": "验证转换结果",
                "description": "验证转换后的数据是否符合预期",
                "type": "validation",
                "required_tools": []
            })
            
            return sub_tasks
        except Exception as e:
            raise TaskDecomposerError(f"生成转换类子任务失败: {str(e)}")
    
    async def _generate_general_sub_tasks(self, task_analysis: Dict, 
                                       relevant_knowledge: List[Dict]) -> List[Dict]:
        """
        生成通用类任务的子任务
        
        Args:
            task_analysis: 任务分析结果
            relevant_knowledge: 相关知识
            
        Returns:
            子任务列表
        """
        try:
            sub_tasks = []
            
            # 子任务1: 理解任务
            sub_tasks.append({
                "name": "理解任务",
                "description": "深入理解任务的需求和目标",
                "type": "analysis",
                "required_tools": []
            })
            
            # 子任务2: 制定计划
            sub_tasks.append({
                "name": "制定计划",
                "description": "根据任务需求制定详细的执行计划",
                "type": "planning",
                "required_tools": []
            })
            
            # 子任务3: 执行任务
            sub_tasks.append({
                "name": "执行任务",
                "description": "按照计划执行任务的具体操作",
                "type": "execution",
                "required_tools": task_analysis["required_tools"]
            })
            
            # 子任务4: 检查结果
            sub_tasks.append({
                "name": "检查结果",
                "description": "检查任务执行的结果是否符合预期",
                "type": "validation",
                "required_tools": []
            })
            
            return sub_tasks
        except Exception as e:
            raise TaskDecomposerError(f"生成通用类子任务失败: {str(e)}")
    
    async def _merge_sub_tasks(self, sub_tasks: List[Dict], target_count: int) -> List[Dict]:
        """
        合并子任务
        
        Args:
            sub_tasks: 子任务列表
            target_count: 目标子任务数量
            
        Returns:
            合并后的子任务列表
        """
        try:
            if len(sub_tasks) <= target_count:
                return sub_tasks
            
            # 简化的合并逻辑
            merged_sub_tasks = []
            merge_ratio = len(sub_tasks) / target_count
            
            for i in range(target_count):
                start_idx = int(i * merge_ratio)
                end_idx = int((i + 1) * merge_ratio)
                
                if end_idx > len(sub_tasks):
                    end_idx = len(sub_tasks)
                
                # 合并子任务
                merged_sub_task = {
                    "name": f"合并任务 {i+1}",
                    "description": "合并多个子任务",
                    "type": "merged",
                    "required_tools": []
                }
                
                # 收集所有工具
                all_tools = set()
                for j in range(start_idx, end_idx):
                    for tool in sub_tasks[j]["required_tools"]:
                        all_tools.add(tool)
                
                merged_sub_task["required_tools"] = list(all_tools)
                
                # 添加原始子任务信息
                merged_sub_task["original_sub_tasks"] = sub_tasks[start_idx:end_idx]
                
                merged_sub_tasks.append(merged_sub_task)
            
            return merged_sub_tasks
        except Exception as e:
            raise TaskDecomposerError(f"合并子任务失败: {str(e)}")
    
    async def _split_sub_tasks(self, sub_tasks: List[Dict], target_count: int) -> List[Dict]:
        """
        拆分子任务
        
        Args:
            sub_tasks: 子任务列表
            target_count: 目标子任务数量
            
        Returns:
            拆分后的子任务列表
        """
        try:
            if len(sub_tasks) >= target_count:
                return sub_tasks
            
            # 简化的拆分逻辑
            split_sub_tasks = []
            
            for sub_task in sub_tasks:
                # 根据子任务类型决定是否拆分
                if sub_task["type"] in ["generation", "analysis", "modification", "execution"]:
                    # 拆分子任务
                    split_count = max(2, target_count // len(sub_tasks))
                    
                    for i in range(split_count):
                        split_sub_task = {
                            "name": f"{sub_task['name']} - 部分 {i+1}",
                            "description": f"{sub_task['description']} - 部分 {i+1}",
                            "type": sub_task["type"],
                            "required_tools": sub_task["required_tools"],
                            "parent_sub_task": sub_task
                        }
                        
                        split_sub_tasks.append(split_sub_task)
                else:
                    # 不拆分
                    split_sub_tasks.append(sub_task)
            
            # 如果仍然不足目标数量，添加一些通用子任务
            while len(split_sub_tasks) < target_count:
                split_sub_tasks.append({
                    "name": f"额外任务 {len(split_sub_tasks) + 1}",
                    "description": "额外的辅助任务",
                    "type": "auxiliary",
                    "required_tools": []
                })
            
            return split_sub_tasks
        except Exception as e:
            raise TaskDecomposerError(f"拆分子任务失败: {str(e)}")
    
    async def _determine_dependencies(self, sub_tasks: List[Dict]) -> List[Dict]:
        """
        确定子任务依赖关系
        
        Args:
            sub_tasks: 子任务列表
            
        Returns:
            更新后的子任务列表
        """
        try:
            # 简化的依赖关系确定逻辑
            for i, sub_task in enumerate(sub_tasks):
                dependencies = []
                
                # 根据子任务类型确定依赖
                if sub_task["type"] == "analysis":
                    # 分析任务通常依赖于数据收集任务
                    for j, prev_task in enumerate(sub_tasks[:i]):
                        if prev_task["type"] in ["collection", "preparation"]:
                            dependencies.append(prev_task["id"])
                
                elif sub_task["type"] == "generation":
                    # 生成任务通常依赖于分析和准备任务
                    for j, prev_task in enumerate(sub_tasks[:i]):
                        if prev_task["type"] in ["analysis", "preparation", "planning"]:
                            dependencies.append(prev_task["id"])
                
                elif sub_task["type"] == "modification":
                    # 修改任务通常依赖于分析任务
                    for j, prev_task in enumerate(sub_tasks[:i]):
                        if prev_task["type"] in ["analysis", "planning"]:
                            dependencies.append(prev_task["id"])
                
                elif sub_task["type"] == "validation":
                    # 验证任务通常依赖于执行任务
                    for j, prev_task in enumerate(sub_tasks[:i]):
                        if prev_task["type"] in ["execution", "generation", "modification", "transformation"]:
                            dependencies.append(prev_task["id"])
                
                # 添加依赖关系
                sub_task["dependencies"] = dependencies
            
            return sub_tasks
        except Exception as e:
            raise TaskDecomposerError(f"确定子任务依赖关系失败: {str(e)}")
    
    async def _optimize_execution_order(self, sub_tasks: List[Dict]) -> List[Dict]:
        """
        优化子任务执行顺序
        
        Args:
            sub_tasks: 子任务列表
            
        Returns:
            优化后的子任务列表
        """
        try:
            # 简化的执行顺序优化逻辑
            # 使用拓扑排序算法确定执行顺序
            
            # 构建依赖图
            graph = {}
            in_degree = {}
            
            for sub_task in sub_tasks:
                task_id = sub_task["id"]
                dependencies = sub_task.get("dependencies", [])
                
                graph[task_id] = dependencies
                in_degree[task_id] = len(dependencies)
            
            # 拓扑排序
            queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
            sorted_tasks = []
            
            while queue:
                # 按原始顺序排序
                queue.sort(key=lambda x: int(x.split("_")[-1]))
                
                task_id = queue.pop(0)
                sorted_tasks.append(task_id)
                
                # 更新依赖
                for dependent_id, dependencies in graph.items():
                    if task_id in dependencies:
                        in_degree[dependent_id] -= 1
                        if in_degree[dependent_id] == 0:
                            queue.append(dependent_id)
            
            # 检查是否有环
            if len(sorted_tasks) != len(sub_tasks):
                self.logger.warning("检测到子任务依赖关系中的环，使用原始顺序")
                return sub_tasks
            
            # 重新排序子任务
            task_map = {task["id"]: task for task in sub_tasks}
            ordered_sub_tasks = [task_map[task_id] for task_id in sorted_tasks]
            
            # 更新顺序
            for i, sub_task in enumerate(ordered_sub_tasks):
                sub_task["order"] = i + 1
            
            return ordered_sub_tasks
        except Exception as e:
            raise TaskDecomposerError(f"优化子任务执行顺序失败: {str(e)}")
    
    async def _save_sub_tasks(self, task_id: int, sub_tasks: List[Dict]):
        """
        保存子任务到数据库
        
        Args:
            task_id: 任务ID
            sub_tasks: 子任务列表
        """
        try:
            # 保存子任务
            for sub_task in sub_tasks:
                await self.task_history_manager.create_sub_task(
                    task_id=task_id,
                    name=sub_task["name"],
                    description=sub_task["description"],
                    order=sub_task["order"],
                    dependencies=sub_task.get("dependencies", []),
                    required_tools=sub_task.get("required_tools", []),
                    metadata={
                        "type": sub_task.get("type", "general"),
                        "original_sub_tasks": sub_task.get("original_sub_tasks", []),
                        "parent_sub_task": sub_task.get("parent_sub_task", {})
                    }
                )
            
            self.logger.info(f"保存了 {len(sub_tasks)} 个子任务到数据库")
        except Exception as e:
            raise TaskDecomposerError(f"保存子任务失败: {str(e)}")
    
    async def get_sub_tasks(self, task_id: int) -> List[Dict]:
        """
        获取任务的子任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            子任务列表
        """
        try:
            sub_tasks = await self.task_history_manager.get_sub_tasks(task_id)
            return sub_tasks
        except Exception as e:
            raise TaskDecomposerError(f"获取子任务失败: {str(e)}")
    
    async def update_sub_task_status(self, sub_task_id: str, status: str, 
                                   result: Optional[Dict] = None):
        """
        更新子任务状态
        
        Args:
            sub_task_id: 子任务ID
            status: 新状态
            result: 子任务结果
        """
        try:
            await self.task_history_manager.update_sub_task_status(
                sub_task_id=sub_task_id,
                status=status,
                result=result
            )
            
            self.logger.info(f"更新子任务 {sub_task_id} 状态为 {status}")
        except Exception as e:
            raise TaskDecomposerError(f"更新子任务状态失败: {str(e)}")