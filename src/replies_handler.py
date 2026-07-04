import imaplib
import email
import re
from email.header import decode_header
from bs4 import BeautifulSoup
from . import config
from . import database
from . import openai_handler
from . import email_handler
from . import leads_handler

def decode_mime_header(header_value):
    if not header_value:
        return ""
    decoded_parts = decode_header(header_value)
    header_text = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            header_text += part.decode(encoding or "utf-8", errors="ignore")
        else:
            header_text += str(part)
    return header_text

def get_email_body(msg):
    body = ""
    if msg.is_multipart():
        html_part = None
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if "attachment" in content_disposition:
                continue
            if content_type == "text/plain":
                try:
                    body = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="ignore")
                    break
                except Exception:
                    pass
            elif content_type == "text/html":
                html_part = part
        
        if not body and html_part:
            try:
                html_content = html_part.get_payload(decode=True).decode(html_part.get_content_charset() or "utf-8", errors="ignore")
                soup = BeautifulSoup(html_content, "html.parser")
                body = soup.get_text()
            except Exception:
                pass
    else:
        content_type = msg.get_content_type()
        if content_type == "text/plain":
            try:
                body = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="ignore")
            except Exception:
                pass
        elif content_type == "text/html":
            try:
                html_content = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="ignore")
                soup = BeautifulSoup(html_content, "html.parser")
                body = soup.get_text()
            except Exception:
                pass
    return body.strip()

def check_and_handle_replies():
    if not config.IMAP_USER or not config.IMAP_PASS or not config.IMAP_HOST:
        print("IMAP configuration is incomplete. Skipping reply check.")
        return

    print("Connecting to IMAP server...")
    try:
        if config.IMAP_TLS:
            mail = imaplib.IMAP4_SSL(config.IMAP_HOST, config.IMAP_PORT)
        else:
            mail = imaplib.IMAP4(config.IMAP_HOST, config.IMAP_PORT)
            
        mail.login(config.IMAP_USER, config.IMAP_PASS)
        mail.select("INBOX")
        
        status, response_data = mail.search(None, "UNSEEN")
        if status != "OK":
            print("Failed to search IMAP messages.")
            mail.logout()
            return
            
        mail_ids = response_data[0].split()
        print(f"Found {len(mail_ids)} unseen emails in INBOX.")
        
        for mail_id in mail_ids:
            status, data = mail.fetch(mail_id, "(RFC822)")
            if status != "OK" or not data:
                continue
                
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            subject = decode_mime_header(msg.get("Subject"))
            sender_raw = msg.get("From")
            sender_name, sender_email = email.utils.parseaddr(sender_raw)
            message_id = msg.get("Message-ID")
            
            if not sender_email:
                continue
                
            sender_email = sender_email.strip().lower()
            
            lead = database.get_lead_by_email(sender_email)
            if not lead:
                continue
                
            if lead["status"] in ["outreached", "engaged", "quoted", "negotiated"]:
                print(f"Processing reply from known lead: {lead['name']} ({sender_email})")
                
                body = get_email_body(msg)
                print(f"Reply text: {body[:100]}...")
                
                # Log incoming reply
                database.log_message(
                    lead_id=lead["id"],
                    message_id=message_id,
                    direction="inbound",
                    subject=subject,
                    body=body
                )
                
                if lead["status"] == "negotiated":
                    print(f"[REPLIES] Lead {sender_email} is already in 'negotiated' status. Marking read and skipping reply.")
                    mail.store(mail_id, "+FLAGS", "\\Seen")
                    continue
                
                if lead["status"] == "outreached":
                    # First reply from client. Check if they are interested.
                    is_interested = openai_handler.classify_reply(body)
                    if not is_interested:
                        print(f"[REPLIES] Lead {sender_email} is not interested. Updating status to 'not_interested'.")
                        database.update_lead_status(lead["id"], "not_interested")
                        mail.store(mail_id, "+FLAGS", "\\Seen")
                        continue
                    
                    # Generate requirements email using NVIDIA key
                    history = database.get_message_history(lead["id"])
                    
                    reply_body = openai_handler.generate_reply(
                        lead_name=lead["name"],
                        lead_type=lead["type"],
                        conversation_history=history[:-1],
                        latest_reply=body
                    )
                    
                    reply_subject = f"Re: {subject}" if not subject.lower().startswith("re:") else subject
                    reply_html = f"<p>{reply_body.replace(chr(10), '<br/>')}</p>"
                    
                    print(f"Sending automated requirements follow-up to {sender_email}...")
                    sent_msg_id = email_handler.send_email(
                        to_email=sender_email,
                        subject=reply_subject,
                        text_content=reply_body,
                        html_content=reply_html,
                        in_reply_to=message_id,
                        references=message_id
                    )
                    
                    database.log_message(
                        lead_id=lead["id"],
                        message_id=sent_msg_id,
                        direction="outbound",
                        subject=reply_subject,
                        body=reply_body
                    )
                    
                    database.update_lead_status(lead["id"], "engaged")
                    print(f"[REPLIES] Automated follow-up sent. Status set to 'engaged'.")
                
                elif lead["status"] == "engaged":
                    # Second reply from client (containing requirements). Send initial high quote.
                    history = database.get_message_history(lead["id"])
                    reply_body = openai_handler.generate_quote_email(
                        lead_name=lead["name"],
                        lead_type=lead["type"],
                        conversation_history=history[:-1],
                        latest_reply=body
                    )
                    
                    reply_subject = f"Re: {subject}" if not subject.lower().startswith("re:") else subject
                    reply_html = f"<p>{reply_body.replace(chr(10), '<br/>')}</p>"
                    
                    print(f"Sending initial price quote to {sender_email}...")
                    sent_msg_id = email_handler.send_email(
                        to_email=sender_email,
                        subject=reply_subject,
                        text_content=reply_body,
                        html_content=reply_html,
                        in_reply_to=message_id,
                        references=message_id
                    )
                    
                    database.log_message(
                        lead_id=lead["id"],
                        message_id=sent_msg_id,
                        direction="outbound",
                        subject=reply_subject,
                        body=reply_body
                    )
                    
                    database.update_lead_status(lead["id"], "quoted")
                    print(f"[REPLIES] Automated initial quote sent. Status set to 'quoted'.")
                    
                elif lead["status"] == "quoted":
                    # Third reply from client (accepting or negotiating). final reply + CSV save
                    history = database.get_message_history(lead["id"])
                    reply_body = openai_handler.generate_negotiation_email(
                        lead_name=lead["name"],
                        lead_type=lead["type"],
                        conversation_history=history[:-1],
                        latest_reply=body
                    )
                    
                    # Parse final price from the tag
                    price_match = re.search(r"Negotiated Price:\s*\$?(\d+)", reply_body)
                    negotiated_price = f"${price_match.group(1)}" if price_match else "Unknown"
                    
                    # Remove the tag from the final email sent to client
                    cleaned_reply_body = re.sub(r"Negotiated Price:\s*\$?\d+", "", reply_body).strip()
                    
                    reply_subject = f"Re: {subject}" if not subject.lower().startswith("re:") else subject
                    reply_html = f"<p>{cleaned_reply_body.replace(chr(10), '<br/>')}</p>"
                    
                    print(f"Sending final negotiation email to {sender_email}...")
                    sent_msg_id = email_handler.send_email(
                        to_email=sender_email,
                        subject=reply_subject,
                        text_content=cleaned_reply_body,
                        html_content=reply_html,
                        in_reply_to=message_id,
                        references=message_id
                    )
                    
                    database.log_message(
                        lead_id=lead["id"],
                        message_id=sent_msg_id,
                        direction="outbound",
                        subject=reply_subject,
                        body=cleaned_reply_body
                    )
                    
                    # Save details to interested CSV file
                    leads_handler.save_interested_lead_to_csv(lead, negotiated_price)
                    
                    database.update_lead_status(lead["id"], "negotiated")
                    print(f"[REPLIES] Automated negotiation complete. Status set to 'negotiated' and saved to CSV.")
                
                mail.store(mail_id, "+FLAGS", "\\Seen")
                print(f"Successfully processed reply from {sender_email} and marked as read.")
                
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"IMAP reply handler failed: {e}")
