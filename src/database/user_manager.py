"""
用户管理器

负责管理用户信息的存储、检索、更新和删除等功能，
提供用户偏好设置和登录记录管理能力。
"""

import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from .database_manager import DatabaseManager
from ..utils.exceptions import DatabaseError


class UserManager:
    """用户管理器，负责用户信息的管理"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化用户管理器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
    
    def create_user(self, username: str, preferences: Optional[Dict] = None) -> int:
        """
        创建新用户
        
        Args:
            username: 用户名
            preferences: 用户偏好设置
            
        Returns:
            用户ID
        """
        try:
            # 检查用户名是否已存在
            existing_user = self.get_user_by_username(username)
            if existing_user:
                raise DatabaseError(f"用户名 '{username}' 已存在")
            
            # 序列化偏好设置
            preferences_json = json.dumps(preferences) if preferences else None
            
            # 插入用户记录
            user_id = self.db_manager.execute_insert(
                "INSERT INTO users (username, preferences) VALUES (?, ?)",
                (username, preferences_json)
            )
            
            return user_id
        except Exception as e:
            raise DatabaseError(f"创建用户失败: {str(e)}")
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """
        获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息字典，如果不存在则返回None
        """
        try:
            results = self.db_manager.execute_query(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            
            if not results:
                return None
            
            user = results[0]
            
            # 反序列化偏好设置
            if user["preferences"]:
                user["preferences"] = json.loads(user["preferences"])
            else:
                user["preferences"] = {}
            
            return user
        except Exception as e:
            raise DatabaseError(f"获取用户失败: {str(e)}")
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """
        根据用户名获取用户信息
        
        Args:
            username: 用户名
            
        Returns:
            用户信息字典，如果不存在则返回None
        """
        try:
            results = self.db_manager.execute_query(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )
            
            if not results:
                return None
            
            user = results[0]
            
            # 反序列化偏好设置
            if user["preferences"]:
                user["preferences"] = json.loads(user["preferences"])
            else:
                user["preferences"] = {}
            
            return user
        except Exception as e:
            raise DatabaseError(f"获取用户失败: {str(e)}")
    
    def update_user_preferences(self, user_id: int, preferences: Dict) -> bool:
        """
        更新用户偏好设置
        
        Args:
            user_id: 用户ID
            preferences: 偏好设置字典
            
        Returns:
            更新是否成功
        """
        try:
            # 序列化偏好设置
            preferences_json = json.dumps(preferences)
            
            # 更新偏好设置
            affected_rows = self.db_manager.execute_update(
                "UPDATE users SET preferences = ? WHERE user_id = ?",
                (preferences_json, user_id)
            )
            
            return affected_rows > 0
        except Exception as e:
            raise DatabaseError(f"更新用户偏好设置失败: {str(e)}")
    
    def update_user_login_time(self, user_id: int) -> bool:
        """
        更新用户登录时间
        
        Args:
            user_id: 用户ID
            
        Returns:
            更新是否成功
        """
        try:
            affected_rows = self.db_manager.execute_update(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            
            return affected_rows > 0
        except Exception as e:
            raise DatabaseError(f"更新用户登录时间失败: {str(e)}")
    
    def delete_user(self, user_id: int) -> bool:
        """
        删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            删除是否成功
        """
        try:
            affected_rows = self.db_manager.execute_update(
                "DELETE FROM users WHERE user_id = ?",
                (user_id,)
            )
            
            return affected_rows > 0
        except Exception as e:
            raise DatabaseError(f"删除用户失败: {str(e)}")
    
    def list_users(self, limit: int = 20, offset: int = 0) -> List[Dict]:
        """
        列出用户
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            用户列表
        """
        try:
            query = "SELECT user_id, username, created_at, last_login FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?"
            
            results = self.db_manager.execute_query(query, (limit, offset))
            
            return results
        except Exception as e:
            raise DatabaseError(f"列出用户失败: {str(e)}")
    
    def get_user_count(self) -> int:
        """
        获取用户数量
        
        Returns:
            用户数量
        """
        try:
            results = self.db_manager.execute_query("SELECT COUNT(*) as count FROM users")
            
            return results[0]["count"]
        except Exception as e:
            raise DatabaseError(f"获取用户数量失败: {str(e)}")
    
    def get_recent_users(self, days: int = 7) -> List[Dict]:
        """
        获取最近注册的用户
        
        Args:
            days: 天数
            
        Returns:
            用户列表
        """
        try:
            query = '''
                SELECT user_id, username, created_at, last_login 
                FROM users 
                WHERE created_at >= datetime('now', '-{} days')
                ORDER BY created_at DESC
            '''.format(days)
            
            results = self.db_manager.execute_query(query)
            
            return results
        except Exception as e:
            raise DatabaseError(f"获取最近用户失败: {str(e)}")
    
    def get_active_users(self, days: int = 7) -> List[Dict]:
        """
        获取最近活跃的用户
        
        Args:
            days: 天数
            
        Returns:
            用户列表
        """
        try:
            query = '''
                SELECT user_id, username, created_at, last_login 
                FROM users 
                WHERE last_login >= datetime('now', '-{} days')
                ORDER BY last_login DESC
            '''.format(days)
            
            results = self.db_manager.execute_query(query)
            
            return results
        except Exception as e:
            raise DatabaseError(f"获取活跃用户失败: {str(e)}")
    
    def search_users(self, keyword: str, limit: int = 20) -> List[Dict]:
        """
        搜索用户
        
        Args:
            keyword: 关键词
            limit: 限制数量
            
        Returns:
            用户列表
        """
        try:
            query = '''
                SELECT user_id, username, created_at, last_login 
                FROM users 
                WHERE username LIKE ?
                ORDER BY username ASC
                LIMIT ?
            '''
            
            results = self.db_manager.execute_query(query, (f"%{keyword}%", limit))
            
            return results
        except Exception as e:
            raise DatabaseError(f"搜索用户失败: {str(e)}")
    
    def get_user_stats(self) -> Dict:
        """
        获取用户统计信息
        
        Returns:
            统计信息字典
        """
        try:
            stats = {}
            
            # 获取总用户数
            total_count = self.db_manager.execute_query("SELECT COUNT(*) as count FROM users")
            stats["total_count"] = total_count[0]["count"]
            
            # 获取今日注册用户数
            today_count = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM users WHERE date(created_at) = date('now')"
            )
            stats["today_count"] = today_count[0]["count"]
            
            # 获取本周注册用户数
            week_count = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM users WHERE created_at >= datetime('now', '-7 days')"
            )
            stats["week_count"] = week_count[0]["count"]
            
            # 获取活跃用户数（最近7天有登录记录）
            active_count = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM users WHERE last_login >= datetime('now', '-7 days')"
            )
            stats["active_count"] = active_count[0]["count"]
            
            # 获取新用户数（最近30天注册但从未登录）
            new_user_count = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM users WHERE created_at >= datetime('now', '-30 days') AND last_login IS NULL"
            )
            stats["new_user_count"] = new_user_count[0]["count"]
            
            return stats
        except Exception as e:
            raise DatabaseError(f"获取用户统计信息失败: {str(e)}")
    
    def cleanup_inactive_users(self, days: int = 90) -> int:
        """
        清理不活跃用户
        
        Args:
            days: 不活跃天数
            
        Returns:
            删除的用户数量
        """
        try:
            # 删除指定天数之前注册且从未登录的用户
            affected_rows = self.db_manager.execute_update(
                "DELETE FROM users WHERE created_at < datetime('now', '-{} days') AND last_login IS NULL".format(days)
            )
            
            return affected_rows
        except Exception as e:
            raise DatabaseError(f"清理不活跃用户失败: {str(e)}")