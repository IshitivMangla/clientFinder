import httpx
from openai import OpenAI
from . import config
from . import database

def get_openai_client(base_url=None):
    http_client = httpx.Client(verify=config.VERIFY_SSL)
    if base_url:
        return OpenAI(
            base_url=base_url,
            api_key=config.NVIDIA_API_KEY,
            http_client=http_client
        )
    else:
        return OpenAI(
            api_key=config.OPENAI_API_KEY,
            http_client=http_client
        )

def generate_reply(lead_name, lead_type, conversation_history, latest_reply):
    api_key = config.NVIDIA_API_KEY or config.OPENAI_API_KEY
    if not api_key:
        # Fallback response
        return (
            f"Hi {lead_name or 'there'},\n\n"
            f"Thanks for reaching out! I'd be happy to help build or improve the website for your {lead_type or 'business'}. "
            f"Could you share a bit more about what you're looking for, or any specific features you'd like to include? "
            f"I can then put together a quick quote for you.\n\n"
            f"Best regards,\n"
            f"{config.EMAIL_FROM.replace(chr(34), '')}"
        )

    try:
        if config.NVIDIA_API_KEY:
            database.enforce_rate_limit("nvidia", 60)
            database.increment_api_usage("nvidia")
            client = get_openai_client(base_url="https://integrate.api.nvidia.com/v1")
            model = config.NVIDIA_MODEL
        else:
            database.enforce_rate_limit("openai", 60)
            database.increment_api_usage("openai")
            client = get_openai_client()
            model = "gpt-4o-mini"
        
        system_prompt = (
            "You are a professional freelance web designer/developer follow-up assistant.\n"
            "A local business owner has replied to your initial website outreach email showing interest.\n"
            "Write a brief, polite, and professional email to ask about their requirements so you can provide an estimate.\n"
            "Specifically, ask them about:\n"
            "- Whether they need a front-end only website (static/informational) or a full-stack website (with dynamic features, databases, or booking systems).\n"
            "- The estimated number of pages they expect.\n\n"
            "Keep the email brief, warm, and highly professional. Avoid long paragraphs. "
            "Keep pricing guidelines in mind but do not offer a price unless they asked:\n"
            "- Front-end only websites: $100 to $200 USD base price depending on the number of pages.\n"
            "- Full-stack websites: $200 to $500 USD base price depending on the number of pages."
        )

        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in conversation_history:
            role = "assistant" if msg["direction"] == "outbound" else "user"
            messages.append({"role": role, "content": msg["body"]})
            
        messages.append({"role": "user", "content": latest_reply})
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating OpenAI reply: {e}")
        return (
            f"Hi {lead_name or 'there'},\n\n"
            f"Thank you for getting back to me! I would love to help you with your website. "
            f"Let me know if you have some time for a quick chat, or feel free to reply with your requirements.\n\n"
            f"Best regards,\n"
            f"{config.EMAIL_FROM.replace(chr(34), '')}"
        )

def classify_reply(latest_reply):
    api_key = config.NVIDIA_API_KEY or config.OPENAI_API_KEY
    if not api_key:
        return True  # Fallback: assume interested if API keys are missing

    try:
        if config.NVIDIA_API_KEY:
            database.enforce_rate_limit("nvidia", 60)
            database.increment_api_usage("nvidia")
            client = get_openai_client(base_url="https://integrate.api.nvidia.com/v1")
            model = config.NVIDIA_MODEL
        else:
            database.enforce_rate_limit("openai", 60)
            database.increment_api_usage("openai")
            client = get_openai_client()
            model = "gpt-4o-mini"

        system_prompt = (
            "You are an email classification assistant. Your job is to classify if the sender of the email "
            "is interested in hearing more about our website design/development services or getting a quote.\n\n"
            "Respond with exactly one of the following words:\n"
            "- INTERESTED: if they express interest, ask for prices, ask for more details, or ask to schedule a call.\n"
            "- NOT_INTERESTED: if they say no, stop, unsubscribe, already have a website, or are hostile.\n"
            "- OTHER: if it is an out-of-office automated reply, a bounce-back, or unclear.\n\n"
            "Output only the classification word. Do not include any other text, explanation, or punctuation."
        )

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": latest_reply}
            ],
            max_tokens=5,
            temperature=0.0
        )

        result = response.choices[0].message.content.strip().upper()
        print(f"[CLASSIFIER] Lead reply classified as: {result}")
        return result == "INTERESTED"
    except Exception as e:
        print(f"Error classifying reply: {e}")
        return True  # Fallback to interested in case of API failure

def generate_outreach_email(lead_name, lead_type, lead_address):
    api_key = config.NVIDIA_API_KEY or config.OPENAI_API_KEY
    if not api_key:
        # Fallback static outreach if no API key is configured
        subject = f"Grow your business with a website for {lead_name}"
        text = (
            f"Hi {lead_name or 'there'},\n\n"
            f"I noticed your {lead_type or 'business'} {f'at {lead_address}' if lead_address else ''} does not yet have a website. "
            f"A simple website can help you get more local customers, improve online visibility, and make bookings easier.\n\n"
            f"I can help set up a modern, mobile-friendly website quickly and affordably. If you're interested, reply to this email and I can share a quote and examples.\n\n"
            f"Best regards,\n"
            f"{config.EMAIL_FROM.replace(chr(34), '')}\n"
        )
        return subject, text

    try:
        if config.NVIDIA_API_KEY:
            database.enforce_rate_limit("nvidia", 60)
            database.increment_api_usage("nvidia")
            client = get_openai_client(base_url="https://integrate.api.nvidia.com/v1")
            model = config.NVIDIA_MODEL
        else:
            database.enforce_rate_limit("openai", 60)
            database.increment_api_usage("openai")
            client = get_openai_client()
            model = "gpt-4o-mini"

        system_prompt = (
            "You are a professional freelance web designer/developer.\n"
            "Write a simple, professional, and personalized outreach email to a local business owner "
            "who does not have a website.\n"
            "Provide the subject line and the email body. The text must be warm, helpful, and concise.\n"
            "Format the output exactly as:\n"
            "Subject: [Subject Line]\n"
            "Body:\n"
            "[Email Body]"
        )

        prompt = f"Business Name: {lead_name}\nBusiness Type: {lead_type}\nAddress: {lead_address}"

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )

        content = response.choices[0].message.content.strip()
        
        subject = f"Grow your business with a website for {lead_name}"
        body = content
        
        # Parse out Subject and Body if formatted as requested
        if "Subject:" in content and "Body:" in content:
            parts = content.split("Body:", 1)
            subject_part = parts[0].replace("Subject:", "").strip()
            body_part = parts[1].strip()
            if subject_part:
                subject = subject_part
            if body_part:
                body = body_part

        return subject, body
    except Exception as e:
        print(f"Error generating outreach email: {e}")
        # Return fallback
        subject = f"Grow your business with a website for {lead_name}"
        text = (
            f"Hi {lead_name or 'there'},\n\n"
            f"I noticed your {lead_type or 'business'} {f'at {lead_address}' if lead_address else ''} does not yet have a website. "
            f"A simple website can help you get more local customers, improve online visibility, and make bookings easier.\n\n"
            f"I can help set up a modern, mobile-friendly website quickly and affordably. If you're interested, reply to this email and I can share a quote and examples.\n\n"
            f"Best regards,\n"
            f"{config.EMAIL_FROM.replace(chr(34), '')}\n"
        )
        return subject, text

def generate_quote_email(lead_name, lead_type, conversation_history, latest_reply):
    api_key = config.NVIDIA_API_KEY or config.OPENAI_API_KEY
    if not api_key:
        return (
            f"Hi {lead_name or 'there'},\n\n"
            f"Thank you for sharing your requirements! Based on what you described, I would recommend a standard website. "
            f"Typically, a frontend website is about $300 USD, while a full-stack system is about $700 USD. "
            f"Please let me know if this works for you. I am happy to discuss or negotiate to fit your budget!\n\n"
            f"Best regards,\n"
            f"{config.EMAIL_FROM.replace(chr(34), '')}"
        )

    try:
        if config.NVIDIA_API_KEY:
            database.enforce_rate_limit("nvidia", 60)
            database.increment_api_usage("nvidia")
            client = get_openai_client(base_url="https://integrate.api.nvidia.com/v1")
            model = config.NVIDIA_MODEL
        else:
            database.enforce_rate_limit("openai", 60)
            database.increment_api_usage("openai")
            client = get_openai_client()
            model = "gpt-4o-mini"

        system_prompt = (
            "You are a professional freelance web designer/developer follow-up assistant.\n"
            "A local business owner has sent you their website requirements in response to your inquiry.\n"
            "Your job is to read their requirements, estimate the project type, and automatically propose a price quote on the higher side:\n"
            "- If they require only front-end (informational, standard pages), quote a price on the higher end of the $100 to $300 USD range (propose around $300 USD based on page count).\n"
            "- If they require full-stack (databases, logins, admin panels, reservation systems, authentication), quote a price on the higher end of the $400 to $700 USD range (propose around $700 USD based on complexity).\n\n"
            "Important instructions:\n"
            "- State the estimated price clearly.\n"
            "- Explicitly mention that the price is negotiable and that you want to work within their budget.\n"
            "- Keep the tone highly professional, warm, and brief.\n"
            "- Do not write a long email."
        )

        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation_history:
            role = "assistant" if msg["direction"] == "outbound" else "user"
            messages.append({"role": role, "content": msg["body"]})
        messages.append({"role": "user", "content": latest_reply})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=300,
            temperature=0.7
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating quote email: {e}")
        return (
            f"Hi {lead_name or 'there'},\n\n"
            f"Thank you for sharing your requirements! Based on what you described, I would recommend a standard website. "
            f"Typically, a frontend website is about $300 USD, while a full-stack system is about $700 USD. "
            f"Please let me know if this works for you. I am happy to discuss or negotiate to fit your budget!\n\n"
            f"Best regards,\n"
            f"{config.EMAIL_FROM.replace(chr(34), '')}"
        )

def generate_negotiation_email(lead_name, lead_type, conversation_history, latest_reply):
    api_key = config.NVIDIA_API_KEY or config.OPENAI_API_KEY
    if not api_key:
        return (
            f"Hi {lead_name or 'there'},\n\n"
            f"Thanks for your reply! I would be happy to finalize this. Let's do $250 USD for a frontend site or $550 USD for a full-stack site. "
            f"Looking forward to working together!\n\n"
            f"Best regards,\n"
            f"{config.EMAIL_FROM.replace(chr(34), '')}\n\n"
            f"Negotiated Price: $250"
        )

    try:
        if config.NVIDIA_API_KEY:
            database.enforce_rate_limit("nvidia", 60)
            database.increment_api_usage("nvidia")
            client = get_openai_client(base_url="https://integrate.api.nvidia.com/v1")
            model = config.NVIDIA_MODEL
        else:
            database.enforce_rate_limit("openai", 60)
            database.increment_api_usage("openai")
            client = get_openai_client()
            model = "gpt-4o-mini"

        system_prompt = (
            "You are a professional freelance web designer/developer negotiation assistant.\n"
            "The client has responded to your price quote, either accepting it or negotiating for a lower price.\n"
            "Your job is to read their email, negotiate a final agreement, and close the deal:\n"
            "- If they ask for a lower price/discount, you can negotiate down slightly, but NEVER go below these floor prices:\n"
            "  * Frontend website floor: $100 USD (do not negotiate below $100).\n"
            "  * Full-stack website floor: $400 USD (do not negotiate below $400).\n"
            "- Be polite, professional, and clear about the value they are getting.\n"
            "- If they accept the original price, simply express your excitement and outline next steps to get started.\n\n"
            "CRITICAL: At the very end of your response, add a new line containing exactly: 'Negotiated Price: $X' "
            "(where X is the final negotiated price in USD you proposed or agreed to in this email, e.g., Negotiated Price: $250 or Negotiated Price: $600). "
            "This line must be on its own line at the very bottom."
        )

        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation_history:
            role = "assistant" if msg["direction"] == "outbound" else "user"
            messages.append({"role": role, "content": msg["body"]})
        messages.append({"role": "user", "content": latest_reply})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=300,
            temperature=0.7
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating negotiation email: {e}")
        return (
            f"Hi {lead_name or 'there'},\n\n"
            f"Thanks for your reply! I would be happy to finalize this. Let's do $250 USD for a frontend site or $550 USD for a full-stack site. "
            f"Looking forward to working together!\n\n"
            f"Best regards,\n"
            f"{config.EMAIL_FROM.replace(chr(34), '')}\n\n"
            f"Negotiated Price: $250"
        )
