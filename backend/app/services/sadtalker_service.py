import subprocess
import uuid
import os
import asyncio
from app.config import settings


class SadTalkerService:
    """SadTalker 数字人视频生成服务"""
    
    def __init__(self):
        self.sadtalker_path = settings.SADTALKER_PATH
        self.device = settings.SADTALKER_DEVICE
        self.output_dir = os.path.join(settings.OUTPUT_DIR, "videos")
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def generate_video(self, image_path: str, audio_path: str, 
                             resolution: str = "1080x1920") -> dict:
        """
        生成数字人视频
        
        Args:
            image_path: 形象图片路径
            audio_path: 音频文件路径
            resolution: 输出分辨率
        
        Returns:
            dict: {"task_id": str, "video_path": str}
        """
        task_id = str(uuid.uuid4())
        
        # 检查 SadTalker 是否存在
        if not os.path.exists(self.sadtalker_path):
            # SadTalker 未安装，返回 mock
            return await self._mock_generate(task_id, image_path, audio_path)
        
        # 真实调用 SadTalker
        output_dir = os.path.join(self.output_dir, task_id)
        os.makedirs(output_dir, exist_ok=True)
        
        cmd = [
            "python", os.path.join(self.sadtalker_path, "inference.py"),
            "--driven_audio", audio_path,
            "--source_image", image_path,
            "--result_dir", output_dir,
            "--still",  # 减少头部运动
            "--enhancer", "gfpgan"  # 面部增强
        ]
        
        if self.device == "cuda":
            cmd.append("--gpu")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.wait()
        
        # 查找生成的视频文件
        video_files = [f for f in os.listdir(output_dir) if f.endswith('.mp4')]
        if video_files:
            video_path = os.path.join(output_dir, video_files[0])
            return {
                "task_id": task_id,
                "video_path": video_path,
                "video_url": f"/outputs/videos/{task_id}/{video_files[0]}"
            }
        
        raise Exception("视频生成失败")
    
    async def _mock_generate(self, task_id: str, image_path: str, audio_path: str) -> dict:
        """
        Mock 生成（用于开发测试，SadTalker 未安装时）
        实际生产环境需要安装 SadTalker
        """
        # 创建一个简单的静态视频（图片 + 音频合成）
        output_path = os.path.join(self.output_dir, f"{task_id}.mp4")
        
        # 使用 FFmpeg 将图片和音频合成为视频
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.wait()
        
        if os.path.exists(output_path):
            return {
                "task_id": task_id,
                "video_path": output_path,
                "video_url": f"/outputs/videos/{task_id}.mp4"
            }
        
        raise Exception("Mock 视频生成失败，请确保 FFmpeg 已安装")


# 单例
sadtalker_service = SadTalkerService()