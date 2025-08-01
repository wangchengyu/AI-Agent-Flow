"""
代码生成工具

提供代码生成、修改、分析和优化的功能。
"""

import os
import re
import json
import logging
from typing import Any, Dict, List, Optional, Union, Awaitable

from ..utils.exceptions import CodeGenerationError


class CodeGenerator:
    """代码生成工具，提供代码生成和分析功能"""
    
    def __init__(self, base_dir: Optional[str] = None, max_file_size: int = 1024 * 1024):
        """
        初始化代码生成工具
        
        Args:
            base_dir: 基础目录，如果为None则不限制操作目录
            max_file_size: 最大文件大小（字节）
        """
        self.base_dir = base_dir
        self.max_file_size = max_file_size
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _validate_path(self, path: str) -> str:
        """
        验证路径
        
        Args:
            path: 文件路径
            
        Returns:
            验证后的绝对路径
            
        Raises:
            CodeGenerationError: 如果路径无效或不安全
        """
        try:
            # 转换为绝对路径
            abs_path = os.path.abspath(path)
            
            # 如果设置了基础目录，检查路径是否在基础目录内
            if self.base_dir:
                base_abs_path = os.path.abspath(self.base_dir)
                if not abs_path.startswith(base_abs_path):
                    raise CodeGenerationError(f"路径 {path} 不在允许的操作目录内")
            
            return abs_path
        except Exception as e:
            raise CodeGenerationError(f"验证路径失败: {str(e)}")
    
    async def generate_class(self, class_name: str, base_classes: Optional[List[str]] = None,
                           attributes: Optional[List[Dict]] = None,
                           methods: Optional[List[Dict]] = None,
                           docstring: Optional[str] = None,
                           language: str = "python") -> str:
        """
        生成类代码
        
        Args:
            class_name: 类名
            base_classes: 基类列表
            attributes: 属性列表，每个属性包含name, type, default_value等
            methods: 方法列表，每个方法包含name, parameters, return_type, body等
            docstring: 类文档字符串
            language: 编程语言
            
        Returns:
            生成的类代码
        """
        try:
            if language.lower() != "python":
                raise CodeGenerationError(f"不支持的编程语言: {language}")
            
            # 生成类定义
            code = f"class {class_name}"
            
            # 添加基类
            if base_classes:
                code += f"({', '.join(base_classes)})"
            
            code += ":\n"
            
            # 添加文档字符串
            if docstring:
                code += f'    """\n    {docstring}\n    """\n\n'
            
            # 添加初始化方法
            init_method = self._generate_init_method(class_name, attributes)
            code += init_method + "\n"
            
            # 添加属性
            if attributes:
                for attr in attributes:
                    attr_code = self._generate_attribute(attr)
                    code += attr_code + "\n"
            
            # 添加方法
            if methods:
                for method in methods:
                    method_code = self._generate_method(method)
                    code += method_code + "\n"
            
            self.logger.info(f"生成类代码: {class_name}")
            return code
        except Exception as e:
            raise CodeGenerationError(f"生成类代码失败: {str(e)}")
    
    def _generate_init_method(self, class_name: str, attributes: Optional[List[Dict]]) -> str:
        """
        生成初始化方法
        
        Args:
            class_name: 类名
            attributes: 属性列表
            
        Returns:
            生成的初始化方法代码
        """
        try:
            code = "    def __init__(self"
            
            # 添加参数
            if attributes:
                for attr in attributes:
                    attr_name = attr.get("name", "")
                    default_value = attr.get("default_value", None)
                    
                    if default_value is not None:
                        code += f", {attr_name}={default_value}"
                    else:
                        code += f", {attr_name}"
            
            code += "):\n"
            
            # 添加属性赋值
            if attributes:
                for attr in attributes:
                    attr_name = attr.get("name", "")
                    code += f"        self.{attr_name} = {attr_name}\n"
            
            return code
        except Exception as e:
            raise CodeGenerationError(f"生成初始化方法失败: {str(e)}")
    
    def _generate_attribute(self, attribute: Dict) -> str:
        """
        生成属性代码
        
        Args:
            attribute: 属性信息
            
        Returns:
            生成的属性代码
        """
        try:
            attr_name = attribute.get("name", "")
            attr_type = attribute.get("type", "Any")
            attr_value = attribute.get("default_value", None)
            
            if attr_value is not None:
                return f"    {attr_name}: {attr_type} = {attr_value}"
            else:
                return f"    {attr_name}: {attr_type}"
        except Exception as e:
            raise CodeGenerationError(f"生成属性代码失败: {str(e)}")
    
    def _generate_method(self, method: Dict) -> str:
        """
        生成方法代码
        
        Args:
            method: 方法信息
            
        Returns:
            生成的方法代码
        """
        try:
            method_name = method.get("name", "")
            parameters = method.get("parameters", [])
            return_type = method.get("return_type", "None")
            body = method.get("body", "pass")
            docstring = method.get("docstring", "")
            
            # 生成方法签名
            code = f"    def {method_name}(self"
            
            # 添加参数
            for param in parameters:
                param_name = param.get("name", "")
                param_type = param.get("type", "Any")
                default_value = param.get("default_value", None)
                
                if default_value is not None:
                    code += f", {param_name}: {param_type} = {default_value}"
                else:
                    code += f", {param_name}: {param_type}"
            
            code += f") -> {return_type}:\n"
            
            # 添加文档字符串
            if docstring:
                code += f'        """\n        {docstring}\n        """\n'
            
            # 添加方法体
            for line in body.split("\n"):
                code += f"        {line}\n"
            
            return code
        except Exception as e:
            raise CodeGenerationError(f"生成方法代码失败: {str(e)}")
    
    async def generate_function(self, function_name: str, parameters: Optional[List[Dict]] = None,
                             return_type: str = "None", body: str = "pass",
                             docstring: Optional[str] = None,
                             language: str = "python") -> str:
        """
        生成函数代码
        
        Args:
            function_name: 函数名
            parameters: 参数列表，每个参数包含name, type, default_value等
            return_type: 返回类型
            body: 函数体
            docstring: 函数文档字符串
            language: 编程语言
            
        Returns:
            生成的函数代码
        """
        try:
            if language.lower() != "python":
                raise CodeGenerationError(f"不支持的编程语言: {language}")
            
            # 生成函数签名
            code = f"def {function_name}("
            
            # 添加参数
            if parameters:
                for i, param in enumerate(parameters):
                    param_name = param.get("name", "")
                    param_type = param.get("type", "Any")
                    default_value = param.get("default_value", None)
                    
                    if default_value is not None:
                        code += f"{param_name}: {param_type} = {default_value}"
                    else:
                        code += f"{param_name}: {param_type}"
                    
                    if i < len(parameters) - 1:
                        code += ", "
            
            code += f") -> {return_type}:\n"
            
            # 添加文档字符串
            if docstring:
                code += f'    """\n    {docstring}\n    """\n'
            
            # 添加函数体
            for line in body.split("\n"):
                code += f"    {line}\n"
            
            self.logger.info(f"生成函数代码: {function_name}")
            return code
        except Exception as e:
            raise CodeGenerationError(f"生成函数代码失败: {str(e)}")
    
    async def analyze_code(self, code: str, language: str = "python") -> Dict:
        """
        分析代码
        
        Args:
            code: 代码内容
            language: 编程语言
            
        Returns:
            代码分析结果
        """
        try:
            if language.lower() != "python":
                raise CodeGenerationError(f"不支持的编程语言: {language}")
            
            # 分析代码结构
            analysis = {
                "classes": [],
                "functions": [],
                "imports": [],
                "lines_of_code": len(code.split("\n")),
                "complexity": self._calculate_complexity(code)
            }
            
            # 提取类
            class_pattern = r"class\s+(\w+)(?:\(([^)]+)\))?:"
            class_matches = re.finditer(class_pattern, code)
            
            for match in class_matches:
                class_name = match.group(1)
                base_classes = match.group(2)
                
                if base_classes:
                    base_classes = [bc.strip() for bc in base_classes.split(",")]
                else:
                    base_classes = []
                
                analysis["classes"].append({
                    "name": class_name,
                    "base_classes": base_classes
                })
            
            # 提取函数
            function_pattern = r"def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^:]+))?:"
            function_matches = re.finditer(function_pattern, code)
            
            for match in function_matches:
                function_name = match.group(1)
                parameters = match.group(2)
                return_type = match.group(3)
                
                # 解析参数
                params = []
                if parameters:
                    for param in parameters.split(","):
                        param = param.strip()
                        if ":" in param:
                            param_name, param_type = param.split(":", 1)
                            param_name = param_name.strip()
                            param_type = param_type.strip()
                            
                            if "=" in param_type:
                                param_type, default_value = param_type.split("=", 1)
                                param_type = param_type.strip()
                                default_value = default_value.strip()
                            else:
                                default_value = None
                            
                            params.append({
                                "name": param_name,
                                "type": param_type,
                                "default_value": default_value
                            })
                        else:
                            params.append({
                                "name": param,
                                "type": "Any",
                                "default_value": None
                            })
                
                analysis["functions"].append({
                    "name": function_name,
                    "parameters": params,
                    "return_type": return_type or "None"
                })
            
            # 提取导入
            import_pattern = r"(?:from\s+(\S+)\s+)?import\s+([^#\n]+)"
            import_matches = re.finditer(import_pattern, code)
            
            for match in import_matches:
                module = match.group(1)
                imports = match.group(2)
                
                if module:
                    # from module import name1, name2
                    import_names = [name.strip() for name in imports.split(",")]
                    for name in import_names:
                        analysis["imports"].append({
                            "type": "from",
                            "module": module,
                            "name": name
                        })
                else:
                    # import module1, module2
                    import_names = [name.strip() for name in imports.split(",")]
                    for name in import_names:
                        analysis["imports"].append({
                            "type": "import",
                            "module": name,
                            "name": None
                        })
            
            self.logger.info("分析代码完成")
            return analysis
        except Exception as e:
            raise CodeGenerationError(f"分析代码失败: {str(e)}")
    
    def _calculate_complexity(self, code: str) -> int:
        """
        计算代码复杂度（简化版圈复杂度）
        
        Args:
            code: 代码内容
            
        Returns:
            复杂度分数
        """
        try:
            # 基础复杂度为1
            complexity = 1
            
            # 计算控制结构数量
            control_structures = [
                r"\bif\b",
                r"\belse\b",
                r"\belif\b",
                r"\bfor\b",
                r"\bwhile\b",
                r"\btry\b",
                r"\bexcept\b",
                r"\bfinally\b",
                r"\bwith\b"
            ]
            
            for pattern in control_structures:
                matches = re.findall(pattern, code)
                complexity += len(matches)
            
            # 计算布尔运算符数量
            boolean_operators = [
                r"\band\b",
                r"\bor\b",
                r"\bnot\b"
            ]
            
            for pattern in boolean_operators:
                matches = re.findall(pattern, code)
                complexity += len(matches)
            
            return complexity
        except Exception as e:
            self.logger.error(f"计算代码复杂度失败: {str(e)}")
            return 1
    
    async def refactor_code(self, code: str, refactoring_type: str, language: str = "python") -> str:
        """
        重构代码
        
        Args:
            code: 原始代码
            refactoring_type: 重构类型
            language: 编程语言
            
        Returns:
            重构后的代码
        """
        try:
            if language.lower() != "python":
                raise CodeGenerationError(f"不支持的编程语言: {language}")
            
            if refactoring_type == "extract_method":
                return await self._extract_method(code)
            elif refactoring_type == "rename_variable":
                return await self._rename_variable(code)
            elif refactoring_type == "inline_method":
                return await self._inline_method(code)
            elif refactoring_type == "extract_variable":
                return await self._extract_variable(code)
            elif refactoring_type == "format_code":
                return await self._format_code(code)
            else:
                raise CodeGenerationError(f"不支持的重构类型: {refactoring_type}")
        except Exception as e:
            raise CodeGenerationError(f"重构代码失败: {str(e)}")
    
    async def _extract_method(self, code: str) -> str:
        """
        提取方法重构
        
        Args:
            code: 原始代码
            
        Returns:
            重构后的代码
        """
        # 这是一个简化的实现，实际应用中需要更复杂的逻辑
        try:
            # 查找可以提取的代码块
            lines = code.split("\n")
            extracted_methods = []
            
            # 查找连续的代码行
            current_block = []
            for line in lines:
                stripped = line.strip()
                
                # 跳过空行和注释
                if not stripped or stripped.startswith("#"):
                    if current_block:
                        extracted_methods.append("\n".join(current_block))
                        current_block = []
                    continue
                
                # 如果是控制结构或方法定义，结束当前块
                if (stripped.startswith("def ") or 
                    stripped.startswith("class ") or
                    stripped.startswith("if ") or
                    stripped.startswith("for ") or
                    stripped.startswith("while ") or
                    stripped.startswith("try ") or
                    stripped.startswith("with ")):
                    
                    if current_block:
                        extracted_methods.append("\n".join(current_block))
                        current_block = []
                
                current_block.append(line)
            
            if current_block:
                extracted_methods.append("\n".join(current_block))
            
            # 为每个代码块生成方法
            refactored_code = code
            for i, block in enumerate(extracted_methods):
                if len(block.split("\n")) > 3:  # 只处理超过3行的代码块
                    method_name = f"extracted_method_{i+1}"
                    method_code = f"\n    def {method_name}(self):\n"
                    for line in block.split("\n"):
                        method_code += f"        {line}\n"
                    
                    # 替换原代码块
                    refactored_code = refactored_code.replace(block, f"self.{method_name}()")
                    
                    # 添加方法到类中
                    class_pattern = r"(class\s+\w+.*?:)"
                    class_match = re.search(class_pattern, refactored_code)
                    if class_match:
                        class_end = class_match.end()
                        refactored_code = (refactored_code[:class_end] + 
                                         method_code + 
                                         refactored_code[class_end:])
            
            return refactored_code
        except Exception as e:
            raise CodeGenerationError(f"提取方法重构失败: {str(e)}")
    
    async def _rename_variable(self, code: str) -> str:
        """
        重命名变量重构
        
        Args:
            code: 原始代码
            
        Returns:
            重构后的代码
        """
        # 这是一个简化的实现，实际应用中需要更复杂的逻辑
        try:
            # 查找单字母变量名
            pattern = r"\b([a-z])\b"
            
            def replace_match(match):
                var_name = match.group(1)
                # 跳过常见的单字母变量名
                if var_name in ["i", "j", "k", "x", "y", "z", "f", "g"]:
                    return var_name
                
                # 生成更有意义的变量名
                meaningful_names = {
                    "a": "item",
                    "b": "buffer",
                    "c": "count",
                    "d": "data",
                    "e": "element",
                    "m": "message",
                    "n": "number",
                    "p": "parameter",
                    "q": "query",
                    "r": "result",
                    "s": "string",
                    "t": "text",
                    "u": "user",
                    "v": "value",
                    "w": "width"
                }
                
                return meaningful_names.get(var_name, var_name)
            
            refactored_code = re.sub(pattern, replace_match, code)
            return refactored_code
        except Exception as e:
            raise CodeGenerationError(f"重命名变量重构失败: {str(e)}")
    
    async def _inline_method(self, code: str) -> str:
        """
        内联方法重构
        
        Args:
            code: 原始代码
            
        Returns:
            重构后的代码
        """
        # 这是一个简化的实现，实际应用中需要更复杂的逻辑
        try:
            # 查找简单的方法定义
            method_pattern = r"(\s+def\s+(\w+)\s*\(\s*self\s*\)\s*:\s*\n\s+return\s+(\w+)\s*\n)"
            
            def replace_method(match):
                indent = match.group(1)
                method_name = match.group(2)
                return_value = match.group(3)
                
                # 返回方法体
                return f"{indent}{return_value}\n"
            
            refactored_code = re.sub(method_pattern, replace_method, code)
            return refactored_code
        except Exception as e:
            raise CodeGenerationError(f"内联方法重构失败: {str(e)}")
    
    async def _extract_variable(self, code: str) -> str:
        """
        提取变量重构
        
        Args:
            code: 原始代码
            
        Returns:
            重构后的代码
        """
        # 这是一个简化的实现，实际应用中需要更复杂的逻辑
        try:
            # 查找重复的表达式
            lines = code.split("\n")
            expression_counts = {}
            
            for line in lines:
                # 简单的表达式匹配
                expressions = re.findall(r"([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*(?:\([^)]*\))?)", line)
                
                for expr in expressions:
                    if len(expr) > 10:  # 只处理较长的表达式
                        if expr in expression_counts:
                            expression_counts[expr] += 1
                        else:
                            expression_counts[expr] = 1
            
            # 找出出现多次的表达式
            repeated_expressions = {expr: count for expr, count in expression_counts.items() if count > 1}
            
            refactored_code = code
            var_counter = 1
            
            for expr, count in repeated_expressions.items():
                if count > 1:
                    var_name = f"extracted_var_{var_counter}"
                    var_counter += 1
                    
                    # 在第一次出现前定义变量
                    first_occurrence = refactored_code.find(expr)
                    if first_occurrence != -1:
                        # 找到行首
                        line_start = refactored_code.rfind("\n", 0, first_occurrence)
                        if line_start == -1:
                            line_start = 0
                        
                        # 插入变量定义
                        indent = "    "  # 假设缩进为4个空格
                        var_definition = f"\n{indent}{var_name} = {expr}\n"
                        refactored_code = (refactored_code[:line_start] + 
                                         var_definition + 
                                         refactored_code[line_start:])
                        
                        # 替换所有出现
                        refactored_code = refactored_code.replace(expr, var_name)
            
            return refactored_code
        except Exception as e:
            raise CodeGenerationError(f"提取变量重构失败: {str(e)}")
    
    async def _format_code(self, code: str) -> str:
        """
        格式化代码
        
        Args:
            code: 原始代码
            
        Returns:
            格式化后的代码
        """
        try:
            # 这是一个简化的实现，实际应用中可以使用autopep8或black等工具
            lines = code.split("\n")
            formatted_lines = []
            
            for line in lines:
                stripped = line.strip()
                
                # 跳过空行
                if not stripped:
                    formatted_lines.append("")
                    continue
                
                # 处理缩进
                indent = ""
                for char in line:
                    if char in " \t":
                        indent += char
                    else:
                        break
                
                # 标准化缩进为4个空格
                if indent:
                    indent_level = len(indent.replace("\t", "    "))
                    indent = "    " * (indent_level // 4)
                
                # 添加格式化后的行
                formatted_lines.append(indent + stripped)
            
            return "\n".join(formatted_lines)
        except Exception as e:
            raise CodeGenerationError(f"格式化代码失败: {str(e)}")
    
    async def generate_test_code(self, code: str, language: str = "python", 
                              test_framework: str = "unittest") -> str:
        """
        生成测试代码
        
        Args:
            code: 原始代码
            language: 编程语言
            test_framework: 测试框架
            
        Returns:
            生成的测试代码
        """
        try:
            if language.lower() != "python":
                raise CodeGenerationError(f"不支持的编程语言: {language}")
            
            if test_framework.lower() != "unittest":
                raise CodeGenerationError(f"不支持的测试框架: {test_framework}")
            
            # 分析代码
            analysis = await self.analyze_code(code)
            
            # 生成测试代码
            test_code = "import unittest\n\n"
            
            # 为每个类生成测试类
            for class_info in analysis["classes"]:
                class_name = class_info["name"]
                test_class_name = f"Test{class_name}"
                
                test_code += f"class {test_class_name}(unittest.TestCase):\n"
                test_code += f"    def setUp(self):\n"
                test_code += f"        self.{class_name.lower()} = {class_name}()\n\n"
                
                # 为每个方法生成测试方法
                for method_info in analysis["functions"]:
                    method_name = method_info["name"]
                    if method_name.startswith("__") and method_name.endswith("__"):
                        continue  # 跳过特殊方法
                    
                    test_method_name = f"test_{method_name}"
                    test_code += f"    def {test_method_name}(self):\n"
                    test_code += f"        # TODO: Implement test for {method_name}\n"
                    test_code += f"        pass\n\n"
                
                test_code += "\n"
            
            # 添加主函数
            test_code += "if __name__ == '__main__':\n"
            test_code += "    unittest.main()\n"
            
            self.logger.info("生成测试代码完成")
            return test_code
        except Exception as e:
            raise CodeGenerationError(f"生成测试代码失败: {str(e)}")
    
    async def optimize_code(self, code: str, language: str = "python") -> Dict:
        """
        优化代码
        
        Args:
            code: 原始代码
            language: 编程语言
            
        Returns:
            优化结果和优化后的代码
        """
        try:
            if language.lower() != "python":
                raise CodeGenerationError(f"不支持的编程语言: {language}")
            
            # 分析代码
            analysis = await self.analyze_code(code)
            
            # 优化建议
            optimizations = []
            optimized_code = code
            
            # 检查循环优化
            loop_pattern = r"for\s+(\w+)\s+in\s+range\(len\((\w+)\)\)\):"
            loop_matches = re.finditer(loop_pattern, code)
            
            for match in loop_matches:
                loop_var = match.group(1)
                list_var = match.group(2)
                original = match.group(0)
                optimized = f"for {loop_var}, _ in enumerate({list_var}):"
                
                optimizations.append({
                    "type": "loop_optimization",
                    "description": f"使用enumerate()优化循环: {original}",
                    "original": original,
                    "optimized": optimized
                })
                
                optimized_code = optimized_code.replace(original, optimized)
            
            # 检查列表推导式
            list_comp_pattern = r"(\w+)\s*=\s*\[\]\s*\n(\s+)for\s+(\w+)\s+in\s+(\w+):\s*\n\2\s*\1\.append\((\w+)\)"
            list_comp_matches = re.finditer(list_comp_pattern, code)
            
            for match in list_comp_matches:
                list_var = match.group(1)
                indent = match.group(2)
                loop_var = match.group(3)
                iter_var = match.group(4)
                append_var = match.group(5)
                original = match.group(0)
                optimized = f"{list_var} = [{append_var} for {loop_var} in {iter_var}]"
                
                optimizations.append({
                    "type": "list_comprehension",
                    "description": f"使用列表推导式优化: {original}",
                    "original": original,
                    "optimized": optimized
                })
                
                optimized_code = optimized_code.replace(original, optimized)
            
            # 检查字符串格式化
            str_format_pattern = r"(\w+)\s*\+\s*str\((\w+)\)"
            str_format_matches = re.finditer(str_format_pattern, code)
            
            for match in str_format_matches:
                var1 = match.group(1)
                var2 = match.group(2)
                original = match.group(0)
                optimized = f'f"{var1}{var2}"'
                
                optimizations.append({
                    "type": "string_formatting",
                    "description": f"使用f-string优化字符串格式化: {original}",
                    "original": original,
                    "optimized": optimized
                })
                
                optimized_code = optimized_code.replace(original, optimized)
            
            return {
                "optimizations": optimizations,
                "optimized_code": optimized_code,
                "original_analysis": analysis
            }
        except Exception as e:
            raise CodeGenerationError(f"优化代码失败: {str(e)}")