FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装 FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# 复制代码
COPY . .

# 创建目录
RUN mkdir -p uploads/avatars outputs/audio outputs/videos

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "run.py"]