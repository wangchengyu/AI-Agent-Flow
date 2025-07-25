"""
Agent 管理模块
使用 crewAI 作为 Agent 管理框架
"""

from typing import List, Dict, Any
from crewai import Agent, Task, Crew


class AgentManager:
    """Agent 管理器"""

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.tasks: List[Task] = []
        self.crew: Crew = None

    def create_agent(self, name: str, role: str, goal: str, backstory: str, **kwargs) -> Agent:
        """
        创建一个新的 Agent
        
        Args:
            name: Agent 名称
            role: Agent 角色
            goal: Agent 目标
            backstory: Agent 背景故事
            **kwargs: 其他参数
            
        Returns:
            Agent: 创建的 Agent 实例
        """
        agent = Agent(
            name=name,
            role=role,
            goal=goal,
            backstory=backstory,
            **kwargs
        )
        self.agents[name] = agent
        return agent

    def get_agent(self, name: str) -> Agent:
        """
        获取指定名称的 Agent
        
        Args:
            name: Agent 名称
            
        Returns:
            Agent: Agent 实例
        """
        return self.agents.get(name)

    def create_task(self, description: str, agent: Agent, expected_output: str, **kwargs) -> Task:
        """
        创建一个新的任务
        
        Args:
            description: 任务描述
            agent: 执行任务的 Agent
            expected_output: 期望输出
            **kwargs: 其他参数
            
        Returns:
            Task: 创建的任务实例
        """
        task = Task(
            description=description,
            agent=agent,
            expected_output=expected_output,
            **kwargs
        )
        self.tasks.append(task)
        return task

    def create_crew(self, agents: List[Agent], tasks: List[Task], **kwargs) -> Crew:
        """
        创建一个 Crew
        
        Args:
            agents: Agent 列表
            tasks: 任务列表
            **kwargs: 其他参数
            
        Returns:
            Crew: 创建的 Crew 实例
        """
        self.crew = Crew(
            agents=agents,
            tasks=tasks,
            **kwargs
        )
        return self.crew

    def execute_crew(self) -> Dict[str, Any]:
        """
        执行 Crew 中的所有任务
        
        Returns:
            Dict[str, Any]: 执行结果
        """
        if self.crew is None:
            raise ValueError("Crew not created. Please create a crew first.")
        
        return self.crew.kickoff()