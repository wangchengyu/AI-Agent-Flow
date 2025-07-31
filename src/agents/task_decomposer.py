from typing import List, Dict, Any
import xml.etree.ElementTree as ET
import re
from .subtask_state import SubTaskState

class TaskDecomposer:
    def __init__(self, llm_model: Any):
        self.llm_model = llm_model
        
    def decompose(self, user_input: str) -> List[Dict]:
        """将自然语言需求分解为结构化任务清单"""
        # 调用LLM生成任务清单
        prompt = f"""
        将以下用户需求分解为结构化任务清单，使用XML格式返回：
        <update_todo_list>
            <todos>
            [ ] 任务1描述
            [ ] 任务2描述
            ...
            </todos>
        </update_todo_list>
        
        用户需求：{user_input}
        """
        
        response = self.llm_model.generate(prompt)
        
        # 解析XML响应
        try:
            root = ET.fromstring(response)
            todos_element = root.find('todos')
            if todos_element is None:
                raise ValueError("Invalid XML format: missing todos element")
                
            tasks = []
            for line in todos_element.text.strip().split('\n'):
                if line.strip():
                    # 解析状态和描述
                    match = re.match(r'\[(.)\]\s*(.+)', line.strip())
                    if match:
                        status_char, description = match.groups()
                        status = self._parse_status(status_char)
                        tasks.append({
                            'description': description,
                            'status': status,
                            'context': []
                        })
            return tasks
        except Exception as e:
            print(f"Error parsing task decomposition: {e}")
            # 返回默认任务结构
            return [{
                'description': user_input,
                'status': SubTaskState.PENDING,
                'context': []
            }]
    
    def _parse_status(self, status_char: str) -> SubTaskState:
        """解析任务状态字符"""
        if status_char == 'x':
            return SubTaskState.COMPLETED
        elif status_char == '-':
            return SubTaskState.EXECUTING
        else:
            return SubTaskState.PENDING
            
    def validate_structure(self, task: Dict) -> bool:
        """验证任务结构有效性"""
        required_keys = ['description', 'status', 'context']
        return all(key in task for key in required_keys)