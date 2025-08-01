"""
本地数据管理模块

负责提供可靠的数据持久化服务，包括任务历史记录、用户配置、
系统状态等数据的存储和检索功能，确保系统数据的完整性和一致性。
"""

from .database_manager import DatabaseManager
from .task_history_manager import TaskHistoryManager
from .config_manager import ConfigManager
from .user_manager import UserManager
from .knowledge_source_manager import KnowledgeSourceManager
from .tool_log_manager import ToolLogManager
from .backup_manager import BackupManager

__all__ = [
    "DatabaseManager",
    "TaskHistoryManager",
    "ConfigManager",
    "UserManager",
    "KnowledgeSourceManager",
    "ToolLogManager",
    "BackupManager"
]