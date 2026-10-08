import collections
import json
import re
import zipfile
from retrieve import CACHE, ROOT

z = zipfile.ZipFile(CACHE / 'commons-merged-hybrid.zip')
print('Objects by type:', collections.Counter(n.split('/')[0] for n in z.namelist()))
catalog = []
for n in z.namelist():
    if n.startswith(('processes/', 'lcia_methods/', 'lcia_categories/')) and n.endswith('.json'):
        o = json.loads(z.read(n))
        row = {'path':n, 'id':o['@id'], 'name':o.get('name'), 'type':o.get('processType'),
               'version':o.get('version'), 'location':o.get('location'), 'tags':o.get('tags')}
        catalog.append(row)
        if n.startswith('lcia_methods/') or re.search(r'polypropylene|polyvinyl|nylon|polyamide|polyoxymethylene|polycarbonate|acrylonitrile|silicone|stainless|brass|copper|corrugat|cardboard|polyethylene.*low|plastic.*injection|injection.*mold|IPCC.*100',o.get('name',''),re.I):
            print(json.dumps(row, ensure_ascii=True))
(ROOT/'data'/'catalog.json').write_text(json.dumps(catalog, indent=2))
