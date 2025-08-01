"""
进度显示器

负责显示任务执行进度，
包括进度条、状态更新和时间统计等功能。
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable

from ..utils.exceptions import ProgressDisplayError


class ProgressDisplay:
    """进度显示器，负责显示任务执行进度"""
    
    def __init__(self, interactive_interface):
        """
        初始化进度显示器
        
        Args:
            interactive_interface: 交互式界面
        """
        self.interface = interactive_interface
        
        # 进度显示配置
        self.config = {
            "refresh_interval": 0.5,  # 刷新间隔（秒）
            "show_time": True,        # 显示时间
            "show_percentage": True,  # 显示百分比
            "show_bar": True,         # 显示进度条
            "bar_width": 50,          # 进度条宽度
            "show_details": True,     # 显示详细信息
            "max_detail_lines": 10    # 最大详细行数
        }
        
        # 当前进度信息
        self.current_progress = {
            "task_id": None,
            "task_name": "",
            "status": "pending",
            "current": 0,
            "total": 0,
            "percentage": 0,
            "start_time": None,
            "end_time": None,
            "elapsed_time": 0,
            "estimated_time": 0,
            "sub_tasks": [],
            "active_sub_tasks": [],
            "completed_sub_tasks": [],
            "failed_sub_tasks": []
        }
        
        # 进度历史
        self.progress_history = []
        
        # 进度显示任务
        self.display_task = None
        self.display_running = False
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("进度显示器初始化完成")
    
    async def initialize(self):
        """初始化进度显示器"""
        try:
            self.logger.info("进度显示器初始化完成")
        except Exception as e:
            raise ProgressDisplayError(f"初始化进度显示器失败: {str(e)}")
    
    async def start_progress(self, task_id: int, task_name: str, total: int = 100) -> bool:
        """
        开始显示进度
        
        Args:
            task_id: 任务ID
            task_name: 任务名称
            total: 总进度
            
        Returns:
            开始是否成功
        """
        try:
            # 停止当前进度显示
            if self.display_running:
                await self.stop_progress()
            
            # 初始化进度信息
            self.current_progress = {
                "task_id": task_id,
                "task_name": task_name,
                "status": "running",
                "current": 0,
                "total": total,
                "percentage": 0,
                "start_time": datetime.now(),
                "end_time": None,
                "elapsed_time": 0,
                "estimated_time": 0,
                "sub_tasks": [],
                "active_sub_tasks": [],
                "completed_sub_tasks": [],
                "failed_sub_tasks": []
            }
            
            # 启动进度显示任务
            self.display_running = True
            self.display_task = asyncio.create_task(self._display_loop())
            
            self.logger.info(f"开始显示任务 {task_id} 的进度")
            return True
        except Exception as e:
            raise ProgressDisplayError(f"开始显示进度失败: {str(e)}")
    
    async def update_progress(self, current: int, status: Optional[str] = None, 
                            sub_tasks: Optional[List[Dict]] = None) -> bool:
        """
        更新进度
        
        Args:
            current: 当前进度
            status: 状态
            sub_tasks: 子任务列表
            
        Returns:
            更新是否成功
        """
        try:
            if not self.display_running:
                return False
            
            # 更新进度信息
            self.current_progress["current"] = current
            self.current_progress["percentage"] = int(current * 100 / self.current_progress["total"]) if self.current_progress["total"] > 0 else 0
            
            if status:
                self.current_progress["status"] = status
            
            # 更新子任务信息
            if sub_tasks:
                self.current_progress["sub_tasks"] = sub_tasks
                
                # 更新子任务状态
                self.current_progress["active_sub_tasks"] = [
                    st for st in sub_tasks if st.get("status") in ["running", "ready"]
                ]
                self.current_progress["completed_sub_tasks"] = [
                    st for st in sub_tasks if st.get("status") == "completed"
                ]
                self.current_progress["failed_sub_tasks"] = [
                    st for st in sub_tasks if st.get("status") == "failed"
                ]
            
            # 更新时间信息
            if self.current_progress["start_time"]:
                now = datetime.now()
                self.current_progress["elapsed_time"] = (now - self.current_progress["start_time"]).total_seconds()
                
                # 估算剩余时间
                if self.current_progress["percentage"] > 0:
                    time_per_unit = self.current_progress["elapsed_time"] / self.current_progress["percentage"]
                    remaining_percentage = 100 - self.current_progress["percentage"]
                    self.current_progress["estimated_time"] = time_per_unit * remaining_percentage
            
            return True
        except Exception as e:
            raise ProgressDisplayError(f"更新进度失败: {str(e)}")
    
    async def stop_progress(self, status: str = "completed") -> bool:
        """
        停止显示进度
        
        Args:
            status: 最终状态
            
        Returns:
            停止是否成功
        """
        try:
            if not self.display_running:
                return False
            
            # 更新进度信息
            self.current_progress["status"] = status
            self.current_progress["end_time"] = datetime.now()
            
            if self.current_progress["start_time"]:
                self.current_progress["elapsed_time"] = (
                    self.current_progress["end_time"] - self.current_progress["start_time"]
                ).total_seconds()
            
            # 停止进度显示任务
            self.display_running = False
            
            if self.display_task:
                self.display_task.cancel()
                try:
                    await self.display_task
                except asyncio.CancelledError:
                    pass
                self.display_task = None
            
            # 显示最终进度
            await self._display_progress()
            
            # 添加到历史记录
            self.progress_history.append(dict(self.current_progress))
            
            self.logger.info(f"停止显示任务 {self.current_progress['task_id']} 的进度")
            return True
        except Exception as e:
            raise ProgressDisplayError(f"停止显示进度失败: {str(e)}")
    
    async def _display_loop(self):
        """进度显示循环"""
        try:
            while self.display_running:
                # 显示进度
                await self._display_progress()
                
                # 等待刷新间隔
                await asyncio.sleep(self.config["refresh_interval"])
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"进度显示循环出错: {str(e)}")
    
    async def _display_progress(self):
        """显示进度"""
        try:
            # 清屏
            if self.config["show_details"]:
                await self.interface.clear()
            
            # 构建进度信息
            progress_info = []
            
            # 添加任务名称
            progress_info.append(f"任务: {self.current_progress['task_name']}")
            
            # 添加状态
            status_color = {
                "pending": "yellow",
                "running": "blue",
                "paused": "yellow",
                "completed": "green",
                "failed": "red",
                "stopped": "yellow"
            }.get(self.current_progress["status"], "white")
            
            progress_info.append(
                f"状态: {self.interface.colorize(self.current_progress['status'], status_color)}"
            )
            
            # 添加进度条
            if self.config["show_bar"]:
                bar_width = self.config["bar_width"]
                filled_width = int(bar_width * self.current_progress["percentage"] / 100)
                bar = "=" * filled_width + "-" * (bar_width - filled_width)
                
                if self.config["show_percentage"]:
                    progress_info.append(f"进度: [{bar}] {self.current_progress['percentage']}%")
                else:
                    progress_info.append(f"进度: [{bar}]")
            else:
                if self.config["show_percentage"]:
                    progress_info.append(f"进度: {self.current_progress['percentage']}%")
            
            # 添加时间信息
            if self.config["show_time"] and self.current_progress["start_time"]:
                # 已用时间
                elapsed_str = self._format_time(self.current_progress["elapsed_time"])
                progress_info.append(f"已用时间: {elapsed_str}")
                
                # 预计剩余时间
                if self.current_progress["estimated_time"] > 0:
                    estimated_str = self._format_time(self.current_progress["estimated_time"])
                    progress_info.append(f"预计剩余: {estimated_str}")
            
            # 显示进度信息
            print("\n".join(progress_info))
            
            # 显示详细信息
            if self.config["show_details"]:
                await self._display_details()
        except Exception as e:
            raise ProgressDisplayError(f"显示进度失败: {str(e)}")
    
    async def _display_details(self):
        """显示详细信息"""
        try:
            details = []
            
            # 添加子任务统计
            total_sub_tasks = len(self.current_progress["sub_tasks"])
            active_sub_tasks = len(self.current_progress["active_sub_tasks"])
            completed_sub_tasks = len(self.current_progress["completed_sub_tasks"])
            failed_sub_tasks = len(self.current_progress["failed_sub_tasks"])
            
            if total_sub_tasks > 0:
                details.append(f"\n子任务统计:")
                details.append(f"  总计: {total_sub_tasks}")
                details.append(f"  进行中: {self.interface.colorize(str(active_sub_tasks), 'blue')}")
                details.append(f"  已完成: {self.interface.colorize(str(completed_sub_tasks), 'green')}")
                details.append(f"  失败: {self.interface.colorize(str(failed_sub_tasks), 'red')}")
            
            # 添加活动子任务
            if self.current_progress["active_sub_tasks"]:
                details.append(f"\n活动子任务:")
                
                for i, sub_task in enumerate(self.current_progress["active_sub_tasks"][:self.config["max_detail_lines"]]):
                    sub_task_name = sub_task.get("name", f"子任务 {sub_task.get('id', '')}")
                    details.append(f"  {i+1}. {sub_task_name}")
                
                if len(self.current_progress["active_sub_tasks"]) > self.config["max_detail_lines"]:
                    details.append(f"  ... 还有 {len(self.current_progress['active_sub_tasks']) - self.config['max_detail_lines']} 个活动子任务")
            
            # 添加最近完成的子任务
            if self.current_progress["completed_sub_tasks"]:
                details.append(f"\n最近完成的子任务:")
                
                # 按完成时间排序
                completed_sorted = sorted(
                    self.current_progress["completed_sub_tasks"],
                    key=lambda x: x.get("end_time", ""),
                    reverse=True
                )
                
                for i, sub_task in enumerate(completed_sorted[:self.config["max_detail_lines"]]):
                    sub_task_name = sub_task.get("name", f"子任务 {sub_task.get('id', '')}")
                    details.append(f"  {i+1}. {sub_task_name}")
                
                if len(self.current_progress["completed_sub_tasks"]) > self.config["max_detail_lines"]:
                    details.append(f"  ... 还有 {len(self.current_progress['completed_sub_tasks']) - self.config['max_detail_lines']} 个已完成子任务")
            
            # 添加失败的子任务
            if self.current_progress["failed_sub_tasks"]:
                details.append(f"\n失败的子任务:")
                
                for i, sub_task in enumerate(self.current_progress["failed_sub_tasks"][:self.config["max_detail_lines"]]):
                    sub_task_name = sub_task.get("name", f"子任务 {sub_task.get('id', '')}")
                    details.append(f"  {i+1}. {self.interface.colorize(sub_task_name, 'red')}")
                
                if len(self.current_progress["failed_sub_tasks"]) > self.config["max_detail_lines"]:
                    details.append(f"  ... 还有 {len(self.current_progress['failed_sub_tasks']) - self.config['max_detail_lines']} 个失败子任务")
            
            # 显示详细信息
            if details:
                print("\n".join(details))
        except Exception as e:
            raise ProgressDisplayError(f"显示详细信息失败: {str(e)}")
    
    def _format_time(self, seconds: float) -> str:
        """
        格式化时间
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化后的时间字符串
        """
        try:
            if seconds < 0:
                return "未知"
            
            # 计算时间单位
            hours, remainder = divmod(int(seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            # 构建时间字符串
            time_parts = []
            
            if hours > 0:
                time_parts.append(f"{hours}小时")
            
            if minutes > 0:
                time_parts.append(f"{minutes}分钟")
            
            if seconds > 0 or not time_parts:
                time_parts.append(f"{seconds}秒")
            
            return "".join(time_parts)
        except Exception as e:
            return "未知"
    
    async def get_progress_summary(self, task_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取进度摘要
        
        Args:
            task_id: 任务ID，如果为None则返回当前进度
            
        Returns:
            进度摘要
        """
        try:
            if task_id is None:
                return dict(self.current_progress)
            
            # 从历史记录中查找
            for progress in self.progress_history:
                if progress["task_id"] == task_id:
                    return dict(progress)
            
            return {}
        except Exception as e:
            raise ProgressDisplayError(f"获取进度摘要失败: {str(e)}")
    
    async def get_progress_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取进度历史
        
        Args:
            limit: 限制数量
            
        Returns:
            进度历史列表
        """
        try:
            # 返回最近的进度历史
            return self.progress_history[-limit:]
        except Exception as e:
            raise ProgressDisplayError(f"获取进度历史失败: {str(e)}")
    
    def set_config(self, key: str, value: Any) -> bool:
        """
        设置配置
        
        Args:
            key: 配置键
            value: 配置值
            
        Returns:
            设置是否成功
        """
        try:
            if key in self.config:
                self.config[key] = value
                self.logger.info(f"设置进度显示配置: {key} = {value}")
                return True
            else:
                self.logger.warning(f"未知的进度显示配置键: {key}")
                return False
        except Exception as e:
            raise ProgressDisplayError(f"设置配置失败: {str(e)}")
    
    def get_config(self, key: str) -> Any:
        """
        获取配置
        
        Args:
            key: 配置键
            
        Returns:
            配置值
        """
        try:
            return self.config.get(key)
        except Exception as e:
            raise ProgressDisplayError(f"获取配置失败: {str(e)}")
    
    async def export_progress(self, file_path: str, task_id: Optional[int] = None) -> bool:
        """
        导出进度信息
        
        Args:
            file_path: 文件路径
            task_id: 任务ID，如果为None则导出当前进度
            
        Returns:
            导出是否成功
        """
        try:
            # 获取进度信息
            if task_id is None:
                progress_data = dict(self.current_progress)
            else:
                progress_data = None
                for progress in self.progress_history:
                    if progress["task_id"] == task_id:
                        progress_data = dict(progress)
                        break
                
                if not progress_data:
                    raise ProgressDisplayError(f"未找到任务 {task_id} 的进度信息")
            
            # 转换时间对象为字符串
            for key in ["start_time", "end_time"]:
                if progress_data.get(key) and isinstance(progress_data[key], datetime):
                    progress_data[key] = progress_data[key].isoformat()
            
            # 写入文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"导出进度信息到 {file_path}")
            return True
        except Exception as e:
            raise ProgressDisplayError(f"导出进度信息失败: {str(e)}")