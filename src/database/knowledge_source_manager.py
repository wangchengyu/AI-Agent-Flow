"""
知识源管理器

负责管理知识源信息的存储、检索、更新和删除等功能，
提供知识库的统一管理能力。
"""

import os
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from .database_manager import DatabaseManager
from ..utils.exceptions import DatabaseError


class KnowledgeSourceManager:
    """知识源管理器，负责知识源信息的管理"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化知识源管理器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
    
    def create_knowledge_source(self, name: str, path: str, description: Optional[str] = None) -> int:
        """
        创建新知识源
        
        Args:
            name: 知识源名称
            path: 知识源路径
            description: 知识源描述
            
        Returns:
            知识源ID
        """
        try:
            # 检查路径是否存在
            if not os.path.exists(path):
                raise DatabaseError(f"路径 '{path}' 不存在")
            
            # 检查名称是否已存在
            existing_source = self.get_knowledge_source_by_name(name)
            if existing_source:
                raise DatabaseError(f"知识源名称 '{name}' 已存在")
            
            # 插入知识源记录
            source_id = self.db_manager.execute_insert(
                "INSERT INTO knowledge_sources (name, path, description) VALUES (?, ?, ?)",
                (name, path, description)
            )
            
            return source_id
        except Exception as e:
            raise DatabaseError(f"创建知识源失败: {str(e)}")
    
    def get_knowledge_source(self, source_id: int) -> Optional[Dict]:
        """
        获取知识源信息
        
        Args:
            source_id: 知识源ID
            
        Returns:
            知识源信息字典，如果不存在则返回None
        """
        try:
            results = self.db_manager.execute_query(
                "SELECT * FROM knowledge_sources WHERE source_id = ?",
                (source_id,)
            )
            
            if not results:
                return None
            
            return results[0]
        except Exception as e:
            raise DatabaseError(f"获取知识源失败: {str(e)}")
    
    def get_knowledge_source_by_name(self, name: str) -> Optional[Dict]:
        """
        根据名称获取知识源信息
        
        Args:
            name: 知识源名称
            
        Returns:
            知识源信息字典，如果不存在则返回None
        """
        try:
            results = self.db_manager.execute_query(
                "SELECT * FROM knowledge_sources WHERE name = ?",
                (name,)
            )
            
            if not results:
                return None
            
            return results[0]
        except Exception as e:
            raise DatabaseError(f"获取知识源失败: {str(e)}")
    
    def update_knowledge_source(self, source_id: int, name: Optional[str] = None, 
                               path: Optional[str] = None, description: Optional[str] = None) -> bool:
        """
        更新知识源信息
        
        Args:
            source_id: 知识源ID
            name: 新名称
            path: 新路径
            description: 新描述
            
        Returns:
            更新是否成功
        """
        try:
            # 获取当前知识源信息
            current_source = self.get_knowledge_source(source_id)
            if not current_source:
                raise DatabaseError(f"知识源ID '{source_id}' 不存在")
            
            # 构建更新语句
            updates = []
            params = []
            
            if name is not None and name != current_source["name"]:
                # 检查名称是否已存在
                existing_source = self.get_knowledge_source_by_name(name)
                if existing_source and existing_source["source_id"] != source_id:
                    raise DatabaseError(f"知识源名称 '{name}' 已存在")
                
                updates.append("name = ?")
                params.append(name)
            
            if path is not None and path != current_source["path"]:
                # 检查路径是否存在
                if not os.path.exists(path):
                    raise DatabaseError(f"路径 '{path}' 不存在")
                
                updates.append("path = ?")
                params.append(path)
            
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            
            if not updates:
                return True  # 没有需要更新的内容
            
            # 添加更新时间
            updates.append("updated_at = CURRENT_TIMESTAMP")
            
            # 执行更新
            query = f"UPDATE knowledge_sources SET {', '.join(updates)} WHERE source_id = ?"
            params.append(source_id)
            
            affected_rows = self.db_manager.execute_update(query, tuple(params))
            
            return affected_rows > 0
        except Exception as e:
            raise DatabaseError(f"更新知识源失败: {str(e)}")
    
    def update_knowledge_source_status(self, source_id: int, status: str) -> bool:
        """
        更新知识源状态
        
        Args:
            source_id: 知识源ID
            status: 新状态
            
        Returns:
            更新是否成功
        """
        try:
            # 检查状态是否有效
            if status not in ["active", "inactive"]:
                raise DatabaseError(f"无效的状态 '{status}'")
            
            # 更新状态和更新时间
            affected_rows = self.db_manager.execute_update(
                "UPDATE knowledge_sources SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE source_id = ?",
                (status, source_id)
            )
            
            return affected_rows > 0
        except Exception as e:
            raise DatabaseError(f"更新知识源状态失败: {str(e)}")
    
    def delete_knowledge_source(self, source_id: int) -> bool:
        """
        删除知识源
        
        Args:
            source_id: 知识源ID
            
        Returns:
            删除是否成功
        """
        try:
            affected_rows = self.db_manager.execute_update(
                "DELETE FROM knowledge_sources WHERE source_id = ?",
                (source_id,)
            )
            
            return affected_rows > 0
        except Exception as e:
            raise DatabaseError(f"删除知识源失败: {str(e)}")
    
    def list_knowledge_sources(self, limit: int = 20, offset: int = 0, status: Optional[str] = None) -> List[Dict]:
        """
        列出知识源
        
        Args:
            limit: 限制数量
            offset: 偏移量
            status: 状态筛选
            
        Returns:
            知识源列表
        """
        try:
            query = "SELECT * FROM knowledge_sources"
            params = []
            
            if status:
                query += " WHERE status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            results = self.db_manager.execute_query(query, tuple(params) if params else None)
            
            return results
        except Exception as e:
            raise DatabaseError(f"列出知识源失败: {str(e)}")
    
    def get_knowledge_source_count(self, status: Optional[str] = None) -> int:
        """
        获取知识源数量
        
        Args:
            status: 状态筛选
            
        Returns:
            知识源数量
        """
        try:
            query = "SELECT COUNT(*) as count FROM knowledge_sources"
            params = []
            
            if status:
                query += " WHERE status = ?"
                params.append(status)
            
            results = self.db_manager.execute_query(query, tuple(params) if params else None)
            
            return results[0]["count"]
        except Exception as e:
            raise DatabaseError(f"获取知识源数量失败: {str(e)}")
    
    def get_active_knowledge_sources(self) -> List[Dict]:
        """
        获取活跃的知识源
        
        Returns:
            知识源列表
        """
        try:
            query = '''
                SELECT * FROM knowledge_sources 
                WHERE status = 'active'
                ORDER BY name ASC
            '''
            
            results = self.db_manager.execute_query(query)
            
            return results
        except Exception as e:
            raise DatabaseError(f"获取活跃知识源失败: {str(e)}")
    
    def search_knowledge_sources(self, keyword: str, limit: int = 20) -> List[Dict]:
        """
        搜索知识源
        
        Args:
            keyword: 关键词
            limit: 限制数量
            
        Returns:
            知识源列表
        """
        try:
            query = '''
                SELECT * FROM knowledge_sources 
                WHERE name LIKE ? OR description LIKE ?
                ORDER BY name ASC
                LIMIT ?
            '''
            
            results = self.db_manager.execute_query(query, (f"%{keyword}%", f"%{keyword}%", limit))
            
            return results
        except Exception as e:
            raise DatabaseError(f"搜索知识源失败: {str(e)}")
    
    def validate_knowledge_source_path(self, source_id: int) -> Dict:
        """
        验证知识源路径
        
        Args:
            source_id: 知识源ID
            
        Returns:
            验证结果字典
        """
        try:
            # 获取知识源信息
            source = self.get_knowledge_source(source_id)
            if not source:
                raise DatabaseError(f"知识源ID '{source_id}' 不存在")
            
            path = source["path"]
            
            # 检查路径是否存在
            if not os.path.exists(path):
                return {
                    "valid": False,
                    "message": f"路径 '{path}' 不存在",
                    "path": path
                }
            
            # 检查是否为目录
            if not os.path.isdir(path):
                return {
                    "valid": False,
                    "message": f"路径 '{path}' 不是目录",
                    "path": path
                }
            
            # 统计文件数量
            file_count = 0
            supported_extensions = [".md", ".txt", ".py", ".js", ".json"]
            
            for root, dirs, files in os.walk(path):
                for file in files:
                    if any(file.endswith(ext) for ext in supported_extensions):
                        file_count += 1
            
            return {
                "valid": True,
                "message": f"路径 '{path}' 有效，包含 {file_count} 个支持的文件",
                "path": path,
                "file_count": file_count
            }
        except Exception as e:
            raise DatabaseError(f"验证知识源路径失败: {str(e)}")
    
    def get_knowledge_source_stats(self) -> Dict:
        """
        获取知识源统计信息
        
        Returns:
            统计信息字典
        """
        try:
            stats = {}
            
            # 获取总知识源数量
            total_count = self.db_manager.execute_query("SELECT COUNT(*) as count FROM knowledge_sources")
            stats["total_count"] = total_count[0]["count"]
            
            # 获取各状态的知识源数量
            status_counts = self.db_manager.execute_query(
                "SELECT status, COUNT(*) as count FROM knowledge_sources GROUP BY status"
            )
            
            stats["status_counts"] = {item["status"]: item["count"] for item in status_counts}
            
            # 获取活跃知识源的文件统计
            active_sources = self.get_active_knowledge_sources()
            stats["active_file_count"] = 0
            
            for source in active_sources:
                validation_result = self.validate_knowledge_source_path(source["source_id"])
                if validation_result["valid"]:
                    stats["active_file_count"] += validation_result["file_count"]
            
            return stats
        except Exception as e:
            raise DatabaseError(f"获取知识源统计信息失败: {str(e)}")
    
    def cleanup_invalid_knowledge_sources(self) -> int:
        """
        清理无效的知识源
        
        Returns:
            清理的知识源数量
        """
        try:
            # 获取所有知识源
            sources = self.list_knowledge_sources(limit=1000)
            
            cleanup_count = 0
            
            for source in sources:
                # 验证路径
                validation_result = self.validate_knowledge_source_path(source["source_id"])
                
                # 如果路径无效，则设置为非活跃状态
                if not validation_result["valid"]:
                    self.update_knowledge_source_status(source["source_id"], "inactive")
                    cleanup_count += 1
            
            return cleanup_count
        except Exception as e:
            raise DatabaseError(f"清理无效知识源失败: {str(e)}")