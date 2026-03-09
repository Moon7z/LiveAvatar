from sqlalchemy import Column, String, DateTime, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./liveavatar.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AvatarModel(Base):
    """形象表"""
    __tablename__ = "avatars"
    
    avatar_id = Column(String, primary_key=True, index=True)
    name = Column(String)
    image_url = Column(String)
    created_at = Column(DateTime)


class AudioModel(Base):
    """音频表"""
    __tablename__ = "audios"
    
    audio_id = Column(String, primary_key=True, index=True)
    text = Column(String)
    voice_type = Column(String)
    audio_url = Column(String)
    duration = Column(Integer)
    created_at = Column(DateTime)


class VideoModel(Base):
    """视频表"""
    __tablename__ = "videos"
    
    task_id = Column(String, primary_key=True, index=True)
    avatar_id = Column(String)
    audio_id = Column(String)
    status = Column(String)
    progress = Column(Integer, default=0)
    video_url = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)
    error = Column(String, nullable=True)
    created_at = Column(DateTime)


class LiveModel(Base):
    """直播表"""
    __tablename__ = "lives"
    
    live_id = Column(String, primary_key=True, index=True)
    video_id = Column(String)
    platform = Column(String)
    stream_url = Column(String)
    stream_key = Column(String)
    status = Column(String)
    started_at = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)


def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()