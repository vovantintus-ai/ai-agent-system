"""CRM - учёт клиентов, сделок, контактов"""
import json
from pathlib import Path
from datetime import datetime

DATA = Path.home() / "ai-agent" / "data" / "crm.json"

def _load():
    try:
        if DATA.exists(): return json.loads(DATA.read_text(encoding="utf-8"))
    except: pass
    return {"clients": {}, "deals": {}, "next_id": 1}

def _save(d):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

class CRMTools:
    def add_client(self, name, email="", phone="", company="", notes="") -> str:
        d = _load()
        cid = f"C{d['next_id']:04d}"; d['next_id'] += 1
        d['clients'][cid] = {
            "id": cid, "name": name, "email": email, "phone": phone,
            "company": company, "notes": notes,
            "created": datetime.now().strftime("%Y-%m-%d"),
            "deals": [], "status": "active"
        }
        _save(d)
        return f"✅ Client added: **{name}** (ID: {cid})\n📧 {email}  📞 {phone}"

    def list_clients(self, search="") -> str:
        d = _load()
        clients = list(d['clients'].values())
        if search:
            s = search.lower()
            clients = [c for c in clients if s in c['name'].lower() or s in c.get('email','').lower() or s in c.get('company','').lower()]
        if not clients: return "📭 No clients found."
        lines = [f"👥 **Clients ({len(clients)}):**\n"]
        for c in clients[:20]:
            lines.append(f"• **{c['name']}** ({c['id']}) — {c.get('company','')}")
            if c.get('email'): lines.append(f"  📧 {c['email']}")
            if c.get('phone'): lines.append(f"  📞 {c['phone']}")
            deals = len(c.get('deals',[]))
            if deals: lines.append(f"  💼 {deals} deal(s)")
            lines.append("")
        return "\n".join(lines)

    def get_client(self, client_id_or_name) -> str:
        d = _load()
        client = d['clients'].get(client_id_or_name)
        if not client:
            for c in d['clients'].values():
                if client_id_or_name.lower() in c['name'].lower():
                    client = c; break
        if not client: return f"❌ Client not found: {client_id_or_name}"
        lines = [f"👤 **{client['name']}** ({client['id']})\n"]
        for k,v in [("Company","company"),("Email","email"),("Phone","phone"),("Notes","notes"),("Status","status"),("Created","created")]:
            if client.get(v): lines.append(f"**{k}:** {client[v]}")
        deals = [d['deals'][did] for did in client.get('deals',[]) if did in d['deals']]
        if deals:
            lines.append(f"\n💼 **Deals ({len(deals)}):**")
            for deal in deals:
                lines.append(f"  • {deal['title']} — €{deal.get('amount',0):.2f} [{deal['status']}]")
        return "\n".join(lines)

    def add_deal(self, client_id_or_name, title, amount=0, status="new", notes="") -> str:
        d = _load()
        client = d['clients'].get(client_id_or_name)
        if not client:
            for cid, c in d['clients'].items():
                if client_id_or_name.lower() in c['name'].lower():
                    client = c; client_id_or_name = cid; break
        if not client: return f"❌ Client not found: {client_id_or_name}"
        did = f"D{d['next_id']:04d}"; d['next_id'] += 1
        d['deals'][did] = {
            "id": did, "client_id": client['id'], "client_name": client['name'],
            "title": title, "amount": float(amount), "status": status,
            "notes": notes, "created": datetime.now().strftime("%Y-%m-%d")
        }
        client['deals'].append(did)
        _save(d)
        return f"✅ Deal added: **{title}**\n💰 €{float(amount):.2f} | Client: {client['name']} | Status: {status}"

    def list_deals(self, status="") -> str:
        d = _load()
        deals = list(d['deals'].values())
        if status: deals = [x for x in deals if x['status'] == status]
        if not deals: return "📭 No deals found."
        total = sum(x.get('amount',0) for x in deals)
        lines = [f"💼 **Deals ({len(deals)}) — Total: €{total:.2f}**\n"]
        for deal in deals[:20]:
            lines.append(f"• **{deal['title']}** ({deal['id']})")
            lines.append(f"  👤 {deal['client_name']} | 💰 €{deal.get('amount',0):.2f} | [{deal['status']}]")
            lines.append("")
        return "\n".join(lines)

    def update_deal_status(self, deal_id, new_status) -> str:
        d = _load()
        if deal_id not in d['deals']: return f"❌ Deal {deal_id} not found"
        d['deals'][deal_id]['status'] = new_status
        _save(d)
        return f"✅ Deal {deal_id} → **{new_status}**"

    def summary(self) -> str:
        d = _load()
        clients = list(d['clients'].values())
        deals = list(d['deals'].values())
        statuses = {}
        for deal in deals:
            s = deal['status']
            statuses[s] = statuses.get(s, 0) + deal.get('amount', 0)
        lines = ["📊 **CRM Summary**\n",
                 f"👥 Total clients: {len(clients)}",
                 f"💼 Total deals: {len(deals)}\n",
                 "**By status:**"]
        for s, amt in statuses.items():
            lines.append(f"  • {s}: €{amt:.2f}")
        won = statuses.get('won', 0)
        pipeline = sum(v for k,v in statuses.items() if k not in ('won','lost'))
        lines.append(f"\n💰 Won: €{won:.2f}")
        lines.append(f"🔄 Pipeline: €{pipeline:.2f}")
        return "\n".join(lines)
