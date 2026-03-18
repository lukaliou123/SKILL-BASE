#!/usr/bin/env python3
"""
OpenClaw Memo Processor

Reads unprocessed notes from inbox, classifies them, optionally enriches
待查 items with web search, writes a structured digest, and routes output
to the configured storage backend (local / Feishu / Notion / Apple Notes).

Usage:
    python3 process_notes.py --notes notes.md --digest digest.md --target local
    python3 process_notes.py --notes notes.md --digest digest.md --target feishu --enrich
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


CATEGORY_ORDER = ["待办", "待查", "想法", "观察", "作息"]

CATEGORY_PATTERNS = [
    ("待办", re.compile(
        r"^(待办|todo|任务|提醒|remind)\s*[：:]\s*(.+)$", re.IGNORECASE
    )),
    ("待查", re.compile(
        r"^(待查|查|搜索|search|了解|look\s*up)\s*[：:]\s*(.+)$", re.IGNORECASE
    )),
    ("想法", re.compile(
        r"^(想法|idea|灵感|思考|方向)\s*[：:]\s*(.+)$", re.IGNORECASE
    )),
    ("观察", re.compile(
        r"^(观察|记录|note|见闻|经历)\s*[：:]\s*(.+)$", re.IGNORECASE
    )),
    ("作息", re.compile(
        r"^(作息|睡眠|锻炼|健康|运动|饮食|sleep|exercise)\s*[：:]\s*(.+)$",
        re.IGNORECASE,
    )),
]


@dataclass
class NoteItem:
    line_index: int
    timestamp: str
    category: str
    content: str
    search_result: str | None = None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Process OpenClaw memo inbox.")
    p.add_argument("--notes", required=True, help="Path to notes.md")
    p.add_argument("--digest", required=True, help="Path to digest.md")
    p.add_argument(
        "--target",
        default=os.getenv("OPENCLAW_MEMO_STORAGE_TARGET", "local"),
        choices=["local", "feishu", "notion", "apple"],
    )
    p.add_argument(
        "--enrich", action="store_true",
        default=os.getenv("OPENCLAW_MEMO_ENRICH", "").lower() in ("1", "true", "yes"),
    )
    p.add_argument("--feishu-doc-token",
                    default=os.getenv("OPENCLAW_MEMO_FEISHU_DOC_TOKEN", ""))
    p.add_argument("--feishu-app-id",
                    default=os.getenv("OPENCLAW_MEMO_FEISHU_APP_ID", ""))
    p.add_argument("--feishu-app-secret",
                    default=os.getenv("OPENCLAW_MEMO_FEISHU_APP_SECRET", ""))
    p.add_argument("--feishu-chat-id",
                    default=os.getenv("OPENCLAW_MEMO_FEISHU_CHAT_ID", ""))
    p.add_argument("--notion-key",
                    default=os.getenv("OPENCLAW_MEMO_NOTION_API_KEY", ""))
    p.add_argument("--notion-db",
                    default=os.getenv("OPENCLAW_MEMO_NOTION_DATABASE_ID", ""))
    return p.parse_args()


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def detect_category(raw: str) -> tuple[str, str]:
    text = raw.strip()
    for category, pattern in CATEGORY_PATTERNS:
        m = pattern.match(text)
        if m:
            return category, m.group(2).strip()
    return "观察", text


def collect_unprocessed(lines: list[str]) -> list[NoteItem]:
    items: list[NoteItem] = []
    ts = "未分组"
    for idx, line in enumerate(lines):
        s = line.strip()
        if s.startswith("### "):
            ts = s.removeprefix("### ").strip()
            continue
        if not s.startswith("- "):
            continue
        if "[processed]" in s:
            continue
        cat, content = detect_category(s[2:])
        items.append(NoteItem(line_index=idx, timestamp=ts,
                              category=cat, content=content))
    return items


def mark_processed(lines: list[str], items: list[NoteItem]) -> list[str]:
    out = list(lines)
    for item in items:
        out[item.line_index] = out[item.line_index].rstrip("\n") + " [processed]\n"
    return out


# ---------------------------------------------------------------------------
# Search enrichment
# ---------------------------------------------------------------------------

def _tavily_search(query: str, api_key: str) -> str | None:
    try:
        import urllib.request
        req = urllib.request.Request(
            "https://api.tavily.com/search",
            data=json.dumps({
                "api_key": api_key,
                "query": query,
                "max_results": 3,
                "search_depth": "basic",
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        results = data.get("results", [])
        if results:
            return "\n".join(
                f"  - {r.get('title', '')}: {r.get('content', '')[:200]}"
                for r in results[:3]
            )
    except Exception as e:
        print(f"  [Tavily] search failed: {e}", file=sys.stderr)
    return None


def _oracle_search(query: str) -> str | None:
    try:
        r = subprocess.run(
            ["oracle", "--print", f"搜索：{query}，给我一句话摘要"],
            capture_output=True, text=True, timeout=20,
        )
        if r.returncode == 0 and r.stdout.strip():
            return "  - " + r.stdout.strip()[:300]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def enrich(items: list[NoteItem]) -> None:
    api_key = os.getenv("OPENCLAW_MEMO_TAVILY_API_KEY", "")
    for item in items:
        if item.category != "待查":
            continue
        print(f"  [搜索] {item.content}...")
        result = None
        if api_key:
            result = _tavily_search(item.content, api_key)
        if not result:
            result = _oracle_search(item.content)
        item.search_result = result or "  - [待搜索 — 未配置搜索 API]"


# ---------------------------------------------------------------------------
# Digest rendering
# ---------------------------------------------------------------------------

def render_digest(items: list[NoteItem], target: str, enriched: bool) -> str:
    now = datetime.now()
    grouped: dict[str, list[NoteItem]] = {c: [] for c in CATEGORY_ORDER}
    for item in items:
        grouped[item.category].append(item)

    lines = [
        f"# Memo Digest — {now.strftime('%Y-%m-%d')}",
        "",
        f"> 生成时间：{now.strftime('%Y-%m-%d %H:%M')} · "
        f"目标：{target} · 条目：{len(items)} · "
        f"搜索增强：{'是' if enriched else '否'}",
        "",
    ]

    for cat in CATEGORY_ORDER:
        cat_items = grouped[cat]
        lines.append(f"## {cat}（{len(cat_items)}）")
        if not cat_items:
            lines.append("_无_")
            lines.append("")
            continue
        for i, item in enumerate(cat_items, 1):
            if cat == "待办":
                lines.append(f"- [ ] **#{i}** {item.content}  _{item.timestamp}_")
            elif cat == "待查" and item.search_result:
                lines.append(f"- **{item.content}**")
                lines.append(item.search_result)
            else:
                lines.append(f"- {item.content}  _{item.timestamp}_")
        lines.append("")

    lines += ["---", f"_OpenClaw Memo · {now.strftime('%Y-%m-%d %H:%M')}_", ""]
    return "\n".join(lines)


def render_notification(items: list[NoteItem]) -> str:
    grouped: dict[str, list[NoteItem]] = {c: [] for c in CATEGORY_ORDER}
    for item in items:
        grouped[item.category].append(item)

    parts = [f"Memo 整理完成 — {len(items)} 条"]
    for cat in CATEGORY_ORDER:
        ci = grouped[cat]
        if ci:
            preview = "、".join(i.content[:20] for i in ci[:3])
            if len(ci) > 3:
                preview += f" 等 {len(ci)} 条"
            parts.append(f"  {cat}：{preview}")
    parts.append("回复「详情」查看完整 digest，或「执行 #1」执行待办。")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Feishu adapter
# ---------------------------------------------------------------------------

def _feishu_token(app_id: str, app_secret: str) -> str:
    import urllib.request
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=json.dumps({"app_id": app_id, "app_secret": app_secret}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read()).get("tenant_access_token", "")


def write_feishu_doc(digest: str, doc_token: str,
                     app_id: str, app_secret: str) -> bool:
    if not all([doc_token, app_id, app_secret]):
        print("[Feishu Doc] missing config, skipping", file=sys.stderr)
        return False
    try:
        import urllib.request
        token = _feishu_token(app_id, app_secret)
        if not token:
            print("[Feishu Doc] token acquisition failed", file=sys.stderr)
            return False

        url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            blocks = json.loads(resp.read())

        block_items = blocks.get("data", {}).get("items", [])
        if not block_items:
            print("[Feishu Doc] empty document, cannot append", file=sys.stderr)
            return False

        last_id = block_items[-1].get("block_id", "")
        payload = json.dumps({
            "children": [{
                "block_type": 2,
                "paragraph": {
                    "elements": [{
                        "type": "text_run",
                        "text_run": {"content": digest[:2000]},
                    }]
                }
            }],
            "index": -1,
        }).encode()

        append_url = (
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}"
            f"/blocks/{last_id}/children"
        )
        req2 = urllib.request.Request(
            append_url, data=payload,
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req2, timeout=10) as resp2:
            result = json.loads(resp2.read())

        ok = result.get("code", -1) == 0
        print(f"[Feishu Doc] {'ok' if ok else 'failed: ' + str(result)}",
              file=sys.stderr)
        return ok
    except Exception as e:
        print(f"[Feishu Doc] error: {e}", file=sys.stderr)
        return False


def send_feishu_im(message: str, app_id: str,
                   app_secret: str, chat_id: str) -> bool:
    if not all([app_id, app_secret, chat_id]):
        return False
    try:
        import urllib.request
        token = _feishu_token(app_id, app_secret)
        if not token:
            return False
        payload = json.dumps({
            "receive_id": chat_id,
            "msg_type": "text",
            "content": json.dumps({"text": message}),
        }).encode()
        req = urllib.request.Request(
            "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
            data=payload,
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
        ok = result.get("code", -1) == 0
        if ok:
            print("[Feishu IM] notification sent", file=sys.stderr)
        else:
            print(f"[Feishu IM] failed: {result}", file=sys.stderr)
        return ok
    except Exception as e:
        print(f"[Feishu IM] error: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Notion adapter
# ---------------------------------------------------------------------------

def write_notion(digest: str, api_key: str, database_id: str) -> bool:
    if not api_key or not database_id:
        print("[Notion] missing config, skipping", file=sys.stderr)
        return False
    try:
        import urllib.request
        title = f"Memo Digest — {datetime.now().strftime('%Y-%m-%d')}"
        payload = json.dumps({
            "parent": {"database_id": database_id},
            "properties": {
                "Name": {"title": [{"text": {"content": title}}]},
            },
            "children": [{
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text",
                                   "text": {"content": digest[:2000]}}]
                },
            }],
        }).encode()
        req = urllib.request.Request(
            "https://api.notion.com/v1/pages",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
        print(f"[Notion] created page: {result.get('id', '')}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[Notion] error: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Apple Notes adapter
# ---------------------------------------------------------------------------

def write_apple_notes(digest: str) -> bool:
    title = f"Memo Digest — {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    try:
        proc = subprocess.run(
            ["memo", "notes", "-a", title],
            input=digest, text=True, capture_output=True,
        )
        if proc.returncode == 0:
            print("[Apple Notes] ok", file=sys.stderr)
            return True
        print(f"[Apple Notes] failed: {proc.stderr}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("[Apple Notes] memo CLI not installed, skipping", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    notes_path = Path(args.notes)
    digest_path = Path(args.digest)

    if not notes_path.exists():
        print(f"[error] notes file not found: {notes_path}", file=sys.stderr)
        return 1

    print(f"[OpenClaw Memo] processing...")
    print(f"  input: {notes_path} | output: {digest_path} | target: {args.target}")

    lines = notes_path.read_text(encoding="utf-8").splitlines(keepends=True)
    items = collect_unprocessed(lines)

    if not items:
        digest_path.write_text(
            "# Memo Digest\n\n没有新的待处理条目。\n", encoding="utf-8"
        )
        print("  no unprocessed items.")
        return 0

    print(f"  found {len(items)} unprocessed items")

    if args.enrich:
        enrich(items)

    digest = render_digest(items, args.target, args.enrich)

    digest_path.write_text(digest, encoding="utf-8")
    print(f"  digest written: {digest_path}")

    notes_path.write_text(
        "".join(mark_processed(lines, items)), encoding="utf-8"
    )
    print(f"  notes marked [processed]")

    if args.target == "feishu":
        write_feishu_doc(digest, args.feishu_doc_token,
                         args.feishu_app_id, args.feishu_app_secret)
    elif args.target == "notion":
        write_notion(digest, args.notion_key, args.notion_db)
    elif args.target == "apple":
        write_apple_notes(digest)

    if args.feishu_app_id and args.feishu_app_secret and args.feishu_chat_id:
        send_feishu_im(render_notification(items),
                       args.feishu_app_id, args.feishu_app_secret,
                       args.feishu_chat_id)

    cat_summary = {}
    for item in items:
        cat_summary[item.category] = cat_summary.get(item.category, 0) + 1
    summary = "、".join(f"{c} {n}" for c, n in cat_summary.items())
    print(f"  done. {len(items)} items ({summary})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
