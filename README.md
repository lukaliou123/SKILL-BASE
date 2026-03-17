# SKILL-BASE

A collection of openclaw skills for physical device control and AI agent integration.

## Skills

| Skill | Description |
|-------|-------------|
| [`minihexa-robot`](./minihexa-robot/) | Direct BLE control of the miniHexa 6-legged ESP32 robot — for the `robot` agent |
| [`tplink-ipc-camera`](./tplink-ipc-camera/) | Grab and analyze frames from TP-Link IPC camera |
| [`call-robot`](./call-robot/) | A2A caller guide — how other agents delegate tasks to the `robot` agent |
| [`feishu-voice`](./feishu-voice/) | Send real Feishu voice messages (OPUS) via NoizAI TTS |

## Structure

```
SKILL-BASE/
├── minihexa-robot/        # Robot BLE control (used by robot agent directly)
│   ├── scripts/
│   │   └── ble_robot.py
│   ├── references/
│   │   ├── actions_map.json
│   │   └── room_map.md
│   └── SKILL.md
├── tplink-ipc-camera/     # Camera integration
│   ├── scripts/
│   │   ├── grab_frame.sh
│   │   └── analyze_frame.py
│   └── SKILL.md
├── call-robot/            # A2A interface guide for callers (e.g. main agent)
│   └── SKILL.md
└── feishu-voice/          # Send Feishu voice messages via NoizAI TTS
    ├── scripts/
    │   └── send_voice.sh
    ├── examples/
    ├── config.env.example  # Copy to config.env and fill in credentials
    └── SKILL.md
```

## Usage

### For the `robot` agent
Install `minihexa-robot` — it provides direct BLE hardware control.

### For other agents (main, etc.)
Install `call-robot` — it teaches you how to delegate tasks to the `robot` agent via:
```bash
openclaw agent --agent robot --message "ACTION:挥手"
```
No BLE knowledge needed.
