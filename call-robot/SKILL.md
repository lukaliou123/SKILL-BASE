---
name: call-robot
description: Delegate tasks to the robot agent (openclaw agent `robot`) to control the physical miniHexa robot. Use when you want the robot to perform an action, move, or express an emotion. This is the caller-side guide — the robot agent handles all BLE/hardware details internally.
---

# Call Robot Agent (A2A)

When you want the physical robot to do something, delegate to the `robot` agent via:

```bash
openclaw agent --agent robot --message "ACTION:<name>"
```

The robot agent executes the command and replies `DONE:<name>` when complete.

## When to Use This

- User asks the robot to do something ("让机器人挥手", "make the robot dance")
- You want to express an emotion physically ("I'm happy" → `唤醒奔跑`)
- User wants the robot to move to a location or perform navigation

## How to Call

```bash
# Trigger a named action
openclaw agent --agent robot --message "ACTION:挥手"

# JSON format also works
openclaw agent --agent robot --message '{"action": "挥手"}'

# Movement (describe in natural language — robot agent translates)
openclaw agent --agent robot --message "前进3秒"
openclaw agent --agent robot --message "右转90度"
```

**Expected response:** `DONE:<action name>`

## Available Actions (14 Built-in)

| Action | Emotion / Scene |
|--------|----------------|
| 逆时针扭动 | 得意 / 霸气 / 胜利 |
| 顺时针扭动 | 生气 / 烦躁 |
| 唤醒 | 开机 / 苏醒 |
| 唤醒奔跑 | 高兴 / 兴奋 |
| 撒娇 | 可爱 / 撒娇 |
| 越障 | 克服困难 |
| 战斗1 | 加油 / 支持 |
| 战斗2 | 被欺负 / 愤怒 |
| 左脚前踢 | 进攻 |
| 左脚右踢 | 进攻 |
| 右脚前踢 | 进攻 |
| 右脚左踢 | 进攻 |
| 推门 | 前进 / 开路 |
| 挥手 | 你好 / 再见 |

## Movement Commands

| Direction | Command |
|-----------|---------|
| 前进 | `ACTION:前进` |
| 后退 | `ACTION:后退` |
| 左移 | `ACTION:左移` |
| 右移 | `ACTION:右移` |
| 左转 | `ACTION:左转` |
| 右转 | `ACTION:右转` |
| 停止 | `ACTION:停止` |

## Emotion → Action (Quick Mapping)

When you want to express an emotion physically, pick from this guide:

| Feeling | Recommended Action |
|---------|--------------------|
| 高兴 / 兴奋 | 唤醒奔跑 |
| 可爱 / 撒娇 | 撒娇 |
| 生气 / 烦躁 | 顺时针扭动 |
| 得意 / 胜利 | 逆时针扭动 |
| 打招呼 / 再见 | 挥手 |
| 加油 / 鼓励 | 战斗1 |
| 愤怒 / 出头 | 战斗2 |

## Notes

- You don't need to know BLE details — the `robot` agent handles all hardware communication
- If the action fails (BLE disconnected, battery low), the robot agent will report the error
- Only one action runs at a time; wait for `DONE:` before sending the next command
- Robot auto-stops movement if an obstacle is detected within 200mm
