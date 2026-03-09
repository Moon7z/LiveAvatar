from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ============ 通用响应 ============
class Response(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[dict] = None


# ============ 形象相关 ============
class AvatarUpload(BaseModel):
    name: Optional[str] = None


class Avatar(BaseModel):
    avatar_id: str
    name: str
    image_url: str
    created_at: datetime


class AvatarListResponse(BaseModel):
    avatars: List[Avatar]
    total: int


# ============ TTS 相关 ============
class TTSSynthesize(BaseModel):
    text: str
    voice_type: str = "zh_female_tianmei"
    speed: float = 1.0
    pitch: float = 1.0


class Voice(BaseModel):
    voice_id: str
    name: str
    gender: str
    language: str


class TTSResponse(BaseModel):
    audio_id: str
    audio_url: str
    duration: float


# ============ 视频相关 ============
class VideoGenerate(BaseModel):
    avatar_id: str
    audio_id: str
    resolution: str = "1080x1920"
    background: str = "#ffffff"


class VideoTask(BaseModel):
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: int
    video_url: Optional[str] = None
    duration: Optional[float] = None
    error: Optional[str] = None


# ============ 直播相关 ============
class LiveStart(BaseModel):
    video_id: str
    platform: str  # douyin, bilibili, wechat
    stream_url: str
    stream_key: str


class LiveStatus(BaseModel):
    live_id: str
    status: str  # streaming, stopped
    started_at: Optional[datetime] = None
    duration: Optional[int] = None