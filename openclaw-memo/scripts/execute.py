#!/usr/bin/env python3
"""
OpenClaw Memo Executor

Reads confirmed actions from digest.md and executes them.
Logs all execution results to an audit file.

Usage:
    python3 execute.py --digest digest.md --items "1,3" --dry-run
    python3 execute.py --digest digest.md --items "1,3"
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


@dataclass
class DigestItem:
    index: int
    category: str
    content: str


@dataclass
class ExecResult:
    item: DigestItem
    action: str
    status: str       # ok / failed / skipped / dry-run
    detail: str


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Execute confirmed memo actions.")
    p.add_argument("--digest", required=True)
    p.add_argument("--items", required=True,
                   help="Comma-separated 1-based indices (e.g. 1,3,5)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--audit-log",
                   default=os.getenv("OPENCLAW_MEMO_AUDIT_LOG", "audit.md"))
    p.add_argument("--feishu-app-id",
                   default=os.getenv("OPENCLAW_MEMO_FEISHU_APP_ID", ""))
    p.add_argument("--feishu-app-secret",
                   default=os.getenv("OPENCLAW_MEMO_FEISHU_APP_SECRET", ""))
    p.add_argument("--feishu-chat-id",
                   default=os.getenv("OPENCLAW_MEMO_FEISHU_CHAT_ID", ""))
    return p.parse_args()


# ---------------------------------------------------------------------------
# Digest parsing
# ---------------------------------------------------------------------------

def extract_items(digest_path: Path) -> list[DigestItem]:
    if not digest_path.exists():
        return []

    text = digest_path.read_text(encoding="utf-8")
    items: list[DigestItem] = []
    current_cat = "未分类"
    idx = 1

    for line in text.splitlines():
        header = re.match(r"^##\s+(待办|待查|想法|观察|作息)", line)
        if header:
            current_cat = header.group(1)
            continue

        if not line.startswith("- "):
            continue
        if line.startswith("  "):
            continue

        content = line[2:].strip()
        content = re.sub(r"\s+_[^_]+_$", "", content).strip()
        content = re.sub(r"^(\[[ x]\]\s*)?(\*\*#\d+\*\*\s*)?", "", content).strip()
        content = content.strip("*").strip()

        if not content or content == "无":
            continue

        items.append(DigestItem(index=idx, category=current_cat, content=content))
        idx += 1

    return items


# ---------------------------------------------------------------------------
# Feishu
# ---------------------------------------------------------------------------

def _feishu_token(app_id: str, app_secret: str) -> str:
    import urllib.request
    payload = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read()).get("tenant_access_token", "")


def _send_feishu(text: str, app_id: str,
                 app_secret: str, chat_id: str) -> bool:
    if not all([app_id, app_secret, chat_id]):
        return False
    try:
        import urllib.request
        token = _feishu_token(app_id, app_secret)
        payload = json.dumps({
            "receive_id": chat_id,
            "msg_type": "text",
            "content": json.dumps({"text": text}),
        }).encode()
        req = urllib.request.Request(
            "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
            data=payload,
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
        return result.get("code", -1) == 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Action dispatch
# ---------------------------------------------------------------------------

ACTION_REGISTRY: list[tuple[str, re.Pattern, callable]] = []


def register(name: str, pattern: str):
    """Decorator to register an action handler."""
    compiled = re.compile(pattern, re.IGNORECASE)
    def decorator(fn):
        ACTION_REGISTRY.append((name, compiled, fn))
        return fn
    return decorator


@register("feishu_message", r"(发消息|通知|飞书|发送)")
def _act_feishu(item: DigestItem, args: argparse.Namespace, dry: bool) -> ExecResult:
    if dry:
        return ExecResult(item, "feishu_message", "dry-run",
                          f"would send: {item.content}")
    if not args.feishu_app_id:
        return ExecResult(item, "feishu_message", "skipped",
                          "Feishu not configured")
    ok = _send_feishu(item.content, args.feishu_app_id,
                      args.feishu_app_secret, args.feishu_chat_id)
    return ExecResult(item, "feishu_message",
                      "ok" if ok else "failed",
                      "sent" if ok else "API call failed")


@register("web_search", r"(查|搜索|search|了解)")
def _act_search(item: DigestItem, args: argparse.Namespace, dry: bool) -> ExecResult:
    if dry:
        return ExecResult(item, "web_search", "dry-run",
                          f"would search: {item.content}")
    try:
        r = subprocess.run(
            ["oracle", "--print", f"搜索并总结：{item.content}"],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0 and r.stdout.strip():
            return ExecResult(item, "web_search", "ok",
                              r.stdout.strip()[:500])
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return ExecResult(item, "web_search", "skipped",
                      "search tool unavailable")


@register("shell_command", r"^(执行|运行|run)\s*[：:]")
def _act_shell(item: DigestItem, args: argparse.Namespace, dry: bool) -> ExecResult:
    cmd_match = re.match(r"^(执行|运行|run)\s*[：:]\s*(.+)$",
                         item.content, re.IGNORECASE)
    if not cmd_match:
        return ExecResult(item, "shell_command", "skipped", "no command found")
    cmd = cmd_match.group(2).strip()
    if dry:
        return ExecResult(item, "shell_command", "dry-run",
                          f"would run: {cmd}")
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True,
                           text=True, timeout=30)
        out = r.stdout.strip() or r.stderr.strip() or "(no output)"
        return ExecResult(item, "shell_command", "ok", out[:300])
    except subprocess.TimeoutExpired:
        return ExecResult(item, "shell_command", "failed", "timeout")
    except Exception as e:
        return ExecResult(item, "shell_command", "failed", str(e))


@register("note_write", r"(写|记录|保存|文档)")
def _act_write(item: DigestItem, args: argparse.Namespace, dry: bool) -> ExecResult:
    if dry:
        return ExecResult(item, "note_write", "dry-run",
                          f"would record: {item.content}")
    return ExecResult(item, "note_write", "ok", f"recorded: {item.content}")


def dispatch(item: DigestItem, args: argparse.Namespace, dry: bool) -> ExecResult:
    if item.category == "待查":
        return _act_search(item, args, dry)

    for name, pattern, handler in ACTION_REGISTRY:
        if pattern.search(item.content):
            return handler(item, args, dry)

    if dry:
        return ExecResult(item, "mark_done", "dry-run",
                          f"would mark complete: {item.content}")
    return ExecResult(item, "mark_done", "ok", f"marked: {item.content}")


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

def write_audit(results: list[ExecResult], audit_path: Path, dry: bool) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"\n## {now} {'(dry-run)' if dry else ''}\n"]
    for r in results:
        icon = {"ok": "v", "failed": "x", "skipped": "-",
                "dry-run": "~"}.get(r.status, "?")
        lines.append(
            f"- [{icon}] **#{r.item.index}** {r.item.category}：{r.item.content}"
        )
        lines.append(f"  action={r.action} status={r.status} → {r.detail}")
    lines.append("")

    with open(audit_path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    digest_path = Path(args.digest)
    audit_path = Path(args.audit_log)

    try:
        indices = [int(i.strip()) for i in args.items.split(",") if i.strip()]
    except ValueError:
        print("invalid item indices — use comma-separated numbers like: 1,3,5",
              file=sys.stderr)
        return 1

    all_items = extract_items(digest_path)
    if not all_items:
        print("no items found in digest")
        return 0

    if args.dry_run:
        print("[dry-run] no actions will actually execute\n")

    print(f"executing {len(indices)} items: {indices}\n")

    results: list[ExecResult] = []
    for idx in indices:
        matching = [i for i in all_items if i.index == idx]
        if not matching:
            print(f"  [{idx}] not found (digest has {len(all_items)} items)")
            continue
        item = matching[0]
        result = dispatch(item, args, args.dry_run)
        results.append(result)

        status_icon = {"ok": "ok", "failed": "FAIL", "skipped": "skip",
                       "dry-run": "dry"}.get(result.status, "?")
        print(f"  [{idx}] {item.category}: {item.content}")
        print(f"       [{status_icon}] {result.action} → {result.detail}")

    write_audit(results, audit_path, args.dry_run)

    ok_count = sum(1 for r in results if r.status == "ok")
    print(f"\ndone. {ok_count}/{len(results)} succeeded. "
          f"audit log: {audit_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
