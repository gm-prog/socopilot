#!/usr/bin/env bash
# Delete the five stale branches that still root the pre-purge (token-bearing)
# history on GitHub. Run this from any machine with a valid GitHub login:
#
#   gh auth login                      # once, if not already authenticated
#   ./scripts/delete-stale-branches.sh          # interactive: asks per branch
#   ./scripts/delete-stale-branches.sh --yes    # delete all five, no prompts
#
# Context (docs/SECURITY_RUNBOOK.md §4, development report §8.2):
#   main's history was rewritten with git filter-repo to remove
#   frontend/public/token.txt; master was deleted. These five branches were
#   NOT rewritten, so the old commits (and the token file inside them) remain
#   reachable from them. Deleting the branches orphans that history on
#   GitHub's side (cached refs/pull/1..4 still need a Support ticket —
#   see docs/GITHUB_SUPPORT_TICKET.md).
set -euo pipefail

REPO="gm-prog/socopilot"
ASSUME_YES=false
[[ "${1:-}" == "--yes" ]] && ASSUME_YES=true

BRANCHES=(
  "devin/1780897696-add-unit-tests"
  "devin/1780897699-improve-error-handling"
  "devin/1780897707-refactor-shared-utilities"
  "devin/1780897712-security-hardening"
  "alerts-page-store-migration"
)

command -v gh >/dev/null || { echo "error: gh CLI not installed"; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "error: not authenticated — run 'gh auth login' first"; exit 1; }

echo "About to delete stale branches from ${REPO}:"
for b in "${BRANCHES[@]}"; do
  echo "  - $b"
done
echo
echo "⚠  alerts-page-store-migration carries ~94 files of diverged alternative"
echo "   work (superseded by main, never CI-tested). Deleting it forfeits that"
echo "   rewrite in exchange for a fully clean history."
if $ASSUME_YES; then
  echo "--yes given: proceeding without prompts."
else
  read -r -p "Delete ALL of the above? [y/N] " reply
  [[ "$reply" == "y" || "$reply" == "Y" ]] || { echo "aborted."; exit 1; }
fi

FAILED=0
for b in "${BRANCHES[@]}"; do
  if gh api -X DELETE "repos/${REPO}/git/refs/heads/${b}" >/dev/null 2>&1; then
    echo "deleted: $b"
  else
    echo "FAILED (may already be gone): $b"
    FAILED=1
  fi
done

echo
echo "Done. Remaining step for a fully orphaned history: the GitHub Support"
echo "ticket in docs/GITHUB_SUPPORT_TICKET.md (cached refs/pull/1..4)."
exit $FAILED
