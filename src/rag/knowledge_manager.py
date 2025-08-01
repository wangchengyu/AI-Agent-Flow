"""
知识管理器

负责统一管理RAG知识管理模块的各个组件，
提供知识库的构建、更新、检索和管理功能。
"""

import os
import time
from typing import Any, Dict, List, Optional, Union, Tuple

from .document_processor import DocumentProcessor
from .vector_embedder import VectorEmbedder
from .vector_database import VectorDatabase
from .retriever import Retriever
from .reranker import Reranker
from ..database.knowledge_source_manager import KnowledgeSourceManager
from ..utils.exceptions import KnowledgeManagerError


class KnowledgeManager:
    """知识管理器，负责统一管理RAG知识管理模块的各个组件"""
    
    def __init__(self, db_manager, 
                 vector_db_name: str = "agent_flow_knowledge",
                 vector_db_path: str = "./chroma_db",
                 embedder_model: str = "moka-ai/m3e-small",
                 reranker_model: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
                 chunk_size: int = 1000, 
                 chunk_overlap: int = 200):
        """
        初始化知识管理器
        
        Args:
            db_manager: 数据库管理器
            vector_db_name: 向量数据库名称
            vector_db_path: 向量数据库路径
            embedder_model: 嵌入器模型名称
            reranker_model: 重排序器模型名称
            chunk_size: 分块大小
            chunk_overlap: 分块重叠大小
        """
        self.db_manager = db_manager
        self.knowledge_source_manager = KnowledgeSourceManager(db_manager)
        
        # 初始化各个组件
        self.document_processor = DocumentProcessor(chunk_size, chunk_overlap)
        self.vector_embedder = VectorEmbedder(embedder_model)
        self.vector_db = VectorDatabase(vector_db_name, vector_db_path)
        self.retriever = Retriever(self.vector_db, self.vector_embedder)
        self.reranker = Reranker(reranker_model)
        
        # 配置参数
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedder_model = embedder_model
        self.reranker_model = reranker_model
    
    def add_knowledge_source(self, name: str, path: str, description: Optional[str] = None) -> int:
        """
        添加知识源
        
        Args:
            name: 知识源名称
            path: 知识源路径
            description: 知识源描述
            
        Returns:
            知识源ID
        """
        try:
            # 添加知识源到数据库
            source_id = self.knowledge_source_manager.create_knowledge_source(name, path, description)
            
            return source_id
        except Exception as e:
            raise KnowledgeManagerError(f"添加知识源失败: {str(e)}")
    
    def build_knowledge_base(self, source_id: Optional[int] = None, 
                           recursive: bool = True, 
                           update_existing: bool = False) -> Dict:
        """
        构建知识库
        
        Args:
            source_id: 知识源ID，如果为None则处理所有活跃知识源
            recursive: 是否递归处理子目录
            update_existing: 是否更新已存在的文档
            
        Returns:
            构建结果字典
        """
        try:
            result = {
                "processed_files": 0,
                "processed_chunks": 0,
                "added_documents": 0,
                "updated_documents": 0,
                "errors": []
            }
            
            # 获取知识源
            if source_id:
                knowledge_sources = [self.knowledge_source_manager.get_knowledge_source(source_id)]
            else:
                knowledge_sources = self.knowledge_source_manager.get_active_knowledge_sources()
            
            if not knowledge_sources:
                result["errors"].append("没有找到活跃的知识源")
                return result
            
            # 处理每个知识源
            for source in knowledge_sources:
                path = source["path"]
                
                # 验证路径
                validation_result = self.knowledge_source_manager.validate_knowledge_source_path(source["source_id"])
                if not validation_result["valid"]:
                    result["errors"].append(f"知识源 '{source['name']}' 路径无效: {validation_result['message']}")
                    continue
                
                # 处理文档
                try:
                    # 处理目录中的所有文档
                    chunks = self.document_processor.process_directory(path, recursive)
                    result["processed_files"] += validation_result["file_count"]
                    result["processed_chunks"] += len(chunks)
                    
                    if not chunks:
                        continue
                    
                    # 为文档块生成向量
                    embedded_chunks = self.vector_embedder.embed_documents(chunks)
                    
                    # 添加或更新文档到向量数据库
                    for chunk in embedded_chunks:
                        # 添加知识源信息到元数据
                        metadata = chunk.get("metadata", {})
                        metadata["source_id"] = source["source_id"]
                        metadata["source_name"] = source["name"]
                        chunk["metadata"] = metadata
                        
                        # 检查文档是否已存在
                        existing_docs = self.vector_db.list_documents(
                            limit=1,
                            where={"file_path": metadata.get("file_path"), "chunk_index": metadata.get("chunk_index")}
                        )
                        
                        if existing_docs and update_existing:
                            # 更新文档
                            doc_id = existing_docs[0]["id"]
                            self.vector_db.update_document(doc_id, chunk, chunk["embedding"])
                            result["updated_documents"] += 1
                        elif not existing_docs:
                            # 添加新文档
                            self.vector_db.add_documents([chunk], [chunk["embedding"]])
                            result["added_documents"] += 1
                except Exception as e:
                    result["errors"].append(f"处理知识源 '{source['name']}' 失败: {str(e)}")
            
            return result
        except Exception as e:
            raise KnowledgeManagerError(f"构建知识库失败: {str(e)}")
    
    def update_knowledge_base(self, source_id: Optional[int] = None) -> Dict:
        """
        更新知识库
        
        Args:
            source_id: 知识源ID，如果为None则更新所有活跃知识源
            
        Returns:
            更新结果字典
        """
        try:
            # 构建知识库，设置update_existing为True
            return self.build_knowledge_base(source_id, update_existing=True)
        except Exception as e:
            raise KnowledgeManagerError(f"更新知识库失败: {str(e)}")
    
    def search_knowledge(self, query: str, n_results: int = 10,
                        filters: Optional[Dict] = None,
                        use_reranking: bool = True,
                        min_score: float = 0.0) -> List[Dict]:
        """
        搜索知识
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            filters: 过滤条件
            use_reranking: 是否使用重排序
            min_score: 最小相似度分数
            
        Returns:
            搜索结果列表
        """
        try:
            # 检索相关文档
            results = self.retriever.retrieve(
                query=query,
                n_results=n_results,
                filters=filters,
                min_score=min_score,
                use_reranking=False  # 先不使用重排序，后面单独处理
            )
            
            # 如果使用重排序，则进行重排序
            if use_reranking and results:
                results = self.reranker.rerank(query, results, n_results)
            
            return results
        except Exception as e:
            raise KnowledgeManagerError(f"搜索知识失败: {str(e)}")
    
    def hybrid_search_knowledge(self, query: str, n_results: int = 10,
                              filters: Optional[Dict] = None,
                              vector_weight: float = 0.7,
                              keyword_weight: float = 0.3,
                              use_reranking: bool = True) -> List[Dict]:
        """
        混合搜索知识（向量检索 + 关键词检索）
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            filters: 过滤条件
            vector_weight: 向量检索权重
            keyword_weight: 关键词检索权重
            use_reranking: 是否使用重排序
            
        Returns:
            搜索结果列表
        """
        try:
            # 混合检索相关文档
            results = self.retriever.hybrid_retrieve(
                query=query,
                n_results=n_results,
                metadata_filters=filters,
                vector_weight=vector_weight,
                keyword_weight=keyword_weight
            )
            
            # 如果使用重排序，则进行重排序
            if use_reranking and results:
                results = self.reranker.rerank(query, results, n_results)
            
            return results
        except Exception as e:
            raise KnowledgeManagerError(f"混合搜索知识失败: {str(e)}")
    
    def diversity_search_knowledge(self, query: str, n_results: int = 10,
                                 filters: Optional[Dict] = None,
                                 lambda_param: float = 0.5) -> List[Dict]:
        """
        多样性搜索知识
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            filters: 过滤条件
            lambda_param: 相关性和多样性的平衡参数
            
        Returns:
            搜索结果列表
        """
        try:
            # 先检索相关文档
            results = self.retriever.retrieve(
                query=query,
                n_results=n_results * 3,  # 获取更多结果以便进行多样性重排序
                filters=filters,
                use_reranking=False
            )
            
            if not results:
                return []
            
            # 进行多样性重排序
            results = self.reranker.diversity_rerank(query, results, n_results, lambda_param)
            
            return results
        except Exception as e:
            raise KnowledgeManagerError(f"多样性搜索知识失败: {str(e)}")
    
    def get_knowledge_stats(self) -> Dict:
        """
        获取知识库统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 获取知识源统计信息
            source_stats = self.knowledge_source_manager.get_knowledge_source_stats()
            
            # 获取向量数据库统计信息
            db_info = self.vector_db.get_collection_info()
            
            # 获取嵌入器信息
            embedder_info = self.vector_embedder.get_model_info()
            
            # 获取重排序器信息
            reranker_info = self.reranker.get_model_info()
            
            # 获取文档处理器信息
            processor_info = {
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap
            }
            
            return {
                "knowledge_sources": source_stats,
                "vector_database": db_info,
                "embedder": embedder_info,
                "reranker": reranker_info,
                "document_processor": processor_info
            }
        except Exception as e:
            raise KnowledgeManagerError(f"获取知识库统计信息失败: {str(e)}")
    
    def clear_knowledge_base(self, source_id: Optional[int] = None):
        """
        清空知识库
        
        Args:
            source_id: 知识源ID，如果为None则清空所有知识
        """
        try:
            if source_id:
                # 删除特定知识源的文档
                filters = {"source_id": source_id}
                documents = self.vector_db.list_documents(where=filters)
                
                doc_ids = [doc["id"] for doc in documents]
                if doc_ids:
                    self.vector_db.delete_documents(doc_ids)
            else:
                # 清空整个向量数据库
                self.vector_db.clear_collection()
        except Exception as e:
            raise KnowledgeManagerError(f"清空知识库失败: {str(e)}")
    
    def delete_knowledge_source(self, source_id: int) -> bool:
        """
        删除知识源
        
        Args:
            source_id: 知识源ID
            
        Returns:
            删除是否成功
        """
        try:
            # 先删除知识源相关的文档
            self.clear_knowledge_base(source_id)
            
            # 删除知识源记录
            success = self.knowledge_source_manager.delete_knowledge_source(source_id)
            
            return success
        except Exception as e:
            raise KnowledgeManagerError(f"删除知识源失败: {str(e)}")
    
    def update_config(self, chunk_size: Optional[int] = None, 
                     chunk_overlap: Optional[int] = None,
                     embedder_model: Optional[str] = None,
                     reranker_model: Optional[str] = None):
        """
        更新配置
        
        Args:
            chunk_size: 分块大小
            chunk_overlap: 分块重叠大小
            embedder_model: 嵌入器模型名称
            reranker_model: 重排序器模型名称
        """
        try:
            # 更新文档处理器配置
            if chunk_size is not None or chunk_overlap is not None:
                self.document_processor.update_config(chunk_size, chunk_overlap)
                if chunk_size is not None:
                    self.chunk_size = chunk_size
                if chunk_overlap is not None:
                    self.chunk_overlap = chunk_overlap
            
            # 更新嵌入器模型
            if embedder_model is not None and embedder_model != self.embedder_model:
                self.vector_embedder = VectorEmbedder(embedder_model)
                self.retriever = Retriever(self.vector_db, self.vector_embedder)
                self.embedder_model = embedder_model
            
            # 更新重排序器模型
            if reranker_model is not None and reranker_model != self.reranker_model:
                self.reranker = Reranker(reranker_model)
                self.reranker_model = reranker_model
        except Exception as e:
            raise KnowledgeManagerError(f"更新配置失败: {str(e)}")
    
    def persist_knowledge_base(self):
        """持久化知识库"""
        try:
            self.vector_db.persist()
        except Exception as e:
            raise KnowledgeManagerError(f"持久化知识库失败: {str(e)}")