# SKILL-BASE

`SKILL-BASE` is a reusable Cursor skill package for controlling the miniHexa ESP32 robot over BLE.

It includes:
- a ready-to-run control script (`BLERobot`)
- action/movement mapping data
- skill instructions for LLM-driven interaction

## Repository Structure

```text
SKILL-BASE/
├── SKILL.md
├── scripts/
│   └── ble_robot.py
└── references/
    └── actions_map.json
```

## Features

- Trigger all 14 built-in action groups (`K|1|id&`)
- Move robot with direction commands (`C|vx|vy|rot&`)
- Auto-stop when obstacle is detected (distance notify over BLE)
- Support emotion-to-action hints for conversational AI

## Requirements

- Python 3.10+
- `bleak`

Install:

```bash
pip install bleak
```

## Quick Start

```python
import asyncio
from scripts.ble_robot import BLERobot

async def main():
    async with BLERobot() as robot:
        await robot.play("挥手")
        await robot.move("前进", duration_s=3)
        print("distance:", robot.distance_mm)

asyncio.run(main())
```

Run interactive mode:

```bash
python scripts/ble_robot.py
```

## Notes

- BLE device name: `miniHexa`
- Write UUID: `0000ffe1-0000-1000-8000-00805f9b34fb`
- Notify UUID: `0000ffe2-0000-1000-8000-00805f9b34fb`
- Forward movement uses `vy` axis: `C|0|30|0&`

## Safety / Scope

- This repo contains no API keys, secrets, tokens, or private credentials.
- It only contains robot-control logic, mappings, and documentation.
