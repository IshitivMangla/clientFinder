import sys

with open('src/dashboard.html', 'rb') as f:
    content = f.read()

sendBtn1_old = b'''    const sendBtn = `<button class="btn btn-p" onclick="sendEmail(${l.id},this)" ${canSend ? '' : 'disabled'} title="${canSend ? 'Send outreach email' : 'No email yet'}">
      <i class="fa-solid fa-paper-plane"></i>${canSend ? ' Email' : ' No Email'}
    </button>`;'''

sendBtn1_new = b'''    const defaultTpl = hasWeb ? 'has_website' : 'no_website';
    const tplSelect = `<select id="tpl-${l.id}" class="btn" style="background:var(--surface2);color:var(--t2);border:1px solid var(--border);padding:6px;border-radius:var(--r-md);margin-right:4px;">
      <option value="no_website" ${defaultTpl === 'no_website' ? 'selected' : ''}>Pitch: No Web</option>
      <option value="has_website" ${defaultTpl === 'has_website' ? 'selected' : ''}>Pitch: Redesign</option>
    </select>`;
    const sendBtn = `<div style="display:flex;align-items:center;">${tplSelect}<button class="btn btn-p" onclick="sendEmail(${l.id},this)" ${canSend ? '' : 'disabled'} title="${canSend ? 'Send outreach email' : 'No email yet'}">
      <i class="fa-solid fa-paper-plane"></i>${canSend ? ' Email' : ' No Email'}
    </button></div>`;'''

content = content.replace(sendBtn1_old, sendBtn1_new)

sendBtn2_old = b'''    const sendBtn = `<button class="btn btn-p" onclick="sendEmail(${l.id},this)" ${canSend?'':'disabled'}>
      <i class="fa-solid fa-paper-plane"></i> Email
    </button>`;'''

sendBtn2_new = b'''    const defaultTpl = hasWeb ? 'has_website' : 'no_website';
    const tplSelect = `<select id="tpl-${l.id}" class="btn" style="background:var(--surface2);color:var(--t2);border:1px solid var(--border);padding:6px;border-radius:var(--r-md);margin-right:4px;">
      <option value="no_website" ${defaultTpl === 'no_website' ? 'selected' : ''}>Pitch: No Web</option>
      <option value="has_website" ${defaultTpl === 'has_website' ? 'selected' : ''}>Pitch: Redesign</option>
    </select>`;
    const sendBtn = `<div style="display:flex;align-items:center;">${tplSelect}<button class="btn btn-p" onclick="sendEmail(${l.id},this)" ${canSend?'':'disabled'}>
      <i class="fa-solid fa-paper-plane"></i> Email
    </button></div>`;'''

content = content.replace(sendBtn2_old, sendBtn2_new)

sendEmail_old = b'''async function sendEmail(id, btn) {
  const orig = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
  toast('Sending outreach email\\xe2\\x80\\xa6', 'info');
  try {
    const res = await fetch(`/api/leads/${id}/send-email`, { method: 'POST' });'''

sendEmail_new = b'''async function sendEmail(id, btn) {
  const orig = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
  const tpl = document.getElementById('tpl-'+id) ? document.getElementById('tpl-'+id).value : 'no_website';
  toast('Sending outreach email...', 'info');
  try {
    const res = await fetch(`/api/leads/${id}/send-email`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ template_type: tpl })
    });'''

content = content.replace(sendEmail_old, sendEmail_new)

# Handle potential ascii alternative
sendEmail_old2 = b'''async function sendEmail(id, btn) {
  const orig = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
  toast('Sending outreach email...', 'info');
  try {
    const res = await fetch(`/api/leads/${id}/send-email`, { method: 'POST' });'''

content = content.replace(sendEmail_old2, sendEmail_new)

with open('src/dashboard.html', 'wb') as f:
    f.write(content)
print('Done!')
