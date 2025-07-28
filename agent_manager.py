"""
Agent management module using CrewAI for the AI Agent Flow system.
Handles agent creation, task management, and coordination.
"""

from crewai import Agent, Task, Crew, Process

class AgentManager:
    """Manages AI agents and their tasks using CrewAI."""
    
    def __init__(self):
        """Initialize agent manager and create core agents."""
        self.agents = {}
        self.create_core_agents()
    
    def create_core_agents(self):
        """Create and register core agents with the system."""
        # Create a basic agent for demonstration
        engineer_agent = Agent(
            role='Software Engineer',
            goal='Write clean, efficient code for the system',
            backstory="""You are an expert software engineer with years of experience
            in Python development and AI systems integration.""",
            verbose=True
        )
        
        self.agents['engineer'] = engineer_agent
    
    def create_task(self, agent_name, task_description):
        """Create a new task for a specific agent."""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")
            
        agent = self.agents[agent_name]
        task = Task(
            description=task_description,
            agent=agent
        )
        
        return task
    
    def run_task(self, task):
        """Execute a single task."""
        crew = Crew(
            agents=[task.agent],
            tasks=[task],
            process=Process.sequential
        )
        
        result = crew.kickoff()
        return result

if __name__ == "__main__":
    # Example usage
    manager = AgentManager()
    task = manager.create_task('engineer', 'Write a function to calculate Fibonacci numbers')
    result = manager.run_task(task)
    print(f"Task result: {result}")