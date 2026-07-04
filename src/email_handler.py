import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid
from . import config

def build_outreach_message(lead):
    subject = f"Grow your business with a website for {lead['name']}"
    
    text = (
        f"Hi {lead['name'] or 'there'},\n\n"
        f"I noticed your {lead['type'] or 'business'} {f'at {lead['address']}' if lead['address'] else ''} does not yet have a website. "
        f"A simple website can help you get more local customers, improve online visibility, and make bookings easier for your guests.\n\n"
        f"I can help set up a modern, mobile-friendly website quickly and affordably. If you're interested, reply to this email and I can share a quote and examples.\n\n"
        f"Best regards,\n"
        f"{config.EMAIL_FROM.replace(chr(34), '')}\n"
    )

    html = (
        f"<p>Hi {lead['name'] or 'there'},</p>"
        f"<p>I noticed your {lead['type'] or 'business'} {f'at {lead['address']}' if lead['address'] else ''} does not yet have a website. "
        f"A simple website can help you get more local customers, improve online visibility, and make bookings easier for your guests.</p>"
        f"<p>I can help set up a modern, mobile-friendly website quickly and affordably. If you're interested, reply to this email and I can share a quote and examples.</p>"
        f"<p>Best regards,<br/>{config.EMAIL_FROM.replace(chr(34), '')}</p>"
    )

    return subject, text, html

def send_email(to_email, subject, text_content, html_content, in_reply_to=None, references=None):
    msg = MIMEMultipart("alternative")
    msg["From"] = config.EMAIL_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    
    # Generate realistic Message-ID based on SMTP_USER domain
    domain = None
    if config.SMTP_USER and "@" in config.SMTP_USER:
        domain = config.SMTP_USER.split("@")[-1]
    
    msg_id = make_msgid(domain=domain)
    msg["Message-ID"] = msg_id
    
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = references

    msg.attach(MIMEText(text_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    if config.DRY_RUN:
        print(f"[DRY RUN] Email payload to {to_email}: Subject: {subject}")
        print(f"[DRY RUN] Message-ID: {msg_id}")
        return msg_id

    if not config.SEND_EMAIL:
        print(f"[INFO] SEND_EMAIL is false. Skipping actual send to {to_email}.")
        return msg_id

    try:
        if config.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=15)
        else:
            server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15)
            server.starttls()
            
        if config.SMTP_USER and config.SMTP_PASS:
            server.login(config.SMTP_USER, config.SMTP_PASS)
            
        server.sendmail(config.EMAIL_FROM, [to_email], msg.as_string())
        server.quit()
        return msg_id
    except Exception as e:
        print(f"SMTP error sending email to {to_email}: {e}")
        raise e
