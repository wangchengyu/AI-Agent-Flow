"""
向量数据库

负责向量的存储、检索和管理，基于ChromaDB实现，
提供高效的向量相似度搜索能力。
"""

import os
import uuid
import json
from typing import Any, Dict, List, Optional, Union, Tuple
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from ..utils.exceptions import VectorDatabaseError


class VectorDatabase:
    """向量数据库，负责向量的存储和检索"""
    
    def __init__(self, collection_name: str = "agent_flow_knowledge", 
                 persist_directory: str = "./chroma_db",
                 distance_metric: str = "cosine"):
        """
        初始化向量数据库
        
        Args:
            collection_name: 集合名称
            persist_directory: 持久化目录
            distance_metric: 距离度量
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.distance_metric = distance_metric
        self.client = None
        self.collection = None
        self._initialize_client()
        self._get_or_create_collection()
    
    def _initialize_client(self):
        """初始化ChromaDB客户端"""
        try:
            # 确保持久化目录存在
            if self.persist_directory and not os.path.exists(self.persist_directory):
                os.makedirs(self.persist_directory)
            
            # 初始化客户端
            if self.persist_directory:
                self.client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=Settings(anonymized_telemetry=False)
                )
            else:
                self.client = chromadb.Client(
                    settings=Settings(anonymized_telemetry=False)
                )
        except Exception as e:
            raise VectorDatabaseError(f"初始化向量数据库客户端失败: {str(e)}")
    
    def _get_or_create_collection(self):
        """获取或创建集合"""
        try:
            # 获取集合
            self.collection = self.client.get_collection(
                name=self.collection_name
            )
        except Exception:
            # 如果集合不存在，则创建
            try:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": self.distance_metric}
                )
            except Exception as e:
                raise VectorDatabaseError(f"创建集合失败: {str(e)}")
    
    def add_documents(self, documents: List[Dict], embeddings: Optional[List[List[float]]] = None) -> List[str]:
        """
        添加文档到向量数据库
        
        Args:
            documents: 文档列表，每个文档应包含content和metadata字段
            embeddings: 文档向量列表，如果为None则使用默认嵌入函数
            
        Returns:
            文档ID列表
        """
        try:
            if not documents:
                return []
            
            # 提取文档内容
            texts = [doc.get("content", "") for doc in documents]
            
            # 提取元数据
            metadatas = []
            for doc in documents:
                metadata = doc.get("metadata", {})
                # 确保元数据是JSON可序列化的
                for key, value in metadata.items():
                    if isinstance(value, (list, dict)):
                        metadata[key] = json.dumps(value)
                metadatas.append(metadata)
            
            # 生成文档ID
            ids = [str(uuid.uuid4()) for _ in documents]
            
            # 添加文档
            if embeddings:
                self.collection.add(
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
            else:
                self.collection.add(
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
            
            return ids
        except Exception as e:
            raise VectorDatabaseError(f"添加文档失败: {str(e)}")
    
    def update_document(self, doc_id: str, document: Dict, embedding: Optional[List[float]] = None):
        """
        更新向量数据库中的文档
        
        Args:
            doc_id: 文档ID
            document: 文档内容，应包含content和metadata字段
            embedding: 文档向量，如果为None则使用默认嵌入函数
        """
        try:
            # 提取文档内容
            text = document.get("content", "")
            
            # 提取元数据
            metadata = document.get("metadata", {})
            # 确保元数据是JSON可序列化的
            for key, value in metadata.items():
                if isinstance(value, (list, dict)):
                    metadata[key] = json.dumps(value)
            
            # 更新文档
            if embedding:
                self.collection.update(
                    embeddings=[embedding],
                    documents=[text],
                    metadatas=[metadata],
                    ids=[doc_id]
                )
            else:
                self.collection.update(
                    documents=[text],
                    metadatas=[metadata],
                    ids=[doc_id]
                )
        except Exception as e:
            raise VectorDatabaseError(f"更新文档失败: {str(e)}")
    
    def delete_document(self, doc_id: str):
        """
        从向量数据库中删除文档
        
        Args:
            doc_id: 文档ID
        """
        try:
            self.collection.delete(ids=[doc_id])
        except Exception as e:
            raise VectorDatabaseError(f"删除文档失败: {str(e)}")
    
    def delete_documents(self, doc_ids: List[str]):
        """
        从向量数据库中批量删除文档
        
        Args:
            doc_ids: 文档ID列表
        """
        try:
            self.collection.delete(ids=doc_ids)
        except Exception as e:
            raise VectorDatabaseError(f"批量删除文档失败: {str(e)}")
    
    def search(self, query_text: str, query_embedding: Optional[List[float]] = None, 
              n_results: int = 5, where: Optional[Dict] = None,
              where_document: Optional[Dict] = None) -> List[Dict]:
        """
        搜索相似文档
        
        Args:
            query_text: 查询文本
            query_embedding: 查询向量，如果为None则使用默认嵌入函数
            n_results: 返回结果数量
            where: 元数据过滤条件
            where_document: 文档内容过滤条件
            
        Returns:
            搜索结果列表
        """
        try:
            # 执行搜索
            if query_embedding:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=where,
                    where_document=where_document
                )
            else:
                results = self.collection.query(
                    query_texts=[query_text],
                    n_results=n_results,
                    where=where,
                    where_document=where_document
                )
            
            # 处理结果
            processed_results = []
            
            for i in range(len(results["ids"][0])):
                doc_id = results["ids"][0][i]
                document = results["documents"][0][i]
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i]
                
                # 处理元数据中的JSON字符串
                for key, value in metadata.items():
                    if isinstance(value, str):
                        try:
                            parsed_value = json.loads(value)
                            metadata[key] = parsed_value
                        except json.JSONDecodeError:
                            pass
                
                processed_results.append({
                    "id": doc_id,
                    "content": document,
                    "metadata": metadata,
                    "distance": distance
                })
            
            return processed_results
        except Exception as e:
            raise VectorDatabaseError(f"搜索文档失败: {str(e)}")
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """
        获取文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            文档信息，如果不存在则返回None
        """
        try:
            results = self.collection.get(ids=[doc_id])
            
            if not results["ids"]:
                return None
            
            # 处理元数据中的JSON字符串
            metadata = results["metadatas"][0]
            for key, value in metadata.items():
                if isinstance(value, str):
                    try:
                        parsed_value = json.loads(value)
                        metadata[key] = parsed_value
                    except json.JSONDecodeError:
                        pass
            
            return {
                "id": results["ids"][0],
                "content": results["documents"][0],
                "metadata": metadata
            }
        except Exception as e:
            raise VectorDatabaseError(f"获取文档失败: {str(e)}")
    
    def list_documents(self, limit: int = 20, offset: int = 0, 
                     where: Optional[Dict] = None) -> List[Dict]:
        """
        列出文档
        
        Args:
            limit: 限制数量
            offset: 偏移量
            where: 元数据过滤条件
            
        Returns:
            文档列表
        """
        try:
            # 获取所有文档ID
            if where:
                results = self.collection.get(where=where)
            else:
                results = self.collection.get()
            
            # 处理结果
            documents = []
            
            for i in range(len(results["ids"])):
                # 应用偏移量和限制
                if i < offset:
                    continue
                if i >= offset + limit:
                    break
                
                doc_id = results["ids"][i]
                document = results["documents"][i]
                metadata = results["metadatas"][i]
                
                # 处理元数据中的JSON字符串
                for key, value in metadata.items():
                    if isinstance(value, str):
                        try:
                            parsed_value = json.loads(value)
                            metadata[key] = parsed_value
                        except json.JSONDecodeError:
                            pass
                
                documents.append({
                    "id": doc_id,
                    "content": document,
                    "metadata": metadata
                })
            
            return documents
        except Exception as e:
            raise VectorDatabaseError(f"列出文档失败: {str(e)}")
    
    def get_document_count(self, where: Optional[Dict] = None) -> int:
        """
        获取文档数量
        
        Args:
            where: 元数据过滤条件
            
        Returns:
            文档数量
        """
        try:
            # 获取所有文档ID
            if where:
                results = self.collection.get(where=where)
            else:
                results = self.collection.get()
            
            return len(results["ids"])
        except Exception as e:
            raise VectorDatabaseError(f"获取文档数量失败: {str(e)}")
    
    def clear_collection(self):
        """清空集合"""
        try:
            # 获取所有文档ID
            results = self.collection.get()
            doc_ids = results["ids"]
            
            # 删除所有文档
            if doc_ids:
                self.collection.delete(ids=doc_ids)
        except Exception as e:
            raise VectorDatabaseError(f"清空集合失败: {str(e)}")
    
    def delete_collection(self):
        """删除集合"""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = None
        except Exception as e:
            raise VectorDatabaseError(f"删除集合失败: {str(e)}")
    
    def get_collection_info(self) -> Dict:
        """
        获取集合信息
        
        Returns:
            集合信息字典
        """
        try:
            # 获取集合
            collection = self.client.get_collection(name=self.collection_name)
            
            # 获取文档数量
            count = self.get_document_count()
            
            return {
                "name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory,
                "distance_metric": self.distance_metric
            }
        except Exception as e:
            raise VectorDatabaseError(f"获取集合信息失败: {str(e)}")
    
    def persist(self):
        """持久化数据"""
        try:
            if self.persist_directory:
                # ChromaDB会自动持久化，这里不需要额外操作
                pass
        except Exception as e:
            raise VectorDatabaseError(f"持久化数据失败: {str(e)}")