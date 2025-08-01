"""
交互式界面

负责处理用户交互，包括输入提示、
确认对话框和菜单选择等功能。
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable

from ..utils.exceptions import InteractiveInterfaceError


class InteractiveInterface:
    """交互式界面，负责处理用户交互"""
    
    def __init__(self):
        """初始化交互式界面"""
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 颜色代码
        self.colors = {
            "reset": "\033[0m",
            "red": "\033[31m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "blue": "\033[34m",
            "magenta": "\033[35m",
            "cyan": "\033[36m",
            "white": "\033[37m",
            "bold": "\033[1m",
            "underline": "\033[4m"
        }
        
        # 检查是否支持颜色
        self.supports_color = sys.stdout.isatty() and os.environ.get("TERM") != "dumb"
        
        # 事件处理器
        self.event_handlers = {}
        
        # 历史记录
        self.history = []
        self.history_index = 0
        
        # 自动完成
        self.completions = {}
        
        self.logger.info("交互式界面初始化完成")
    
    async def initialize(self):
        """初始化交互式界面"""
        try:
            # 检查终端支持
            self._check_terminal_support()
            
            # 初始化历史记录
            self._init_history()
            
            # 初始化自动完成
            self._init_completions()
            
            self.logger.info("交互式界面初始化完成")
        except Exception as e:
            raise InteractiveInterfaceError(f"初始化交互式界面失败: {str(e)}")
    
    def _check_terminal_support(self):
        """检查终端支持"""
        try:
            # 检查是否支持颜色
            if not self.supports_color:
                self.logger.info("终端不支持颜色输出")
            
            # 检查是否支持输入控制
            try:
                import termios
                import tty
                self._has_termios = True
            except ImportError:
                self._has_termios = False
                self.logger.info("系统不支持termios模块，某些交互功能可能不可用")
        except Exception as e:
            raise InteractiveInterfaceError(f"检查终端支持失败: {str(e)}")
    
    def _init_history(self):
        """初始化历史记录"""
        try:
            # 从文件加载历史记录
            history_file = os.path.expanduser("~/.agent_history")
            
            if os.path.exists(history_file):
                with open(history_file, "r", encoding="utf-8") as f:
                    self.history = [line.strip() for line in f.readlines() if line.strip()]
            
            self.history_index = len(self.history)
        except Exception as e:
            self.logger.warning(f"初始化历史记录失败: {str(e)}")
            self.history = []
            self.history_index = 0
    
    def _save_history(self):
        """保存历史记录"""
        try:
            history_file = os.path.expanduser("~/.agent_history")
            
            with open(history_file, "w", encoding="utf-8") as f:
                for item in self.history:
                    f.write(f"{item}\n")
        except Exception as e:
            self.logger.warning(f"保存历史记录失败: {str(e)}")
    
    def _init_completions(self):
        """初始化自动完成"""
        try:
            # 命令自动完成
            self.completions["commands"] = [
                "run", "status", "list", "stop", "pause", "resume", 
                "retry", "result", "config", "stats", "knowledge", "tools", "help", "exit", "quit"
            ]
            
            # 配置自动完成
            self.completions["config"] = ["get", "set", "list"]
            
            # 知识库自动完成
            self.completions["knowledge"] = ["add", "search", "list"]
            
            # 工具自动完成
            self.completions["tools"] = ["list", "info"]
        except Exception as e:
            self.logger.warning(f"初始化自动完成失败: {str(e)}")
            self.completions = {}
    
    def colorize(self, text: str, color: str) -> str:
        """
        为文本添加颜色
        
        Args:
            text: 文本
            color: 颜色名称
            
        Returns:
            带颜色的文本
        """
        if not self.supports_color or color not in self.colors:
            return text
        
        return f"{self.colors[color]}{text}{self.colors['reset']}"
    
    async def prompt(self, text: str, default: Optional[str] = None, 
                   password: bool = False, required: bool = False) -> str:
        """
        提示用户输入
        
        Args:
            text: 提示文本
            default: 默认值
            password: 是否为密码输入
            required: 是否为必填项
            
        Returns:
            用户输入
        """
        try:
            # 构建提示
            prompt_text = text
            if default is not None:
                prompt_text += f" [{default}]"
            
            if required:
                prompt_text += " *"
            
            prompt_text += ": "
            
            # 输入循环
            while True:
                # 显示提示
                if password:
                    import getpass
                    user_input = getpass.getpass(prompt_text)
                else:
                    user_input = input(prompt_text)
                
                # 处理默认值
                if not user_input and default is not None:
                    user_input = default
                
                # 检查必填项
                if required and not user_input:
                    print(self.colorize("此为必填项，请输入", "red"))
                    continue
                
                # 添加到历史记录
                if user_input and not password:
                    self._add_to_history(user_input)
                
                return user_input
        except KeyboardInterrupt:
            print("\n" + self.colorize("操作已取消", "yellow"))
            raise InteractiveInterfaceError("用户取消操作")
        except Exception as e:
            raise InteractiveInterfaceError(f"提示用户输入失败: {str(e)}")
    
    async def confirm(self, text: str, default: bool = False) -> bool:
        """
        确认对话框
        
        Args:
            text: 确认文本
            default: 默认值
            
        Returns:
            用户确认结果
        """
        try:
            # 构建提示
            prompt_text = text
            if default:
                prompt_text += " [Y/n]"
            else:
                prompt_text += " [y/N]"
            
            prompt_text += ": "
            
            # 输入循环
            while True:
                # 显示提示
                user_input = input(prompt_text).strip().lower()
                
                # 处理默认值
                if not user_input:
                    return default
                
                # 处理用户输入
                if user_input in ["y", "yes"]:
                    return True
                elif user_input in ["n", "no"]:
                    return False
                else:
                    print(self.colorize("请输入 y/yes 或 n/no", "red"))
        except KeyboardInterrupt:
            print("\n" + self.colorize("操作已取消", "yellow"))
            return default
        except Exception as e:
            raise InteractiveInterfaceError(f"确认对话框失败: {str(e)}")
    
    async def select(self, text: str, options: List[str], 
                    default: Optional[int] = None, multiple: bool = False) -> Union[str, List[str]]:
        """
        选择菜单
        
        Args:
            text: 选择文本
            options: 选项列表
            default: 默认选项索引
            multiple: 是否允许多选
            
        Returns:
            用户选择结果
        """
        try:
            # 显示标题
            print(f"\n{self.colorize(text, 'bold')}")
            
            # 显示选项
            for i, option in enumerate(options):
                option_text = f"{i + 1}. {option}"
                if default is not None and i == default:
                    option_text += " " + self.colorize("(默认)", "yellow")
                
                print(option_text)
            
            # 输入循环
            while True:
                # 构建提示
                if multiple:
                    prompt_text = "请选择选项 (多个选项用逗号分隔)"
                else:
                    prompt_text = "请选择选项"
                
                if default is not None:
                    prompt_text += f" [{default + 1}]"
                
                prompt_text += ": "
                
                # 显示提示
                user_input = input(prompt_text).strip()
                
                # 处理默认值
                if not user_input and default is not None:
                    if multiple:
                        return [options[default]]
                    else:
                        return options[default]
                
                # 处理用户输入
                try:
                    if multiple:
                        # 处理多选
                        indices = [int(idx.strip()) - 1 for idx in user_input.split(",")]
                        
                        # 验证索引
                        valid_indices = []
                        for idx in indices:
                            if 0 <= idx < len(options):
                                valid_indices.append(idx)
                            else:
                                print(self.colorize(f"无效选项: {idx + 1}", "red"))
                        
                        if valid_indices:
                            return [options[idx] for idx in valid_indices]
                        else:
                            print(self.colorize("请选择有效的选项", "red"))
                    else:
                        # 处理单选
                        idx = int(user_input) - 1
                        
                        # 验证索引
                        if 0 <= idx < len(options):
                            return options[idx]
                        else:
                            print(self.colorize(f"无效选项: {user_input}", "red"))
                except ValueError:
                    print(self.colorize("请输入有效的数字", "red"))
        except KeyboardInterrupt:
            print("\n" + self.colorize("操作已取消", "yellow"))
            if multiple:
                return [options[default]] if default is not None else []
            else:
                return options[default] if default is not None else ""
        except Exception as e:
            raise InteractiveInterfaceError(f"选择菜单失败: {str(e)}")
    
    async def menu(self, title: str, items: List[Dict[str, Any]], 
                  key_field: str = "name", value_field: str = "value",
                  default: Optional[str] = None) -> Any:
        """
        菜单选择
        
        Args:
            title: 菜单标题
            items: 菜单项列表
            key_field: 键字段名
            value_field: 值字段名
            default: 默认值
            
        Returns:
            用户选择结果
        """
        try:
            # 显示标题
            print(f"\n{self.colorize(title, 'bold')}")
            
            # 显示选项
            options = []
            default_index = None
            
            for i, item in enumerate(items):
                key = item.get(key_field, str(i))
                value = item.get(value_field, item)
                
                option_text = f"{i + 1}. {key}"
                
                # 检查是否为默认值
                if default is not None and value == default:
                    option_text += " " + self.colorize("(默认)", "yellow")
                    default_index = i
                
                # 显示描述
                if "description" in item:
                    option_text += f" - {item['description']}"
                
                print(option_text)
                options.append(value)
            
            # 输入循环
            while True:
                # 构建提示
                prompt_text = "请选择选项"
                
                if default_index is not None:
                    prompt_text += f" [{default_index + 1}]"
                
                prompt_text += ": "
                
                # 显示提示
                user_input = input(prompt_text).strip()
                
                # 处理默认值
                if not user_input and default_index is not None:
                    return options[default_index]
                
                # 处理用户输入
                try:
                    idx = int(user_input) - 1
                    
                    # 验证索引
                    if 0 <= idx < len(options):
                        return options[idx]
                    else:
                        print(self.colorize(f"无效选项: {user_input}", "red"))
                except ValueError:
                    print(self.colorize("请输入有效的数字", "red"))
        except KeyboardInterrupt:
            print("\n" + self.colorize("操作已取消", "yellow"))
            return default
        except Exception as e:
            raise InteractiveInterfaceError(f"菜单选择失败: {str(e)}")
    
    async def form(self, title: str, fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        表单输入
        
        Args:
            title: 表单标题
            fields: 字段列表
            
        Returns:
            表单数据
        """
        try:
            # 显示标题
            print(f"\n{self.colorize(title, 'bold')}")
            
            # 收集表单数据
            form_data = {}
            
            for field in fields:
                field_name = field.get("name", "")
                field_label = field.get("label", field_name)
                field_type = field.get("type", "text")
                field_default = field.get("default", None)
                field_required = field.get("required", False)
                field_options = field.get("options", [])
                field_description = field.get("description", "")
                
                # 显示字段描述
                if field_description:
                    print(f"  {field_description}")
                
                # 根据字段类型收集数据
                if field_type == "text":
                    value = await self.prompt(
                        f"  {field_label}",
                        default=field_default,
                        required=field_required
                    )
                elif field_type == "password":
                    value = await self.prompt(
                        f"  {field_label}",
                        password=True,
                        required=field_required
                    )
                elif field_type == "confirm":
                    value = await self.confirm(
                        f"  {field_label}",
                        default=field_default if field_default is not None else False
                    )
                elif field_type == "select":
                    value = await self.select(
                        f"  {field_label}",
                        field_options,
                        default=field_options.index(field_default) if field_default in field_options else None
                    )
                elif field_type == "multiselect":
                    value = await self.select(
                        f"  {field_label}",
                        field_options,
                        default=field_options.index(field_default) if field_default in field_options else None,
                        multiple=True
                    )
                else:
                    value = await self.prompt(
                        f"  {field_label}",
                        default=field_default,
                        required=field_required
                    )
                
                form_data[field_name] = value
                
                # 添加空行
                print()
            
            return form_data
        except KeyboardInterrupt:
            print("\n" + self.colorize("操作已取消", "yellow"))
            return {}
        except Exception as e:
            raise InteractiveInterfaceError(f"表单输入失败: {str(e)}")
    
    async def progress(self, text: str, current: int, total: int, 
                      width: int = 50, suffix: str = "") -> None:
        """
        显示进度条
        
        Args:
            text: 进度文本
            current: 当前进度
            total: 总进度
            width: 进度条宽度
            suffix: 后缀文本
        """
        try:
            # 计算进度百分比
            if total == 0:
                percent = 100
            else:
                percent = int(current * 100 / total)
            
            # 构建进度条
            filled_width = int(width * current / total)
            bar = "=" * filled_width + "-" * (width - filled_width)
            
            # 显示进度条
            print(f"\r{text}: [{bar}] {percent}% {suffix}", end="")
            
            # 如果完成，添加换行
            if current >= total:
                print()
        except Exception as e:
            raise InteractiveInterfaceError(f"显示进度条失败: {str(e)}")
    
    async def table(self, headers: List[str], rows: List[List[str]], 
                   title: Optional[str] = None) -> None:
        """
        显示表格
        
        Args:
            headers: 表头列表
            rows: 行数据列表
            title: 表格标题
        """
        try:
            # 计算列宽
            col_widths = [len(header) for header in headers]
            
            for row in rows:
                for i, cell in enumerate(row):
                    if i < len(col_widths):
                        col_widths[i] = max(col_widths[i], len(str(cell)))
            
            # 显示标题
            if title:
                print(f"\n{self.colorize(title, 'bold')}")
            
            # 显示表头
            header_line = "|"
            separator_line = "+"
            
            for i, header in enumerate(headers):
                width = col_widths[i]
                header_line += f" {header.ljust(width)} |"
                separator_line += f"{'-' * (width + 2)}+"
            
            print(separator_line)
            print(header_line)
            print(separator_line)
            
            # 显示行数据
            for row in rows:
                row_line = "|"
                
                for i, cell in enumerate(row):
                    if i < len(col_widths):
                        width = col_widths[i]
                        row_line += f" {str(cell).ljust(width)} |"
                
                print(row_line)
            
            print(separator_line)
        except Exception as e:
            raise InteractiveInterfaceError(f"显示表格失败: {str(e)}")
    
    async def message(self, text: str, level: str = "info") -> None:
        """
        显示消息
        
        Args:
            text: 消息文本
            level: 消息级别
        """
        try:
            # 根据级别选择颜色
            if level == "error":
                color = "red"
                prefix = "错误"
            elif level == "warning":
                color = "yellow"
                prefix = "警告"
            elif level == "success":
                color = "green"
                prefix = "成功"
            else:
                color = "blue"
                prefix = "信息"
            
            # 显示消息
            print(f"{self.colorize(prefix, color)}: {text}")
        except Exception as e:
            raise InteractiveInterfaceError(f"显示消息失败: {str(e)}")
    
    async def clear(self) -> None:
        """清屏"""
        try:
            os.system("cls" if os.name == "nt" else "clear")
        except Exception as e:
            raise InteractiveInterfaceError(f"清屏失败: {str(e)}")
    
    def _add_to_history(self, item: str):
        """添加到历史记录"""
        try:
            # 如果历史记录中已有此项，先删除
            if item in self.history:
                self.history.remove(item)
            
            # 添加到历史记录末尾
            self.history.append(item)
            
            # 限制历史记录长度
            max_history = 1000
            if len(self.history) > max_history:
                self.history = self.history[-max_history:]
            
            # 更新历史索引
            self.history_index = len(self.history)
            
            # 保存历史记录
            self._save_history()
        except Exception as e:
            self.logger.warning(f"添加到历史记录失败: {str(e)}")
    
    def add_event_handler(self, event: str, handler: Callable) -> bool:
        """
        添加事件处理器
        
        Args:
            event: 事件名称
            handler: 处理器函数
            
        Returns:
            添加是否成功
        """
        try:
            if event not in self.event_handlers:
                self.event_handlers[event] = []
            
            self.event_handlers[event].append(handler)
            self.logger.info(f"添加事件处理器: {event}")
            return True
        except Exception as e:
            raise InteractiveInterfaceError(f"添加事件处理器失败: {str(e)}")
    
    async def trigger_event(self, event: str, data: Any = None) -> List[Any]:
        """
        触发事件
        
        Args:
            event: 事件名称
            data: 事件数据
            
        Returns:
            处理结果列表
        """
        try:
            results = []
            
            if event in self.event_handlers:
                for handler in self.event_handlers[event]:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            result = await handler(data)
                        else:
                            result = handler(data)
                        
                        results.append(result)
                    except Exception as e:
                        self.logger.error(f"事件处理器执行失败: {str(e)}")
            
            return results
        except Exception as e:
            raise InteractiveInterfaceError(f"触发事件失败: {str(e)}")