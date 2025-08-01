"""
工具日志管理器

负责管理工具调用日志的存储、检索、更新和删除等功能，
提供工具使用情况的跟踪和分析能力。
"""

import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from .database_manager import DatabaseManager
from ..utils.exceptions import DatabaseError


class ToolLogManager:
    """工具日志管理器，负责工具调用日志的管理"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化工具日志管理器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
    
    def create_tool_log(self, tool_name: str, action: str, parameters: Optional[Dict] = None,
                       result: Optional[str] = None, status: str = "success",
                       execution_time: Optional[int] = None, task_id: Optional[int] = None) -> int:
        """
        创建工具日志
        
        Args:
            tool_name: 工具名称
            action: 操作名称
            parameters: 参数字典
            result: 结果字符串
            status: 状态
            execution_time: 执行时间（毫秒）
            task_id: 关联的任务ID
            
        Returns:
            日志ID
        """
        try:
            # 序列化参数
            parameters_json = json.dumps(parameters) if parameters else None
            
            # 插入日志记录
            log_id = self.db_manager.execute_insert(
                "INSERT INTO tool_logs (tool_name, action, parameters, result, status, execution_time, task_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (tool_name, action, parameters_json, result, status, execution_time, task_id)
            )
            
            return log_id
        except Exception as e:
            raise DatabaseError(f"创建工具日志失败: {str(e)}")
    
    def get_tool_log(self, log_id: int) -> Optional[Dict]:
        """
        获取工具日志
        
        Args:
            log_id: 日志ID
            
        Returns:
            日志信息字典，如果不存在则返回None
        """
        try:
            results = self.db_manager.execute_query(
                "SELECT * FROM tool_logs WHERE log_id = ?",
                (log_id,)
            )
            
            if not results:
                return None
            
            log = results[0]
            
            # 反序列化参数
            if log["parameters"]:
                log["parameters"] = json.loads(log["parameters"])
            else:
                log["parameters"] = {}
            
            return log
        except Exception as e:
            raise DatabaseError(f"获取工具日志失败: {str(e)}")
    
    def update_tool_log(self, log_id: int, result: Optional[str] = None, 
                       status: Optional[str] = None, execution_time: Optional[int] = None) -> bool:
        """
        更新工具日志
        
        Args:
            log_id: 日志ID
            result: 结果字符串
            status: 状态
            execution_time: 执行时间（毫秒）
            
        Returns:
            更新是否成功
        """
        try:
            # 构建更新语句
            updates = []
            params = []
            
            if result is not None:
                updates.append("result = ?")
                params.append(result)
            
            if status is not None:
                updates.append("status = ?")
                params.append(status)
            
            if execution_time is not None:
                updates.append("execution_time = ?")
                params.append(execution_time)
            
            if not updates:
                return True  # 没有需要更新的内容
            
            # 执行更新
            query = f"UPDATE tool_logs SET {', '.join(updates)} WHERE log_id = ?"
            params.append(log_id)
            
            affected_rows = self.db_manager.execute_update(query, tuple(params))
            
            return affected_rows > 0
        except Exception as e:
            raise DatabaseError(f"更新工具日志失败: {str(e)}")
    
    def delete_tool_log(self, log_id: int) -> bool:
        """
        删除工具日志
        
        Args:
            log_id: 日志ID
            
        Returns:
            删除是否成功
        """
        try:
            affected_rows = self.db_manager.execute_update(
                "DELETE FROM tool_logs WHERE log_id = ?",
                (log_id,)
            )
            
            return affected_rows > 0
        except Exception as e:
            raise DatabaseError(f"删除工具日志失败: {str(e)}")
    
    def list_tool_logs(self, limit: int = 20, offset: int = 0, tool_name: Optional[str] = None,
                      status: Optional[str] = None, task_id: Optional[int] = None) -> List[Dict]:
        """
        列出工具日志
        
        Args:
            limit: 限制数量
            offset: 偏移量
            tool_name: 工具名称筛选
            status: 状态筛选
            task_id: 任务ID筛选
            
        Returns:
            日志列表
        """
        try:
            query = "SELECT log_id, tool_name, action, status, execution_time, task_id, created_at FROM tool_logs"
            params = []
            conditions = []
            
            if tool_name:
                conditions.append("tool_name = ?")
                params.append(tool_name)
            
            if status:
                conditions.append("status = ?")
                params.append(status)
            
            if task_id:
                conditions.append("task_id = ?")
                params.append(task_id)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            results = self.db_manager.execute_query(query, tuple(params) if params else None)
            
            return results
        except Exception as e:
            raise DatabaseError(f"列出工具日志失败: {str(e)}")
    
    def get_tool_log_count(self, tool_name: Optional[str] = None, status: Optional[str] = None,
                          task_id: Optional[int] = None) -> int:
        """
        获取工具日志数量
        
        Args:
            tool_name: 工具名称筛选
            status: 状态筛选
            task_id: 任务ID筛选
            
        Returns:
            日志数量
        """
        try:
            query = "SELECT COUNT(*) as count FROM tool_logs"
            params = []
            conditions = []
            
            if tool_name:
                conditions.append("tool_name = ?")
                params.append(tool_name)
            
            if status:
                conditions.append("status = ?")
                params.append(status)
            
            if task_id:
                conditions.append("task_id = ?")
                params.append(task_id)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            results = self.db_manager.execute_query(query, tuple(params) if params else None)
            
            return results[0]["count"]
        except Exception as e:
            raise DatabaseError(f"获取工具日志数量失败: {str(e)}")
    
    def get_recent_tool_logs(self, days: int = 7, limit: int = 50) -> List[Dict]:
        """
        获取最近的工具日志
        
        Args:
            days: 天数
            limit: 限制数量
            
        Returns:
            日志列表
        """
        try:
            query = '''
                SELECT log_id, tool_name, action, status, execution_time, task_id, created_at 
                FROM tool_logs 
                WHERE created_at >= datetime('now', '-{} days')
                ORDER BY created_at DESC
                LIMIT ?
            '''.format(days, limit)
            
            results = self.db_manager.execute_query(query)
            
            return results
        except Exception as e:
            raise DatabaseError(f"获取最近工具日志失败: {str(e)}")
    
    def get_tool_logs_by_task(self, task_id: int) -> List[Dict]:
        """
        获取任务相关的工具日志
        
        Args:
            task_id: 任务ID
            
        Returns:
            日志列表
        """
        try:
            query = '''
                SELECT log_id, tool_name, action, status, execution_time, created_at 
                FROM tool_logs 
                WHERE task_id = ?
                ORDER BY created_at ASC
            '''
            
            results = self.db_manager.execute_query(query, (task_id,))
            
            return results
        except Exception as e:
            raise DatabaseError(f"获取任务工具日志失败: {str(e)}")
    
    def get_tool_usage_stats(self, days: int = 7) -> Dict:
        """
        获取工具使用统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        try:
            stats = {}
            
            # 获取各工具的使用次数
            tool_usage = self.db_manager.execute_query('''
                SELECT tool_name, COUNT(*) as count 
                FROM tool_logs 
                WHERE created_at >= datetime('now', '-{} days')
                GROUP BY tool_name
                ORDER BY count DESC
            '''.format(days))
            
            stats["tool_usage"] = {item["tool_name"]: item["count"] for item in tool_usage}
            
            # 获取各工具的成功率
            tool_success = self.db_manager.execute_query('''
                SELECT tool_name, 
                       SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                       COUNT(*) as total_count
                FROM tool_logs 
                WHERE created_at >= datetime('now', '-{} days')
                GROUP BY tool_name
            '''.format(days))
            
            stats["tool_success"] = {}
            for item in tool_success:
                success_rate = item["success_count"] / item["total_count"] if item["total_count"] > 0 else 0
                stats["tool_success"][item["tool_name"]] = {
                    "success_count": item["success_count"],
                    "total_count": item["total_count"],
                    "success_rate": success_rate
                }
            
            # 获取各工具的平均执行时间
            tool_execution_time = self.db_manager.execute_query('''
                SELECT tool_name, AVG(execution_time) as avg_time
                FROM tool_logs 
                WHERE created_at >= datetime('now', '-{} days') AND execution_time IS NOT NULL
                GROUP BY tool_name
            '''.format(days))
            
            stats["tool_execution_time"] = {item["tool_name"]: item["avg_time"] for item in tool_execution_time}
            
            # 获取总调用次数
            total_calls = self.db_manager.execute_query('''
                SELECT COUNT(*) as count 
                FROM tool_logs 
                WHERE created_at >= datetime('now', '-{} days')
            '''.format(days))
            
            stats["total_calls"] = total_calls[0]["count"]
            
            # 获取总成功率
            total_success = self.db_manager.execute_query('''
                SELECT SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                       COUNT(*) as total_count
                FROM tool_logs 
                WHERE created_at >= datetime('now', '-{} days')
            '''.format(days))
            
            if total_success[0]["total_count"] > 0:
                stats["success_rate"] = total_success[0]["success_count"] / total_success[0]["total_count"]
            else:
                stats["success_rate"] = 0
            
            return stats
        except Exception as e:
            raise DatabaseError(f"获取工具使用统计信息失败: {str(e)}")
    
    def cleanup_old_tool_logs(self, days: int = 30) -> int:
        """
        清理旧工具日志
        
        Args:
            days: 保留天数
            
        Returns:
            删除的日志数量
        """
        try:
            # 删除指定天数之前的日志
            affected_rows = self.db_manager.execute_update(
                "DELETE FROM tool_logs WHERE created_at < datetime('now', '-{} days')".format(days)
            )
            
            return affected_rows
        except Exception as e:
            raise DatabaseError(f"清理旧工具日志失败: {str(e)}")