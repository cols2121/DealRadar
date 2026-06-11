import os
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from digest.renderer import render_email_html


def send_email_digest(
    candidates: list[dict],
    run_stats: dict,
    to_addresses: list[str],
) -> bool:
    """
    Send email digest. Uses Resend if RESEND_API_KEY is set, else SMTP.
    Returns True if sent, False if skipped (no config).
    """
    if not to_addresses:
        return False

    subject = (
        f"DealRadar — {date.today().strftime('%d %b %Y')} "
        f"| Top {len(candidates)} pre-seed signals"
    )
    html = render_email_html(candidates, run_stats)

    resend_key = os.environ.get("RESEND_API_KEY")
    if resend_key:
        return _send_via_resend(resend_key, to_addresses, subject, html)

    smtp_host = os.environ.get("SMTP_HOST")
    if smtp_host:
        return _send_via_smtp(smtp_host, to_addresses, subject, html)

    return False


def _send_via_resend(
    api_key: str,
    to_addresses: list[str],
    subject: str,
    html: str,
) -> bool:
    import httpx

    r = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "from": "DealRadar <digest@dealradar.dev>",
            "to": to_addresses,
            "subject": subject,
            "html": html,
        },
        timeout=15,
    )
    r.raise_for_status()
    return True


def _send_via_smtp(
    host: str,
    to_addresses: list[str],
    subject: str,
    html: str,
) -> bool:
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASS", "")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = user or "dealradar@localhost"
    msg["To"] = ", ".join(to_addresses)
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(host, port) as smtp:
        smtp.ehlo()
        smtp.starttls()
        if user and password:
            smtp.login(user, password)
        smtp.sendmail(msg["From"], to_addresses, msg.as_string())

    return True
