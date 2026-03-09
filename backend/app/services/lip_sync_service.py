import httpx
import base64
import uuid
import os
import time

class LipSyncService:
    """火山引擎单图音频驱动服务 - 实现口型同步"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        # 智能视觉服务 API
        self.base_url = "https://open.volcengineapi.com"
        self.service = "cv"
        self.version = "2022-08-31"
    
    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_avatar(self, image_path: str) -> dict:
        """
        步骤1: 创建数字人形象
        
        Args:
            image_path: 图片路径
        
        Returns:
            dict: {"avatar_id": str}
        """
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        url = f"{self.base_url}/api/v3/contents/generation/avatar/create"
        
        data = {
            "image_base64": image_data,
            "image_type": "jpeg"
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
    
    async def generate_lipsync_video(self, avatar_id: str, audio_path: str, 
                                       output_path: str = None) -> dict:
        """
        步骤2: 生成口型同步视频
        
        Args:
            avatar_id: 形象ID
            audio_path: 音频文件路径
            output_path: 视频输出路径
        
        Returns:
            dict: {"task_id": str, "video_url": str}
        """
        with open(audio_path, "rb") as f:
            audio_data = base64.b64encode(f.read()).decode()
        
        url = f"{self.base_url}/api/v3/contents/generation/avatar/video"
        
        data = {
            "avatar_id": avatar_id,
            "audio_base64": audio_data,
            "audio_type": "mp3"
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=self._get_headers(), json=data)
            result = response.json()
            
            if result.get("code") == 10000:
                task_id = result["data"]["task_id"]
                
                # 轮询等待完成
                video_url = await self._wait_for_video(task_id, client)
                
                if video_url and output_path:
                    # 下载视频
                    video_response = await client.get(video_url)
                    with open(output_path, "wb") as f:
                        f.write(video_response.content)
                    
                    return {
                        "task_id": task_id,
                        "video_url": video_url,
                        "video_path": output_path
                    }
                
                return {
                    "task_id": task_id,
                    "video_url": video_url
                }
            else:
                raise Exception(f"视频生成失败: {result}")
    
    async def _wait_for_video(self, task_id: str, client: httpx.AsyncClient, 
                               max_wait: int = 300) -> str:
        """等待视频生成完成"""
        url = f"{self.base_url}/api/v3/contents/generation/avatar/video/status"
        
        for _ in range(max_wait // 5):
            data = {"task_id": task_id}
            response = await client.post(url, headers=self._get_headers(), json=data)
            result = response.json()
            
            status = result.get("data", {}).get("status")
            
            if status == "completed":
                return result["data"].get("video_url")
            elif status == "failed":
                raise Exception(f"视频生成失败: {result}")
            
            await asyncio.sleep(5)
        
        raise Exception("视频生成超时")
    
    async def generate_from_image_audio(self, image_path: str, audio_path: str,
                                         output_path: str = None) -> dict:
        """
        一键生成口型同步视频
        
        Args:
            image_path: 图片路径
            audio_path: 音频路径
            output_path: 输出路径
        
        Returns:
            dict: {"video_path": str}
        """
        # 步骤1: 创建形象
        avatar_result = await self.create_avatar(image_path)
        avatar_id = avatar_result["avatar_id"]
        
        # 步骤2: 生成视频
        video_result = await self.generate_lipsync_video(
            avatar_id, audio_path, output_path
        )
        
        return video_result


# 全局实例
lip_sync_service = None

def init_lip_sync_service(api_key: str):
    global lip_sync_service
    lip_sync_service = LipSyncService(api_key)