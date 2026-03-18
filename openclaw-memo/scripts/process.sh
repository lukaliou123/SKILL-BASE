#!/usr/bin/env bash
# OpenClaw Memo — Process Script
# Wrapper around process_notes.py that loads config.env automatically.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORKSPACE_ROOT="$(cd "${SKILL_DIR}/../.." && pwd)"
CONFIG_FILE="${SKILL_DIR}/config.env"

# Load config if present
if [[ -f "${CONFIG_FILE}" ]]; then
  # shellcheck disable=SC1090
  set -a
  source "${CONFIG_FILE}"
  set +a
fi

NOTES_FILE="${WORKSPACE_ROOT}/${OPENCLAW_MEMO_NOTES_FILE:-notes.md}"
DIGEST_FILE="${WORKSPACE_ROOT}/${OPENCLAW_MEMO_DIGEST_FILE:-digest.md}"
STORAGE_TARGET="${OPENCLAW_MEMO_STORAGE_TARGET:-local}"
ENRICH="${OPENCLAW_MEMO_ENRICH:-0}"

ENRICH_FLAG=""
if [[ "${ENRICH}" == "1" || "${ENRICH}" == "true" ]]; then
  ENRICH_FLAG="--enrich"
fi

python3 "${SCRIPT_DIR}/process_notes.py" \
  --notes "${NOTES_FILE}" \
  --digest "${DIGEST_FILE}" \
  --target "${STORAGE_TARGET}" \
  ${ENRICH_FLAG}
