import httpx
import base64
import uuid
import os
from app.config import settings


class TTSService:
    """火山引擎 TTS 服务"""
    
    # 可用音色列表
    VOICES = [
        {"voice_id": "zh_female_tianmei", "name": "甜美女声", "gender": "female", "language": "zh-CN"},
        {"voice_id": "zh_male_chunhou", "name": "醇厚男声", "gender": "male", "language": "zh-CN"},
        {"voice_id": "zh_female_wanwan", "name": "温婉女声", "gender": "female", "language": "zh-CN"},
        {"voice_id": "zh_male_hunhou", "name": "浑厚男声", "gender": "male", "language": "zh-CN"},
    ]
    
    def __init__(self):
        self.api_key = settings.VOLCENGINE_API_KEY
        self.output_dir = os.path.join(settings.OUTPUT_DIR, "audio")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def get_voices(self):
        """获取可用音色列表"""
        return self.VOICES
    
    async def synthesize(self, text: str, voice_type: str = "zh_female_tianmei", 
                         speed: float = 1.0, pitch: float = 1.0) -> dict:
        """
        文本转语音
        
        Args:
            text: 要合成的文本
            voice_type: 音色ID
            speed: 语速 (0.5-2.0)
            pitch: 音调 (0.5-2.0)
        
        Returns:
            dict: {"audio_id": str, "audio_url": str, "duration": float}
        """
        audio_id = str(uuid.uuid4())
        audio_path = os.path.join(self.output_dir, f"{audio_id}.mp3")
        
        # 火山引擎 TTS API 调用
        url = "https://openspeech.byteds.com/api/v1/tts"
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
                "pitch_ratio": pitch
            },
            "request": {
                "reqid": audio_id,
                "text": text,
                "operation": "query"
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=data)
                result = response.json()
                
                if result.get("code") != 3000:
                    raise Exception(f"TTS API 错误: {result}")
                
                # 解码 base64 音频数据
                audio_data = base64.b64decode(result["data"])
                
                # 保存音频文件
                with open(audio_path, "wb") as f:
                    f.write(audio_data)
                
                # 估算时长 (粗略计算：假设平均语速 4 字符/秒)
                duration = len(text) / 4.0
                
                return {
                    "audio_id": audio_id,
                    "audio_url": f"/outputs/audio/{audio_id}.mp3",
                    "duration": round(duration, 2)
                }
                
        except Exception as e:
            # 如果 API 调用失败，使用 gTTS 作为备用
            print(f"火山引擎 TTS 失败，使用 gTTS 备用: {e}")
            return await self._synthesize_gtts(text, audio_id, audio_path)
    
    async def _synthesize_gtts(self, text: str, audio_id: str, audio_path: str) -> dict:
        """使用 gTTS 作为备用方案"""
        from gtts import gTTS
        
        tts = gTTS(text=text, lang='zh-CN')
        tts.save(audio_path)
        
        # 估算时长
        duration = len(text) / 4.0
        
        return {
            "audio_id": audio_id,
            "audio_url": f"/outputs/audio/{audio_id}.mp3",
            "duration": round(duration, 2)
        }


# 单例
tts_service = TTSService()