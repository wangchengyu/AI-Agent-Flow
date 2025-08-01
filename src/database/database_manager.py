"""
数据库管理器

负责管理SQLite数据库的连接、表创建、数据操作等基础功能，
为其他数据管理类提供统一的数据库访问接口。
"""

import sqlite3
import os
import json
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path

from ..utils.exceptions import DatabaseError


class DatabaseManager:
    """数据库管理器，负责SQLite数据库的基础操作"""
    
    def __init__(self, db_path: str = "agent_flow.db"):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    def _init_database(self):
        """初始化数据库，创建必要的表"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 创建任务历史表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS task_history (
                        task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_input TEXT NOT NULL,
                        subtasks JSON,
                        results BLOB,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP
                    )
                ''')
                
                # 创建配置表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS config (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建用户表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        preferences JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP
                    )
                ''')
                
                # 创建知识源表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_sources (
                        source_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        path TEXT NOT NULL,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建工具日志表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tool_logs (
                        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tool_name TEXT NOT NULL,
                        action TEXT NOT NULL,
                        parameters JSON,
                        result TEXT,
                        status TEXT DEFAULT 'success',
                        execution_time INTEGER,
                        task_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (task_id) REFERENCES task_history (task_id)
                    )
                ''')
                
                # 创建备份记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS backup_records (
                        backup_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        size INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        description TEXT
                    )
                ''')
                
                conn.commit()
        except Exception as e:
            raise DatabaseError(f"初始化数据库失败: {str(e)}")
    
    def get_connection(self) -> sqlite3.Connection:
        """
        获取数据库连接
        
        Returns:
            SQLite数据库连接对象
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 返回字典形式的行
            return conn
        except Exception as e:
            raise DatabaseError(f"连接数据库失败: {str(e)}")
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """
        执行查询语句
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # 将结果转换为字典列表
                results = [dict(row) for row in cursor.fetchall()]
                return results
        except Exception as e:
            raise DatabaseError(f"执行查询失败: {str(e)}")
    
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        执行更新语句
        
        Args:
            query: SQL更新语句
            params: 更新参数
            
        Returns:
            受影响的行数
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            raise DatabaseError(f"执行更新失败: {str(e)}")
    
    def execute_insert(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        执行插入语句
        
        Args:
            query: SQL插入语句
            params: 插入参数
            
        Returns:
            新插入行的ID
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            raise DatabaseError(f"执行插入失败: {str(e)}")
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """
        批量执行语句
        
        Args:
            query: SQL语句
            params_list: 参数列表
            
        Returns:
            受影响的行数
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            raise DatabaseError(f"批量执行失败: {str(e)}")
    
    def table_exists(self, table_name: str) -> bool:
        """
        检查表是否存在
        
        Args:
            table_name: 表名
            
        Returns:
            表是否存在
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        results = self.execute_query(query, (table_name,))
        return len(results) > 0
    
    def get_table_info(self, table_name: str) -> List[Dict]:
        """
        获取表结构信息
        
        Args:
            table_name: 表名
            
        Returns:
            表结构信息列表
        """
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query)
    
    def backup_database(self, backup_path: str) -> bool:
        """
        备份数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            备份是否成功
        """
        try:
            # 确保备份目录存在
            backup_dir = os.path.dirname(backup_path)
            if backup_dir and not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # 复制数据库文件
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            # 记录备份信息
            file_size = os.path.getsize(backup_path)
            self.execute_insert(
                "INSERT INTO backup_records (filename, size, description) VALUES (?, ?, ?)",
                (backup_path, file_size, f"数据库备份 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            )
            
            return True
        except Exception as e:
            raise DatabaseError(f"备份数据库失败: {str(e)}")
    
    def restore_database(self, backup_path: str) -> bool:
        """
        恢复数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            恢复是否成功
        """
        try:
            # 关闭所有连接
            # 复制备份文件
            import shutil
            shutil.copy2(backup_path, self.db_path)
            
            # 重新初始化数据库
            self._init_database()
            
            return True
        except Exception as e:
            raise DatabaseError(f"恢复数据库失败: {str(e)}")
    
    def get_database_stats(self) -> Dict:
        """
        获取数据库统计信息
        
        Returns:
            数据库统计信息字典
        """
        try:
            stats = {}
            
            # 获取数据库文件大小
            if os.path.exists(self.db_path):
                stats["file_size"] = os.path.getsize(self.db_path)
            else:
                stats["file_size"] = 0
            
            # 获取各表的记录数
            tables = ["task_history", "config", "users", "knowledge_sources", "tool_logs", "backup_records"]
            stats["table_counts"] = {}
            
            for table in tables:
                if self.table_exists(table):
                    result = self.execute_query(f"SELECT COUNT(*) as count FROM {table}")
                    stats["table_counts"][table] = result[0]["count"]
                else:
                    stats["table_counts"][table] = 0
            
            # 获取最后备份时间
            backup_result = self.execute_query("SELECT MAX(created_at) as last_backup FROM backup_records")
            stats["last_backup"] = backup_result[0]["last_backup"] if backup_result[0]["last_backup"] else None
            
            return stats
        except Exception as e:
            raise DatabaseError(f"获取数据库统计信息失败: {str(e)}")
    
    def vacuum_database(self) -> bool:
        """
        清理数据库，释放空间
        
        Returns:
            清理是否成功
        """
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                conn.commit()
                return True
        except Exception as e:
            raise DatabaseError(f"清理数据库失败: {str(e)}")