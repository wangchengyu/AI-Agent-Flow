"""
大模型客户端模块
与大模型API进行交互
"""

import openai
from typing import Dict, Any, List, Optional
import json


class LLMClient:
    """大模型客户端"""

    def __init__(self, base_url: str = None, api_key: str = None, model: str = "gpt-3.5-turbo"):
        """
        初始化大模型客户端
        
        Args:
            base_url: API基础URL
            api_key: API密钥
            model: 模型名称
        """
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        
        # 配置OpenAI客户端
        self.client = openai.OpenAI(
            base_url=base_url,
            api_key=api_key
        )

    def set_config(self, base_url: str = None, api_key: str = None, model: str = None):
        """
        设置配置
        
        Args:
            base_url: API基础URL
            api_key: API密钥
            model: 模型名称
        """
        if base_url is not None:
            self.base_url = base_url
        if api_key is not None:
            self.api_key = api_key
        if model is not None:
            self.model = model
            
        # 重新配置OpenAI客户端
        self.client = openai.OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        聊天完成请求
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 响应结果
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            
            return {
                "success": True,
                "content": response.choices[0].message.content,
                "response": response
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def task_decomposition(self, requirement: str) -> Dict[str, Any]:
        """
        任务分解
        
        Args:
            requirement: 用户需求
            
        Returns:
            Dict[str, Any]: 任务分解结果
        """
        messages = [
            {
                "role": "system",
                "content": "你是一个任务分解专家。请将用户的需求分解为具体的子任务，并以JSON格式返回。"
            },
            {
                "role": "user",
                "content": f"请将以下需求分解为具体的子任务：\n{requirement}"
            }
        ]
        
        return self.chat_completion(messages, temperature=0.7)

    def content_generation(self, context: str, task: str) -> Dict[str, Any]:
        """
        内容生成
        
        Args:
            context: 上下文信息
            task: 生成任务
            
        Returns:
            Dict[str, Any]: 生成结果
        """
        messages = [
            {
                "role": "system",
                "content": "你是一个内容生成专家。请根据提供的上下文和任务生成相应的内容。"
            },
            {
                "role": "user",
                "content": f"上下文：\n{context}\n\n任务：\n{task}"
            }
        ]
        
        return self.chat_completion(messages, temperature=0.7)

    def result_validation(self, result: str, requirement: str) -> Dict[str, Any]:
        """
        结果验证
        
        Args:
            result: 执行结果
            requirement: 原始需求
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        messages = [
            {
                "role": "system",
                "content": "你是一个结果验证专家。请检查执行结果是否符合原始需求，并给出验证报告。"
            },
            {
                "role": "user",
                "content": f"原始需求：\n{requirement}\n\n执行结果：\n{result}\n\n请检查执行结果是否符合原始需求，并给出验证报告。"
            }
        ]
        
        return self.chat_completion(messages, temperature=0.3)

    def result_integration(self, results: List[str]) -> Dict[str, Any]:
        """
        结果整合
        
        Args:
            results: 结果列表
            
        Returns:
            Dict[str, Any]: 整合结果
        """
        messages = [
            {
                "role": "system",
                "content": "你是一个结果整合专家。请将多个子任务的结果整合为完整的解决方案。"
            },
            {
                "role": "user",
                "content": f"请将以下子任务结果整合为完整的解决方案：\n{json.dumps(results, ensure_ascii=False, indent=2)}"
            }
        ]
        
        return self.chat_completion(messages, temperature=0.5)

    def need_additional_info(self, task_context: str, current_task: str) -> Dict[str, Any]:
        """
        判断是否需要额外信息以及需要哪种类型的额外信息
        
        Args:
            task_context: 任务上下文
            current_task: 当前任务
            
        Returns:
            Dict[str, Any]: 推理结果，包括是否需要额外信息和信息类型
        """
        messages = [
            {
                "role": "system",
                "content": """你是一个任务分析专家。请分析当前任务是否需要额外信息才能完成。
                如果需要，请指定需要的信息类型：
                1. natural_language: 用户用自然语言补充的信息
                2. user_data: 用户提交的数据或其他信息
                3. folder_content: 请求当前文件夹的所有文件
                4. open_file: 请求打开某个文件
                
                返回JSON格式的结果，包含以下字段：
                - need_info: boolean, 是否需要额外信息
                - info_type: string, 信息类型（如果need_info为true）
                - reason: string, 需要额外信息的原因
                - question: string, 向用户提出的问题（如果需要）
                """
            },
            {
                "role": "user",
                "content": f"任务上下文：\n{task_context}\n\n当前任务：\n{current_task}\n\n请分析是否需要额外信息。"
            }
        ]
        
        return self.chat_completion(messages, temperature=0.3)