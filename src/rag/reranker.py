"""
重排序器

负责对检索结果进行重排序，提高检索结果的相关性，
支持多种重排序策略和模型。
"""

import os
import re
from typing import Any, Dict, List, Optional, Union, Tuple
import numpy as np
from sentence_transformers import CrossEncoder

from ..utils.exceptions import RerankingError


class Reranker:
    """重排序器，负责对检索结果进行重排序"""
    
    def __init__(self, model_name: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1", 
                 device: str = "cpu", batch_size: int = 32):
        """
        初始化重排序器
        
        Args:
            model_name: 重排序模型名称
            device: 计算设备
            batch_size: 批处理大小
        """
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载重排序模型"""
        try:
            # 加载交叉编码器模型
            self.model = CrossEncoder(self.model_name, device=self.device)
        except Exception as e:
            raise RerankingError(f"加载重排序模型失败: {str(e)}")
    
    def rerank(self, query: str, documents: List[Dict], n_results: int = 10) -> List[Dict]:
        """
        对检索结果进行重排序
        
        Args:
            query: 查询文本
            documents: 检索结果列表
            n_results: 返回结果数量
            
        Returns:
            重排序后的结果列表
        """
        try:
            if not documents:
                return []
            
            # 提取文档内容
            doc_contents = [doc.get("content", "") for doc in documents]
            
            # 准备查询-文档对
            pairs = [(query, doc_content) for doc_content in doc_contents]
            
            # 批量预测相关性分数
            scores = self.model.predict(pairs, batch_size=self.batch_size)
            
            # 将分数添加到文档中
            reranked_docs = []
            for i, doc in enumerate(documents):
                doc_copy = doc.copy()
                doc_copy["rerank_score"] = float(scores[i])
                reranked_docs.append(doc_copy)
            
            # 按重排序分数降序排序
            reranked_docs.sort(key=lambda x: x["rerank_score"], reverse=True)
            
            return reranked_docs[:n_results]
        except Exception as e:
            raise RerankingError(f"重排序失败: {str(e)}")
    
    def hybrid_rerank(self, query: str, documents: List[Dict], n_results: int = 10,
                     vector_weight: float = 0.4, keyword_weight: float = 0.3,
                     cross_encoder_weight: float = 0.3) -> List[Dict]:
        """
        混合重排序（结合向量分数、关键词匹配分数和交叉编码器分数）
        
        Args:
            query: 查询文本
            documents: 检索结果列表
            n_results: 返回结果数量
            vector_weight: 向量分数权重
            keyword_weight: 关键词匹配分数权重
            cross_encoder_weight: 交叉编码器分数权重
            
        Returns:
            重排序后的结果列表
        """
        try:
            if not documents:
                return []
            
            # 计算交叉编码器分数
            cross_encoder_scores = self._compute_cross_encoder_scores(query, documents)
            
            # 计算关键词匹配分数
            keyword_scores = self._compute_keyword_scores(query, documents)
            
            # 计算综合分数
            reranked_docs = []
            for i, doc in enumerate(documents):
                doc_copy = doc.copy()
                
                # 获取各种分数
                vector_score = doc.get("score", 0.0)
                keyword_score = keyword_scores[i]
                cross_encoder_score = cross_encoder_scores[i]
                
                # 归一化分数
                normalized_vector_score = self._normalize_score(vector_score, documents, "score")
                normalized_keyword_score = self._normalize_score(keyword_score, keyword_scores)
                normalized_cross_encoder_score = self._normalize_score(cross_encoder_score, cross_encoder_scores)
                
                # 计算综合分数
                combined_score = (
                    normalized_vector_score * vector_weight +
                    normalized_keyword_score * keyword_weight +
                    normalized_cross_encoder_score * cross_encoder_weight
                )
                
                doc_copy["rerank_score"] = combined_score
                doc_copy["vector_score"] = vector_score
                doc_copy["keyword_score"] = keyword_score
                doc_copy["cross_encoder_score"] = cross_encoder_score
                
                reranked_docs.append(doc_copy)
            
            # 按综合分数降序排序
            reranked_docs.sort(key=lambda x: x["rerank_score"], reverse=True)
            
            return reranked_docs[:n_results]
        except Exception as e:
            raise RerankingError(f"混合重排序失败: {str(e)}")
    
    def _compute_cross_encoder_scores(self, query: str, documents: List[Dict]) -> List[float]:
        """
        计算交叉编码器分数
        
        Args:
            query: 查询文本
            documents: 文档列表
            
        Returns:
            交叉编码器分数列表
        """
        try:
            # 提取文档内容
            doc_contents = [doc.get("content", "") for doc in documents]
            
            # 准备查询-文档对
            pairs = [(query, doc_content) for doc_content in doc_contents]
            
            # 批量预测相关性分数
            scores = self.model.predict(pairs, batch_size=self.batch_size)
            
            return [float(score) for score in scores]
        except Exception as e:
            raise RerankingError(f"计算交叉编码器分数失败: {str(e)}")
    
    def _compute_keyword_scores(self, query: str, documents: List[Dict]) -> List[float]:
        """
        计算关键词匹配分数
        
        Args:
            query: 查询文本
            documents: 文档列表
            
        Returns:
            关键词匹配分数列表
        """
        try:
            # 提取查询关键词
            query_keywords = self._extract_keywords(query)
            
            if not query_keywords:
                return [0.0] * len(documents)
            
            # 计算每个文档的关键词匹配分数
            keyword_scores = []
            for doc in documents:
                content = doc.get("content", "").lower()
                score = 0.0
                
                # 计算关键词匹配分数
                for keyword in query_keywords:
                    keyword_lower = keyword.lower()
                    # 计算关键词出现次数
                    count = len(re.findall(r'\b' + re.escape(keyword_lower) + r'\b', content))
                    score += count
                
                # 归一化分数
                normalized_score = score / len(query_keywords) if query_keywords else 0.0
                keyword_scores.append(normalized_score)
            
            return keyword_scores
        except Exception as e:
            raise RerankingError(f"计算关键词匹配分数失败: {str(e)}")
    
    def _normalize_score(self, score: float, scores: List[float], score_key: Optional[str] = None) -> float:
        """
        归一化分数
        
        Args:
            score: 原始分数
            scores: 所有分数列表
            score_key: 分数键名（如果从文档中提取）
            
        Returns:
            归一化后的分数
        """
        try:
            # 如果从文档中提取分数
            if score_key:
                all_scores = [doc.get(score_key, 0.0) for doc in scores]
            else:
                all_scores = scores
            
            # 计算最小值和最大值
            min_score = min(all_scores)
            max_score = max(all_scores)
            
            # 如果所有分数相同，则返回0.5
            if min_score == max_score:
                return 0.5
            
            # 归一化到[0, 1]范围
            normalized_score = (score - min_score) / (max_score - min_score)
            
            return normalized_score
        except Exception as e:
            raise RerankingError(f"归一化分数失败: {str(e)}")
    
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
            raise RerankingError(f"提取关键词失败: {str(e)}")
    
    def diversity_rerank(self, query: str, documents: List[Dict], n_results: int = 10,
                        lambda_param: float = 0.5) -> List[Dict]:
        """
        多样性重排序（MMR算法）
        
        Args:
            query: 查询文本
            documents: 检索结果列表
            n_results: 返回结果数量
            lambda_param: 相关性和多样性的平衡参数
            
        Returns:
            重排序后的结果列表
        """
        try:
            if not documents:
                return []
            
            # 计算交叉编码器分数
            cross_encoder_scores = self._compute_cross_encoder_scores(query, documents)
            
            # 初始化结果列表和剩余文档
            selected_docs = []
            remaining_docs = list(range(len(documents)))
            
            # 选择相关性最高的文档作为第一个结果
            first_doc_idx = np.argmax(cross_encoder_scores)
            selected_docs.append(first_doc_idx)
            remaining_docs.remove(first_doc_idx)
            
            # 迭代选择剩余文档
            while len(selected_docs) < min(n_results, len(documents)) and remaining_docs:
                max_score = -float('inf')
                best_doc_idx = -1
                
                # 计算每个剩余文档的MMR分数
                for doc_idx in remaining_docs:
                    # 计算相关性分数
                    relevance_score = cross_encoder_scores[doc_idx]
                    
                    # 计算与已选文档的最大相似度
                    max_similarity = 0.0
                    for selected_idx in selected_docs:
                        # 计算文档相似度（这里简化为基于关键词重叠的相似度）
                        similarity = self._compute_document_similarity(
                            documents[doc_idx].get("content", ""),
                            documents[selected_idx].get("content", "")
                        )
                        max_similarity = max(max_similarity, similarity)
                    
                    # 计算MMR分数
                    mmr_score = lambda_param * relevance_score - (1 - lambda_param) * max_similarity
                    
                    if mmr_score > max_score:
                        max_score = mmr_score
                        best_doc_idx = doc_idx
                
                # 选择最佳文档
                selected_docs.append(best_doc_idx)
                remaining_docs.remove(best_doc_idx)
            
            # 构建结果列表
            reranked_docs = []
            for i, doc_idx in enumerate(selected_docs):
                doc = documents[doc_idx]
                doc_copy = doc.copy()
                doc_copy["rerank_score"] = cross_encoder_scores[doc_idx]
                doc_copy["rank"] = i + 1
                reranked_docs.append(doc_copy)
            
            return reranked_docs
        except Exception as e:
            raise RerankingError(f"多样性重排序失败: {str(e)}")
    
    def _compute_document_similarity(self, content1: str, content2: str) -> float:
        """
        计算两个文档之间的相似度
        
        Args:
            content1: 文档1内容
            content2: 文档2内容
            
        Returns:
            相似度分数
        """
        try:
            # 提取关键词
            keywords1 = set(self._extract_keywords(content1))
            keywords2 = set(self._extract_keywords(content2))
            
            if not keywords1 or not keywords2:
                return 0.0
            
            # 计算Jaccard相似度
            intersection = len(keywords1.intersection(keywords2))
            union = len(keywords1.union(keywords2))
            
            similarity = intersection / union if union > 0 else 0.0
            
            return similarity
        except Exception as e:
            raise RerankingError(f"计算文档相似度失败: {str(e)}")
    
    def get_model_info(self) -> Dict:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        return {
            "model_name": self.model_name,
            "device": self.device,
            "batch_size": self.batch_size
        }