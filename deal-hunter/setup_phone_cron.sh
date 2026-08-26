#!/data/data/com.termux/files/usr/bin/bash
#
# One-time setup: make Deal Hunter run itself on this Android phone (Termux)
# every 4 hours and send results to your Telegram bot. Run it once:
#
#     bash setup_phone_cron.sh
#
# It asks for your bot token + chat id ONCE, stores them in a private local
# file (~/.deal-hunter.env, not in the repo), installs cron, schedules the run,
# and starts the scheduler.
set -e
cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"
ENV_FILE="$HOME/.deal-hunter.env"
RUNNER="$HOME/deal-hunter-run.sh"
LOG="$HOME/deal-hunter.log"

echo "== Deal Hunter phone auto-setup =="

# 1) Secrets — asked once, kept locally, never committed.
if [ ! -f "$ENV_FILE" ]; then
  printf "Telegram BOT TOKEN: "
  read -r TOK
  printf "Telegram CHAT ID:  "
  read -r CHAT
  printf 'export TELEGRAM_TOKEN=%s\nexport TELEGRAM_CHAT_ID=%s\n' "$TOK" "$CHAT" > "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  echo "Saved secrets to $ENV_FILE"
else
  echo "Using existing secrets in $ENV_FILE"
fi

# 2) Install cron + services (quiet; ignore if already there).
echo "Installing scheduler (cronie)..."
pkg install -y cronie termux-services termux-api >/dev/null 2>&1 || true

# 3) The runner the scheduler calls each time.
cat > "$RUNNER" <<RUN
#!/data/data/com.termux/files/usr/bin/bash
source "$ENV_FILE"
cd "$PROJECT_DIR"
termux-wake-lock 2>/dev/null || true
python run.py --config config.electronics.yaml --telegram >> "$LOG" 2>&1
termux-wake-unlock 2>/dev/null || true
RUN
chmod +x "$RUNNER"
echo "Runner: $RUNNER"

# 4) Schedule every 4 hours (replace any previous entry).
( crontab -l 2>/dev/null | grep -v 'deal-hunter-run.sh' ; \
  echo "0 */4 * * * $RUNNER" ) | crontab -
echo "Scheduled: every 4 hours."

# 5) Start the scheduler.
sv-enable crond 2>/dev/null || true
sv up crond 2>/dev/null || crond 2>/dev/null || true

echo ""
echo "Done. Deal Hunter will run every 4 hours and send new electronics deals"
echo "to your Telegram bot. Log: $LOG"
echo "To change what it hunts, edit config.electronics.yaml (the query lines)."
echo "To run it right now once:  bash $RUNNER"
