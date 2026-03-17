---
name: tplink-ipc-camera
description: "TP-Link IPC 摄像头抓帧 + 云台控制。抓帧用 ffmpeg RTSP，PTZ 用 ONVIF。2026-03-16 实测验证通过。"
metadata: { "openclaw": { "emoji": "📷", "requires": { "bins": ["ffmpeg", "python3"] } } }
---

# TP-Link IPC 摄像头控制

| 项目 | 值 |
|---|---|
| IP | 172.16.200.9（原 172.16.201.18，2026-03-17 变更）|
| 账号 | admin / LongLiveTheMech1! |
| RTSP | 554 端口，stream1=4K，stream2=640×360 |
| ONVIF | 2020 端口 |

## ⚠️ 重要：摄像头倒立安装

**摄像头倒立安装，所有抓帧必须旋转180°（hflip,vflip），否则方位判断完全反转！**

## 抓帧（标准方式）

**永远用封装脚本，不要手写 ffmpeg 命令：**

```bash
# 标准抓帧（自动旋转180°，输出到指定路径）
bash /Users/mechforge1/.openclaw/workspace/skills/tplink-ipc-camera/scripts/grab_frame.sh /tmp/cam.jpg
```

脚本内置旋转，无需手动添加 `-vf "hflip,vflip"`。

<details>
<summary>底层 ffmpeg 命令（仅供参考，不要直接用）</summary>

```bash
export PATH="/opt/homebrew/bin:/usr/sbin:/usr/bin:/bin:/sbin:$PATH"
/opt/homebrew/bin/ffmpeg -loglevel error -rtsp_transport tcp \
  -i "rtsp://admin:LongLiveTheMech1!@172.16.200.9:554/stream1" \
  -frames:v 1 -vf "hflip,vflip" -update 1 /tmp/cam.jpg -y
```
</details>

## 云台控制

脚本：`~/midscene-agent/ptz_onvif.py`（依赖 `onvif-zeep`）

```bash
export PATH="/opt/homebrew/bin:/usr/sbin:/usr/bin:/bin:/sbin:$PATH"

/opt/homebrew/bin/python3 ~/midscene-agent/ptz_onvif.py left            # 左转
/opt/homebrew/bin/python3 ~/midscene-agent/ptz_onvif.py right           # 右转
/opt/homebrew/bin/python3 ~/midscene-agent/ptz_onvif.py up              # 上
/opt/homebrew/bin/python3 ~/midscene-agent/ptz_onvif.py down            # 下
/opt/homebrew/bin/python3 ~/midscene-agent/ptz_onvif.py right 0.8 1.5  # 速度0.8 持续1.5s
```

## 抓帧 + 转动 + 再抓帧

```bash
export PATH="/opt/homebrew/bin:/usr/sbin:/usr/bin:/bin:/sbin:$PATH"

# 1. 拍
bash /Users/mechforge1/.openclaw/workspace/skills/tplink-ipc-camera/scripts/grab_frame.sh /tmp/before.jpg

# 2. 转
/opt/homebrew/bin/python3 ~/midscene-agent/ptz_onvif.py right 0.5 1.5
sleep 1

# 3. 再拍
bash /Users/mechforge1/.openclaw/workspace/skills/tplink-ipc-camera/scripts/grab_frame.sh /tmp/after.jpg
```

## 视觉分析

```bash
# AI 分析（Gemini，适合内容理解）
/opt/homebrew/bin/python3 /Users/mechforge1/.openclaw/workspace/skills/tplink-ipc-camera/scripts/analyze_frame.py /tmp/cam.jpg "提示词"

# OpenCV 分析（适合机器人导航，快速精准）
# ⚠️ 导航时不要用 grab_frame.sh 的压缩版，用 4K 原图：
export PATH="/opt/homebrew/bin:/usr/sbin:/usr/bin:/bin:/sbin:$PATH"
/opt/homebrew/bin/ffmpeg -loglevel error -rtsp_transport tcp \
  -i "rtsp://admin:LongLiveTheMech1!@172.16.200.9:554/stream1" \
  -frames:v 1 -vf "hflip,vflip" -update 1 /tmp/cam_4k.jpg -y
```

## 视觉分析

```bash
# 用 Gemini 分析帧内容（导航、识别等）
/opt/homebrew/bin/python3 \
  /Users/mechforge1/.openclaw/workspace/skills/tplink-ipc-camera/scripts/analyze_frame.py \
  /tmp/cam.jpg "提示词"
```

⚠️ **导航时不要压缩图片**：grab_frame.sh 的 sips 压缩适合 AI API 省钱，但 OpenCV 本地处理请用 4K 原图：
```bash
export PATH="/opt/homebrew/bin:/usr/sbin:/usr/bin:/bin:/sbin:$PATH"
/opt/homebrew/bin/ffmpeg -loglevel error -rtsp_transport tcp \
  -i "rtsp://admin:LongLiveTheMech1!@172.16.200.9:554/stream1" \
  -frames:v 1 -vf "hflip,vflip" -update 1 /tmp/cam_4k.jpg -y
```

## 踩过的坑

- **不要用 HTTP 私有 API 控 PTZ** — 认证极复杂（RSA+XOR+MD5），5次失败锁30分钟，用 ONVIF 秒解决
- `-loglevel error` 必须在 `-i` 前面
- 必须用 `/opt/homebrew/bin/python3`，系统 python3 缺库
- stream2 画质太差，AI 分析请用 stream1
