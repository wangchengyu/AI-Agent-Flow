"""
任务历史管理器

负责管理任务历史记录的存储、检索、更新和删除等功能，
提供完整的任务生命周期管理能力。
"""

import json
import pickle
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from .database_manager import DatabaseManager
from ..utils.exceptions import DatabaseError


class TaskHistoryManager:
    """任务历史管理器，负责任务历史记录的管理"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化任务历史管理器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
    
    def create_task(self, user_input: str, subtasks: Optional[List[Dict]] = None) -> int:
        """
        创建新任务
        
        Args:
            user_input: 用户输入
            subtasks: 子任务列表
            
        Returns:
            任务ID
        """
        try:
            # 序列化子任务
            subtasks_json = json.dumps(subtasks) if subtasks else None
            
            # 插入任务记录
            task_id = self.db_manager.execute_insert(
                "INSERT INTO task_history (user_input, subtasks, status) VALUES (?, ?, ?)",
                (user_input, subtasks_json, "pending")
            )
            
            return task_id
        except Exception as e:
            raise DatabaseError(f"创建任务失败: {str(e)}")
    
    def get_task(self, task_id: int) -> Optional[Dict]:
        """
        获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务信息字典，如果不存在则返回None
        """
        try:
            results = self.db_manager.execute_query(
                "SELECT * FROM task_history WHERE task_id = ?",
                (task_id,)
            )
            
            if not results:
                return None
            
            task = results[0]
            
            # 反序列化子任务
            if task["subtasks"]:
                task["subtasks"] = json.loads(task["subtasks"])
            else:
                task["subtasks"] = []
            
            # 反序列化结果
            if task["results"]:
                task["results"] = pickle.loads(task["results"])
            else:
                task["results"] = {}
            
            return task
        except Exception as e:
            raise DatabaseError(f"获取任务失败: {str(e)}")
    
    def update_task_status(self, task_id: int, status: str) -> bool:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            
        Returns:
            更新是否成功
        """
        try:
            # 更新状态和更新时间
            affected_rows = self.db_manager.execute_update(
                "UPDATE task_history SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE task_id = ?",
                (status, task_id)
            )
            
            # 如果状态为完成，更新完成时间
            if status == "completed":
                self.db_manager.execute_update(
                    "UPDATE task_history SET completed_at = CURRENT_TIMESTAMP WHERE task_id = ?",
                    (task_id,)
                )
            
            return affected_rows > 0
        except Exception as e:
            raise DatabaseError(f"更新任务状态失败: {str(e)}")
    
    def update_task_subtasks(self, task_id: int, subtasks: List[Dict]) -> bool:
        """
        更新任务子任务
        
        Args:
            task_id: 任务ID
            subtasks: 子任务列表
            
        Returns:
            更新是否成功
        """
        try:
            # 序列化子任务
            subtasks_json = json.dumps(subtasks)
            
            # 更新子任务和更新时间
            affected_rows = self.db_manager.execute_update(
                "UPDATE task_history SET subtasks = ?, updated_at = CURRENT_TIMESTAMP WHERE task_id = ?",
                (subtasks_json, task_id)
            )
            
            return affected_rows > 0
        except Exception as e:
            raise DatabaseError(f"更新任务子任务失败: {str(e)}")
    
    def update_task_results(self, task_id: int, results: Dict) -> bool:
        """
        更新任务结果
        
        Args:
            task_id: 任务ID
            results: 结果字典
            
        Returns:
            更新是否成功
        """
        try:
            # 序列化结果
            results_blob = pickle.dumps(results)
            
            # 更新结果和更新时间
            affected_rows = self.db_manager.execute_update(
                "UPDATE task_history SET results = ?, updated_at = CURRENT_TIMESTAMP WHERE task_id = ?",
                (results_blob, task_id)
            )
            
            return affected_rows > 0
        except Exception as e:
            raise DatabaseError(f"更新任务结果失败: {str(e)}")
    
    def delete_task(self, task_id: int) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            删除是否成功
        """
        try:
            affected_rows = self.db_manager.execute_update(
                "DELETE FROM task_history WHERE task_id = ?",
                (task_id,)
            )
            
            return affected_rows > 0
        except Exception as e:
            raise DatabaseError(f"删除任务失败: {str(e)}")
    
    def list_tasks(self, limit: int = 20, offset: int = 0, status: Optional[str] = None) -> List[Dict]:
        """
        列出任务
        
        Args:
            limit: 限制数量
            offset: 偏移量
            status: 状态筛选
            
        Returns:
            任务列表
        """
        try:
            query = "SELECT task_id, user_input, status, created_at, updated_at, completed_at FROM task_history"
            params = []
            
            if status:
                query += " WHERE status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            results = self.db_manager.execute_query(query, tuple(params) if params else None)
            
            return results
        except Exception as e:
            raise DatabaseError(f"列出任务失败: {str(e)}")
    
    def get_task_count(self, status: Optional[str] = None) -> int:
        """
        获取任务数量
        
        Args:
            status: 状态筛选
            
        Returns:
            任务数量
        """
        try:
            query = "SELECT COUNT(*) as count FROM task_history"
            params = []
            
            if status:
                query += " WHERE status = ?"
                params.append(status)
            
            results = self.db_manager.execute_query(query, tuple(params) if params else None)
            
            return results[0]["count"]
        except Exception as e:
            raise DatabaseError(f"获取任务数量失败: {str(e)}")
    
    def get_recent_tasks(self, days: int = 7) -> List[Dict]:
        """
        获取最近的任务
        
        Args:
            days: 天数
            
        Returns:
            任务列表
        """
        try:
            query = '''
                SELECT task_id, user_input, status, created_at, updated_at, completed_at 
                FROM task_history 
                WHERE created_at >= datetime('now', '-{} days')
                ORDER BY created_at DESC
            '''.format(days)
            
            results = self.db_manager.execute_query(query)
            
            return results
        except Exception as e:
            raise DatabaseError(f"获取最近任务失败: {str(e)}")
    
    def search_tasks(self, keyword: str, limit: int = 20) -> List[Dict]:
        """
        搜索任务
        
        Args:
            keyword: 关键词
            limit: 限制数量
            
        Returns:
            任务列表
        """
        try:
            query = '''
                SELECT task_id, user_input, status, created_at, updated_at, completed_at 
                FROM task_history 
                WHERE user_input LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            '''
            
            results = self.db_manager.execute_query(query, (f"%{keyword}%", limit))
            
            return results
        except Exception as e:
            raise DatabaseError(f"搜索任务失败: {str(e)}")
    
    def get_task_stats(self) -> Dict:
        """
        获取任务统计信息
        
        Returns:
            统计信息字典
        """
        try:
            stats = {}
            
            # 获取各状态的任务数量
            status_counts = self.db_manager.execute_query(
                "SELECT status, COUNT(*) as count FROM task_history GROUP BY status"
            )
            
            stats["status_counts"] = {item["status"]: item["count"] for item in status_counts}
            
            # 获取总任务数
            total_count = self.db_manager.execute_query("SELECT COUNT(*) as count FROM task_history")
            stats["total_count"] = total_count[0]["count"]
            
            # 获取今日任务数
            today_count = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM task_history WHERE date(created_at) = date('now')"
            )
            stats["today_count"] = today_count[0]["count"]
            
            # 获取本周任务数
            week_count = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM task_history WHERE created_at >= datetime('now', '-7 days')"
            )
            stats["week_count"] = week_count[0]["count"]
            
            # 获取平均完成时间（已完成任务）
            avg_completion_time = self.db_manager.execute_query(
                '''
                SELECT AVG(
                    (julianday(completed_at) - julianday(created_at)) * 24 * 60
                ) as avg_minutes
                FROM task_history 
                WHERE status = 'completed' AND completed_at IS NOT NULL
                '''
            )
            stats["avg_completion_minutes"] = avg_completion_time[0]["avg_minutes"] or 0
            
            return stats
        except Exception as e:
            raise DatabaseError(f"获取任务统计信息失败: {str(e)}")
    
    def cleanup_old_tasks(self, days: int = 30) -> int:
        """
        清理旧任务
        
        Args:
            days: 保留天数
            
        Returns:
            删除的任务数量
        """
        try:
            # 删除指定天数之前的任务
            affected_rows = self.db_manager.execute_update(
                "DELETE FROM task_history WHERE created_at < datetime('now', '-{} days')".format(days)
            )
            
            return affected_rows
        except Exception as e:
            raise DatabaseError(f"清理旧任务失败: {str(e)}")