import time
import requests


def fetch_raw(url, headers=None, rate_limit_delay=3.0):
    headers = headers or {"User-Agent":  "IntelliCorpus/1.0 (contact: paull@scholar-cergy.com)"}
    time.sleep(rate_limit_delay)
    r = requests.get(url, headers=headers, timeout=60)
    r.raise_for_status()
    content_type = r.headers.get("Content-Type","")
    if 'xml' in content_type:
        return r.text
    elif 'json' in content_type:
        return r.json()
    else:
        return r.text