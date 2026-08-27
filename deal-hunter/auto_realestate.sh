#!/data/data/com.termux/files/usr/bin/bash
#
# Auto-run the real-estate searches (sale + rent) on a loop, every few hours,
# and keep sending to Telegram. Keep Termux open while this runs.
#
# Usage (from the deal-hunter folder), after exporting your bot secrets:
#   export TELEGRAM_TOKEN=...        # or store them in ~/.deal-hunter.env
#   export TELEGRAM_CHAT_ID=...
#   bash auto_realestate.sh          # default: every 4 hours
#   bash auto_realestate.sh 7200     # or pass seconds (7200 = 2 hours)
#
# Stop it with Ctrl-C.
cd "$(dirname "$0")"

# Load secrets from a private file if present (so you don't re-export each time).
[ -f "$HOME/.deal-hunter.env" ] && source "$HOME/.deal-hunter.env"

INTERVAL="${1:-14400}"   # seconds between rounds (default 4h)

termux-wake-lock 2>/dev/null || true
echo "[auto] real-estate loop started; interval ${INTERVAL}s. Ctrl-C to stop."

while true; do
  echo "[auto] running apartment-rental search"
  python run.py --config config.realestate-huur.yaml --telegram
  echo "[auto] sleeping ${INTERVAL}s..."
  sleep "$INTERVAL"
done
