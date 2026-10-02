import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr

logger = logging.getLogger(__name__)


def mail_configured():
    return bool(
        os.environ.get("MAIL_SERVER")
        and os.environ.get("MAIL_USERNAME")
        and os.environ.get("MAIL_PASSWORD")
    )


def send_email(to_email, subject, html_body, text_body=None):
    """Envia e-mail via SMTP. Retorna True se enviou."""
    server = (os.environ.get("MAIL_SERVER") or "").strip()
    username = (os.environ.get("MAIL_USERNAME") or "").strip()
    password = os.environ.get("MAIL_PASSWORD") or ""
    from_raw = (os.environ.get("MAIL_FROM") or username).strip()
    port = int(os.environ.get("MAIL_PORT") or 587)
    use_tls = (os.environ.get("MAIL_USE_TLS") or "true").lower() in ("1", "true", "yes")

    if not server or not username or not password:
        logger.error("E-mail não configurado (verifique MAIL_SERVER, MAIL_USERNAME e MAIL_PASSWORD).")
        return False

    from_name, from_addr = parseaddr(from_raw)
    if not from_addr:
        from_addr = username
    if not from_name:
        from_name = "NutriTrack"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr((from_name, from_addr))
    msg["To"] = to_email
    msg.attach(MIMEText(text_body or "Abra este e-mail em um cliente que suporte HTML.", "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(server, port, timeout=20) as smtp:
            smtp.ehlo()
            if use_tls:
                smtp.starttls()
                smtp.ehlo()
            smtp.login(username, password)
            smtp.sendmail(from_addr, [to_email], msg.as_string())
        return True
    except Exception:
        logger.exception("Falha ao enviar e-mail para %s", to_email)
        return False
