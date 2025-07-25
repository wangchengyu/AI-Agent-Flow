"""
数据库管理模块
使用 SQLite3 进行本地数据管理
"""

import sqlite3
import os
from typing import Dict, Any, List, Optional
from contextlib import contextmanager


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str = "ai_agent_flow.db"):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            # 创建任务表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT UNIQUE NOT NULL,
                    parent_task_id TEXT,
                    description TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建执行结果表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    result_content TEXT,
                    validation_status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks (task_id)
                )
            """)
            
            # 创建配置表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_task_id ON tasks(task_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_parent_task_id ON tasks(parent_task_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_results_task_id ON task_results(task_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_config_key ON config(key)")

    @contextmanager
    def get_connection(self):
        """
        获取数据库连接的上下文管理器
        
        Yields:
            sqlite3.Connection: 数据库连接
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_task(self, task_id: str, description: str, parent_task_id: str = None) -> bool:
        """
        创建任务
        
        Args:
            task_id: 任务ID
            description: 任务描述
            parent_task_id: 父任务ID
            
        Returns:
            bool: 是否创建成功
        """
        try:
            with self.get_connection() as conn:
                conn.execute(
                    "INSERT INTO tasks (task_id, parent_task_id, description) VALUES (?, ?, ?)",
                    (task_id, parent_task_id, description)
                )
            return True
        except sqlite3.IntegrityError:
            # 任务ID已存在
            return False
        except Exception:
            return False

    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 任务状态
            
        Returns:
            bool: 是否更新成功
        """
        try:
            with self.get_connection() as conn:
                conn.execute(
                    "UPDATE tasks SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE task_id = ?",
                    (status, task_id)
                )
            return True
        except Exception:
            return False

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Dict[str, Any]]: 任务信息
        """
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_tasks_by_parent(self, parent_task_id: str) -> List[Dict[str, Any]]:
        """
        根据父任务ID获取子任务列表
        
        Args:
            parent_task_id: 父任务ID
            
        Returns:
            List[Dict[str, Any]]: 子任务列表
        """
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM tasks WHERE parent_task_id = ?", (parent_task_id,))
            return [dict(row) for row in cursor.fetchall()]

    def save_task_result(self, task_id: str, result_content: str, validation_status: str = "pending") -> bool:
        """
        保存任务执行结果
        
        Args:
            task_id: 任务ID
            result_content: 结果内容
            validation_status: 验证状态
            
        Returns:
            bool: 是否保存成功
        """
        try:
            with self.get_connection() as conn:
                conn.execute(
                    "INSERT INTO task_results (task_id, result_content, validation_status) VALUES (?, ?, ?)",
                    (task_id, result_content, validation_status)
                )
            return True
        except Exception:
            return False

    def update_result_validation_status(self, task_id: str, validation_status: str) -> bool:
        """
        更新结果验证状态
        
        Args:
            task_id: 任务ID
            validation_status: 验证状态
            
        Returns:
            bool: 是否更新成功
        """
        try:
            with self.get_connection() as conn:
                conn.execute(
                    "UPDATE task_results SET validation_status = ?, updated_at = CURRENT_TIMESTAMP WHERE task_id = ?",
                    (validation_status, task_id)
                )
            return True
        except Exception:
            return False

    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务执行结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Dict[str, Any]]: 任务执行结果
        """
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM task_results WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def set_config(self, key: str, value: str, description: str = "") -> bool:
        """
        设置配置项
        
        Args:
            key: 配置键
            value: 配置值
            description: 配置描述
            
        Returns:
            bool: 是否设置成功
        """
        try:
            with self.get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO config (key, value, description, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (key, value, description)
                )
            return True
        except Exception:
            return False

    def get_config(self, key: str) -> Optional[str]:
        """
        获取配置项
        
        Args:
            key: 配置键
            
        Returns:
            Optional[str]: 配置值
        """
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT value FROM config WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return row[0]
            return None

    def get_all_config(self) -> Dict[str, str]:
        """
        获取所有配置项
        
        Returns:
            Dict[str, str]: 所有配置项
        """
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT key, value FROM config")
            return {row[0]: row[1] for row in cursor.fetchall()}

    def delete_config(self, key: str) -> bool:
        """
        删除配置项
        
        Args:
            key: 配置键
            
        Returns:
            bool: 是否删除成功
        """
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM config WHERE key = ?", (key,))
            return True
        except Exception:
            return False