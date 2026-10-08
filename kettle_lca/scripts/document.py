"""Build the study README, search record, sensitivities and file manifest."""
import csv
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results'/'independent-2026-10-08'
def rows(name):return list(csv.DictReader((OUT/name).open(encoding='utf-8-sig')))
summary=json.loads((OUT/'summary.json').read_text())
publication_path=ROOT/'publication.json'
publication=json.loads(publication_path.read_text()) if publication_path.exists() else {}
repo_url=publication.get('repository_url','unknown (local workspace only)')
alias=publication.get('github_login','unknown (not supplied)')
publication_status=publication.get('status','not published')
baseline_tag=publication.get('baseline_tag','not created')
contributions=rows('contributions.csv')
mapping=rows('material_mapping.csv')
flows=rows('elementary_flows.csv')
z=zipfile.ZipFile(ROOT/'data'/'sources'/'commons-merged-hybrid.zip')
catalog=json.loads((ROOT/'data'/'catalog.json').read_text())
queries={
 'Stainless steel':['stainless'], 'Brass':['brass','copper zinc','copper-zinc'], 'Copper':['copper'],
 'Polypropylene (PP)':['polypropylene'], 'Polyvinyl chloride (PVC)':['polyvinyl chloride'],
 'Nylon, grade unspecified':['nylon','polyamide'], 'Polyoxymethylene (POM)':['polyoxymethylene','polyacetal','polyformaldehyde','acetal'],
 'Polycarbonate (PC)':['polycarbonate'], 'Acrylonitrile-butadiene-styrene (ABS)':['acrylonitrile-butadiene-styrene'],
 'Silicone':['silicone','siloxane','pdms'], 'LDPE packaging foil':['low-density polyethylene','low density polyethylene'],
 'Cardboard packaging':['cardboard','corrugated']}
searches=[]
for material,terms in queries.items():
    hits=[{k:p[k] for k in ['id','name','version','tags']} for p in catalog if p['path'].startswith('processes/') and any(t in p['name'].lower() for t in terms)]
    searches.append({'material':material,'queries':terms,'search_scope':'process names in downloaded Commons Merged Hybrid archive','candidates':hits})
(ROOT/'data'/'search_log.json').write_text(json.dumps(searches,indent=2))

subtotal=summary['characterized_material_supply_subtotal_kg_co2e']
pp=float(next(r for r in contributions if r['material']=='Polypropylene (PP)')['gwp100_characterized_subtotal_kg_co2e'])
nylon=float(next(r for r in contributions if r['material']=='Nylon, grade unspecified')['gwp100_characterized_subtotal_kg_co2e'])
p6=json.loads(z.read('processes/a2174501-418e-4b2e-9dbd-fa81f5f0bcc7.json'))
p66=json.loads(z.read('processes/052c051b-b37f-4f00-9fe8-f5b2764b69c1.json'))
def bridge_input(p):
    es=[e for e in p['exchanges'] if e['isInput']]
    assert len(es)==1
    return es[0]
b6,b66=bridge_input(p6),bridge_input(p66)
assert b6['flow']['@id']==b66['flow']['@id'] and b6['defaultProvider']['@id']==b66['defaultProvider']['@id']
scenarios=[{'scenario':'Baseline partial material supply','subtotal_kg_co2e':subtotal,'delta_kg_co2e':0},
 {'scenario':'PP purchase yield 95%; other inputs unchanged; scrap treatment excluded','subtotal_kg_co2e':subtotal+pp*(1/.95-1),'delta_kg_co2e':pp*(1/.95-1)},
 {'scenario':'Nylon 66 monetary bridge instead of nylon 6; same plastics sector, different published price','subtotal_kg_co2e':subtotal+nylon*(b66['amount']/b6['amount']-1),'delta_kg_co2e':nylon*(b66['amount']/b6['amount']-1)}]
with (OUT/'sensitivity.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,list(scenarios[0]));w.writeheader();w.writerows(scenarios)

numeric=[r for r in contributions if r['gwp100_characterized_subtotal_kg_co2e']]
table='\n'.join(f"| {r['material']} | {float(r['mass_g']):.2f} | {float(r['gwp100_characterized_subtotal_kg_co2e']):.6f} | {r['match_type']} |" if r['gwp100_characterized_subtotal_kg_co2e'] else f"| {r['material']} | {float(r['mass_g']):.2f} | Not calculated | Missing provider |" for r in contributions)
largest=sorted(numeric,key=lambda r:float(r['gwp100_characterized_subtotal_kg_co2e']),reverse=True)[:3]
top='; '.join(f"{r['material']}: {float(r['gwp100_characterized_subtotal_kg_co2e']):.6f} kg CO2-eq" for r in largest)
climate=sorted([r for r in flows if r['gwp100_kg_co2e']],key=lambda r:abs(float(r['gwp100_kg_co2e'])),reverse=True)[:8]
flowtable='\n'.join(f"| {r['flow_name']} | {r['direction']} | {float(r['amount']):.9g} | {r['unit']} | {float(r['cf']):g} | {float(r['gwp100_kg_co2e']):.6f} |" for r in climate)
sens='\n'.join(f"| {r['scenario']} | {r['subtotal_kg_co2e']:.6f} | {r['delta_kg_co2e']:+.6f} |" for r in scenarios)
doc=f'''# BC1 kettle: process activity, elementary inventory and GWP100

**Calculation status: partial.** The characterized material-supply subtotal is **{subtotal:.6f} kg CO2-eq** for the quantities in one kettle's BOM. The complete manufactured-and-packaged factory-gate footprint is **not calculated**. Missing materials, conversion, assembly and unresolved background requirements are not numerical zeros. This subtotal is not a proven lower bound because source inventories also contain credits and removals.

## 1. Study identity and purpose

Study: BC1 1 L plastic electric kettle, U.S. material-supply screening. Public alias: {alias}. Repository URL: {repo_url}. Run: `independent-2026-10-08`; study/retrieval date: 2026-10-08, Asia/Seoul. Goal: execute `A s = f`, `g = B s`, `h = C g` using the supplied BOM and traceable public inventory. Intended comparison: no alternative kettle specified; two explicit input sensitivities are provided.

This is the independent baseline; no classmates' results were supplied. Baseline Git tag: {baseline_tag}. The exact publication commit SHA is available from Git history; this README does not embed its own future hash. The user subsequently requested GitHub upload and explicitly selected a new public repository named `kettle-lca`. Publication status: {publication_status}. The attachment's ten-section structure is reporting context; course submission was not requested.

## 2. Product, declared unit and system boundary

Target declared unit: one manufactured and packaged BC1 representative 1 L plastic electric kettle at the factory gate. It is a base case, not an identified commercial model. The supplied BOM passes the **723.0 g kettle + 137.8 g packaging = 860.8 g** check. BOM source: user's message, 2026-10-08, stored at [data/bom.csv](data/bom.csv). The [classroom reference](https://tiangong-lca-decision-lab.ecodino73.chatgpt.site) attributes the same BOM to the EU Electric Kettles preparatory study (2020), Task 4, Tables 4-3, 4-4 and 4-8; the original PDF was not independently audited in this run.

Actual calculated boundary: supply of nine mapped material quantities, including their linked upstream processes and the original dataset recycling conventions. Represented finished mass: **818.8 g ({818.8/860.8*100:.4f}%)**. Unmapped: brass 20.25 g, POM 9.75 g, silicone 12 g, totaling 42 g. Mass coverage is not impact coverage.

Unquantified within the intended factory-gate boundary: component molding/forming, PVC compounding, wire/component fabrication, foil conversion, box converting/printing, assembly energy, factory-specific transport, production losses and associated scrap treatment. Database-internal transport and energy remain included. Customer delivery, kettle operation and kettle end-of-life are excluded. No use or end-of-life extension was calculated.

Scenario geography: U.S. background where available, with North American resin datasets and stainless technology based on Europe with American upstream conditions. A single common reference year is not available: source vintages differ and are recorded in the mapping table. The archive release date does not imply that all measurements are from 2026.

## 3. Foreground inventory and quantitative assumptions

| Material | Finished mass, g | Characterized subtotal, kg CO2-eq | Match status |
|---|---:|---:|---|
{table}

| Parameter | Value | Unit | Evidence / status |
|---|---:|---|---|
| Finished masses | As above | g/kettle | Sourced: user's BOM |
| Material purchase yield | 1.00 | kg finished/kg purchased | Assumed screening boundary; not measured |
| Purchased quantity | finished mass / 1000 / yield | kg | Calculated |
| Stainless grade | 304 coil | grade/form | Assumed material proxy |
| Nylon grade | Nylon 6 | grade | Assumed; alternate nylon 66 price bridge sensitivity |
| Cardboard type | Average corrugated board | type | Assumed packaging proxy |
| Conversion services | Not calculated | service units | Required quantities/matches unestablished |
| Assembly electricity | Unknown | kWh/kettle | Not in BOM; no invented zero |
| Foreground transport | Unknown | t-km/kettle | Distances/modes not supplied |
| Foreground losses/scrap | Not calculated | kg/kettle | 100% yield defines screening purchase mass only |

The plastics are resin supply, not finished molded components. An injection-molding candidate was inspected and rejected from this baseline because it already contains **1.034 kg PP resin, 6.444 MJ electricity, 0.1 kg corrugated packaging, transport and waste exchanges per kg output**. Adding its full inventory alongside resin supply would duplicate resin. Its use in a future component model must replace the corresponding supply route and reconcile packaging and scrap.

The stainless dataset contains extensive cumulative elementary flows but also an explicit scrap supplier. The solver follows that declared link once; it does not append a second generic electricity/material burden. The scrap provider describes EUROFER's *value-of-scrap* convention, not simply scrap collection. Its debit is retained. No additional future kettle recycling credit is claimed. Compatibility with a different recycling system model remains a limitation.

## 4. Background data and matching decisions

Primary calculation archive: [Commons Merged Hybrid](https://www.lcacommons.gov/lca-collaboration/Federal_LCA_Commons/commons_merged_hybrid/datasets), pinned repository revision `f04287a6c7b2955169a426423a9a1d6380ceeda9`, retrieved 2026-10-08; SHA-256 `4cf9bfdc5a8c9a531f9a6f3ba681f18014f25cf9ee7033c96e720a689fc4d13d` (78,740,869 bytes). It combines USLCI, electricity, woody biomass, USEEIO and methods. See [official package description](https://flcac-admin.github.io/FLCAC-docs/commons-merged/). Object tags contain multiple release vintages, including unchanged USLCI objects tagged `v1.2026-06.1`; these are retained, not relabelled as new measurements.

[Complete material mapping](results/independent-2026-10-08/material_mapping.csv) records UUIDs, object versions, dataset names, tags, geography, validity dates, reference flows/amounts/units, source endpoints, retrieval date, raw-object hashes and selection rationale. [All linked process hashes](results/independent-2026-10-08/process_manifest.csv), [archive manifest](data/sources/merged-download-manifest.json), [searches and alternatives](data/search_log.json), and [provider links](results/independent-2026-10-08/provider_links.csv) are supplied. The separate USLCI archive was retrieved to inspect candidates; all numerical results use the single merged archive, so duplicate imports are avoided.

Monetary proxies are explicitly hybrid inventory, not physical material-specific measurements:

| Material | Sector | Quantity / price basis |
|---|---|---|
| Copper | Copper, gold and silver concentrates; NAICS 331410 | 9.13 USD 2012 producer price/kg; publisher derives this from 10,558 USD/ton purchaser price in 2025 |
| Nylon 6 | Plastics; NAICS 325211 | 1.649258065 USD 2012 producer price/kg; 2,150 USD/ton purchaser price in 2025 |
| Polycarbonate | Plastics; NAICS 325211 | 6.970610088 USD 2012 producer price/kg; source uses 96.45 USD/23.4 lb sheet purchaser price in 2025 |

Each bridge multiplies its price by physical demand and purchases the specified USEEIO sector's reference output. Background USD quantities retain 2012 producer-price units. Publisher conversion ratios and original price descriptions are in the mapping CSV. No retail cost of a finished kettle is used. The copper sector is broader than refined copper, and PC sheet prices poorly represent resin pellets; these are substantive proxy limitations.

TianGong: the [official CLI documentation](https://github.com/tiangong-lca/cli) and organization repositories were reviewed. The CLI was not installed and no authenticated dataset session was established. Public-web searches for POM, silicone and brass did not provide a usable process export. Consequently, TianGong inventory was **not queried through its authenticated process search and not used**; no claim of database-wide absence is made. The three missing matches refer to the searched public archive, not to all possible LCA databases.

## 5. Calculation and impact-assessment methods

Columns are allocated `(process UUID, supplied output exchange)` pairs, since different co-products of one process can supply distinct demands. Exchanges are converted to the flow's reference property/unit using `amount × unit conversion / flow-property conversion`. Each process column is divided by its selected supplied reference-output amount. `T[i,j]` is the required amount of provider i per reference unit of j; **A = I − T**. The demand vector f contains the nine mapped BOM masses in kg. Missing BOM entries stay explicitly uncalculated, not zero-valued material results.

SciPy sparse LU solves `A s = f` and twelve component right-hand sides (missing materials have no modeled column contribution and their published impact stays null). `B` contains elementary exchange coefficients; `g = B s`. Elementary identities retain **UUID and input/output direction**, including distinct environmental compartments. Input quantities are stored positive; the downloaded method encodes uptake/removal through signed CFs. `C` contains matched factors and `h = C g` gives the characterized subtotal. `[A.npz, B.npz, C.npz]` and [vectors.npz](results/independent-2026-10-08/vectors.npz) preserve the exact numerical model. Process activity is expressed in reference units; `dataset_runs_allocated_column` is normalized activity divided by the original reference amount, not necessarily an observable factory production count.

Provider linking: explicit default provider with exact product/waste-flow identity and direction first, otherwise only a unique exact provider. Ambiguous matches are not guessed. Local/global parameter formulas are evaluated with a restricted AST evaluator; **766 exchange formulas matched their exported numeric defaults exactly**. Original default physical/economic/causal allocation factors are applied to burdens for the supplied co-product; preallocated `NO_ALLOCATION` datasets are not reallocated. Original avoided products and signed source exchanges are retained. There are 18 nodes with activity below −1e−12 from the resulting credit-containing model; their existence is disclosed rather than clipped away.

Characterization: **IPCC AR6 GWP100**, category `AR6-100`, UUID `a6206006-65bc-395c-8dc9-f12262f45a04`, object version `01.04.001`, IPCC method object `01.04.000`, built with LCIA Formatter 1.4.0 in the archive. [Full factor table](results/independent-2026-10-08/characterization_category.json). This is the `AR6-100` variant, not `AR6-100 Net Biogenic`. For example, the source method sets air-emitted CO2 to 1, generic methane to 29.8, N2O to 273, explicitly biogenic methane to 27, explicitly biogenic CO2 emissions to 0, and generic atmospheric CO2 resource uptake to −1. Original unlabelled CO2 is not reclassified as biogenic. Legacy source carbon accounting therefore limits comparability.

**Supplier closure fails:** {summary['unlinked_product_input_exchanges']} product-input exchange instances and {summary['unlinked_waste_output_exchanges']} waste-output instances lack a unique connected provider in the assembled graph. Counts are per allocated node/exchange, not distinct suppliers, and include very small or zero-activity requirements. Many waste outputs are USEEIO waste-generation reporting flows; they are not elementary emissions. Attaching generic waste treatment without checking existing monetary waste-service purchases could double count. All are retained in diagnostics; no claim is made that every waste row represents an omitted additional GWP burden.

[Unlinked product inputs](results/independent-2026-10-08/unlinked_product_inputs.csv) and [unlinked waste outputs](results/independent-2026-10-08/unlinked_waste_outputs.csv) quantify these exchanges. The reported number characterizes the solvable retained subgraph. Missing-provider contributions are unknown, not modeled as physically zero. No mass, cost or impact threshold was used to silently discard them.

Of {summary['elementary_flow_direction_rows']} elementary flow/direction rows, {summary['characterized_flow_rows']} have explicit factors (including true zero factors); {summary['uncharacterized_flow_rows']} lack a factor in this climate method. Most non-climate pollutants/resources are outside GWP100. Four detected air HCFC names (`HCFC-121a`, `HCFC-132b`, `HCFC-253`, `HCFC-253fb`) remain unmatched; water emissions are not relabelled as air emissions. Missing CF fields stay blank in the [uncharacterized-flow table](results/independent-2026-10-08/uncharacterized_flows.csv). Sparse C uses zero entries for the *characterized subtotal only*, not as an assertion of zero physical impact.

## 6. How to reproduce the analysis

Tested on Windows/PowerShell, Python 3.12.14, NumPy 2.3.5, SciPy 1.18.1. From this directory:

```powershell
python -m pip install --target .deps -r requirements.txt
python scripts/download_merged.py
python scripts/inspect_archive.py
python scripts/calculate.py
python scripts/verify.py
python scripts/document.py
```

The original host used the bundled Python 3.12.14 runtime. NumPy already existed; only SciPy was installed into `.deps` there. Code does not require openLCA or a remote TianGong solve.

`download_merged.py` uses the exact public repository revision and validates its expected SHA-256. If the server retires that revision or returns different bytes, use the preserved matching cache or retrieve that exact archived release; do not silently replace it with current data. The auxiliary `retrieve.py` collected reference HTML/release listings and prepared the separate USLCI archive; it is not necessary for rerunning the calculation. `data/sources/commons-merged-hybrid.zip` is the numerical source, `data/bom.csv` and `data/mapping.json` are foreground controls. `results/independent-2026-10-08/` contains matrices, activity, inventory, contributions, characterization, verification and gaps. Open this README for the report.

Public archive retrieval requires no user account in this tested route. USDA's documented API route can instead use `LCA_COMMONS_API_KEY` (not needed by this pinned public-download script); use the official [API guide](https://www.lcacommons.gov/lca-commons-api-guide). No private credentials were used or stored. `DEMO_KEY` in auxiliary source-retrieval examples is the public demonstration constant. For a future authenticated TianGong search, follow official OAuth login; its documented configuration names include `TIANGONG_LCA_API_BASE_URL`, `TIANGONG_LCA_SUPABASE_PUBLISHABLE_KEY` and `TIANGONG_LCA_AUTH_MODE`. This run does not depend on them.

Source datasets are public; individual metadata and source terms still apply. Downloaded archives and installed binaries are excluded from Git by `.gitignore`. Do not infer blanket relicensing of third-party inventories. No random draws or seed were used. Manual steps still needed for a complete result: supply/approve the three missing material inventories and manufacturing quantities, resolve relevant upstream gaps, and check system-model compatibility.

## 7. Results, checks and interpretation

Characterized subtotal: **{subtotal:.6f} kg CO2-eq**. Complete factory-gate GWP100: **not calculated**. This distinction applies to every output. The detailed contribution table above covers all twelve BOM rows; absent values are not numerical zeros. Top three contributors *within the partial model*: {top}.

The actual solver produced **{summary['process_nodes']} allocated provider nodes**, **{summary['linked_exchanges']:,} supplier links** and **{summary['elementary_flow_direction_rows']:,} elementary flow/direction rows**. [Process activity](results/independent-2026-10-08/process_activity.csv) and [summed elementary flows](results/independent-2026-10-08/elementary_flows.csv) are complete for the modeled subgraph.

The following are the eight largest absolute characterized flow contributions. Each row below is the generic `air` compartment, except the CO2 input, which is `resource/air`; the CSV preserves all compartments separately.

| Elementary flow | Direction | Summed quantity | Unit | CF, kg CO2-eq/unit | Contribution, kg CO2-eq |
|---|---|---:|---|---:|---:|
{flowtable}

Checks: BOM mass and g→kg conversion pass; reference quantities and exchange unit/property compatibility are validated during construction; max absolute `A S − F` residual is **{summary['matrix_residual_max_abs']:.3g}**; contribution sum difference is **{summary['contribution_sum_error']:.3g} kg CO2-eq**. Twelve numerical/security/omission checks passed in [verification.json](results/independent-2026-10-08/verification.json), including an analytic cyclic-system benchmark and an independent Neumann iteration (48 steps; max activity difference approximately 6.92e−14). These prove arithmetic for the specified matrix, not completeness or empirical accuracy. A universal elemental/mass balance across all heterogeneous background processes was not calculated. Supplier closure and complete factory-gate scope both fail.

The steel debit, resin energy/feedstocks and packaging production drive this partial result. Monetary proxy prices affect nylon, copper and PC. No complete-kettle ranking, environmental superiority claim, confidence interval, or claim of publication-grade comparability is supported. No additional generic electricity, resin or recycling burden was added to cumulative source inventories; nevertheless, the mixed source allocation/recycling conventions remain a limitation that arithmetic checks cannot resolve.

## 8. Uncertainty and sensitivity

Probabilistic uncertainty was **not calculated**: no defensible foreground parameter distributions/correlations were supplied, and structural/provider gaps dominate. Mean, median, P05/P95, central 90% interval, Monte Carlo draw count, seed and convergence of a stochastic simulation: not applicable. Published source uncertainty fields were not sampled.

Two deterministic sensitivities are available in [sensitivity.csv](results/independent-2026-10-08/sensitivity.csv). All numbers remain partial material-supply subtotals. The 95% yield is illustrative, not sourced; additional scrap treatment is still excluded. The nylon change compares publisher price bridges to the same sector, not physical PA6 versus PA66 manufacturing inventories.

| Case | Partial subtotal, kg CO2-eq | Change, kg CO2-eq |
|---|---:|---:|
{sens}

Parameter sensitivity, provider/system-model uncertainty, and variability between repeated AI runs are different concepts; repeated AI-run variability was not assessed.

## 9. Codex and human decisions

Assistant identity available in this session: Codex, GPT-6 based. Exact UI model variant, sampling settings, temperature and reasoning settings: unknown. Run date: 2026-10-08. The human supplied the BOM/reference sources and explicitly selected a U.S. inventory scenario with compatible GWP100. No student/group identity was supplied.

Consequential assistant decisions: use a pinned public Commons Merged Hybrid archive; use AR6-100; keep nine mapped materials and report three unmatched; assume 100% purchase yield, 304 coil, nylon 6 and corrugated cardboard; retain published monetary bridges, source allocation and scrap conventions; do not create ungrounded POM/silicone/brass inventories or manufacturing energy. Reject LLDPE film as an exact LDPE match and avoid adding an entire molding process on top of its resin input. See [decision log](decision-log.md) and [search record](data/search_log.json). Technical corrections during implementation included safe parsing of source `if(a=1;...;...)` expressions and distinguishing waste-output diagnostics from product-input gaps. Verification was performed by code in this session; independent human review has not been reported.

## 10. Independent and revised runs

The preserved independent outputs are under `results/independent-2026-10-08/`; [results hashes](results/independent-2026-10-08/output_manifest.json) identify the finalized files. Baseline Git tag: {baseline_tag}; use the repository history for the exact published commit. Repository URL: {repo_url}. No external comparison or revised run occurred. Prior commit, one post-comparison changed decision, predicted change, revised result and percentage difference: not applicable. The two declared sensitivity cases do not overwrite the baseline or constitute a class-comparison revision.

The solver compares saved hashes of its code, BOM, mapping and archive before rerunning. Identical inputs can reproduce this run. For a substantive change, use `python scripts/calculate.py --output-dir results/revised-run-name` and preserve the independent results. The report and verification scripts currently target the independent run; adapt their output selection explicitly for a revision and record the changed input and comparison.
'''
(ROOT/'README.md').write_text(doc,encoding='utf-8')
manifest=[]
for f in sorted(OUT.iterdir()):
    if f.is_file() and f.name!='output_manifest.json':
        manifest.append({'file':f.name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(OUT/'output_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'README':str(ROOT/'README.md'),'subtotal':subtotal,'sensitivity':scenarios,'result_files':len(manifest)}))
