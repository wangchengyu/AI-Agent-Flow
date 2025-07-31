import argparse
import cmd
from typing import List, Dict, Any
from src.agents.subtask_state import SubTaskState
from src.agents.agent_manager import AgentManager
from src.database.db_manager import DatabaseManager
from src.tools.mcp_service import MCPRegistry

class CLIInterface(cmd.Cmd):
    prompt = "agent_flow> "
    
    def __init__(self, agent_manager: AgentManager, db_manager: DatabaseManager):
        super().__init__()
        self.agent_manager = agent_manager
        self.db_manager = db_manager
        self.current_task_id = None
        self.session_state = {
            'history': []
        }
        
    def start(self):
        """启动命令行交互"""
        print("AI Agent Flow System - Type /help for commands")
        self.cmdloop()
        
    def do_exit(self, arg):
        """退出系统: exit"""
        print("Exiting...")
        return True
        
    def do_history(self, arg):
        """查看任务历史: /history [limit]"""
        limit = 10
        if arg:
            try:
                limit = int(arg)
            except ValueError:
                print("Invalid limit value. Using default 10.")
                
        tasks = self.db_manager.get_task_history(limit)
        if not tasks:
            print("No task history found.")
            return
            
        print("\nTask History:")
        for task in tasks:
            print(f"ID: {task['task_id']}, Time: {task['timestamp']}")
            print(f"Input: {task['user_input']}")
            print("---")
            
    def do_config(self, arg):
        """修改LLM参数: /config <param> <value>"""
        # 简化实现，实际应支持多种参数配置
        print("Config command not implemented yet.")
        
    def do_debug(self, arg):
        """进入调试模式: /debug"""
        print("Entering debug mode...")
        DebugCLI(self).cmdloop()
        
    def default(self, line):
        """处理自然语言输入"""
        if line.startswith('/'):
            print(f"Unknown command: {line.split()[0]}")
            return
            
        # 保存到会话历史
        self.session_state['history'].append({
            'input': line,
            'output': None
        })
        
        # 处理用户输入
        print("Processing your request...")
        results = self.agent_manager.process_tasks(line)
        
        # 保存任务
        tasks = [{
            'description': line,
            'status': SubTaskState.COMPLETED
        }]
        task_id = self.db_manager.save_task(line, tasks)
        self.current_task_id = task_id
        
        # 显示结果
        print("\nTask Results:")
        for result in results:
            print(result.get('result', 'No result'))
            
        # 添加到会话历史
        self.session_state['history'][-1]['output'] = results
        
    def emptyline(self):
        """忽略空行"""
        pass
        
    def precmd(self, line):
        """命令预处理"""
        # 保存命令历史
        if line and line != 'EOF':
            self.session_state['history'].append({
                'input': line,
                'output': None
            })
        return line
        
    def postcmd(self, stop, line):
        """命令后处理"""
        if line:
            # 更新会话历史
            self.session_state['history'][-1]['output'] = "Command executed"
        return stop
        
class DebugCLI(cmd.Cmd):
    prompt = "debug> "
    
    def __init__(self, main_cli: CLIInterface):
        super().__init__()
        self.main_cli = main_cli
        
    def do_state(self, arg):
        """查看当前任务状态: state"""
        if self.main_cli.current_task_id:
            task = self.main_cli.db_manager.get_task_history(1)[0]
            print(f"Current Task ID: {task['task_id']}")
            print(f"Input: {task['user_input']}")
            subtasks = task['subtasks']
            for i, subtask in enumerate(subtasks):
                print(f"Subtask {i+1}: {subtask['description']}")
                print(f"  Status: {subtask['status'].name}")
        else:
            print("No active task.")
            
    def do_back(self, arg):
        """返回主界面: back"""
        print("Exiting debug mode.")
        return True