from typing import List, Dict, Any
from crewai import Agent, Task, Crew
from .task_decomposer import TaskDecomposer
from .subtask_state import SubTaskState

class AgentManager:
    def __init__(self, llm_model: Any):
        self.llm_model = llm_model
        self.task_decomposer = TaskDecomposer(llm_model)
        self.crew = None
        
    def initialize(self, agents: List[Agent]):
        """初始化Agent工作流"""
        self.crew = Crew(
            agents=agents,
            verbose=True,
            memory=True
        )
        
    def process_tasks(self, user_input: str) -> List[Dict]:
        """处理用户输入并执行任务"""
        # 任务分解
        tasks = self.task_decomposer.decompose(user_input)
        
        # 创建CrewAI任务
        crewai_tasks = []
        for task in tasks:
            crewai_tasks.append(Task(
                description=task['description'],
                agent=self._select_agent(task),
                expected_output=task.get('expected_output', '')
            ))
        
        # 执行任务
        results = self.crew.kickoff(inputs={'user_input': user_input})
        return self._process_results(results)
        
    def _select_agent(self, task: Dict) -> Agent:
        """根据任务类型选择Agent"""
        # 简化实现，实际应根据任务类型动态选择
        return self.crew.agents[0]
        
    def _process_results(self, results: Any) -> List[Dict]:
        """处理任务执行结果"""
        # 简化实现，实际应解析结构化结果
        return [{'result': results}]
        
    def handle_state_transitions(self, task_id: str, new_state: SubTaskState):
        """处理子任务状态转换"""
        # 状态转换逻辑实现
        print(f"Task {task_id} transitioned to {new_state.name}")