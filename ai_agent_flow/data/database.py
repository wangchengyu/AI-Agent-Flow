import sqlite3
import logging
import os
from datetime import datetime

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='ai_agent_flow/logs/database.log'
)

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path='ai_agent_flow/data/agent.db'):
        """初始化数据库连接"""
        self.db_path = db_path
        self._create_table()
        
    def _connect(self):
        """创建数据库连接"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"数据库连接失败: {str(e)}")
            raise
            
    def _create_table(self):
        """创建数据库表"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    goal TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    result TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            
    def insert_task(self, task_id, description, status='pending'):
        """插入新任务"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tasks (task_id, description, status)
                VALUES (?, ?, ?)
            ''', (task_id, description, status))
            conn.commit()
            
    def update_task_status(self, task_id, status):
        """更新任务状态"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tasks
                SET status = ?, updated_at = ?
                WHERE task_id = ?
            ''', (status, datetime.now().isoformat(), task_id))
            conn.commit()
            
    def get_task(self, task_id):
        """获取任务信息"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tasks WHERE task_id = ?', (task_id,))
            return dict(cursor.fetchone()) if cursor.rowcount > 0 else None
            
    def insert_agent(self, agent_id, role, goal, status='active'):
        """插入新Agent"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO agents (agent_id, role, goal, status)
                VALUES (?, ?, ?, ?)
            ''', (agent_id, role, goal, status))
            conn.commit()
            
    def get_agent(self, agent_id):
        """获取Agent信息"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM agents WHERE agent_id = ?', (agent_id,))
            return dict(cursor.fetchone()) if cursor.rowcount > 0 else None
            
    def insert_task_result(self, task_id, result):
        """插入任务结果"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO task_results (task_id, result)
                VALUES (?, ?)
            ''', (task_id, result))
            conn.commit()