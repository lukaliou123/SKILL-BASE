#!/bin/bash
# grab_frame.sh - 抓取摄像头单帧
#
# 内置两个固定处理步骤（不可跳过）：
#   1. 旋转 180°（摄像头倒立安装）
#   2. 压缩到 800px / Q40（降低视觉API传输时间）
#
# 用法：
#   bash grab_frame.sh [输出路径]
#   bash grab_frame.sh /tmp/cam.jpg
#
# 输出：压缩后的 JPEG，约 20-50KB

export PATH="/opt/homebrew/bin:/usr/sbin:/usr/bin:/bin:/sbin:$PATH"

RTSP_URL="rtsp://admin:YOUR_PASSWORD@YOUR_CAMERA_IP:554/stream1"
OUTPUT="${1:-/tmp/cam_frame.jpg}"
TMP_RAW="/tmp/cam_raw_$$.jpg"

# Step 1: 抓帧 + 旋转180°
/opt/homebrew/bin/ffmpeg \
  -loglevel error \
  -rtsp_transport tcp \
  -i "$RTSP_URL" \
  -frames:v 1 \
  -vf "hflip,vflip" \
  -update 1 \
  "$TMP_RAW" -y

# Step 2: 压缩到 800px Q40
sips -Z 800 -s format jpeg -s formatOptions 40 "$TMP_RAW" --out "$OUTPUT" > /dev/null 2>&1

rm -f "$TMP_RAW"
echo "$OUTPUT"
