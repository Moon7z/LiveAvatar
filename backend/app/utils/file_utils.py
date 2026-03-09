import os
import uuid
import aiofiles
from datetime import datetime
from fastapi import UploadFile
from app.config import settings


class FileUtils:
    """文件处理工具"""
    
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.output_dir = settings.OUTPUT_DIR
        self.max_size = settings.MAX_UPLOAD_SIZE
        
        # 确保目录存在
        os.makedirs(os.path.join(self.upload_dir, "avatars"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "audio"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "videos"), exist_ok=True)
    
    async def save_upload(self, file: UploadFile, subfolder: str = "") -> tuple:
        """
        保存上传文件
        
        Args:
            file: 上传的文件对象
            subfolder: 子文件夹名称
        
        Returns:
            tuple: (file_id, file_path, file_url)
        """
        file_id = str(uuid.uuid4())
        
        # 获取文件扩展名
        ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
        
        # 构建保存路径
        save_dir = os.path.join(self.upload_dir, subfolder)
        os.makedirs(save_dir, exist_ok=True)
        
        file_path = os.path.join(save_dir, f"{file_id}{ext}")
        file_url = f"/uploads/{subfolder}/{file_id}{ext}"
        
        # 保存文件
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            
            # 检查文件大小
            if len(content) > self.max_size:
                raise ValueError(f"文件大小超过限制 ({self.max_size / 1024 / 1024}MB)")
            
            await f.write(content)
        
        return file_id, file_path, file_url
    
    def get_file_path(self, file_url: str) -> str:
        """根据 URL 获取文件路径"""
        # /uploads/avatars/xxx.jpg -> uploads/avatars/xxx.jpg
        relative_path = file_url.lstrip("/")
        return os.path.join(self.upload_dir if "uploads" in file_url else self.output_dir, 
                           relative_path.split("/", 1)[1] if "/" in relative_path else relative_path)
    
    def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception as e:
            print(f"删除文件失败: {e}")
        return False


# 单例
file_utils = FileUtils()