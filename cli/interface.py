"""
命令行交互界面模块
提供用户与系统交互的命令行界面
"""

import argparse
import sys
import json
from typing import Dict, Any

from llm.client import LLMClient
from agent.manager import AgentManager
from agent.executor import TaskExecutor
from mcp.service import MCPService
from mcp.tools.file_manager import TOOL_INFO as FILE_TOOLS
from data.database import DatabaseManager


class CLIInterface:
    """命令行交互界面"""

    def __init__(self):
        self.llm_client = LLMClient()
        self.agent_manager = AgentManager()
        self.task_executor = TaskExecutor(self.agent_manager)
        self.mcp_service = MCPService()
        self.db_manager = DatabaseManager()
        
        # 注册MCP工具
        self._register_mcp_tools()
        
        # 设置命令行参数解析器
        self.parser = self._setup_argument_parser()

    def _register_mcp_tools(self):
        """注册MCP工具"""
        for tool_name, tool_info in FILE_TOOLS.items():
            self.mcp_service.register_tool(
                tool_name, 
                tool_info["function"], 
                tool_info["description"]
            )

    def _setup_argument_parser(self) -> argparse.ArgumentParser:
        """设置命令行参数解析器"""
        parser = argparse.ArgumentParser(
            description="AI Agent Flow - AI驱动的工程实现闭环系统",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
使用示例:
  %(prog)s -r "创建一个Python Web应用"  # 直接提供需求
  %(prog)s -i                     # 进入交互模式
  %(prog)s -c "config.json"       # 使用配置文件
"""
        )
        
        parser.add_argument(
            "-r", "--requirement",
            help="直接提供需求描述",
            type=str
        )
        
        parser.add_argument(
            "-i", "--interactive",
            help="进入交互模式",
            action="store_true"
        )
        
        parser.add_argument(
            "-c", "--config",
            help="配置文件路径",
            type=str
        )
        
        parser.add_argument(
            "-v", "--verbose",
            help="显示详细信息",
            action="store_true"
        )
        
        return parser

    def _load_config(self, config_path: str):
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 设置LLM配置
            llm_config = config.get("llm", {})
            self.llm_client.set_config(
                base_url=llm_config.get("base_url"),
                api_key=llm_config.get("api_key"),
                model=llm_config.get("model")
            )
            
            # 设置数据库配置
            db_config = config.get("database", {})
            db_path = db_config.get("path")
            if db_path:
                self.db_manager = DatabaseManager(db_path)
                
            if self.parser.parse_args().verbose:
                print(f"配置文件加载成功: {config_path}")
        except Exception as e:
            print(f"配置文件加载失败: {e}")

    def _get_user_requirement(self) -> str:
        """获取用户需求"""
        print("请输入您的需求描述（输入完成后按Ctrl+D或Ctrl+Z结束）:")
        print("(您可以直接粘贴需求，然后按Ctrl+D（Linux/Mac）或Ctrl+Z+Enter（Windows）)")
        
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        
        return "\n".join(lines)

    def _get_additional_info(self, info_type: str, question: str) -> Dict[str, Any]:
        """获取额外信息"""
        print(f"\n需要额外信息: {question}")
        
        if info_type == "natural_language":
            print("请输入您的补充信息:")
            lines = []
            try:
                while True:
                    line = input()
                    lines.append(line)
            except EOFError:
                pass
            return {"type": "natural_language", "content": "\n".join(lines)}
        
        elif info_type == "user_data":
            print("请提供相关数据或其他信息:")
            lines = []
            try:
                while True:
                    line = input()
                    lines.append(line)
            except EOFError:
                pass
            return {"type": "user_data", "content": "\n".join(lines)}
        
        elif info_type == "folder_content":
            # 请求文件夹内容
            result = self.mcp_service.execute_tool("list_files", {"directory": "."})
            if result["success"]:
                files = result["result"]["files"]
                print("当前文件夹内容:")
                for file in files:
                    print(f"  {file['name']} ({'目录' if file['is_directory'] else '文件'})")
                return {"type": "folder_content", "content": files}
            else:
                print(f"获取文件夹内容失败: {result['error']}")
                return {"type": "folder_content", "content": [], "error": result["error"]}
        
        elif info_type == "open_file":
            print("请输入要打开的文件路径:")
            file_path = input().strip()
            result = self.mcp_service.execute_tool("read_file", {"file_path": file_path})
            if result["success"]:
                print(f"文件内容:\n{result['result']['content']}")
                return {"type": "open_file", "content": result["result"]["content"], "file_path": file_path}
            else:
                print(f"读取文件失败: {result['error']}")
                return {"type": "open_file", "content": "", "file_path": file_path, "error": result["error"]}
        
        else:
            print("未知的信息类型")
            return {"type": "unknown", "content": ""}

    def _process_requirement(self, requirement: str):
        """处理用户需求"""
        print(f"正在处理需求: {requirement[:50]}...")
        
        # 1. 任务分解
        print("正在进行任务分解...")
        decomposition_result = self.llm_client.task_decomposition(requirement)
        
        if not decomposition_result["success"]:
            print(f"任务分解失败: {decomposition_result['error']}")
            return
        
        print("任务分解完成")
        if self.parser.parse_args().verbose:
            print(f"分解结果: {decomposition_result['content']}")
        
        # 2. 创建Agent和任务
        print("正在创建Agent和任务...")
        # 这里可以根据分解结果创建具体的Agent和任务
        # 为简化示例，我们创建一个通用的Agent
        general_agent = self.agent_manager.create_agent(
            name="通用Agent",
            role="通用任务执行者",
            goal="高效完成用户需求",
            backstory="一个经验丰富的AI助手，能够处理各种任务"
        )
        
        # 3. 执行任务（带推理和额外信息获取）
        print("正在执行任务...")
        # 解析任务分解结果
        try:
            tasks = json.loads(decomposition_result["content"])
        except json.JSONDecodeError:
            print("任务分解结果不是有效的JSON格式，使用默认任务")
            tasks = [{"description": "根据需求生成完整的解决方案", "type": "content_generation"}]
        
        # 任务执行结果列表
        task_results = []
        
        # 推理循环计数器
        inference_count = 0
        max_inference_count = 5
        
        # 执行每个任务
        for i, task in enumerate(tasks):
            # 检查推理循环次数
            if inference_count >= max_inference_count:
                print(f"已达到最大推理循环次数({max_inference_count})，跳过剩余任务")
                break
            
            task_description = task.get("description", "未指定任务描述")
            task_type = task.get("type", "content_generation")
            
            print(f"\n执行任务 {i+1}/{len(tasks)}: {task_description}")
            
            # 循环推理和获取额外信息，直到不需要额外信息或达到最大循环次数
            while inference_count < max_inference_count:
                # 构建任务上下文
                task_context = f"原始需求: {requirement}\n\n已完成的任务结果:\n"
                for j, result in enumerate(task_results):
                    task_context += f"{j+1}. {result.get('task', '未知任务')}: {result.get('result', '无结果')}\n"
                
                # 调用大模型推理是否需要额外信息
                print("正在推理是否需要额外信息...")
                inference_result = self.llm_client.need_additional_info(task_context, task_description)
                
                if not inference_result["success"]:
                    print(f"推理失败: {inference_result['error']}")
                    break
                
                inference_count += 1
                
                # 解析推理结果
                try:
                    inference_data = json.loads(inference_result["content"])
                except json.JSONDecodeError:
                    print("推理结果不是有效的JSON格式")
                    print(f"推理结果内容: {inference_result['content']}")
                    break
                
                # 检查是否需要额外信息
                if inference_data.get("need_info", False):
                    info_type = inference_data.get("info_type", "")
                    reason = inference_data.get("reason", "")
                    question = inference_data.get("question", "请提供相关信息")
                    
                    print(f"需要额外信息 ({info_type}): {reason}")
                    
                    # 获取额外信息
                    additional_info = self._get_additional_info(info_type, question)
                    
                    # 将额外信息添加到任务上下文中
                    task_context += f"\n用户提供的额外信息 ({additional_info['type']}):\n{additional_info['content']}\n"
                    
                    # 继续循环，再次推理
                    continue
                else:
                    print("不需要额外信息，继续执行任务")
                    break
            
            # 执行任务
            if task_type == "content_generation":
                generation_result = self.llm_client.content_generation(
                    context=task_context,
                    task=task_description
                )
                
                if not generation_result["success"]:
                    print(f"任务执行失败: {generation_result['error']}")
                    task_results.append({
                        "task": task_description,
                        "result": f"执行失败: {generation_result['error']}",
                        "status": "error"
                    })
                else:
                    print("任务执行完成")
                    task_results.append({
                        "task": task_description,
                        "result": generation_result["content"],
                        "status": "success"
                    })
            else:
                # 其他类型的任务，这里简化处理
                print(f"执行任务类型: {task_type}")
                task_results.append({
                    "task": task_description,
                    "result": f"执行了 {task_type} 类型的任务",
                    "status": "success"
                })
        
        # 4. 结果整合
        print("正在整合结果...")
        integration_result = self.llm_client.result_integration([result["result"] for result in task_results])
        
        if not integration_result["success"]:
            print(f"结果整合失败: {integration_result['error']}")
            return
        
        print("结果整合完成")
        
        # 5. 结果展示
        print("\n=== 解决方案 ===")
        print(integration_result["content"])
        print("================\n")

    def run(self):
        """运行命令行界面"""
        args = self.parser.parse_args()
        
        # 加载配置文件
        if args.config:
            self._load_config(args.config)
        
        # 处理需求
        if args.requirement:
            # 直接处理提供的需求
            self._process_requirement(args.requirement)
        elif args.interactive:
            # 进入交互模式
            print("欢迎使用 AI Agent Flow!")
            print("输入 'quit' 或 'exit' 退出程序")
            
            while True:
                try:
                    user_input = input("\n> ").strip()
                    
                    if user_input.lower() in ['quit', 'exit']:
                        print("再见!")
                        break
                    
                    if user_input.lower() == 'help':
                        self.parser.print_help()
                        continue
                    
                    if user_input:
                        self._process_requirement(user_input)
                except KeyboardInterrupt:
                    print("\n\n程序被用户中断")
                    break
                except EOFError:
                    print("\n\n再见!")
                    break
        else:
            # 没有提供参数，显示帮助信息
            self.parser.print_help()
            
            # 询问是否进入交互模式
            print("\n是否进入交互模式? (y/n): ", end="")
            try:
                choice = input().strip().lower()
                if choice in ['y', 'yes']:
                    args.interactive = True
                    self.run()
            except:
                pass