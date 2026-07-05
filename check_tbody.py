with open('src/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()
    if 'id="leads-tbody"' in text:
        print('leads-tbody exists')
    if 'id="tbody"' in text:
        print('tbody exists')
    else:
        print('no tbody')
