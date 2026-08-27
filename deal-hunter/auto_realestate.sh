#!/data/data/com.termux/files/usr/bin/bash
#
# Auto-run on a loop with SEPARATE intervals:
#   * JOBS       every 2 hours
#   * APARTMENTS every 3 hours
# Ticks once per hour. Keep Termux open while this runs. Stop with Ctrl-C.
#
# Usage (after exporting your bot secrets, or storing them in ~/.deal-hunter.env):
#   bash auto_realestate.sh
cd "$(dirname "$0")"

[ -f "$HOME/.deal-hunter.env" ] && source "$HOME/.deal-hunter.env"

TICK=3600          # 1 hour
JOBS_EVERY=2       # hours
APTS_EVERY=3       # hours

termux-wake-lock 2>/dev/null || true
echo "[auto] started — jobs every ${JOBS_EVERY}h, apartments every ${APTS_EVERY}h. Ctrl-C to stop."

h=0
while true; do
  if (( h % JOBS_EVERY == 0 )); then
    echo "[auto] jobs search (h=${h})"
    python run.py --config config.jobs.yaml --telegram --photos
  fi
  if (( h % APTS_EVERY == 0 )); then
    echo "[auto] apartment-rental search (h=${h})"
    python run.py --config config.realestate-huur.yaml --telegram --photos
    bash report_to_github.sh || true
  fi
  h=$(( h + 1 ))
  echo "[auto] sleeping ${TICK}s..."
  sleep "$TICK"
done
