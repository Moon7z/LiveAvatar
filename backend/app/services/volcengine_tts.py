import httpx
import base64
import uuid
import os

class VolcengineTTSService:
    """火山引擎 TTS 服务 - 支持多种音色"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://openspeech.byteds.com/api/v1/tts"
        
        # 可用音色列表
        self.voices = [
            {"voice_id": "BV001_streaming", "name": "通用女声", "gender": "female", "language": "zh-CN"},
            {"voice_id": "BV002_streaming", "name": "通用男声", "gender": "male", "language": "zh-CN"},
            {"voice_id": "zh_female_tianmei", "name": "甜美女声", "gender": "female", "language": "zh-CN"},
            {"voice_id": "zh_male_chunhou", "name": "醇厚男声", "gender": "male", "language": "zh-CN"},
            {"voice_id": "zh_female_wanwan", "name": "温婉女声", "gender": "female", "language": "zh-CN"},
            {"voice_id": "zh_male_hunhou", "name": "浑厚男声", "gender": "male", "language": "zh-CN"},
            {"voice_id": "zh_female_xiaomei", "name": "小美女声", "gender": "female", "language": "zh-CN"},
            {"voice_id": "zh_male_xiaoyu", "name": "小宇男声", "gender": "male", "language": "zh-CN"},
        ]
    
    def get_voices(self):
        """获取可用音色列表"""
        return self.voices
    
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
                
                # 估算时长
                duration = len(text) / 4.0
                
                return {
                    "audio_path": output_path,
                    "audio_url": output_path.replace("/tmp", "/outputs/audio"),
                    "duration": round(duration, 2)
                }
            else:
                # 火山引擎失败，使用 gTTS 备用
                return await self._synthesize_gtts(text, output_path)
    
    async def _synthesize_gtts(self, text: str, output_path: str = None) -> dict:
        """gTTS 备用方案"""
        from gtts import gTTS
        
        if not output_path:
            output_path = f"/tmp/tts_{uuid.uuid4()}.mp3"
        
        tts = gTTS(text=text, lang='zh-CN')
        tts.save(output_path)
        
        duration = len(text) / 4.0
        
        return {
            "audio_path": output_path,
            "audio_url": output_path.replace("/tmp", "/outputs/audio"),
            "duration": round(duration, 2)
        }


# 全局实例
volcengine_tts_service = None

def init_tts_service(api_key: str):
    global volcengine_tts_service
    volcengine_tts_service = VolcengineTTSService(api_key)