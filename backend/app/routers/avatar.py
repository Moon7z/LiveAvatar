import uuid
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import asyncio
import json

from app.models.schemas import Response
from app.utils.file_utils import file_utils
from app.database import get_db, AvatarModel
from app.config import settings

router = APIRouter(prefix="/api/avatar", tags=["形象管理"])


async def generate_three_views_task(avatar_id: str, image_path: str, output_dir: str):
    """后台任务：生成三视图"""
    from sqlalchemy.orm import sessionmaker
    from app.database import engine
    from app.services.three_view_service import ThreeViewService
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print(f"开始生成三视图: {avatar_id}")
        
        # 生成三视图
        service = ThreeViewService(settings.VOLCENGINE_API_KEY)
        results = await service.generate_three_views(image_path, output_dir)
        
        print(f"三视图生成结果: {results}")
        
        # 更新数据库
        avatar = db.query(AvatarModel).filter(AvatarModel.avatar_id == avatar_id).first()
        if avatar and results:
            avatar.set_three_views(results)
            db.commit()
            print(f"三视图已保存到数据库")
            
    except Exception as e:
        print(f"三视图生成失败: {e}")
    finally:
        db.close()


@router.post("/upload", response_model=Response)
async def upload_avatar(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    generate_views: bool = Form(True),
    db: Session = Depends(get_db)
):
    """
    上传形象图片
    
    - 支持 JPG/PNG 格式
    - generate_views: 是否自动生成三视图（正面/侧面/背面）
    """
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="只支持 JPG/PNG 格式图片")
    
    try:
        # 保存文件
        avatar_id, file_path, image_url = await file_utils.save_upload(file, "avatars")
        
        # 创建输出目录
        output_dir = os.path.join(settings.OUTPUT_DIR, "three_views", avatar_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # 存储记录
        avatar = AvatarModel(
            avatar_id=avatar_id,
            name=name or f"形象_{avatar_id[:8]}",
            image_url=image_url,
            created_at=datetime.now()
        )
        db.add(avatar)
        db.commit()
        db.refresh(avatar)
        
        response_data = {
            "avatar_id": avatar.avatar_id,
            "name": avatar.name,
            "image_url": avatar.image_url,
            "created_at": avatar.created_at.isoformat(),
            "three_views_status": "pending" if generate_views else "skipped"
        }
        
        # 如果需要生成三视图
        if generate_views:
            asyncio.create_task(generate_three_views_task(avatar_id, file_path, output_dir))
        
        return Response(data=response_data)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {e}")


@router.get("/list", response_model=Response)
async def list_avatars(db: Session = Depends(get_db)):
    """获取形象列表"""
    avatars = db.query(AvatarModel).order_by(AvatarModel.created_at.desc()).all()
    
    result = []
    for a in avatars:
        item = {
            "avatar_id": a.avatar_id,
            "name": a.name,
            "image_url": a.image_url,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "has_three_views": bool(a.get_three_views())
        }
        result.append(item)
    
    return Response(data={"avatars": result, "total": len(result)})


@router.get("/{avatar_id}", response_model=Response)
async def get_avatar(avatar_id: str, db: Session = Depends(get_db)):
    """获取单个形象详情"""
    avatar = db.query(AvatarModel).filter(AvatarModel.avatar_id == avatar_id).first()
    if not avatar:
        raise HTTPException(status_code=404, detail="形象不存在")
    
    data = {
        "avatar_id": avatar.avatar_id,
        "name": avatar.name,
        "image_url": avatar.image_url,
        "created_at": avatar.created_at.isoformat() if avatar.created_at else None
    }
    
    # 获取三视图
    three_views = avatar.get_three_views()
    if three_views:
        data["three_views"] = three_views
        data["has_three_views"] = True
    else:
        data["has_three_views"] = False
    
    return Response(data=data)


@router.get("/{avatar_id}/views", response_model=Response)
async def get_avatar_views(avatar_id: str, db: Session = Depends(get_db)):
    """获取形象的三视图"""
    avatar = db.query(AvatarModel).filter(AvatarModel.avatar_id == avatar_id).first()
    if not avatar:
        raise HTTPException(status_code=404, detail="形象不存在")
    
    three_views = avatar.get_three_views()
    
    if not three_views:
        return Response(data={
            "status": "not_generated",
            "message": "三视图未生成，请稍后再试或重新上传"
        })
    
    return Response(data={
        "status": "generated",
        "avatar_id": avatar_id,
        "views": {
            "front": {"url": three_views.get("front"), "label": "正面"},
            "side": {"url": three_views.get("side"), "label": "侧面"},
            "back": {"url": three_views.get("back"), "label": "背面"}
        }
    })


@router.post("/{avatar_id}/select-view", response_model=Response)
async def select_avatar_view(
    avatar_id: str,
    view_type: str = Form(...),  # front, side, back
    db: Session = Depends(get_db)
):
    """
    选择用于生成视频的视角
    
    - view_type: front（正面）, side（侧面）, back（背面）
    """
    if view_type not in ["front", "side", "back"]:
        raise HTTPException(status_code=400, detail="view_type 必须是 front, side 或 back")
    
    avatar = db.query(AvatarModel).filter(AvatarModel.avatar_id == avatar_id).first()
    if not avatar:
        raise HTTPException(status_code=404, detail="形象不存在")
    
    three_views = avatar.get_three_views()
    if not three_views or not three_views.get(view_type):
        raise HTTPException(status_code=400, detail=f"{view_type} 视角尚未生成")
    
    # 更新选中的视角
    avatar.selected_view = view_type
    db.commit()
    
    return Response(data={
        "avatar_id": avatar_id,
        "selected_view": view_type,
        "image_url": three_views.get(view_type)
    })


@router.delete("/{avatar_id}", response_model=Response)
async def delete_avatar(avatar_id: str, db: Session = Depends(get_db)):
    """删除形象"""
    avatar = db.query(AvatarModel).filter(AvatarModel.avatar_id == avatar_id).first()
    if not avatar:
        raise HTTPException(status_code=404, detail="形象不存在")
    
    # 删除主文件
    file_path = file_utils.get_file_path(avatar.image_url)
    file_utils.delete_file(file_path)
    
    # 删除三视图
    three_views = avatar.get_three_views()
    if three_views:
        for view_path in three_views.values():
            if view_path and os.path.exists(view_path):
                os.remove(view_path)
    
    # 删除数据库记录
    db.delete(avatar)
    db.commit()
    
    return Response(message="删除成功")