"""
命令行解析器

负责解析命令行参数和命令，
并提供命令帮助信息。
"""

import argparse
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Union, Tuple

from ..utils.exceptions import CLIParserError


class CLIParser:
    """命令行解析器，负责解析命令行参数和命令"""
    
    def __init__(self):
        """初始化命令行解析器"""
        self.parser = argparse.ArgumentParser(
            description="智能Agent系统",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例:
  %(prog)s run "创建一个用户管理系统"
  %(prog)s status --task-id 123
  %(prog)s list --status completed --limit 10
  %(prog)s stop --task-id 123
  %(prog)s config --set database.url "sqlite:///agent.db"
            """
        )
        
        self.subparsers = self.parser.add_subparsers(
            dest="command",
            help="可用命令",
            metavar="COMMAND"
        )
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 初始化命令
        self._init_commands()
    
    def _init_commands(self):
        """初始化命令"""
        try:
            # run 命令 - 运行任务
            run_parser = self.subparsers.add_parser(
                "run",
                help="运行任务",
                description="运行一个新的任务"
            )
            run_parser.add_argument(
                "task_description",
                help="任务描述"
            )
            run_parser.add_argument(
                "--user-id",
                type=int,
                help="用户ID"
            )
            run_parser.add_argument(
                "--context",
                type=str,
                help="任务上下文JSON字符串"
            )
            run_parser.add_argument(
                "--async",
                action="store_true",
                help="异步运行任务"
            )
            
            # status 命令 - 查看任务状态
            status_parser = self.subparsers.add_parser(
                "status",
                help="查看任务状态",
                description="查看指定任务的状态"
            )
            status_parser.add_argument(
                "--task-id",
                type=int,
                required=True,
                help="任务ID"
            )
            status_parser.add_argument(
                "--verbose",
                action="store_true",
                help="显示详细信息"
            )
            
            # list 命令 - 列出任务
            list_parser = self.subparsers.add_parser(
                "list",
                help="列出任务",
                description="列出符合条件的任务"
            )
            list_parser.add_argument(
                "--user-id",
                type=int,
                help="用户ID"
            )
            list_parser.add_argument(
                "--status",
                choices=["pending", "running", "paused", "completed", "failed", "stopped"],
                help="任务状态"
            )
            list_parser.add_argument(
                "--limit",
                type=int,
                default=20,
                help="限制数量"
            )
            list_parser.add_argument(
                "--offset",
                type=int,
                default=0,
                help="偏移量"
            )
            list_parser.add_argument(
                "--format",
                choices=["table", "json"],
                default="table",
                help="输出格式"
            )
            
            # stop 命令 - 停止任务
            stop_parser = self.subparsers.add_parser(
                "stop",
                help="停止任务",
                description="停止正在运行的任务"
            )
            stop_parser.add_argument(
                "--task-id",
                type=int,
                required=True,
                help="任务ID"
            )
            stop_parser.add_argument(
                "--reason",
                type=str,
                default="用户请求停止",
                help="停止原因"
            )
            
            # pause 命令 - 暂停任务
            pause_parser = self.subparsers.add_parser(
                "pause",
                help="暂停任务",
                description="暂停正在运行的任务"
            )
            pause_parser.add_argument(
                "--task-id",
                type=int,
                required=True,
                help="任务ID"
            )
            
            # resume 命令 - 恢复任务
            resume_parser = self.subparsers.add_parser(
                "resume",
                help="恢复任务",
                description="恢复已暂停的任务"
            )
            resume_parser.add_argument(
                "--task-id",
                type=int,
                required=True,
                help="任务ID"
            )
            
            # retry 命令 - 重试任务
            retry_parser = self.subparsers.add_parser(
                "retry",
                help="重试任务",
                description="重试失败的任务"
            )
            retry_parser.add_argument(
                "--task-id",
                type=int,
                required=True,
                help="任务ID"
            )
            
            # result 命令 - 查看任务结果
            result_parser = self.subparsers.add_parser(
                "result",
                help="查看任务结果",
                description="查看指定任务的执行结果"
            )
            result_parser.add_argument(
                "--task-id",
                type=int,
                required=True,
                help="任务ID"
            )
            result_parser.add_argument(
                "--format",
                choices=["text", "json"],
                default="text",
                help="输出格式"
            )
            
            # config 命令 - 配置管理
            config_parser = self.subparsers.add_parser(
                "config",
                help="配置管理",
                description="管理系统配置"
            )
            config_subparsers = config_parser.add_subparsers(
                dest="config_command",
                help="配置命令",
                metavar="COMMAND"
            )
            
            # config get 命令 - 获取配置
            config_get_parser = config_subparsers.add_parser(
                "get",
                help="获取配置值"
            )
            config_get_parser.add_argument(
                "key",
                help="配置键"
            )
            
            # config set 命令 - 设置配置
            config_set_parser = config_subparsers.add_parser(
                "set",
                help="设置配置值"
            )
            config_set_parser.add_argument(
                "key",
                help="配置键"
            )
            config_set_parser.add_argument(
                "value",
                help="配置值"
            )
            
            # config list 命令 - 列出配置
            config_list_parser = config_subparsers.add_parser(
                "list",
                help="列出所有配置"
            )
            
            # stats 命令 - 统计信息
            stats_parser = self.subparsers.add_parser(
                "stats",
                help="统计信息",
                description="显示系统统计信息"
            )
            stats_parser.add_argument(
                "--days",
                type=int,
                default=30,
                help="统计天数"
            )
            stats_parser.add_argument(
                "--type",
                choices=["task", "tool", "validation", "all"],
                default="all",
                help="统计类型"
            )
            
            # knowledge 命令 - 知识库管理
            knowledge_parser = self.subparsers.add_parser(
                "knowledge",
                help="知识库管理",
                description="管理系统知识库"
            )
            knowledge_subparsers = knowledge_parser.add_subparsers(
                dest="knowledge_command",
                help="知识库命令",
                metavar="COMMAND"
            )
            
            # knowledge add 命令 - 添加知识
            knowledge_add_parser = knowledge_subparsers.add_parser(
                "add",
                help="添加知识"
            )
            knowledge_add_parser.add_argument(
                "--file",
                type=str,
                required=True,
                help="知识文件路径"
            )
            knowledge_add_parser.add_argument(
                "--source",
                type=str,
                help="知识来源"
            )
            knowledge_add_parser.add_argument(
                "--tags",
                type=str,
                help="知识标签，逗号分隔"
            )
            
            # knowledge search 命令 - 搜索知识
            knowledge_search_parser = knowledge_subparsers.add_parser(
                "search",
                help="搜索知识"
            )
            knowledge_search_parser.add_argument(
                "query",
                help="搜索查询"
            )
            knowledge_search_parser.add_argument(
                "--limit",
                type=int,
                default=10,
                help="结果数量限制"
            )
            
            # knowledge list 命令 - 列出知识
            knowledge_list_parser = knowledge_subparsers.add_parser(
                "list",
                help="列出知识"
            )
            knowledge_list_parser.add_argument(
                "--source",
                type=str,
                help="知识来源"
            )
            knowledge_list_parser.add_argument(
                "--tags",
                type=str,
                help="知识标签，逗号分隔"
            )
            knowledge_list_parser.add_argument(
                "--limit",
                type=int,
                default=20,
                help="结果数量限制"
            )
            
            # tools 命令 - 工具管理
            tools_parser = self.subparsers.add_parser(
                "tools",
                help="工具管理",
                description="管理系统工具"
            )
            tools_subparsers = tools_parser.add_subparsers(
                dest="tools_command",
                help="工具命令",
                metavar="COMMAND"
            )
            
            # tools list 命令 - 列出工具
            tools_list_parser = tools_subparsers.add_parser(
                "list",
                help="列出可用工具"
            )
            tools_list_parser.add_argument(
                "--format",
                choices=["table", "json"],
                default="table",
                help="输出格式"
            )
            
            # tools info 命令 - 工具信息
            tools_info_parser = tools_subparsers.add_parser(
                "info",
                help="显示工具信息"
            )
            tools_info_parser.add_argument(
                "tool_name",
                help="工具名称"
            )
            
            # version 命令 - 显示版本
            version_parser = self.subparsers.add_parser(
                "version",
                help="显示版本信息"
            )
            
            # help 命令 - 显示帮助
            help_parser = self.subparsers.add_parser(
                "help",
                help="显示帮助信息"
            )
            help_parser.add_argument(
                "command",
                nargs="?",
                help="命令名称"
            )
            
            self.logger.info("命令行解析器初始化完成")
        except Exception as e:
            raise CLIParserError(f"初始化命令行解析器失败: {str(e)}")
    
    def parse_args(self, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        解析命令行参数
        
        Args:
            args: 命令行参数列表，如果为None则使用sys.argv[1:]
            
        Returns:
            解析后的参数字典
        """
        try:
            if args is None:
                args = sys.argv[1:]
            
            # 解析参数
            parsed_args = self.parser.parse_args(args)
            
            # 转换为字典
            args_dict = vars(parsed_args)
            
            # 处理特殊参数
            if "context" in args_dict and args_dict["context"]:
                try:
                    args_dict["context"] = json.loads(args_dict["context"])
                except json.JSONDecodeError:
                    raise CLIParserError(f"无效的JSON上下文: {args_dict['context']}")
            
            # 处理标签参数
            if "tags" in args_dict and args_dict["tags"]:
                args_dict["tags"] = [tag.strip() for tag in args_dict["tags"].split(",")]
            
            return args_dict
        except Exception as e:
            raise CLIParserError(f"解析命令行参数失败: {str(e)}")
    
    def print_help(self, command: Optional[str] = None):
        """
        打印帮助信息
        
        Args:
            command: 命令名称，如果为None则打印总体帮助
        """
        try:
            if command:
                # 打印特定命令的帮助
                if command in self.subparsers.choices:
                    self.subparsers.choices[command].print_help()
                else:
                    print(f"未知命令: {command}")
                    self.parser.print_help()
            else:
                # 打印总体帮助
                self.parser.print_help()
        except Exception as e:
            raise CLIParserError(f"打印帮助信息失败: {str(e)}")
    
    def get_command_help(self, command: str) -> str:
        """
        获取命令帮助信息
        
        Args:
            command: 命令名称
            
        Returns:
            帮助信息字符串
        """
        try:
            if command in self.subparsers.choices:
                # 获取子解析器
                subparser = self.subparsers.choices[command]
                
                # 获取帮助信息
                import io
                buffer = io.StringIO()
                subparser.print_help(buffer)
                help_text = buffer.getvalue()
                buffer.close()
                
                return help_text
            else:
                return f"未知命令: {command}"
        except Exception as e:
            raise CLIParserError(f"获取命令帮助信息失败: {str(e)}")
    
    def validate_args(self, args_dict: Dict[str, Any]) -> bool:
        """
        验证参数
        
        Args:
            args_dict: 参数字典
            
        Returns:
            验证是否通过
        """
        try:
            command = args_dict.get("command")
            
            if not command:
                print("错误: 未指定命令")
                return False
            
            # 根据命令验证参数
            if command == "run":
                if not args_dict.get("task_description"):
                    print("错误: 未指定任务描述")
                    return False
            
            elif command == "status":
                if not args_dict.get("task_id"):
                    print("错误: 未指定任务ID")
                    return False
            
            elif command == "stop":
                if not args_dict.get("task_id"):
                    print("错误: 未指定任务ID")
                    return False
            
            elif command == "pause":
                if not args_dict.get("task_id"):
                    print("错误: 未指定任务ID")
                    return False
            
            elif command == "resume":
                if not args_dict.get("task_id"):
                    print("错误: 未指定任务ID")
                    return False
            
            elif command == "retry":
                if not args_dict.get("task_id"):
                    print("错误: 未指定任务ID")
                    return False
            
            elif command == "result":
                if not args_dict.get("task_id"):
                    print("错误: 未指定任务ID")
                    return False
            
            elif command == "config":
                config_command = args_dict.get("config_command")
                if not config_command:
                    print("错误: 未指定配置命令")
                    return False
                
                if config_command == "get" and not args_dict.get("key"):
                    print("错误: 未指定配置键")
                    return False
                
                if config_command == "set" and (not args_dict.get("key") or not args_dict.get("value")):
                    print("错误: 未指定配置键或值")
                    return False
            
            elif command == "knowledge":
                knowledge_command = args_dict.get("knowledge_command")
                if not knowledge_command:
                    print("错误: 未指定知识库命令")
                    return False
                
                if knowledge_command == "add" and not args_dict.get("file"):
                    print("错误: 未指定知识文件路径")
                    return False
                
                if knowledge_command == "search" and not args_dict.get("query"):
                    print("错误: 未指定搜索查询")
                    return False
            
            elif command == "tools":
                tools_command = args_dict.get("tools_command")
                if not tools_command:
                    print("错误: 未指定工具命令")
                    return False
                
                if tools_command == "info" and not args_dict.get("tool_name"):
                    print("错误: 未指定工具名称")
                    return False
            
            return True
        except Exception as e:
            raise CLIParserError(f"验证参数失败: {str(e)}")
    
    def format_args(self, args_dict: Dict[str, Any]) -> str:
        """
        格式化参数为字符串
        
        Args:
            args_dict: 参数字典
            
        Returns:
            格式化后的字符串
        """
        try:
            # 过滤掉None值
            filtered_args = {k: v for k, v in args_dict.items() if v is not None}
            
            # 转换为JSON字符串
            return json.dumps(filtered_args, indent=2, ensure_ascii=False)
        except Exception as e:
            raise CLIParserError(f"格式化参数失败: {str(e)}")