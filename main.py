#!/usr/bin/env python3
"""
AI Agent Flow 主入口
"""

import sys
from cli.interface import CLIInterface


def main():
    """主函数"""
    cli = CLIInterface()
    cli.run()


if __name__ == "__main__":
    main()