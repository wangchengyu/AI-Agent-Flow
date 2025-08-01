"""
AI Agent Flow 系统

一个基于多智能体协作的AI驱动工程实现闭环系统，通过自然语言需求解析、
任务拆解、工具调用和结果验证的全流程管理，实现用户需求的自动化处理。
"""

__version__ = "1.0.0"
__author__ = "AI Agent Flow Team"

from .agent_flow import AgentManager
from .database import DatabaseManager
from .rag import KnowledgeManager
from .mcp_tools import ToolManager
from .cli import CLIApplication