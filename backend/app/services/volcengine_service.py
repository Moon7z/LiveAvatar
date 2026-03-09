import httpx
import base64
import json
import time
import os
import uuid

class VolcengineAvatarService:
    """火山引擎数字人视频生成服务"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://open.volcengineapi.com"
        
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
    
    async def generate_video(self, avatar_id: str, text: str = None, 
                             audio_path: str = None) -> dict:
        """
        生成数字人视频
        
        Args:
            avatar_id: 形象ID
            text: 文本内容
            audio_path: 音频文件路径
        
        Returns:
            dict: {"task_id": str, "status": str}
        """
        url = f"{self.base_url}/api/v3/contents/generation/avatar/video"
        
        data = {
            "avatar_id": avatar_id
        }
        
        if text:
            data["text"] = text
            data["voice_type"] = "zh_female_tianmei"
        
        if audio_path:
            with open(audio_path, "rb") as f:
                audio_data = base64.b64encode(f.read()).decode()
            data["audio_base64"] = audio_data
        
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
        """查询视频生成状态"""
        url = f"{self.base_url}/api/v3/contents/generation/avatar/video/status"
        
        data = {"task_id": task_id}
        
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


# 火山引擎 TTS 服务（已验证可用）
class VolcengineTTSService:
    """火山引擎 TTS 服务"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://openspeech.byteds.com/api/v1/tts"
    
    async def synthesize(self, text: str, voice_type: str = "zh_female_tianmei",
                         speed: float = 1.0, output_path: str = None) -> dict:
        """文本转语音"""
        
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
                
                duration = len(text) / 4.0
                
                return {
                    "audio_path": output_path,
                    "duration": round(duration, 2)
                }
            else:
                raise Exception(f"TTS 失败: {result}")


# 全局实例
volcengine_avatar_service = None
volcengine_tts_service = None

def init_volcengine(api_key: str):
    """初始化火山引擎服务"""
    global volcengine_avatar_service, volcengine_tts_service
    volcengine_avatar_service = VolcengineAvatarService(api_key)
    volcengine_tts_service = VolcengineTTSService(api_key)