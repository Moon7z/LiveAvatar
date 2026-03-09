import uuid
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.models.schemas import Response, TTSSynthesize, TTSResponse
from app.services.volcengine_tts import volcengine_tts_service
from app.database import get_db, AudioModel
from app.config import settings

router = APIRouter(prefix="/api/tts", tags=["语音合成"])

# 音色列表
VOICES = [
    {"voice_id": "BV001_streaming", "name": "通用女声", "gender": "female", "language": "zh-CN"},
    {"voice_id": "BV002_streaming", "name": "通用男声", "gender": "male", "language": "zh-CN"},
    {"voice_id": "zh_female_tianmei", "name": "甜美女声", "gender": "female", "language": "zh-CN"},
    {"voice_id": "zh_male_chunhou", "name": "醇厚男声", "gender": "male", "language": "zh-CN"},
    {"voice_id": "zh_female_wanwan", "name": "温婉女声", "gender": "female", "language": "zh-CN"},
    {"voice_id": "zh_male_hunhou", "name": "浑厚男声", "gender": "male", "language": "zh-CN"},
    {"voice_id": "zh_female_xiaomei", "name": "小美女声", "gender": "female", "language": "zh-CN"},
    {"voice_id": "zh_male_xiaoyu", "name": "小宇男声", "gender": "male", "language": "zh-CN"},
]


@router.post("/synthesize", response_model=Response)
async def synthesize_speech(request: TTSSynthesize, db: Session = Depends(get_db)):
    """
    文本转语音
    
    - text: 要合成的文本
    - voice_type: 音色ID
    - speed: 语速 0.5-2.0
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="文本不能为空")
    
    if len(request.text) > 5000:
        raise HTTPException(status_code=400, detail="文本长度不能超过 5000 字符")
    
    try:
        # 生成音频文件
        output_dir = os.path.join(settings.OUTPUT_DIR, "audio")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{uuid.uuid4()}.mp3")
        
        # 尝试火山引擎 TTS
        try:
            from app.services.volcengine_tts import VolcengineTTSService
            tts = VolcengineTTSService(settings.VOLCENGINE_API_KEY)
            result = await tts.synthesize(
                text=request.text,
                voice_type=request.voice_type,
                speed=request.speed,
                output_path=output_path
            )
        except Exception as e:
            # 火山引擎失败，使用 gTTS
            print(f"火山引擎 TTS 失败: {e}, 使用 gTTS 备用")
            from gtts import gTTS
            tts = gTTS(text=request.text, lang='zh-CN')
            tts.save(output_path)
            result = {
                "audio_path": output_path,
                "duration": len(request.text) / 4.0
            }
        
        audio_id = os.path.basename(output_path).replace(".mp3", "")
        audio_url = f"/outputs/audio/{audio_id}.mp3"
        
        # 保存到数据库
        audio = AudioModel(
            audio_id=audio_id,
            text=request.text,
            voice_type=request.voice_type,
            audio_url=audio_url,
            duration=int(result.get("duration", len(request.text) / 4)),
            created_at=datetime.now()
        )
        db.add(audio)
        db.commit()
        
        return Response(data={
            "audio_id": audio_id,
            "audio_url": audio_url,
            "duration": result.get("duration", len(request.text) / 4)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音合成失败: {e}")


@router.get("/voices", response_model=Response)
async def get_voices():
    """获取可用音色列表"""
    return Response(data={"voices": VOICES})


@router.get("/list", response_model=Response)
async def list_audios(db: Session = Depends(get_db)):
    """获取音频列表"""
    audios = db.query(AudioModel).order_by(AudioModel.created_at.desc()).limit(50).all()
    
    result = [{
        "audio_id": a.audio_id,
        "text": a.text[:50] + "..." if len(a.text) > 50 else a.text,
        "voice_type": a.voice_type,
        "audio_url": a.audio_url,
        "duration": a.duration,
        "created_at": a.created_at.isoformat() if a.created_at else None
    } for a in audios]
    
    return Response(data={"audios": result, "total": len(result)})