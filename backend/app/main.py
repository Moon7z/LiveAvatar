from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

from app.config import settings
from app.routers import avatar, tts, video, live
from app.database import init_db

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description="一张图片 + 一段文字 → 自动生成数字人直播视频",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(avatar.router)
app.include_router(tts.router)
app.include_router(video.router)
app.include_router(live.router)

# 挂载静态文件目录
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
upload_dir = os.path.join(backend_dir, settings.UPLOAD_DIR)
output_dir = os.path.join(backend_dir, settings.OUTPUT_DIR)

os.makedirs(upload_dir, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")
app.mount("/outputs", StaticFiles(directory=output_dir), name="outputs")


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    init_db()


@app.get("/")
async def root():
    """返回前端页面"""
    frontend_path = os.path.join(backend_dir, "frontend", "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "message": "一张图片 + 一段文字 → 自动生成数字人直播视频"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}