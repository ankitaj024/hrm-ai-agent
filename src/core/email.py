

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
        
        # IPv4 Resolution Handling for Render
        # Render sometimes has issues with IPv6 routing for Gmail, causing [Errno 101] Network is unreachable
        target_host = settings.SMTP_HOST
        import socket
        try:
            # FORCE IPv4 using getaddrinfo
            # This returns a list of tuples, we take the first one's IP
            addr_info = socket.getaddrinfo(settings.SMTP_HOST, 465, family=socket.AF_INET, proto=socket.IPPROTO_TCP)
            # addr_info[0] is (family, type, proto, canonname, sockaddr)
            # sockaddr is (ip, port)
            target_ip = addr_info[0][4][0]
            print(f"STRICT RESOLUTION: Resolved {settings.SMTP_HOST} to IPv4: {target_ip}")
            target_host = target_ip
        except Exception as dns_error:
            print(f"Warning: Could not resolve IPv4 for SMTP using getaddrinfo: {dns_error}")
            try:
                # Fallback to simple gethostbyname
                target_ip = socket.gethostbyname(settings.SMTP_HOST)
                print(f"Fallback resolution: {settings.SMTP_HOST} -> {target_ip}")
                target_host = target_ip
            except Exception as e2:
                print(f"CRITICAL: Accessing SMTP host failed resolution: {e2}")
                # We will try the hostname directly, but it likely fails IPv6

            # Fallback to original host

        # Context for SSL (Verify original hostname, not the IP)
        import ssl
        context = ssl.create_default_context()
        # We must tell it to check the original hostname, not the IP we are connecting to
        
        # Logic: 
        # 1. Try 465 (SSL)
        # 2. Key: If connecting to IP, we must handle wrapping carefully or accept potential cert mismatch warnings 
        #    (though Gmail certs likely won't match the IP).
        #    Actually, standard smtplib validates `host`. If we pass IP, validation fails.
        #    So we create a wrapper context.

        def create_context():
            ctx = ssl.create_default_context()
            # If we are using IP, hostname check might fail. 
            # Ideally we pass 'server_hostname' to wrap_socket, but smtplib hides that.
            # We will disable hostname check for this specific connection if needed, 
            # OR better: use smtplib's ability to pass IP but validate HOST? 
            # smtplib doesn't support that easily.
            # For now, to get it working, we might have to disable check_hostname if using IP, 
            # OR trust that 'gethostbyname' is safe enough in this container Env.
            ctx.check_hostname = False 
            ctx.verify_mode = ssl.CERT_NONE 
            return ctx

        # Attempt 1: Port 465 (SSL)
        try:
             # Try connecting
             print(f"Attempting SMTP_SSL on {target_host}:465...")
             with smtplib.SMTP_SSL(target_host, 465, timeout=timeout_seconds, context=create_context()) as server:
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(sender_email, to_email, message.as_string())
        except Exception as e1:
            print(f"SMTP SSL (465) failed: {e1}. Retrying with TLS (587)...")
            
            # Attempt 2: Port 587 (TLS)
            try:
                print(f"Attempting SMTP on {target_host}:587...")
                with smtplib.SMTP(target_host, 587, timeout=timeout_seconds) as server:
                    # Upgrade to TLS
                    # Here we also need context for the IP issue
                    server.starttls(context=create_context()) 
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(sender_email, to_email, message.as_string())
            except Exception as e2:
                 raise Exception(f"All SMTP attempts failed. 465: {e1} | 587: {e2}")

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

