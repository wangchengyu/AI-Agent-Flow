"""
数据库操作工具

提供数据库查询、更新、备份和恢复等功能。
"""

import os
import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional, Union, Awaitable
from datetime import datetime

from ..utils.exceptions import DatabaseOperationError


class DatabaseOperations:
    """数据库操作工具，提供数据库操作功能"""
    
    def __init__(self, db_manager, max_rows: int = 1000):
        """
        初始化数据库操作工具
        
        Args:
            db_manager: 数据库管理器
            max_rows: 最大查询行数限制
        """
        self.db_manager = db_manager
        self.max_rows = max_rows
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """
        执行查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
            
        Raises:
            DatabaseOperationError: 如果执行查询失败
        """
        try:
            # 检查查询是否为SELECT语句
            if not query.strip().upper().startswith("SELECT"):
                raise DatabaseOperationError("只允许执行SELECT查询")
            
            # 执行查询
            results = await self.db_manager.execute_query(query, params)
            
            # 限制结果行数
            if len(results) > self.max_rows:
                results = results[:self.max_rows]
                self.logger.warning(f"查询结果超过最大行数限制 {self.max_rows}，已截断")
            
            self.logger.info(f"执行查询成功，返回 {len(results)} 行结果")
            return results
        except Exception as e:
            raise DatabaseOperationError(f"执行查询失败: {str(e)}")
    
    async def execute_update(self, query: str, params: Optional[tuple] = None) -> Dict:
        """
        执行更新
        
        Args:
            query: SQL更新语句
            params: 更新参数
            
        Returns:
            更新结果字典
            
        Raises:
            DatabaseOperationError: 如果执行更新失败
        """
        try:
            # 检查查询是否为允许的更新语句
            allowed_operations = ["INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP"]
            query_upper = query.strip().upper()
            
            if not any(query_upper.startswith(op) for op in allowed_operations):
                raise DatabaseOperationError(f"不允许执行的操作: {query.split()[0] if query.split() else 'unknown'}")
            
            # 执行更新
            affected_rows = await self.db_manager.execute_update(query, params)
            
            result = {
                "success": True,
                "affected_rows": affected_rows,
                "message": f"更新成功，影响 {affected_rows} 行"
            }
            
            self.logger.info(f"执行更新成功，影响 {affected_rows} 行")
            return result
        except Exception as e:
            raise DatabaseOperationError(f"执行更新失败: {str(e)}")
    
    async def get_table_info(self, table_name: str) -> Dict:
        """
        获取表信息
        
        Args:
            table_name: 表名
            
        Returns:
            表信息字典
            
        Raises:
            DatabaseOperationError: 如果获取表信息失败
        """
        try:
            # 获取表结构
            query = f"PRAGMA table_info({table_name})"
            columns = await self.db_manager.execute_query(query)
            
            # 获取表索引
            query = f"PRAGMA index_list({table_name})"
            indexes = await self.db_manager.execute_query(query)
            
            # 获取表外键
            query = f"PRAGMA foreign_key_list({table_name})"
            foreign_keys = await self.db_manager.execute_query(query)
            
            # 获取表行数
            query = f"SELECT COUNT(*) as count FROM {table_name}"
            count_result = await self.db_manager.execute_query(query)
            row_count = count_result[0]["count"] if count_result else 0
            
            return {
                "name": table_name,
                "columns": columns,
                "indexes": indexes,
                "foreign_keys": foreign_keys,
                "row_count": row_count
            }
        except Exception as e:
            raise DatabaseOperationError(f"获取表信息失败: {str(e)}")
    
    async def list_tables(self) -> List[Dict]:
        """
        列出所有表
        
        Returns:
            表信息列表
            
        Raises:
            DatabaseOperationError: 如果列出表失败
        """
        try:
            # 查询所有表
            query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            tables = await self.db_manager.execute_query(query)
            
            # 获取每个表的信息
            result = []
            for table in tables:
                table_name = table["name"]
                table_info = await self.get_table_info(table_name)
                result.append(table_info)
            
            self.logger.info(f"列出 {len(result)} 个表")
            return result
        except Exception as e:
            raise DatabaseOperationError(f"列出表失败: {str(e)}")
    
    async def backup_database(self, backup_path: str) -> bool:
        """
        备份数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            备份是否成功
            
        Raises:
            DatabaseOperationError: 如果备份数据库失败
        """
        try:
            # 确保备份目录存在
            backup_dir = os.path.dirname(backup_path)
            if backup_dir and not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # 获取数据库路径
            db_path = self.db_manager.db_path
            
            # 备份数据库
            source_conn = sqlite3.connect(db_path)
            backup_conn = sqlite3.connect(backup_path)
            
            with backup_conn:
                source_conn.backup(backup_conn)
            
            source_conn.close()
            backup_conn.close()
            
            self.logger.info(f"备份数据库成功: {backup_path}")
            return True
        except Exception as e:
            raise DatabaseOperationError(f"备份数据库失败: {str(e)}")
    
    async def restore_database(self, backup_path: str) -> bool:
        """
        恢复数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            恢复是否成功
            
        Raises:
            DatabaseOperationError: 如果恢复数据库失败
        """
        try:
            # 检查备份文件是否存在
            if not os.path.exists(backup_path):
                raise DatabaseOperationError(f"备份文件不存在: {backup_path}")
            
            # 获取数据库路径
            db_path = self.db_manager.db_path
            
            # 恢复数据库
            backup_conn = sqlite3.connect(backup_path)
            restore_conn = sqlite3.connect(db_path)
            
            with restore_conn:
                backup_conn.backup(restore_conn)
            
            backup_conn.close()
            restore_conn.close()
            
            self.logger.info(f"恢复数据库成功: {backup_path}")
            return True
        except Exception as e:
            raise DatabaseOperationError(f"恢复数据库失败: {str(e)}")
    
    async def export_table_to_csv(self, table_name: str, csv_path: str, 
                               delimiter: str = ",", include_header: bool = True) -> bool:
        """
        导出表到CSV文件
        
        Args:
            table_name: 表名
            csv_path: CSV文件路径
            delimiter: 分隔符
            include_header: 是否包含表头
            
        Returns:
            导出是否成功
            
        Raises:
            DatabaseOperationError: 如果导出表失败
        """
        try:
            import csv
            
            # 确保CSV目录存在
            csv_dir = os.path.dirname(csv_path)
            if csv_dir and not os.path.exists(csv_dir):
                os.makedirs(csv_dir)
            
            # 查询表数据
            query = f"SELECT * FROM {table_name}"
            results = await self.db_manager.execute_query(query)
            
            if not results:
                self.logger.warning(f"表 {table_name} 没有数据")
                return True
            
            # 写入CSV文件
            with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile, delimiter=delimiter)
                
                # 写入表头
                if include_header:
                    headers = list(results[0].keys())
                    writer.writerow(headers)
                
                # 写入数据
                for row in results:
                    writer.writerow(row.values())
            
            self.logger.info(f"导出表 {table_name} 到CSV文件成功: {csv_path}")
            return True
        except Exception as e:
            raise DatabaseOperationError(f"导出表到CSV文件失败: {str(e)}")
    
    async def import_csv_to_table(self, csv_path: str, table_name: str, 
                                delimiter: str = ",", include_header: bool = True) -> Dict:
        """
        从CSV文件导入表
        
        Args:
            csv_path: CSV文件路径
            table_name: 表名
            delimiter: 分隔符
            include_header: CSV文件是否包含表头
            
        Returns:
            导入结果字典
            
        Raises:
            DatabaseOperationError: 如果导入表失败
        """
        try:
            import csv
            
            # 检查CSV文件是否存在
            if not os.path.exists(csv_path):
                raise DatabaseOperationError(f"CSV文件不存在: {csv_path}")
            
            # 读取CSV文件
            with open(csv_path, "r", newline="", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile, delimiter=delimiter)
                
                # 读取表头
                if include_header:
                    headers = next(reader)
                else:
                    # 如果没有表头，需要获取表的列名
                    table_info = await self.get_table_info(table_name)
                    headers = [col["name"] for col in table_info["columns"]]
                
                # 准备插入语句
                placeholders = ", ".join(["?"] * len(headers))
                columns = ", ".join(headers)
                query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                
                # 插入数据
                inserted_rows = 0
                for row in reader:
                    await self.db_manager.execute_update(query, tuple(row))
                    inserted_rows += 1
            
            result = {
                "success": True,
                "inserted_rows": inserted_rows,
                "message": f"从CSV文件导入表成功，插入 {inserted_rows} 行"
            }
            
            self.logger.info(f"从CSV文件导入表 {table_name} 成功，插入 {inserted_rows} 行")
            return result
        except Exception as e:
            raise DatabaseOperationError(f"从CSV文件导入表失败: {str(e)}")
    
    async def export_table_to_json(self, table_name: str, json_path: str) -> bool:
        """
        导出表到JSON文件
        
        Args:
            table_name: 表名
            json_path: JSON文件路径
            
        Returns:
            导出是否成功
            
        Raises:
            DatabaseOperationError: 如果导出表失败
        """
        try:
            # 确保JSON目录存在
            json_dir = os.path.dirname(json_path)
            if json_dir and not os.path.exists(json_dir):
                os.makedirs(json_dir)
            
            # 查询表数据
            query = f"SELECT * FROM {table_name}"
            results = await self.db_manager.execute_query(query)
            
            # 写入JSON文件
            with open(json_path, "w", encoding="utf-8") as jsonfile:
                json.dump(results, jsonfile, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"导出表 {table_name} 到JSON文件成功: {json_path}")
            return True
        except Exception as e:
            raise DatabaseOperationError(f"导出表到JSON文件失败: {str(e)}")
    
    async def import_json_to_table(self, json_path: str, table_name: str) -> Dict:
        """
        从JSON文件导入表
        
        Args:
            json_path: JSON文件路径
            table_name: 表名
            
        Returns:
            导入结果字典
            
        Raises:
            DatabaseOperationError: 如果导入表失败
        """
        try:
            # 检查JSON文件是否存在
            if not os.path.exists(json_path):
                raise DatabaseOperationError(f"JSON文件不存在: {json_path}")
            
            # 读取JSON文件
            with open(json_path, "r", encoding="utf-8") as jsonfile:
                data = json.load(jsonfile)
            
            if not data:
                raise DatabaseOperationError(f"JSON文件为空: {json_path}")
            
            # 获取表的列名
            table_info = await self.get_table_info(table_name)
            columns = [col["name"] for col in table_info["columns"]]
            
            # 准备插入语句
            placeholders = ", ".join(["?"] * len(columns))
            columns_str = ", ".join(columns)
            query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            
            # 插入数据
            inserted_rows = 0
            for row in data:
                # 提取列值
                values = []
                for col in columns:
                    values.append(row.get(col, None))
                
                await self.db_manager.execute_update(query, tuple(values))
                inserted_rows += 1
            
            result = {
                "success": True,
                "inserted_rows": inserted_rows,
                "message": f"从JSON文件导入表成功，插入 {inserted_rows} 行"
            }
            
            self.logger.info(f"从JSON文件导入表 {table_name} 成功，插入 {inserted_rows} 行")
            return result
        except Exception as e:
            raise DatabaseOperationError(f"从JSON文件导入表失败: {str(e)}")
    
    async def create_table(self, table_name: str, columns: List[Dict], 
                          primary_key: Optional[str] = None,
                          foreign_keys: Optional[List[Dict]] = None) -> bool:
        """
        创建表
        
        Args:
            table_name: 表名
            columns: 列定义列表，每个列包含name, type, not_null, default等
            primary_key: 主键列名
            foreign_keys: 外键定义列表，每个外键包含column, references_table, references_column等
            
        Returns:
            创建是否成功
            
        Raises:
            DatabaseOperationError: 如果创建表失败
        """
        try:
            # 构建列定义
            column_defs = []
            for col in columns:
                col_def = f"{col['name']} {col['type']}"
                
                if col.get("not_null", False):
                    col_def += " NOT NULL"
                
                if "default" in col:
                    default_value = col["default"]
                    if isinstance(default_value, str):
                        col_def += f" DEFAULT '{default_value}'"
                    else:
                        col_def += f" DEFAULT {default_value}"
                
                column_defs.append(col_def)
            
            # 添加主键
            if primary_key:
                column_defs.append(f"PRIMARY KEY ({primary_key})")
            
            # 构建CREATE TABLE语句
            query = f"CREATE TABLE {table_name} (\n  "
            query += ",\n  ".join(column_defs)
            query += "\n)"
            
            # 执行创建表
            await self.db_manager.execute_update(query)
            
            # 添加外键
            if foreign_keys:
                for fk in foreign_keys:
                    fk_query = f"ALTER TABLE {table_name} ADD FOREIGN KEY ({fk['column']}) REFERENCES {fk['references_table']}({fk['references_column']})"
                    await self.db_manager.execute_update(fk_query)
            
            self.logger.info(f"创建表 {table_name} 成功")
            return True
        except Exception as e:
            raise DatabaseOperationError(f"创建表失败: {str(e)}")
    
    async def drop_table(self, table_name: str) -> bool:
        """
        删除表
        
        Args:
            table_name: 表名
            
        Returns:
            删除是否成功
            
        Raises:
            DatabaseOperationError: 如果删除表失败
        """
        try:
            # 执行删除表
            query = f"DROP TABLE IF EXISTS {table_name}"
            await self.db_manager.execute_update(query)
            
            self.logger.info(f"删除表 {table_name} 成功")
            return True
        except Exception as e:
            raise DatabaseOperationError(f"删除表失败: {str(e)}")
    
    async def add_column(self, table_name: str, column_name: str, column_type: str,
                       not_null: bool = False, default_value: Optional[Any] = None) -> bool:
        """
        添加列
        
        Args:
            table_name: 表名
            column_name: 列名
            column_type: 列类型
            not_null: 是否非空
            default_value: 默认值
            
        Returns:
            添加是否成功
            
        Raises:
            DatabaseOperationError: 如果添加列失败
        """
        try:
            # 构建ALTER TABLE语句
            query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            
            if not_null:
                query += " NOT NULL"
            
            if default_value is not None:
                if isinstance(default_value, str):
                    query += f" DEFAULT '{default_value}'"
                else:
                    query += f" DEFAULT {default_value}"
            
            # 执行添加列
            await self.db_manager.execute_update(query)
            
            self.logger.info(f"添加列 {column_name} 到表 {table_name} 成功")
            return True
        except Exception as e:
            raise DatabaseOperationError(f"添加列失败: {str(e)}")
    
    async def drop_column(self, table_name: str, column_name: str) -> bool:
        """
        删除列
        
        Args:
            table_name: 表名
            column_name: 列名
            
        Returns:
            删除是否成功
            
        Raises:
            DatabaseOperationError: 如果删除列失败
        """
        try:
            # 执行删除列
            query = f"ALTER TABLE {table_name} DROP COLUMN {column_name}"
            await self.db_manager.execute_update(query)
            
            self.logger.info(f"删除列 {column_name} 从表 {table_name} 成功")
            return True
        except Exception as e:
            raise DatabaseOperationError(f"删除列失败: {str(e)}")
    
    async def rename_table(self, old_name: str, new_name: str) -> bool:
        """
        重命名表
        
        Args:
            old_name: 旧表名
            new_name: 新表名
            
        Returns:
            重命名是否成功
            
        Raises:
            DatabaseOperationError: 如果重命名表失败
        """
        try:
            # 执行重命名表
            query = f"ALTER TABLE {old_name} RENAME TO {new_name}"
            await self.db_manager.execute_update(query)
            
            self.logger.info(f"重命名表 {old_name} 为 {new_name} 成功")
            return True
        except Exception as e:
            raise DatabaseOperationError(f"重命名表失败: {str(e)}")
    
    async def get_database_stats(self) -> Dict:
        """
        获取数据库统计信息
        
        Returns:
            数据库统计信息字典
            
        Raises:
            DatabaseOperationError: 如果获取数据库统计信息失败
        """
        try:
            # 获取数据库文件大小
            db_path = self.db_manager.db_path
            db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
            
            # 获取表数量
            query = "SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'"
            result = await self.db_manager.execute_query(query)
            table_count = result[0]["count"] if result else 0
            
            # 获取索引数量
            query = "SELECT COUNT(*) as count FROM sqlite_master WHERE type='index'"
            result = await self.db_manager.execute_query(query)
            index_count = result[0]["count"] if result else 0
            
            # 获取视图数量
            query = "SELECT COUNT(*) as count FROM sqlite_master WHERE type='view'"
            result = await self.db_manager.execute_query(query)
            view_count = result[0]["count"] if result else 0
            
            # 获取触发器数量
            query = "SELECT COUNT(*) as count FROM sqlite_master WHERE type='trigger'"
            result = await self.db_manager.execute_query(query)
            trigger_count = result[0]["count"] if result else 0
            
            # 获取数据库版本信息
            query = "SELECT sqlite_version() as version"
            result = await self.db_manager.execute_query(query)
            db_version = result[0]["version"] if result else "unknown"
            
            return {
                "db_path": db_path,
                "db_size": db_size,
                "table_count": table_count,
                "index_count": index_count,
                "view_count": view_count,
                "trigger_count": trigger_count,
                "db_version": db_version
            }
        except Exception as e:
            raise DatabaseOperationError(f"获取数据库统计信息失败: {str(e)}")
    
    async def optimize_database(self) -> bool:
        """
        优化数据库
        
        Returns:
            优化是否成功
            
        Raises:
            DatabaseOperationError: 如果优化数据库失败
        """
        try:
            # 执行VACUUM命令
            await self.db_manager.execute_update("VACUUM")
            
            # 执行ANALYZE命令
            await self.db_manager.execute_update("ANALYZE")
            
            self.logger.info("优化数据库成功")
            return True
        except Exception as e:
            raise DatabaseOperationError(f"优化数据库失败: {str(e)}")
    
    def set_max_rows(self, max_rows: int):
        """
        设置最大查询行数限制
        
        Args:
            max_rows: 最大查询行数限制
        """
        try:
            self.max_rows = max_rows
            self.logger.info(f"设置最大查询行数限制: {max_rows}")
        except Exception as e:
            raise DatabaseOperationError(f"设置最大查询行数限制失败: {str(e)}")