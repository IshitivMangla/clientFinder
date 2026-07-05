import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid
from . import config

def build_outreach_message(lead):
    lead_name = lead.get("name", "there")
    lead_type = lead.get("type", "business").lower()
    lead_address = lead.get("address", "")
    
    # Determine type label
    is_hotel = any(kw in lead_type for kw in ["hotel", "lodging", "motel", "inn"])
    type_label = "hotel" if is_hotel else "restaurant"
    
    # Customize the featured image and template details based on type
    if is_hotel:
        featured_img = "https://images.unsplash.com/photo-1566073771259-6a8506099945?q=80&w=600&auto=format&fit=crop"
        preview_title = "Modern Boutique Hotel Website Layout"
        mockup_desc = "Complete room booking integration, interactive gallery, and customer review portal."
    else:
        featured_img = "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?q=80&w=600&auto=format&fit=crop"
        preview_title = "Sleek Gourmet Restaurant Website Layout"
        mockup_desc = "Interactive digital menu, reservation system, and location-based SEO setup."

    subject = f"Premium Custom Website Design for {lead_name}"
    
    text = (
        f"Hi {lead_name},\n\n"
        f"I recently came across your {type_label} and noticed you don't have an active website online. "
        f"In today's digital landscape, over 80% of customers research menus, rooms, and booking options online before visiting.\n\n"
        f"I specialize in building premium, high-converting websites specifically for local businesses. "
        f"I've attached a link/preview to some of our latest restaurant/hotel website designs. We can build a custom, mobile-friendly site for you that includes booking systems, interactive maps, and beautiful menus.\n\n"
        f"If you are interested, reply to this email. I'd love to share a few design drafts and a quick quote.\n\n"
        f"Best regards,\n"
        f"{config.EMAIL_FROM.replace(chr(34), '')}\n"
    )

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            background-color: #f3f4f6;
            color: #1f2937;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
            border: 1px solid #e5e7eb;
        }}
        .header {{
            background: linear-gradient(135deg, #4f46e5, #6366f1);
            color: #ffffff;
            padding: 40px 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }}
        .content {{
            padding: 30px;
            line-height: 1.6;
        }}
        .content p {{
            font-size: 16px;
            margin-bottom: 20px;
        }}
        .showcase {{
            background-color: #f9fafb;
            border: 1px solid #f3f4f6;
            border-radius: 12px;
            padding: 20px;
            margin: 30px 0;
            text-align: center;
        }}
        .showcase-image {{
            width: 100%;
            max-height: 250px;
            object-fit: cover;
            border-radius: 8px;
            margin-bottom: 15px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        }}
        .showcase-title {{
            font-size: 18px;
            font-weight: 600;
            color: #111827;
            margin-bottom: 5px;
        }}
        .showcase-desc {{
            font-size: 14px;
            color: #6b7280;
            margin-bottom: 0;
        }}
        .footer {{
            background-color: #f9fafb;
            padding: 24px 30px;
            text-align: center;
            font-size: 14px;
            color: #6b7280;
            border-top: 1px solid #e5e7eb;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Custom Digital Presence for {lead_name}</h1>
        </div>
        <div class="content">
            <p>Hi {lead_name},</p>
            <p>I recently came across your {type_label} {f'located at {lead_address}' if lead_address else ''} and noticed that you don't have an active website online.</p>
            <p>In today's market, <strong>over 80% of customers</strong> check menus, photos, and room availability online before deciding to visit in person. Having a stunning, mobile-friendly website is one of the most effective ways to capture new customers and streamline bookings.</p>
            
            <div class="showcase">
                <img class="showcase-image" src="{featured_img}" alt="{preview_title}" />
                <div class="showcase-title">{preview_title}</div>
                <p class="showcase-desc">{mockup_desc}</p>
            </div>
            
            <p>I specialize in building custom websites tailored specifically for local hospitality businesses. I can build a modern website for your {type_label} that features:</p>
            <ul style="padding-left: 20px; font-size: 15px; margin-bottom: 25px;">
                <li>Interactive menus or room booking lists</li>
                <li>Sleek, responsive design (looks beautiful on mobile)</li>
                <li>Google Maps integration and local SEO setup</li>
                <li>Fast load speeds & SSL security</li>
            </ul>
            
            <p>If you're interested in learning more, simply reply to this email! I can share some custom design ideas and provide a free quote.</p>
            
            <p>Best regards,<br/><strong>{config.EMAIL_FROM.replace(chr(34), '')}</strong></p>
        </div>
        <div class="container-footer" style="background-color: #f9fafb; padding: 24px 30px; text-align: center; font-size: 14px; color: #6b7280; border-top: 1px solid #e5e7eb;">
            <p>This message was sent to {lead.get('email')}. If you wish to opt-out, please reply "STOP".</p>
        </div>
    </div>
</body>
</html>"""
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
