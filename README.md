# LiveAvatar - 数字人直播一键生成器

## 项目简介

一张图片 + 一段文字 → 自动生成数字人直播视频

## 快速开始

### 启动服务

```bash
export PATH="$HOME/miniconda3/bin:$PATH"
source activate liveavatar
cd backend
python run.py
```

### 访问地址

- **前端 UI**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## 功能模块

### 1. 形象管理
- 上传人物图片
- 自动生成三视图（正面/侧面/背面）
- 选择视角生成视频

### 2. 语音合成
- 文本转语音
- 8种音色可选
- 支持语速调节

### 3. 视频生成（标准化配置）
- ✅ 固定镜头，禁止镜头移动
- ✅ 保持人物原始比例
- ✅ 人物位置不变
- ✅ FFmpeg 后处理确保比例正确

### 4. 直播控制
- 开始/停止直播
- 支持多平台推流

---

## 📋 数字人生成标准

### 必须遵守的标准

| 项目 | 标准 |
|------|------|
| **镜头** | 固定不动，禁止推进/拉远 |
| **人物比例** | 保持原图比例，不变形 |
| **人物位置** | 居中不变 |
| **后处理** | FFmpeg 确保比例正确 |

### 提示词模板

```
固定摄像机位置，绝对禁止镜头往前推进或往后拉远，
禁止任何形式的镜头移动，人物位置保持不变，
保持原始人物比例不变形，表情生动自然
```

### FFmpeg 后处理命令

```bash
ffmpeg -y -i input.mp4 \
  -vf "scale=940:1280:force_original_aspect_ratio=decrease,pad=940:1280:(ow-iw)/2:(oh-ih)/2:black" \
  -c:a copy \
  output.mp4
```

---

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/avatar/upload | POST | 上传形象图片（自动生成三视图） |
| /api/avatar/list | GET | 获取形象列表 |
| /api/avatar/{id}/views | GET | 获取三视图 |
| /api/avatar/{id}/select-view | POST | 选择视角 |
| /api/tts/synthesize | POST | 语音合成 |
| /api/tts/voices | GET | 获取音色列表 |
| /api/video/generate | POST | 生成视频（标准化配置） |
| /api/video/status/{id} | GET | 查询视频状态 |
| /api/live/start | POST | 开始直播 |
| /api/live/stop/{id} | POST | 停止直播 |

---

## 技术栈

- **后端**: Python 3.10 + FastAPI + SQLAlchemy
- **前端**: Vue 3 + Tailwind CSS
- **语音**: 火山引擎 TTS / gTTS
- **视频**: 火山引擎 Seedance + FFmpeg
- **三视图**: 火山引擎 Seedream

---

## 火山引擎配置

### API Key 配置

```bash
cp backend/.env.example backend/.env
# 编辑 .env 填入 API Key
```

### 需要开通的服务

| 服务 | 说明 |
|------|------|
| Seedance | 视频生成 |
| Seedream | 图像生成（三视图） |
| TTS | 语音合成 |

---

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
├── docker-compose.yml
├── start.sh
└── README.md
```

---

## Docker 部署

```bash
docker-compose up -d
```

---

## 许可证

MIT License