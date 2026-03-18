#!/usr/bin/env bash
# OpenClaw Memo — Setup Script
# Run once to initialize notes.md, digest.md, and config.env.
# Optionally installs a cron job for automatic processing.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config.env"
CONFIG_TEMPLATE="${SCRIPT_DIR}/config.example.env"
NOTES_FILE="${WORKSPACE_ROOT}/notes.md"
DIGEST_FILE="${WORKSPACE_ROOT}/digest.md"

# ── Create notes.md ───────────────────────────────────────────────────────────
if [[ ! -f "${NOTES_FILE}" ]]; then
  cat > "${NOTES_FILE}" <<'EOF'
# OpenClaw Memo Inbox

Processed entries are marked [processed] by the processor script.

### 2026-01-01 00:00
- 待办：示例待办 [processed]
EOF
  printf '✅ Created: %s\n' "${NOTES_FILE}"
else
  printf '✓  Exists:  %s\n' "${NOTES_FILE}"
fi

# ── Create digest.md ─────────────────────────────────────────────────────────
if [[ ! -f "${DIGEST_FILE}" ]]; then
  cat > "${DIGEST_FILE}" <<'EOF'
# OpenClaw Memo Digest

No digest yet. Run the processor to generate one:

    bash skills/openclaw-memo/scripts/process.sh
EOF
  printf '✅ Created: %s\n' "${DIGEST_FILE}"
else
  printf '✓  Exists:  %s\n' "${DIGEST_FILE}"
fi

# ── Create config.env ─────────────────────────────────────────────────────────
if [[ ! -f "${CONFIG_FILE}" ]]; then
  cp "${CONFIG_TEMPLATE}" "${CONFIG_FILE}"
  printf '✅ Created config: %s\n' "${CONFIG_FILE}"
  printf '   → Edit it to fill in your Feishu / Notion keys.\n'
else
  printf '✓  Config exists: %s\n' "${CONFIG_FILE}"
fi

# ── Cron setup (optional) ────────────────────────────────────────────────────
printf '\n'
read -r -p "Install cron job for automatic processing at 12:00 and 21:00? [y/N] " INSTALL_CRON
if [[ "${INSTALL_CRON,,}" == "y" ]]; then
  PROCESS_CMD="cd '${WORKSPACE_ROOT}' && python3 '${SCRIPT_DIR}/scripts/process_notes.py' --notes notes.md --digest digest.md >> /tmp/openclaw-memo.log 2>&1"
  CRON_ENTRY_12="0 12 * * * ${PROCESS_CMD}"
  CRON_ENTRY_21="0 21 * * * ${PROCESS_CMD}"

  # Add entries if not already present
  EXISTING=$(crontab -l 2>/dev/null || true)
  NEW_CRON="${EXISTING}"
  if ! echo "${EXISTING}" | grep -qF "openclaw-memo"; then
    NEW_CRON="${EXISTING}
${CRON_ENTRY_12}
${CRON_ENTRY_21}"
    echo "${NEW_CRON}" | crontab -
    printf '✅ Cron jobs installed (12:00 and 21:00 daily).\n'
  else
    printf '✓  Cron job already exists, skipping.\n'
  fi
fi

printf '\n──────────────────────────────────────────\n'
printf '  OpenClaw Memo initialized.\n'
printf '  notes:   %s\n' "${NOTES_FILE}"
printf '  digest:  %s\n' "${DIGEST_FILE}"
printf '  config:  %s\n' "${CONFIG_FILE}"
printf '\n  Next step: edit config.env, then test:\n'
printf '    bash skills/openclaw-memo/scripts/process.sh\n'
printf '──────────────────────────────────────────\n'
