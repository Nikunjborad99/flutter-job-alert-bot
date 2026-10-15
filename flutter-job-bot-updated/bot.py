import os, re, json, html, hashlib, logging, imaplib, email
from email.header import decode_header, make_header
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
import requests

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
HISTORY = Path('sent_jobs.json')
SOURCES = ['remotive', 'arbeitnow', 'remoteok', 'linkedin_email']
SESSION = requests.Session()
SESSION.headers.update({'User-Agent': 'FlutterJobAlertBot/1.0 (personal job alerts)'})
TIMEOUT = 20

def get(url, headers=None):
    r = SESSION.get(url, timeout=TIMEOUT, headers=headers)
    r.raise_for_status()
    return r.json()

def clean(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]*>', ' ', str(s or '')))).strip()

def job(source, title, company, url, description='', location='', job_type='', date=''):
    if not url or not title: return None
    return dict(source=source, title=clean(title), company=clean(company), url=str(url),
                description=clean(description), location=clean(location), job_type=clean(job_type), date=str(date or ''))

def remotive():
    data = get('https://remotive.com/api/remote-jobs?search=flutter')
    return [job('Remotive', x.get('title'), x.get('company_name'), x.get('url'), x.get('description'), x.get('candidate_required_location'), x.get('job_type'), x.get('publication_date')) for x in data.get('jobs', [])]

def arbeitnow():
    data = get('https://www.arbeitnow.com/api/job-board-api')
    return [job('Arbeitnow', x.get('title'), x.get('company_name'), x.get('url'), x.get('description'), x.get('location'), 'remote' if x.get('remote') else '', x.get('created_at')) for x in data.get('data', []) if x.get('remote')]

def remoteok():
    data = get('https://remoteok.com/api', headers={'Accept': 'application/json'})
    return [job('Remote OK', x.get('position'), x.get('company'), x.get('url') or x.get('apply_url'), x.get('description'), x.get('location'), ' '.join(x.get('tags') or []), x.get('date')) for x in data if isinstance(x, dict) and x.get('position')]

def unwrap_linkedin(url):
    from urllib.parse import urlsplit
    parsed = urlsplit(url)
    if 'linkedin.com' in (parsed.hostname or ''):
        return url
    params = parse_qs(parsed.query)
    for key in ('url', 'u', 'redirect', 'redirectUrl'):
        for val in params.get(key, []):
            if 'linkedin.com' in val: return unquote(val)
    return None

def linkedin_email():
    username, password = os.getenv('IMAP_USER'), os.getenv('IMAP_APP_PASSWORD')
    if not username or not password:
        logging.info('LinkedIn email source skipped: IMAP credentials missing')
        return []
    host = os.getenv('IMAP_HOST', 'imap.gmail.com')
    mailbox = imaplib.IMAP4_SSL(host, 993)
    result = []
    try:
        mailbox.login(username, password)
        mailbox.select('INBOX', readonly=True)
        since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%d-%b-%Y')
        status, ids = mailbox.search(None, 'SINCE', since)
        if status != 'OK': return []
        for msgid in ids[0].split()[-150:]:
            status, parts = mailbox.fetch(msgid, '(RFC822)')
            if status != 'OK': continue
            raw = next((p[1] for p in parts if isinstance(p, tuple)), None)
            if not raw: continue
            message = email.message_from_bytes(raw)
            sender = str(message.get('From', '')).lower()
            if not re.search(r'linkedin\.com', sender): continue
            subject = str(make_header(decode_header(message.get('Subject', ''))))
            if not re.search(r'job|flutter|remote|opportunit', subject, re.I): continue
            for part in message.walk():
                if part.get_content_type() != 'text/html': continue
                payload = part.get_payload(decode=True)
                if not payload: continue
                body = payload.decode(part.get_content_charset() or 'utf-8', errors='replace')
                urls = re.findall(r'href=["\']([^"\']+)["\']', body, re.I)
                for link in urls:
                    link = unwrap_linkedin(html.unescape(link))
                    if not link or not re.search(r'linkedin\.com/(jobs/view/|comm/jobs/view/)', link): continue
                    # Email subjects are not necessarily individual job titles. Mark source as a lead.
                    result.append(job('LinkedIn email', 'Flutter freelance alert (unverified)', 'LinkedIn (verify listing)', link, subject, 'Remote / verify eligibility', 'Unverified LinkedIn lead'))
    finally:
        try: mailbox.logout()
        except Exception: pass
    return result

from filters import matches

def identity(x):
    url = x['url'].split('?')[0].rstrip('/').lower()
    return hashlib.sha256((x['source'] + '|' + url).encode()).hexdigest()

def send(text):
    token, chat = os.environ['TELEGRAM_BOT_TOKEN'], os.environ['TELEGRAM_CHAT_ID']
    r = SESSION.post(f'https://api.telegram.org/bot{token}/sendMessage', json={'chat_id': chat, 'text': text, 'disable_web_page_preview': True}, timeout=TIMEOUT)
    r.raise_for_status()
    if not r.json().get('ok'): raise RuntimeError('Telegram rejected message')

def main():
    if not os.getenv('TELEGRAM_BOT_TOKEN') or not os.getenv('TELEGRAM_CHAT_ID'):
        raise RuntimeError('TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID required')
    history = json.loads(HISTORY.read_text()) if HISTORY.exists() else {}
    jobs = []
    for source in (remotive, arbeitnow, remoteok, linkedin_email):
        try:
            found = source()
            logging.info('%s returned %s items', source.__name__, len(found))
            jobs.extend(j for j in found if j and (matches(j) or (j['source'] == 'LinkedIn email' and 'flutter' in j['description'].lower())))
        except Exception as exc:
            logging.warning('%s failed: %s', source.__name__, exc)
    unique = {identity(j): j for j in jobs}
    unseen = [(key, val) for key, val in unique.items() if key not in history]
    unseen = unseen[:20]  # cap daily Telegram volume; remaining jobs can appear next run
    if not unseen:
        send('📭 Flutter job digest: no new matching jobs today.')
    else:
        send(f'🚀 Flutter freelance/contract digest: {len(unseen)} new leads for ~3.5 years experience. Verify eligibility and pay before applying.')
        for key, j in unseen:
            msg = f"💼 {j['title'][:180]}\n🏢 {j['company'][:100] or 'Not specified'}\n🌍 {j['location'][:120] or 'Remote / location not specified'}\n📌 {j['job_type'][:100] or 'Type not specified'}\n🔎 {j['source']}\n🔗 {j['url']}"
            send(msg)
            history[key] = datetime.now(timezone.utc).isoformat()
            HISTORY.write_text(json.dumps(history, indent=2) + '\n')
    # Keep only 180 days of sent history.
    cutoff = datetime.now(timezone.utc) - timedelta(days=180)
    history = {k: v for k, v in history.items() if datetime.fromisoformat(v) >= cutoff}
    HISTORY.write_text(json.dumps(history, indent=2) + '\n')

if __name__ == '__main__': main()
