#!/usr/bin/env python3
"""
analyze_frame.py - 用 OpenRouter gemini-3-flash-preview 分析摄像头帧

用法：
    python3 analyze_frame.py <图片路径> "提示词"

示例：
    python3 analyze_frame.py /tmp/cam.jpg "机器人箭头朝几点钟？"
"""
import base64, sys, json
import urllib.request

OR_KEY = "YOUR_OPENROUTER_API_KEY"
MODEL  = "google/gemini-3-flash-preview"

def analyze(image_path: str, prompt: str) -> str:
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    payload = json.dumps({
        "model": MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                {"type": "text", "text": prompt}
            ]
        }],
        "max_tokens": 512
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {OR_KEY}", "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    return data["choices"][0]["message"]["content"]

if __name__ == "__main__":
    img  = sys.argv[1]
    text = sys.argv[2] if len(sys.argv) > 2 else "描述这张图片"
    print(analyze(img, text))
