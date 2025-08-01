"""
备份管理器

负责管理数据库备份的创建、恢复、清理等功能，
提供数据安全和灾难恢复能力。
"""

import os
import shutil
import glob
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

from .database_manager import DatabaseManager
from ..utils.exceptions import DatabaseError


class BackupManager:
    """备份管理器，负责数据库备份的管理"""
    
    def __init__(self, db_manager: DatabaseManager, backup_dir: str = "./backups"):
        """
        初始化备份管理器
        
        Args:
            db_manager: 数据库管理器实例
            backup_dir: 备份目录
        """
        self.db_manager = db_manager
        self.backup_dir = backup_dir
        self._ensure_backup_directory()
    
    def _ensure_backup_directory(self):
        """确保备份目录存在"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_backup(self, description: Optional[str] = None) -> str:
        """
        创建数据库备份
        
        Args:
            description: 备份描述
            
        Returns:
            备份文件路径
        """
        try:
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"agent_flow_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, filename)
            
            # 创建备份
            success = self.db_manager.backup_database(backup_path)
            
            if not success:
                raise DatabaseError("创建备份失败")
            
            # 添加描述到备份记录
            if description:
                self.db_manager.execute_update(
                    "UPDATE backup_records SET description = ? WHERE filename = ?",
                    (description, backup_path)
                )
            
            return backup_path
        except Exception as e:
            raise DatabaseError(f"创建备份失败: {str(e)}")
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        恢复数据库备份
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            恢复是否成功
        """
        try:
            # 检查备份文件是否存在
            if not os.path.exists(backup_path):
                raise DatabaseError(f"备份文件 '{backup_path}' 不存在")
            
            # 恢复备份
            success = self.db_manager.restore_database(backup_path)
            
            return success
        except Exception as e:
            raise DatabaseError(f"恢复备份失败: {str(e)}")
    
    def list_backups(self, limit: int = 20, offset: int = 0) -> List[Dict]:
        """
        列出备份记录
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            备份记录列表
        """
        try:
            query = '''
                SELECT backup_id, filename, size, created_at, description 
                FROM backup_records 
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            '''
            
            results = self.db_manager.execute_query(query, (limit, offset))
            
            return results
        except Exception as e:
            raise DatabaseError(f"列出备份记录失败: {str(e)}")
    
    def get_backup_count(self) -> int:
        """
        获取备份记录数量
        
        Returns:
            备份记录数量
        """
        try:
            results = self.db_manager.execute_query("SELECT COUNT(*) as count FROM backup_records")
            
            return results[0]["count"]
        except Exception as e:
            raise DatabaseError(f"获取备份记录数量失败: {str(e)}")
    
    def get_backup_info(self, backup_path: str) -> Optional[Dict]:
        """
        获取备份信息
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            备份信息字典，如果不存在则返回None
        """
        try:
            results = self.db_manager.execute_query(
                "SELECT * FROM backup_records WHERE filename = ?",
                (backup_path,)
            )
            
            if not results:
                return None
            
            return results[0]
        except Exception as e:
            raise DatabaseError(f"获取备份信息失败: {str(e)}")
    
    def delete_backup(self, backup_path: str) -> bool:
        """
        删除备份
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            删除是否成功
        """
        try:
            # 删除备份文件
            if os.path.exists(backup_path):
                os.remove(backup_path)
            
            # 删除备份记录
            affected_rows = self.db_manager.execute_update(
                "DELETE FROM backup_records WHERE filename = ?",
                (backup_path,)
            )
            
            return affected_rows > 0
        except Exception as e:
            raise DatabaseError(f"删除备份失败: {str(e)}")
    
    def cleanup_old_backups(self, max_backups: int = 30, max_days: int = 90) -> int:
        """
        清理旧备份
        
        Args:
            max_backups: 最大保留备份数量
            max_days: 最大保留天数
            
        Returns:
            删除的备份数量
        """
        try:
            deleted_count = 0
            
            # 获取所有备份记录，按创建时间降序排列
            all_backups = self.db_manager.execute_query(
                "SELECT backup_id, filename, created_at FROM backup_records ORDER BY created_at DESC"
            )
            
            # 按数量清理
            if len(all_backups) > max_backups:
                for backup in all_backups[max_backups:]:
                    if self.delete_backup(backup["filename"]):
                        deleted_count += 1
            
            # 按天数清理
            cutoff_date = datetime.now() - timedelta(days=max_days)
            old_backups = self.db_manager.execute_query(
                "SELECT backup_id, filename FROM backup_records WHERE created_at < ?",
                (cutoff_date.strftime("%Y-%m-%d %H:%M:%S"),)
            )
            
            for backup in old_backups:
                if self.delete_backup(backup["filename"]):
                    deleted_count += 1
            
            return deleted_count
        except Exception as e:
            raise DatabaseError(f"清理旧备份失败: {str(e)}")
    
    def get_backup_stats(self) -> Dict:
        """
        获取备份统计信息
        
        Returns:
            统计信息字典
        """
        try:
            stats = {}
            
            # 获取备份记录数量
            backup_count = self.db_manager.execute_query("SELECT COUNT(*) as count FROM backup_records")
            stats["backup_count"] = backup_count[0]["count"]
            
            # 获取备份总大小
            backup_size = self.db_manager.execute_query("SELECT SUM(size) as total_size FROM backup_records")
            stats["total_size"] = backup_size[0]["total_size"] or 0
            
            # 获取最近的备份时间
            latest_backup = self.db_manager.execute_query(
                "SELECT MAX(created_at) as latest FROM backup_records"
            )
            stats["latest_backup"] = latest_backup[0]["latest"]
            
            # 获取备份目录大小
            if os.path.exists(self.backup_dir):
                dir_size = 0
                for root, dirs, files in os.walk(self.backup_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            dir_size += os.path.getsize(file_path)
                stats["directory_size"] = dir_size
            else:
                stats["directory_size"] = 0
            
            # 获取最近7天的备份数量
            recent_backups = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM backup_records WHERE created_at >= datetime('now', '-7 days')"
            )
            stats["recent_backups"] = recent_backups[0]["count"]
            
            return stats
        except Exception as e:
            raise DatabaseError(f"获取备份统计信息失败: {str(e)}")
    
    def schedule_auto_backup(self, interval_hours: int = 24, max_backups: int = 30) -> bool:
        """
        设置自动备份计划
        
        Args:
            interval_hours: 备份间隔（小时）
            max_backups: 最大保留备份数量
            
        Returns:
            设置是否成功
        """
        try:
            # 检查是否需要创建备份
            latest_backup = self.db_manager.execute_query(
                "SELECT MAX(created_at) as latest FROM backup_records"
            )
            
            if latest_backup[0]["latest"]:
                latest_time = datetime.strptime(latest_backup[0]["latest"], "%Y-%m-%d %H:%M:%S")
                next_backup_time = latest_time + timedelta(hours=interval_hours)
                
                if datetime.now() < next_backup_time:
                    return True  # 还不需要备份
            
            # 创建备份
            description = f"自动备份 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            self.create_backup(description)
            
            # 清理旧备份
            self.cleanup_old_backups(max_backups=max_backups)
            
            return True
        except Exception as e:
            raise DatabaseError(f"设置自动备份失败: {str(e)}")
    
    def verify_backup(self, backup_path: str) -> Dict:
        """
        验证备份文件
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            验证结果字典
        """
        try:
            result = {
                "valid": True,
                "message": "备份文件有效",
                "path": backup_path
            }
            
            # 检查文件是否存在
            if not os.path.exists(backup_path):
                result["valid"] = False
                result["message"] = f"备份文件 '{backup_path}' 不存在"
                return result
            
            # 检查文件大小
            file_size = os.path.getsize(backup_path)
            result["file_size"] = file_size
            
            if file_size == 0:
                result["valid"] = False
                result["message"] = "备份文件为空"
                return result
            
            # 尝试打开数据库并检查基本表结构
            import sqlite3
            import tempfile
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # 复制备份文件到临时文件
                shutil.copy2(backup_path, temp_path)
                
                # 尝试连接数据库
                conn = sqlite3.connect(temp_path)
                cursor = conn.cursor()
                
                # 检查基本表是否存在
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                expected_tables = ["task_history", "config", "users", "knowledge_sources", "tool_logs", "backup_records"]
                missing_tables = [table for table in expected_tables if table not in tables]
                
                if missing_tables:
                    result["valid"] = False
                    result["message"] = f"备份文件缺少必要的表: {', '.join(missing_tables)}"
                
                # 关闭连接
                conn.close()
            except Exception as e:
                result["valid"] = False
                result["message"] = f"备份文件无法读取或已损坏: {str(e)}"
            finally:
                # 删除临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            return result
        except Exception as e:
            raise DatabaseError(f"验证备份失败: {str(e)}")