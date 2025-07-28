import requests
import logging
import json
from datetime import datetime
from config.config import load_config

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='ai_agent_flow/logs/llm_interaction.log'
)

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        """初始化LLM客户端"""
        self.config = load_config()['openai']
        self.base_url = self.config['base_url']
        self.model_name = self.config['model_name']
        self.api_key = os.getenv('OPENAI_API_KEY', self.config['api_key'])
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
    def send_request(self, prompt, context=None):
        """
        发送请求到大模型
        :param prompt: 用户提示
        :param context: 上下文信息
        :return: 模型响应
        """
        timestamp = datetime.now().isoformat()
        logger.info(f"请求时间: {timestamp}")
        logger.info(f"请求内容: {prompt}")
        logger.info(f"上下文信息: {context}")
        
        url = f"{self.base_url}/chat/completions"
        
        data = {
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": self.config['max_tokens'],
            "temperature": self.config['temperature']
        }
        
        if context:
            data["context"] = context
            
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"响应内容: {json.dumps(result, ensure_ascii=False)}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {str(e)}")
            return {"error": str(e)}
            
    def pre_execute_reasoning(self, task_description, context=None, max_retries=5):
        """
        子任务执行前的推理
        :param task_description: 任务描述
        :param context: 上下文信息
        :param max_retries: 最大重试次数
        :return: 推理结果和需要的额外信息
        """
        prompt = f"""
        请分析以下任务是否需要额外信息才能执行：
        任务描述: {task_description}
        
        上下文信息: {context}
        
        请返回以下格式的JSON：
        {{
            "need_extra_info": boolean,
            "extra_info_types": array,
            "reason": string
        }}
        
        需要额外信息的类型可能包括：
        - 用户用自然语言补充的信息
        - 用户提交的数据或者其他信息
        - 请求当前文件夹的所有文件
        - 请求打开某个文件
        
        请严格按JSON格式返回，不要包含其他内容。
        """
        
        for i in range(max_retries):
            result = self.send_request(prompt, context)
            if "error" in result:
                logger.error(f"推理请求失败: {result['error']}")
                continue
                
            try:
                result_json = json.loads(result["choices"][0]["text"])
                if result_json["need_extra_info"]:
                    logger.info(f"需要额外信息: {result_json['extra_info_types']}，原因: {result_json['reason']}")
                    return result_json
                else:
                    logger.info(f"无需额外信息，原因: {result_json['reason']}")
                    return result_json
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"解析推理结果失败: {str(e)}")
                logger.error(f"原始结果: {result}")
                
        logger.error(f"达到最大重试次数({max_retries})，无法获取有效推理结果")
        return {
            "need_extra_info": False,
            "extra_info_types": [],
            "reason": "无法获取有效推理结果"
        }