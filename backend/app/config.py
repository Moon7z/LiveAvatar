from pydantic import BaseSettings, Field
from typing import List


class Settings(BaseSettings):
    # 服务配置
    APP_NAME: str = "LiveAvatar"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 火山引擎 TTS
    VOLCENGINE_API_KEY: str = ""
    
    # SadTalker
    SADTALKER_PATH: str = "./SadTalker"
    SADTALKER_DEVICE: str = "cpu"  # cuda 或 cpu
    
    # 文件存储
    UPLOAD_DIR: str = "./uploads"
    OUTPUT_DIR: str = "./outputs"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # 视频配置
    DEFAULT_RESOLUTION: str = "1080x1920"
    SUPPORTED_RESOLUTIONS: List[str] = ["720x1280", "1080x1920", "1920x1080"]
    
    class Config:
        env_file = ".env"


settings = Settings()