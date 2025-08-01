"""
文档处理器

负责文档的加载、解析、分块和预处理等功能，
为后续的向量化和检索提供基础。
"""

import os
import re
import json
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
import markdown
from bs4 import BeautifulSoup

from ..utils.exceptions import DocumentProcessingError


class DocumentProcessor:
    """文档处理器，负责文档的加载、解析和分块"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        初始化文档处理器
        
        Args:
            chunk_size: 分块大小
            chunk_overlap: 分块重叠大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.supported_formats = [".md", ".txt", ".py", ".js", ".json"]
    
    def load_document(self, file_path: str) -> Dict:
        """
        加载文档
        
        Args:
            file_path: 文档路径
            
        Returns:
            文档信息字典
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise DocumentProcessingError(f"文件 '{file_path}' 不存在")
            
            # 获取文件信息
            file_path_obj = Path(file_path)
            file_name = file_path_obj.name
            file_ext = file_path_obj.suffix.lower()
            
            # 检查文件格式是否支持
            if file_ext not in self.supported_formats:
                raise DocumentProcessingError(f"不支持的文件格式 '{file_ext}'")
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析内容
            parsed_content = self._parse_content(content, file_ext)
            
            # 构建文档信息
            document = {
                "file_path": file_path,
                "file_name": file_name,
                "file_ext": file_ext,
                "content": content,
                "parsed_content": parsed_content,
                "metadata": {
                    "size": len(content),
                    "created_at": os.path.getctime(file_path),
                    "modified_at": os.path.getmtime(file_path)
                }
            }
            
            return document
        except Exception as e:
            raise DocumentProcessingError(f"加载文档失败: {str(e)}")
    
    def _parse_content(self, content: str, file_ext: str) -> str:
        """
        解析内容
        
        Args:
            content: 原始内容
            file_ext: 文件扩展名
            
        Returns:
            解析后的内容
        """
        try:
            if file_ext == ".md":
                # 解析Markdown
                html = markdown.markdown(content)
                soup = BeautifulSoup(html, 'html.parser')
                
                # 移除代码块
                for code in soup.find_all('code'):
                    code.decompose()
                
                # 移除链接
                for link in soup.find_all('a'):
                    link.decompose()
                
                # 获取纯文本
                parsed_content = soup.get_text()
                
                # 清理多余的空白字符
                parsed_content = re.sub(r'\s+', ' ', parsed_content).strip()
                
                return parsed_content
            
            elif file_ext == ".json":
                # 解析JSON
                try:
                    json_data = json.loads(content)
                    return json.dumps(json_data, indent=2, ensure_ascii=False)
                except json.JSONDecodeError:
                    return content
            
            elif file_ext in [".py", ".js"]:
                # 移除注释
                lines = content.split('\n')
                cleaned_lines = []
                
                for line in lines:
                    # 移除单行注释
                    if file_ext == ".py":
                        line = re.sub(r'#.*$', '', line)
                    elif file_ext == ".js":
                        line = re.sub(r'//.*$', '', line)
                    
                    cleaned_lines.append(line)
                
                # 移除多行注释
                cleaned_content = '\n'.join(cleaned_lines)
                
                if file_ext == ".py":
                    cleaned_content = re.sub(r'""".*?"""', '', cleaned_content, flags=re.DOTALL)
                    cleaned_content = re.sub(r"'''.*?'''", '', cleaned_content, flags=re.DOTALL)
                elif file_ext == ".js":
                    cleaned_content = re.sub(r'/\*.*?\*/', '', cleaned_content, flags=re.DOTALL)
                
                # 清理多余的空白字符
                cleaned_content = re.sub(r'\s+', ' ', cleaned_content).strip()
                
                return cleaned_content
            
            else:  # .txt
                # 清理多余的空白字符
                cleaned_content = re.sub(r'\s+', ' ', content).strip()
                return cleaned_content
        except Exception as e:
            raise DocumentProcessingError(f"解析内容失败: {str(e)}")
    
    def chunk_document(self, document: Dict) -> List[Dict]:
        """
        分块文档
        
        Args:
            document: 文档信息字典
            
        Returns:
            文档块列表
        """
        try:
            content = document["parsed_content"]
            chunks = []
            
            # 如果内容小于分块大小，直接作为一个块
            if len(content) <= self.chunk_size:
                chunks.append({
                    "content": content,
                    "start_index": 0,
                    "end_index": len(content),
                    "metadata": {
                        "file_path": document["file_path"],
                        "file_name": document["file_name"],
                        "chunk_index": 0
                    }
                })
            else:
                # 否则进行分块
                start_index = 0
                chunk_index = 0
                
                while start_index < len(content):
                    # 计算结束索引
                    end_index = min(start_index + self.chunk_size, len(content))
                    
                    # 如果不是最后一个块，尝试在句子边界处分割
                    if end_index < len(content):
                        # 寻找最近的句子边界
                        sentence_end = max(
                            content.rfind('.', start_index, end_index),
                            content.rfind('!', start_index, end_index),
                            content.rfind('?', start_index, end_index),
                            content.rfind('\n', start_index, end_index)
                        )
                        
                        if sentence_end > start_index + self.chunk_size // 2:
                            end_index = sentence_end + 1
                    
                    # 提取块内容
                    chunk_content = content[start_index:end_index].strip()
                    
                    # 如果块内容不为空，则添加到块列表
                    if chunk_content:
                        chunks.append({
                            "content": chunk_content,
                            "start_index": start_index,
                            "end_index": end_index,
                            "metadata": {
                                "file_path": document["file_path"],
                                "file_name": document["file_name"],
                                "chunk_index": chunk_index
                            }
                        })
                        
                        chunk_index += 1
                    
                    # 更新开始索引，考虑重叠
                    start_index = end_index - self.chunk_overlap if end_index < len(content) else end_index
            
            return chunks
        except Exception as e:
            raise DocumentProcessingError(f"分块文档失败: {str(e)}")
    
    def process_directory(self, directory_path: str, recursive: bool = True) -> List[Dict]:
        """
        处理目录中的所有文档
        
        Args:
            directory_path: 目录路径
            recursive: 是否递归处理子目录
            
        Returns:
            文档块列表
        """
        try:
            all_chunks = []
            
            # 遍历目录
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = Path(file).suffix.lower()
                    
                    # 检查文件格式是否支持
                    if file_ext in self.supported_formats:
                        # 加载文档
                        document = self.load_document(file_path)
                        
                        # 分块文档
                        chunks = self.chunk_document(document)
                        
                        # 添加到总块列表
                        all_chunks.extend(chunks)
                
                # 如果不递归处理子目录，则跳出循环
                if not recursive:
                    break
            
            return all_chunks
        except Exception as e:
            raise DocumentProcessingError(f"处理目录失败: {str(e)}")
    
    def get_document_stats(self, directory_path: str, recursive: bool = True) -> Dict:
        """
        获取文档统计信息
        
        Args:
            directory_path: 目录路径
            recursive: 是否递归处理子目录
            
        Returns:
            统计信息字典
        """
        try:
            stats = {
                "total_files": 0,
                "supported_files": 0,
                "unsupported_files": 0,
                "file_types": {},
                "total_chars": 0,
                "total_chunks": 0,
                "avg_chunk_size": 0
            }
            
            total_chunk_size = 0
            
            # 遍历目录
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = Path(file).suffix.lower()
                    
                    stats["total_files"] += 1
                    
                    if file_ext in self.supported_formats:
                        stats["supported_files"] += 1
                        
                        # 更新文件类型统计
                        if file_ext not in stats["file_types"]:
                            stats["file_types"][file_ext] = 0
                        stats["file_types"][file_ext] += 1
                        
                        # 加载文档
                        document = self.load_document(file_path)
                        
                        # 更新字符统计
                        stats["total_chars"] += len(document["parsed_content"])
                        
                        # 分块文档
                        chunks = self.chunk_document(document)
                        
                        # 更新块统计
                        stats["total_chunks"] += len(chunks)
                        
                        # 计算总块大小
                        for chunk in chunks:
                            total_chunk_size += len(chunk["content"])
                    else:
                        stats["unsupported_files"] += 1
                
                # 如果不递归处理子目录，则跳出循环
                if not recursive:
                    break
            
            # 计算平均块大小
            if stats["total_chunks"] > 0:
                stats["avg_chunk_size"] = total_chunk_size / stats["total_chunks"]
            
            return stats
        except Exception as e:
            raise DocumentProcessingError(f"获取文档统计信息失败: {str(e)}")
    
    def update_config(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        """
        更新配置
        
        Args:
            chunk_size: 分块大小
            chunk_overlap: 分块重叠大小
        """
        if chunk_size is not None:
            self.chunk_size = chunk_size
        
        if chunk_overlap is not None:
            self.chunk_overlap = chunk_overlap