import subprocess
import os
import asyncio
from app.config import settings


class VideoService:
    """FFmpeg 视频处理服务"""
    
    def __init__(self):
        self.output_dir = os.path.join(settings.OUTPUT_DIR, "videos")
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def resize(self, input_path: str, resolution: str = "1080x1920") -> str:
        """
        调整视频分辨率
        
        Args:
            input_path: 输入视频路径
            resolution: 目标分辨率 (宽x高)
        
        Returns:
            str: 输出视频路径
        """
        width, height = resolution.split("x")
        output_path = input_path.replace(".mp4", f"_{resolution}.mp4")
        
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
            "-c:a", "copy",
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(*cmd)
        await process.wait()
        
        return output_path
    
    async def loop_video(self, input_path: str, duration_seconds: int = 3600) -> str:
        """
        循环视频
        
        Args:
            input_path: 输入视频路径
            duration_seconds: 循环时长（秒）
        
        Returns:
            str: 输出视频路径
        """
        output_path = input_path.replace(".mp4", "_loop.mp4")
        
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", input_path,
            "-c", "copy",
            "-t", str(duration_seconds),
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(*cmd)
        await process.wait()
        
        return output_path
    
    async def add_background(self, input_path: str, background_color: str = "#ffffff") -> str:
        """
        添加背景色
        
        Args:
            input_path: 输入视频路径
            background_color: 背景颜色
        
        Returns:
            str: 输出视频路径
        """
        output_path = input_path.replace(".mp4", "_bg.mp4")
        
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", f"pad=iw+20:ih+20:10:10:{background_color}",
            "-c:a", "copy",
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(*cmd)
        await process.wait()
        
        return output_path


# 单例
video_service = VideoService()