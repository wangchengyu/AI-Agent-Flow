"""
配置管理器

负责管理系统配置参数，包括加载、保存、获取和设置配置等功能。
支持从环境变量、配置文件和默认配置中加载配置。
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

from .settings import DEFAULT_CONFIG


class ConfigManager:
    """配置管理器，负责管理系统配置参数"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        self.config_file = config_file or os.path.join(os.getcwd(), "config.json")
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置
        
        Returns:
            配置字典
        """
        # 从默认配置开始
        config = DEFAULT_CONFIG.copy()
        
        # 如果配置文件存在，则加载配置文件
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                
                # 递归更新配置
                self._update_config(config, file_config)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
        
        # 从环境变量中加载配置
        self._load_from_env(config)
        
        return config
    
    def _update_config(self, base_config: Dict[str, Any], update_config: Dict[str, Any]):
        """
        递归更新配置
        
        Args:
            base_config: 基础配置
            update_config: 更新配置
        """
        for key, value in update_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self._update_config(base_config[key], value)
            else:
                base_config[key] = value
    
    def _load_from_env(self, config: Dict[str, Any]):
        """
        从环境变量中加载配置
        
        Args:
            config: 配置字典
        """
        # 支持的环境变量格式：AGENT_FLOW_{SECTION}_{KEY}
        env_prefix = "AGENT_FLOW_"
        
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                # 解析环境变量键
                parts = key[len(env_prefix):].lower().split('_')
                if len(parts) >= 2:
                    section = parts[0]
                    setting = '_'.join(parts[1:])
                    
                    # 更新配置
                    if section in config:
                        # 尝试将值转换为适当的类型
                        try:
                            if value.lower() in ('true', 'false'):
                                value = value.lower() == 'true'
                            elif value.isdigit():
                                value = int(value)
                            elif '.' in value and value.replace('.', '').isdigit():
                                value = float(value)
                        except ValueError:
                            pass
                        
                        config[section][setting] = value
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            section: 配置节
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            return self.config[section][key]
        except KeyError:
            return default
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取配置节
        
        Args:
            section: 配置节名
            
        Returns:
            配置节字典
        """
        return self.config.get(section, {})
    
    def set(self, section: str, key: str, value: Any):
        """
        设置配置值
        
        Args:
            section: 配置节
            key: 配置键
            value: 配置值
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
    
    def save(self):
        """保存配置到文件"""
        try:
            # 确保配置文件目录存在
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"保存配置文件失败: {e}")
    
    def reset_to_defaults(self):
        """重置配置为默认值"""
        self.config = DEFAULT_CONFIG.copy()
    
    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置
        
        Returns:
            所有配置字典
        """
        return self.config.copy()
    
    def update_from_dict(self, config_dict: Dict[str, Any]):
        """
        从字典更新配置
        
        Args:
            config_dict: 配置字典
        """
        self._update_config(self.config, config_dict)
    
    def validate_config(self) -> bool:
        """
        验证配置是否有效
        
        Returns:
            配置是否有效
        """
        # 这里可以添加配置验证逻辑
        # 例如检查必需的配置项是否存在，值是否在有效范围内等
        
        # 暂时返回True
        return True