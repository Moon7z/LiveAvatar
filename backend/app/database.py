from sqlalchemy import Column, String, DateTime, Integer, create_engine, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import json

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
    # 三视图 JSON 存储: {"front": "path", "side": "path", "back": "path"}
    three_views = Column(Text, nullable=True)
    # 用户选择的视角: front, side, back（默认 front）
    selected_view = Column(String, default="front")
    
    def get_three_views(self):
        """获取三视图字典"""
        if self.three_views:
            try:
                return json.loads(self.three_views)
            except:
                return None
        return None
    
    def set_three_views(self, views_dict):
        """设置三视图"""
        self.three_views = json.dumps(views_dict)
    
    def get_selected_image_url(self):
        """获取用户选择的视角图片URL"""
        three_views = self.get_three_views()
        if three_views and self.selected_view:
            return three_views.get(self.selected_view)
        return self.image_url


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