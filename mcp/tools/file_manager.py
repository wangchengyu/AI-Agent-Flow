"""
文件管理工具示例
提供基本的文件操作功能
"""

import os
import json
from typing import Dict, Any, List


def read_file(file_path: str) -> Dict[str, Any]:
    """
    读取文件内容
    
    Args:
        file_path: 文件路径
        
    Returns:
        Dict[str, Any]: 读取结果
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "success": True,
            "content": content,
            "file_path": file_path
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def write_file(file_path: str, content: str) -> Dict[str, Any]:
    """
    写入文件内容
    
    Args:
        file_path: 文件路径
        content: 文件内容
        
    Returns:
        Dict[str, Any]: 写入结果
    """
    try:
        # 创建目录（如果不存在）
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # 写入文件内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "success": True,
            "message": f"File written successfully: {file_path}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def list_files(directory: str) -> Dict[str, Any]:
    """
    列出目录中的文件
    
    Args:
        directory: 目录路径
        
    Returns:
        Dict[str, Any]: 文件列表
    """
    try:
        # 检查目录是否存在
        if not os.path.exists(directory):
            return {
                "success": False,
                "error": f"Directory not found: {directory}"
            }
        
        # 列出文件
        files = os.listdir(directory)
        file_info = []
        
        for file in files:
            file_path = os.path.join(directory, file)
            stat = os.stat(file_path)
            file_info.append({
                "name": file,
                "path": file_path,
                "size": stat.st_size,
                "is_directory": os.path.isdir(file_path)
            })
        
        return {
            "success": True,
            "files": file_info,
            "directory": directory
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def delete_file(file_path: str) -> Dict[str, Any]:
    """
    删除文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        Dict[str, Any]: 删除结果
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        # 删除文件
        os.remove(file_path)
        
        return {
            "success": True,
            "message": f"File deleted successfully: {file_path}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def create_directory(directory_path: str) -> Dict[str, Any]:
    """
    创建目录
    
    Args:
        directory_path: 目录路径
        
    Returns:
        Dict[str, Any]: 创建结果
    """
    try:
        # 创建目录（如果不存在）
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        
        return {
            "success": True,
            "message": f"Directory created successfully: {directory_path}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# 工具注册信息
TOOL_INFO = {
    "read_file": {
        "function": read_file,
        "description": "读取文件内容"
    },
    "write_file": {
        "function": write_file,
        "description": "写入文件内容"
    },
    "list_files": {
        "function": list_files,
        "description": "列出目录中的文件"
    },
    "delete_file": {
        "function": delete_file,
        "description": "删除文件"
    },
    "create_directory": {
        "function": create_directory,
        "description": "创建目录"
    }
}