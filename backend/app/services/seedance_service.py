import httpx
import base64
import uuid
import os

class VolcengineSeedanceService:
    """火山引擎豆包 Seedance 视频生成服务"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks"
        self.model = "doubao-seedance-1-0-lite-i2v-250428"
    
    def _get_headers(self):
        """获取请求头"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    async def generate_video_from_image(self, image_path: str, prompt: str = "人物自然说话，口型同步，表情生动") -> dict:
        """
        从图片生成视频
        
        Args:
            image_path: 图片路径
            prompt: 视频描述提示词
        
        Returns:
            dict: {"task_id": str, "status": str}
        """
        # 读取图片并转为 base64
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        # 获取图片格式
        ext = os.path.splitext(image_path)[1].lower()
        mime_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"
        
        data = {
            "model": self.model,
            "content": [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_data}"
                    }
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.base_url,
                headers=self._get_headers(),
                json=data
            )
            result = response.json()
            
            if "task_id" in result:
                return {
                    "task_id": result["task_id"],
                    "status": "processing"
                }
            else:
                raise Exception(f"视频生成失败: {result}")
    
    async def get_task_status(self, task_id: str) -> dict:
        """
        查询任务状态
        
        Args:
            task_id: 任务ID
        
        Returns:
            dict: {"status": str, "video_url": str, "progress": int}
        """
        url = f"https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/{task_id}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self._get_headers())
            result = response.json()
            
            status = result.get("status", "unknown")
            
            # 状态映射
            status_map = {
                "pending": "pending",
                "processing": "processing",
                "completed": "completed",
                "failed": "failed"
            }
            
            video_url = None
            if status == "completed" and "output" in result:
                # 获取视频URL
                output = result["output"]
                if isinstance(output, dict) and "video_url" in output:
                    video_url = output["video_url"]
                elif isinstance(output, list) and len(output) > 0:
                    video_url = output[0].get("video_url")
            
            return {
                "status": status_map.get(status, status),
                "progress": 100 if status == "completed" else 50,
                "video_url": video_url,
                "error": result.get("error")
            }
    
    async def download_video(self, video_url: str, output_path: str) -> str:
        """下载视频"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(video_url)
            with open(output_path, "wb") as f:
                f.write(response.content)
        return output_path


# 单例
volcengine_seedance_service = None

def init_seedance_service(api_key: str):
    """初始化 Seedance 服务"""
    global volcengine_seedance_service
    volcengine_seedance_service = VolcengineSeedanceService(api_key)