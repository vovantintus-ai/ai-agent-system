#!/data/data/com.termux/files/usr/bin/bash
# Push the latest rental digest to GitHub so it can be reviewed remotely.
# Requires the repo's git remote to be authenticated (token in the URL).
set -e
cd "$(dirname "$0")"
REPO_ROOT="$(git rev-parse --show-toplevel)"
mkdir -p "$REPO_ROOT/deal-hunter/reports"

# Copy the latest digest (written to $HOME by run.py) into the repo.
if [ -f "$HOME/re-huur-latest.md" ]; then
  cp "$HOME/re-huur-latest.md" "$REPO_ROOT/deal-hunter/reports/latest-huur.md"
fi

cd "$REPO_ROOT"
git add deal-hunter/reports/latest-huur.md 2>/dev/null || true
if git diff --cached --quiet; then
  echo "[report] no change to report"
  exit 0
fi
STAMP="$(date -u +%Y-%m-%dT%H:%MZ 2>/dev/null || echo now)"
git -c user.email=phone@local -c user.name="phone" \
    commit -q -m "report: rental digest $STAMP"
git pull --rebase --autostash origin master >/dev/null 2>&1 || true
git push origin master && echo "[report] pushed digest to GitHub" \
  || echo "[report] push failed (check the GitHub token on the remote URL)"
