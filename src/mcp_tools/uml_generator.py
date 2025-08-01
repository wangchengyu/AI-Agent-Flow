"""
UML生成工具

提供UML图生成功能，包括类图、序列图、用例图等。
"""

import os
import re
import json
import logging
from typing import Any, Dict, List, Optional, Union, Awaitable

from ..utils.exceptions import UMLGenerationError


class UMLGenerator:
    """UML生成工具，提供UML图生成功能"""
    
    def __init__(self, output_dir: str = "./uml_output", format: str = "png"):
        """
        初始化UML生成工具
        
        Args:
            output_dir: 输出目录
            format: 输出格式（png, svg, pdf等）
        """
        self.output_dir = output_dir
        self.format = format.lower()
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def generate_class_diagram(self, classes: List[Dict], 
                                  relationships: Optional[List[Dict]] = None,
                                  title: Optional[str] = None) -> str:
        """
        生成类图
        
        Args:
            classes: 类信息列表，每个类包含name, attributes, methods等
            relationships: 关系信息列表，每个关系包含from, to, type等
            title: 图表标题
            
        Returns:
            生成的UML文件路径
        """
        try:
            # 生成PlantUML代码
            plantuml_code = "@startuml\n"
            
            if title:
                plantuml_code += f"title {title}\n\n"
            
            # 添加类定义
            for cls in classes:
                class_name = cls.get("name", "")
                attributes = cls.get("attributes", [])
                methods = cls.get("methods", [])
                
                plantuml_code += f"class {class_name} {{\n"
                
                # 添加属性
                for attr in attributes:
                    visibility = attr.get("visibility", "+")
                    attr_name = attr.get("name", "")
                    attr_type = attr.get("type", "")
                    
                    plantuml_code += f"  {visibility} {attr_name}: {attr_type}\n"
                
                # 添加方法
                for method in methods:
                    visibility = method.get("visibility", "+")
                    method_name = method.get("name", "")
                    parameters = method.get("parameters", [])
                    return_type = method.get("return_type", "")
                    
                    param_str = ", ".join([f"{p.get('name', '')}: {p.get('type', '')}" for p in parameters])
                    plantuml_code += f"  {visibility} {method_name}({param_str}): {return_type}\n"
                
                plantuml_code += "}\n\n"
            
            # 添加关系
            if relationships:
                for rel in relationships:
                    from_class = rel.get("from", "")
                    to_class = rel.get("to", "")
                    rel_type = rel.get("type", "")
                    label = rel.get("label", "")
                    
                    if rel_type == "inheritance":
                        plantuml_code += f"{to_class} <|-- {from_class}\n"
                    elif rel_type == "association":
                        plantuml_code += f"{from_class} --> {to_class}"
                        if label:
                            plantuml_code += f" : {label}"
                        plantuml_code += "\n"
                    elif rel_type == "aggregation":
                        plantuml_code += f"{from_class} o-- {to_class}"
                        if label:
                            plantuml_code += f" : {label}"
                        plantuml_code += "\n"
                    elif rel_type == "composition":
                        plantuml_code += f"{from_class} *-- {to_class}"
                        if label:
                            plantuml_code += f" : {label}"
                        plantuml_code += "\n"
                    elif rel_type == "dependency":
                        plantuml_code += f"{from_class} ..> {to_class}"
                        if label:
                            plantuml_code += f" : {label}"
                        plantuml_code += "\n"
            
            plantuml_code += "@enduml\n"
            
            # 保存PlantUML文件
            file_name = f"class_diagram_{int(os.time() * 1000)}.puml"
            file_path = os.path.join(self.output_dir, file_name)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(plantuml_code)
            
            # 生成图像
            image_path = await self._generate_image(file_path)
            
            self.logger.info(f"生成类图: {image_path}")
            return image_path
        except Exception as e:
            raise UMLGenerationError(f"生成类图失败: {str(e)}")
    
    async def generate_sequence_diagram(self, actors: List[Dict], 
                                      interactions: List[Dict],
                                      title: Optional[str] = None) -> str:
        """
        生成序列图
        
        Args:
            actors: 参与者列表，每个参与者包含name, type等
            interactions: 交互列表，每个交互包含from, to, message等
            title: 图表标题
            
        Returns:
            生成的UML文件路径
        """
        try:
            # 生成PlantUML代码
            plantuml_code = "@startuml\n"
            
            if title:
                plantuml_code += f"title {title}\n\n"
            
            # 添加参与者
            for actor in actors:
                actor_name = actor.get("name", "")
                actor_type = actor.get("type", "participant")
                
                if actor_type == "actor":
                    plantuml_code += f"actor {actor_name}\n"
                elif actor_type == "boundary":
                    plantuml_code += f"boundary {actor_name}\n"
                elif actor_type == "control":
                    plantuml_code += f"control {actor_name}\n"
                elif actor_type == "entity":
                    plantuml_code += f"entity {actor_name}\n"
                elif actor_type == "database":
                    plantuml_code += f"database {actor_name}\n"
                else:
                    plantuml_code += f"participant {actor_name}\n"
            
            plantuml_code += "\n"
            
            # 添加交互
            for interaction in interactions:
                from_actor = interaction.get("from", "")
                to_actor = interaction.get("to", "")
                message = interaction.get("message", "")
                interaction_type = interaction.get("type", "->")
                activation = interaction.get("activation", False)
                return_message = interaction.get("return_message", "")
                
                # 处理激活
                if activation:
                    plantuml_code += f"activate {from_actor}\n"
                
                # 处理消息
                if interaction_type == "->":
                    plantuml_code += f"{from_actor} -> {to_actor}: {message}\n"
                elif interaction_type == "-->":
                    plantuml_code += f"{from_actor} --> {to_actor}: {message}\n"
                elif interaction_type == "->>":
                    plantuml_code += f"{from_actor} ->> {to_actor}: {message}\n"
                elif interaction_type == "-->>":
                    plantuml_code += f"{from_actor} -->> {to_actor}: {message}\n"
                
                # 处理返回消息
                if return_message:
                    plantuml_code += f"{to_actor} --> {from_actor}: {return_message}\n"
                
                # 处理去激活
                if activation:
                    plantuml_code += f"deactivate {from_actor}\n"
            
            plantuml_code += "@enduml\n"
            
            # 保存PlantUML文件
            file_name = f"sequence_diagram_{int(os.time() * 1000)}.puml"
            file_path = os.path.join(self.output_dir, file_name)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(plantuml_code)
            
            # 生成图像
            image_path = await self._generate_image(file_path)
            
            self.logger.info(f"生成序列图: {image_path}")
            return image_path
        except Exception as e:
            raise UMLGenerationError(f"生成序列图失败: {str(e)}")
    
    async def generate_use_case_diagram(self, actors: List[Dict], 
                                      use_cases: List[Dict],
                                      relationships: Optional[List[Dict]] = None,
                                      title: Optional[str] = None) -> str:
        """
        生成用例图
        
        Args:
            actors: 参与者列表，每个参与者包含name等
            use_cases: 用例列表，每个用例包含name等
            relationships: 关系列表，每个关系包含from, to, type等
            title: 图表标题
            
        Returns:
            生成的UML文件路径
        """
        try:
            # 生成PlantUML代码
            plantuml_code = "@startuml\n"
            
            if title:
                plantuml_code += f"title {title}\n\n"
            
            # 设置皮肤参数
            plantuml_code += "skinparam actorStyle awesome\n"
            plantuml_code += "skinparam usecase {\n"
            plantuml_code += "  BackgroundColor LightSkyBlue\n"
            plantuml_code += "  BorderColor DarkSlateGray\n"
            plantuml_code += "}\n\n"
            
            # 添加参与者
            for actor in actors:
                actor_name = actor.get("name", "")
                plantuml_code += f"actor {actor_name}\n"
            
            plantuml_code += "\n"
            
            # 添加用例
            for use_case in use_cases:
                use_case_name = use_case.get("name", "")
                plantuml_code += f"usecase {use_case_name}\n"
            
            plantuml_code += "\n"
            
            # 添加关系
            if relationships:
                for rel in relationships:
                    from_item = rel.get("from", "")
                    to_item = rel.get("to", "")
                    rel_type = rel.get("type", "")
                    label = rel.get("label", "")
                    
                    if rel_type == "association":
                        plantuml_code += f"{from_item} --> {to_item}"
                        if label:
                            plantuml_code += f" : {label}"
                        plantuml_code += "\n"
                    elif rel_type == "include":
                        plantuml_code += f"{from_item} ..> {to_item} : include\n"
                    elif rel_type == "extend":
                        plantuml_code += f"{from_item} ..> {to_item} : extend\n"
                    elif rel_type == "generalization":
                        plantuml_code += f"{from_item} --|> {to_item}\n"
            
            plantuml_code += "@enduml\n"
            
            # 保存PlantUML文件
            file_name = f"use_case_diagram_{int(os.time() * 1000)}.puml"
            file_path = os.path.join(self.output_dir, file_name)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(plantuml_code)
            
            # 生成图像
            image_path = await self._generate_image(file_path)
            
            self.logger.info(f"生成用例图: {image_path}")
            return image_path
        except Exception as e:
            raise UMLGenerationError(f"生成用例图失败: {str(e)}")
    
    async def generate_activity_diagram(self, activities: List[Dict], 
                                       flows: Optional[List[Dict]] = None,
                                       title: Optional[str] = None) -> str:
        """
        生成活动图
        
        Args:
            activities: 活动列表，每个活动包含name, type等
            flows: 流程列表，每个流程包含from, to等
            title: 图表标题
            
        Returns:
            生成的UML文件路径
        """
        try:
            # 生成PlantUML代码
            plantuml_code = "@startuml\n"
            
            if title:
                plantuml_code += f"title {title}\n\n"
            
            # 设置皮肤参数
            plantuml_code += "skinparam activity {\n"
            plantuml_code += "  BackgroundColor LightGreen\n"
            plantuml_code += "  BorderColor DarkGreen\n"
            plantuml_code += "}\n\n"
            
            # 添加活动
            for activity in activities:
                activity_name = activity.get("name", "")
                activity_type = activity.get("type", "activity")
                
                if activity_type == "start":
                    plantuml_code += f"start\n"
                elif activity_type == "end":
                    plantuml_code += f"end\n"
                elif activity_type == "decision":
                    plantuml_code += f"if \"{activity_name}\" then\n"
                elif activity_type == "fork":
                    plantuml_code += "fork\n"
                elif activity_type == "merge":
                    plantuml_code += "end fork\n"
                else:
                    plantuml_code += f":{activity_name};\n"
            
            plantuml_code += "\n"
            
            # 添加流程
            if flows:
                for flow in flows:
                    from_activity = flow.get("from", "")
                    to_activity = flow.get("to", "")
                    condition = flow.get("condition", "")
                    
                    if condition:
                        plantuml_code += f"{from_activity} -{condition}-> {to_activity}\n"
                    else:
                        plantuml_code += f"{from_activity} --> {to_activity}\n"
            
            plantuml_code += "@enduml\n"
            
            # 保存PlantUML文件
            file_name = f"activity_diagram_{int(os.time() * 1000)}.puml"
            file_path = os.path.join(self.output_dir, file_name)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(plantuml_code)
            
            # 生成图像
            image_path = await self._generate_image(file_path)
            
            self.logger.info(f"生成活动图: {image_path}")
            return image_path
        except Exception as e:
            raise UMLGenerationError(f"生成活动图失败: {str(e)}")
    
    async def generate_component_diagram(self, components: List[Dict], 
                                        interfaces: Optional[List[Dict]] = None,
                                        relationships: Optional[List[Dict]] = None,
                                        title: Optional[str] = None) -> str:
        """
        生成组件图
        
        Args:
            components: 组件列表，每个组件包含name等
            interfaces: 接口列表，每个接口包含name等
            relationships: 关系列表，每个关系包含from, to, type等
            title: 图表标题
            
        Returns:
            生成的UML文件路径
        """
        try:
            # 生成PlantUML代码
            plantuml_code = "@startuml\n"
            
            if title:
                plantuml_code += f"title {title}\n\n"
            
            # 设置皮肤参数
            plantuml_code += "skinparam component {\n"
            plantuml_code += "  BackgroundColor LightYellow\n"
            plantuml_code += "  BorderColor DarkGoldenRod\n"
            plantuml_code += "}\n\n"
            
            # 添加接口
            if interfaces:
                for interface in interfaces:
                    interface_name = interface.get("name", "")
                    plantuml_code += f"interface {interface_name}\n"
                
                plantuml_code += "\n"
            
            # 添加组件
            for component in components:
                component_name = component.get("name", "")
                plantuml_code += f"component {component_name}\n"
            
            plantuml_code += "\n"
            
            # 添加关系
            if relationships:
                for rel in relationships:
                    from_item = rel.get("from", "")
                    to_item = rel.get("to", "")
                    rel_type = rel.get("type", "")
                    label = rel.get("label", "")
                    
                    if rel_type == "dependency":
                        plantuml_code += f"{from_item} ..> {to_item}"
                        if label:
                            plantuml_code += f" : {label}"
                        plantuml_code += "\n"
                    elif rel_type == "interface":
                        plantuml_code += f"{from_item} -up- {to_item}\n"
                    elif rel_type == "association":
                        plantuml_code += f"{from_item} --> {to_item}"
                        if label:
                            plantuml_code += f" : {label}"
                        plantuml_code += "\n"
            
            plantuml_code += "@enduml\n"
            
            # 保存PlantUML文件
            file_name = f"component_diagram_{int(os.time() * 1000)}.puml"
            file_path = os.path.join(self.output_dir, file_name)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(plantuml_code)
            
            # 生成图像
            image_path = await self._generate_image(file_path)
            
            self.logger.info(f"生成组件图: {image_path}")
            return image_path
        except Exception as e:
            raise UMLGenerationError(f"生成组件图失败: {str(e)}")
    
    async def generate_state_diagram(self, states: List[Dict], 
                                   transitions: List[Dict],
                                   title: Optional[str] = None) -> str:
        """
        生成状态图
        
        Args:
            states: 状态列表，每个状态包含name, type等
            transitions: 转换列表，每个转换包含from, to, event等
            title: 图表标题
            
        Returns:
            生成的UML文件路径
        """
        try:
            # 生成PlantUML代码
            plantuml_code = "@startuml\n"
            
            if title:
                plantuml_code += f"title {title}\n\n"
            
            # 设置皮肤参数
            plantuml_code += "skinparam state {\n"
            plantuml_code += "  BackgroundColor LightCyan\n"
            plantuml_code += "  BorderColor DarkTurquoise\n"
            plantuml_code += "}\n\n"
            
            # 添加状态
            for state in states:
                state_name = state.get("name", "")
                state_type = state.get("type", "state")
                
                if state_type == "start":
                    plantuml_code += f"[*] --> {state_name}\n"
                elif state_type == "end":
                    plantuml_code += f"{state_name} --> [*]\n"
                elif state_type == "fork":
                    plantuml_code += f"state {state_name} <<fork>>\n"
                elif state_type == "join":
                    plantuml_code += f"state {state_name} <<join>>\n"
                else:
                    plantuml_code += f"state {state_name}\n"
            
            plantuml_code += "\n"
            
            # 添加转换
            for transition in transitions:
                from_state = transition.get("from", "")
                to_state = transition.get("to", "")
                event = transition.get("event", "")
                condition = transition.get("condition", "")
                action = transition.get("action", "")
                
                transition_str = f"{from_state} --> {to_state}"
                label_parts = []
                
                if event:
                    label_parts.append(event)
                
                if condition:
                    label_parts.append(f"[{condition}]")
                
                if action:
                    label_parts.append(f"/ {action}")
                
                if label_parts:
                    transition_str += f" : {' '.join(label_parts)}"
                
                plantuml_code += transition_str + "\n"
            
            plantuml_code += "@enduml\n"
            
            # 保存PlantUML文件
            file_name = f"state_diagram_{int(os.time() * 1000)}.puml"
            file_path = os.path.join(self.output_dir, file_name)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(plantuml_code)
            
            # 生成图像
            image_path = await self._generate_image(file_path)
            
            self.logger.info(f"生成状态图: {image_path}")
            return image_path
        except Exception as e:
            raise UMLGenerationError(f"生成状态图失败: {str(e)}")
    
    async def _generate_image(self, plantuml_file_path: str) -> str:
        """
        从PlantUML文件生成图像
        
        Args:
            plantuml_file_path: PlantUML文件路径
            
        Returns:
            生成的图像文件路径
        """
        try:
            # 这里应该调用PlantUML工具生成图像
            # 由于我们无法直接调用外部工具，这里只返回一个模拟的路径
            
            file_name = os.path.basename(plantuml_file_path)
            image_name = file_name.replace(".puml", f".{self.format}")
            image_path = os.path.join(self.output_dir, image_name)
            
            # 在实际应用中，这里应该调用PlantUML工具
            # 例如：os.system(f"java -jar plantuml.jar -t{self.format} {plantuml_file_path}")
            
            return image_path
        except Exception as e:
            raise UMLGenerationError(f"生成图像失败: {str(e)}")
    
    async def generate_diagram_from_json(self, json_file_path: str) -> str:
        """
        从JSON文件生成UML图
        
        Args:
            json_file_path: JSON文件路径
            
        Returns:
            生成的图像文件路径
        """
        try:
            # 读取JSON文件
            with open(json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 根据图表类型生成相应的UML图
            diagram_type = data.get("type", "")
            
            if diagram_type == "class":
                return await self.generate_class_diagram(
                    classes=data.get("classes", []),
                    relationships=data.get("relationships", []),
                    title=data.get("title")
                )
            elif diagram_type == "sequence":
                return await self.generate_sequence_diagram(
                    actors=data.get("actors", []),
                    interactions=data.get("interactions", []),
                    title=data.get("title")
                )
            elif diagram_type == "use_case":
                return await self.generate_use_case_diagram(
                    actors=data.get("actors", []),
                    use_cases=data.get("use_cases", []),
                    relationships=data.get("relationships", []),
                    title=data.get("title")
                )
            elif diagram_type == "activity":
                return await self.generate_activity_diagram(
                    activities=data.get("activities", []),
                    flows=data.get("flows", []),
                    title=data.get("title")
                )
            elif diagram_type == "component":
                return await self.generate_component_diagram(
                    components=data.get("components", []),
                    interfaces=data.get("interfaces", []),
                    relationships=data.get("relationships", []),
                    title=data.get("title")
                )
            elif diagram_type == "state":
                return await self.generate_state_diagram(
                    states=data.get("states", []),
                    transitions=data.get("transitions", []),
                    title=data.get("title")
                )
            else:
                raise UMLGenerationError(f"不支持的图表类型: {diagram_type}")
        except Exception as e:
            raise UMLGenerationError(f"从JSON文件生成UML图失败: {str(e)}")
    
    async def generate_diagram_from_code(self, code_files: List[str], 
                                      diagram_type: str = "class") -> str:
        """
        从代码文件生成UML图
        
        Args:
            code_files: 代码文件路径列表
            diagram_type: 图表类型
            
        Returns:
            生成的图像文件路径
        """
        try:
            # 解析代码文件
            classes = []
            relationships = []
            
            for file_path in code_files:
                with open(file_path, "r", encoding="utf-8") as f:
                    code = f.read()
                
                # 提取类信息
                file_classes, file_relationships = await self._parse_code(code)
                classes.extend(file_classes)
                relationships.extend(file_relationships)
            
            # 根据图表类型生成相应的UML图
            if diagram_type == "class":
                return await self.generate_class_diagram(
                    classes=classes,
                    relationships=relationships,
                    title=f"Class Diagram from Code"
                )
            else:
                raise UMLGenerationError(f"不支持的图表类型: {diagram_type}")
        except Exception as e:
            raise UMLGenerationError(f"从代码文件生成UML图失败: {str(e)}")
    
    async def _parse_code(self, code: str) -> tuple:
        """
        解析代码，提取类和关系信息
        
        Args:
            code: 代码内容
            
        Returns:
            类信息列表和关系信息列表的元组
        """
        try:
            classes = []
            relationships = []
            
            # 提取类定义
            class_pattern = r"class\s+(\w+)(?:\(([^)]+)\))?:"
            class_matches = re.finditer(class_pattern, code)
            
            for match in class_matches:
                class_name = match.group(1)
                base_classes = match.group(2)
                
                if base_classes:
                    base_classes = [bc.strip() for bc in base_classes.split(",")]
                else:
                    base_classes = []
                
                # 提取属性
                attributes = []
                attr_pattern = r"(\s*)(self\.\w+\s*=\s*[^#\n]+)"
                attr_matches = re.finditer(attr_pattern, code)
                
                for attr_match in attr_matches:
                    indent = attr_match.group(1)
                    attr_line = attr_match.group(2)
                    
                    # 只处理类定义内的属性
                    if indent and not indent.startswith("    "):
                        continue
                    
                    # 解析属性
                    attr_parts = attr_line.split("=", 1)
                    if len(attr_parts) == 2:
                        attr_name = attr_parts[0].strip().replace("self.", "")
                        attr_value = attr_parts[1].strip()
                        
                        attributes.append({
                            "name": attr_name,
                            "visibility": "+",
                            "type": "Any"  # 简化处理，实际应该推断类型
                        })
                
                # 提取方法
                methods = []
                method_pattern = r"(\s*)def\s+(\w+)\s*\(([^)]*)\):"
                method_matches = re.finditer(method_pattern, code)
                
                for method_match in method_matches:
                    indent = method_match.group(1)
                    method_name = method_match.group(2)
                    params = method_match.group(3)
                    
                    # 只处理类定义内的方法
                    if indent and not indent.startswith("    "):
                        continue
                    
                    # 解析参数
                    parameters = []
                    if params.strip():
                        for param in params.split(","):
                            param = param.strip()
                            if param == "self":
                                continue
                            
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
                            else:
                                param_name = param
                                param_type = "Any"
                                default_value = None
                            
                            parameters.append({
                                "name": param_name,
                                "type": param_type,
                                "default_value": default_value
                            })
                    
                    # 简化处理返回类型
                    return_type = "None"
                    
                    methods.append({
                        "name": method_name,
                        "visibility": "+",
                        "parameters": parameters,
                        "return_type": return_type
                    })
                
                classes.append({
                    "name": class_name,
                    "attributes": attributes,
                    "methods": methods
                })
                
                # 添加继承关系
                for base_class in base_classes:
                    relationships.append({
                        "from": class_name,
                        "to": base_class,
                        "type": "inheritance"
                    })
            
            return classes, relationships
        except Exception as e:
            raise UMLGenerationError(f"解析代码失败: {str(e)}")
    
    def set_output_format(self, format: str):
        """
        设置输出格式
        
        Args:
            format: 输出格式（png, svg, pdf等）
        """
        try:
            self.format = format.lower()
            self.logger.info(f"设置输出格式: {self.format}")
        except Exception as e:
            raise UMLGenerationError(f"设置输出格式失败: {str(e)}")
    
    def set_output_directory(self, output_dir: str):
        """
        设置输出目录
        
        Args:
            output_dir: 输出目录
        """
        try:
            self.output_dir = output_dir
            os.makedirs(output_dir, exist_ok=True)
            self.logger.info(f"设置输出目录: {self.output_dir}")
        except Exception as e:
            raise UMLGenerationError(f"设置输出目录失败: {str(e)}")