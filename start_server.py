#!/usr/bin/env python3
"""
Alex系统启动脚本
确保正确的Python路径设置，避免相对导入问题
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
api_dir = project_root / "api"

# 确保api目录在Python路径中
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

# 设置工作目录为api目录
os.chdir(api_dir)

# 导入并启动FastAPI应用
if __name__ == "__main__":
    import uvicorn
    from main import app

    print("🚀 启动Alex系统后端服务...")
    print(f"📁 工作目录: {os.getcwd()}")
    print(f"🐍 Python路径: {sys.path[:3]}...")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
