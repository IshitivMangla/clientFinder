import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid
from . import config

def build_outreach_message(lead, template_type="no_website"):
    lead_name    = lead.get("name", "there")
    lead_type    = lead.get("type", "business").lower()
    lead_address = lead.get("address", "")
    
    is_hotel   = any(kw in lead_type for kw in ["hotel", "lodging", "motel", "inn"])
    type_label = "hotel" if is_hotel else "restaurant"

    # ── Image set ──────────────────────────────────────────────────
    if is_hotel:
        hero_img    = "https://images.unsplash.com/photo-1566073771259-6a8506099945?q=90&w=700&auto=format&fit=crop"
        feature_img = "https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?q=80&w=700&auto=format&fit=crop"
        extra_img   = "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?q=80&w=700&auto=format&fit=crop"
        hero_alt    = "Luxury hotel lobby"
        preview_title   = "Luxury Hotel Website Design"
        preview_caption = "Full room booking engine · Interactive gallery · Guest reviews · Direct reservation system"
        cta_color   = "#0f766e"
        accent      = "#0d9488"
        type_emoji  = "🏨"
        features = [
            "🛎 Online room booking & availability calendar",
            "📸 Full-screen photo gallery with virtual tours",
            "⭐ Guest reviews & testimonials section",
            "📍 Interactive map & local attractions guide",
            "📱 Mobile-first responsive design",
            "🔒 SSL security & fast load speeds",
        ]
    else:
        hero_img    = "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?q=90&w=700&auto=format&fit=crop"
        feature_img = "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?q=80&w=700&auto=format&fit=crop"
        extra_img   = "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?q=80&w=700&auto=format&fit=crop"
        hero_alt    = "Elegant restaurant dining room"
        preview_title   = "Premium Restaurant Website Design"
        preview_caption = "Digital menu · Table reservations · Online ordering · Local SEO setup"
        cta_color   = "#7c3aed"
        accent      = "#8b5cf6"
        type_emoji  = "🍽"
        features = [
            "🍴 Interactive digital menu with photos & prices",
            "📅 Online table reservation system",
            "🛵 Online ordering & delivery integration",
            "📸 Professional food photography gallery",
            "📍 Google Maps & local SEO optimization",
            "📱 Mobile-first responsive design",
        ]

    subject = f"Your {type_label.title()} Deserves a Premium Website — Free Design Preview"

    # ── Plain text version ─────────────────────────────────────────
    text = (
        f"Hi {lead_name},\n\n"
        f"I came across your {type_label} at {lead_address} and wanted to reach out.\n\n"
        f"In today's market, over 80% of customers search online before visiting a {type_label}. "
        f"{'A beautiful, mobile-ready website can dramatically increase your walk-in customers and bookings.' if template_type == 'no_website' else 'A premium, modernized website can dramatically increase your walk-in customers and direct bookings.'}\n\n"
        f"I specialize in building premium websites for local {type_label}s, including:\n"
        + "".join(f"  - {f[2:]}\n" for f in features) +
        f"\nI'd love to create a free, no-commitment custom design concept for {lead_name}. "
        f"If you're interested in seeing what's possible, just reply to this email.\n\n"
        f"Best regards,\n{config.EMAIL_FROM.replace(chr(34), '')}\n"
    )

    # ── HTML version ───────────────────────────────────────────────
    features_html = "".join(
        f'<li style="margin-bottom:8px;font-size:15px;color:#374151">{f}</li>'
        for f in features
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{subject}</title>
</head>
<body style="margin:0;padding:0;background:#060912;font-family:'Inter', 'Helvetica Neue',Helvetica,Arial,sans-serif;color:#f8fafc">

  <!-- Outer wrapper -->
  <table width="100%" cellpadding="0" cellspacing="0" role="presentation"
         style="background:#060912;padding:40px 16px">
    <tr><td align="center">

      <!-- Card -->
      <table width="600" cellpadding="0" cellspacing="0" role="presentation"
             style="max-width:600px;background:#0e1529;border-radius:24px;overflow:hidden;
                    box-shadow:0 20px 60px rgba(0,0,0,0.6);border:1px solid rgba(255,255,255,0.06)">

        <!-- ── HERO BANNER ───────────────────────────────────────── -->
        <tr>
          <td style="padding:0;position:relative">
            <div style="position:relative;background:#000;">
                <img src="{hero_img}" alt="{hero_alt}"
                     width="600" style="width:100%;max-height:320px;object-fit:cover;display:block;opacity:0.85;">
            </div>
            <!-- Overlay label -->
            <table width="100%" cellpadding="0" cellspacing="0" role="presentation"
                   style="position:absolute;bottom:0;left:0;right:0;background:linear-gradient(transparent,rgba(6,9,18,1));
                          border-radius:0;padding:40px 32px 24px">
              <tr>
                <td style="color:#ffffff">
                  <div style="font-size:12px;font-weight:700;letter-spacing:3px;text-transform:uppercase;
                              color:{cta_color};margin-bottom:8px">{type_emoji} {"Premium Website Concept" if template_type == "no_website" else "Website Redesign Concept"}</div>
                  <div style="font-size:28px;font-weight:900;line-height:1.2;letter-spacing:-0.5px;color:#ffffff">
                    {lead_name}
                  </div>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- ── GREETING ─────────────────────────────────────────── -->
        <tr>
          <td style="padding:40px 40px 0">
            <p style="margin:0 0 16px;font-size:17px;color:#f8fafc;font-weight:600">
              Hi {lead_name} 👋
            </p>
            <p style="margin:0 0 16px;font-size:15px;color:#94a3b8;line-height:1.7">
              I discovered your {type_label} {"at <strong>"+lead_address+"</strong>" if lead_address else ""} and 
              {"noticed you don't yet have a dedicated website online." if template_type == "no_website" else "noticed your current website could be modernized to drive more direct customers and reduce platform fees."}
            </p>
            <p style="margin:0 0 16px;font-size:15px;color:#94a3b8;line-height:1.7">
              In today's market, <strong style="color:#ffffff">over 80% of customers</strong> search 
              menus, rooms, photos, and reviews online before visiting in person. A stunning website 
              is one of the highest-ROI investments a {type_label} can make.
            </p>
          </td>
        </tr>

        <!-- ── DESIGN SHOWCASE 1 ─────────────────────────────────── -->
        <tr>
          <td style="padding:28px 40px 0">
            <div style="border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,0.06);
                        box-shadow:0 8px 30px rgba(0,0,0,0.3);background:#111a2f;">
              <img src="{feature_img}" alt="{preview_title}"
                   width="518" style="width:100%;max-height:280px;object-fit:cover;display:block;opacity:0.9">
              <div style="padding:20px;border-top:1px solid rgba(255,255,255,0.04)">
                <div style="font-size:15px;font-weight:700;color:#f8fafc;margin-bottom:6px">
                  {type_emoji} {preview_title}
                </div>
                <div style="font-size:14px;color:#94a3b8">{preview_caption}</div>
              </div>
            </div>
          </td>
        </tr>

        <!-- ── FEATURES ──────────────────────────────────────────── -->
        <tr>
          <td style="padding:36px 40px 0">
            <p style="margin:0 0 20px;font-size:16px;font-weight:700;color:#ffffff;letter-spacing:-0.2px">
              Everything included in your custom website:
            </p>
            <ul style="margin:0;padding-left:0;list-style:none">
              {"".join(f'<li style="margin-bottom:12px;font-size:15px;color:#cbd5e1;display:flex;align-items:center"><span style="color:{cta_color};margin-right:8px">✦</span> {f[2:]}</li>' for f in features)}
            </ul>
          </td>
        </tr>

        <!-- ── DESIGN SHOWCASE 2 ─────────────────────────────────── -->
        <tr>
          <td style="padding:32px 40px 0">
            <div style="border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,0.06);
                        box-shadow:0 8px 30px rgba(0,0,0,0.3);background:#111a2f;">
              <img src="{extra_img}" alt="Additional website feature"
                   width="518" style="width:100%;max-height:240px;object-fit:cover;display:block;opacity:0.9">
              <div style="padding:16px 20px;border-top:1px solid rgba(255,255,255,0.04)">
                <div style="font-size:14px;color:#94a3b8">
                  {"Room booking, local attractions & guest experience pages" if is_hotel else "Food photography, online ordering & reservation system pages"}
                </div>
              </div>
            </div>
          </td>
        </tr>

        <!-- ── CTA BUTTON ────────────────────────────────────────── -->
        <tr>
          <td style="padding:48px 40px 32px;text-align:center">
            <p style="margin:0 0 24px;font-size:16px;color:#94a3b8;line-height:1.7">
              I'd love to create a <strong style="color:#ffffff">free custom design concept</strong> 
              for {lead_name}. No commitment — just reply to this email to get started.
            </p>
            <a href="mailto:{config.EMAIL_FROM}"
               style="display:inline-block;background:linear-gradient(135deg, {cta_color}, {accent});color:#ffffff;
                      padding:16px 36px;border-radius:12px;font-size:16px;font-weight:700;
                      text-decoration:none;letter-spacing:-0.2px;
                      box-shadow:0 8px 25px rgba({int(cta_color[1:3], 16)},{int(cta_color[3:5], 16)},{int(cta_color[5:7], 16)},0.4)">
              Reply for Free Design Concept →
            </a>
          </td>
        </tr>

        <!-- ── SIGNATURE ─────────────────────────────────────────── -->
        <tr>
          <td style="padding:0 40px 32px">
            <div style="border-top:1px solid rgba(255,255,255,0.06);padding-top:24px">
              <p style="margin:0;font-size:15px;color:#94a3b8">
                Best regards,<br>
                <strong style="color:#f8fafc;font-size:16px;display:inline-block;margin-top:4px">{config.EMAIL_FROM.replace(chr(34), '')}</strong>
              </p>
            </div>
          </td>
        </tr>

        <!-- ── FOOTER ────────────────────────────────────────────── -->
        <tr>
          <td style="background:#0a0f1e;padding:24px 40px;border-top:1px solid rgba(255,255,255,0.04);
                     border-radius:0 0 24px 24px;text-align:center">
            <p style="margin:0;font-size:12px;color:#475569;line-height:1.6">
              This email was sent to {lead.get('email','')}.<br>
              To opt out, reply with <strong>STOP</strong> and we'll remove you immediately.
            </p>
          </td>
        </tr>

      </table><!-- /Card -->
    </td></tr>
  </table><!-- /Outer wrapper -->

</body>
</html>"""
    return subject, text, html


def send_email(to_email, subject, text_content, html_content, in_reply_to=None, references=None):
    msg = MIMEMultipart("alternative")
    msg["From"]    = config.EMAIL_FROM
    msg["To"]      = to_email
    msg["Subject"] = subject
    
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
