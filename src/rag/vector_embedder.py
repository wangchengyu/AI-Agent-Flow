"""
向量嵌入器

负责将文本转换为向量表示，支持多种预训练模型，
为后续的向量检索提供基础。
"""

import os
import numpy as np
from typing import Any, Dict, List, Optional, Union
from sentence_transformers import SentenceTransformer

from ..utils.exceptions import EmbeddingError


class VectorEmbedder:
    """向量嵌入器，负责将文本转换为向量表示"""
    
    def __init__(self, model_name: str = "moka-ai/m3e-small", normalize_embeddings: bool = True):
        """
        初始化向量嵌入器
        
        Args:
            model_name: 模型名称
            normalize_embeddings: 是否对嵌入向量进行归一化
        """
        self.model_name = model_name
        self.normalize_embeddings = normalize_embeddings
        self.model = None
        self.dimension = None
        self._load_model()
    
    def _load_model(self):
        """加载模型"""
        try:
            # 加载预训练模型
            self.model = SentenceTransformer(self.model_name)
            
            # 获取向量维度
            test_embedding = self.embed_text("test")
            self.dimension = len(test_embedding)
        except Exception as e:
            raise EmbeddingError(f"加载模型失败: {str(e)}")
    
    def embed_text(self, text: str) -> List[float]:
        """
        将文本转换为向量
        
        Args:
            text: 输入文本
            
        Returns:
            向量表示
        """
        try:
            if not text or not text.strip():
                # 返回零向量
                return [0.0] * self.dimension
            
            # 使用模型生成向量
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            # 转换为列表
            embedding = embedding.tolist()
            
            # 归一化
            if self.normalize_embeddings:
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = [x / norm for x in embedding]
            
            return embedding
        except Exception as e:
            raise EmbeddingError(f"文本嵌入失败: {str(e)}")
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量将文本转换为向量
        
        Args:
            texts: 输入文本列表
            
        Returns:
            向量表示列表
        """
        try:
            if not texts:
                return []
            
            # 过滤空文本
            valid_texts = [text for text in texts if text and text.strip()]
            
            if not valid_texts:
                # 如果没有有效文本，返回零向量列表
                return [[0.0] * self.dimension for _ in texts]
            
            # 使用模型批量生成向量
            embeddings = self.model.encode(valid_texts, convert_to_numpy=True)
            
            # 转换为列表
            embeddings = [embedding.tolist() for embedding in embeddings]
            
            # 归一化
            if self.normalize_embeddings:
                embeddings = [
                    [x / np.linalg.norm(embedding) for x in embedding] 
                    if np.linalg.norm(embedding) > 0 else embedding
                    for embedding in embeddings
                ]
            
            # 处理空文本，返回零向量
            result = []
            text_index = 0
            for text in texts:
                if text and text.strip():
                    result.append(embeddings[text_index])
                    text_index += 1
                else:
                    result.append([0.0] * self.dimension)
            
            return result
        except Exception as e:
            raise EmbeddingError(f"批量文本嵌入失败: {str(e)}")
    
    def embed_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        将文档转换为向量
        
        Args:
            documents: 文档列表，每个文档应包含content字段
            
        Returns:
            带有向量的文档列表
        """
        try:
            if not documents:
                return []
            
            # 提取文本内容
            texts = [doc.get("content", "") for doc in documents]
            
            # 批量嵌入
            embeddings = self.embed_texts(texts)
            
            # 将向量添加到文档中
            result = []
            for i, doc in enumerate(documents):
                doc_copy = doc.copy()
                doc_copy["embedding"] = embeddings[i]
                result.append(doc_copy)
            
            return result
        except Exception as e:
            raise EmbeddingError(f"文档嵌入失败: {str(e)}")
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        计算两个向量之间的余弦相似度
        
        Args:
            embedding1: 向量1
            embedding2: 向量2
            
        Returns:
            相似度分数，范围[0, 1]
        """
        try:
            # 转换为numpy数组
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # 计算余弦相似度
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # 确保在[0, 1]范围内
            return max(0.0, min(1.0, similarity))
        except Exception as e:
            raise EmbeddingError(f"计算相似度失败: {str(e)}")
    
    def compute_similarities(self, query_embedding: List[float], document_embeddings: List[List[float]]) -> List[float]:
        """
        计算查询向量与文档向量之间的相似度
        
        Args:
            query_embedding: 查询向量
            document_embeddings: 文档向量列表
            
        Returns:
            相似度分数列表
        """
        try:
            if not document_embeddings:
                return []
            
            # 转换为numpy数组
            query_vec = np.array(query_embedding)
            doc_vecs = np.array(document_embeddings)
            
            # 计算余弦相似度
            dot_products = np.dot(doc_vecs, query_vec)
            query_norm = np.linalg.norm(query_vec)
            doc_norms = np.linalg.norm(doc_vecs, axis=1)
            
            # 避免除以零
            doc_norms[doc_norms == 0] = 1e-10
            if query_norm == 0:
                query_norm = 1e-10
            
            similarities = dot_products / (doc_norms * query_norm)
            
            # 确保在[0, 1]范围内
            similarities = np.clip(similarities, 0.0, 1.0)
            
            return similarities.tolist()
        except Exception as e:
            raise EmbeddingError(f"批量计算相似度失败: {str(e)}")
    
    def get_model_info(self) -> Dict:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "normalize_embeddings": self.normalize_embeddings
        }
    
    def save_model(self, save_path: str):
        """
        保存模型
        
        Args:
            save_path: 保存路径
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # 保存模型
            self.model.save(save_path)
        except Exception as e:
            raise EmbeddingError(f"保存模型失败: {str(e)}")
    
    def load_model_from_path(self, model_path: str):
        """
        从路径加载模型
        
        Args:
            model_path: 模型路径
        """
        try:
            # 加载模型
            self.model = SentenceTransformer(model_path)
            
            # 获取向量维度
            test_embedding = self.embed_text("test")
            self.dimension = len(test_embedding)
        except Exception as e:
            raise EmbeddingError(f"从路径加载模型失败: {str(e)}")