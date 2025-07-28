"""
Large Language Model interface module for the AI Agent Flow system.
Handles communication with LLMs using OpenAI-compatible API.
"""

import requests
import json
from typing import Dict, Any, List, Optional

class LLMInterface:
    """Interface for interacting with Large Language Models."""
    
    def __init__(self, 
                 base_url: str = "https://api.openai.com/v1",
                 model_name: str = "gpt-3.5-turbo",
                 api_key: str = "YOUR_API_KEY"):
        """Initialize LLM interface with connection parameters."""
        self.base_url = base_url
        self.model_name = model_name
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to the LLM API."""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"LLM API request failed: {e}")
            return {"error": str(e)}
    
    def chat_completion(self, messages: List[Dict[str, str]], 
                       temperature: float = 0.7, 
                       max_tokens: int = 1000) -> Dict[str, Any]:
        """Get chat completion from LLM."""
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        return self._make_request("chat/completions", payload)
    
    def task_analysis(self, task_description: str) -> Dict[str, Any]:
        """Analyze and decompose a task using LLM reasoning."""
        system_prompt = """You are an AI task analyst. Analyze the given task and provide:
        1. A structured breakdown of the task
        2. Required resources and information
        3. Potential challenges and solutions
        4. Recommended approach and methodology"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task_description}
        ]
        
        return self.chat_completion(messages)
    
    def generate_code(self, design_spec: str) -> Dict[str, Any]:
        """Generate code based on a design specification."""
        system_prompt = """You are an expert code generator. Create code that:
        1. Meets the design specifications exactly
        2. Follows best coding practices
        3. Includes appropriate documentation
        4. Provides implementation notes"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": design_spec}
        ]
        
        return self.chat_completion(messages)
    
    def validate_result(self, result: str, task: str) -> Dict[str, Any]:
        """Validate a task result against the original task."""
        system_prompt = """You are a code and result validator. Evaluate whether:
        1. The result meets the task requirements
        2. There are any potential issues or improvements
        3. Additional verification is needed
        4. The result should be accepted or modified"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Task: {task}\nResult: {result}"}
        ]
        
        return self.chat_completion(messages)

if __name__ == "__main__":
    # Example usage
    llm = LLMInterface()
    
    # Test task analysis
    analysis = llm.task_analysis("Create a Python function to calculate Fibonacci numbers")
    print("Task Analysis:")
    print(analysis.get("choices", [{}])[0].get("message", {}).get("content", "No response"))
    
    # Test code generation
    design = "Implement a REST API for a to-do list application with CRUD operations"
    code_result = llm.generate_code(design)
    print("\nCode Generation Result:")
    print(code_result.get("choices", [{}])[0].get("message", {}).get("content", "No response"))