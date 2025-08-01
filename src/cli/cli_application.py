"""
命令行应用程序

负责整合命令行交互模块的各个组件，
提供完整的命令行应用功能。
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable

from .cli_parser import CLIParser
from .interactive_interface import InteractiveInterface
from .progress_display import ProgressDisplay
from .result_formatter import ResultFormatter

from ..agent.agent_manager import AgentManager
from ..database.database_manager import DatabaseManager
from ..rag.knowledge_manager import KnowledgeManager
from ..mcp_tools.tool_manager import ToolManager
from ..config.config_manager import ConfigManager

from ..utils.exceptions import CLIApplicationError


class CLIApplication:
    """命令行应用程序，负责整合命令行交互模块的各个组件"""
    
    def __init__(self):
        """初始化命令行应用程序"""
        # 初始化组件
        self.cli_parser = CLIParser()
        self.interface = InteractiveInterface()
        self.progress_display = ProgressDisplay(self.interface)
        self.result_formatter = ResultFormatter(self.interface)
        
        # 初始化管理器
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager(self.config_manager)
        self.knowledge_manager = KnowledgeManager(self.db_manager)
        self.tool_manager = ToolManager(self.db_manager)
        self.agent_manager = AgentManager(
            self.db_manager,
            self.knowledge_manager,
            self.tool_manager
        )
        
        # 应用程序状态
        self.running = False
        self.current_task_id = None
        self.interactive_mode = False
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("命令行应用程序初始化完成")
    
    async def initialize(self):
        """初始化命令行应用程序"""
        try:
            # 初始化配置管理器
            await self.config_manager.initialize()
            
            # 初始化数据库管理器
            await self.db_manager.initialize()
            
            # 初始化知识管理器
            await self.knowledge_manager.initialize()
            
            # 初始化工具管理器
            await self.tool_manager.initialize()
            
            # 初始化Agent管理器
            await self.agent_manager.initialize()
            
            # 初始化交互式界面
            await self.interface.initialize()
            
            # 初始化进度显示器
            await self.progress_display.initialize()
            
            # 初始化结果格式化器
            await self.result_formatter.initialize()
            
            self.logger.info("命令行应用程序初始化完成")
        except Exception as e:
            raise CLIApplicationError(f"初始化命令行应用程序失败: {str(e)}")
    
    async def run(self, args: Optional[List[str]] = None):
        """
        运行命令行应用程序
        
        Args:
            args: 命令行参数，如果为None则使用sys.argv[1:]
        """
        try:
            # 解析命令行参数
            parsed_args = self.cli_parser.parse_args(args)
            
            # 验证参数
            if not self.cli_parser.validate_args(parsed_args):
                return
            
            # 执行命令
            command = parsed_args.get("command")
            
            if command == "run":
                await self._handle_run_command(parsed_args)
            elif command == "status":
                await self._handle_status_command(parsed_args)
            elif command == "list":
                await self._handle_list_command(parsed_args)
            elif command == "stop":
                await self._handle_stop_command(parsed_args)
            elif command == "pause":
                await self._handle_pause_command(parsed_args)
            elif command == "resume":
                await self._handle_resume_command(parsed_args)
            elif command == "retry":
                await self._handle_retry_command(parsed_args)
            elif command == "result":
                await self._handle_result_command(parsed_args)
            elif command == "config":
                await self._handle_config_command(parsed_args)
            elif command == "stats":
                await self._handle_stats_command(parsed_args)
            elif command == "knowledge":
                await self._handle_knowledge_command(parsed_args)
            elif command == "tools":
                await self._handle_tools_command(parsed_args)
            elif command == "version":
                await self._handle_version_command(parsed_args)
            elif command == "help":
                await self._handle_help_command(parsed_args)
            else:
                print(f"未知命令: {command}")
                self.cli_parser.print_help()
        except KeyboardInterrupt:
            print("\n操作已取消")
        except Exception as e:
            print(f"错误: {str(e)}")
            self.logger.error(f"运行命令行应用程序失败: {str(e)}")
    
    async def _handle_run_command(self, args: Dict[str, Any]):
        """
        处理run命令
        
        Args:
            args: 命令参数
        """
        try:
            task_description = args.get("task_description", "")
            user_id = args.get("user_id")
            context = args.get("context", {})
            async_mode = args.get("async", False)
            
            if not task_description:
                print("错误: 任务描述不能为空")
                return
            
            # 显示任务信息
            print(f"开始执行任务: {task_description}")
            if user_id:
                print(f"用户ID: {user_id}")
            if context:
                print(f"上下文: {json.dumps(context, ensure_ascii=False, indent=2)}")
            print()
            
            # 运行任务
            if async_mode:
                # 异步运行
                task_id = await self.agent_manager.run_task_async(
                    task_description=task_description,
                    user_id=user_id,
                    context=context
                )
                
                print(f"任务已提交，任务ID: {task_id}")
                print("使用以下命令查看任务状态:")
                print(f"  agent status --task-id {task_id}")
            else:
                # 同步运行
                task_id = await self.agent_manager.run_task(
                    task_description=task_description,
                    user_id=user_id,
                    context=context,
                    progress_callback=self._progress_callback
                )
                
                # 获取任务结果
                task_result = await self.agent_manager.get_task_result(task_id)
                
                # 格式化并显示结果
                result_text = await self.result_formatter.format_task_result(task_result)
                print(result_text)
        except Exception as e:
            print(f"执行任务失败: {str(e)}")
            self.logger.error(f"执行任务失败: {str(e)}")
    
    async def _handle_status_command(self, args: Dict[str, Any]):
        """
        处理status命令
        
        Args:
            args: 命令参数
        """
        try:
            task_id = args.get("task_id")
            verbose = args.get("verbose", False)
            
            if not task_id:
                print("错误: 任务ID不能为空")
                return
            
            # 获取任务状态
            task_status = await self.agent_manager.get_task_status(task_id)
            
            if not task_status:
                print(f"错误: 任务 {task_id} 不存在")
                return
            
            # 显示任务状态
            print(f"任务ID: {task_id}")
            print(f"任务名称: {task_status.get('task_name', '未知')}")
            print(f"状态: {task_status.get('status', '未知')}")
            
            # 显示详细信息
            if verbose:
                print(f"任务描述: {task_status.get('description', '无')}")
                print(f"创建时间: {task_status.get('created_at', '未知')}")
                print(f"开始时间: {task_status.get('start_time', '未知')}")
                print(f"结束时间: {task_status.get('end_time', '未知')}")
                
                # 显示子任务状态
                sub_tasks = task_status.get("sub_tasks", [])
                if sub_tasks:
                    print("\n子任务状态:")
                    for sub_task in sub_tasks:
                        sub_task_id = sub_task.get("id", "未知")
                        sub_task_name = sub_task.get("name", "未知")
                        sub_task_status = sub_task.get("status", "未知")
                        print(f"  - {sub_task_name} (ID: {sub_task_id}): {sub_task_status}")
        except Exception as e:
            print(f"获取任务状态失败: {str(e)}")
            self.logger.error(f"获取任务状态失败: {str(e)}")
    
    async def _handle_list_command(self, args: Dict[str, Any]):
        """
        处理list命令
        
        Args:
            args: 命令参数
        """
        try:
            user_id = args.get("user_id")
            status = args.get("status")
            limit = args.get("limit", 20)
            offset = args.get("offset", 0)
            output_format = args.get("format", "table")
            
            # 获取任务列表
            tasks = await self.agent_manager.list_tasks(
                user_id=user_id,
                status=status,
                limit=limit,
                offset=offset
            )
            
            if not tasks:
                print("没有找到符合条件的任务")
                return
            
            # 根据输出格式显示任务列表
            if output_format == "json":
                print(json.dumps(tasks, ensure_ascii=False, indent=2))
            else:
                # 构建表格数据
                headers = ["ID", "名称", "状态", "创建时间"]
                rows = []
                
                for task in tasks:
                    task_id = task.get("id", "未知")
                    task_name = task.get("task_name", "未知")
                    task_status = task.get("status", "未知")
                    created_at = task.get("created_at", "未知")
                    
                    rows.append([
                        str(task_id),
                        task_name,
                        task_status,
                        created_at
                    ])
                
                # 显示表格
                await self.interface.table(headers, rows, "任务列表")
        except Exception as e:
            print(f"获取任务列表失败: {str(e)}")
            self.logger.error(f"获取任务列表失败: {str(e)}")
    
    async def _handle_stop_command(self, args: Dict[str, Any]):
        """
        处理stop命令
        
        Args:
            args: 命令参数
        """
        try:
            task_id = args.get("task_id")
            reason = args.get("reason", "用户请求停止")
            
            if not task_id:
                print("错误: 任务ID不能为空")
                return
            
            # 停止任务
            success = await self.agent_manager.stop_task(
                task_id=task_id,
                reason=reason
            )
            
            if success:
                print(f"任务 {task_id} 已停止")
            else:
                print(f"停止任务 {task_id} 失败")
        except Exception as e:
            print(f"停止任务失败: {str(e)}")
            self.logger.error(f"停止任务失败: {str(e)}")
    
    async def _handle_pause_command(self, args: Dict[str, Any]):
        """
        处理pause命令
        
        Args:
            args: 命令参数
        """
        try:
            task_id = args.get("task_id")
            
            if not task_id:
                print("错误: 任务ID不能为空")
                return
            
            # 暂停任务
            success = await self.agent_manager.pause_task(task_id=task_id)
            
            if success:
                print(f"任务 {task_id} 已暂停")
            else:
                print(f"暂停任务 {task_id} 失败")
        except Exception as e:
            print(f"暂停任务失败: {str(e)}")
            self.logger.error(f"暂停任务失败: {str(e)}")
    
    async def _handle_resume_command(self, args: Dict[str, Any]):
        """
        处理resume命令
        
        Args:
            args: 命令参数
        """
        try:
            task_id = args.get("task_id")
            
            if not task_id:
                print("错误: 任务ID不能为空")
                return
            
            # 恢复任务
            success = await self.agent_manager.resume_task(task_id=task_id)
            
            if success:
                print(f"任务 {task_id} 已恢复")
            else:
                print(f"恢复任务 {task_id} 失败")
        except Exception as e:
            print(f"恢复任务失败: {str(e)}")
            self.logger.error(f"恢复任务失败: {str(e)}")
    
    async def _handle_retry_command(self, args: Dict[str, Any]):
        """
        处理retry命令
        
        Args:
            args: 命令参数
        """
        try:
            task_id = args.get("task_id")
            
            if not task_id:
                print("错误: 任务ID不能为空")
                return
            
            # 重试任务
            success = await self.agent_manager.retry_task(task_id=task_id)
            
            if success:
                print(f"任务 {task_id} 已重试")
            else:
                print(f"重试任务 {task_id} 失败")
        except Exception as e:
            print(f"重试任务失败: {str(e)}")
            self.logger.error(f"重试任务失败: {str(e)}")
    
    async def _handle_result_command(self, args: Dict[str, Any]):
        """
        处理result命令
        
        Args:
            args: 命令参数
        """
        try:
            task_id = args.get("task_id")
            output_format = args.get("format", "text")
            
            if not task_id:
                print("错误: 任务ID不能为空")
                return
            
            # 获取任务结果
            task_result = await self.agent_manager.get_task_result(task_id)
            
            if not task_result:
                print(f"错误: 任务 {task_id} 不存在或没有结果")
                return
            
            # 格式化并显示结果
            result_text = await self.result_formatter.format_task_result(
                task_result=task_result,
                format_type=output_format
            )
            print(result_text)
        except Exception as e:
            print(f"获取任务结果失败: {str(e)}")
            self.logger.error(f"获取任务结果失败: {str(e)}")
    
    async def _handle_config_command(self, args: Dict[str, Any]):
        """
        处理config命令
        
        Args:
            args: 命令参数
        """
        try:
            config_command = args.get("config_command")
            
            if config_command == "get":
                key = args.get("key")
                if not key:
                    print("错误: 配置键不能为空")
                    return
                
                # 获取配置值
                value = await self.config_manager.get(key)
                print(f"{key} = {value}")
            
            elif config_command == "set":
                key = args.get("key")
                value = args.get("value")
                
                if not key or value is None:
                    print("错误: 配置键和值不能为空")
                    return
                
                # 尝试解析JSON值
                try:
                    parsed_value = json.loads(value)
                except json.JSONDecodeError:
                    parsed_value = value
                
                # 设置配置值
                success = await self.config_manager.set(key, parsed_value)
                
                if success:
                    print(f"配置已更新: {key} = {parsed_value}")
                else:
                    print(f"更新配置失败: {key}")
            
            elif config_command == "list":
                # 获取所有配置
                config = await self.config_manager.get_all()
                
                # 显示配置
                for key, value in config.items():
                    print(f"{key} = {value}")
            
            else:
                print(f"未知配置命令: {config_command}")
                self.cli_parser.print_help("config")
        except Exception as e:
            print(f"配置管理失败: {str(e)}")
            self.logger.error(f"配置管理失败: {str(e)}")
    
    async def _handle_stats_command(self, args: Dict[str, Any]):
        """
        处理stats命令
        
        Args:
            args: 命令参数
        """
        try:
            days = args.get("days", 30)
            stats_type = args.get("type", "all")
            
            # 获取统计信息
            if stats_type == "task" or stats_type == "all":
                task_stats = await self.agent_manager.get_task_statistics(days)
                
                if task_stats:
                    print("任务统计:")
                    print(f"  总任务数: {task_stats.get('total_tasks', 0)}")
                    print(f"  完成任务数: {task_stats.get('completed_tasks', 0)}")
                    print(f"  失败任务数: {task_stats.get('failed_tasks', 0)}")
                    print(f"  平均执行时间: {task_stats.get('avg_execution_time', 0):.2f} 秒")
                    print()
            
            if stats_type == "tool" or stats_type == "all":
                tool_stats = await self.tool_manager.get_tool_usage_statistics(days)
                
                if tool_stats:
                    print("工具使用统计:")
                    print(f"  总调用次数: {tool_stats.get('total_calls', 0)}")
                    print(f"  成功调用次数: {tool_stats.get('successful_calls', 0)}")
                    print(f"  失败调用次数: {tool_stats.get('failed_calls', 0)}")
                    print()
            
            if stats_type == "validation" or stats_type == "all":
                validation_stats = await self.agent_manager.get_validation_statistics(days)
                
                if validation_stats:
                    print("验证统计:")
                    print(f"  总验证次数: {validation_stats.get('total_validations', 0)}")
                    print(f"  通过验证次数: {validation_stats.get('passed_validations', 0)}")
                    print(f"  未通过验证次数: {validation_stats.get('failed_validations', 0)}")
                    print(f"  平均验证分数: {validation_stats.get('avg_validation_score', 0):.2f}")
                    print()
        except Exception as e:
            print(f"获取统计信息失败: {str(e)}")
            self.logger.error(f"获取统计信息失败: {str(e)}")
    
    async def _handle_knowledge_command(self, args: Dict[str, Any]):
        """
        处理knowledge命令
        
        Args:
            args: 命令参数
        """
        try:
            knowledge_command = args.get("knowledge_command")
            
            if knowledge_command == "add":
                file_path = args.get("file")
                source = args.get("source")
                tags = args.get("tags", [])
                
                if not file_path:
                    print("错误: 文件路径不能为空")
                    return
                
                # 添加知识
                knowledge_id = await self.knowledge_manager.add_knowledge(
                    file_path=file_path,
                    source=source,
                    tags=tags
                )
                
                print(f"知识已添加，ID: {knowledge_id}")
            
            elif knowledge_command == "search":
                query = args.get("query")
                limit = args.get("limit", 10)
                
                if not query:
                    print("错误: 搜索查询不能为空")
                    return
                
                # 搜索知识
                results = await self.knowledge_manager.search_knowledge(
                    query=query,
                    limit=limit
                )
                
                if not results:
                    print("没有找到匹配的知识")
                    return
                
                # 显示搜索结果
                print(f"找到 {len(results)} 条匹配的知识:")
                print()
                
                for i, result in enumerate(results):
                    knowledge_id = result.get("id", "未知")
                    title = result.get("title", "未知")
                    source = result.get("source", "未知")
                    score = result.get("score", 0)
                    
                    print(f"{i+1}. {title} (ID: {knowledge_id})")
                    print(f"   来源: {source}")
                    print(f"   相关性: {score:.2f}")
                    print()
            
            elif knowledge_command == "list":
                source = args.get("source")
                tags = args.get("tags", [])
                limit = args.get("limit", 20)
                
                # 列出知识
                knowledge_list = await self.knowledge_manager.list_knowledge(
                    source=source,
                    tags=tags,
                    limit=limit
                )
                
                if not knowledge_list:
                    print("没有找到知识")
                    return
                
                # 显示知识列表
                print(f"找到 {len(knowledge_list)} 条知识:")
                print()
                
                for i, knowledge in enumerate(knowledge_list):
                    knowledge_id = knowledge.get("id", "未知")
                    title = knowledge.get("title", "未知")
                    source = knowledge.get("source", "未知")
                    created_at = knowledge.get("created_at", "未知")
                    
                    print(f"{i+1}. {title} (ID: {knowledge_id})")
                    print(f"   来源: {source}")
                    print(f"   创建时间: {created_at}")
                    print()
            
            else:
                print(f"未知知识库命令: {knowledge_command}")
                self.cli_parser.print_help("knowledge")
        except Exception as e:
            print(f"知识库管理失败: {str(e)}")
            self.logger.error(f"知识库管理失败: {str(e)}")
    
    async def _handle_tools_command(self, args: Dict[str, Any]):
        """
        处理tools命令
        
        Args:
            args: 命令参数
        """
        try:
            tools_command = args.get("tools_command")
            output_format = args.get("format", "table")
            
            if tools_command == "list":
                # 获取工具列表
                tools = await self.tool_manager.list_tools()
                
                if not tools:
                    print("没有找到工具")
                    return
                
                # 根据输出格式显示工具列表
                if output_format == "json":
                    print(json.dumps(tools, ensure_ascii=False, indent=2))
                else:
                    # 构建表格数据
                    headers = ["名称", "描述", "类别"]
                    rows = []
                    
                    for tool in tools:
                        tool_name = tool.get("name", "未知")
                        description = tool.get("description", "无")
                        category = tool.get("category", "未知")
                        
                        rows.append([
                            tool_name,
                            description,
                            category
                        ])
                    
                    # 显示表格
                    await self.interface.table(headers, rows, "工具列表")
            
            elif tools_command == "info":
                tool_name = args.get("tool_name")
                
                if not tool_name:
                    print("错误: 工具名称不能为空")
                    return
                
                # 获取工具信息
                tool_info = await self.tool_manager.get_tool_info(tool_name)
                
                if not tool_info:
                    print(f"错误: 工具 {tool_name} 不存在")
                    return
                
                # 显示工具信息
                print(f"工具名称: {tool_info.get('name', '未知')}")
                print(f"描述: {tool_info.get('description', '无')}")
                print(f"类别: {tool_info.get('category', '未知')}")
                print(f"版本: {tool_info.get('version', '未知')}")
                
                # 显示参数
                parameters = tool_info.get("parameters", [])
                if parameters:
                    print("\n参数:")
                    for param in parameters:
                        param_name = param.get("name", "未知")
                        param_type = param.get("type", "未知")
                        param_description = param.get("description", "无")
                        param_required = param.get("required", False)
                        
                        print(f"  - {param_name} ({param_type}){' *' if param_required else ''}")
                        print(f"    描述: {param_description}")
            
            else:
                print(f"未知工具命令: {tools_command}")
                self.cli_parser.print_help("tools")
        except Exception as e:
            print(f"工具管理失败: {str(e)}")
            self.logger.error(f"工具管理失败: {str(e)}")
    
    async def _handle_version_command(self, args: Dict[str, Any]):
        """
        处理version命令
        
        Args:
            args: 命令参数
        """
        try:
            # 获取版本信息
            version = await self.config_manager.get("version", "1.0.0")
            
            print(f"智能Agent系统 v{version}")
            print("Copyright (c) 2025")
        except Exception as e:
            print(f"获取版本信息失败: {str(e)}")
            self.logger.error(f"获取版本信息失败: {str(e)}")
    
    async def _handle_help_command(self, args: Dict[str, Any]):
        """
        处理help命令
        
        Args:
            args: 命令参数
        """
        try:
            command = args.get("command")
            
            # 显示帮助信息
            self.cli_parser.print_help(command)
        except Exception as e:
            print(f"显示帮助信息失败: {str(e)}")
            self.logger.error(f"显示帮助信息失败: {str(e)}")
    
    async def _progress_callback(self, task_id: int, current: int, total: int, 
                                status: str, sub_tasks: List[Dict]):
        """
        进度回调函数
        
        Args:
            task_id: 任务ID
            current: 当前进度
            total: 总进度
            status: 状态
            sub_tasks: 子任务列表
        """
        try:
            # 更新进度显示
            if not self.progress_display.display_running:
                await self.progress_display.start_progress(task_id, f"任务 {task_id}", total)
            
            await self.progress_display.update_progress(
                current=current,
                status=status,
                sub_tasks=sub_tasks
            )
            
            # 如果任务完成，停止进度显示
            if status in ["completed", "failed", "stopped"]:
                await self.progress_display.stop_progress(status)
        except Exception as e:
            self.logger.error(f"进度回调失败: {str(e)}")
    
    async def run_interactive(self):
        """运行交互式模式"""
        try:
            self.interactive_mode = True
            self.running = True
            
            # 显示欢迎信息
            await self.interface.clear()
            await self.interface.message("欢迎使用智能Agent系统", "success")
            await self.interface.message("输入 'help' 查看可用命令，输入 'exit' 退出", "info")
            print()
            
            # 主循环
            while self.running:
                try:
                    # 获取用户输入
                    user_input = await self.interface.prompt("agent> ")
                    
                    if not user_input:
                        continue
                    
                    # 解析命令
                    args = user_input.split()
                    
                    if not args:
                        continue
                    
                    # 处理特殊命令
                    if args[0] in ["exit", "quit"]:
                        await self._handle_exit_command()
                    elif args[0] == "clear":
                        await self.interface.clear()
                    elif args[0] == "help":
                        await self._handle_interactive_help_command()
                    else:
                        # 处理其他命令
                        await self.run(args)
                except KeyboardInterrupt:
                    print("\n使用 'exit' 命令退出")
                except Exception as e:
                    print(f"错误: {str(e)}")
                    self.logger.error(f"交互式模式出错: {str(e)}")
        except Exception as e:
            raise CLIApplicationError(f"运行交互式模式失败: {str(e)}")
        finally:
            self.interactive_mode = False
            self.running = False
    
    async def _handle_exit_command(self):
        """处理退出命令"""
        try:
            if await self.interface.confirm("确定要退出吗?"):
                self.running = False
                await self.interface.message("再见!", "success")
        except Exception as e:
            self.logger.error(f"处理退出命令失败: {str(e)}")
    
    async def _handle_interactive_help_command(self):
        """处理交互式帮助命令"""
        try:
            help_text = """
可用命令:
  run <任务描述>           - 运行任务
  status --task-id <ID>   - 查看任务状态
  list [选项]             - 列出任务
  stop --task-id <ID>     - 停止任务
  pause --task-id <ID>    - 暂停任务
  resume --task-id <ID>   - 恢复任务
  retry --task-id <ID>    - 重试任务
  result --task-id <ID>   - 查看任务结果
  config <子命令>         - 配置管理
  stats [选项]            - 统计信息
  knowledge <子命令>     - 知识库管理
  tools <子命令>         - 工具管理
  version                - 显示版本信息
  clear                  - 清屏
  help                   - 显示帮助
  exit/quit              - 退出

使用 'help <命令>' 查看特定命令的详细帮助。
            """
            
            print(help_text)
        except Exception as e:
            print(f"显示帮助信息失败: {str(e)}")
            self.logger.error(f"显示帮助信息失败: {str(e)}")
    
    async def shutdown(self):
        """关闭应用程序"""
        try:
            # 停止进度显示
            if self.progress_display.display_running:
                await self.progress_display.stop_progress()
            
            # 关闭Agent管理器
            await self.agent_manager.shutdown()
            
            # 关闭工具管理器
            await self.tool_manager.shutdown()
            
            # 关闭知识管理器
            await self.knowledge_manager.shutdown()
            
            # 关闭数据库管理器
            await self.db_manager.shutdown()
            
            self.logger.info("命令行应用程序已关闭")
        except Exception as e:
            raise CLIApplicationError(f"关闭应用程序失败: {str(e)}")