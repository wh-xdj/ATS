#!/usr/bin/env python3
"""Agent启动脚本（作为模块运行）"""
import sys
from pathlib import Path

# 添加agent目录到Python路径
agent_dir = Path(__file__).parent
sys.path.insert(0, str(agent_dir.parent))

from agent.agent import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())

