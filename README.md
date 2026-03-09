# LiveAvatar - 数字人直播一键生成器

## 项目简介

一张图片 + 一段文字 → 自动生成数字人直播视频

## 快速开始

### 启动服务

```bash
cd /home/admin/.openclaw/workspace/projects/LiveAvatar
./start.sh
```

或手动启动：

```bash
export PATH="$HOME/miniconda3/bin:$PATH"
source activate liveavatar
cd backend
python run.py
```

### 访问地址

- **前端 UI**: http://47.96.117.215:8000
- **API 文档**: http://47.96.117.215:8000/docs

## 功能模块

### 1. 形象管理
- 上传人物图片
- 支持JPG/PNG格式
- 形象列表管理

### 2. 语音合成
- 文本转语音
- 4种音色可选
- 支持语速调节

### 3. 视频生成
- 图片+音频合成视频
- 支持竖屏/横屏
- 后台任务处理

### 4. 直播控制
- 开始/停止直播
- 支持多平台推流

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/avatar/upload | POST | 上传形象图片 |
| /api/avatar/list | GET | 获取形象列表 |
| /api/tts/synthesize | POST | 语音合成 |
| /api/tts/voices | GET | 获取音色列表 |
| /api/video/generate | POST | 生成视频 |
| /api/video/status/{id} | GET | 查询视频状态 |
| /api/live/start | POST | 开始直播 |
| /api/live/stop/{id} | POST | 停止直播 |

## 技术栈

- **后端**: Python 3.10 + FastAPI + SQLAlchemy
- **前端**: Vue 3 + Tailwind CSS
- **语音**: 火山引擎 TTS / gTTS
- **视频**: FFmpeg

## 注意事项

1. 火山引擎 TTS 需要配置正确的 API Key
2. 视频生成使用 FFmpeg Mock 模式
3. SadTalker 真实集成需要 GPU 服务器

## 项目结构

```
LiveAvatar/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI 入口
│   │   ├── config.py        # 配置管理
│   │   ├── database.py      # 数据库模型
│   │   ├── routers/         # API 路由
│   │   ├── services/        # 业务服务
│   │   └── models/          # 数据模型
│   ├── uploads/             # 上传文件
│   ├── outputs/             # 生成文件
│   └── requirements.txt
├── frontend/
│   └── index.html           # 前端页面
├── start.sh                 # 启动脚本
└── README.md
```