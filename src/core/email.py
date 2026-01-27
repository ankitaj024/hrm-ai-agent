

import smtplib
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.core.config import settings

def send_email(to_email: str, subject: str, body: str):
    """
    Sends an email using the configured SMTP server.
    If credentials are missing or connection fails, logs the email instead.
    """
    # Use the SMTP user as the sender if available, otherwise fallback (which likely won't work on prod)
    sender_email = settings.SMTP_USER if settings.SMTP_USER else "test@yopmail.com"

    try:
        # Check if SMTP config is present (Mock check)
        if not settings.SMTP_HOST or not settings.SMTP_PORT:
            raise ValueError("SMTP Configuration missing")

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = to_email
        message["Subject"] = subject

        if "<html" in body:
            message.attach(MIMEText(body, "html"))
        else:
            message.attach(MIMEText(body, "plain"))

        # Add timeout to prevent blocking for too long
        timeout_seconds = 10
        if int(settings.SMTP_PORT) == 465:
            # Use SSL for port 465, with fallback to 587
            try:
                with smtplib.SMTP_SSL(settings.SMTP_HOST, 465, timeout=timeout_seconds) as server:
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(sender_email, to_email, message.as_string())
            except OSError as e:
                # Network unreachable or other socket error, likely port blocked. Try 587.
                print(f"SMTP SSL (465) failed: {e}. Retrying with TLS (587)...")
                with smtplib.SMTP(settings.SMTP_HOST, 587, timeout=timeout_seconds) as server:
                    server.starttls()
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(sender_email, to_email, message.as_string())
        else:
            # For 587 or other ports
            with smtplib.SMTP(settings.SMTP_HOST, int(settings.SMTP_PORT), timeout=timeout_seconds) as server:
                server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(sender_email, to_email, message.as_string())
            
        print(f"EMAIL SENT: To: {to_email}, Subject: {subject}")
        return True

    except Exception as e:
        # Fallback logging for development/demo
        print(f"--------------------------------------------------")
        print(f"EMAIL FAILED (Error: {e})")
        print(traceback.format_exc()) # Print full traceback to logs
        print(f"FROM: {sender_email}")
        print(f"TO: {to_email}")
        print(f"SUBJECT: {subject}")
        print(f"BODY:\n{body}")
        print(f"--------------------------------------------------")
        return False
