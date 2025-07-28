from crewai import Agent, Task, Crew
from config.config import load_config

class AgentManager:
    def __init__(self):
        self.config = load_config()
        self.agents = {}
        self.tasks = {}
        self.crew = None
        
    def create_agent(self, role, goal, backstory, verbose=True):
        """创建一个新的Agent"""
        agent = Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=verbose,
            allow_delegation=True
        )
        self.agents[role] = agent
        return agent
        
    def create_task(self, description, agent, expected_output):
        """创建一个新的任务"""
        task = Task(
            description=description,
            agent=agent,
            expected_output=expected_output
        )
        self.tasks[description] = task
        return task
        
    def create_crew(self, agents, tasks, process_type="sequential"):
        """创建Crew团队"""
        self.crew = Crew(
            agents=agents,
            tasks=tasks,
            process=process_type
        )
        return self.crew
        
    def run_crew(self):
        """运行Crew团队"""
        if self.crew:
            return self.crew.kickoff()
        return None