# LiveAvatar 后端开发需求文档

## 项目概述

**项目名称：** LiveAvatar  
**目标：** 一张图片 + 一段文字 → 自动生成数字人直播视频  
**技术栈：** Python FastAPI + SadTalker + 火山引擎 TTS + FFmpeg

---

## 一、项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── avatar.py        # 形象管理 API
│   │   ├── tts.py           # 语音合成 API
│   │   ├── video.py         # 视频生成 API
│   │   └── live.py          # 直播控制 API
│   ├── services/
│   │   ├── __init__.py
│   │   ├── sadtalker_service.py   # SadTalker 封装
│   │   ├── tts_service.py         # TTS 封装
│   │   └── video_service.py       # FFmpeg 封装
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic 模型
│   └── utils/
│       ├── __init__.py
│       └── file_utils.py    # 文件处理工具
├── uploads/                 # 上传文件存储
├── outputs/                 # 生成视频存储
├── requirements.txt
├── .env.example
└── README.md
```

---

## 二、API 设计

### 2.1 形象管理 API (`/api/avatar`)

#### POST `/api/avatar/upload`
**功能：** 上传形象图片  
**请求：** `multipart/form-data`
- `file`: 图片文件 (JPG/PNG)
- `name`: 形象名称 (可选)

**响应：**
```json
{
  "code": 200,
  "data": {
    "avatar_id": "uuid-xxx",
    "name": "形象1",
    "image_url": "/uploads/avatars/xxx.jpg",
    "created_at": "2026-03-07T12:00:00Z"
  }
}
```

#### GET `/api/avatar/list`
**功能：** 获取形象列表

**响应：**
```json
{
  "code": 200,
  "data": {
    "avatars": [
      {
        "avatar_id": "uuid-xxx",
        "name": "形象1",
        "image_url": "/uploads/avatars/xxx.jpg",
        "created_at": "2026-03-07T12:00:00Z"
      }
    ],
    "total": 1
  }
}
```

#### DELETE `/api/avatar/{avatar_id}`
**功能：** 删除形象

---

### 2.2 语音合成 API (`/api/tts`)

#### POST `/api/tts/synthesize`
**功能：** 文本转语音  
**请求：**
```json
{
  "text": "欢迎来到直播间",
  "voice_type": "zh_female_tianmei",
  "speed": 1.0,
  "pitch": 1.0
}
```

**响应：**
```json
{
  "code": 200,
  "data": {
    "audio_id": "uuid-xxx",
    "audio_url": "/outputs/audio/xxx.mp3",
    "duration": 3.5
  }
}
```

#### GET `/api/tts/voices`
**功能：** 获取可用音色列表

**响应：**
```json
{
  "code": 200,
  "data": {
    "voices": [
      {
        "voice_id": "zh_female_tianmei",
        "name": "甜美女声",
        "gender": "female",
        "language": "zh-CN"
      },
      {
        "voice_id": "zh_male_chunhou",
        "name": "醇厚男声",
        "gender": "male",
        "language": "zh-CN"
      }
    ]
  }
}
```

---

### 2.3 视频生成 API (`/api/video`)

#### POST `/api/video/generate`
**功能：** 生成数字人视频  
**请求：**
```json
{
  "avatar_id": "uuid-xxx",
  "audio_id": "uuid-xxx",
  "resolution": "1080x1920",
  "background": "#ffffff"
}
```

**响应：**
```json
{
  "code": 200,
  "data": {
    "task_id": "task-xxx",
    "status": "processing",
    "estimated_time": 60
  }
}
```

#### GET `/api/video/status/{task_id}`
**功能：** 查询视频生成状态

**响应：**
```json
{
  "code": 200,
  "data": {
    "task_id": "task-xxx",
    "status": "completed",
    "progress": 100,
    "video_url": "/outputs/videos/xxx.mp4",
    "duration": 10.5
  }
}
```

#### GET `/api/video/list`
**功能：** 获取视频列表

---

### 2.4 直播控制 API (`/api/live`)

#### POST `/api/live/start`
**功能：** 开始直播  
**请求：**
```json
{
  "video_id": "uuid-xxx",
  "platform": "douyin",
  "stream_url": "rtmp://xxx",
  "stream_key": "xxx"
}
```

**响应：**
```json
{
  "code": 200,
  "data": {
    "live_id": "live-xxx",
    "status": "streaming",
    "started_at": "2026-03-07T12:00:00Z"
  }
}
```

#### POST `/api/live/stop/{live_id}`
**功能：** 停止直播

#### GET `/api/live/status/{live_id}`
**功能：** 查询直播状态

---

## 三、核心服务实现

### 3.1 TTS 服务 (`services/tts_service.py`)

**需求：**
- 封装火山引擎 TTS API
- 支持多种音色选择
- 支持语速、音调调节
- 返回音频文件路径

**火山引擎 API 调用示例：**
```python
import httpx

async def synthesize(text: str, voice_type: str, speed: float = 1.0):
    url = "https://openspeech.byteds.com/api/v1/tts"
    headers = {
        "Authorization": f"Bearer {VOLCENGINE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "app": {"appid": "default", "token": "access_token"},
        "user": {"uid": "user1"},
        "audio": {
            "voice_type": voice_type,
            "encoding": "mp3",
            "speed_ratio": speed,
            "volume_ratio": 1.0,
            "pitch_ratio": 1.0
        },
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": text,
            "operation": "query"
        }
    }
    response = await httpx.post(url, headers=headers, json=data)
    result = response.json()
    # 解码 base64 音频数据并保存
    audio_data = base64.b64decode(result["data"])
    # 保存到文件
    audio_path = f"outputs/audio/{uuid.uuid4()}.mp3"
    async with aiofiles.open(audio_path, "wb") as f:
        await f.write(audio_data)
    return audio_path
```

**可用音色：**
- `zh_female_tianmei` - 甜美女声
- `zh_male_chunhou` - 醇厚男声
- `zh_female_wanwan` - 温婉女声
- `zh_male_hunhou` - 浑厚男声

---

### 3.2 SadTalker 服务 (`services/sadtalker_service.py`)

**需求：**
- 封装 SadTalker 推理接口
- 输入：图片路径 + 音频路径
- 输出：视频文件路径
- 支持 GPU 加速
- 支持多种分辨率

**SadTalker 调用示例：**
```python
import subprocess

async def generate_video(image_path: str, audio_path: str, output_path: str):
    """
    使用 SadTalker 生成数字人视频
    """
    cmd = [
        "python", "inference.py",
        "--driven_audio", audio_path,
        "--source_image", image_path,
        "--result_dir", output_path,
        "--still",  # 减少头部运动，更适合直播
        "--enhancer", "gfpgan"  # 面部增强
    ]
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.wait()
    return output_path
```

**安装 SadTalker：**
```bash
git clone https://github.com/OpenTalker/SadTalker.git
cd SadTalker
pip install -r requirements.txt
# 下载预训练模型
```

---

### 3.3 FFmpeg 服务 (`services/video_service.py`)

**需求：**
- 视频格式转换
- 视频分辨率调整
- 背景替换
- 视频拼接（循环播放）

**FFmpeg 常用命令：**
```bash
# 调整分辨率 (竖屏 1080x1920)
ffmpeg -i input.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2" output.mp4

# 视频循环
ffmpeg -stream_loop -1 -i input.mp4 -c copy -t 3600 output.mp4

# 添加背景音乐
ffmpeg -i video.mp4 -i audio.mp3 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 output.mp4
```

---

## 四、数据模型 (`models/schemas.py`)

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# 形象相关
class AvatarUpload(BaseModel):
    name: Optional[str] = None

class Avatar(BaseModel):
    avatar_id: str
    name: str
    image_url: str
    created_at: datetime

# TTS 相关
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

# 视频相关
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

# 直播相关
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
```

---

## 五、配置文件 (`config.py`)

```python
from pydantic_settings import BaseSettings

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
    SADTALKER_DEVICE: str = "cuda"  # cuda 或 cpu
    
    # 文件存储
    UPLOAD_DIR: str = "./uploads"
    OUTPUT_DIR: str = "./outputs"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # 视频配置
    DEFAULT_RESOLUTION: str = "1080x1920"
    SUPPORTED_RESOLUTIONS: list = ["720x1280", "1080x1920", "1920x1080"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 六、环境变量 (`.env.example`)

```env
# 服务配置
DEBUG=true
HOST=0.0.0.0
PORT=8000

# 火山引擎 TTS
VOLCENGINE_API_KEY=your_api_key_here

# SadTalker
SADTALKER_PATH=./SadTalker
SADTALKER_DEVICE=cuda

# 文件存储
UPLOAD_DIR=./uploads
OUTPUT_DIR=./outputs
```

---

## 七、开发优先级

### Phase 1 (核心功能)
1. ✅ 项目结构搭建
2. 🚧 TTS 服务集成 (火山引擎)
3. 🚧 SadTalker 集成
4. 🚧 视频生成 API

### Phase 2 (完善功能)
5. 前端 UI
6. OBS 推流集成
7. 视频循环播放

### Phase 3 (优化)
8. 性能优化
9. 错误处理
10. 文档完善

---

## 八、注意事项

1. **GPU 依赖：** SadTalker 需要 GPU 加速，确保服务器有 CUDA 环境
2. **并发处理：** 视频生成耗时，建议使用异步任务队列 (Celery 或 asyncio)
3. **文件清理：** 定期清理临时文件，避免磁盘占用过多
4. **API 限流：** 防止滥用，建议添加请求频率限制
5. **错误处理：** 所有 API 需要有完善的错误处理和日志记录

---

## 九、测试用例

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_tts_synthesize():
    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.post("/api/tts/synthesize", json={
            "text": "测试语音合成",
            "voice_type": "zh_female_tianmei"
        })
        assert response.status_code == 200
        data = response.json()
        assert "audio_url" in data["data"]

@pytest.mark.asyncio
async def test_video_generate():
    # 先上传形象
    # 再合成语音
    # 最后生成视频
    pass
```

---

**以上是完整的后端需求文档，可以直接交给 AI 编程工具执行。**