#!/data/data/com.termux/files/usr/bin/bash
# Chooser: pick what to hunt, then send results (photos) to Telegram.
#   bash hunt.sh          # asks 1=apartments / 2=jobs
#   bash hunt.sh 1        # apartments directly
#   bash hunt.sh 2        # jobs directly
cd "$(dirname "$0")"
[ -f "$HOME/.deal-hunter.env" ] && source "$HOME/.deal-hunter.env"

CHOICE="$1"
if [ -z "$CHOICE" ]; then
  echo "Что искать?"
  echo "  1 = Квартиры (аренда)"
  echo "  2 = Работа — Marktplaats (vacatures)"
  echo "  3 = Работа — Indeed.nl"
  printf "Выбор [1/2/3]: "
  read -r CHOICE
fi

case "$CHOICE" in
  1) python run.py --config config.realestate-huur.yaml --telegram --photos --print ;;
  2) python run.py --config config.jobs.yaml --telegram --photos --print ;;
  3) python run.py --config config.jobs-indeed.yaml --telegram --print ;;
  *) echo "Введите 1, 2 или 3." ; exit 1 ;;
esac
