import hashlib
import json
import time
import urllib.request
from retrieve import CACHE, ROOT

token = 'repository_Federal_LCA_Commons@commons_merged_hybrid@f04287a6c7b2955169a426423a9a1d6380ceeda9'
expected_sha256 = '4cf9bfdc5a8c9a531f9a6f3ba681f18014f25cf9ee7033c96e720a689fc4d13d'
url = 'https://www.lcacommons.gov/lca-collaboration/ws/public/download/json/' + token
target = CACHE / 'commons-merged-hybrid.zip'
if not target.exists():
    with urllib.request.urlopen(url, timeout=60) as response, target.with_suffix('.part').open('wb') as out:
        total = int(response.headers.get('Content-Length', 0))
        count = 0
        print('Download bytes:', total, flush=True)
        while chunk := response.read(1024 * 1024):
            out.write(chunk)
            count += len(chunk)
            if count % (10 * 1024 * 1024) == 0:
                print('Downloaded bytes:', count, flush=True)
        if total and count != total:
            raise ValueError('Incomplete download')
    target.with_suffix('.part').replace(target)
info = {'file':str(target.relative_to(ROOT)), 'url':url, 'repository_token':token,
        'bytes':target.stat().st_size, 'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'retrieval_date':'2026-10-08'}
if info['sha256'] != expected_sha256:
    raise ValueError('Archive hash differs from pinned independent-run data. Do not silently substitute another release.')
(CACHE / 'merged-download-manifest.json').write_text(json.dumps(info, indent=2))
print(json.dumps(info), flush=True)
