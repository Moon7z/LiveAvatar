import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.models.schemas import Response, LiveStart, LiveStatus
from app.database import get_db, LiveModel, VideoModel

router = APIRouter(prefix="/api/live", tags=["直播控制"])


@router.post("/start", response_model=Response)
async def start_live(request: LiveStart, db: Session = Depends(get_db)):
    """
    开始直播
    
    - video_id: 视频ID
    - platform: 平台 (douyin/bilibili/wechat)
    - stream_url: 推流地址
    - stream_key: 推流密钥
    """
    # 检查视频
    video = db.query(VideoModel).filter(VideoModel.task_id == request.video_id).first()
    if not video or video.status != "completed":
        raise HTTPException(status_code=400, detail="视频不存在或未完成")
    
    live_id = str(uuid.uuid4())
    
    live = LiveModel(
        live_id=live_id,
        video_id=request.video_id,
        platform=request.platform,
        stream_url=request.stream_url,
        stream_key=request.stream_key,
        status="streaming",
        started_at=datetime.now()
    )
    db.add(live)
    db.commit()
    
    # TODO: 启动 FFmpeg 推流进程
    # ffmpeg -re -i video.mp4 -c copy -f flv rtmp://xxx/key
    
    return Response(data={
        "live_id": live_id,
        "status": "streaming",
        "started_at": live.started_at.isoformat(),
        "message": "直播已启动（模拟模式，需配置 FFmpeg 推流）"
    })


@router.post("/stop/{live_id}", response_model=Response)
async def stop_live(live_id: str, db: Session = Depends(get_db)):
    """停止直播"""
    live = db.query(LiveModel).filter(LiveModel.live_id == live_id).first()
    if not live:
        raise HTTPException(status_code=404, detail="直播不存在")
    
    live.status = "stopped"
    if live.started_at:
        live.duration = int((datetime.now() - live.started_at).total_seconds())
    db.commit()
    
    return Response(message="直播已停止")


@router.get("/status/{live_id}", response_model=Response)
async def get_live_status(live_id: str, db: Session = Depends(get_db)):
    """查询直播状态"""
    live = db.query(LiveModel).filter(LiveModel.live_id == live_id).first()
    if not live:
        raise HTTPException(status_code=404, detail="直播不存在")
    
    duration = live.duration
    if live.status == "streaming" and live.started_at:
        duration = int((datetime.now() - live.started_at).total_seconds())
    
    return Response(data={
        "live_id": live.live_id,
        "video_id": live.video_id,
        "platform": live.platform,
        "status": live.status,
        "started_at": live.started_at.isoformat() if live.started_at else None,
        "duration": duration
    })


@router.get("/list", response_model=Response)
async def list_lives(db: Session = Depends(get_db)):
    """获取直播列表"""
    lives = db.query(LiveModel).order_by(LiveModel.started_at.desc()).limit(50).all()
    
    result = [{
        "live_id": l.live_id,
        "video_id": l.video_id,
        "platform": l.platform,
        "status": l.status,
        "started_at": l.started_at.isoformat() if l.started_at else None,
        "duration": l.duration
    } for l in lives]
    
    return Response(data={"lives": result, "total": len(result)})