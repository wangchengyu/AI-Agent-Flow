"""
AI Agent Flow 系统安装脚本

用于项目的安装、打包和分发。
"""

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# 读取requirements.txt
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ai-agent-flow",
    version="1.0.0",
    author="AI Agent Flow Team",
    author_email="team@aiagentflow.com",
    description="一个基于多智能体协作的AI驱动工程实现闭环系统",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/aiagentflow/ai-agent-flow",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "agent-flow=src.cli.cli_application:main",
        ],
    },
    include_package_data=True,
    package_data={
        "src.config": ["*.json", "*.yaml", "*.yml"],
        "src": ["*.md", "*.txt"],
    },
    zip_safe=False,
    keywords="ai agent crew mcp rag cli",
    project_urls={
        "Bug Reports": "https://github.com/aiagentflow/ai-agent-flow/issues",
        "Source": "https://github.com/aiagentflow/ai-agent-flow",
        "Documentation": "https://ai-agent-flow.readthedocs.io/",
    },
)