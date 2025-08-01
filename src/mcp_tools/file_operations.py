"""
文件操作工具

提供文件和目录的读取、写入、创建、删除等操作功能。
"""

import os
import shutil
import json
import logging
from typing import Any, Dict, List, Optional, Union, Awaitable
from pathlib import Path

from ..utils.exceptions import FileOperationError


class FileOperations:
    """文件操作工具，提供文件和目录操作功能"""
    
    def __init__(self, base_dir: Optional[str] = None, max_file_size: int = 10 * 1024 * 1024):
        """
        初始化文件操作工具
        
        Args:
            base_dir: 基础目录，如果为None则不限制操作目录
            max_file_size: 最大文件大小（字节）
        """
        self.base_dir = base_dir
        self.max_file_size = max_file_size
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _validate_path(self, path: str) -> str:
        """
        验证路径
        
        Args:
            path: 文件路径
            
        Returns:
            验证后的绝对路径
            
        Raises:
            FileOperationError: 如果路径无效或不安全
        """
        try:
            # 转换为绝对路径
            abs_path = os.path.abspath(path)
            
            # 如果设置了基础目录，检查路径是否在基础目录内
            if self.base_dir:
                base_abs_path = os.path.abspath(self.base_dir)
                if not abs_path.startswith(base_abs_path):
                    raise FileOperationError(f"路径 {path} 不在允许的操作目录内")
            
            return abs_path
        except Exception as e:
            raise FileOperationError(f"验证路径失败: {str(e)}")
    
    def _check_file_size(self, file_path: str):
        """
        检查文件大小
        
        Args:
            file_path: 文件路径
            
        Raises:
            FileOperationError: 如果文件大小超过限制
        """
        try:
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                raise FileOperationError(f"文件大小 {file_size} 超过限制 {self.max_file_size}")
        except Exception as e:
            raise FileOperationError(f"检查文件大小失败: {str(e)}")
    
    async def read_file(self, file_path: str, encoding: str = "utf-8") -> str:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径
            encoding: 文件编码
            
        Returns:
            文件内容
            
        Raises:
            FileOperationError: 如果读取文件失败
        """
        try:
            # 验证路径
            validated_path = self._validate_path(file_path)
            
            # 检查文件是否存在
            if not os.path.exists(validated_path):
                raise FileOperationError(f"文件 {file_path} 不存在")
            
            # 检查是否为文件
            if not os.path.isfile(validated_path):
                raise FileOperationError(f"{file_path} 不是文件")
            
            # 检查文件大小
            self._check_file_size(validated_path)
            
            # 读取文件
            with open(validated_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            self.logger.info(f"读取文件: {file_path}")
            return content
        except Exception as e:
            raise FileOperationError(f"读取文件失败: {str(e)}")
    
    async def read_file_lines(self, file_path: str, encoding: str = "utf-8", 
                            start_line: int = 0, end_line: Optional[int] = None) -> List[str]:
        """
        读取文件行
        
        Args:
            file_path: 文件路径
            encoding: 文件编码
            start_line: 起始行号（从0开始）
            end_line: 结束行号（不包含），如果为None则读到文件末尾
            
        Returns:
            文件行列表
            
        Raises:
            FileOperationError: 如果读取文件失败
        """
        try:
            # 验证路径
            validated_path = self._validate_path(file_path)
            
            # 检查文件是否存在
            if not os.path.exists(validated_path):
                raise FileOperationError(f"文件 {file_path} 不存在")
            
            # 检查是否为文件
            if not os.path.isfile(validated_path):
                raise FileOperationError(f"{file_path} 不是文件")
            
            # 检查文件大小
            self._check_file_size(validated_path)
            
            # 读取文件行
            with open(validated_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
            
            # 截取指定行
            if end_line is None:
                end_line = len(lines)
            
            result_lines = lines[start_line:end_line]
            
            # 去除每行的换行符
            result_lines = [line.rstrip('\n\r') for line in result_lines]
            
            self.logger.info(f"读取文件行: {file_path} ({start_line}-{end_line})")
            return result_lines
        except Exception as e:
            raise FileOperationError(f"读取文件行失败: {str(e)}")
    
    async def write_file(self, file_path: str, content: str, encoding: str = "utf-8",
                        create_dirs: bool = True) -> bool:
        """
        写入文件
        
        Args:
            file_path: 文件路径
            content: 文件内容
            encoding: 文件编码
            create_dirs: 是否创建目录
            
        Returns:
            写入是否成功
            
        Raises:
            FileOperationError: 如果写入文件失败
        """
        try:
            # 验证路径
            validated_path = self._validate_path(file_path)
            
            # 检查内容大小
            content_size = len(content.encode(encoding))
            if content_size > self.max_file_size:
                raise FileOperationError(f"内容大小 {content_size} 超过限制 {self.max_file_size}")
            
            # 创建目录（如果需要）
            dir_path = os.path.dirname(validated_path)
            if create_dirs and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            
            # 写入文件
            with open(validated_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            self.logger.info(f"写入文件: {file_path}")
            return True
        except Exception as e:
            raise FileOperationError(f"写入文件失败: {str(e)}")
    
    async def append_file(self, file_path: str, content: str, encoding: str = "utf-8") -> bool:
        """
        追加内容到文件
        
        Args:
            file_path: 文件路径
            content: 要追加的内容
            encoding: 文件编码
            
        Returns:
            追加是否成功
            
        Raises:
            FileOperationError: 如果追加内容失败
        """
        try:
            # 验证路径
            validated_path = self._validate_path(file_path)
            
            # 检查文件是否存在
            if not os.path.exists(validated_path):
                raise FileOperationError(f"文件 {file_path} 不存在")
            
            # 检查是否为文件
            if not os.path.isfile(validated_path):
                raise FileOperationError(f"{file_path} 不是文件")
            
            # 检查文件大小
            self._check_file_size(validated_path)
            
            # 检查内容大小
            content_size = len(content.encode(encoding))
            if content_size > self.max_file_size:
                raise FileOperationError(f"内容大小 {content_size} 超过限制 {self.max_file_size}")
            
            # 追加内容
            with open(validated_path, 'a', encoding=encoding) as f:
                f.write(content)
            
            self.logger.info(f"追加内容到文件: {file_path}")
            return True
        except Exception as e:
            raise FileOperationError(f"追加内容到文件失败: {str(e)}")
    
    async def delete_file(self, file_path: str) -> bool:
        """
        删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            删除是否成功
            
        Raises:
            FileOperationError: 如果删除文件失败
        """
        try:
            # 验证路径
            validated_path = self._validate_path(file_path)
            
            # 检查文件是否存在
            if not os.path.exists(validated_path):
                raise FileOperationError(f"文件 {file_path} 不存在")
            
            # 检查是否为文件
            if not os.path.isfile(validated_path):
                raise FileOperationError(f"{file_path} 不是文件")
            
            # 删除文件
            os.remove(validated_path)
            
            self.logger.info(f"删除文件: {file_path}")
            return True
        except Exception as e:
            raise FileOperationError(f"删除文件失败: {str(e)}")
    
    async def copy_file(self, src_path: str, dst_path: str, create_dirs: bool = True) -> bool:
        """
        复制文件
        
        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径
            create_dirs: 是否创建目录
            
        Returns:
            复制是否成功
            
        Raises:
            FileOperationError: 如果复制文件失败
        """
        try:
            # 验证路径
            validated_src_path = self._validate_path(src_path)
            validated_dst_path = self._validate_path(dst_path)
            
            # 检查源文件是否存在
            if not os.path.exists(validated_src_path):
                raise FileOperationError(f"源文件 {src_path} 不存在")
            
            # 检查源文件是否为文件
            if not os.path.isfile(validated_src_path):
                raise FileOperationError(f"{src_path} 不是文件")
            
            # 检查源文件大小
            self._check_file_size(validated_src_path)
            
            # 创建目录（如果需要）
            dir_path = os.path.dirname(validated_dst_path)
            if create_dirs and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            
            # 复制文件
            shutil.copy2(validated_src_path, validated_dst_path)
            
            self.logger.info(f"复制文件: {src_path} -> {dst_path}")
            return True
        except Exception as e:
            raise FileOperationError(f"复制文件失败: {str(e)}")
    
    async def move_file(self, src_path: str, dst_path: str, create_dirs: bool = True) -> bool:
        """
        移动文件
        
        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径
            create_dirs: 是否创建目录
            
        Returns:
            移动是否成功
            
        Raises:
            FileOperationError: 如果移动文件失败
        """
        try:
            # 验证路径
            validated_src_path = self._validate_path(src_path)
            validated_dst_path = self._validate_path(dst_path)
            
            # 检查源文件是否存在
            if not os.path.exists(validated_src_path):
                raise FileOperationError(f"源文件 {src_path} 不存在")
            
            # 检查源文件是否为文件
            if not os.path.isfile(validated_src_path):
                raise FileOperationError(f"{src_path} 不是文件")
            
            # 检查源文件大小
            self._check_file_size(validated_src_path)
            
            # 创建目录（如果需要）
            dir_path = os.path.dirname(validated_dst_path)
            if create_dirs and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            
            # 移动文件
            shutil.move(validated_src_path, validated_dst_path)
            
            self.logger.info(f"移动文件: {src_path} -> {dst_path}")
            return True
        except Exception as e:
            raise FileOperationError(f"移动文件失败: {str(e)}")
    
    async def list_files(self, dir_path: str, recursive: bool = False, 
                        include_hidden: bool = False) -> List[Dict]:
        """
        列出目录中的文件
        
        Args:
            dir_path: 目录路径
            recursive: 是否递归列出子目录中的文件
            include_hidden: 是否包含隐藏文件
            
        Returns:
            文件信息列表
            
        Raises:
            FileOperationError: 如果列出文件失败
        """
        try:
            # 验证路径
            validated_path = self._validate_path(dir_path)
            
            # 检查目录是否存在
            if not os.path.exists(validated_path):
                raise FileOperationError(f"目录 {dir_path} 不存在")
            
            # 检查是否为目录
            if not os.path.isdir(validated_path):
                raise FileOperationError(f"{dir_path} 不是目录")
            
            # 列出文件
            files = []
            
            if recursive:
                # 递归列出文件
                for root, dirs, filenames in os.walk(validated_path):
                    for filename in filenames:
                        # 检查是否为隐藏文件
                        if not include_hidden and filename.startswith('.'):
                            continue
                        
                        file_path = os.path.join(root, filename)
                        rel_path = os.path.relpath(file_path, validated_path)
                        
                        # 获取文件信息
                        stat = os.stat(file_path)
                        files.append({
                            "name": filename,
                            "path": rel_path,
                            "full_path": file_path,
                            "size": stat.st_size,
                            "is_dir": False,
                            "modified_time": stat.st_mtime
                        })
            else:
                # 非递归列出文件
                for item in os.listdir(validated_path):
                    # 检查是否为隐藏文件
                    if not include_hidden and item.startswith('.'):
                        continue
                    
                    item_path = os.path.join(validated_path, item)
                    
                    # 获取文件信息
                    stat = os.stat(item_path)
                    files.append({
                        "name": item,
                        "path": item,
                        "full_path": item_path,
                        "size": stat.st_size,
                        "is_dir": os.path.isdir(item_path),
                        "modified_time": stat.st_mtime
                    })
            
            self.logger.info(f"列出文件: {dir_path} (递归: {recursive})")
            return files
        except Exception as e:
            raise FileOperationError(f"列出文件失败: {str(e)}")
    
    async def create_directory(self, dir_path: str, parents: bool = True) -> bool:
        """
        创建目录
        
        Args:
            dir_path: 目录路径
            parents: 是否创建父目录
            
        Returns:
            创建是否成功
            
        Raises:
            FileOperationError: 如果创建目录失败
        """
        try:
            # 验证路径
            validated_path = self._validate_path(dir_path)
            
            # 创建目录
            if parents:
                os.makedirs(validated_path, exist_ok=True)
            else:
                os.mkdir(validated_path)
            
            self.logger.info(f"创建目录: {dir_path}")
            return True
        except Exception as e:
            raise FileOperationError(f"创建目录失败: {str(e)}")
    
    async def delete_directory(self, dir_path: str, recursive: bool = False) -> bool:
        """
        删除目录
        
        Args:
            dir_path: 目录路径
            recursive: 是否递归删除
            
        Returns:
            删除是否成功
            
        Raises:
            FileOperationError: 如果删除目录失败
        """
        try:
            # 验证路径
            validated_path = self._validate_path(dir_path)
            
            # 检查目录是否存在
            if not os.path.exists(validated_path):
                raise FileOperationError(f"目录 {dir_path} 不存在")
            
            # 检查是否为目录
            if not os.path.isdir(validated_path):
                raise FileOperationError(f"{dir_path} 不是目录")
            
            # 删除目录
            if recursive:
                shutil.rmtree(validated_path)
            else:
                os.rmdir(validated_path)
            
            self.logger.info(f"删除目录: {dir_path} (递归: {recursive})")
            return True
        except Exception as e:
            raise FileOperationError(f"删除目录失败: {str(e)}")
    
    async def get_file_info(self, file_path: str) -> Dict:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典
            
        Raises:
            FileOperationError: 如果获取文件信息失败
        """
        try:
            # 验证路径
            validated_path = self._validate_path(file_path)
            
            # 检查文件是否存在
            if not os.path.exists(validated_path):
                raise FileOperationError(f"文件 {file_path} 不存在")
            
            # 获取文件信息
            stat = os.stat(validated_path)
            
            return {
                "name": os.path.basename(validated_path),
                "path": validated_path,
                "size": stat.st_size,
                "is_dir": os.path.isdir(validated_path),
                "is_file": os.path.isfile(validated_path),
                "created_time": stat.st_ctime,
                "modified_time": stat.st_mtime,
                "accessed_time": stat.st_atime
            }
        except Exception as e:
            raise FileOperationError(f"获取文件信息失败: {str(e)}")
    
    async def read_json_file(self, file_path: str, encoding: str = "utf-8") -> Dict:
        """
        读取JSON文件
        
        Args:
            file_path: 文件路径
            encoding: 文件编码
            
        Returns:
            JSON数据
            
        Raises:
            FileOperationError: 如果读取JSON文件失败
        """
        try:
            # 读取文件内容
            content = await self.read_file(file_path, encoding)
            
            # 解析JSON
            try:
                data = json.loads(content)
                return data
            except json.JSONDecodeError as e:
                raise FileOperationError(f"解析JSON文件失败: {str(e)}")
        except Exception as e:
            raise FileOperationError(f"读取JSON文件失败: {str(e)}")
    
    async def write_json_file(self, file_path: str, data: Dict, encoding: str = "utf-8",
                           indent: Optional[int] = None, create_dirs: bool = True) -> bool:
        """
        写入JSON文件
        
        Args:
            file_path: 文件路径
            data: JSON数据
            encoding: 文件编码
            indent: 缩进空格数
            create_dirs: 是否创建目录
            
        Returns:
            写入是否成功
            
        Raises:
            FileOperationError: 如果写入JSON文件失败
        """
        try:
            # 序列化JSON
            try:
                content = json.dumps(data, indent=indent, ensure_ascii=False)
            except TypeError as e:
                raise FileOperationError(f"序列化JSON数据失败: {str(e)}")
            
            # 写入文件
            return await self.write_file(file_path, content, encoding, create_dirs)
        except Exception as e:
            raise FileOperationError(f"写入JSON文件失败: {str(e)}")
    
    async def search_files(self, dir_path: str, pattern: str, recursive: bool = True,
                         case_sensitive: bool = False) -> List[Dict]:
        """
        搜索文件
        
        Args:
            dir_path: 目录路径
            pattern: 搜索模式（支持通配符）
            recursive: 是否递归搜索
            case_sensitive: 是否区分大小写
            
        Returns:
            匹配的文件信息列表
            
        Raises:
            FileOperationError: 如果搜索文件失败
        """
        try:
            import fnmatch
            
            # 验证路径
            validated_path = self._validate_path(dir_path)
            
            # 检查目录是否存在
            if not os.path.exists(validated_path):
                raise FileOperationError(f"目录 {dir_path} 不存在")
            
            # 检查是否为目录
            if not os.path.isdir(validated_path):
                raise FileOperationError(f"{dir_path} 不是目录")
            
            # 搜索文件
            matched_files = []
            
            if recursive:
                # 递归搜索
                for root, dirs, filenames in os.walk(validated_path):
                    for filename in filenames:
                        # 检查文件名是否匹配模式
                        if case_sensitive:
                            match = fnmatch.fnmatch(filename, pattern)
                        else:
                            match = fnmatch.fnmatch(filename.lower(), pattern.lower())
                        
                        if match:
                            file_path = os.path.join(root, filename)
                            rel_path = os.path.relpath(file_path, validated_path)
                            
                            # 获取文件信息
                            stat = os.stat(file_path)
                            matched_files.append({
                                "name": filename,
                                "path": rel_path,
                                "full_path": file_path,
                                "size": stat.st_size,
                                "is_dir": False,
                                "modified_time": stat.st_mtime
                            })
            else:
                # 非递归搜索
                for item in os.listdir(validated_path):
                    item_path = os.path.join(validated_path, item)
                    
                    # 只检查文件
                    if os.path.isfile(item_path):
                        # 检查文件名是否匹配模式
                        if case_sensitive:
                            match = fnmatch.fnmatch(item, pattern)
                        else:
                            match = fnmatch.fnmatch(item.lower(), pattern.lower())
                        
                        if match:
                            # 获取文件信息
                            stat = os.stat(item_path)
                            matched_files.append({
                                "name": item,
                                "path": item,
                                "full_path": item_path,
                                "size": stat.st_size,
                                "is_dir": False,
                                "modified_time": stat.st_mtime
                            })
            
            self.logger.info(f"搜索文件: {dir_path} (模式: {pattern})")
            return matched_files
        except Exception as e:
            raise FileOperationError(f"搜索文件失败: {str(e)}")