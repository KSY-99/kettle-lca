# Kettle LCA — BC1 1 L electric kettle

Reproducible U.S. material-supply screening using public LCA Commons data and IPCC AR6 GWP100.

**Result: 3.025601 kg CO₂-eq, partial material-supply subtotal.**

The complete manufactured-and-packaged kettle footprint is **not calculated**. Brass, POM, silicone, manufacturing/assembly, and unresolved background requirements remain unquantified. Missing values are not numerical zeros.

| Result | Value |
|---|---:|
| Kettle finished mass | 723.0 g |
| Packaging mass | 137.8 g |
| Total BOM mass | 860.8 g |
| Mapped material mass | 818.8 g |
| Allocated process nodes | 1,422 |
| Elementary flow/direction rows | 5,273 |
| Numerical verification checks passed | 12 |

The calculation follows `A s = f`, `g = B s`, then `h = C g`. An independent iterative solve agrees with the sparse LU solution to within approximately 7 × 10⁻¹⁴ in activity.

- [Korean HTML report: charts, material filters, calculations, verification and limitations](kettle_lca/reports/kettle-lca-report.html) — download and open in a browser; self-contained and works offline.
- [Full study report: methods, assumptions, sources, limitations and reproduction](kettle_lca/README.md)
- [Material contributions](kettle_lca/results/independent-2026-10-08/contributions.csv)
- [Process activity](kettle_lca/results/independent-2026-10-08/process_activity.csv)
- [Summed elementary flows and characterization](kettle_lca/results/independent-2026-10-08/elementary_flows.csv)
- [Verification](kettle_lca/results/independent-2026-10-08/verification.json)
- [Model inputs](kettle_lca/data/)
- [Calculation code](kettle_lca/scripts/)

## Reproduce

With Python 3.12, from `kettle_lca/`:

```shell
python -m pip install --target .deps -r requirements.txt
python scripts/download_merged.py
python scripts/inspect_archive.py
python scripts/calculate.py
python scripts/verify.py
python scripts/document.py
```

The numerical archive is retrieved by a pinned public revision and checked against its SHA-256. Large original source archives and installed libraries are excluded from this repository; their retrieval instructions are included. The finalized independent numerical outputs are preserved under `results/independent-2026-10-08/`.

To regenerate the Korean HTML report and SVG chart from the saved baseline, install the optional report dependencies and run:

```shell
python -m pip install --target .deps -r requirements-report.txt
python scripts/html_report.py
```

The report checks the baseline output hashes before rendering. It does not recalculate or modify the numerical model. The baseline tag and calculation commit remain preserved.

Third-party inventory data retain their original source terms. This repository does not assert a blanket license over those datasets.
