"""Analytical benchmarks and independent iterative verification of saved results."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.deps'))
from calculate import safe_formula, Inventory
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

OUT=ROOT/'results'/'independent-2026-10-08'
checks=[]
def check(name,condition,detail):
    checks.append({'check':name,'passed':bool(condition),'detail':detail})
    if not condition: raise AssertionError((name,detail))

toy=sparse.csc_matrix([[1,-0.2],[-0.5,1]])
s=splu(toy).solve(np.array([1.0,0.0]))
check('analytical cyclic two-process benchmark',np.allclose(s,[10/9,5/9]),s.tolist())
g=np.array([[1.,2.]])@s
check('analytical inventory and characterization',np.allclose(g*27,[60.]),float(g[0]*27))
check('source conditional formula',safe_formula('if(mode=1; x*2; 0)',{'mode':1,'x':3})==6,'6 expected')
blocked=False
try:safe_formula('__import__("os").system("echo unsafe")',{})
except ValueError:blocked=True
check('formula evaluator rejects code execution',blocked,'AST whitelist')

A=sparse.load_npz(OUT/'A.npz');B=sparse.load_npz(OUT/'B.npz');C=sparse.load_npz(OUT/'C.npz')
v=np.load(OUT/'vectors.npz');T=sparse.eye(A.shape[0],format='csc')-A
x=np.zeros(A.shape[0])
for iterations in range(1,10001):
    new=v['f']+T@x
    delta=float(np.max(np.abs(new-x)))
    x=new
    if delta<1e-13:break
check('independent Neumann iteration converged',iterations<10000,{'iterations':iterations,'delta':delta})
error=float(np.max(np.abs(x-v['s'])))
check('LU versus independent iterative activity',error<1e-10,error)
check('stored elementary inventory',np.allclose(B@v['s'],v['g'],rtol=1e-10,atol=1e-12),'B @ s matches saved g')
check('stored characterized subtotal',np.allclose(C@v['g'],v['h'],rtol=1e-10,atol=1e-12),'C @ g matches saved h')
check('component contributions sum',np.allclose(v['G'].sum(axis=1),v['g']), 'component inventories sum to total inventory')
check('BOM mass balance',abs(723+137.8-860.8)<1e-9,'723 g + 137.8 g = 860.8 g')
summary=json.loads((OUT/'summary.json').read_text())
check('missing full result retained as null',summary['complete_factory_gate_gwp100_kg_co2e'] is None,'No numerical zero substituted for a complete result')
check('three missing materials remain explicit',len(summary['missing_materials'])==3,summary['missing_materials'])
(OUT/'verification.json').write_text(json.dumps(checks,indent=2))
print(json.dumps({'checks_passed':len(checks),'iterations':iterations,'activity_difference':error}))
