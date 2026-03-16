---
name: minihexa-robot-control
description: Control the miniHexa 6-legged ESP32 robot via BLE (Bluetooth). Provides action commands (14 built-in action groups), movement control (forward/back/turn/stop), and real-time obstacle detection. Use when the user wants to control the miniHexa robot, trigger robot actions based on emotion/context, make the robot move, or integrate robot control into an AI assistant workflow.
---

# miniHexa Robot Control

The robot is controlled wirelessly via BLE using `scripts/ble_robot.py`. All 14 action groups, movement directions, and emotion mappings are in `references/actions_map.json`.

## Setup

This skill includes ready-to-use scripts. Copy them to your working directory first:

```powershell
$skill = "$env:USERPROFILE\.cursor\skills\minihexa-robot-control"
cp "$skill\scripts\ble_robot.py" .
cp "$skill\references\actions_map.json" .
```

Requires: `pip install bleak`

## Quick Start

```python
import asyncio
from ble_robot import BLERobot

async def main():
    async with BLERobot() as robot:
        await robot.play("挥手")               # trigger action by name
        await robot.move("前进", duration_s=3) # move forward 3s then auto-stop
        print(robot.distance_mm)               # current obstacle distance

asyncio.run(main())
```

Or run standalone: `python ble_robot.py` (interactive CLI)

## Skill Files

| File | Purpose |
|------|---------|
| `scripts/ble_robot.py` | Main BLE control class (`BLERobot`) — copy to project |
| `references/actions_map.json` | All actions, movement cmds, emotion hints — copy to project |

## BLE Protocol

- Device name: `miniHexa`
- Write char (commands): `0000ffe1-0000-1000-8000-00805f9b34fb`
- Notify char (sensor data): `0000ffe2-0000-1000-8000-00805f9b34fb`
- Sensor push format: `$battery_mV$distance_mm$` every 200ms

## Command Reference

| Command | Format | Notes |
|---------|--------|-------|
| Action group | `K\|1\|{id}&` | id 1–14 |
| Move | `C\|vx\|vy\|rot&` | **vx=left/right, vy=front/back** (vy=30 = forward) |
| Stop | `C\|0\|0\|0&` | Robot keeps moving until stop is sent |
| Reset pose | `O&` | Return to standing |

**Important**: `vx` is left/right, `vy` is front/back. Forward = `C|0|30|0&`.

## 14 Built-in Actions

| Name | ID | Emotion / Scene |
|------|----|-----------------|
| 逆时针扭动 | 1 | 得意/霸气/胜利 |
| 顺时针扭动 | 2 | 生气/烦躁 |
| 唤醒 | 3 | 开机/苏醒 |
| 唤醒奔跑 | 4 | 高兴/兴奋 |
| 撒娇 | 5 | 可爱/撒娇 |
| 越障 | 6 | 克服困难 |
| 战斗1 | 7 | 加油/支持 |
| 战斗2 | 8 | 被欺负/愤怒/出头 |
| 左脚前踢 | 9 | 进攻 |
| 左脚右踢 | 10 | 进攻 |
| 右脚前踢 | 11 | 进攻 |
| 右脚左踢 | 12 | 进攻 |
| 推门 | 13 | 前进/开路 |
| 挥手 | 14 | 你好/再见 |

## Movement Directions

| Name | Command |
|------|---------|
| 前进 | `C\|0\|30\|0&` |
| 后退 | `C\|0\|-30\|0&` |
| 左移 | `C\|-30\|0\|0&` |
| 右移 | `C\|30\|0\|0&` |
| 左转 | `C\|0\|0\|1&` |
| 右转 | `C\|0\|0\|2&` |
| 停止 | `C\|0\|0\|0&` |

## Obstacle Detection

`BLERobot` auto-stops movement when `distance_mm < 200`. To set a custom callback:

```python
async def on_obstacle(dist_mm):
    print(f"Obstacle at {dist_mm}mm!")

robot.set_obstacle_callback(on_obstacle)
```

## Emotion → Action Mapping (LLM Integration)

Read `references/actions_map.json` → `emotion_hints` for suggested mappings. Example:

```python
# Load and use emotion hints
with open("actions_map.json", encoding="utf-8") as f:
    mapping = json.load(f)["emotion_hints"]
# mapping["被欺负/委屈/受气"] == "战斗2"
```

Then call `await robot.play(action_name)`.

## Caveats

- WiFi only supports `C` (move) and `F` (pose) — **no action groups over WiFi**
- BLE is the only wireless channel that supports all 14 action groups (`K` command)
- `L` (direct servo control) is **serial-only**, not available over BLE
- Battery warning threshold: 7000mV (robot beeps when low)
