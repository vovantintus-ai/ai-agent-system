"""
Email & Calendar Tools - Windows compatible
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
import uuid


class EmailTools:
    def send_email(self, to: str, subject: str, body: str) -> str:
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS")
        from_addr = os.getenv("EMAIL_FROM", smtp_user)

        if not all([smtp_host, smtp_user, smtp_pass]):
            return (
                "⚠️ Email not configured. Add to .env:\n"
                "SMTP_HOST=smtp.gmail.com\n"
                "SMTP_PORT=587\n"
                "SMTP_USER=your@email.com\n"
                "SMTP_PASS=your_app_password\n"
                "EMAIL_FROM=your@email.com"
            )

        try:
            msg = MIMEMultipart()
            msg['From'] = from_addr
            msg['To'] = to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(from_addr, to, msg.as_string())

            return f"✅ Email sent to {to}"
        except Exception as e:
            return f"❌ Email error: {str(e)}"

    def create_calendar_event(self, title: str, start: str, end: str, description: str = "") -> str:
        try:
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
            start_str = start_dt.strftime("%Y%m%dT%H%M%S")
            end_str = end_dt.strftime("%Y%m%dT%H%M%S")
            now_str = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            uid = str(uuid.uuid4())

            ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//AI Agent//Calendar//EN
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{now_str}
DTSTART:{start_str}
DTEND:{end_str}
SUMMARY:{title}
DESCRIPTION:{description}
END:VEVENT
END:VCALENDAR"""

            # Save to Documents\Calendar on Windows
            cal_dir = Path.home() / "Documents" / "Calendar"
            cal_dir.mkdir(parents=True, exist_ok=True)
            safe_title = "".join(c for c in title if c.isalnum() or c in " _-").strip().replace(" ", "_")
            filename = cal_dir / f"{safe_title}_{start_dt.strftime('%Y%m%d')}.ics"

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(ics)

            return (
                f"✅ Event created: {title}\n"
                f"📅 {start_dt.strftime('%d.%m.%Y %H:%M')} — {end_dt.strftime('%H:%M')}\n"
                f"📁 File: {filename}\n"
                f"Double-click the .ics file to import into Outlook / Google Calendar"
            )
        except Exception as e:
            return f"❌ Calendar error: {str(e)}"
