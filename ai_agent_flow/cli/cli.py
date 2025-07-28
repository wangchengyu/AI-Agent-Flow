import argparse
import os
from agent.agent_manager import AgentManager
from mcp.tools.file_manager import FileManager
from llm.llm_interface import LLMClient
from mcp.mcp_manager import MCPManager
from data.database import Database

class CLI:
    def __init__(self):
        """初始化命令行接口"""
        self.agent_manager = AgentManager()
        self.file_manager = FileManager()
        self.llm_client = LLMClient()
        self.mcp_manager = MCPManager()
        self.database = Database()
        
    def run(self):
        """运行命令行界面"""
        parser = argparse.ArgumentParser(description='AI Agent Flow CLI')
        subparsers = parser.add_subparsers(dest='command')
        
        # Agent相关命令
        agent_parser = subparsers.add_parser('agent', help='Agent管理')
        agent_subparsers = agent_parser.add_subparsers(dest='agent_command')
        
        create_agent_parser = agent_subparsers.add_parser('create', help='创建Agent')
        create_agent_parser.add_argument('--role', required=True, help='Agent角色')
        create_agent_parser.add_argument('--goal', required=True, help='Agent目标')
        create_agent_parser.add_argument('--backstory', required=True, help='Agent背景故事')
        
        # 任务相关命令
        task_parser = subparsers.add_parser('task', help='任务管理')
        task_subparsers = task_parser.add_subparsers(dest='task_command')
        
        create_task_parser = task_subparsers.add_parser('create', help='创建任务')
        create_task_parser.add_argument('--description', required=True, help='任务描述')
        create_task_parser.add_argument('--agent', required=True, help='关联Agent')
        create_task_parser.add_argument('--expected_output', required=True, help='预期输出')
        
        # 文件管理命令
        file_parser = subparsers.add_parser('file', help='文件管理')
        file_subparsers = file_parser.add_subparsers(dest='file_command')
        
        list_files_parser = file_subparsers.add_parser('list', help='列出文件')
        list_files_parser.add_argument('--path', default='.', help='路径')
        
        read_file_parser = file_subparsers.add_parser('read', help='读取文件')
        read_file_parser.add_argument('--path', required=True, help='文件路径')
        
        # 大模型交互命令
        llm_parser = subparsers.add_parser('llm', help='大模型交互')
        llm_parser.add_argument('--prompt', required=True, help='用户提示')
        llm_parser.add_argument('--context', help='上下文信息')
        
        # MCP服务命令
        mcp_parser = subparsers.add_parser('mcp', help='MCP服务管理')
        mcp_subparsers = mcp_parser.add_subparsers(dest='mcp_command')
        
        start_mcp_parser = mcp_subparsers.add_parser('start', help='启动MCP服务')
        
        # 执行命令
        execute_parser = subparsers.add_parser('execute', help='执行任务')
        execute_parser.add_argument('--task', required=True, help='任务描述')
        
        args = parser.parse_args()
        
        if args.command == 'agent' and args.agent_command == 'create':
            self.agent_manager.create_agent(args.role, args.goal, args.backstory)
            print(f"创建Agent: {args.role}")
            print("Agent创建成功，已记录到数据库")
            
        elif args.command == 'task' and args.task_command == 'create':
            agent = self.agent_manager.agents.get(args.agent)
            if agent:
                self.agent_manager.create_task(args.description, agent, args.expected_output)
                print(f"创建任务: {args.description}")
                print("任务创建成功，已记录到数据库")
            else:
                print(f"错误: 找不到Agent {args.agent}")
                
        elif args.command == 'file' and args.file_command == 'list':
            result = self.file_manager.list_files(args.path)
            if result['status'] == 'success':
                print(f"文件列表 ({args.path}):")
                for file in result['files']:
                    print(f"- {file}")
            else:
                print(f"错误: {result['message']}")
                
        elif args.command == 'file' and args.file_command == 'read':
            result = self.file_manager.read_file(args.path)
            if result['status'] == 'success':
                print(f"文件内容 ({args.path}):")
                print(result['content'])
            else:
                print(f"错误: {result['message']}")
                
        elif args.command == 'llm':
            result = self.llm_client.send_request(args.prompt, args.context)
            print("大模型响应:")
            print(result)
            
        elif args.command == 'mcp' and args.mcp_command == 'start':
            self.mcp_manager.start_mcp_server()
            print("MCP服务启动成功")
            
        elif args.command == 'execute':
            # 执行任务前的推理
            reasoning_result = self.llm_client.pre_execute_reasoning(args.task)
            
            if reasoning_result.get('need_extra_info', False):
                print("任务需要额外信息:")
                print(f"类型: {reasoning_result.get('extra_info_types', [])}")
                print(f"原因: {reasoning_result.get('reason', '')}")
                
                # 根据额外信息类型进行处理
                for info_type in reasoning_result.get('extra_info_types', []):
                    if info_type == "用户用自然语言补充的信息":
                        user_input = input("请补充任务信息: ")
                        args.task += f"\n用户补充: {user_input}"
                    
                    elif info_type == "请求当前文件夹的所有文件":
                        result = self.file_manager.list_files('.')
                        if result['status'] == 'success':
                            print("文件列表:")
                            for file in result['files']:
                                print(f"- {file}")
                            args.task += f"\n文件列表: {', '.join(result['files'])}"
                        else:
                            print(f"获取文件列表失败: {result['message']}")
            
            # 执行任务
            result = self.llm_client.send_request(args.task)
            print("任务执行结果:")
            print(result)
            
            # 将任务结果保存到数据库
            self.database.insert_task_result('task_123', str(result))
            
        else:
            parser.print_help()

if __name__ == '__main__':
    cli = CLI()
    cli.run()