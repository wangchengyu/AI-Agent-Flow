"""
检索器

负责从向量数据库中检索相关文档，
支持多种检索策略和结果过滤。
"""

import re
from typing import Any, Dict, List, Optional, Union, Tuple

from .vector_database import VectorDatabase
from .vector_embedder import VectorEmbedder
from ..utils.exceptions import RetrievalError


class Retriever:
    """检索器，负责从向量数据库中检索相关文档"""
    
    def __init__(self, vector_db: VectorDatabase, embedder: VectorEmbedder):
        """
        初始化检索器
        
        Args:
            vector_db: 向量数据库
            embedder: 向量嵌入器
        """
        self.vector_db = vector_db
        self.embedder = embedder
    
    def retrieve(self, query: str, n_results: int = 5, 
                filters: Optional[Dict] = None,
                min_score: float = 0.0,
                use_reranking: bool = False) -> List[Dict]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            filters: 过滤条件
            min_score: 最小相似度分数
            use_reranking: 是否使用重排序
            
        Returns:
            检索结果列表
        """
        try:
            # 生成查询向量
            query_embedding = self.embedder.embed_text(query)
            
            # 执行向量搜索
            results = self.vector_db.search(
                query_text=query,
                query_embedding=query_embedding,
                n_results=n_results * 2 if use_reranking else n_results,  # 如果使用重排序，获取更多结果
                where=filters
            )
            
            # 过滤低分结果
            filtered_results = []
            for result in results:
                # 将距离转换为相似度分数（假设使用余弦距离）
                score = 1.0 - result["distance"]
                
                if score >= min_score:
                    result_copy = result.copy()
                    result_copy["score"] = score
                    filtered_results.append(result_copy)
            
            # 如果使用重排序，则进行重排序
            if use_reranking and filtered_results:
                filtered_results = self._rerank_results(query, filtered_results, n_results)
            
            return filtered_results[:n_results]
        except Exception as e:
            raise RetrievalError(f"检索文档失败: {str(e)}")
    
    def retrieve_by_metadata(self, metadata_filters: Dict, n_results: int = 20) -> List[Dict]:
        """
        根据元数据检索文档
        
        Args:
            metadata_filters: 元数据过滤条件
            n_results: 返回结果数量
            
        Returns:
            检索结果列表
        """
        try:
            # 从向量数据库中获取文档
            documents = self.vector_db.list_documents(
                limit=n_results,
                where=metadata_filters
            )
            
            # 为每个文档添加默认分数
            results = []
            for doc in documents:
                result = {
                    "id": doc["id"],
                    "content": doc["content"],
                    "metadata": doc["metadata"],
                    "score": 1.0  # 元数据匹配的文档默认分数为1.0
                }
                results.append(result)
            
            return results
        except Exception as e:
            raise RetrievalError(f"根据元数据检索文档失败: {str(e)}")
    
    def retrieve_by_keywords(self, query: str, n_results: int = 10, 
                          metadata_filters: Optional[Dict] = None) -> List[Dict]:
        """
        根据关键词检索文档
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            metadata_filters: 元数据过滤条件
            
        Returns:
            检索结果列表
        """
        try:
            # 提取关键词
            keywords = self._extract_keywords(query)
            
            if not keywords:
                return []
            
            # 构建文档内容过滤条件
            document_filter = {
                "$or": [
                    {"$contains": keyword} for keyword in keywords
                ]
            }
            
            # 从向量数据库中获取文档
            documents = self.vector_db.list_documents(
                limit=n_results * 5,  # 获取更多文档以便进行关键词匹配评分
                where=metadata_filters
            )
            
            # 对文档进行关键词匹配评分
            scored_documents = []
            for doc in documents:
                content = doc["content"].lower()
                score = 0.0
                
                # 计算关键词匹配分数
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    # 计算关键词出现次数
                    count = len(re.findall(r'\b' + re.escape(keyword_lower) + r'\b', content))
                    score += count
                
                # 如果分数大于0，则添加到结果列表
                if score > 0:
                    result = {
                        "id": doc["id"],
                        "content": doc["content"],
                        "metadata": doc["metadata"],
                        "score": score
                    }
                    scored_documents.append(result)
            
            # 按分数排序并返回前n_results个结果
            scored_documents.sort(key=lambda x: x["score"], reverse=True)
            
            return scored_documents[:n_results]
        except Exception as e:
            raise RetrievalError(f"根据关键词检索文档失败: {str(e)}")
    
    def hybrid_retrieve(self, query: str, n_results: int = 10,
                      metadata_filters: Optional[Dict] = None,
                      vector_weight: float = 0.7,
                      keyword_weight: float = 0.3) -> List[Dict]:
        """
        混合检索（向量检索 + 关键词检索）
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            metadata_filters: 元数据过滤条件
            vector_weight: 向量检索权重
            keyword_weight: 关键词检索权重
            
        Returns:
            检索结果列表
        """
        try:
            # 执行向量检索
            vector_results = self.retrieve(
                query=query,
                n_results=n_results * 2,
                filters=metadata_filters,
                use_reranking=False
            )
            
            # 执行关键词检索
            keyword_results = self.retrieve_by_keywords(
                query=query,
                n_results=n_results * 2,
                metadata_filters=metadata_filters
            )
            
            # 合并结果并计算综合分数
            combined_results = {}
            
            # 处理向量检索结果
            for result in vector_results:
                doc_id = result["id"]
                if doc_id not in combined_results:
                    combined_results[doc_id] = result.copy()
                    combined_results[doc_id]["vector_score"] = result["score"]
                    combined_results[doc_id]["keyword_score"] = 0.0
                else:
                    combined_results[doc_id]["vector_score"] = result["score"]
            
            # 处理关键词检索结果
            for result in keyword_results:
                doc_id = result["id"]
                if doc_id not in combined_results:
                    combined_results[doc_id] = result.copy()
                    combined_results[doc_id]["vector_score"] = 0.0
                    combined_results[doc_id]["keyword_score"] = result["score"]
                else:
                    combined_results[doc_id]["keyword_score"] = result["score"]
            
            # 计算综合分数
            final_results = []
            for doc_id, result in combined_results.items():
                # 归一化分数
                vector_score = result["vector_score"]
                keyword_score = result["keyword_score"]
                
                # 计算综合分数
                combined_score = (vector_score * vector_weight + keyword_score * keyword_weight)
                
                # 更新结果
                result["score"] = combined_score
                final_results.append(result)
            
            # 按综合分数排序
            final_results.sort(key=lambda x: x["score"], reverse=True)
            
            return final_results[:n_results]
        except Exception as e:
            raise RetrievalError(f"混合检索失败: {str(e)}")
    
    def _rerank_results(self, query: str, results: List[Dict], n_results: int) -> List[Dict]:
        """
        重排序结果
        
        Args:
            query: 查询文本
            results: 检索结果列表
            n_results: 返回结果数量
            
        Returns:
            重排序后的结果列表
        """
        try:
            # 这里可以使用更复杂的重排序算法
            # 目前使用简单的基于内容相关性的重排序
            
            # 提取查询关键词
            query_keywords = self._extract_keywords(query)
            
            # 对每个结果计算重排序分数
            reranked_results = []
            for result in results:
                content = result["content"].lower()
                
                # 计算关键词匹配分数
                keyword_score = 0.0
                for keyword in query_keywords:
                    keyword_lower = keyword.lower()
                    count = len(re.findall(r'\b' + re.escape(keyword_lower) + r'\b', content))
                    keyword_score += count
                
                # 计算重排序分数（结合原始分数和关键词匹配分数）
                original_score = result["score"]
                rerank_score = 0.7 * original_score + 0.3 * (keyword_score / len(query_keywords) if query_keywords else 0)
                
                # 更新结果
                result_copy = result.copy()
                result_copy["score"] = rerank_score
                reranked_results.append(result_copy)
            
            # 按重排序分数排序
            reranked_results.sort(key=lambda x: x["score"], reverse=True)
            
            return reranked_results[:n_results]
        except Exception as e:
            raise RetrievalError(f"重排序结果失败: {str(e)}")
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词
        
        Args:
            text: 输入文本
            
        Returns:
            关键词列表
        """
        try:
            # 简单的关键词提取
            # 移除标点符号和特殊字符
            text = re.sub(r'[^\w\s]', ' ', text)
            
            # 分词
            words = text.split()
            
            # 过滤停用词和短词
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'if', 'because', 'as', 'until', 'while',
                'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into',
                'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from',
                'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further',
                'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any',
                'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
                'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can',
                'will', 'just', 'don', 'should', 'now', 'd', 'll', 'm', 'o', 're', 've', 'y',
                'ain', 'aren', 'couldn', 'didn', 'doesn', 'hadn', 'hasn', 'haven', 'isn', 'ma',
                'mightn', 'mustn', 'needn', 'shan', 'shouldn', 'wasn', 'weren', 'won', 'wouldn',
                '的', '了', '和', '是', '在', '我', '有', '就', '不', '人', '都', '一', '个', '上',
                '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'
            }
            
            keywords = []
            for word in words:
                word_lower = word.lower()
                if len(word_lower) > 2 and word_lower not in stop_words:
                    keywords.append(word_lower)
            
            return keywords
        except Exception as e:
            raise RetrievalError(f"提取关键词失败: {str(e)}")
    
    def get_retrieval_stats(self) -> Dict:
        """
        获取检索统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 获取向量数据库信息
            db_info = self.vector_db.get_collection_info()
            
            # 获取嵌入器信息
            embedder_info = self.embedder.get_model_info()
            
            return {
                "vector_database": db_info,
                "embedder": embedder_info
            }
        except Exception as e:
            raise RetrievalError(f"获取检索统计信息失败: {str(e)}")