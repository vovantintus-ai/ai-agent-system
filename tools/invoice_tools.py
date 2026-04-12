"""Генерация счётов и коммерческих предложений"""
import json
from pathlib import Path
from datetime import datetime, timedelta

DATA = Path.home() / "ai-agent" / "data" / "invoices.json"
OUT_DIR = Path.home() / "ai-agent" / "invoices"

def _load():
    try:
        if DATA.exists(): return json.loads(DATA.read_text(encoding="utf-8"))
    except: pass
    return {"invoices": {}, "next_num": 1, "company": {}}

def _save(d):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

class InvoiceTools:
    def set_company(self, name, address="", email="", phone="", iban="", kvk="", btw="") -> str:
        d = _load()
        d['company'] = {"name":name,"address":address,"email":email,
                        "phone":phone,"iban":iban,"kvk":kvk,"btw":btw}
        _save(d)
        return f"✅ Company saved: **{name}**"

    def create_invoice(self, client_name: str, client_email: str,
                       items: list, due_days: int = 14) -> str:
        """items = [{'desc': '...', 'qty': 1, 'price': 100.0}]"""
        d = _load()
        num = f"INV-{datetime.now().year}-{d['next_num']:04d}"
        d['next_num'] += 1
        subtotal = sum(i.get('qty',1) * i.get('price',0) for i in items)
        btw_pct = 21
        btw_amt = subtotal * btw_pct / 100
        total = subtotal + btw_amt
        due = (datetime.now() + timedelta(days=due_days)).strftime("%Y-%m-%d")

        inv = {
            "number": num, "client_name": client_name, "client_email": client_email,
            "items": items, "subtotal": subtotal, "btw_pct": btw_pct,
            "btw_amt": btw_amt, "total": total,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "due": due, "status": "sent",
            "company": d.get('company', {})
        }
        d['invoices'][num] = inv
        _save(d)

        # Generate text invoice
        txt = self._render_invoice(inv)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUT_DIR / f"{num}.txt"
        out_path.write_text(txt, encoding="utf-8")

        return (f"✅ Invoice created: **{num}**\n"
                f"👤 Client: {client_name}\n"
                f"💰 Total: €{total:.2f} (incl. {btw_pct}% BTW)\n"
                f"📅 Due: {due}\n"
                f"📄 Saved: {out_path}")

    def _render_invoice(self, inv) -> str:
        co = inv.get('company', {})
        lines = [
            "=" * 60,
            f"FACTUUR / INVOICE",
            "=" * 60,
            f"Nummer:  {inv['number']}",
            f"Datum:   {inv['date']}",
            f"Vervalt: {inv['due']}",
            "",
        ]
        if co.get('name'):
            lines += [f"VAN: {co['name']}", co.get('address',''),
                      co.get('email',''), co.get('phone',''),
                      f"IBAN: {co.get('iban','')}", f"KVK: {co.get('kvk','')}", f"BTW: {co.get('btw','')}",""]
        lines += [f"AAN: {inv['client_name']}", inv['client_email'], "", "-" * 60,
                  f"{'Omschrijving':<35} {'Qty':>5} {'Prijs':>8} {'Totaal':>8}", "-" * 60]
        for item in inv['items']:
            qty = item.get('qty',1)
            price = item.get('price',0)
            lines.append(f"{item.get('desc',''):<35} {qty:>5} {price:>8.2f} {qty*price:>8.2f}")
        lines += ["-"*60,
                  f"{'Subtotaal':<49} {inv['subtotal']:>8.2f}",
                  f"{'BTW ' + str(inv['btw_pct']) + '%':<49} {inv['btw_amt']:>8.2f}",
                  "=" * 60,
                  f"{'TOTAAL':<49} {inv['total']:>8.2f}",
                  "=" * 60,
                  f"\nBetaling: {inv['due']}",
                  f"IBAN: {co.get('iban','')}"]
        return "\n".join(lines)

    def create_quote(self, client_name: str, items: list, valid_days=30) -> str:
        """Create commercial proposal / offerte"""
        subtotal = sum(i.get('qty',1)*i.get('price',0) for i in items)
        btw = subtotal * 0.21
        total = subtotal + btw
        valid = (datetime.now() + timedelta(days=valid_days)).strftime("%Y-%m-%d")
        d = _load()
        num = f"OFF-{datetime.now().year}-{d['next_num']:04d}"
        d['next_num'] += 1
        _save(d)

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        co = d.get('company',{})
        lines = ["="*60, "OFFERTE / QUOTATION", "="*60,
                 f"Nummer: {num}", f"Datum: {datetime.now().strftime('%Y-%m-%d')}",
                 f"Geldig tot: {valid}", f"Voor: {client_name}", "",
                 f"{'Omschrijving':<35}{'Qty':>5}{'Prijs':>8}{'Totaal':>8}", "-"*60]
        for item in items:
            qty=item.get('qty',1); price=item.get('price',0)
            lines.append(f"{item.get('desc',''):<35}{qty:>5}{price:>8.2f}{qty*price:>8.2f}")
        lines += ["-"*60, f"{'Subtotaal':<49}{subtotal:>8.2f}",
                  f"{'BTW 21%':<49}{btw:>8.2f}", "="*60,
                  f"{'TOTAAL':<49}{total:>8.2f}", "="*60]
        path = OUT_DIR / f"{num}.txt"
        path.write_text("\n".join(lines), encoding="utf-8")
        return (f"✅ Quote created: **{num}**\n"
                f"👤 {client_name}\n💰 €{total:.2f}\n📅 Valid until: {valid}\n📄 {path}")

    def list_invoices(self) -> str:
        d = _load()
        invs = list(d['invoices'].values())
        if not invs: return "📭 No invoices yet."
        total = sum(i['total'] for i in invs)
        paid = sum(i['total'] for i in invs if i.get('status')=='paid')
        lines = [f"🧾 **Invoices ({len(invs)}) — Total: €{total:.2f}**",
                 f"✅ Paid: €{paid:.2f} | ⏳ Outstanding: €{total-paid:.2f}\n"]
        for inv in sorted(invs, key=lambda x: x['date'], reverse=True)[:15]:
            icon = "✅" if inv.get('status')=='paid' else "⏳"
            lines.append(f"{icon} **{inv['number']}** — {inv['client_name']} — €{inv['total']:.2f} — due {inv['due']}")
        return "\n".join(lines)

    def mark_paid(self, invoice_num: str) -> str:
        d = _load()
        if invoice_num not in d['invoices']: return f"❌ Invoice {invoice_num} not found"
        d['invoices'][invoice_num]['status'] = 'paid'
        d['invoices'][invoice_num]['paid_date'] = datetime.now().strftime("%Y-%m-%d")
        _save(d)
        amt = d['invoices'][invoice_num]['total']
        return f"✅ Invoice {invoice_num} marked as PAID — €{amt:.2f}"
