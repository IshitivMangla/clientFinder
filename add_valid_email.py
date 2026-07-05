import re
import sys

path = 'src/leads_handler.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

valid_email_func = '''
def valid_email(email):
    pattern = r'^[\\w\\.-]+@[\\w\\.-]+\\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

'''

if 'def valid_email' not in content:
    content = content.replace('def get_us_locations():', valid_email_func + 'def get_us_locations():')

# Modify extract_emails_from_text
def repl1(m):
    return m.group(1) + "if valid_email(email):\n" + m.group(2) + "    emails.add(email.lower())"

# We look for the exact lines in extract_emails_from_text
content = re.sub(
    r'(if not any\(email\.lower\(\)\.endswith\(dom\) for dom in exclude_domains\):\n)(\s+)emails\.add\(email\.lower\(\)\)',
    r'\1\2    if valid_email(email):\n\2        emails.add(email.lower())',
    content
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Refactored leads_handler.py to include valid_email')
