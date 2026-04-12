"""Финансовый трекер — доходы, расходы, отчёты"""
import json
from pathlib import Path
from datetime import datetime, date

DATA = Path.home() / "ai-agent" / "data" / "finance.json"

CATEGORIES = {
    "income": ["salary","freelance","sales","investment","other_income"],
    "expense": ["food","transport","housing","software","marketing","salary_out","taxes","equipment","other"]
}

def _load():
    try:
        if DATA.exists(): return json.loads(DATA.read_text(encoding="utf-8"))
    except: pass
    return {"transactions": [], "next_id": 1, "currency": "EUR"}

def _save(d):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

class FinanceTools:
    def add_income(self, amount: float, description: str, category="other_income") -> str:
        d = _load()
        d['transactions'].append({
            "id": d['next_id'], "type": "income", "amount": float(amount),
            "description": description, "category": category,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "month": datetime.now().strftime("%Y-%m")
        })
        d['next_id'] += 1
        _save(d)
        return f"✅ Income: +€{float(amount):.2f} — {description}"

    def add_expense(self, amount: float, description: str, category="other") -> str:
        d = _load()
        d['transactions'].append({
            "id": d['next_id'], "type": "expense", "amount": float(amount),
            "description": description, "category": category,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "month": datetime.now().strftime("%Y-%m")
        })
        d['next_id'] += 1
        _save(d)
        return f"✅ Expense: -€{float(amount):.2f} — {description}"

    def monthly_report(self, month: str = None) -> str:
        d = _load()
        if not month: month = datetime.now().strftime("%Y-%m")
        txs = [t for t in d['transactions'] if t.get('month') == month]
        if not txs: return f"📭 No transactions for {month}"
        income = sum(t['amount'] for t in txs if t['type'] == 'income')
        expense = sum(t['amount'] for t in txs if t['type'] == 'expense')
        profit = income - expense

        # Group expenses by category
        by_cat = {}
        for t in txs:
            if t['type'] == 'expense':
                cat = t.get('category','other')
                by_cat[cat] = by_cat.get(cat, 0) + t['amount']

        lines = [f"📈 **Report: {month}**\n",
                 f"💚 Income:  €{income:.2f}",
                 f"💸 Expense: €{expense:.2f}",
                 f"{'✅' if profit>=0 else '❌'} Profit:  €{profit:.2f}\n",
                 "**Expenses by category:**"]
        for cat, amt in sorted(by_cat.items(), key=lambda x: -x[1]):
            pct = (amt/expense*100) if expense else 0
            lines.append(f"  • {cat}: €{amt:.2f} ({pct:.0f}%)")
        return "\n".join(lines)

    def balance(self) -> str:
        d = _load()
        income = sum(t['amount'] for t in d['transactions'] if t['type'] == 'income')
        expense = sum(t['amount'] for t in d['transactions'] if t['type'] == 'expense')
        profit = income - expense

        # This month
        month = datetime.now().strftime("%Y-%m")
        m_income = sum(t['amount'] for t in d['transactions'] if t['type']=='income' and t.get('month')==month)
        m_expense = sum(t['amount'] for t in d['transactions'] if t['type']=='expense' and t.get('month')==month)

        return (f"💰 **Financial Balance**\n\n"
                f"**All time:**\n"
                f"  Income:  €{income:.2f}\n"
                f"  Expense: €{expense:.2f}\n"
                f"  Profit:  €{profit:.2f}\n\n"
                f"**This month ({month}):**\n"
                f"  Income:  €{m_income:.2f}\n"
                f"  Expense: €{m_expense:.2f}\n"
                f"  Profit:  €{m_income-m_expense:.2f}")

    def recent_transactions(self, n=10) -> str:
        d = _load()
        txs = sorted(d['transactions'], key=lambda x: x['date'], reverse=True)[:n]
        if not txs: return "📭 No transactions yet."
        lines = [f"📋 **Last {len(txs)} transactions:**\n"]
        for t in txs:
            icon = "💚" if t['type'] == 'income' else "💸"
            sign = "+" if t['type'] == 'income' else "-"
            lines.append(f"{icon} {t['date']}  {sign}€{t['amount']:.2f}  {t['description']}")
        return "\n".join(lines)

    def yearly_summary(self) -> str:
        d = _load()
        year = str(datetime.now().year)
        txs = [t for t in d['transactions'] if t.get('date','').startswith(year)]
        by_month = {}
        for t in txs:
            m = t.get('month', t['date'][:7])
            if m not in by_month: by_month[m] = {'income':0,'expense':0}
            by_month[m][t['type']] += t['amount']
        lines = [f"📊 **{year} Summary**\n"]
        total_i = total_e = 0
        for m in sorted(by_month.keys()):
            i = by_month[m]['income']
            e = by_month[m]['expense']
            p = i - e
            total_i += i; total_e += e
            lines.append(f"**{m}**: +€{i:.2f} / -€{e:.2f} = €{p:+.2f}")
        lines.append(f"\n**Total: +€{total_i:.2f} / -€{total_e:.2f} = €{total_i-total_e:+.2f}**")
        return "\n".join(lines)
