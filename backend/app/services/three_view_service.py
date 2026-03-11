import httpx
import base64
import uuid
import os
import asyncio

class ThreeViewService:
    """火山引擎三视图生成服务"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks"
        # 使用 Seedream 图像生成模型
        self.model = "doubao-seedream-5-0-lite-260128"
    
    def _get_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    async def generate_three_views(self, image_path: str, output_dir: str = None) -> dict:
        """
        从单张图片生成三视图（正面/侧面/背面）
        
        Args:
            image_path: 原始图片路径
            output_dir: 输出目录
        
        Returns:
            dict: {
                "front": "正面图路径",
                "side": "侧面图路径",
                "back": "背面图路径"
            }
        """
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        if not output_dir:
            output_dir = "/tmp/three_views"
        
        os.makedirs(output_dir, exist_ok=True)
        
        results = {}
        
        # 生成三个角度的图片
        views = [
            ("front", "人物正面肖像照片，正面视角，保持原始风格和服装"),
            ("side", "人物侧面肖像照片，侧面视角，90度侧脸，保持原始风格和服装"),
            ("back", "人物背影照片，背面视角，保持原始风格和服装")
        ]
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            for view_name, prompt in views:
                print(f"生成 {view_name} 视图...")
                
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
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
                
                try:
                    response = await client.post(
                        self.base_url,
                        headers=self._get_headers(),
                        json=data
                    )
                    result = response.json()
                    print(f"{view_name} 响应: {result}")
                    
                    if "id" in result:
                        task_id = result["id"]
                        image_url = await self._wait_for_image(task_id, client)
                        
                        if image_url:
                            output_path = os.path.join(output_dir, f"{view_name}_{uuid.uuid4()}.jpg")
                            img_response = await client.get(image_url)
                            with open(output_path, "wb") as f:
                                f.write(img_response.content)
                            results[view_name] = output_path
                            print(f"{view_name} 已保存: {output_path}")
                except Exception as e:
                    print(f"生成 {view_name} 失败: {e}")
        
        return results
    
    async def _wait_for_image(self, task_id: str, client: httpx.AsyncClient, max_wait: int = 60) -> str:
        """等待图像生成完成"""
        for _ in range(max_wait // 5):
            await asyncio.sleep(5)
            
            response = await client.get(
                f"{self.base_url}/{task_id}",
                headers=self._get_headers()
            )
            result = response.json()
            status = result.get("status")
            
            print(f"任务状态: {status}")
            
            if status == "succeeded":
                # 获取图片 URL
                content = result.get("content", {})
                if isinstance(content, dict):
                    return content.get("image_url") or content.get("url")
                elif isinstance(content, list) and len(content) > 0:
                    return content[0].get("image_url") or content[0].get("url")
            elif status == "failed":
                print(f"生成失败: {result}")
                return None
        
        return None


# 全局实例
three_view_service = None

def init_three_view_service(api_key: str):
    global three_view_service
    three_view_service = ThreeViewService(api_key)