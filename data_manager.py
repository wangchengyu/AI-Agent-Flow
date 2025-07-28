"""
Local data management module using SQLite3 for the AI Agent Flow system.
Handles data storage, retrieval, and schema management.
"""

import sqlite3
import json
from datetime import datetime

class DataManager:
    """Manages local data storage and retrieval using SQLite3."""
    
    def __init__(self, db_path='agent_flow.db'):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._initialize_schema()
    
    def _initialize_schema(self):
        """Create database schema if it doesn't exist."""
        with self.conn:
            # Create tasks table
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    description TEXT NOT NULL,
                    result TEXT,
                    status TEXT NOT NULL
                )
            ''')
            
            # Create files table for tracking managed files
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    path TEXT PRIMARY KEY,
                    last_modified TEXT NOT NULL,
                    size INTEGER NOT NULL
                )
            ''')
    
    def save_task_result(self, description, result, status='completed'):
        """Save a task result to the database."""
        timestamp = datetime.now().isoformat()
        with self.conn:
            self.conn.execute(
                'INSERT INTO tasks (timestamp, description, result, status) VALUES (?, ?, ?, ?)',
                (timestamp, description, json.dumps(result), status)
            )
    
    def get_task_history(self, limit=10):
        """Retrieve recent task history from the database."""
        cursor = self.conn.execute(
            'SELECT timestamp, description, result, status FROM tasks ORDER BY id DESC LIMIT ?',
            (limit,)
        )
        return [
            {
                'timestamp': row[0],
                'description': row[1],
                'result': json.loads(row[2]),
                'status': row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def update_file_metadata(self, path, size):
        """Update file metadata in the database."""
        timestamp = datetime.now().isoformat()
        with self.conn:
            self.conn.execute(
                'REPLACE INTO files (path, last_modified, size) VALUES (?, ?, ?)',
                (path, timestamp, size)
            )
    
    def get_file_metadata(self, path):
        """Retrieve file metadata from the database."""
        cursor = self.conn.execute(
            'SELECT last_modified, size FROM files WHERE path = ?', 
            (path,)
        )
        result = cursor.fetchone()
        if result:
            return {
                'last_modified': result[0],
                'size': result[1]
            }
        return None

if __name__ == "__main__":
    # Example usage
    data_manager = DataManager()
    
    # Test task storage
    test_result = {"output": "Sample code generated", "files": ["new_script.py"]}
    data_manager.save_task_result("Create sample script", test_result)
    
    print("Recent tasks:")
    for task in data_manager.get_task_history():
        print(f"{task['timestamp']} - {task['description']} ({task['status']})")