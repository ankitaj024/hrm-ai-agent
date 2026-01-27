import requests
import traceback
from src.core.config import settings

def send_email(to_email: str, subject: str, body: str):
    """
    Sends an email using the Resend API (HTTP).
    This bypasses port blocking issues on Render/Cloud platforms.
    """
    api_key = settings.RESEND_API_KEY
    if not api_key:
        print("--------------------------------------------------")
        print("EMAIL SKIPPED: RESEND_API_KEY not set.")
        print(f"TO: {to_email}")
        print(f"SUBJECT: {subject}")
        print("--------------------------------------------------")
        return False

    url = "https://api.resend.com/emails"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Resend requires a verified domain or uses 'onboarding@resend.dev' for testing (only to verified email)
    from_email = settings.RESEND_FROM_EMAIL if settings.RESEND_FROM_EMAIL else "onboarding@resend.dev"
    
    # DEV/TEST OVERRIDE: Resend Free Tier only allows sending TO the verified email.
    if settings.RESEND_TEST_RECIPIENT:
        print(f"DEBUG: Redirecting email for {to_email} to verified recipient {settings.RESEND_TEST_RECIPIENT}")
        subject = f"[TEST -> {to_email}] {subject}"
        to_email = settings.RESEND_TEST_RECIPIENT
    
    payload = {
        "from": f"HR AI Agent <{from_email}>",
        "to": [to_email],
        "subject": subject,
        "html": body
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code in [200, 201]:
            print(f"EMAIL SENT via Resend API: To: {to_email} | ID: {response.json().get('id')}")
            return True
        else:
            print(f"--------------------------------------------------")
            print(f"EMAIL FAILED (Resend API Error: {response.status_code})")
            print(response.text)
            print(f"TO: {to_email}")
            print(f"SUBJECT: {subject}")
            print(f"--------------------------------------------------")
            return False

    except Exception as e:
        print(f"--------------------------------------------------")
        print(f"EMAIL FAILED (Exception: {str(e)})")
        print(traceback.format_exc())
        print(f"TO: {to_email}")
        print(f"--------------------------------------------------")
        return False
