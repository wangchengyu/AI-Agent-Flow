"""
权限管理器

负责管理工具权限，提供权限的授予、撤销、
检查和管理功能。
"""

import logging
from typing import Any, Dict, List, Optional, Set

from ..database.user_manager import UserManager
from ..utils.exceptions import PermissionManagerError


class PermissionManager:
    """权限管理器，负责管理工具权限"""
    
    def __init__(self, db_manager):
        """
        初始化权限管理器
        
        Args:
            db_manager: 数据库管理器
        """
        self.db_manager = db_manager
        self.user_manager = UserManager(db_manager)
        
        # 权限缓存
        self.permissions = {}
        self.user_permissions = {}
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """初始化权限管理器"""
        try:
            # 加载权限数据
            await self._load_permissions()
            
            self.logger.info("权限管理器初始化完成")
        except Exception as e:
            raise PermissionManagerError(f"初始化权限管理器失败: {str(e)}")
    
    async def _load_permissions(self):
        """加载权限数据"""
        try:
            # 从数据库加载权限
            query = "SELECT * FROM permissions"
            results = await self.db_manager.execute_query(query)
            
            # 构建权限字典
            self.permissions = {}
            for row in results:
                permission_id = row["id"]
                permission_name = row["name"]
                description = row["description"]
                
                self.permissions[permission_name] = {
                    "id": permission_id,
                    "name": permission_name,
                    "description": description
                }
            
            # 加载用户权限
            await self._load_user_permissions()
        except Exception as e:
            raise PermissionManagerError(f"加载权限数据失败: {str(e)}")
    
    async def _load_user_permissions(self):
        """加载用户权限数据"""
        try:
            # 从数据库加载用户权限
            query = """
            SELECT up.user_id, p.name 
            FROM user_permissions up
            JOIN permissions p ON up.permission_id = p.id
            """
            results = await self.db_manager.execute_query(query)
            
            # 构建用户权限字典
            self.user_permissions = {}
            for row in results:
                user_id = row["user_id"]
                permission_name = row["name"]
                
                if user_id not in self.user_permissions:
                    self.user_permissions[user_id] = set()
                
                self.user_permissions[user_id].add(permission_name)
        except Exception as e:
            raise PermissionManagerError(f"加载用户权限数据失败: {str(e)}")
    
    async def register_permission(self, name: str, description: str) -> bool:
        """
        注册权限
        
        Args:
            name: 权限名称
            description: 权限描述
            
        Returns:
            注册是否成功
        """
        try:
            # 检查权限是否已存在
            if name in self.permissions:
                self.logger.warning(f"权限 {name} 已存在")
                return True
            
            # 插入权限到数据库
            query = """
            INSERT INTO permissions (name, description)
            VALUES (?, ?)
            """
            await self.db_manager.execute_update(query, (name, description))
            
            # 更新权限缓存
            permission_id = await self.db_manager.get_last_insert_id()
            self.permissions[name] = {
                "id": permission_id,
                "name": name,
                "description": description
            }
            
            self.logger.info(f"注册权限: {name}")
            return True
        except Exception as e:
            raise PermissionManagerError(f"注册权限失败: {str(e)}")
    
    async def unregister_permission(self, name: str) -> bool:
        """
        注销权限
        
        Args:
            name: 权限名称
            
        Returns:
            注销是否成功
        """
        try:
            # 检查权限是否存在
            if name not in self.permissions:
                self.logger.warning(f"权限 {name} 不存在")
                return False
            
            # 从数据库删除权限
            permission_id = self.permissions[name]["id"]
            
            # 先删除用户权限关联
            query = "DELETE FROM user_permissions WHERE permission_id = ?"
            await self.db_manager.execute_update(query, (permission_id,))
            
            # 删除权限
            query = "DELETE FROM permissions WHERE id = ?"
            await self.db_manager.execute_update(query, (permission_id,))
            
            # 更新权限缓存
            del self.permissions[name]
            
            # 更新用户权限缓存
            for user_id, permissions in self.user_permissions.items():
                if name in permissions:
                    permissions.remove(name)
            
            self.logger.info(f"注销权限: {name}")
            return True
        except Exception as e:
            raise PermissionManagerError(f"注销权限失败: {str(e)}")
    
    async def grant_permission(self, user_id: int, permission_name: str) -> bool:
        """
        授予用户权限
        
        Args:
            user_id: 用户ID
            permission_name: 权限名称
            
        Returns:
            授予是否成功
        """
        try:
            # 检查权限是否存在
            if permission_name not in self.permissions:
                self.logger.warning(f"权限 {permission_name} 不存在")
                return False
            
            # 检查用户是否已有该权限
            if user_id in self.user_permissions and permission_name in self.user_permissions[user_id]:
                self.logger.warning(f"用户 {user_id} 已有权限 {permission_name}")
                return True
            
            # 获取权限ID
            permission_id = self.permissions[permission_name]["id"]
            
            # 插入用户权限到数据库
            query = """
            INSERT INTO user_permissions (user_id, permission_id)
            VALUES (?, ?)
            """
            await self.db_manager.execute_update(query, (user_id, permission_id))
            
            # 更新用户权限缓存
            if user_id not in self.user_permissions:
                self.user_permissions[user_id] = set()
            
            self.user_permissions[user_id].add(permission_name)
            
            self.logger.info(f"授予用户 {user_id} 权限 {permission_name}")
            return True
        except Exception as e:
            raise PermissionManagerError(f"授予权限失败: {str(e)}")
    
    async def revoke_permission(self, user_id: int, permission_name: str) -> bool:
        """
        撤销用户权限
        
        Args:
            user_id: 用户ID
            permission_name: 权限名称
            
        Returns:
            撤销是否成功
        """
        try:
            # 检查权限是否存在
            if permission_name not in self.permissions:
                self.logger.warning(f"权限 {permission_name} 不存在")
                return False
            
            # 检查用户是否有该权限
            if user_id not in self.user_permissions or permission_name not in self.user_permissions[user_id]:
                self.logger.warning(f"用户 {user_id} 没有权限 {permission_name}")
                return True
            
            # 获取权限ID
            permission_id = self.permissions[permission_name]["id"]
            
            # 从数据库删除用户权限
            query = """
            DELETE FROM user_permissions 
            WHERE user_id = ? AND permission_id = ?
            """
            await self.db_manager.execute_update(query, (user_id, permission_id))
            
            # 更新用户权限缓存
            if user_id in self.user_permissions:
                self.user_permissions[user_id].discard(permission_name)
            
            self.logger.info(f"撤销用户 {user_id} 权限 {permission_name}")
            return True
        except Exception as e:
            raise PermissionManagerError(f"撤销权限失败: {str(e)}")
    
    async def check_permission(self, user_id: int, permission_name: str) -> bool:
        """
        检查用户是否有权限
        
        Args:
            user_id: 用户ID
            permission_name: 权限名称
            
        Returns:
            是否有权限
        """
        try:
            # 检查权限是否存在
            if permission_name not in self.permissions:
                return False
            
            # 检查用户是否有该权限
            if user_id not in self.user_permissions:
                return False
            
            return permission_name in self.user_permissions[user_id]
        except Exception as e:
            raise PermissionManagerError(f"检查权限失败: {str(e)}")
    
    async def check_permissions(self, user_id: int, permission_names: List[str]) -> Dict[str, bool]:
        """
        检查用户是否有多个权限
        
        Args:
            user_id: 用户ID
            permission_names: 权限名称列表
            
        Returns:
            权限检查结果字典
        """
        try:
            results = {}
            
            for permission_name in permission_names:
                results[permission_name] = await self.check_permission(user_id, permission_name)
            
            return results
        except Exception as e:
            raise PermissionManagerError(f"检查多个权限失败: {str(e)}")
    
    async def check_all_permissions(self, user_id: int, permission_names: List[str]) -> bool:
        """
        检查用户是否有所有权限
        
        Args:
            user_id: 用户ID
            permission_names: 权限名称列表
            
        Returns:
            是否有所有权限
        """
        try:
            results = await self.check_permissions(user_id, permission_names)
            
            return all(results.values())
        except Exception as e:
            raise PermissionManagerError(f"检查所有权限失败: {str(e)}")
    
    async def check_any_permission(self, user_id: int, permission_names: List[str]) -> bool:
        """
        检查用户是否有任意一个权限
        
        Args:
            user_id: 用户ID
            permission_names: 权限名称列表
            
        Returns:
            是否有任意一个权限
        """
        try:
            results = await self.check_permissions(user_id, permission_names)
            
            return any(results.values())
        except Exception as e:
            raise PermissionManagerError(f"检查任意权限失败: {str(e)}")
    
    async def get_user_permissions(self, user_id: int) -> List[str]:
        """
        获取用户权限列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            权限名称列表
        """
        try:
            if user_id not in self.user_permissions:
                return []
            
            return list(self.user_permissions[user_id])
        except Exception as e:
            raise PermissionManagerError(f"获取用户权限列表失败: {str(e)}")
    
    async def get_all_permissions(self) -> List[Dict]:
        """
        获取所有权限
        
        Returns:
            权限信息列表
        """
        try:
            return [
                {
                    "id": permission["id"],
                    "name": permission["name"],
                    "description": permission["description"]
                }
                for permission in self.permissions.values()
            ]
        except Exception as e:
            raise PermissionManagerError(f"获取所有权限失败: {str(e)}")
    
    async def get_permission_info(self, name: str) -> Optional[Dict]:
        """
        获取权限信息
        
        Args:
            name: 权限名称
            
        Returns:
            权限信息字典，如果不存在则返回None
        """
        try:
            if name not in self.permissions:
                return None
            
            permission = self.permissions[name]
            return {
                "id": permission["id"],
                "name": permission["name"],
                "description": permission["description"]
            }
        except Exception as e:
            raise PermissionManagerError(f"获取权限信息失败: {str(e)}")
    
    async def get_users_with_permission(self, permission_name: str) -> List[int]:
        """
        获取有特定权限的用户ID列表
        
        Args:
            permission_name: 权限名称
            
        Returns:
            用户ID列表
        """
        try:
            # 检查权限是否存在
            if permission_name not in self.permissions:
                return []
            
            # 从数据库查询有该权限的用户
            permission_id = self.permissions[permission_name]["id"]
            query = """
            SELECT user_id 
            FROM user_permissions 
            WHERE permission_id = ?
            """
            results = await self.db_manager.execute_query(query, (permission_id,))
            
            return [row["user_id"] for row in results]
        except Exception as e:
            raise PermissionManagerError(f"获取有特定权限的用户失败: {str(e)}")
    
    async def grant_role_permissions(self, role_name: str, permission_names: List[str]) -> bool:
        """
        授予角色权限
        
        Args:
            role_name: 角色名称
            permission_names: 权限名称列表
            
        Returns:
            授予是否成功
        """
        try:
            # 获取角色下的所有用户
            users = await self.user_manager.get_users_by_role(role_name)
            
            # 为每个用户授予权限
            success = True
            for user in users:
                user_id = user["id"]
                for permission_name in permission_names:
                    result = await self.grant_permission(user_id, permission_name)
                    if not result:
                        success = False
            
            return success
        except Exception as e:
            raise PermissionManagerError(f"授予角色权限失败: {str(e)}")
    
    async def revoke_role_permissions(self, role_name: str, permission_names: List[str]) -> bool:
        """
        撤销角色权限
        
        Args:
            role_name: 角色名称
            permission_names: 权限名称列表
            
        Returns:
            撤销是否成功
        """
        try:
            # 获取角色下的所有用户
            users = await self.user_manager.get_users_by_role(role_name)
            
            # 为每个用户撤销权限
            success = True
            for user in users:
                user_id = user["id"]
                for permission_name in permission_names:
                    result = await self.revoke_permission(user_id, permission_name)
                    if not result:
                        success = False
            
            return success
        except Exception as e:
            raise PermissionManagerError(f"撤销角色权限失败: {str(e)}")
    
    async def refresh_cache(self):
        """刷新权限缓存"""
        try:
            await self._load_permissions()
            self.logger.info("权限缓存已刷新")
        except Exception as e:
            raise PermissionManagerError(f"刷新权限缓存失败: {str(e)}")