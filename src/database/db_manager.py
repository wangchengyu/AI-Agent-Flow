import sqlite3
import json
from typing import Dict, List, Any
from datetime import datetime
import os
from enum import Enum

class SubTaskState(Enum):
    PENDING = 0
    INFO_GATHERING = 1
    EXECUTING = 2
    VALIDATING = 3
    COMPLETED = 4

class DatabaseManager:
    def __init__(self, db_path: str = "agent_flow.db"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 创建任务历史表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_history (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT NOT NULL,
            subtasks TEXT NOT NULL,  -- JSON格式存储
            results BLOB,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 创建子任务状态表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS subtask_state (
            subtask_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            state INTEGER NOT NULL CHECK(state BETWEEN 0 AND 4),
            context TEXT,  -- JSON格式存储
            FOREIGN KEY(task_id) REFERENCES task_history(task_id)
        )
        """)
        
        conn.commit()
        conn.close()
        
    def _get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
        
    def save_task(self, user_input: str, subtasks: List[Dict]) -> int:
        """保存任务到数据库"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 保存任务历史
        cursor.execute("""
        INSERT INTO task_history (user_input, subtasks)
        VALUES (?, ?)
        """, (user_input, json.dumps(subtasks)))
        
        task_id = cursor.lastrowid
        
        # 保存子任务状态
        for subtask in subtasks:
            cursor.execute("""
            INSERT INTO subtask_state (task_id, state, context)
            VALUES (?, ?, ?)
            """, (task_id, subtask['status'].value, json.dumps(subtask.get('context', []))))
        
        conn.commit()
        conn.close()
        return task_id
        
    def update_subtask_state(self, subtask_id: int, new_state: SubTaskState, context: List[Any] = None):
        """更新子任务状态"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE subtask_state
        SET state = ?, context = ?
        WHERE subtask_id = ?
        """, (new_state.value, json.dumps(context) if context else None, subtask_id))
        
        conn.commit()
        conn.close()
        
    def get_task_history(self, limit: int = 10) -> List[Dict]:
        """获取最近的任务历史"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT task_id, user_input, subtasks, timestamp
        FROM task_history
        ORDER BY timestamp DESC
        LIMIT ?
        """, (limit,))
        
        tasks = []
        for row in cursor.fetchall():
            task_id, user_input, subtasks_json, timestamp = row
            tasks.append({
                'task_id': task_id,
                'user_input': user_input,
                'subtasks': json.loads(subtasks_json),
                'timestamp': timestamp
            })
        
        conn.close()
        return tasks
        
    def get_subtask_state(self, subtask_id: int) -> Dict:
        """获取子任务状态"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT state, context
        FROM subtask_state
        WHERE subtask_id = ?
        """, (subtask_id,))
        
        row = cursor.fetchone()
        if row:
            state, context_json = row
            return {
                'state': SubTaskState(state),
                'context': json.loads(context_json) if context_json else []
            }
        return None
        
    def backup_database(self, backup_path: str):
        """创建数据库备份"""
        conn = self._get_connection()
        with open(backup_path, 'w') as f:
            for line in conn.iterdump():
                f.write(f"{line}\n")
        conn.close()
        
    def restore_database(self, backup_path: str):
        """从备份恢复数据库"""
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 清空当前数据库
        cursor.execute("DROP TABLE IF EXISTS task_history")
        cursor.execute("DROP TABLE IF EXISTS subtask_state")
        conn.commit()
        
        # 执行备份脚本
        with open(backup_path, 'r') as f:
            sql_script = f.read()
            cursor.executescript(sql_script)
        
        conn.commit()
        conn.close()
        
        # 重新初始化数据库结构
        self._init_db()