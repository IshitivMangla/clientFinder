import re

path = 'src/pipeline.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update batch size to 20
content = content.replace('for _ in range(1):', 'for _ in range(20):')
content = content.replace('for _ in range(15):', 'for _ in range(20):') # Just in case

# 2. Add "processing" status update immediately after fetching lead
# We find where it fetches lead_id
# lead_dict = dict(lead)
# lead_id = lead_dict["id"]
processing_code = '''        lead_dict = dict(lead)
        lead_id = lead_dict["id"]
        
        # Mark as processing immediately to prevent duplicate runs
        database.update_lead_status(lead_id, "processing")
'''
content = content.replace('        lead_dict = dict(lead)\n        lead_id = lead_dict["id"]\n', processing_code)

# 3. Increase delay to 20-40 seconds at the end of the loop
# We find time.sleep(2) and replace it
sleep_code = '''        import random
        delay = random.randint(20, 40)
        print(f"[PIPELINE] Sleeping for {delay} seconds...")
        time.sleep(delay)
'''
content = content.replace('        time.sleep(2)\n', sleep_code)
content = content.replace('        time.sleep(300)\n', sleep_code)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Refactored pipeline.py')
