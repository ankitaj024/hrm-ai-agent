
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.core.config import settings

def send_email(to_email: str, subject: str, body: str):
    """
    Sends an email using the configured SMTP server.
    If credentials are missing or connection fails, logs the email instead.
    """
    sender_email = "test@yopmail.com"

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
        with smtplib.SMTP(settings.SMTP_HOST, int(settings.SMTP_PORT), timeout=5) as server:
            server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(sender_email, to_email, message.as_string())
            
        print(f"EMAIL SENT: To: {to_email}, Subject: {subject}")
        return True

    except Exception as e:
        # Fallback logging for development/demo
        print(f"--------------------------------------------------")
        print(f"EMAIL SIMULATION (Failed to send real email: {e})")
        print(f"FROM: {sender_email}")
        print(f"TO: {to_email}")
        print(f"SUBJECT: {subject}")
        print(f"BODY:\n{body}")
        print(f"--------------------------------------------------")
        return False
