import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT") or 587)
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
EMAIL_FROM = os.getenv("EMAIL_FROM")

IMAP_HOST = os.getenv("IMAP_HOST")
IMAP_PORT = int(os.getenv("IMAP_PORT") or 993)
IMAP_USER = os.getenv("IMAP_USER")
IMAP_PASS = os.getenv("IMAP_PASS")
IMAP_TLS = os.getenv("IMAP_TLS", "true").lower() != "false"

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
SEARCH_QUERY = os.getenv("SEARCH_QUERY", "restaurant hotel")
SEARCH_LOCATION = os.getenv("SEARCH_LOCATION")
SEARCH_RADIUS = int(os.getenv("SEARCH_RADIUS") or 5000)

SEND_EMAIL = os.getenv("SEND_EMAIL", "false").lower() == "true"
DRY_RUN = os.getenv("DRY_RUN", "true").lower() != "false"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LEADS_CSV = os.getenv("LEADS_CSV", "./leads/leads.csv")

# Path to local database
DB_PATH = os.getenv("DB_PATH", "./leads.db")

# NVIDIA API Settings
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")
