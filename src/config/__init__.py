"""
配置模块

负责管理系统配置参数，包括数据库配置、RAG配置、MCP配置、
Agent配置等，提供统一的配置访问接口。
"""

from .config_manager import ConfigManager
from .settings import (
    DATABASE_CONFIG,
    RAG_CONFIG,
    MCP_CONFIG,
    AGENT_CONFIG,
    CLI_CONFIG
)

__all__ = [
    "ConfigManager",
    "DATABASE_CONFIG",
    "RAG_CONFIG",
    "MCP_CONFIG",
    "AGENT_CONFIG",
    "CLI_CONFIG"
]