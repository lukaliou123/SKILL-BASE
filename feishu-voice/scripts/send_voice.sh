#!/bin/bash
# Feishu Voice Skill - 发送飞书语音条
# 用法：bash send_voice.sh -t "文字内容"

set -e

# 自动加载同级 skill 目录的 config.env（如果存在）
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
if [[ -f "${SKILL_DIR}/config.env" ]]; then
  # shellcheck disable=SC1090
  source "${SKILL_DIR}/config.env"
fi

# 默认配置
SPEED="1.0"
EMOTION="neutral"
NO_SEND=false
OUTPUT_FILE=""
TEXT=""
TEXT_FILE=""

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印帮助
print_help() {
    cat << EOF
🎤 Feishu Voice Skill - 发送飞书语音条

用法：bash $0 [选项]

选项:
  -t, --text <text>       要转换的文字（必需，除非使用 -f）
  -f, --file <file>       文字文件路径
  -o, --output <file>     输出音频文件路径
  --chat-id <id>          飞书聊天 ID（覆盖环境变量）
  --app-id <id>           飞书 App ID（覆盖环境变量）
  --app-secret <secret>   飞书 App Secret（覆盖环境变量）
  --speed <1.0>           语速（0.5-2.0，默认 1.0）
  --emotion <neutral>     情感（happy/sad/angry/neutral）
  --no-send               只生成音频，不发送
  -h, --help              显示帮助信息

示例:
  bash $0 -t "主人晚上好～"
  bash $0 -f message.txt --speed 0.9
  bash $0 -t "你好" --no-send -o /tmp/voice.opus

EOF
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--text)
            TEXT="$2"
            shift 2
            ;;
        -f|--file)
            TEXT_FILE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --chat-id)
            FEISHU_CHAT_ID="$2"
            shift 2
            ;;
        --app-id)
            FEISHU_APP_ID="$2"
            shift 2
            ;;
        --app-secret)
            FEISHU_APP_SECRET="$2"
            shift 2
            ;;
        --speed)
            SPEED="$2"
            shift 2
            ;;
        --emotion)
            EMOTION="$2"
            shift 2
            ;;
        --no-send)
            NO_SEND=true
            shift
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            echo -e "${RED}❌ 未知选项：$1${NC}"
            print_help
            exit 1
            ;;
    esac
done

# 检查必需参数
if [ -z "$TEXT" ] && [ -z "$TEXT_FILE" ]; then
    echo -e "${RED}❌ 错误：必须提供 -t 文字或 -f 文件${NC}"
    print_help
    exit 1
fi

# 从文件读取文字
if [ -n "$TEXT_FILE" ]; then
    if [ ! -f "$TEXT_FILE" ]; then
        echo -e "${RED}❌ 错误：文件不存在：$TEXT_FILE${NC}"
        exit 1
    fi
    TEXT=$(cat "$TEXT_FILE")
fi

# 检查环境变量
if [ -z "$FEISHU_APP_ID" ] || [ -z "$FEISHU_APP_SECRET" ] || [ -z "$FEISHU_CHAT_ID" ]; then
    echo -e "${RED}❌ 错误：缺少 Feishu 配置${NC}"
    echo "请设置以下环境变量："
    echo "  export FEISHU_APP_ID=\"cli_xxx\""
    echo "  export FEISHU_APP_SECRET=\"xxx\""
    echo "  export FEISHU_CHAT_ID=\"oc_xxx\""
    exit 1
fi

if [ -z "$NOIZ_API_KEY" ]; then
    echo -e "${RED}❌ 错误：缺少 NoizAI API Key${NC}"
    echo "请设置：export NOIZ_API_KEY=\"your_key\""
    exit 1
fi

echo -e "${BLUE}🎤 开始生成语音...${NC}"

# 生成临时文件
TEMP_DIR=$(mktemp -d)
TEMP_OPUS="$TEMP_DIR/voice.opus"

# 定位 noiz_tts.py（优先找已安装的 tts skill）
NOIZ_TTS_PY=""
SEARCH_PATHS=(
    "$(dirname "$0")/../../.agents/skills/tts/scripts/noiz_tts.py"
    "$HOME/.openclaw/workspace/.agents/skills/tts/scripts/noiz_tts.py"
)
for p in "${SEARCH_PATHS[@]}"; do
    if [ -f "$p" ]; then
        NOIZ_TTS_PY="$(realpath "$p")"
        break
    fi
done

if [ -z "$NOIZ_TTS_PY" ]; then
    echo -e "${RED}❌ 错误：未找到 noiz_tts.py，请先安装 tts skill：${NC}"
    echo "  npx skills add https://github.com/noizai/skills --skill tts --yes"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# 构建 TTS 参数
TTS_ARGS=(
    --text "$TEXT"
    --api-key "$NOIZ_API_KEY"
    --output-format opus
    --output "$TEMP_OPUS"
    --speed "$SPEED"
)

# 音色：优先使用 VOICE_ID 环境变量，否则使用默认音色（婉青｜情绪抚慰 77e15f2c）
VOICE_ID="${NOIZ_VOICE_ID:-77e15f2c}"
TTS_ARGS+=(--voice-id "$VOICE_ID")

# 情感映射（将 happy/sad/angry/neutral 转为 Noiz emo 格式）
case "$EMOTION" in
    happy)  TTS_ARGS+=(--emo '{"Joy":0.7}') ;;
    sad)    TTS_ARGS+=(--emo '{"Sadness":0.7}') ;;
    angry)  TTS_ARGS+=(--emo '{"Anger":0.7}') ;;
    neutral) ;;  # 不传 emo，使用默认
esac

echo -e "${YELLOW}  音色: $VOICE_ID | 语速: $SPEED | 情感: $EMOTION${NC}"

python3 "$NOIZ_TTS_PY" "${TTS_ARGS[@]}"
TTS_EXIT=$?

if [ $TTS_EXIT -ne 0 ] || [ ! -f "$TEMP_OPUS" ] || [ ! -s "$TEMP_OPUS" ]; then
    echo -e "${RED}❌ 错误：语音生成失败${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo -e "${GREEN}✅ 语音生成成功（OPUS）${NC}"

# 保存输出文件（如果指定）
if [ -n "$OUTPUT_FILE" ]; then
    cp "$TEMP_OPUS" "$OUTPUT_FILE"
    echo -e "${GREEN}✅ 已保存到：$OUTPUT_FILE${NC}"
fi

# 只生成不发送
if [ "$NO_SEND" = true ]; then
    rm -rf "$TEMP_DIR"
    echo -e "${GREEN}✅ 完成（未发送）${NC}"
    exit 0
fi

echo -e "${BLUE}📤 上传到飞书...${NC}"

# 获取 Token
TOKEN=$(curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d "{\"app_id\":\"$FEISHU_APP_ID\",\"app_secret\":\"$FEISHU_APP_SECRET\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('tenant_access_token',''))")

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ 错误：获取 Token 失败${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# 上传文件
UPLOAD_RESULT=$(curl -s -X POST "https://open.feishu.cn/open-apis/im/v1/files" \
  -H "Authorization: Bearer $TOKEN" \
  -F "type=audio" \
  -F "file=@$TEMP_OPUS" \
  -F "file_type=opus")

FILE_KEY=$(echo "$UPLOAD_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('file_key',''))")

if [ -z "$FILE_KEY" ]; then
    echo -e "${RED}❌ 错误：文件上传失败${NC}"
    echo "$UPLOAD_RESULT"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo -e "${GREEN}✅ 文件上传成功，File Key: $FILE_KEY${NC}"

# 获取音频时长
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$TEMP_OPUS")
DURATION_MS=$(echo "$DURATION" | awk '{printf "%.0f", $1 * 1000}')

echo -e "${BLUE}📤 发送语音消息...${NC}"

# 发送消息
RESULT=$(curl -s -X POST "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"receive_id\":\"$FEISHU_CHAT_ID\",\"msg_type\":\"audio\",\"content\":\"{\\\"file_key\\\":\\\"$FILE_KEY\\\",\\\"duration\\\":$DURATION_MS}\"}")

MESSAGE_ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('message_id',''))")

# 清理临时文件
rm -rf "$TEMP_DIR"

# 检查结果
if [ -n "$MESSAGE_ID" ]; then
    echo -e "${GREEN}✅ 发送成功！${NC}"
    echo "Message ID: $MESSAGE_ID"
    echo "Chat ID: $FEISHU_CHAT_ID"
    echo "时长：${DURATION_MS}ms"
else
    echo -e "${RED}❌ 发送失败${NC}"
    echo "$RESULT"
    exit 1
fi
