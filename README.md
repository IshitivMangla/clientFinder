# Client Outreach Bot

This project is a python-based automation bot for discovering local restaurant and hotel leads, sending email outreach, and handling reply automation.

## Key Improvements in Python Port

- **State Tracking (SQLite)**: Leads and conversation logs are persisted in a local SQLite database (`leads.db`), preventing duplicate outreach and enabling contextual conversations.
- **DuckDuckGo Email Finder**: Since Google Places does not return email addresses, the bot automatically searches DuckDuckGo for `"{business_name} {address} email"` and extracts candidate emails using regex.
- **Context-Aware Responses**: Connects your previous thread history to OpenAI (`gpt-4o-mini`) to generate tailored conversation responses.
- **Fixed IMAP Bug**: Correctly searches for unseen inbound messages instead of filtering by sender as the bot itself.

## What it does

1. **Loads leads** from `leads/leads.csv` or discovers them via Google Places API.
2. **Finds emails** for leads without them via DuckDuckGo search.
3. **Filters leads** that do not have their own website.
4. **Sends outreach email** via SMTP and logs them.
5. **Tracks replies** in your IMAP inbox, matches them with known leads, and uses OpenAI to generate and send follow-up messages.

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   Make sure you have a `.env` file containing your credentials (copied from `.env.example`). Set `SEND_EMAIL=true` and `DRY_RUN=false` when ready to send real emails.

3. **Initialize Database**:
   ```bash
   python main.py --init-db
   ```

4. **Prepare leads**:
   Populate `leads/leads.csv` or supply your `GOOGLE_PLACES_API_KEY` in `.env`.

## Usage

You can run the bot with specific command-line flags depending on your needs:

- **Discover and Enrich Leads**: Load CSV and query Google Places + search DuckDuckGo for emails:
  ```bash
  python main.py --find-leads
  ```

- **Send Outreach**: Email all pending leads without websites:
  ```bash
  python main.py --outreach
  ```

- **Check and Reply to Inbox**: Run this on a schedule (e.g. Cron job) to reply to incoming lead responses:
  ```bash
  python main.py --check-replies
  ```

- **Run all steps**:
  ```bash
  python main.py --all
  ```
