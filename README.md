# 数码宝贝 — Digital Companion Skill Suite

一套基于 [OpenClaw](https://openclaw.ai) 的 AI 陪伴系统。

让一个 AI 真正「认识你」，并以数字和实体两种形态，持续陪在你身边。

---

## 它是什么

用户只需随口说一句话，系统自动完成**记录、分类整理、飞书归档、定时提醒和任务执行**的完整闭环。

与此同时，它通过读取用户的语音记录和日程，主动了解你今天经历了什么，每晚发起复盘对话——不是等你来问，而是主动关心你。

与 AI 对话时，桌面上的六足机器人会同步发出语音、做出动作，让这个 AI 不只活在屏幕里，而是真实存在于你的空间中。

## 解决什么问题

现有 AI 助手**没有记忆连续性、没有存在感、没有关系感**——每次对话都是重新开始的工具，而不是陪你过日子的存在。

这个项目试图填补这个空缺：让一个 AI 真正「认识你」，并以数字和实体两种形态，持续陪在你身边。

## 当前效果

- 跑通「碎片输入 → 自动整理 → 飞书归档 → 提醒执行」的完整闭环
- 语音交互、录音豆摘取、机器人动作联动均已实现
- 同一个 AI 人格的交互，可以无缝跨越手机、飞书和实体机器人三个场景
- 陪伴不因场景切换而中断

---

## 五个 Skill，一个存在

```
数码宝贝
├── 大脑    openclaw-memo       记忆、思考、整理、执行、陪伴
├── 声音    feishu-voice        用真正的语音条说话，不是冷冰冰的文字
├── 身体    minihexa-robot      六足机器人，用动作表达情绪和回应
├── 桥梁    call-robot          让大脑能指挥身体（A2A 协议）
└── 眼睛    tplink-ipc-camera   看见物理世界，感知环境
```

### [`openclaw-memo`](./openclaw-memo/) — 大脑

AI 秘书的核心。捕捉用户的碎片化输入，自动分类（待办 / 待查 / 想法 / 观察 / 作息），定时整理成结构化日报，对待查项联网搜索补充，确认后执行任务。长期记忆形成陪伴感——它真的记得你说过什么。

- 随口一句话 → 自动记录分类
- 定时整理 → 飞书 / Notion / Apple Notes 归档
- 待查自动搜索 → 结果附在日报里
- 模式识别 → 「你这周一直在想硬件的事」
- 过期提醒 → 「有 2 条待办放了三天了」

### [`feishu-voice`](./feishu-voice/) — 声音

让 AI 能通过飞书发送真正的语音条（点击即播，不是文件附件）。基于 NoizAI TTS，支持情感控制。早安问候、晚间复盘、任务提醒——用声音而不是文字，让交互有温度。

- 一行命令发送语音消息
- 支持情感参数：happy / sad / neutral
- 适合晨间问候、日报播报、睡前故事

### [`minihexa-robot`](./minihexa-robot/) — 身体

通过 BLE 蓝牙控制 miniHexa 六足 ESP32 机器人。14 个内置动作组（挥手、撒娇、战斗、唤醒奔跑...），每个动作对应一种情绪场景。AI 高兴时机器人跑起来，AI 打招呼时机器人挥手——让情绪不只是文字，而是看得见的肢体语言。

- 14 个情绪化动作 + 六向移动控制
- 障碍检测 + 自动避障
- 完整速度标定和偏转纠偏算法
- 情绪 → 动作自动映射

### [`call-robot`](./call-robot/) — 桥梁

A2A（Agent-to-Agent）协议。让 memo 秘书和其他 agent 能直接指挥机器人，不需要懂 BLE 细节。一句话委托：

```bash
openclaw agent --agent robot --message "ACTION:挥手"
```

高兴时让机器人跑起来，难过时让它安静下来，打招呼时挥手——AI 的情绪通过机器人的动作表达出来。

### [`tplink-ipc-camera`](./tplink-ipc-camera/) — 眼睛

TP-Link IPC 摄像头集成。通过 RTSP 抓帧 + ONVIF 云台控制，给 AI 视觉感知能力。可以看见机器人在哪、房间里有什么、用户是否在场。配合 Gemini 视觉分析，让 AI 理解物理空间。

- 4K 抓帧 + AI 视觉分析
- 云台控制（上下左右旋转）
- 机器人导航的视觉辅助

---

## 跨场景体验

同一个 AI 人格，三种场景无缝切换：

| 场景 | 交互形式 | 核心 Skill |
|------|---------|-----------|
| **外出 / 手机** | 飞书文字对话，随时记录碎片 | openclaw-memo |
| **工作 / 电脑** | 飞书语音 + 文字，接收日报和提醒 | openclaw-memo + feishu-voice |
| **回家 / 桌面** | 机器人用动作回应，语音对话 | minihexa-robot + feishu-voice + tplink-ipc-camera |

你跟手机上的秘书说了一句话，回到家，桌上的机器人已经知道了。

---

## 产品演化路线

```
Level 0 — 文字秘书        ✅ 已实现
           碎片输入 → 自动整理 → 归档 → 提醒 → 执行

Level 1 — 语音秘书        ✅ 已实现
           飞书语音条 + TTS 情感控制

Level 2 — 环境感知        ✅ 已实现
           摄像头视觉 + 录音豆摘取

Level 3 — 具身陪伴        ✅ 已实现
           六足机器人动作联动 + 情绪映射 + A2A 协作
```

每一层向上兼容。Level 0 独立可用，Level 3 是完整形态。

---

## 快速开始

### 1. 只用文字秘书（最小部署）

```bash
# 安装 memo skill
cp -r openclaw-memo/ /path/to/workspace/skills/openclaw-memo/
bash skills/openclaw-memo/setup.sh
```

对 bot 说话就行。"记一下买电池"、"查查声网延迟"——它会自动记录、分类、整理。

### 2. 加上语音

```bash
# 安装 feishu-voice skill
cp -r feishu-voice/ /path/to/workspace/skills/feishu-voice/
# 配置 Feishu App + NoizAI API Key
```

AI 的回复变成语音条，点击即播。

### 3. 加上机器人

```bash
# 安装 robot skills
cp -r minihexa-robot/ /path/to/workspace/skills/minihexa-robot/
cp -r call-robot/ /path/to/workspace/skills/call-robot/
pip3 install bleak
```

AI 高兴时机器人跑起来。打招呼时挥手。它不再只是屏幕上的文字。

### 4. 加上视觉

```bash
cp -r tplink-ipc-camera/ /path/to/workspace/skills/tplink-ipc-camera/
```

AI 能看见房间，知道机器人在哪，感知物理世界。

---

## 项目结构

```
SKILL-BASE/
├── openclaw-memo/             # 大脑：记忆、整理、执行、陪伴
│   ├── SKILL.md               #   Agent 行为指南
│   ├── README.md              #   人类安装指南
│   ├── clawhub.yaml           #   ClaWHub 发布清单
│   ├── setup.sh               #   一键初始化
│   ├── config.example.env     #   配置模板
│   └── scripts/
│       ├── process.sh         #   Cron 入口
│       ├── process_notes.py   #   处理器 + 存储适配器
│       └── execute.py         #   任务执行器
├── feishu-voice/              # 声音：飞书语音条
│   ├── SKILL.md
│   ├── clawhub.yaml
│   ├── scripts/
│   │   └── send_voice.sh
│   └── examples/
├── minihexa-robot/            # 身体：六足机器人 BLE 控制
│   ├── SKILL.md
│   ├── scripts/
│   │   └── ble_robot.py
│   └── references/
│       ├── actions_map.json
│       └── room_map.md
├── call-robot/                # 桥梁：A2A 委托协议
│   └── SKILL.md
└── tplink-ipc-camera/         # 眼睛：摄像头抓帧 + 云台
    ├── SKILL.md
    └── scripts/
        ├── grab_frame.sh
        └── analyze_frame.py
```

---

## 核心理念

**陪伴不是拟人化表演，而是因为它真的记得你。**

这个系统的陪伴感不来自说漂亮话，而来自三个真实能力：
1. **记忆连续性** — 它见过你所有的碎片，所以能说出有上下文的话
2. **主动性** — 它不等你问，而是在你沉默的时候继续工作
3. **具身存在** — 它不只活在屏幕里，桌上的机器人让它真实存在于你的空间中

---

## 技术栈

- **平台**: [OpenClaw](https://openclaw.ai) 3.8+
- **通信**: 飞书 Bot API / Discord
- **语音**: NoizAI TTS + FFmpeg
- **硬件**: miniHexa ESP32 (BLE) + TP-Link IPC (RTSP/ONVIF)
- **搜索**: Tavily API
- **存储**: 飞书文档 / Notion / Apple Notes / 本地文件
- **语言**: Python 3, Bash

## License

MIT
