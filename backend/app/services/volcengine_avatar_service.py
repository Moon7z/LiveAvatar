import httpx
import base64
import json
import time
import os

class VolcengineAvatarService:
    """火山引擎数字人视频生成服务"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://open.volcengineapi.com"
        self.service = "cv"
        self.version = "2022-08-31"
        
    def _get_headers(self):
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_avatar(self, image_path: str) -> dict:
        """
        创建数字人形象
        
        Args:
            image_path: 图片路径
        
        Returns:
            dict: {"avatar_id": str, "status": str}
        """
        # 读取图片并转为 base64
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        # 调用形象创建 API
        url = f"{self.base_url}/api/v3/contents/generation/avatar/create"
        
        data = {
            "image_base64": image_data,
            "image_type": "jpg"
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=self._get_headers(), json=data)
            result = response.json()
            
            if result.get("code") == 10000:
                return {
                    "avatar_id": result["data"]["avatar_id"],
                    "status": "created"
                }
            else:
                raise Exception(f"形象创建失败: {result}")
    
    async def generate_video(self, avatar_id: str, audio_path: str = None, 
                             text: str = None, voice_type: str = "zh_female_tianmei") -> dict:
        """
        生成数字人视频
        
        Args:
            avatar_id: 形象ID
            audio_path: 音频文件路径（可选）
            text: 文本内容（可选，如果提供则自动生成语音）
            voice_type: 音色类型
        
        Returns:
            dict: {"task_id": str, "status": str}
        """
        url = f"{self.base_url}/api/v3/contents/generation/avatar/video"
        
        data = {
            "avatar_id": avatar_id
        }
        
        # 如果提供音频文件
        if audio_path:
            with open(audio_path, "rb") as f:
                audio_data = base64.b64encode(f.read()).decode()
            data["audio_base64"] = audio_data
            data["audio_type"] = "mp3"
        
        # 如果提供文本
        if text:
            data["text"] = text
            data["voice_type"] = voice_type
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=self._get_headers(), json=data)
            result = response.json()
            
            if result.get("code") == 10000:
                return {
                    "task_id": result["data"]["task_id"],
                    "status": "processing"
                }
            else:
                raise Exception(f"视频生成失败: {result}")
    
    async def get_video_status(self, task_id: str) -> dict:
        """
        查询视频生成状态
        
        Args:
            task_id: 任务ID
        
        Returns:
            dict: {"status": str, "video_url": str, "progress": int}
        """
        url = f"{self.base_url}/api/v3/contents/generation/avatar/video/status"
        
        data = {
            "task_id": task_id
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=self._get_headers(), json=data)
            result = response.json()
            
            if result.get("code") == 10000:
                return {
                    "status": result["data"]["status"],
                    "progress": result["data"].get("progress", 0),
                    "video_url": result["data"].get("video_url")
                }
            else:
                raise Exception(f"查询状态失败: {result}")
    
    async def generate_video_with_image(self, image_path: str, text: str, 
                                        voice_type: str = "zh_female_tianmei") -> dict:
        """
        一键生成数字人视频（图片 + 文字）
        
        Args:
            image_path: 图片路径
            text: 文本内容
            voice_type: 音色类型
        
        Returns:
            dict: {"task_id": str, "video_url": str}
        """
        # 1. 创建形象
        avatar_result = await self.create_avatar(image_path)
        avatar_id = avatar_result["avatar_id"]
        
        # 2. 生成视频
        video_result = await self.generate_video(
            avatar_id=avatar_id,
            text=text,
            voice_type=voice_type
        )
        
        return video_result


# 使用火山引擎 TTS API 生成语音
class VolcengineTTSService:
    """火山引擎 TTS 服务"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://openspeech.byteds.com/api/v1/tts"
    
    async def synthesize(self, text: str, voice_type: str = "zh_female_tianmei",
                         speed: float = 1.0, output_path: str = None) -> dict:
        """
        文本转语音
        
        Args:
            text: 文本内容
            voice_type: 音色类型
            speed: 语速
            output_path: 输出路径
        
        Returns:
            dict: {"audio_path": str, "duration": float}
        """
        import uuid
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "app": {"appid": "default", "token": "access_token"},
            "user": {"uid": "liveavatar"},
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
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.url, headers=headers, json=data)
            result = response.json()
            
            if result.get("code") == 3000:
                audio_data = base64.b64decode(result["data"])
                
                if not output_path:
                    output_path = f"/tmp/tts_{uuid.uuid4()}.mp3"
                
                with open(output_path, "wb") as f:
                    f.write(audio_data)
                
                duration = len(text) / 4.0  # 估算时长
                
                return {
                    "audio_path": output_path,
                    "duration": round(duration, 2)
                }
            else:
                raise Exception(f"TTS 失败: {result}")


# 单例
volcengine_avatar_service = None
volcengine_tts_service = None

def init_volcengine_services(api_key: str):
    """初始化火山引擎服务"""
    global volcengine_avatar_service, volcengine_tts_service
    volcengine_avatar_service = VolcengineAvatarService(api_key)
    volcengine_tts_service = VolcengineTTSService(api_key)