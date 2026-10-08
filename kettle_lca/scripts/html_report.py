"""Build an offline Korean HTML report from the preserved numerical outputs.

From kettle_lca/: python scripts/html_report.py
This is presentation only: no solver inputs or baseline results are changed.
"""
from __future__ import annotations

import base64
import csv
import hashlib
import html
import io
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RUN = "independent-2026-10-08"
RESULTS = ROOT / "results" / RUN
OUT = ROOT / "reports"
BASELINE = "5c158602ab557edff6f0aa6fafa48eb91f71dc6b"
REPO = "https://github.com/KSY-99/kettle-lca"
TREE = f"{REPO}/blob/{BASELINE}/kettle_lca"


def read_json(name):
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def read_csv(name):
    with (RESULTS / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def esc(value):
    return html.escape(str(value), quote=True)


def source_link(filename, label):
    return f'<a href="{TREE}/results/{RUN}/{filename}">{esc(label)} ↗</a>'


def download(filename, label):
    encoded = base64.b64encode((RESULTS / filename).read_bytes()).decode("ascii")
    mime = "text/csv" if filename.endswith(".csv") else "application/json"
    return f'<a class="button secondary" download="{filename}" href="data:{mime};base64,{encoded}">{esc(label)} ↓</a>'


# Check the actual preserved files rather than trusting rounded report text.
manifest = read_json("output_manifest.json")
for item in manifest:
    actual = hashlib.sha256((RESULTS / item["file"]).read_bytes()).hexdigest()
    if actual != item["sha256"]:
        raise ValueError(f"Baseline hash mismatch: {item['file']}")
s = read_json("summary.json")
checks = read_json("verification.json")
materials = read_csv("contributions.csv")
mapping = {r["material"]: r for r in read_csv("material_mapping.csv")}
flows = read_csv("elementary_flows.csv")
activities = read_csv("process_activity.csv")
sensitivities = read_csv("sensitivity.csv")
archive = json.loads((ROOT / "data/sources/merged-download-manifest.json").read_text(encoding="utf-8"))
total = s["characterized_material_supply_subtotal_kg_co2e"]
mapped = [r for r in materials if r["gwp100_characterized_subtotal_kg_co2e"] != ""]
missing = [r for r in materials if r not in mapped]
assert s["complete_factory_gate_gwp100_kg_co2e"] is None
assert math.isclose(sum(float(r["mass_g"]) for r in materials), s["total_mass_g"])
assert math.isclose(sum(float(r["gwp100_characterized_subtotal_kg_co2e"]) for r in mapped), total, abs_tol=1e-12)
assert all(c["passed"] for c in checks)
coverage = 100 * s["mapped_mass_g"] / s["total_mass_g"]
kettle = sum(float(r["gwp100_characterized_subtotal_kg_co2e"]) for r in mapped if r["scope"] == "Kettle")
packaging = total - kettle
ranked = sorted(mapped, key=lambda r: float(r["gwp100_characterized_subtotal_kg_co2e"]), reverse=True)
top2_share = 100 * sum(float(r["gwp100_characterized_subtotal_kg_co2e"]) for r in ranked[:2]) / total

KO = {
    "Stainless steel": ("스테인리스강", "304 코일 대체", "BOM의 강종·가공 형태가 불명확하여 304 압연 코일을 적용. 유럽 기술과 미국 상류 조건을 결합."),
    "Brass": ("황동", "미연결", "사용 가능한 생산 공정 미확보. 합금 조성과 가공 조건이 없어 구리로 대체하지 않음."),
    "Copper": ("구리", "금액 환산 대체", "공개 물량–금액 환산 공정으로 USEEIO 구리·금·은 정광 부문에 연결. 정련 구리의 직접 측정값이 아님."),
    "Polypropylene (PP)": ("폴리프로필렌 · PP", "수지 연결", "버진 PP 수지 공급. 부품 사출·성형은 계산에 포함하지 않음."),
    "Polyvinyl chloride (PVC)": ("폴리염화비닐 · PVC", "등급 대체", "현탁 중합 PVC 수지를 적용. 가소제·배합·부품 압출은 미계산."),
    "Nylon, grade unspecified": ("나일론 · 등급 미지정", "등급·금액 환산 대체", "나일론 6을 가정하고 USEEIO 일반 플라스틱 부문에 금액으로 연결."),
    "Polyoxymethylene (POM)": ("폴리옥시메틸렌 · POM", "미연결", "생산 공정 미확보. 일반 플라스틱으로 임의 대체하지 않음."),
    "Polycarbonate (PC)": ("폴리카보네이트 · PC", "금액 환산 대체", "PC 시트 가격과 일반 플라스틱 부문을 사용. 성형 부품을 대표하는 데 한계가 있음."),
    "Acrylonitrile-butadiene-styrene (ABS)": ("ABS 수지", "수지 연결", "ABS 공중합 수지 공급. 부품 성형은 미계산."),
    "Silicone": ("실리콘", "미연결", "실리콘 엘라스토머 생산 공정 미확보. 금속 규소나 다른 수지로 대체하지 않음."),
    "LDPE packaging foil": ("LDPE 포장 필름", "수지만 연결", "LDPE 버진 수지만 적용. 필름 압출·가공은 제외하며 LLDPE와 구분."),
    "Cardboard packaging": ("판지 포장", "골판지 대체", "미국 평균 골판지 생산을 적용. 해당 주전자 상자의 추가 인쇄·가공은 미계산."),
}
SHORT = {"Stainless steel": "Stainless steel", "Polypropylene (PP)": "PP", "Cardboard packaging": "Cardboard",
         "Nylon, grade unspecified": "Nylon 6 proxy", "Copper": "Copper proxy", "Acrylonitrile-butadiene-styrene (ABS)": "ABS",
         "Polyvinyl chloride (PVC)": "PVC", "Polycarbonate (PC)": "PC proxy", "LDPE packaging foil": "LDPE resin"}

# Standard plotting tool; SVG paths preserve text appearance without web fonts.
OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "svg.hashsalt": "kettle-lca-report-v1"})
fig, ax = plt.subplots(figsize=(10.2, 4.9), layout="constrained")
fig.patch.set_alpha(0)
ax.set_facecolor("none")
values = [float(r["gwp100_characterized_subtotal_kg_co2e"]) for r in ranked]
ax.barh(range(len(ranked)), values, height=.52, color=["#af7424" if r["scope"] == "Packaging" else "#246451" for r in ranked])
ax.set_yticks(range(len(ranked)), [SHORT[r["material"]] for r in ranked])
ax.invert_yaxis()
ax.set_xlim(0, max(values) * 1.30)
ax.set_xticks([0, .5, 1, 1.5])
ax.set_xlabel("Partial material-supply contribution (kg CO₂-eq)", labelpad=14, color="#485a50")
ax.xaxis.grid(True, color="#dce3db", linewidth=.8)
ax.set_axisbelow(True)
ax.tick_params(axis="both", length=0, labelcolor="#34483e", pad=9)
for spine in ax.spines.values():
    spine.set_visible(False)
for i, value in enumerate(values):
    ax.text(value + .027, i, f"{value:.3f}  ·  {value / total * 100:.1f}%", va="center", fontsize=10, color="#34483e")
buf = io.StringIO()
fig.savefig(buf, format="svg", transparent=True, metadata={"Date": None, "Creator": "Matplotlib / kettle-lca"})
plt.close(fig)
svg = buf.getvalue()
svg = svg[svg.index("<svg"):]
svg = svg.replace("<svg ", '<svg role="img" aria-labelledby="chart-title chart-desc" ', 1)
svg = svg.replace('version="1.1">', 'version="1.1"><title id="chart-title">재료별 GWP100 부분 합계 기여도</title><desc id="chart-desc">스테인리스강, PP, 판지 순으로 기여도가 큽니다. 수치는 아래 표에 제공됩니다. 누락 재료 3종은 차트에 포함되지 않습니다.</desc>', 1)
(OUT / "material-contributions.svg").write_text(svg, encoding="utf-8")

material_rows = []
for row in materials:
    name = row["material"]
    ko, status, note = KO[name]
    value = row["gwp100_characterized_subtotal_kg_co2e"]
    scope = "본체" if row["scope"] == "Kettle" else "포장"
    number = f'{float(value):.6f}' if value else '<span class="missing">미계산</span>'
    share = f'{float(value) / total * 100:.2f}%' if value else "—"
    linked = mapping[name].get("process_id", "")
    info = f'<a href="{esc(mapping[name]["source_url"])}">{esc(status)} ↗</a>' if linked else esc(status)
    material_rows.append(f'''<tr data-scope="{row['scope']}" data-missing="{str(not bool(value)).lower()}"><th scope="row">{ko}<small>{esc(name)}</small></th><td>{scope}</td><td class="num">{float(row['mass_g']):.2f}</td><td class="num">{number}</td><td class="num">{share}</td><td class="mapping">{info}<small>{note}</small></td></tr>''')

activity_rows = []
for row in mapped:
    meta = mapping[row["material"]]
    candidates = [a for a in activities if a["process_id"] == meta["process_id"] and a["reference_flow_id"] == meta["reference_flow_id"]]
    if len(candidates) != 1:
        raise ValueError(f"Expected a single allocated reference output: {row['material']}")
    a = candidates[0]
    activity_rows.append(f'<tr><th scope="row">{KO[row["material"]][0]}<small>{esc(a["process_name"])}</small></th><td class="num">{float(a["activity_reference_units"]):.9g}</td><td>{esc(a["reference_unit"])}</td><td class="num">{a["node"]}</td></tr>')

top_flows = sorted([f for f in flows if f["gwp100_kg_co2e"]], key=lambda f: abs(float(f["gwp100_kg_co2e"])), reverse=True)[:8]
flow_rows = []
for f in top_flows:
    direction = "환경 투입" if f["direction"] == "input" else "환경 배출"
    compartment = f["compartment"].replace("Elementary flows/", "")
    flow_rows.append(f'<tr><th scope="row">{esc(f["flow_name"])}<small>{esc(compartment)}</small></th><td>{direction}</td><td class="num">{float(f["amount"]):.8g}</td><td>{esc(f["unit"])}</td><td class="num">{float(f["cf"]):g}</td><td class="num">{float(f["gwp100_kg_co2e"]):+.6f}</td></tr>')
flow_rest = total - sum(float(f["gwp100_kg_co2e"]) for f in top_flows)

CHECK_NAMES = ["순환 2공정 분석해 벤치마크", "분석해 기반 목록·특성화 계산", "원천 조건식 평가", "수식 평가기의 코드 실행 차단", "독립 Neumann 반복법 수렴", "LU와 독립 반복법의 활동량 일치", "저장 기본흐름 목록: B × s", "저장 특성화 합계: C × g", "재료별 목록·기여도 합계", "BOM 질량 수지", "전체 결과의 null 유지", "누락 재료 3종 명시 유지"]
check_rows = "".join(f'<li><span class="check">통과</span><span>{label}</span></li>' for label in CHECK_NAMES)
mapping_rows = "".join(f'<tr><th scope="row">{KO[r["material"]][0]}</th><td>{esc(mapping[r["material"]]["geography"])}</td><td>{esc(mapping[r["material"]]["valid_from"])}<br>{esc(mapping[r["material"]]["valid_until"])}</td><td>{esc(mapping[r["material"]]["version"])}</td></tr>' for r in mapped)
scenario_labels = [("기준 시나리오", "구매 수율 100% 가정 · 나일론 6 가격 연결"), ("PP 구매 수율 95%", "다른 입력은 동일 · 추가 스크랩 처리는 제외"), ("나일론 66 가격 연결", "동일 플라스틱 부문에 다른 공개 가격 적용")]
sensitivity_rows = "".join(f'<tr><th scope="row">{label}<small>{note}</small></th><td class="num">{float(r["subtotal_kg_co2e"]):.6f}</td><td class="num">{float(r["delta_kg_co2e"]):+.6f}</td><td class="num">{float(r["delta_kg_co2e"])/total*100:+.2f}%</td></tr>' for r, (label, note) in zip(sensitivities, scenario_labels))

CSS = '''
:root{--ink:#183b30;--muted:#586a60;--green:#246451;--paper:#f6f7f1;--line:#dce3d9;--gold:#af7424;--amber:#855a13;--soft:#edf2eb;--warn:#fff3dc;--white:#fff;--radius:18px}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:90px}body{margin:0;background:var(--paper);color:var(--ink);font-family:"Malgun Gothic","Apple SD Gothic Neo",system-ui,sans-serif;font-size:15px;line-height:1.75}a{color:var(--green);text-underline-offset:4px}button,input{font:inherit}button,a,input{-webkit-tap-highlight-color:transparent}button:focus-visible,a:focus-visible,input:focus-visible,summary:focus-visible{outline:3px solid #b77722;outline-offset:4px}h1,h2,h3,p{margin-top:0}h1,h2,h3{word-break:keep-all;line-height:1.35}h1{font-size:clamp(34px,4.7vw,62px);letter-spacing:-.06em;margin-bottom:22px;font-weight:750}h2{font-size:29px;letter-spacing:-.04em;margin-bottom:12px}h3{font-size:18px;margin-bottom:12px}p{margin-bottom:14px}small{display:block;color:var(--muted);font-size:12px;line-height:1.6;margin-top:5px}.eyebrow{font-size:11px;font-weight:800;letter-spacing:.16em;text-transform:uppercase}.muted{color:var(--muted)}.mono,code,.num{font-family:ui-monospace,"Cascadia Code",Consolas,monospace;font-variant-numeric:tabular-nums}.num{text-align:right;white-space:nowrap}code{font-size:.89em;overflow-wrap:anywhere}.wrap{width:min(1180px,calc(100% - 64px));margin:auto}.skip{position:absolute;left:20px;top:-100px;background:white;padding:12px;z-index:10}.skip:focus{top:10px}
header{position:sticky;top:0;z-index:5;background:rgba(246,247,241,.96);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}.topbar{min-height:70px;display:flex;align-items:center;justify-content:space-between;gap:24px}.brand{color:var(--ink);font-weight:800;text-decoration:none;white-space:nowrap;letter-spacing:-.03em}.brand span{display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--green);margin-right:10px}nav{display:flex;gap:24px}nav a{font-size:12px;text-decoration:none;color:var(--muted)}nav a:hover{color:var(--green);text-decoration:underline}.print{border:1px solid var(--line);border-radius:50px;background:transparent;padding:7px 16px;color:var(--ink);cursor:pointer;white-space:nowrap}
main{padding-top:48px}.hero{display:grid;grid-template-columns:1.05fr 1fr;gap:55px;align-items:center;padding-bottom:40px}.hero .eyebrow{margin-bottom:25px;color:var(--green)}.lead{font-size:16px;max-width:520px;color:var(--muted);word-break:keep-all}.meta{font-size:12px;color:var(--muted);border-top:1px solid var(--line);padding-top:19px;margin-top:27px}.result-card{background:var(--ink);color:white;border-radius:24px;padding:32px 34px;position:relative;overflow:hidden}.result-card:after{content:"";position:absolute;width:170px;height:170px;border:1px solid #ffffff18;border-radius:50%;right:-85px;top:-80px;pointer-events:none}.pill{display:inline-flex;align-items:center;gap:6px;border-radius:50px;padding:4px 10px;font-size:11px;font-weight:700;letter-spacing:.02em}.result-card .pill{background:#eff4e3;color:var(--ink);margin-bottom:21px}.result-number{font-family:ui-monospace,Consolas,monospace;font-size:clamp(39px,4.7vw,63px);font-weight:600;letter-spacing:-.06em;line-height:1.15;white-space:nowrap}.unit{font-size:15px;color:#c3d7c8;margin-top:8px}.result-note{font-size:12px;color:#d0dfd5;margin:18px 0 24px}.scope-totals{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid #ffffff30;padding-top:17px;gap:14px}.scope-totals span{display:block;font-size:11px;color:#c3d7c8}.scope-totals strong{font-size:19px;font-weight:500}.notice{border:1px solid #e6d2af;border-left:4px solid var(--gold);background:var(--warn);border-radius:9px;padding:18px 22px;font-size:13px;line-height:1.8}.notice p{margin:0}.notice strong{color:#6b4712}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;margin-top:28px}.metric{background:var(--paper);padding:22px}.metric .label{font-size:12px;color:var(--muted)}.metric b{display:block;font-size:28px;font-weight:600;letter-spacing:-.03em;line-height:1.6}.metric b em{font-size:13px;font-style:normal;font-weight:400}.metric small{font-size:11px;margin:0}
section{padding-top:60px}.section-head{display:flex;gap:18px;align-items:flex-start;margin-bottom:23px}.section-num{font-family:Georgia,serif;font-size:25px;color:#869b8b;line-height:1.4}.section-head p{color:var(--muted);margin:0;max-width:800px;font-size:14px}.panel{background:white;border:1px solid var(--line);border-radius:var(--radius);padding:28px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:22px}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.scopebox h3{font-size:16px}.scopebox ul,.scopebox ol{padding-left:18px;color:var(--muted);font-size:13px;margin-bottom:0}.scopebox li+li{margin-top:9px}.status-label{display:block;font-size:11px;color:var(--green);font-weight:800;margin-bottom:9px}.mass-track{height:12px;display:flex;overflow:hidden;border-radius:8px;background:#e4c99c;margin:17px 0 11px}.mass-track span{display:block;background:var(--green)}.track-legend{display:flex;justify-content:space-between;gap:15px;font-size:12px;color:var(--muted)}.track-legend strong{color:var(--ink)}.mass-panel{margin-top:20px;padding:20px 25px;background:var(--soft);border-radius:12px}.mass-heading{display:flex;justify-content:space-between;gap:15px;font-size:13px}.mass-heading strong{font-size:20px}.chart-head{display:flex;justify-content:space-between;gap:20px;align-items:flex-start}.legend{display:flex;gap:15px;white-space:nowrap;font-size:11px;color:var(--muted)}.legend i{width:8px;height:8px;display:inline-block;border-radius:50%;margin-right:5px}.legend .green{background:var(--green)}.legend .gold{background:var(--gold)}figure{margin:0}.chart{width:100%;margin:10px 0}.chart svg{display:block;width:100%;height:auto}figcaption,.footnote{font-size:12px;color:var(--muted);line-height:1.8;margin:12px 0 0}.insight{background:var(--soft);border-radius:10px;padding:14px 19px;font-size:13px;margin-top:14px}.insight strong{color:var(--green)}
.toolbar{display:flex;justify-content:space-between;gap:15px;flex-wrap:wrap;align-items:center;margin:24px 0 13px}.filters{display:flex;gap:6px;flex-wrap:wrap}.filters button{background:transparent;border:1px solid var(--line);padding:6px 12px;border-radius:50px;color:var(--muted);cursor:pointer;font-size:12px}.filters button[aria-pressed=true]{background:var(--ink);border-color:var(--ink);color:white}.search{display:flex;align-items:center;gap:9px;font-size:12px;color:var(--muted)}input{border:1px solid var(--line);border-radius:8px;padding:8px 10px;background:white;width:220px;color:var(--ink);font-size:12px}.tablebox{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:white}table{border-collapse:collapse;width:100%;font-size:13px;line-height:1.6}caption{text-align:left;font-size:12px;color:var(--muted);padding:15px 16px;background:white}th,td{padding:13px 16px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}thead th{background:#edf2eb;color:var(--muted);font-size:11px;font-weight:600;white-space:nowrap}tbody th{font-weight:600}tbody tr:last-child>*{border-bottom:0}tfoot>*{background:var(--soft);font-weight:700}tfoot th,tfoot td{border-top:1px solid var(--line);border-bottom:0}td.mapping{min-width:240px;max-width:320px;font-size:12px}th small{font-weight:400}td small{font-size:11px}.missing{color:var(--amber);font-family:"Malgun Gothic",sans-serif;font-size:12px;background:var(--warn);padding:3px 7px;border-radius:4px}.table-info{display:flex;justify-content:space-between;gap:20px;margin-top:10px;font-size:11px;color:var(--muted)}.no-results{display:none;padding:24px;text-align:center;font-size:13px}.formula{font-family:Georgia,"Times New Roman",serif;font-size:33px;color:var(--green);margin:10px 0 12px}.step{display:flex;gap:12px;align-items:center;font-size:11px;font-weight:700;color:var(--muted)}.step b{border:1px solid var(--line);border-radius:50%;width:24px;height:24px;text-align:center;line-height:22px}.process p{font-size:13px;color:var(--muted)}.process .metric-inline{border-top:1px solid var(--line);padding-top:12px;font-size:12px}.subheading{font-size:19px;margin:27px 0 14px}.diagnostics{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:19px}.diagnostic{border:1px solid var(--line);background:white;border-radius:12px;padding:20px}.diagnostic strong{display:block;font-size:25px;color:var(--ink);font-weight:600}.diagnostic span{font-size:12px;color:var(--muted)}.details{border:1px solid var(--line);border-radius:12px;background:white;margin-top:18px;padding:18px 23px}summary{cursor:pointer;font-size:13px;font-weight:700}details[open] summary{margin-bottom:18px}.checklist{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:1fr 1fr;gap:9px 30px}.checklist li{font-size:12px;display:flex;gap:10px;align-items:center}.check{font-size:10px;color:var(--green);background:var(--soft);border-radius:4px;padding:2px 7px;white-space:nowrap}.qa-note{font-size:13px;margin-top:18px;color:var(--muted)}.checks-summary{display:flex;gap:25px;justify-content:space-between;border-top:1px solid var(--line);padding-top:19px;margin-top:20px;font-size:12px}.checks-summary b{display:block;color:var(--green);font-size:18px;font-weight:500}.sourcegrid{display:grid;grid-template-columns:1.1fr 1fr;gap:22px}.source-list{margin:0;display:grid;grid-template-columns:110px 1fr;font-size:12px;gap:14px}.source-list dt{color:var(--muted)}.source-list dd{margin:0;overflow-wrap:anywhere}.source-list code{font-size:11px}.links{padding-left:18px;font-size:13px}.links li+li{margin-top:8px}.buttons{display:flex;gap:10px;flex-wrap:wrap;margin-top:22px}.button{display:inline-flex;align-items:center;justify-content:center;padding:10px 16px;border-radius:9px;text-decoration:none;font-size:12px;background:var(--ink);color:white}.button.secondary{background:white;border:1px solid var(--line);color:var(--ink)}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#183b30;color:#e2ece5;border-radius:10px;padding:20px;font-size:12px;line-height:1.9;margin:15px 0 0}.numbered{font-size:13px;color:var(--muted);padding-left:19px}.numbered li+li{margin-top:10px}footer{border-top:1px solid var(--line);padding:28px 0;margin-top:60px;font-size:11px;color:var(--muted)}.footer-row{display:flex;justify-content:space-between;gap:20px}noscript p{background:var(--warn);padding:14px;font-size:12px}
@media(max-width:950px){.wrap{width:calc(100% - 40px)}.hero{gap:28px}.result-card{padding:26px}.result-number{font-size:45px}nav{gap:16px}.grid3{grid-template-columns:1fr}.process{display:grid;grid-template-columns:160px 1fr;gap:0 20px}.process .step{grid-column:1/-1}.process .metric-inline{grid-column:1/-1}.diagnostics{grid-template-columns:repeat(2,1fr)}.sourcegrid{grid-template-columns:1fr}.metric{padding:16px}}
@media(max-width:680px){body{font-size:14px}.wrap{width:calc(100% - 32px)}.topbar{min-height:60px;gap:10px}nav{display:none}.brand{font-size:14px}.print{font-size:11px;padding:6px 10px}main{padding-top:30px}.hero{grid-template-columns:1fr;gap:20px;padding-bottom:22px}h1{font-size:38px;margin-bottom:16px}.hero .eyebrow{margin-bottom:15px}.lead{font-size:14px}.meta{margin-top:18px;padding-top:14px}.result-number{font-size:49px}.result-card{padding:26px}.metrics{grid-template-columns:1fr 1fr;margin-top:20px}.metric{padding:17px}.metric b{font-size:26px}.notice{padding:15px 17px;font-size:12px}section{padding-top:42px}.section-head{gap:12px;margin-bottom:18px}h2{font-size:24px}.section-head p{font-size:13px}.panel{padding:20px}.grid2{grid-template-columns:1fr}.chart-head{display:block}.legend{margin-top:8px}.chart{overflow-x:auto}.chart svg{min-width:590px}.tablebox table{min-width:650px}.tablebox.compact table{min-width:510px}.toolbar{gap:12px}.search{width:100%}.search input{flex:1;min-width:0;width:100%}.track-legend{display:block}.track-legend span{display:block}.mass-heading{align-items:center}.mass-heading strong{font-size:17px}.process{display:block}.checklist{grid-template-columns:1fr}.checks-summary{flex-wrap:wrap;gap:14px}.source-list{grid-template-columns:85px 1fr;gap:12px}.source-list dd{min-width:0}.footer-row{display:block}.table-info{display:block}.table-info span{display:block}.flow-table td,.flow-table th{padding:12px}.sourcegrid .panel{padding:20px}.buttons .button{flex:1;min-width:130px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@media print{@page{size:A4;margin:14mm}body{background:white;color:#142e25;font-size:10px;line-height:1.6;-webkit-print-color-adjust:exact;print-color-adjust:exact}.wrap{width:100%}header,.toolbar,.buttons,.skip,.no-results,nav,.table-info,#screen-note{display:none!important}main{padding-top:0}.hero{grid-template-columns:1fr 1fr;gap:22px;padding-bottom:18px}h1{font-size:32px}.hero .eyebrow{font-size:9px;margin-bottom:12px}.lead{font-size:11px}.meta{font-size:9px;margin-top:12px;padding-top:12px}.result-card{padding:21px;border-radius:12px}.result-number{font-size:37px}.unit{font-size:11px}.result-note{font-size:9px;margin:12px 0}.scope-totals strong{font-size:14px}.notice{font-size:10px;padding:12px}.metrics{margin-top:17px}.metric{padding:12px}.metric b{font-size:23px}.metric small{font-size:9px}.metric .label{font-size:10px}section{padding-top:27px}.section-head{margin-bottom:13px}.section-head p,.panel p{font-size:10px}h2{font-size:21px}h3{font-size:14px}.section-num{font-size:20px}.panel{padding:16px;border-radius:10px}.grid3{gap:10px}.grid2{gap:14px}.scopebox ul,.scopebox ol{font-size:10px}.sourcegrid{grid-template-columns:1fr}.chart svg{max-height:92mm;width:100%;min-width:0}.chart-head h3{font-size:13px}.footnote,figcaption,.insight{font-size:9px}.tablebox{overflow:visible;border-radius:0}.tablebox table{min-width:0;width:100%;font-size:9px}.tablebox th,.tablebox td{padding:7px 8px}.tablebox td.mapping{min-width:0;max-width:190px;font-size:9px}.tablebox small,thead th{font-size:8px}.tablebox .num{white-space:normal}caption{font-size:9px;padding:8px}.tablebox tr{break-inside:avoid}tbody tr[hidden]{display:table-row!important}thead{display:table-header-group}tfoot{display:table-row-group}.grid3,.hero,.metrics,.mass-panel,.diagnostics,.notice,.process,.panel.scopebox,.section-head,.details{break-inside:avoid}.panel.chart-panel{break-inside:avoid}.diagnostics{gap:10px}.diagnostic{padding:12px}.diagnostic strong{font-size:22px}.diagnostic span{font-size:9px}.subheading{font-size:15px;margin:20px 0 10px}.details{padding:14px}summary,.qa-note,.checklist li{font-size:10px}.checks-summary{font-size:9px}.checks-summary b{font-size:14px}.links,.numbered{font-size:10px}.source-list{font-size:10px}.source-list code{font-size:9px}pre{font-size:9px;padding:13px}.sourcegrid .panel{break-inside:avoid}footer{margin-top:24px;padding:15px 0;font-size:9px}a{color:inherit}h2,h3,summary{break-after:avoid}.print-note{display:block}}
'''

page = f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><meta name="description" content="전기주전자 BOM 기반 미국 재료 공급 LCA: 공정 활동량, 기본흐름, IPCC AR6 GWP100 부분 합계와 데이터 한계."><title>전기주전자 LCA 결과 보고서 | Kettle LCA</title><style>{CSS}</style></head>
<body><a class="skip" href="#main">본문 바로가기</a>
<header><div class="wrap topbar"><a class="brand" href="#main"><span></span>KETTLE / LCA</a><nav aria-label="보고서 목차"><a href="#scope">범위</a><a href="#results">재료별 결과</a><a href="#method">계산 과정</a><a href="#quality">검증·한계</a><a href="#sources">출처</a></nav><button class="print" id="print-button" type="button">인쇄 / PDF 저장</button></div></header>
<main id="main" class="wrap"><div class="hero"><div><div class="eyebrow">BC1 · U.S. INVENTORY · IPCC AR6 GWP100</div><h1>전기주전자,<br>재료에서 시작하는<br>환경영향 분석.</h1><p class="lead">주전자 1대와 포장재의 BOM을 바탕으로 공정 활동량을 풀고, 기본흐름을 합산한 뒤 100년 지구온난화 영향을 특성화했습니다.</p><div class="meta">분석 기준일 <b>2026.10.08</b> &nbsp;·&nbsp; 독립 기준 시나리오<br>공개 저장소 <a href="{REPO}">KSY-99 / kettle-lca ↗</a></div></div><aside class="result-card" aria-label="핵심 결과"><span class="pill">부분 결과 · 재료 공급</span><div class="result-number">{total:.6f}</div><div class="unit">kg CO₂-eq / 주전자 1대의 BOM</div><p class="result-note">연결된 9개 재료의 공급망만 특성화한 합계입니다.<br>완성품 공장 출하 단계의 전체 값은 미계산입니다.</p><div class="scope-totals"><div><span>본체 재료 부분 합계</span><strong>{kettle:.6f}</strong></div><div><span>포장 재료 부분 합계</span><strong>{packaging:.6f}</strong></div></div></aside></div>
<div class="notice"><p><strong>해석의 전제</strong> · 황동·POM·실리콘, 부품 가공·조립 및 일부 상류 공급망이 미계산입니다. 누락값은 0이 아니며, 원천 데이터에 공제·제거 효과가 있으므로 이 부분 합계를 전체 영향의 하한으로 단정할 수도 없습니다.</p></div>
<div class="metrics"><div class="metric"><span class="label">BOM 총질량</span><b>{s['total_mass_g']:,.1f} <em>g</em></b><small>본체 723.0 g + 포장 137.8 g</small></div><div class="metric"><span class="label">질량 기준 연결률</span><b>{coverage:.2f}<em> %</em></b><small>818.8 g 연결 · 영향 포괄률과 다름</small></div><div class="metric"><span class="label">미연결 재료</span><b>{len(missing)}<em> 종 / 42.0 g</em></b><small>황동 · POM · 실리콘</small></div><div class="metric"><span class="label">수치·처리 검증</span><b>{len(checks)}<em> / {len(checks)} 통과</em></b><small>범위의 완전성을 의미하지 않음</small></div></div>

<section id="scope"><div class="section-head"><span class="section-num">01</span><div><h2>무엇을 계산했나</h2><p>대상은 BC1 대표 1 L 플라스틱 전기주전자 1대와 포장입니다. 실제 계산 범위는 연결된 재료 공급이며, 완성된 주전자의 전 과정평가는 아닙니다.</p></div></div><div class="grid3"><div class="panel scopebox"><span class="status-label">계산에 포함</span><h3>연결된 재료 공급</h3><ul><li>9개 재료와 연결 가능한 상류 공정</li><li>원천 공정에 포함된 에너지·운송</li><li>원천 데이터의 배분·스크랩·공제 규칙</li><li>미국 배경 우선, 일부 북미 및 유럽 기술 대체</li></ul></div><div class="panel scopebox"><span class="status-label">목표 범위 내 · 미계산</span><h3>확보되지 않은 입력</h3><ul><li>황동 20.25 g, POM 9.75 g, 실리콘 12 g</li><li>부품 성형·배합, 필름·상자 추가 가공</li><li>조립 에너지 및 공장별 운송</li><li>생산 손실과 추가 스크랩 처리</li></ul></div><div class="panel scopebox"><span class="status-label">시스템 경계 밖</span><h3>사용·폐기 단계</h3><ul><li>소비자에게 배송</li><li>주전자 사용 중 전력·물 소비</li><li>제품 폐기·재활용 단계</li><li>다른 주전자와의 성능·환경 우위 비교</li></ul></div></div><div class="mass-panel"><div class="mass-heading"><span>완제품 질량 → 구매 수요</span><strong>기준 구매 수율 100% 가정</strong></div><div class="mass-track" role="img" aria-label="총 860.8그램 중 818.8그램, 95.12퍼센트의 재료를 연결"><span style="width:{coverage:.8f}%"></span></div><div class="track-legend"><span><strong>연결 818.8 g</strong> · {coverage:.2f}%</span><span>미연결 42.0 g · {100-coverage:.2f}%</span></div><p class="footnote">구매량 = 완제품 질량 ÷ 1,000 ÷ 수율(kg). 수율은 실측값이 아닌 선별 분석 가정입니다. 연결률은 질량의 비율이며 공급망 완전성이나 환경영향의 포괄률을 나타내지 않습니다.</p></div></section>

<section id="results"><div class="section-head"><span class="section-num">02</span><div><h2>재료별 기여도</h2><p>같은 특성화 방법으로 계산한 재료별 공급망 부분 합계입니다. 표의 비중은 전체 주전자 영향이 아니라 계산된 부분 합계를 분모로 합니다.</p></div></div><div class="panel chart-panel"><div class="chart-head"><h3>스테인리스강과 PP가 부분 합계의 {top2_share:.1f}%</h3><div class="legend"><span><i class="green"></i>본체</span><span><i class="gold"></i>포장</span></div></div><figure><div class="chart">{svg}</div><figcaption>연결된 재료 9종을 기여도 순으로 정렬했습니다. 미계산 재료는 막대에 표시하지 않습니다. 소수점 반올림으로 표시 비중의 합이 100%와 약간 다를 수 있습니다.</figcaption></figure><div class="insight"><strong>현재 모델의 주요 기여 재료</strong> · 스테인리스강 {values[0]:.3f}, PP {values[1]:.3f}, 판지 {values[2]:.3f} kg CO₂-eq. 누락 공정과 대체 데이터가 보완되면 순위와 크기가 달라질 수 있습니다.</div></div>
<div class="toolbar"><div class="filters" role="group" aria-label="재료 범위 필터"><button type="button" data-filter="all" aria-pressed="true">전체 12</button><button type="button" data-filter="Kettle" aria-pressed="false">본체 10</button><button type="button" data-filter="Packaging" aria-pressed="false">포장 2</button><button type="button" data-filter="missing" aria-pressed="false">미계산 3</button></div><label class="search" for="material-search">재료 검색<input id="material-search" type="search" placeholder="예: PP, 나일론, 황동" autocomplete="off"></label></div>
<div class="tablebox"><table id="material-table"><caption>BOM 12종 · 질량, 부분 합계 및 공정 매핑 근거</caption><thead><tr><th scope="col">재료</th><th scope="col">범위</th><th scope="col" class="num">질량 (g)</th><th scope="col" class="num">부분 합계<br>(kg CO₂-eq)</th><th scope="col" class="num">부분 합계 내 비중</th><th scope="col">매핑·가정</th></tr></thead><tbody>{''.join(material_rows)}</tbody></table><div class="no-results" id="no-results">일치하는 재료가 없습니다.</div></div><div class="table-info"><span id="row-count" role="status" aria-live="polite">12개 중 12개 표시</span><span>미계산 ≠ 0 · 검색과 필터는 표에만 적용</span></div><div class="buttons">{download('contributions.csv', '재료별 원본 CSV')}{download('summary.json', '요약 JSON')}</div><noscript><p>모든 결과는 JavaScript 없이도 읽을 수 있습니다. 검색·필터·인쇄 버튼은 JavaScript가 필요하며 브라우저의 기본 인쇄 기능도 사용할 수 있습니다.</p></noscript></section>

<section id="method"><div class="section-head"><span class="section-num">03</span><div><h2>공정 활동량 → 기본흐름 → 영향</h2><p>공정별 단위와 기준 산출량을 정규화하고 배분을 적용한 뒤, 희소 행렬 모델로 공급망의 순환 연결까지 풉니다.</p></div></div><div class="grid3"><div class="panel process"><div class="step"><b>1</b>공정 활동량 풀기</div><div class="formula">A s = f</div><p>A = I − T. T는 공급 공정 투입 계수, f는 연결된 BOM 수요, s는 기준 산출 단위로 표현한 공정 활동량입니다. SciPy 희소 LU로 풉니다.</p><div class="metric-inline"><strong>{s['process_nodes']:,}</strong>개 배분 공정 노드 · <strong>{s['linked_exchanges']:,}</strong>개 연결</div></div><div class="panel process"><div class="step"><b>2</b>기본흐름 합산</div><div class="formula">g = B s</div><p>B의 공정별 기본흐름 계수에 활동량을 곱합니다. 흐름 UUID, 환경 매체, 투입·배출 방향을 보존하여 g로 합산합니다.</p><div class="metric-inline"><strong>{s['elementary_flow_direction_rows']:,}</strong>개 기본흐름·방향 행</div></div><div class="panel process"><div class="step"><b>3</b>GWP100 특성화</div><div class="formula">h = C g</div><p>C는 동일한 흐름에 연결한 IPCC AR6-100 특성화 계수입니다. 명시된 계수가 있는 흐름만 특성화하여 부분 합계 h를 구합니다.</p><div class="metric-inline"><strong>{s['characterized_flow_rows']:,}</strong>개 계수 연결 행 · 실제 0 계수 포함</div></div></div>
<h3 class="subheading">BOM에 직접 연결한 공급 공정의 활동량</h3><div class="tablebox compact"><table><caption>저장된 해 s에서 추출한 9개 기준 산출 공정 · 전체 공급망 활동량 {s['process_nodes']:,}개 중 일부</caption><thead><tr><th scope="col">공정</th><th scope="col" class="num">활동량 s</th><th scope="col">기준 단위</th><th scope="col" class="num">노드</th></tr></thead><tbody>{''.join(activity_rows)}</tbody></table></div><p class="footnote">활동량은 선택된 기준 산출량의 단위로 나타냅니다. 단위가 다른 공정의 활동량을 단순 합산하지 않습니다. 전체 표의 <code>dataset_runs_allocated_column</code>은 정규화 활동량을 원래 기준량으로 나눈 값이며, 실제 공장 가동 횟수와 동일하지 않습니다. {source_link('process_activity.csv','공정 활동량 원본')}</p>
<h3 class="subheading">절댓값 기준 상위 8개 특성화 기본흐름</h3><div class="tablebox flow-table"><table><caption>양의 환경 투입량에도 음의 특성화 계수가 적용될 수 있습니다.</caption><thead><tr><th scope="col">기본흐름 / 환경 매체</th><th scope="col">방향</th><th scope="col" class="num">합산량 g</th><th scope="col">단위</th><th scope="col" class="num">CF<br>kg CO₂-eq/단위</th><th scope="col" class="num">기여도<br>kg CO₂-eq</th></tr></thead><tbody>{''.join(flow_rows)}</tbody></table></div><p class="footnote">상위 8개 외 나머지 특성화 기여도의 합은 {flow_rest:+.6f} kg CO₂-eq입니다. 원천 방법의 부호를 유지하며 생물기원 여부가 불명확한 CO₂를 임의 재분류하지 않습니다. 본 방법은 <strong>AR6-100</strong>이며 <em>AR6-100 Net Biogenic</em> 변형은 아닙니다. {source_link('elementary_flows.csv','전체 기본흐름·계수·기여도')} · {source_link('characterization_category.json','원본 특성화 계수')}</p></section>

<section id="quality"><div class="section-head"><span class="section-num">04</span><div><h2>계산은 검증됐고, 범위는 불완전합니다</h2><p>수치 일치 여부와 데이터의 완전성은 별개입니다. 아래 진단값은 현재 모델에서 해결되지 않은 연결과 방법 적용 범위를 보여줍니다.</p></div></div><div class="diagnostics"><div class="diagnostic"><strong>{s['unlinked_product_input_exchanges']:,}</strong><span>미연결 제품 투입 교환</span></div><div class="diagnostic"><strong>{s['unlinked_waste_output_exchanges']:,}</strong><span>미연결 폐기물 산출 교환</span></div><div class="diagnostic"><strong>{s['uncharacterized_flow_rows']:,}</strong><span>선택 방법에서 계수 미연결 행</span></div><div class="diagnostic"><strong>{s['negative_activity_nodes']:,}</strong><span>공제 등을 반영한 음의 활동 노드</span></div></div><div class="grid2"><div class="panel scopebox"><h3>진단 수치를 읽는 방법</h3><ul><li>교환 수는 배분 노드·교환별 건수입니다. 고유 공급업체 수나 환경영향 비율이 아닙니다.</li><li>폐기물 산출 다수는 USEEIO의 폐기물 발생 보고 흐름입니다. 기존 폐기물 서비스 구매를 검토하지 않고 처리를 추가하면 중복될 수 있습니다.</li><li>계수 미연결 행 다수는 GWP100 대상이 아닌 오염물질·자원입니다. 공기 중 HCFC 4개 이름도 미연결로 남았습니다.</li><li>원천 배분·재활용 관례와 누적 목록의 호환성은 별도 검토가 필요합니다.</li></ul></div><div class="panel"><h3>수치 검증 결과</h3><p class="muted" style="font-size:13px">분석해가 있는 순환 공정 예제와 독립 Neumann 반복법으로 선형 해를 점검했습니다. 저장된 목록·특성화 결과도 행렬 곱과 대조했습니다.</p><div class="checks-summary"><div>최대 절대 행렬 잔차<b>{s['matrix_residual_max_abs']:.2e}</b></div><div>재료 기여도 합산 오차<b>{s['contribution_sum_error']:.2e}</b></div></div><div class="checks-summary"><div>독립 반복 해와의 활동량 차이<b>6.92e−14</b></div><div>원천 수식·저장 기본값 일치<b>{s['formula_exchange_count']:,} / {s['formula_exchange_count']:,}</b></div></div><p class="footnote">독립 반복법 48회 수렴. 모든 배경 공정에 대한 보편적인 원소·질량 수지는 계산하지 않았습니다.</p></div></div><details class="details"><summary>검증 항목 {len(checks)}개 모두 보기</summary><ul class="checklist">{check_rows}</ul><p class="qa-note">이 항목들은 지정된 행렬의 계산·처리를 검증합니다. 실측 정확도, 공급망 완결성 또는 외부 독립 검토를 뜻하지 않습니다. {source_link('verification.json','검증 원본')}</p></details><p class="footnote">미연결 자료: {source_link('unlinked_product_inputs.csv','제품 투입')} · {source_link('unlinked_waste_outputs.csv','폐기물 산출')} · {source_link('uncharacterized_flows.csv','미특성화 기본흐름')}</p></section>

<section id="sensitivity"><div class="section-head"><span class="section-num">05</span><div><h2>가정을 바꾸면 얼마나 달라지나</h2><p>두 가지 결정론적 민감도 사례입니다. 모든 수치는 여전히 재료 공급 부분 합계이며, 신뢰구간이나 전체 모델 불확실성을 나타내지 않습니다.</p></div></div><div class="tablebox compact"><table><caption>기준 대비 단일 가정 변화 · 다른 조건은 유지</caption><thead><tr><th scope="col">시나리오</th><th scope="col" class="num">부분 합계<br>kg CO₂-eq</th><th scope="col" class="num">변화량<br>kg CO₂-eq</th><th scope="col" class="num">변화율</th></tr></thead><tbody>{sensitivity_rows}</tbody></table></div><p class="footnote">PP 수율 95%는 예시 가정이며 추가 스크랩 처리를 포함하지 않습니다. 나일론 사례는 같은 산업 부문에 적용한 가격 연결의 차이로, PA6와 PA66의 실제 제조 공정을 직접 비교한 결과가 아닙니다. {source_link('sensitivity.csv','민감도 원본')}</p><div class="notice" style="margin-top:20px"><p><strong>확률적 불확실성은 미계산</strong> · 방어 가능한 입력 분포·상관관계가 확보되지 않았고 구조적 누락이 남아 있습니다. 평균·중앙값·P05/P95·Monte Carlo 신뢰구간은 제공하지 않습니다. 표시 소수점은 계산 재현용 정밀도이며 실측 정확도를 보장하지 않습니다.</p></div></section>

<section id="sources"><div class="section-head"><span class="section-num">06</span><div><h2>출처와 재현 정보</h2><p>이 HTML은 보존된 기준 결과를 읽어 만든 보고서입니다. 원래 수치 결과와 기준 태그는 수정하지 않았습니다.</p></div></div><div class="sourcegrid"><div class="panel"><h3>분석 계보</h3><dl class="source-list"><dt>입력</dt><dd>사용자 제공 BOM · 12개 재료<br><a href="{TREE}/data/bom.csv">원본 BOM ↗</a></dd><dt>배경 데이터</dt><dd><a href="https://www.lcacommons.gov/lca-collaboration/Federal_LCA_Commons/commons_merged_hybrid/datasets">LCA Commons Merged Hybrid ↗</a><br>USLCI·전력·목질 바이오매스·USEEIO·방법 통합</dd><dt>고정 리비전</dt><dd><code>f04287a6c7b2955169a426423a9a1d6380ceeda9</code></dd><dt>수집일</dt><dd>{archive['retrieval_date']} · {archive['bytes']:,} bytes</dd><dt>아카이브 SHA-256</dt><dd><code>{archive['sha256']}</code></dd><dt>영향 방법</dt><dd>IPCC AR6 GWP100 / AR6-100<br>범주 버전 01.04.001 · 방법 객체 01.04.000<br><code>{s['method']['@id']}</code></dd><dt>계산 기준 커밋</dt><dd><a href="{REPO}/commit/{BASELINE}"><code>{BASELINE}</code></a></dd><dt>기준 태그</dt><dd><code>{RUN}</code></dd><dt>환경</dt><dd>Python 3.12.14 · NumPy {s['versions']['numpy']} · SciPy {s['versions']['scipy']}</dd></dl></div><div class="panel"><h3>결과 파일과 문서</h3><ul class="links"><li><a href="{TREE}/README.md">전체 연구 보고서 · 가정·한계·재현 절차 ↗</a></li><li>{source_link('material_mapping.csv','공정 매핑·UUID·원천 해시')}</li><li>{source_link('process_manifest.csv','연결 공정 목록 및 해시')}</li><li>{source_link('provider_links.csv','공급망 연결')}</li><li>{source_link('output_manifest.json','기준 결과 SHA-256 목록')}</li><li>{source_link('run_inputs.json','입력·계산 코드 SHA-256')}</li><li><a href="{TREE}/scripts/calculate.py">계산 코드 ↗</a> · <a href="{TREE}/decision-log.md">선택 기록 ↗</a></li><li><a href="https://flcac-admin.github.io/FLCAC-docs/commons-merged/">공식 통합 데이터 설명 ↗</a> · <a href="https://www.lcacommons.gov/lca-commons-api-guide">API 안내 ↗</a></li></ul><p class="footnote">위 저장소 파일 링크는 계산 기준 커밋에 고정되어 있습니다. 다운로드 버튼은 이 HTML에 내장된 원본 CSV·JSON을 저장하므로 오프라인에서도 동작합니다.</p><h3 class="subheading">계산 재현</h3><p class="muted" style="font-size:12px">저장소의 <code>kettle_lca/</code> 폴더에서 실행합니다. 원천 데이터 다운로드는 인터넷 연결이 필요합니다.</p><pre><code>python -m pip install --target .deps -r requirements.txt
python scripts/download_merged.py
python scripts/inspect_archive.py
python scripts/calculate.py
python scripts/verify.py</code></pre><p class="footnote">HTML 재생성: <code>pip install --target .deps -r requirements-report.txt</code> 실행 후 <code>python scripts/html_report.py</code>. HTML 열람에는 추가 설치나 서버가 필요하지 않습니다.</p></div></div><details class="details"><summary>재료별 원천 데이터의 지역·기간·버전</summary><div class="tablebox compact"><table><caption>자료에서 unknown인 필드는 미확인 상태를 그대로 유지합니다.</caption><thead><tr><th scope="col">재료</th><th scope="col">지역</th><th scope="col">유효 기간 시작 / 종료</th><th scope="col">객체 버전</th></tr></thead><tbody>{mapping_rows}</tbody></table></div><p class="footnote">자료의 발표·통합 시점과 실제 조사 연도는 다릅니다. 서로 다른 원천 연도를 하나의 2026년 실측값으로 해석하지 않습니다. 스테인리스강은 유럽 생산 기술에 미국 상류 조건을 적용한 대체 데이터입니다.</p></details><p class="footnote">TianGong CLI 문서와 공개 자료는 검토했으나 인증된 공정 검색·계산은 수행하지 않았으며 TianGong 목록을 계산에 사용하지 않았습니다. 미연결 판단은 검색한 공개 아카이브의 범위에 한정됩니다. 출처 데이터에는 각 원천의 이용 조건이 적용됩니다.</p></section>

<section id="next"><div class="section-head"><span class="section-num">07</span><div><h2>전체 결과를 위해 필요한 다음 입력</h2><p>현재 부분 합계는 데이터 보완의 출발점입니다. 제품 간 환경 우위나 전체 주전자 발자국을 판단하려면 아래 항목을 추가로 해결해야 합니다.</p></div></div><div class="panel"><ol class="numbered"><li><strong>미연결 3개 재료:</strong> 황동 조성·가공, POM 수지, 실리콘 엘라스토머의 추적 가능한 생산 목록을 확보합니다.</li><li><strong>제조 정보:</strong> 실제 성형·배합·포장 가공, 구매 수율·스크랩, 조립 전력, 공장 운송량을 수집합니다.</li><li><strong>공급망과 방법:</strong> 영향이 있는 미연결 제품·폐기물 서비스를 검토하고, 배분·재활용·탄소 회계의 일관성을 확인합니다.</li><li><strong>기준 보존:</strong> 새 입력은 별도의 개정 실행 폴더에 저장하고, 기존 기준 결과와 변경 이유·영향을 비교합니다.</li></ol></div></section>
<footer><div class="footer-row"><div><strong>KETTLE / LCA</strong> &nbsp;·&nbsp; 한국어 결과 보고서 · 2026.10.08<br>기준 결과 파일 {len(manifest)}개 SHA-256 검증 후 생성 · HTML/차트는 표시용 산출물</div><div>부분 재료 공급 결과 · 전체 탄소발자국 미계산<br><a href="{REPO}">KSY-99 / kettle-lca ↗</a></div></div></footer></main>
<script>
(()=>{{'use strict';const rows=[...document.querySelectorAll('#material-table tbody tr')];const input=document.getElementById('material-search');const buttons=[...document.querySelectorAll('[data-filter]')];let filter='all';
function render(){{const term=input.value.trim().toLocaleLowerCase();let count=0;rows.forEach(row=>{{const scope=filter==='all'||row.dataset.scope===filter||(filter==='missing'&&row.dataset.missing==='true');const match=row.textContent.toLocaleLowerCase().includes(term);row.hidden=!(scope&&match);if(!row.hidden)count++;}});document.getElementById('row-count').textContent=`${{rows.length}}개 중 ${{count}}개 표시`;document.getElementById('no-results').style.display=count?'none':'block';}}
buttons.forEach(button=>button.addEventListener('click',()=>{{filter=button.dataset.filter;buttons.forEach(b=>b.setAttribute('aria-pressed',String(b===button)));render();}}));input.addEventListener('input',render);document.getElementById('print-button').addEventListener('click',()=>window.print());let opened=[];window.addEventListener('beforeprint',()=>{{opened=[...document.querySelectorAll('details:not([open])')];opened.forEach(d=>d.open=true);}});window.addEventListener('afterprint',()=>{{opened.forEach(d=>d.open=false);opened=[];}});}})();
</script></body></html>'''

destination = OUT / "kettle-lca-report.html"
destination.write_text(page, encoding="utf-8")
print(json.dumps({"html": str(destination), "bytes": destination.stat().st_size,
                  "verified_baseline_files": len(manifest), "materials": len(materials),
                  "subtotal_kg_co2e": total, "reporting_only": True}, ensure_ascii=False))
