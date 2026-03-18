# OpenClaw Memo

A skill-first personal memo system for [OpenClaw](https://openclaw.ai).

Speak in fragments. The system captures, classifies, enriches, stores, and acts.

## What It Does

1. **Capture** — You say "明天要买电池", the agent writes `待办：买电池` to `notes.md`
2. **Process** — Cron or manual trigger classifies entries, searches 待查 items online, generates a digest
3. **Execute** — You confirm which tasks to act on, the agent executes them
4. **Companion** — The agent notices patterns, reminds you of stale tasks, sends morning briefings

## Install

```bash
# From ClaWHub
clawhub install openclaw-memo

# Or copy manually into your workspace
cp -r openclaw-memo/ /path/to/workspace/skills/openclaw-memo/
```

## Setup

```bash
# 1. Bootstrap files and config
bash skills/openclaw-memo/setup.sh

# 2. Edit config (optional — local mode works out of the box)
nano skills/openclaw-memo/config.env

# 3. Test
bash skills/openclaw-memo/scripts/process.sh
```

That's it. Notes go into `notes.md`, digests come out in `digest.md`.

## Storage Targets

| Target | Description | Config Needed |
|--------|-------------|---------------|
| `local` | Write to `digest.md` (default) | None |
| `feishu` | Append to Feishu document + IM notification | App ID, Secret, Doc Token |
| `notion` | Create page in Notion database | API Key, Database ID |
| `apple` | Create note in Apple Notes (macOS only) | `memo` CLI |

Set via `OPENCLAW_MEMO_STORAGE_TARGET` in `config.env`.

## Usage

### Capture (automatic)

Just talk to the agent naturally:

- "记：买电池" → `待办：买电池`
- "声网延迟到底多少" → `查：声网延迟`
- "想法：做一个硬件项目" → `想法：做一个硬件项目`
- "今天见了客户聊了合作" → `观察：见了客户，聊合作`
- "昨晚两点才睡" → `作息：昨晚两点入睡`

### Process (manual or cron)

```bash
# Basic
bash skills/openclaw-memo/scripts/process.sh

# With search enrichment for 待查 items
python3 skills/openclaw-memo/scripts/process_notes.py \
  --notes notes.md --digest digest.md --target local --enrich

# Output to Feishu
python3 skills/openclaw-memo/scripts/process_notes.py \
  --notes notes.md --digest digest.md --target feishu --enrich
```

### Execute (after user confirms)

```bash
# Preview
python3 skills/openclaw-memo/scripts/execute.py \
  --digest digest.md --items "1,3" --dry-run

# Execute
python3 skills/openclaw-memo/scripts/execute.py \
  --digest digest.md --items "1,3"
```

### Cron (recommended)

```bash
# Every day at 12:00 and 21:00
0 12,21 * * * cd /path/to/workspace && bash skills/openclaw-memo/scripts/process.sh >> /tmp/openclaw-memo.log 2>&1
```

`setup.sh` can install this automatically when prompted.

## Configuration

All config lives in `skills/openclaw-memo/config.env`.

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENCLAW_MEMO_STORAGE_TARGET` | `local` / `feishu` / `notion` / `apple` | `local` |
| `OPENCLAW_MEMO_NOTES_FILE` | Input notes path | `notes.md` |
| `OPENCLAW_MEMO_DIGEST_FILE` | Output digest path | `digest.md` |
| `OPENCLAW_MEMO_ENRICH` | Always search 待查 (`1` = yes) | `0` |
| `OPENCLAW_MEMO_TAVILY_API_KEY` | Tavily key for search enrichment | — |
| `OPENCLAW_MEMO_FEISHU_APP_ID` | Feishu app ID | — |
| `OPENCLAW_MEMO_FEISHU_APP_SECRET` | Feishu app secret | — |
| `OPENCLAW_MEMO_FEISHU_DOC_TOKEN` | Feishu doc token | — |
| `OPENCLAW_MEMO_FEISHU_CHAT_ID` | Feishu chat ID for notifications | — |
| `OPENCLAW_MEMO_NOTION_API_KEY` | Notion API key | — |
| `OPENCLAW_MEMO_NOTION_DATABASE_ID` | Notion database ID | — |
| `OPENCLAW_MEMO_APPLE_NOTES_FOLDER` | Apple Notes folder | `Memos` |

## Files

```
openclaw-memo/
├── SKILL.md              # Agent behavioral guide (how the LLM uses this skill)
├── README.md             # This file (human quick-start)
├── setup.sh              # One-time bootstrap
├── config.example.env    # Config template
└── scripts/
    ├── process.sh        # Cron-friendly wrapper
    ├── process_notes.py  # Processor + storage adapters
    └── execute.py        # Action executor
```

## Status

- [x] Capture fragments → notes.md
- [x] Classify: 待办 / 待查 / 想法 / 观察 / 作息
- [x] Process into categorized digest
- [x] Mark processed items `[processed]`
- [x] Tavily search enrichment for 待查
- [x] Storage adapters: local, Feishu, Notion, Apple Notes
- [x] Feishu IM digest notification
- [x] Execution module with dry-run
- [x] Cron-ready wrapper (`process.sh`)
- [ ] Companion: morning briefing
- [ ] Companion: pattern recognition
- [ ] Companion: stale task reminders
- [ ] More execution actions (email, Apple Reminders)

## License

MIT
