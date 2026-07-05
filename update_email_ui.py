import sys

with open('src/dashboard.html', 'rb') as f:
    content = f.read()

# Update card view email cell
old_str = b'''    const emailCell = (l.email && l.email.trim())
      ? `<a href="mailto:${l.email}" style="font-family:monospace;font-size:.74rem;color:var(--sky);text-decoration:none">${l.email}</a>`
      : `<span style="color:var(--t3);font-size:.72rem;display:flex;align-items:center;gap:4px"><i class="fa-solid fa-rotate fa-spin" style="font-size:.6rem"></i> Scraping...</span>`;'''

new_str = b'''    const emailCell = (l.email && l.email.trim())
      ? `<a href="mailto:${l.email}" style="font-family:monospace;font-size:.74rem;color:var(--sky);text-decoration:none">${l.email}</a>`
      : (l.status === 'no_email_found' ? `<span style="color:var(--t3);font-size:.72rem">Not Found</span>` : `<span style="color:var(--t3);font-size:.72rem;display:flex;align-items:center;gap:4px"><i class="fa-solid fa-rotate fa-spin" style="font-size:.6rem"></i> Scraping...</span>`);'''

old_str2 = b'''    const emailCell = (l.email && l.email.trim())
      ? `<a href="mailto:${l.email}" style="font-family:monospace;font-size:.74rem;color:var(--sky);text-decoration:none">${l.email}</a>`
      : `<span style="color:var(--t3);font-size:.72rem;display:flex;align-items:center;gap:4px"><i class="fa-solid fa-rotate fa-spin" style="font-size:.6rem"></i> Scraping\xef\xbf\xbd</span>`;'''

content = content.replace(old_str, new_str)
content = content.replace(old_str2, new_str)

# Update table view email cell to be more descriptive too
old_table = b'''    const emailCell = l.email
      ? `<span style="font-family:monospace;font-size:.74rem;color:var(--t2)">${l.email}</span>`
      : `<span style="color:var(--t3);font-size:.74rem">\xe2\x80\x94</span>`;'''

old_table2 = b'''    const emailCell = l.email
      ? `<span style="font-family:monospace;font-size:.74rem;color:var(--t2)">${l.email}</span>`
      : `<span style="color:var(--t3);font-size:.74rem">\xef\xbf\xbd</span>`;'''

new_table = b'''    const emailCell = l.email
      ? `<span style="font-family:monospace;font-size:.74rem;color:var(--t2)">${l.email}</span>`
      : (l.status === 'no_email_found' ? `<span style="color:var(--t3);font-size:.74rem">Not Found</span>` : `<span style="color:var(--t3);font-size:.74rem">Scraping...</span>`);'''

content = content.replace(old_table, new_table)
content = content.replace(old_table2, new_table)

with open('src/dashboard.html', 'wb') as f:
    f.write(content)
print('Done!')
