"""Retrieve public source bytes without executing downloaded code."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'data' / 'sources'
CACHE.mkdir(parents=True, exist_ok=True)

def get(name, url):
    dest = CACHE / name
    if not dest.exists():
        request = urllib.request.Request(url, headers={'User-Agent': 'Kettle-LCA-research/1.0'})
        with urllib.request.urlopen(request, timeout=90) as response:
            data = response.read()
        dest.write_bytes(data)
    data = dest.read_bytes()
    return {'file': str(dest.relative_to(ROOT)), 'url': url, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

if __name__ == '__main__':
    sources = [
        ('lab.html', 'https://tiangong-lca-decision-lab.ecodino73.chatgpt.site'),
        ('release-downloads.md', 'https://raw.githubusercontent.com/FLCAC-admin/uslci-content/dev/docs/release_info/release-downloads.md'),
        ('uslci-github-files.json', 'https://api.github.com/repos/FLCAC-admin/uslci-content/contents/downloads?ref=dev'),
        ('prepare.json', 'https://api.nal.usda.gov/FederalLCACommonsapi/download/json/prepare/National_Renewable_Energy_Laboratory/USLCI_Database_Public?api_key=DEMO_KEY'),
    ]
    with concurrent.futures.ThreadPoolExecutor(4) as pool:
        jobs = [pool.submit(get, *source) for source in sources]
        for job in jobs:
            try: print(json.dumps(job.result()))
            except Exception as error: print(type(error).__name__, str(error))
