#!/bin/bash
# LiveAvatar 启动脚本

export PATH="$HOME/miniconda3/bin:$PATH"
source activate liveavatar

cd /home/admin/.openclaw/workspace/projects/LiveAvatar/backend

echo "正在启动 LiveAvatar 服务..."
echo "访问地址: http://47.96.117.215:8000"
echo "API文档: http://47.96.117.215:8000/docs"
echo ""

python run.py