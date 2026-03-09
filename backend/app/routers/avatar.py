import uuid
import os
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
from sqlalchemy.orm import Session

from app.models.schemas import Response, Avatar, AvatarListResponse
from app.utils.file_utils import file_utils
from app.database import get_db, AvatarModel, init_db

router = APIRouter(prefix="/api/avatar", tags=["形象管理"])


@router.post("/upload", response_model=Response)
async def upload_avatar(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    上传形象图片
    
    - 支持 JPG/PNG 格式
    - 建议使用正面清晰照片
    """
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="只支持 JPG/PNG 格式图片")
    
    try:
        avatar_id, file_path, image_url = await file_utils.save_upload(file, "avatars")
        
        avatar = AvatarModel(
            avatar_id=avatar_id,
            name=name or f"形象_{avatar_id[:8]}",
            image_url=image_url,
            created_at=datetime.now()
        )
        db.add(avatar)
        db.commit()
        db.refresh(avatar)
        
        return Response(data={
            "avatar_id": avatar.avatar_id,
            "name": avatar.name,
            "image_url": avatar.image_url,
            "created_at": avatar.created_at.isoformat()
        })
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"上传失败: {e}")


@router.get("/list", response_model=Response)
async def list_avatars(db: Session = Depends(get_db)):
    """获取形象列表"""
    avatars = db.query(AvatarModel).order_by(AvatarModel.created_at.desc()).all()
    
    result = [{
        "avatar_id": a.avatar_id,
        "name": a.name,
        "image_url": a.image_url,
        "created_at": a.created_at.isoformat() if a.created_at else None
    } for a in avatars]
    
    return Response(data={"avatars": result, "total": len(result)})


@router.get("/{avatar_id}", response_model=Response)
async def get_avatar(avatar_id: str, db: Session = Depends(get_db)):
    """获取单个形象"""
    avatar = db.query(AvatarModel).filter(AvatarModel.avatar_id == avatar_id).first()
    if not avatar:
        raise HTTPException(status_code=404, detail="形象不存在")
    
    return Response(data={
        "avatar_id": avatar.avatar_id,
        "name": avatar.name,
        "image_url": avatar.image_url,
        "created_at": avatar.created_at.isoformat() if avatar.created_at else None
    })


@router.delete("/{avatar_id}", response_model=Response)
async def delete_avatar(avatar_id: str, db: Session = Depends(get_db)):
    """删除形象"""
    avatar = db.query(AvatarModel).filter(AvatarModel.avatar_id == avatar_id).first()
    if not avatar:
        raise HTTPException(status_code=404, detail="形象不存在")
    
    # 删除文件
    file_path = file_utils.get_file_path(avatar.image_url)
    file_utils.delete_file(file_path)
    
    # 删除数据库记录
    db.delete(avatar)
    db.commit()
    
    return Response(message="删除成功")