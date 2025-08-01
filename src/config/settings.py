"""
系统配置参数

定义了各个模块的默认配置参数，包括数据库配置、RAG配置、
MCP配置、Agent配置和CLI配置等。
"""

# 数据库配置
DATABASE_CONFIG = {
    "db_path": "agent_flow.db",
    "backup_dir": "./backups",
    "auto_backup": True,
    "backup_interval": 86400,  # 24小时
    "max_backups": 30,
    "connection_timeout": 30,
    "query_timeout": 10
}

# RAG系统配置
RAG_CONFIG = {
    "document_processing": {
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "supported_formats": [".md", ".txt", ".py", ".js", ".json"]
    },
    "embedding": {
        "model_name": "moka-ai/m3e-small",
        "normalize_embeddings": True
    },
    "vector_database": {
        "collection_name": "agent_flow_knowledge",
        "persist_directory": "./chroma_db",
        "distance_metric": "cosine"
    },
    "reranking": {
        "model_name": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
        "top_k": 3
    },
    "retrieval": {
        "default_top_k": 5,
        "min_similarity_score": 0.5,
        "use_reranking": True
    }
}

# MCP服务端配置
MCP_SERVER_CONFIG = {
    "name": "ai-agent-flow-tools",
    "transport": "stdio",
    "tools": {
        "file_operations": {
            "enabled": True,
            "max_file_size": "10MB",
            "allowed_extensions": [".py", ".md", ".txt", ".json"]
        },
        "code_operations": {
            "enabled": True,
            "execution_timeout": 30,
            "allowed_languages": ["python", "javascript", "java"]
        },
        "uml_operations": {
            "enabled": True,
            "max_classes": 50,
            "max_interactions": 100
        },
        "database_operations": {
            "enabled": True,
            "db_path": "agent_flow.db",
            "max_query_time": 10
        }
    }
}

# MCP客户端配置
MCP_CLIENT_CONFIG = {
    "server": {
        "command": "python",
        "args": ["mcp_server.py"]
    },
    "connection": {
        "timeout": 30,
        "retry_attempts": 3,
        "retry_delay": 1
    },
    "caching": {
        "enabled": True,
        "ttl": 300
    }
}

# Agent流程配置
AGENT_CONFIG = {
    "llm": {
        "model": "openai/gpt-4o",
        "temperature": 0.7,
        "max_tokens": 4000
    },
    "task_decomposition": {
        "max_subtasks": 20,
        "auto_validation": False
    },
    "info_gathering": {
        "max_rounds": 5,
        "timeout_per_round": 60
    },
    "validation": {
        "enabled": True,
        "require_user_confirmation": True
    }
}

# CLI配置
CLI_CONFIG = {
    "default_format": "text",
    "max_history_display": 20,
    "progress_refresh_rate": 10,
    "confirm_on_exit": True,
    "enable_syntax_highlighting": True,
    "table_max_width": 120,
    "color_scheme": "default"
}

# 交互式配置
INTERACTIVE_CONFIG = {
    "prompt": "请输入您的需求",
    "welcome_message": "AI Agent Flow - 交互式会话",
    "goodbye_message": "感谢使用 AI Agent Flow!",
    "command_prefix": "/",
    "history_size": 100,
    "auto_save_context": True,
    "context_file": ".context.json"
}

# 知识源配置
KNOWLEDGE_SOURCES = {
    "technical_docs": {
        "path": "./knowledge/technical_docs",
        "description": "技术文档",
        "priority": 1
    },
    "code_examples": {
        "path": "./knowledge/code_examples",
        "description": "代码示例",
        "priority": 2
    },
    "tool_manuals": {
        "path": "./knowledge/tool_manuals",
        "description": "工具手册",
        "priority": 3
    }
}

# 默认配置
DEFAULT_CONFIG = {
    "database": DATABASE_CONFIG,
    "rag": RAG_CONFIG,
    "mcp_server": MCP_SERVER_CONFIG,
    "mcp_client": MCP_CLIENT_CONFIG,
    "agent": AGENT_CONFIG,
    "cli": CLI_CONFIG,
    "interactive": INTERACTIVE_CONFIG,
    "knowledge_sources": KNOWLEDGE_SOURCES
}