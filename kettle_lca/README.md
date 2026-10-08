# BC1 kettle: process activity, elementary inventory and GWP100

**Calculation status: partial.** The characterized material-supply subtotal is **3.025601 kg CO2-eq** for the quantities in one kettle's BOM. The complete manufactured-and-packaged factory-gate footprint is **not calculated**. Missing materials, conversion, assembly and unresolved background requirements are not numerical zeros. This subtotal is not a proven lower bound because source inventories also contain credits and removals.

## 1. Study identity and purpose

Study: BC1 1 L plastic electric kettle, U.S. material-supply screening. Public alias: KSY-99. Repository URL: https://github.com/KSY-99/kettle-lca. Run: `independent-2026-10-08`; study/retrieval date: 2026-10-08, Asia/Seoul. Goal: execute `A s = f`, `g = B s`, `h = C g` using the supplied BOM and traceable public inventory. Intended comparison: no alternative kettle specified; two explicit input sensitivities are provided.

This is the independent baseline; no classmates' results were supplied. Baseline Git tag: independent-2026-10-08. The exact publication commit SHA is available from Git history; this README does not embed its own future hash. The user subsequently requested GitHub upload and explicitly selected a new public repository named `kettle-lca`. Publication status: Public GitHub publication authorized by the user on 2026-10-08. The attachment's ten-section structure is reporting context; course submission was not requested.

## 2. Product, declared unit and system boundary

Target declared unit: one manufactured and packaged BC1 representative 1 L plastic electric kettle at the factory gate. It is a base case, not an identified commercial model. The supplied BOM passes the **723.0 g kettle + 137.8 g packaging = 860.8 g** check. BOM source: user's message, 2026-10-08, stored at [data/bom.csv](data/bom.csv). The [classroom reference](https://tiangong-lca-decision-lab.ecodino73.chatgpt.site) attributes the same BOM to the EU Electric Kettles preparatory study (2020), Task 4, Tables 4-3, 4-4 and 4-8; the original PDF was not independently audited in this run.

Actual calculated boundary: supply of nine mapped material quantities, including their linked upstream processes and the original dataset recycling conventions. Represented finished mass: **818.8 g (95.1208%)**. Unmapped: brass 20.25 g, POM 9.75 g, silicone 12 g, totaling 42 g. Mass coverage is not impact coverage.

Unquantified within the intended factory-gate boundary: component molding/forming, PVC compounding, wire/component fabrication, foil conversion, box converting/printing, assembly energy, factory-specific transport, production losses and associated scrap treatment. Database-internal transport and energy remain included. Customer delivery, kettle operation and kettle end-of-life are excluded. No use or end-of-life extension was calculated.

Scenario geography: U.S. background where available, with North American resin datasets and stainless technology based on Europe with American upstream conditions. A single common reference year is not available: source vintages differ and are recorded in the mapping table. The archive release date does not imply that all measurements are from 2026.

## 3. Foreground inventory and quantitative assumptions

| Material | Finished mass, g | Characterized subtotal, kg CO2-eq | Match status |
|---|---:|---:|---|
| Stainless steel | 186.00 | 1.448245 | grade proxy |
| Brass | 20.25 | Not calculated | Missing provider |
| Copper | 15.00 | 0.109964 | monetary proxy |
| Polypropylene (PP) | 350.25 | 0.752651 | resin match |
| Polyvinyl chloride (PVC) | 43.50 | 0.092100 | grade proxy |
| Nylon, grade unspecified | 49.50 | 0.146418 | grade and monetary proxy |
| Polyoxymethylene (POM) | 9.75 | Not calculated | Missing provider |
| Polycarbonate (PC) | 6.75 | 0.084387 | monetary proxy |
| Acrylonitrile-butadiene-styrene (ABS) | 30.00 | 0.093521 | resin match |
| Silicone | 12.00 | Not calculated | Missing provider |
| LDPE packaging foil | 6.30 | 0.015000 | resin only |
| Cardboard packaging | 131.50 | 0.283316 | packaging proxy |

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

**Supplier closure fails:** 695 product-input exchange instances and 72201 waste-output instances lack a unique connected provider in the assembled graph. Counts are per allocated node/exchange, not distinct suppliers, and include very small or zero-activity requirements. Many waste outputs are USEEIO waste-generation reporting flows; they are not elementary emissions. Attaching generic waste treatment without checking existing monetary waste-service purchases could double count. All are retained in diagnostics; no claim is made that every waste row represents an omitted additional GWP burden.

[Unlinked product inputs](results/independent-2026-10-08/unlinked_product_inputs.csv) and [unlinked waste outputs](results/independent-2026-10-08/unlinked_waste_outputs.csv) quantify these exchanges. The reported number characterizes the solvable retained subgraph. Missing-provider contributions are unknown, not modeled as physically zero. No mass, cost or impact threshold was used to silently discard them.

Of 5273 elementary flow/direction rows, 118 have explicit factors (including true zero factors); 5155 lack a factor in this climate method. Most non-climate pollutants/resources are outside GWP100. Four detected air HCFC names (`HCFC-121a`, `HCFC-132b`, `HCFC-253`, `HCFC-253fb`) remain unmatched; water emissions are not relabelled as air emissions. Missing CF fields stay blank in the [uncharacterized-flow table](results/independent-2026-10-08/uncharacterized_flows.csv). Sparse C uses zero entries for the *characterized subtotal only*, not as an assertion of zero physical impact.

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

Characterized subtotal: **3.025601 kg CO2-eq**. Complete factory-gate GWP100: **not calculated**. This distinction applies to every output. The detailed contribution table above covers all twelve BOM rows; absent values are not numerical zeros. Top three contributors *within the partial model*: Stainless steel: 1.448245 kg CO2-eq; Polypropylene (PP): 0.752651 kg CO2-eq; Cardboard packaging: 0.283316 kg CO2-eq.

The actual solver produced **1422 allocated provider nodes**, **89,833 supplier links** and **5,273 elementary flow/direction rows**. [Process activity](results/independent-2026-10-08/process_activity.csv) and [summed elementary flows](results/independent-2026-10-08/elementary_flows.csv) are complete for the modeled subgraph.

The following are the eight largest absolute characterized flow contributions. Each row below is the generic `air` compartment, except the CO2 input, which is `resource/air`; the CSV preserves all compartments separately.

| Elementary flow | Direction | Summed quantity | Unit | CF, kg CO2-eq/unit | Contribution, kg CO2-eq |
|---|---|---:|---|---:|---:|
| Carbon dioxide | output | 2.71471238 | kg | 1 | 2.714712 |
| Methane | output | 0.00854232051 | kg | 29.8 | 0.254561 |
| Nitrous oxide | output | 0.000196929924 | kg | 273 | 0.053762 |
| Carbon dioxide | input | 0.0147876429 | kg | -1 | -0.014788 |
| Sulfur hexafluoride | output | 1.94750097e-07 | kg | 25200 | 0.004908 |
| HFC-23 | output | 3.27943003e-07 | kg | 14600 | 0.004788 |
| HCFC-22 | output | 1.16798219e-06 | kg | 1960 | 0.002289 |
| Methane, biogenic | output | 7.78013637e-05 | kg | 27 | 0.002101 |

Checks: BOM mass and g→kg conversion pass; reference quantities and exchange unit/property compatibility are validated during construction; max absolute `A S − F` residual is **2.15e-16**; contribution sum difference is **4.44e-16 kg CO2-eq**. Twelve numerical/security/omission checks passed in [verification.json](results/independent-2026-10-08/verification.json), including an analytic cyclic-system benchmark and an independent Neumann iteration (48 steps; max activity difference approximately 6.92e−14). These prove arithmetic for the specified matrix, not completeness or empirical accuracy. A universal elemental/mass balance across all heterogeneous background processes was not calculated. Supplier closure and complete factory-gate scope both fail.

The steel debit, resin energy/feedstocks and packaging production drive this partial result. Monetary proxy prices affect nylon, copper and PC. No complete-kettle ranking, environmental superiority claim, confidence interval, or claim of publication-grade comparability is supported. No additional generic electricity, resin or recycling burden was added to cumulative source inventories; nevertheless, the mixed source allocation/recycling conventions remain a limitation that arithmetic checks cannot resolve.

## 8. Uncertainty and sensitivity

Probabilistic uncertainty was **not calculated**: no defensible foreground parameter distributions/correlations were supplied, and structural/provider gaps dominate. Mean, median, P05/P95, central 90% interval, Monte Carlo draw count, seed and convergence of a stochastic simulation: not applicable. Published source uncertainty fields were not sampled.

Two deterministic sensitivities are available in [sensitivity.csv](results/independent-2026-10-08/sensitivity.csv). All numbers remain partial material-supply subtotals. The 95% yield is illustrative, not sourced; additional scrap treatment is still excluded. The nylon change compares publisher price bridges to the same sector, not physical PA6 versus PA66 manufacturing inventories.

| Case | Partial subtotal, kg CO2-eq | Change, kg CO2-eq |
|---|---:|---:|
| Baseline partial material supply | 3.025601 | +0.000000 |
| PP purchase yield 95%; other inputs unchanged; scrap treatment excluded | 3.065215 | +0.039613 |
| Nylon 66 monetary bridge instead of nylon 6; same plastics sector, different published price | 3.052842 | +0.027241 |

Parameter sensitivity, provider/system-model uncertainty, and variability between repeated AI runs are different concepts; repeated AI-run variability was not assessed.

## 9. Codex and human decisions

Assistant identity available in this session: Codex, GPT-6 based. Exact UI model variant, sampling settings, temperature and reasoning settings: unknown. Run date: 2026-10-08. The human supplied the BOM/reference sources and explicitly selected a U.S. inventory scenario with compatible GWP100. No student/group identity was supplied.

Consequential assistant decisions: use a pinned public Commons Merged Hybrid archive; use AR6-100; keep nine mapped materials and report three unmatched; assume 100% purchase yield, 304 coil, nylon 6 and corrugated cardboard; retain published monetary bridges, source allocation and scrap conventions; do not create ungrounded POM/silicone/brass inventories or manufacturing energy. Reject LLDPE film as an exact LDPE match and avoid adding an entire molding process on top of its resin input. See [decision log](decision-log.md) and [search record](data/search_log.json). Technical corrections during implementation included safe parsing of source `if(a=1;...;...)` expressions and distinguishing waste-output diagnostics from product-input gaps. Verification was performed by code in this session; independent human review has not been reported.

## 10. Independent and revised runs

The preserved independent outputs are under `results/independent-2026-10-08/`; [results hashes](results/independent-2026-10-08/output_manifest.json) identify the finalized files. Baseline Git tag: independent-2026-10-08; use the repository history for the exact published commit. Repository URL: https://github.com/KSY-99/kettle-lca. No external comparison or revised run occurred. Prior commit, one post-comparison changed decision, predicted change, revised result and percentage difference: not applicable. The two declared sensitivity cases do not overwrite the baseline or constitute a class-comparison revision.

The solver compares saved hashes of its code, BOM, mapping and archive before rerunning. Identical inputs can reproduce this run. For a substantive change, use `python scripts/calculate.py --output-dir results/revised-run-name` and preserve the independent results. The report and verification scripts currently target the independent run; adapt their output selection explicitly for a revision and record the changed input and comparison.
