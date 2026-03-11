import uuid
import os
import time
import base64
import subprocess
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import httpx

from app.models.schemas import Response, VideoGenerate
from app.utils.file_utils import file_utils
from app.database import get_db, VideoModel, AvatarModel, AudioModel
from app.config import settings

router = APIRouter(prefix="/api/video", tags=["视频生成"])


class VideoGenerationService:
    """视频生成服务 - 标准化配置"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks"
        self.model = "doubao-seedance-1-5-pro-251215"
        
        # 标准化提示词模板
        self.prompt_template = (
            "固定摄像机位置，绝对禁止镜头往前推进或往后拉远，"
            "禁止任何形式的镜头移动，人物位置保持不变，"
            "保持原始人物比例不变形，表情生动自然"
        )
    
    def _get_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    async def generate(self, image_path: str, duration: int = 10, ratio: str = "3:4") -> dict:
        """生成视频"""
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        data = {
            "model": self.model,
            "content": [
                {"type": "text", "text": self.prompt_template},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
            ],
            "duration": duration,
            "ratio": ratio
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.base_url,
                headers=self._get_headers(),
                json=data
            )
            return response.json()
    
    async def get_status(self, task_id: str) -> dict:
        """查询任务状态"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/{task_id}",
                headers=self._get_headers()
            )
            return response.json()
    
    async def download_video(self, video_url: str, output_path: str):
        """下载视频"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(video_url)
            with open(output_path, "wb") as f:
                f.write(response.content)
    
    def post_process_video(self, input_path: str, output_path: str, target_width: int, target_height: int):
        """
        FFmpeg 后处理 - 保持原图比例
        
        标准处理流程：
        1. 缩放视频以适应目标尺寸（不变形）
        2. 用黑边填充到目标尺寸
        3. 保持音频不变
        """
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black",
            "-c:a", "copy",
            output_path
        ]
        
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_path


def generate_video_task_sync(task_id: str, avatar_path: str, audio_path: str, resolution: str):
    """后台视频生成任务"""
    from sqlalchemy.orm import sessionmaker
    from app.database import engine
    import asyncio
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        video = db.query(VideoModel).filter(VideoModel.task_id == task_id).first()
        if not video:
            return
        
        video.status = "processing"
        video.progress = 20
        db.commit()
        
        output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "outputs", "videos")
        os.makedirs(output_dir, exist_ok=True)
        temp_path = os.path.join(output_dir, f"{task_id}_temp.mp4")
        final_path = os.path.join(output_dir, f"{task_id}.mp4")
        
        # 获取目标分辨率
        width, height = map(int, resolution.split("x"))
        
        # 使用标准化服务生成视频
        service = VideoGenerationService(settings.VOLCENGINE_API_KEY)
        
        import asyncio
        
        # 提交任务
        result = asyncio.run(service.generate(avatar_path, duration=10, ratio="3:4"))
        
        if "id" in result:
            seedance_task_id = result["id"]
            video.progress = 40
            db.commit()
            
            # 等待完成
            for _ in range(60):
                status = asyncio.run(service.get_status(seedance_task_id))
                
                if status.get("status") == "succeeded":
                    video_url = status.get("content", {}).get("video_url")
                    
                    if video_url:
                        # 下载视频
                        asyncio.run(service.download_video(video_url, temp_path))
                        
                        # FFmpeg 后处理 - 保持比例
                        service.post_process_video(temp_path, final_path, width, height)
                        
                        # 清理临时文件
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        
                        if os.path.exists(final_path) and os.path.getsize(final_path) > 0:
                            video.status = "completed"
                            video.progress = 100
                            video.video_url = f"/outputs/videos/{task_id}.mp4"
                            video.duration = 10
                            db.commit()
                            return
                    
                elif status.get("status") == "failed":
                    raise Exception(f"视频生成失败: {status.get('error')}")
                
                time.sleep(5)
        
        raise Exception("视频生成超时")
        
    except Exception as e:
        video = db.query(VideoModel).filter(VideoModel.task_id == task_id).first()
        if video:
            video.status = "failed"
            video.error = str(e)
            db.commit()
    finally:
        db.close()


@router.post("/generate", response_model=Response)
async def generate_video(
    request: VideoGenerate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    生成数字人视频
    
    标准化配置：
    - 固定镜头，禁止镜头移动
    - 保持人物原始比例
    - 人物位置不变
    
    参数：
    - avatar_id: 形象ID
    - audio_id: 音频ID
    - resolution: 分辨率 (默认: 940x1280)
    """
    avatar = db.query(AvatarModel).filter(AvatarModel.avatar_id == request.avatar_id).first()
    if not avatar:
        raise HTTPException(status_code=404, detail="形象不存在")
    
    audio = db.query(AudioModel).filter(AudioModel.audio_id == request.audio_id).first()
    if not audio:
        raise HTTPException(status_code=404, detail="音频不存在")
    
    avatar_path = file_utils.get_file_path(avatar.image_url)
    audio_path = file_utils.get_file_path(audio.audio_url)
    
    task_id = str(uuid.uuid4())
    video = VideoModel(
        task_id=task_id,
        avatar_id=request.avatar_id,
        audio_id=request.audio_id,
        status="pending",
        progress=0,
        created_at=datetime.now()
    )
    db.add(video)
    db.commit()
    
    background_tasks.add_task(
        generate_video_task_sync, 
        task_id, avatar_path, audio_path, request.resolution
    )
    
    return Response(data={
        "task_id": task_id,
        "status": "pending",
        "progress": 0,
        "message": "视频生成任务已提交，使用标准化配置"
    })


@router.get("/status/{task_id}", response_model=Response)
async def get_video_status(task_id: str, db: Session = Depends(get_db)):
    """查询视频生成状态"""
    video = db.query(VideoModel).filter(VideoModel.task_id == task_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return Response(data={
        "task_id": video.task_id,
        "status": video.status,
        "progress": video.progress,
        "video_url": video.video_url,
        "duration": video.duration,
        "error": video.error
    })


@router.get("/list", response_model=Response)
async def list_videos(db: Session = Depends(get_db)):
    """获取视频列表"""
    videos = db.query(VideoModel).order_by(VideoModel.created_at.desc()).limit(50).all()
    
    result = [{
        "task_id": v.task_id,
        "avatar_id": v.avatar_id,
        "status": v.status,
        "progress": v.progress,
        "video_url": v.video_url,
        "duration": v.duration,
        "created_at": v.created_at.isoformat() if v.created_at else None
    } for v in videos]
    
    return Response(data={"videos": result, "total": len(result)})