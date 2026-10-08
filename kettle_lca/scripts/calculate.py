"""Auditable partial material-supply LCA from openLCA JSON-LD.

Missing technosphere requirements are exported, never described as zero impact.
The reported subtotal is NOT the complete manufactured-kettle footprint.
"""
import ast
import argparse
import collections
import csv
import functools
import hashlib
import json
import math
import operator
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.deps'))
import numpy as np
import scipy
from scipy import sparse
from scipy.sparse.linalg import splu

OUT = ROOT / 'results' / 'independent-2026-10-08'

def write_csv(name, rows, fields=None):
    rows = list(rows)
    if not fields:
        fields = list(dict.fromkeys(k for r in rows for k in r))
    with (OUT / name).open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fields)
        w.writeheader()
        w.writerows(rows)

def safe_formula(text, names):
    text = re.sub(r'\bif\s*\(', 'choose(', text, flags=re.I).replace(';', ',').replace('^','**')
    text = re.sub(r'(?<![<>=!])=(?!=)', '==', text)
    tree = ast.parse(text, mode='eval')
    ops = {ast.Add:operator.add, ast.Sub:operator.sub, ast.Mult:operator.mul, ast.Div:operator.truediv,
           ast.Pow:operator.pow, ast.Mod:operator.mod, ast.Eq:operator.eq, ast.NotEq:operator.ne,
           ast.Lt:operator.lt, ast.LtE:operator.le, ast.Gt:operator.gt, ast.GtE:operator.ge}
    def visit(n):
        if isinstance(n, ast.Expression): return visit(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (float,int,bool)): return n.value
        if isinstance(n, ast.Name): return names[n.id]
        if isinstance(n, ast.BinOp) and type(n.op) in ops: return ops[type(n.op)](visit(n.left),visit(n.right))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op,(ast.USub,ast.UAdd)): return (-1 if isinstance(n.op,ast.USub) else 1)*visit(n.operand)
        if isinstance(n, ast.Compare) and len(n.ops)==1 and type(n.ops[0]) in ops: return ops[type(n.ops[0])](visit(n.left),visit(n.comparators[0]))
        if isinstance(n, ast.BoolOp) and isinstance(n.op,(ast.And,ast.Or)):
            return all(visit(v) for v in n.values) if isinstance(n.op,ast.And) else any(visit(v) for v in n.values)
        if isinstance(n, ast.Call) and isinstance(n.func,ast.Name) and not n.keywords:
            if n.func.id=='choose' and len(n.args)==3: return visit(n.args[1] if visit(n.args[0]) else n.args[2])
            funcs={'abs':abs,'min':min,'max':max,'sqrt':math.sqrt,'exp':math.exp,'log':math.log,'ln':math.log}
            if n.func.id in funcs: return funcs[n.func.id](*[visit(a) for a in n.args])
        raise ValueError('Unsupported formula: '+text)
    answer=float(visit(tree))
    if not math.isfinite(answer): raise ValueError('Nonfinite formula: '+text)
    return answer

class Inventory:
    def __init__(self, filename):
        self.z=zipfile.ZipFile(filename)
        self.paths=set(self.z.namelist())
        self.processes={}
        self.units={}
        self.providers=collections.defaultdict(list)
        self.formulas=[]
        self.global_params={}
        self.methods=[]
        self.categories=[]
        for name in sorted(self.paths):
            if not name.endswith('.json'): continue
            if name.startswith(('processes/','unit_groups/','parameters/','lcia_methods/','lcia_categories/')):
                o=json.loads(self.z.read(name))
                if name.startswith('processes/'): self.processes[o['@id']]=o
                elif name.startswith('unit_groups/'):
                    for u in o['units']: self.units[u['@id']]=dict(u,group=o['@id'])
                elif name.startswith('parameters/'): self.global_params[o['name']]=o
                elif name.startswith('lcia_methods/'): self.methods.append(o)
                else: self.categories.append(o)
        for pid,p in self.processes.items():
            for e in p.get('exchanges',[]):
                t=e['flow'].get('flowType') or self.flow(e['flow']['@id'])['flowType']
                if (t=='PRODUCT_FLOW' and not e['isInput'] or t=='WASTE_FLOW' and e['isInput']) and not e.get('isAvoidedProduct'):
                    self.providers[(e['flow']['@id'],e['isInput'])].append((pid,e))

    @functools.lru_cache(maxsize=None)
    def flow(self, fid): return json.loads(self.z.read('flows/'+fid+'.json'))

    @functools.lru_cache(maxsize=None)
    def params(self,pid):
        specs=dict(self.global_params)
        specs.update({p['name']:p for p in self.processes[pid].get('parameters',[])})
        values={k:p['value'] for k,p in specs.items() if not p.get('formula') or p.get('isInputParameter')}
        todo={k:p for k,p in specs.items() if k not in values}
        while todo:
            done=[]
            for k,p in todo.items():
                try: values[k]=safe_formula(p['formula'],values); done.append(k)
                except KeyError: pass
            if not done: raise ValueError('Unresolved parameter dependency in '+pid+': '+str(list(todo)))
            for k in done: del todo[k]
        return values

    def amount(self,pid,e):
        if e.get('amountFormula'):
            x=safe_formula(e['amountFormula'],self.params(pid))
            self.formulas.append({'process_id':pid,'exchange_id':e['internalId'],'formula':e['amountFormula'],
                                  'exported_amount':e['amount'],'evaluated_amount':x,'difference':x-e['amount']})
            return x
        return float(e['amount'])

    def conversion(self,e):
        return self.unit_conversion(e['flow']['@id'],e['flowProperty']['@id'],e['unit']['@id'])

    @functools.lru_cache(maxsize=None)
    def unit_conversion(self,fid,fpid,uid):
        u=self.units[uid]
        fl=self.flow(fid)
        prop=next(p for p in fl['flowProperties'] if p['flowProperty']['@id']==fpid)
        # Validate the exchange unit belongs to the chosen flow-property unit group.
        fp=json.loads(self.z.read('flow_properties/'+fpid+'.json'))
        assert fp['unitGroup']['@id']==u['group'], ('Unit/property mismatch',fid,fpid,uid)
        return u['conversionFactor']/prop['conversionFactor']

    def converted(self,pid,e): return self.amount(pid,e)*self.conversion(e)

    def reference(self,pid):
        refs=[e for e in self.processes[pid]['exchanges'] if e.get('isQuantitativeReference')]
        if len(refs)!=1: raise ValueError('Expected one reference exchange: '+pid)
        return refs[0]

    def provider(self,e):
        fid=e['flow']['@id']; typ=self.flow(fid)['flowType']; inp=typ=='WASTE_FLOW'
        candidates=self.providers.get((fid,inp),[])
        chosen=e.get('defaultProvider',{}).get('@id')
        if chosen:
            if chosen not in self.processes: return None,'missing default provider'
            candidates=[c for c in candidates if c[0]==chosen]
            if len(candidates)!=1: return None,'default provider has no unique matching product'
            return candidates[0],'default'
        if len(candidates)==1: return candidates[0],'unique exact flow and direction'
        return None, 'no provider' if not candidates else 'ambiguous providers: '+str(len(candidates))

    def allocation(self,pid,reference,e):
        p=self.processes[pid]
        method=p.get('defaultAllocationMethod') or 'NO_ALLOCATION'
        if method=='NO_ALLOCATION': return 1.0
        af=[a for a in p.get('allocationFactors',[]) if a['allocationType']==method]
        if not af:
            prods=[x for x in p['exchanges'] if not x['isInput'] and x['flow'].get('flowType')=='PRODUCT_FLOW' and not x.get('isAvoidedProduct') and x.get('amount')]
            if len(prods)>1: raise ValueError('Missing allocation factors for multifunctional process '+pid)
            return 1.0
        selected=[a for a in af if a['product']['@id']==reference['flow']['@id']]
        if method=='CAUSAL_ALLOCATION': selected=[a for a in selected if a.get('exchange',{}).get('internalId')==e['internalId']]
        if len(selected)!=1: raise ValueError('Allocation factor absent or ambiguous '+pid+' '+str(e['internalId']))
        return float(selected[0]['value'])

def main():
    global OUT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=OUT,help='Use a new directory for a substantive revised run.')
    OUT=parser.parse_args().output_dir.resolve()
    numerical_inputs=['data/bom.csv','data/mapping.json','data/sources/commons-merged-hybrid.zip','scripts/calculate.py']
    input_hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in numerical_inputs}
    expected_archive='4cf9bfdc5a8c9a531f9a6f3ba681f18014f25cf9ee7033c96e720a689fc4d13d'
    if input_hashes['data/sources/commons-merged-hybrid.zip']!=expected_archive:
        raise ValueError('Numerical archive does not match the pinned source hash.')
    stamp=OUT/'run_inputs.json'
    if stamp.exists() and json.loads(stamp.read_text())!=input_hashes:
        raise ValueError('Inputs or solver changed. Preserve the independent run and supply --output-dir with a new run directory.')
    OUT.mkdir(parents=True,exist_ok=True)
    db=Inventory(ROOT/'data'/'sources'/'commons-merged-hybrid.zip')
    print('Loaded',len(db.processes),'processes;',len(db.categories),'impact categories',flush=True)
    mapping=json.loads((ROOT/'data'/'mapping.json').read_text())
    bom=list(csv.DictReader((ROOT/'data'/'bom.csv').open(encoding='utf-8-sig')))
    labels=[r['material'] for r in bom]
    nodes=[]; index={}; refs={}; gaps=[]; links=[]; bio=[]; tech=[]; mapping_rows=[]
    def add(pid,e):
        key=(pid,e['internalId'])
        if key not in index:
            index[key]=len(nodes); nodes.append(key); refs[key]=e
        return index[key]
    roots=[]
    for i,r in enumerate(bom):
        mass=float(r['finished_mass_g'])/1000
        m=mapping[r['material']]; pid=m['process_id']
        row=dict(material=r['material'],finished_mass_g=float(r['finished_mass_g']),demand_kg=mass,scope=r['scope'],**m)
        if pid:
            p=db.processes[pid]; q=db.reference(pid)
            assert q['unit']['name']=='kg', (pid,q['unit'])
            roots.append((add(pid,q),i,mass))
            doc=p.get('processDocumentation',{})
            row.update(dataset_name=p['name'],version=p.get('version'),geography=p.get('location',{}).get('name','unknown'),
                       valid_from=doc.get('validFrom','unknown'),valid_until=doc.get('validUntil','unknown'),
                       reference_flow_id=q['flow']['@id'],reference_amount=q['amount'],reference_unit=q['unit']['name'],
                       process_type=p.get('processType'),description=p.get('description',''),
                       database_tags='; '.join(p.get('tags',[])),
                       price_documentation=doc.get('dataTreatmentDescription',''),
                       file_sha256=hashlib.sha256(db.z.read('processes/'+pid+'.json')).hexdigest(),
                       source_url='https://api.nal.usda.gov/FederalLCACommonsapi/browse/Federal_LCA_Commons/commons_merged_hybrid/PROCESS/'+pid,
                       retrieval_date='2026-10-08')
        mapping_rows.append(row)
    write_csv('material_mapping.csv',mapping_rows)
    for key in nodes:
        pid,_=key; j=index[key]; p=db.processes[pid]; ref=refs[key]
        q=db.converted(pid,ref)
        if q<=0: raise ValueError('Nonpositive provider reference quantity '+pid)
        for e in p['exchanges']:
            if e is ref: continue
            typ=db.flow(e['flow']['@id'])['flowType']
            amount=db.converted(pid,e)
            if not amount: continue
            # Allocate burdens, not co-product outputs; explicit avoided products retain negative demand.
            is_requirement=(typ=='PRODUCT_FLOW' and e['isInput']) or (typ=='WASTE_FLOW' and not e['isInput'])
            is_credit=bool(e.get('isAvoidedProduct'))
            if typ!='ELEMENTARY_FLOW' and not is_requirement and not is_credit: continue
            coefficient=amount/q*db.allocation(pid,ref,e)
            if typ=='ELEMENTARY_FLOW':
                # Keep direction separate; CFs already encode removal/uptake semantics by flow identity.
                bio.append(((e['flow']['@id'],bool(e['isInput'])),j,coefficient))
            else:
                provider,rule=db.provider(e)
                if provider:
                    upstream,upref=provider; k=add(upstream,upref)
                    tech.append((k,j,coefficient*(-1 if is_credit else 1)))
                    links.append({'consumer_node':j,'consumer_id':pid,'exchange_id':e['internalId'],
                                  'flow_id':e['flow']['@id'],'provider_node':k,'provider_id':upstream,'rule':rule,
                                  'coefficient':coefficient,'avoided_product':is_credit})
                else:
                    gaps.append({'consumer_node':j,'consumer_id':pid,'consumer_name':p['name'],'exchange_id':e['internalId'],
                                 'flow_id':e['flow']['@id'],'flow_name':e['flow'].get('name'),
                                 'reference_unit':e['flow'].get('refUnit'),'coefficient':coefficient,'reason':rule,'avoided_product':is_credit})
                    gaps[-1].update(flow_type=typ,direction='input' if e['isInput'] else 'output',
                                    database_tags='; '.join(p.get('tags',[])))
    n=len(nodes); ekeys=sorted(set(x[0] for x in bio)); eindex={key:i for i,key in enumerate(ekeys)}
    T=sparse.coo_matrix(([t[2] for t in tech],([t[0] for t in tech],[t[1] for t in tech])),shape=(n,n)).tocsc()
    A=sparse.eye(n,format='csc')-T
    B=sparse.coo_matrix(([t[2] for t in bio],([eindex[t[0]] for t in bio],[t[1] for t in bio])),shape=(len(ekeys),n)).tocsc()
    F=np.zeros((n,len(labels)))
    for j,i,mass in roots:F[j,i]+=mass
    S=splu(A).solve(F); G=B@S
    st=S.sum(axis=1); gt=G.sum(axis=1)
    residual=float(np.max(np.abs(A@S-F)))
    print('Solved',n,'allocated provider nodes;',len(ekeys),'flow/direction rows;',len(gaps),'missing provider exchanges; residual',residual,flush=True)
    methods=[{'id':m['@id'],'name':m['name'],'version':m.get('version'),'categories':m.get('impactCategories')} for m in db.methods]
    (OUT/'available_methods.json').write_text(json.dumps(methods,indent=2))
    cats=[c for c in db.categories if c['name']=='AR6-100']
    if len(cats)!=1:
        print('GWP candidates',[(c['@id'],c['name']) for c in cats])
        raise ValueError('Select an unambiguous AR6 GWP100 category')
    cat=cats[0]; cfs={}; inventory_fids={k[0] for k in ekeys}
    for cf in cat['impactFactors']:
        fid=cf['flow']['@id']
        if fid not in inventory_fids: continue
        if cf.get('location'): raise ValueError('Regional CF requires explicit matching')
        e={'flow':cf['flow'],'flowProperty':cf['flowProperty'],'unit':cf['unit']}
        v=float(cf['value'])/db.conversion(e)
        if fid in cfs and cfs[fid]!=v: raise ValueError('Conflicting CFs for '+fid)
        cfs[fid]=v
    cv=np.array([cfs.get(fid,0.0) for fid,inp in ekeys]); C=sparse.csr_matrix(cv.reshape(1,-1))
    h=np.asarray(C@G).ravel(); ht=float(h.sum())
    flows=[]
    for i,(fid,inp) in enumerate(ekeys):
        fl=db.flow(fid)
        refprop=next(p for p in fl['flowProperties'] if p.get('isRefFlowProperty'))
        prop=json.loads(db.z.read('flow_properties/'+refprop['flowProperty']['@id']+'.json'))
        ugid=prop['unitGroup']['@id']; unit=next(u['name'] for u in db.units.values() if u['group']==ugid and u.get('isRefUnit'))
        row={'flow_id':fid,'flow_name':fl['name'],'compartment':fl.get('category'),'direction':'input' if inp else 'output',
             'amount':float(gt[i]),'unit':unit,'cf':cfs.get(fid),'cf_status':'matched UUID' if fid in cfs else 'not characterized by selected method',
             'gwp100_kg_co2e':float(gt[i]*cfs[fid]) if fid in cfs else None}
        flows.append(row)
    write_csv('elementary_flows.csv',flows)
    write_csv('uncharacterized_flows.csv',[r for r in flows if r['cf'] is None])
    for gap in gaps:
        gap['unresolved_quantity_per_basket']=gap['coefficient']*st[gap['consumer_node']]
    write_csv('missing_providers.csv',gaps)
    write_csv('unlinked_product_inputs.csv',[g for g in gaps if g['flow_type']=='PRODUCT_FLOW'])
    write_csv('unlinked_waste_outputs.csv',[g for g in gaps if g['flow_type']=='WASTE_FLOW'])
    write_csv('provider_links.csv',links)
    activity=[]
    for j,key in enumerate(nodes):
        pid,_=key;p=db.processes[pid];ref=refs[key]
        row={'node':j,'process_id':pid,'process_name':p['name'],'reference_flow_id':ref['flow']['@id'],
             'reference_exchange_id':ref['internalId'],'activity_reference_units':float(st[j]),
             'reference_unit':ref['flow'].get('refUnit',ref['unit']['name']),
             'dataset_runs_allocated_column':float(st[j]/db.converted(pid,ref)),
             'allocation_method':p.get('defaultAllocationMethod','NO_ALLOCATION'),
             'direct_gwp100_kg_co2e':float((C@B[:,j]).toarray()[0,0]*st[j])}
        activity.append(row)
    write_csv('process_activity.csv',activity)
    write_csv('process_manifest.csv',[
        {'process_id':pid,'name':db.processes[pid]['name'],'version':db.processes[pid].get('version'),
         'database_tags':'; '.join(db.processes[pid].get('tags',[])),
         'file_sha256':hashlib.sha256(db.z.read('processes/'+pid+'.json')).hexdigest(),
         'archive_path':'processes/'+pid+'.json','retrieval_date':'2026-10-08'}
        for pid in sorted(set(k[0] for k in nodes))])
    contrib=[]
    for i,r in enumerate(bom):
        pid=mapping[r['material']]['process_id']; missing_mass=pid is None
        affected=[g for g in gaps if abs(S[g['consumer_node'],i]*g['coefficient'])>1e-20]
        contrib.append({'material':r['material'],'mass_g':float(r['finished_mass_g']),'scope':r['scope'],
                        'gwp100_characterized_subtotal_kg_co2e':None if missing_mass else float(h[i]),
                        'missing_provider_exchange_count':None if missing_mass else len(affected),
                        'unlinked_product_inputs':None if missing_mass else sum(g['flow_type']=='PRODUCT_FLOW' for g in affected),
                        'unlinked_waste_outputs':None if missing_mass else sum(g['flow_type']=='WASTE_FLOW' for g in affected),
                        'status':'not calculated: missing material provider' if missing_mass else ('partial: upstream gaps' if affected else 'calculated within material-supply boundary'),
                        'match_type':mapping[r['material']]['status']})
    write_csv('contributions.csv',contrib)
    # Keep formulas unique even if the same allocation node was visited more than once.
    formulas={ (x['process_id'],x['exchange_id']):x for x in db.formulas }
    write_csv('formula_audit.csv',formulas.values())
    sparse.save_npz(OUT/'A.npz',A); sparse.save_npz(OUT/'B.npz',B); sparse.save_npz(OUT/'C.npz',C)
    np.savez_compressed(OUT/'vectors.npz',f=F.sum(axis=1),s=st,g=gt,h=np.array([ht]),F=F,S=S,G=G,component_h=h)
    summary={'run_id':OUT.name,'status':'partial material-supply calculation; not a complete factory-gate footprint',
             'kettle_mass_g':sum(float(r['finished_mass_g']) for r in bom if r['scope']=='Kettle'),
             'packaging_mass_g':sum(float(r['finished_mass_g']) for r in bom if r['scope']=='Packaging'),
             'total_mass_g':sum(float(r['finished_mass_g']) for r in bom),
             'mapped_mass_g':sum(float(r['finished_mass_g']) for r in bom if mapping[r['material']]['process_id']),
             'missing_materials':[r['material'] for r in bom if not mapping[r['material']]['process_id']],
             'complete_factory_gate_gwp100_kg_co2e':None,'characterized_material_supply_subtotal_kg_co2e':ht,
             'process_nodes':n,'elementary_flow_direction_rows':len(ekeys),'linked_exchanges':len(links),
             'missing_provider_exchanges':len(gaps),'characterized_flow_rows':sum(fid in cfs for fid,inp in ekeys),
             'unlinked_product_input_exchanges':sum(g['flow_type']=='PRODUCT_FLOW' for g in gaps),
             'unlinked_waste_output_exchanges':sum(g['flow_type']=='WASTE_FLOW' for g in gaps),
             'negative_activity_nodes':int(np.sum(st < -1e-12)),
             'uncharacterized_flow_rows':sum(fid not in cfs for fid,inp in ekeys),
             'matrix_residual_max_abs':residual,'contribution_sum_error':abs(sum(r['direct_gwp100_kg_co2e'] for r in activity)-ht),
             'method':{k:v for k,v in cat.items() if k!='impactFactors'},
             'versions':{'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__},
             'formula_exchange_count':len(formulas),'max_formula_cache_difference':max((abs(x['difference']) for x in formulas.values()),default=0),
             'uncertainty':'not calculated','assumed_yield':1.0}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2))
    (OUT/'characterization_category.json').write_text(json.dumps(cat,indent=2))
    stamp.write_text(json.dumps(input_hashes,indent=2))
    print(json.dumps(summary,ensure_ascii=True),flush=True)

if __name__=='__main__':main()
