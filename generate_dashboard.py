#!/usr/bin/env python3
"""
So Vizion FBA Optimizer V2.0 — DEFINITIVE BUILD
Upload supplier CSV + Keepa CSV directly in browser.
Matches on ASIN, EAN, GTIN, UPC, SKU — whichever is available.
All sliders and filters fully working.
"""

import os, webbrowser
OUT_HTML = "/Users/soso/Desktop/So Vizion Code app/So Vizion FBA Optimizer HTML/sovizion_v2.html"

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>So Vizion — FBA Optimizer V2.0</title>
<style>
:root{
  --bg:#0f1117;--card:#1a1d27;--border:#2a2d3a;--accent:#6c63ff;
  --green:#22c55e;--yellow:#f59e0b;--red:#ef4444;--blue:#3b82f6;
  --text:#e2e8f0;--muted:#64748b;
  --b:#00d9ff;--g:#00ff88;--a:#ffcc00;--r:#ff4757;
  --pad:28px;
}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--text);font-family:'Inter',system-ui,sans-serif;font-size:14px;min-height:100vh;}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-track{background:var(--bg);}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px;}
.screen{display:none;}.screen.active{display:block;}

/* UPLOAD */
.upload-wrap{min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px var(--pad);}
.logo{text-align:center;margin-bottom:40px;}
.logo h1{font-size:34px;font-weight:900;letter-spacing:-1px;margin-bottom:6px;}
.logo h1 span{color:var(--accent);}
.logo p{font-size:13px;color:var(--muted);}
.version{display:inline-block;margin-top:8px;background:rgba(108,99,255,.15);color:var(--accent);border:1px solid rgba(108,99,255,.3);border-radius:20px;padding:3px 14px;font-size:11px;font-weight:700;}
.upload-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;width:100%;max-width:900px;margin-bottom:24px;}
@media(max-width:700px){.upload-grid{grid-template-columns:1fr;}}
.upload-card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:28px;display:flex;flex-direction:column;gap:16px;}
.uc-title{display:flex;align-items:center;gap:10px;font-size:13px;font-weight:700;}
.uc-title .ico{font-size:22px;}
.uc-desc{font-size:11px;color:var(--muted);line-height:1.7;}
.uc-desc strong{color:var(--text);}
.dz{border:2px dashed var(--border);border-radius:12px;padding:28px 20px;text-align:center;cursor:pointer;transition:all .2s;color:var(--muted);display:flex;flex-direction:column;align-items:center;gap:8px;}
.dz:hover,.dz.over{border-color:var(--accent);background:rgba(108,99,255,.06);color:var(--text);}
.dz.done{border-color:var(--green);background:rgba(34,197,94,.06);color:var(--green);}
.dz.err{border-color:var(--red);background:rgba(239,68,68,.06);}
.dz-ico{font-size:30px;}
.dz-txt{font-size:12px;font-weight:600;}
.dz-hint{font-size:10px;line-height:1.6;}
input[type=file]{display:none;}
.btn-go{width:100%;max-width:900px;padding:16px;border-radius:12px;border:none;background:var(--accent);color:#fff;font-size:15px;font-weight:700;cursor:pointer;transition:all .2s;opacity:.35;pointer-events:none;}
.btn-go.ready{opacity:1;pointer-events:all;}
.btn-go.ready:hover{background:#7c73ff;transform:translateY(-1px);box-shadow:0 8px 28px rgba(108,99,255,.4);}
.upload-note{font-size:11px;color:var(--muted);text-align:center;max-width:460px;line-height:1.7;margin-top:6px;}

/* MAPPING */
.map-wrap{min-height:100vh;padding:40px var(--pad);}
.map-header{text-align:center;margin-bottom:32px;}
.map-header h2{font-size:22px;font-weight:800;margin-bottom:6px;}
.map-header p{font-size:13px;color:var(--muted);}
.map-card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:28px;max-width:780px;margin:0 auto 20px;}
.map-card h3{font-size:10px;font-weight:700;color:var(--b);text-transform:uppercase;letter-spacing:2px;margin-bottom:18px;display:flex;align-items:center;gap:8px;}
.map-card h3::after{content:'';flex:1;height:1px;background:var(--border);}
.map-row{display:grid;grid-template-columns:1fr 20px 1fr;align-items:center;gap:12px;margin-bottom:10px;}
.col-name{background:#0f1117;border:1px solid var(--border);border-radius:8px;padding:9px 12px;font-size:12px;color:var(--muted);font-family:monospace;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.arrow{color:var(--border);text-align:center;}
.col-sel{background:#0f1117;border:1px solid var(--border);color:var(--text);border-radius:8px;padding:9px 10px;font-size:12px;outline:none;cursor:pointer;width:100%;}
.col-sel:focus{border-color:var(--accent);}
.col-sel.mapped{border-color:var(--green);color:var(--green);}
.map-preview{background:#0f1117;border:1px solid var(--border);border-radius:8px;padding:12px;margin-top:14px;font-size:11px;color:var(--muted);font-family:monospace;max-height:90px;overflow-y:auto;line-height:1.8;}
.map-preview strong{color:var(--text);}
.map-status{text-align:center;font-size:12px;margin-top:10px;min-height:20px;}
.map-status.ok{color:var(--green);}
.map-status.err{color:var(--red);}
.map-actions{display:flex;gap:12px;justify-content:center;margin-top:20px;}
.btn-back{padding:12px 24px;border-radius:10px;border:1px solid var(--border);background:none;color:var(--muted);font-size:14px;cursor:pointer;}
.btn-back:hover{border-color:var(--text);color:var(--text);}
.btn-confirm{padding:12px 32px;border-radius:10px;border:none;background:var(--accent);color:#fff;font-size:14px;font-weight:700;cursor:pointer;}
.btn-confirm:hover{background:#7c73ff;}

/* LOADING */
.load-wrap{min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:20px;}
.spinner{width:48px;height:48px;border:3px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .8s linear infinite;}
@keyframes spin{to{transform:rotate(360deg);}}
.load-msg{font-size:14px;color:var(--muted);}
.load-step{font-size:12px;color:var(--muted);font-family:monospace;}

/* DASHBOARD */
.dash-header{background:var(--card);border-bottom:1px solid var(--border);padding:18px var(--pad);display:flex;align-items:flex-start;gap:20px;flex-wrap:wrap;}
.dash-left{display:flex;flex-direction:column;gap:4px;}
.dash-header h1{font-size:20px;font-weight:800;letter-spacing:-.5px;}
.dash-header h1 span{color:var(--accent);}
.dash-sub{font-size:12px;color:var(--muted);}
.dash-right{margin-left:auto;display:flex;gap:8px;align-items:center;flex-wrap:wrap;}
.badge{background:#6c63ff22;color:var(--accent);border:1px solid var(--accent);border-radius:20px;padding:3px 12px;font-size:12px;font-weight:600;}
.live-badge{background:#22c55e22;color:var(--green);border:1px solid var(--green);border-radius:20px;padding:3px 10px;font-size:11px;}
.btn-new{background:none;border:1px solid var(--border);color:var(--muted);border-radius:8px;padding:5px 12px;font-size:11px;cursor:pointer;}
.btn-new:hover{border-color:var(--accent);color:var(--accent);}

/* MATCH REPORT */
.match-report{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:16px 22px;margin:16px var(--pad) 0;font-size:12px;}
.match-report-title{font-family:monospace;font-size:9px;color:var(--b);letter-spacing:3px;text-transform:uppercase;margin-bottom:10px;}
.match-stats{display:flex;flex-wrap:wrap;gap:20px;}
.match-stat{display:flex;flex-direction:column;gap:2px;}
.match-stat .ms-val{font-size:20px;font-weight:700;}
.match-stat .ms-lbl{font-size:10px;color:var(--muted);}
.match-stat.ok .ms-val{color:var(--green);}
.match-stat.warn .ms-val{color:var(--yellow);}
.match-stat.bad .ms-val{color:var(--red);}
.match-stat.info .ms-val{color:var(--b);}

/* MARKETPLACE DETECTED */
.mkt-detected{display:flex;align-items:center;gap:14px;background:rgba(0,217,255,.05);border:1px solid rgba(0,217,255,.20);border-radius:12px;padding:12px 18px;margin:16px var(--pad) 0;flex-wrap:wrap;}
.mkt-det-lbl{font-family:monospace;font-size:9px;color:var(--b);letter-spacing:3px;text-transform:uppercase;white-space:nowrap;}
.mkt-det-flag{font-size:26px;line-height:1;}
.mkt-det-info{flex:1;}
.mkt-det-name{font-size:14px;font-weight:800;color:var(--text);}
.mkt-det-domain{font-family:monospace;font-size:10px;color:var(--b);margin-top:2px;}
.mkt-det-link{font-family:monospace;font-size:11px;color:var(--b);text-decoration:none;border:1px solid rgba(0,217,255,.25);border-radius:6px;padding:5px 12px;transition:all .15s;white-space:nowrap;margin-left:auto;}
.mkt-det-link:hover{background:rgba(0,217,255,.1);}

/* KPI */
.kpi-row{display:flex;gap:14px;padding:16px var(--pad);flex-wrap:wrap;}
.kpi{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px 20px;min-width:130px;flex:1;}
.kpi .val{font-size:26px;font-weight:700;}
.kpi .lbl{font-size:11px;color:var(--muted);margin-top:4px;}
.kpi.t1 .val{color:var(--green);}
.kpi.t2 .val{color:var(--blue);}
.kpi.t3 .val{color:var(--yellow);}
.kpi.ng .val{color:var(--red);}

/* FILTER PANEL */
.fp{background:var(--card);border:1px solid var(--border);border-radius:14px;margin:0 var(--pad);overflow:hidden;}
.fp-toggle{display:flex;align-items:center;gap:10px;padding:14px 20px;cursor:pointer;user-select:none;transition:background .15s;}
.fp-toggle:hover{background:#ffffff05;}
.fp-toggle-ico{font-size:15px;}
.fp-toggle-title{font-family:monospace;font-size:9px;color:var(--b);letter-spacing:3px;text-transform:uppercase;font-weight:700;}
.fp-toggle-sum{font-size:11px;color:var(--muted);margin-left:4px;}
.fp-toggle-arr{margin-left:auto;color:var(--muted);font-size:11px;transition:transform .2s;}
.fp.open .fp-toggle-arr{transform:rotate(180deg);}
.fp-body{display:none;padding:16px 20px 20px;border-top:1px solid var(--border);}
.fp.open .fp-body{display:block;}
.sg{margin-bottom:20px;}
.sr{display:flex;align-items:center;gap:10px;margin-bottom:8px;}
.sl{font-size:12px;color:var(--text);font-weight:600;min-width:240px;}
.sv{font-family:monospace;font-size:11px;font-weight:700;color:var(--b);background:rgba(0,217,255,.08);border:1px solid rgba(0,217,255,.2);border-radius:6px;padding:3px 10px;white-space:nowrap;min-width:170px;text-align:center;}
.br{background:none;border:1px solid var(--border);color:var(--muted);border-radius:6px;padding:3px 10px;font-size:11px;cursor:pointer;white-space:nowrap;transition:all .15s;}
.br:hover{border-color:var(--accent);color:var(--accent);}
.si{-webkit-appearance:none;appearance:none;width:100%;height:8px;border-radius:4px;background:linear-gradient(to right,var(--g) 0%,var(--a) 50%,var(--r) 100%);cursor:pointer;outline:none;}
.si::-webkit-slider-thumb{-webkit-appearance:none;width:22px;height:22px;border-radius:50%;background:var(--text);border:3px solid var(--b);box-shadow:0 0 10px rgba(0,217,255,.45);cursor:pointer;}
.si::-moz-range-thumb{width:22px;height:22px;border-radius:50%;background:var(--text);border:3px solid var(--b);box-shadow:0 0 10px rgba(0,217,255,.45);cursor:pointer;}
.st{display:flex;justify-content:space-between;margin-top:4px;font-family:monospace;font-size:9px;color:var(--muted);padding:0 2px;}
.sg.cg .sl{color:var(--a);}
.sg.cg .sv{color:var(--a);background:rgba(255,204,0,.08);border-color:rgba(255,204,0,.2);}
.fa{display:flex;gap:12px;align-items:center;flex-wrap:wrap;padding-top:14px;border-top:1px solid var(--border);margin-top:8px;}
.fa label{font-size:11px;color:var(--muted);white-space:nowrap;}
.fa select{background:#0f1117;border:1px solid var(--border);color:var(--text);border-radius:8px;padding:7px 10px;font-size:12px;outline:none;cursor:pointer;}
.pin{background:#0f1117;border:1px solid var(--border);color:var(--text);border-radius:8px;padding:7px 12px;font-size:12px;outline:none;width:190px;}
.pin:focus{border-color:var(--accent);}
.pin::placeholder{color:var(--muted);}
.bsp{background:var(--accent);color:#fff;border:none;border-radius:8px;padding:7px 14px;font-size:12px;font-weight:600;cursor:pointer;}
.bsp:hover{opacity:.85;}
.bra{background:none;border:1px solid var(--border);color:var(--muted);border-radius:8px;padding:7px 14px;font-size:12px;cursor:pointer;white-space:nowrap;transition:all .15s;margin-left:auto;}
.bra:hover{border-color:var(--red);color:var(--red);}
.pl{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px;}
.plbl{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;width:100%;margin-bottom:2px;font-family:monospace;}
.pc{display:flex;align-items:center;gap:6px;background:#0f1117;border:1px solid var(--border);border-radius:20px;padding:5px 10px 5px 12px;font-size:11px;cursor:pointer;transition:all .15s;}
.pc:hover{border-color:var(--accent);background:rgba(108,99,255,.08);}
.pc .pn{color:var(--text);font-weight:600;}
.pc .pm{color:var(--muted);font-family:monospace;font-size:9px;margin-left:4px;}
.pc button{background:none;border:none;color:var(--muted);cursor:pointer;font-size:14px;line-height:1;padding:0 0 0 4px;}
.pc button:hover{color:var(--red);}
.sb{margin-top:14px;padding:11px 16px;border-radius:8px;font-size:12px;background:rgba(0,217,255,.05);border:1px solid rgba(0,217,255,.12);color:var(--muted);line-height:1.6;}
.sb strong{color:var(--text);}
.sb.nm{background:rgba(239,68,68,.07);border-color:rgba(239,68,68,.2);color:var(--red);}

/* SEARCH */
.sw{padding:14px var(--pad) 0;}
.sw input{width:100%;background:var(--card);border:1px solid var(--border);color:var(--text);border-radius:10px;padding:10px 16px;font-size:13px;outline:none;}
.sw input:focus{border-color:var(--accent);}
.sw input::placeholder{color:var(--muted);}
.cb{padding:10px var(--pad) 6px;font-size:12px;color:var(--muted);}
.cb strong{color:var(--text);}

/* TABLE */
.tw{padding:0 var(--pad) 48px;overflow-x:auto;}
table{width:100%;border-collapse:collapse;font-size:13px;table-layout:fixed;}
thead th:nth-child(1),tbody td:nth-child(1){width:90px;}
thead th:nth-child(2),tbody td:nth-child(2){width:240px;}
thead th:nth-child(3),tbody td:nth-child(3){width:78px;}
thead th:nth-child(4),tbody td:nth-child(4){width:88px;}
thead th:nth-child(5),tbody td:nth-child(5){width:78px;}
thead th:nth-child(6),tbody td:nth-child(6){width:110px;}
thead th:nth-child(7),tbody td:nth-child(7){width:80px;}
thead th:nth-child(8),tbody td:nth-child(8){width:80px;}
thead th:nth-child(9),tbody td:nth-child(9){width:90px;}
thead th:nth-child(10),tbody td:nth-child(10){width:100px;}
thead th:nth-child(11),tbody td:nth-child(11){width:90px;}
thead th:nth-child(12),tbody td:nth-child(12){width:120px;}
thead th{background:var(--card);color:var(--muted);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.5px;padding:10px 12px;border-bottom:2px solid var(--border);white-space:nowrap;cursor:pointer;user-select:none;position:sticky;top:0;z-index:10;text-align:left;overflow:hidden;text-overflow:ellipsis;}
thead th:hover{color:var(--text);}
thead th.sorted{color:var(--accent);}
thead th .sa{margin-left:4px;opacity:.5;}
thead th.sorted .sa{opacity:1;}
thead th:nth-child(3),thead th:nth-child(4),thead th:nth-child(5),thead th:nth-child(6),thead th:nth-child(7),thead th:nth-child(8){text-align:right;}
thead th:nth-child(9),thead th:nth-child(10),thead th:nth-child(11),thead th:nth-child(12){text-align:center;}
tbody tr{border-bottom:1px solid var(--border);cursor:pointer;transition:background .1s;}
tbody tr:hover{background:#ffffff06;}
tbody tr.expanded{background:#6c63ff0a;}
td{padding:10px 12px;vertical-align:middle;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
td:nth-child(3),td:nth-child(4),td:nth-child(5),td:nth-child(6),td:nth-child(7),td:nth-child(8){text-align:right;}
td:nth-child(9),td:nth-child(10),td:nth-child(11),td:nth-child(12){text-align:center;}
td:nth-child(2){font-weight:500;max-width:240px;}
.tier-badge{display:inline-block;border-radius:4px;padding:2px 8px;font-size:11px;font-weight:700;white-space:nowrap;}
.t1b{background:#22c55e22;color:var(--green);border:1px solid #22c55e44;}
.t2b{background:#3b82f622;color:var(--blue);border:1px solid #3b82f644;}
.t3b{background:#f59e0b22;color:var(--yellow);border:1px solid #f59e0b44;}
.t4b{background:#ef444422;color:var(--red);border:1px solid #ef444444;}
.rh{color:var(--green);font-weight:700;}
.rm{color:var(--yellow);font-weight:700;}
.rl{color:var(--red);font-weight:700;}
.ss{color:var(--green);}
.smod{color:var(--yellow);}
.svol{color:var(--red);}
.sunk{color:var(--muted);}
.al{color:var(--green);}
.am{color:var(--yellow);}
.ah{color:var(--red);}
.db{background:#ffffff10;border-radius:4px;padding:2px 6px;font-size:11px;}
.dg{background:#22c55e22;color:var(--green);}
.detail-row td{padding:0!important;overflow:visible!important;white-space:normal!important;text-align:left!important;}
.detail-box{background:#13151f;border-bottom:2px solid var(--accent);padding:20px 28px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;}
.ds h4{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);margin-bottom:10px;font-weight:600;}
.ds p{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #ffffff08;font-size:13px;}
.ds p span:last-child{font-weight:600;color:var(--text);}
.sens-table{width:100%;border-collapse:collapse;margin-top:4px;}
.sens-table th{font-size:11px;color:var(--muted);padding:5px 8px;text-align:right;background:#0f1117;border-bottom:1px solid var(--border);}
.sens-table th:first-child{text-align:left;}
.sens-table td{padding:6px 8px;text-align:right;border-bottom:1px solid #ffffff06;font-size:12px;}
.sens-table td:first-child{text-align:left;font-weight:600;}
.sens-table tr.ar td{background:#6c63ff15;color:var(--text);}
.sens-table tr.ar td:first-child{color:var(--accent);}
.ok{color:var(--green);}.warn{color:var(--yellow);}.bad{color:var(--red);}
.nr{text-align:center;padding:60px;color:var(--muted);}
@media(max-width:768px){:root{--pad:16px;}.fa{flex-direction:column;align-items:flex-start;}.bra{margin-left:0;}.detail-box{grid-template-columns:1fr;}}
</style>
</head>
<body>

<!-- ══ SCREEN 1: UPLOAD ══ -->
<div id="s-upload" class="screen active">
<div class="upload-wrap">
  <div class="logo">
    <h1>So Vizion <span>FBA Optimizer</span></h1>
    <p>Upload your files — all filters and sliders fully working</p>
    <span class="version">V2.0</span>
  </div>
  <div class="upload-grid">

    <div class="upload-card">
      <div class="uc-title"><span class="ico">🏭</span>Supplier Catalog</div>
      <div class="uc-desc">
        Any supplier format accepted.<br>
        <strong>Identifies products by:</strong> EAN, GTIN, UPC, ASIN, or SKU<br>
        <strong>Required:</strong> At least one product identifier + purchase price<br>
        Column names auto-detected in any language.
      </div>
      <div class="dz" id="dz-sup"
        onclick="document.getElementById('fi-sup').click()"
        ondragover="event.preventDefault();this.classList.add('over')"
        ondragleave="this.classList.remove('over')"
        ondrop="onDrop(event,'sup')">
        <div class="dz-ico">📋</div>
        <div class="dz-txt" id="dzt-sup">Click or drag &amp; drop</div>
        <div class="dz-hint" id="dzh-sup">CSV accepted · Numbers/Excel → export as CSV first</div>
      </div>
      <input type="file" id="fi-sup" accept=".csv,.txt" onchange="onFile(this,'sup')">
    </div>

    <div class="upload-card">
      <div class="uc-title"><span class="ico">📊</span>Keepa Export CSV</div>
      <div class="uc-desc">
        Standard Keepa Product Viewer export.<br>
        <strong>French and English</strong> column names both supported.<br>
        Matches on: ASIN, EAN, GTIN, UPC — whichever is available.<br>
        Extracts: Buy Box, BSR, drops, FBA fees, Amazon BB% and more.
      </div>
      <div class="dz" id="dz-kpa"
        onclick="document.getElementById('fi-kpa').click()"
        ondragover="event.preventDefault();this.classList.add('over')"
        ondragleave="this.classList.remove('over')"
        ondrop="onDrop(event,'kpa')">
        <div class="dz-ico">🔑</div>
        <div class="dz-txt" id="dzt-kpa">Click or drag &amp; drop</div>
        <div class="dz-hint" id="dzh-kpa">CSV file · French or English Keepa export</div>
      </div>
      <input type="file" id="fi-kpa" accept=".csv,.txt" onchange="onFile(this,'kpa')">
    </div>

  </div>
  <button class="btn-go" id="btn-go" onclick="goToMapping()">🔍 &nbsp;Analyze Products</button>
  <p class="upload-note">Files never leave your computer — all processing happens locally in your browser.</p>
</div>
</div>

<!-- ══ SCREEN 2: COLUMN MAPPING ══ -->
<div id="s-map" class="screen">
<div class="map-wrap">
  <div class="map-header">
    <h2>🗂 Map Your Supplier Columns</h2>
    <p>Confirm which column is which. Auto-detected from your file.<br>
    At least one identifier (EAN / GTIN / UPC / ASIN / SKU) is required.</p>
  </div>
  <div class="map-card">
    <h3>Supplier CSV Columns</h3>
    <div id="map-rows"></div>
    <div class="map-preview" id="map-preview"></div>
  </div>
  <div class="map-status" id="map-status"></div>
  <div class="map-actions">
    <button class="btn-back" onclick="showScreen('upload')">← Back</button>
    <button class="btn-confirm" id="btn-confirm" onclick="runAnalysis()">✓ Confirm &amp; Analyze</button>
  </div>
</div>
</div>

<!-- ══ SCREEN 3: LOADING ══ -->
<div id="s-load" class="screen">
<div class="load-wrap">
  <div class="spinner"></div>
  <div class="load-msg">Building your dashboard…</div>
  <div class="load-step" id="load-step">Reading files…</div>
</div>
</div>

<!-- ══ SCREEN 4: DASHBOARD ══ -->
<div id="s-dash" class="screen">

  <div class="dash-header">
    <div class="dash-left">
      <h1>So Vizion <span>FBA Optimizer</span></h1>
      <div class="dash-sub" id="dash-sub">Supplier catalog · amazon.fr</div>
    </div>
    <div class="dash-right">
      <span class="badge" id="dash-badge">— / — analyzed</span>
      <span class="live-badge">🟢 LIVE DATA</span>
      <button class="btn-new" onclick="newAnalysis()">↑ New Analysis</button>
    </div>
  </div>

  <!-- Match report -->
  <div class="match-report" id="match-report">
    <div class="match-report-title">Match Report</div>
    <div class="match-stats" id="match-stats"></div>
  </div>

  <!-- Marketplace (detected from CSV) -->
  <div class="mkt-detected" id="mkt-detected" style="display:none"></div>

  <!-- KPIs -->
  <div class="kpi-row" id="kpi-row"></div>

  <!-- Filters -->
  <div class="fp open" id="fp">
    <div class="fp-toggle" onclick="toggleFP()">
      <span class="fp-toggle-ico">🔧</span>
      <span class="fp-toggle-title">Dynamic Filters</span>
      <span class="fp-toggle-sum" id="fp-sum">&nbsp;— No filters active</span>
      <span class="fp-toggle-arr">▲</span>
    </div>
    <div class="fp-body">

      <div class="sg">
        <div class="sr"><span class="sl">📈 ROI Minimum</span>
          <span class="sv" id="v-roi">No minimum — showing all</span>
          <button class="br" onclick="rst('roi')">Reset</button></div>
        <input type="range" class="si" id="sl-roi" min="0" max="100" step="1" value="0" oninput="onSl('roi',this.value)">
        <div class="st"><span>0%</span><span>25%</span><span>50%</span><span>75%</span><span>100%</span></div>
      </div>

      <div class="sg">
        <div class="sr"><span class="sl">🛒 Amazon Buy Box % Maximum</span>
          <span class="sv" id="v-bb">No maximum — showing all</span>
          <button class="br" onclick="rst('bb')">Reset</button></div>
        <input type="range" class="si" id="sl-bb" min="0" max="100" step="1" value="0" oninput="onSl('bb',this.value)">
        <div class="st"><span>0%</span><span>25%</span><span>50%</span><span>75%</span><span>100%</span></div>
      </div>

      <div class="sg">
        <div class="sr"><span class="sl">📦 BSR Drops Minimum (90d)</span>
          <span class="sv" id="v-drp">No minimum — showing all</span>
          <button class="br" onclick="rst('drp')">Reset</button></div>
        <input type="range" class="si" id="sl-drp" min="0" max="150" step="1" value="0" oninput="onSl('drp',this.value)">
        <div class="st"><span>0</span><span>37</span><span>75</span><span>112</span><span>150</span></div>
      </div>

      <div class="sg cg">
        <div class="sr"><span class="sl">🏭 Additional Cost per Unit (Prep, Packaging…)</span>
          <span class="sv" id="v-cst">€0.00 — no extra cost</span>
          <button class="br" onclick="rst('cst')">Reset</button></div>
        <input type="range" class="si" id="sl-cst" min="0" max="20" step="0.10" value="0" oninput="onSl('cst',this.value)">
        <div class="st"><span>€0</span><span>€5</span><span>€10</span><span>€15</span><span>€20</span></div>
      </div>

      <div class="fa">
        <div style="display:flex;align-items:center;gap:8px">
          <label>Sort By</label>
          <select id="sort-sel" onchange="onSort(this.value)">
            <option value="roi">ROI % (highest first)</option>
            <option value="drp">BSR Drops (highest first)</option>
            <option value="pft">Profit € (highest first)</option>
            <option value="amz">Amazon BB % (lowest first)</option>
            <option value="stb">Stability (best first)</option>
          </select>
        </div>
        <div style="display:flex;align-items:center;gap:6px">
          <input type="text" id="pname" class="pin" placeholder='Name preset (e.g. "Conservative")'>
          <button class="bsp" onclick="savePreset()">💾 Save</button>
        </div>
        <button class="bra" onclick="rstAll()">↺ Reset All</button>
      </div>
      <div class="pl" id="pl"></div>
      <div class="sb" id="sb"></div>
    </div>
  </div>

  <div class="sw">
    <input type="search" id="search" placeholder="🔍  Search by product name, ASIN, EAN, UPC or SKU…" oninput="applyF()">
  </div>
  <div class="cb" id="cb"></div>

  <div class="tw">
    <table>
      <thead><tr>
        <th onclick="sCol('tier')"        id="th-tier">Tier <span class="sa">↕</span></th>
        <th onclick="sCol('name')"        id="th-name">Product <span class="sa">↕</span></th>
        <th onclick="sCol('pa_net')"      id="th-pa_net">Cost <span class="sa">↕</span></th>
        <th onclick="sCol('bb')"          id="th-bb">BB Price <span class="sa">↕</span></th>
        <th onclick="sCol('ppf')"         id="th-ppf">FBA Fee <span class="sa">↕</span></th>
        <th onclick="sCol('ref_fee')"     id="th-ref_fee">Ref Fee <span class="sa">↕</span></th>
        <th onclick="sCol('roi')"         id="th-roi" class="sorted">ROI % <span class="sa">↓</span></th>
        <th onclick="sCol('profit')"      id="th-profit">Profit <span class="sa">↕</span></th>
        <th onclick="sCol('bsr_drops')"   id="th-bsr_drops">BSR Drops <span class="sa">↕</span></th>
        <th onclick="sCol('amazon_pct')"  id="th-amazon_pct">Amazon BB% <span class="sa">↕</span></th>
        <th onclick="sCol('stab')"        id="th-stab">Stability <span class="sa">↕</span></th>
        <th>ID / ASIN</th>
      </tr></thead>
      <tbody id="tbody"></tbody>
    </table>
    <div class="nr" id="nr" style="display:none">No products match your filters. Try adjusting the sliders.</div>
  </div>
</div>

<script>
// ════════════════════════════════════════════════════════════════
// CONSTANTS
// ════════════════════════════════════════════════════════════════
const LOCALE_MAP={
  fr:    {flag:'🇫🇷',name:'France',          domain:'amazon.fr'},
  de:    {flag:'🇩🇪',name:'Germany',         domain:'amazon.de'},
  uk:    {flag:'🇬🇧',name:'United Kingdom',  domain:'amazon.co.uk'},
  co_uk: {flag:'🇬🇧',name:'United Kingdom',  domain:'amazon.co.uk'},
  it:    {flag:'🇮🇹',name:'Italy',           domain:'amazon.it'},
  es:    {flag:'🇪🇸',name:'Spain',           domain:'amazon.es'},
  nl:    {flag:'🇳🇱',name:'Netherlands',     domain:'amazon.nl'},
  se:    {flag:'🇸🇪',name:'Sweden',          domain:'amazon.se'},
  pl:    {flag:'🇵🇱',name:'Poland',          domain:'amazon.pl'},
  be:    {flag:'🇧🇪',name:'Belgium',         domain:'amazon.com.be'},
  ie:    {flag:'🇮🇪',name:'Ireland',         domain:'amazon.ie'},
  tr:    {flag:'🇹🇷',name:'Turkey',          domain:'amazon.com.tr'},
};
const FUEL=1.015;
const FBA={
  FR:{sym:'€',rate:1,   fees:[[150,4.56],[400,5.07],[900,5.79],[1400,5.87],[1900,6.10],[3900,7.80],[5900,8.22],[8900,8.84],[11900,9.38]]},
  DE:{sym:'€',rate:1,   fees:[[150,3.12],[400,3.13],[900,3.14],[1400,3.15],[1900,3.17],[3900,4.28],[5900,4.96],[8900,5.77],[11900,6.39]]},
  UK:{sym:'£',rate:1.18,fees:[[150,2.91],[400,3.00],[900,3.04],[1400,3.05],[1900,3.25],[3900,3.27],[5900,3.56],[8900,3.57],[11900,3.58]]},
  IT:{sym:'€',rate:1,   fees:[[150,4.13],[400,4.54],[900,4.95],[1400,5.11],[1900,5.14],[3900,5.16],[5900,5.38],[8900,5.41],[11900,6.25]]},
  ES:{sym:'€',rate:1,   fees:[[150,3.52],[400,3.74],[900,3.95],[1400,4.21],[1900,4.27],[3900,5.50],[5900,5.96],[8900,7.24],[11900,7.85]]},
  NL:{sym:'€',rate:1,   fees:[[150,3.47],[400,3.51],[900,4.03],[1400,4.50],[1900,4.82],[3900,5.90],[5900,5.30],[8900,5.74],[11900,6.31]]},
  BE:{sym:'€',rate:1,   fees:[[150,3.39],[400,3.67],[900,4.15],[1400,4.63],[1900,4.95],[3900,6.38],[5900,6.54],[8900,6.90],[11900,7.36]]},
  IE:{sym:'€',rate:1,   fees:[[150,1.87],[400,2.08],[900,2.37],[1400,2.75],[1900,3.02],[3900,3.52],[5900,3.67],[8900,3.88],[11900,4.13]]},
  PL:{sym:'zł',rate:.23,fees:[[150,3.61],[400,3.67],[900,3.71],[1400,3.76],[1900,3.81],[3900,3.93],[5900,4.19],[8900,4.24],[11900,4.37]]},
  SE:{sym:'kr',rate:.088,fees:[[150,45.41],[400,47.29],[900,48.19],[1400,52.68],[1900,54.49],[3900,64.10],[5900,70.20],[8900,72.20],[11900,87.92]]},
};

// ════════════════════════════════════════════════════════════════
// SUPPLIER FIELD DEFINITIONS
// Covers: EAN, GTIN, UPC, ASIN, SKU — all identifier types
// ════════════════════════════════════════════════════════════════
const SUP_FIELDS = [
  // IDENTIFIERS — at least one required
  {key:'ean',   label:'EAN (barcode)',        required:false, isId:true,
   hints:['code ean','ean','barcode','code barre','codes produit: ean','product codes: ean']},
  {key:'gtin',  label:'GTIN (14-digit EAN)',  required:false, isId:true,
   hints:['gtin','code gtin','global trade']},
  {key:'upc',   label:'UPC (US barcode)',     required:false, isId:true,
   hints:['upc','codes produit: upc','product codes: upc']},
  {key:'asin',  label:'ASIN (Amazon ID)',     required:false, isId:true,
   hints:['asin']},
  {key:'sku',   label:'SKU (supplier ref)',   required:false, isId:true,
   hints:['sku','référence','reference','ref','n° art','n° article','article number','partnumber','part number','part_number']},
  // REQUIRED DATA
  {key:'name',  label:'Product Name ✦',       required:true,  isId:false,
   hints:['descriptif','designation','libelle','nom','description','name','titre','product','label','article']},
  {key:'pa_net',label:'Purchase Cost (PA NET) ✦', required:true, isId:false,
   hints:['pa net','pa_net','prix achat','purchase','buying','cost','coût','net price','pv ht','prix ht','tarif','achat']},
  // OPTIONAL
  {key:'pvc',   label:'RRP / List Price',     required:false, isId:false,
   hints:['pvc','rrp','pvp','prix vente','list price','retail','recommended','conseille','msrp']},
];

// ════════════════════════════════════════════════════════════════
// STATE
// ════════════════════════════════════════════════════════════════
let supText='', kpaText='';
let supHeaders=[], supRows=[];
let colMap={ean:-1,gtin:-1,upc:-1,asin:-1,sku:-1,name:-1,pa_net:-1,pvc:-1};
let PRODUCTS=[];
let detectedMkt=null;
let fRoi=0,fBB=0,fDrp=0,fCst=0,fSort='roi';
let _cs={};
let _matchStats={};

// ════════════════════════════════════════════════════════════════
// SCREENS
// ════════════════════════════════════════════════════════════════
function showScreen(id){
  document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
  document.getElementById('s-'+id).classList.add('active');
}
function newAnalysis(){
  supText='';kpaText='';
  detectedMkt=null;
  PRODUCTS=[];_cs={};_matchStats={};
  // Reset upload dropzones
  ['sup','kpa'].forEach(t=>{
    document.getElementById('dz-'+t).className='dz';
    document.getElementById('dzt-'+t).textContent='Click or drag & drop';
    document.getElementById('dzt-'+t).style.color='';
    document.getElementById('dzh-'+t).style.color='';
    document.getElementById('fi-'+t).value='';
  });
  document.getElementById('dzh-sup').textContent='CSV accepted · Numbers/Excel → export as CSV first';
  document.getElementById('dzh-kpa').textContent='CSV file · French or English Keepa export';
  checkReady();
  showScreen('upload');
}

// ════════════════════════════════════════════════════════════════
// LAYER 1 — FILE UPLOAD & VALIDATION
// ════════════════════════════════════════════════════════════════
function onDrop(e,type){
  e.preventDefault();
  document.getElementById('dz-'+type).classList.remove('over');
  if(e.dataTransfer.files[0]) readFile(e.dataTransfer.files[0],type);
}
function onFile(inp,type){if(inp.files[0]) readFile(inp.files[0],type);}

function readFile(file,type){
  const fname=file.name.toLowerCase();
  const dz=document.getElementById('dz-'+type);
  const hint=document.getElementById('dzh-'+type);
  const txt=document.getElementById('dzt-'+type);

  // Block unsupported formats with specific instructions
  const badMap={
    '.numbers':'Open in Numbers → File → Export To → CSV, then upload the CSV.',
    '.xlsx':   'Open in Excel → File → Save As → CSV UTF-8, then upload the CSV.',
    '.xls':    'Open in Excel → File → Save As → CSV, then upload the CSV.',
    '.pdf':    'Send the PDF to Claude with MASTER_MERGE_PROMPT to convert it first.',
    '.doc':    'Convert to CSV first. Open the file and export as CSV.',
    '.docx':   'Convert to CSV first. Open the file and export as CSV.',
    '.ods':    'Open in LibreOffice → File → Save As → CSV, then upload.',
  };
  for(const[ext,msg] of Object.entries(badMap)){
    if(fname.endsWith(ext)){
      dz.className='dz err';
      txt.style.color='var(--red)';
      txt.textContent='⚠ Cannot read: '+file.name;
      hint.style.color='var(--red)';
      hint.textContent=msg;
      if(type==='sup') supText='';
      else kpaText='';
      checkReady();
      return;
    }
  }

  // Reset styling
  dz.className='dz';
  txt.style.color='';hint.style.color='';

  const reader=new FileReader();
  reader.onload=e=>{
    const text=e.target.result;
    if(type==='sup'){
      supText=text;
      dz.className='dz done';
      txt.textContent='✓ '+file.name;
      hint.textContent=Math.round(file.size/1024)+'KB — ready';
    } else {
      kpaText=text;
      dz.className='dz done';
      txt.textContent='✓ '+file.name;
      hint.textContent=Math.round(file.size/1024)+'KB — ready';
    }
    checkReady();
  };
  // Latin-1 handles most European supplier files + Keepa exports
  reader.readAsText(file,'latin1');
}

function checkReady(){
  document.getElementById('btn-go').classList.toggle('ready',!!(supText&&kpaText));
}

// ════════════════════════════════════════════════════════════════
// LAYER 2 — CSV PARSER
// State-machine parser: handles quoted fields, embedded commas,
// embedded newlines, semicolon/comma/tab delimiters
// ════════════════════════════════════════════════════════════════
function parseCSV(text){
  // Detect delimiter by counting unquoted occurrences in first line
  const firstLine=text.split(/\r?\n/)[0]||'';
  let commas=0,semis=0,tabs=0;
  let q=false;
  for(const c of firstLine){
    if(c==='"'){q=!q;continue;}
    if(!q){if(c===',')commas++;else if(c===';')semis++;else if(c==='\t')tabs++;}
  }
  const d=tabs>commas&&tabs>semis?'\t':semis>commas?';':',';

  const rows=[];
  let row=[''];
  let inQ=false;

  for(let i=0;i<text.length;i++){
    const c=text[i];
    const nx=text[i+1];
    if(c==='"'){
      if(inQ&&nx==='"'){row[row.length-1]+='"';i++;}  // escaped quote
      else inQ=!inQ;
    } else if(c===d&&!inQ){
      row.push('');  // new field
    } else if((c==='\r'||c==='\n')&&!inQ){
      if(c==='\r'&&nx==='\n')i++;  // skip \r\n pair
      if(row.length>1||row[0].trim())rows.push(row);
      row=[''];
    } else {
      row[row.length-1]+=c;
    }
  }
  if(row.length>1||row[0].trim())rows.push(row);
  return rows;
}

// Clean a cell value: strip quotes and whitespace
function cv(s){return(s||'').replace(/^"|"$/g,'').trim();}

// Parse numeric value: handles €12,50 / 12.50 / 12,50 / "12.50€"
function cn(s){
  if(!s)return null;
  let v=String(s).replace(/[^\d.,\-]/g,'');  // strip currency/spaces
  // If both . and , exist, the last one is decimal separator
  const lastDot=v.lastIndexOf('.');
  const lastComma=v.lastIndexOf(',');
  if(lastDot>=0&&lastComma>=0){
    if(lastComma>lastDot) v=v.replace(/\./g,'').replace(',','.');  // 1.234,56 → 1234.56
    else v=v.replace(/,/g,'');                                       // 1,234.56 → 1234.56
  } else {
    v=v.replace(',','.');  // simple 12,50 → 12.50
  }
  const x=parseFloat(v);
  return isNaN(x)?null:x;
}

// ════════════════════════════════════════════════════════════════
// LAYER 3 — IDENTIFIER NORMALIZER
// Converts ANY identifier format to a clean string for matching.
// Handles: int→string, .0 suffix, scientific notation, leading zeros,
// GTIN→EAN conversion (strip leading zero), whitespace
// ════════════════════════════════════════════════════════════════
function normalizeId(raw){
  if(!raw)return '';
  let s=String(raw).trim();
  // Remove .0 suffix (float corruption: 4008431797601.0 → 4008431797601)
  s=s.replace(/\.0+$/,'');
  // Remove scientific notation (4.00843E+12 → 400843...)
  if(/[eE][+\-]?\d+/.test(s)){
    try{s=String(Math.round(parseFloat(s)));}catch(e){}
  }
  // Remove any remaining decimal part
  s=s.replace(/\.\d+$/,'');
  // Keep only alphanumeric (covers EAN digits and ASIN letters+digits)
  s=s.replace(/[^0-9a-zA-Z]/g,'');
  // Remove leading zeros ONLY for numeric identifiers (EAN/UPC/GTIN)
  // ASIN starts with B so we keep it as-is
  if(/^\d+$/.test(s)) s=s.replace(/^0+/,'');
  return s;
}

// Extract ALL identifier variants from a cell that may contain multiple
// values separated by | or , (Keepa format: "4008431797601, 4053452002081")
function extractIds(raw){
  if(!raw)return[];
  return String(raw).split(/[|,]/)
    .map(e=>normalizeId(e))
    .filter(e=>e.length>=8);  // min 8 chars = valid EAN/UPC/ASIN
}

// ════════════════════════════════════════════════════════════════
// COLUMN MAPPING UI
// ════════════════════════════════════════════════════════════════
function goToMapping(){
  if(!supText||!kpaText)return;
  const rows=parseCSV(supText);
  if(rows.length<2){
    alert('Supplier CSV appears empty or unreadable. Try re-exporting as CSV.');return;
  }

  // Find the actual header row — skip title/image rows at top
  // A valid header row has at least 3 non-empty cells
  let headIdx=0;
  for(let i=0;i<Math.min(rows.length,8);i++){
    if(rows[i].filter(c=>cv(c).length>0).length>=3){headIdx=i;break;}
  }
  supHeaders=rows[headIdx].map(h=>cv(h));
  supRows=rows.slice(headIdx+1).filter(r=>r.some(c=>cv(c)));

  // Auto-detect column mapping
  colMap={ean:-1,gtin:-1,upc:-1,asin:-1,sku:-1,name:-1,pa_net:-1,pvc:-1};
  SUP_FIELDS.forEach(f=>{
    // Try exact match first, then partial match
    let idx=supHeaders.findIndex(h=>
      f.hints.some(hint=>h.toLowerCase()===hint)
    );
    if(idx<0) idx=supHeaders.findIndex(h=>
      f.hints.some(hint=>h.toLowerCase().includes(hint))
    );
    if(idx>=0) colMap[f.key]=idx;
  });

  buildMapUI();
  showScreen('map');
}

function buildMapUI(){
  const wrap=document.getElementById('map-rows');
  wrap.innerHTML=supHeaders.map((h,i)=>{
    const mapped=Object.entries(colMap).find(([k,v])=>v===i);
    const sel=mapped?mapped[0]:'ignore';
    return`<div class="map-row">
      <div class="col-name" title="${h}">${h||'(empty)'}</div>
      <div class="arrow">→</div>
      <select class="col-sel${sel!=='ignore'?' mapped':''}" data-col="${i}" onchange="onMap(${i},this)">
        <option value="ignore"${sel==='ignore'?' selected':''}>— Ignore —</option>
        ${SUP_FIELDS.map(f=>`<option value="${f.key}"${sel===f.key?' selected':''}>${f.label}</option>`).join('')}
      </select>
    </div>`;
  }).join('');

  // Show first real data row as preview
  if(supRows.length>0){
    const first=supRows[0];
    document.getElementById('map-preview').innerHTML=
      '<strong>First data row:</strong> '+
      supHeaders.slice(0,8).map((h,i)=>`${h}: <strong>${cv(first[i])||'—'}</strong>`).join(' &nbsp;·&nbsp; ')+
      (supHeaders.length>8?'…':'');
  }
  validateMap();
}

function onMap(colIdx,sel){
  const field=sel.value;
  // Clear any previous mapping for this column index
  Object.keys(colMap).forEach(k=>{if(colMap[k]===colIdx)colMap[k]=-1;});
  if(field!=='ignore'){
    // If another column was mapped to this field, unmap it
    if(colMap[field]>=0){
      const old=document.querySelector(`select[data-col="${colMap[field]}"]`);
      if(old){old.value='ignore';old.classList.remove('mapped');}
    }
    colMap[field]=colIdx;
    sel.classList.add('mapped');
  } else {
    sel.classList.remove('mapped');
  }
  validateMap();
}

function validateMap(){
  const st=document.getElementById('map-status');
  const btn=document.getElementById('btn-confirm');

  // Check required fields
  const missingRequired=SUP_FIELDS.filter(f=>f.required&&!f.isId&&colMap[f.key]<0);

  // Check at least one identifier is mapped
  const hasIdentifier=SUP_FIELDS.filter(f=>f.isId).some(f=>colMap[f.key]>=0);

  if(missingRequired.length>0){
    st.className='map-status err';
    st.textContent='⚠ Missing: '+missingRequired.map(f=>f.label.replace(' ✦','')).join(', ');
    btn.style.opacity='.4';btn.style.pointerEvents='none';
  } else if(!hasIdentifier){
    st.className='map-status err';
    st.textContent='⚠ Map at least one identifier: EAN, GTIN, UPC, ASIN, or SKU';
    btn.style.opacity='.4';btn.style.pointerEvents='none';
  } else {
    const ids=SUP_FIELDS.filter(f=>f.isId&&colMap[f.key]>=0).map(f=>f.label.split(' ')[0]);
    st.className='map-status ok';
    st.textContent=`✓ Ready — matching by: ${ids.join(', ')}`;
    btn.style.opacity='1';btn.style.pointerEvents='all';
  }
}

// ════════════════════════════════════════════════════════════════
// LAYER 4 — PARSE SUPPLIER
// Extracts and normalizes all identifiers + data from supplier file
// ════════════════════════════════════════════════════════════════
function parseSupplier(){
  const out={};  // key: normalized identifier → product data
  let skipped=0;

  for(const row of supRows){
    try{
      const name=colMap.name>=0?cv(row[colMap.name]||''):'';
      if(!name)continue;

      const paStr=colMap.pa_net>=0?cv(row[colMap.pa_net]||''):'';
      if(!paStr||paStr.toLowerCase().includes('demande'))continue;
      const pa=cn(paStr);
      if(!pa||pa<=0)continue;

      const pvc=colMap.pvc>=0&&colMap.pvc<row.length?cn(cv(row[colMap.pvc]||''))||0:0;

      // Collect all identifiers from this row
      const ids=[];

      // EAN — may have multiple values
      if(colMap.ean>=0){
        const raw=cv(row[colMap.ean]||'');
        extractIds(raw).forEach(id=>ids.push({type:'ean',val:id}));
      }
      // GTIN — strip leading zero to get EAN
      if(colMap.gtin>=0){
        const raw=cv(row[colMap.gtin]||'');
        extractIds(raw).forEach(id=>{
          ids.push({type:'gtin',val:id});
          // Also add GTIN without leading zero (= EAN)
          if(id.startsWith('0'))ids.push({type:'gtin_as_ean',val:id.replace(/^0+/,'')});
        });
      }
      // UPC
      if(colMap.upc>=0){
        const raw=cv(row[colMap.upc]||'');
        extractIds(raw).forEach(id=>ids.push({type:'upc',val:id}));
      }
      // ASIN
      if(colMap.asin>=0){
        const raw=cv(row[colMap.asin]||'');
        if(raw.trim())ids.push({type:'asin',val:normalizeId(raw)});
      }
      // SKU
      if(colMap.sku>=0){
        const raw=cv(row[colMap.sku]||'');
        if(raw.trim())ids.push({type:'sku',val:normalizeId(raw)});
      }

      if(!ids.length){skipped++;continue;}

      const product={
        name,pa_net:pa,pvc,
        // Store first EAN as primary identifier for display
        ean: ids.find(x=>x.type==='ean')?.val ||
             ids.find(x=>x.type==='gtin_as_ean')?.val ||
             ids.find(x=>x.type==='upc')?.val ||
             ids[0]?.val || '',
        matched_by:'',
      };

      // Register product under ALL its identifiers
      for(const id of ids){
        if(id.val&&id.val.length>=3){
          out[id.val]=product;
        }
      }
    }catch(e){skipped++;}
  }
  return{products:out, skipped};
}

// ════════════════════════════════════════════════════════════════
// LAYER 5 — PARSE KEEPA
// Extracts all identifier columns and stores product data under
// every possible identifier variant for maximum match coverage
// ════════════════════════════════════════════════════════════════
function parseKeepa(){
  const rows=parseCSV(kpaText);
  if(rows.length<2)return{products:{},count:0};
  const hdr=rows[0].map(h=>cv(h));

  // Detect marketplace from Locale/Région/Region column — always reset first
  detectedMkt=null;
  const locIdx=hdr.findIndex(h=>{const l=h.toLowerCase();return l==='locale'||l==='region'||l.includes('gion');});
  if(locIdx>=0&&rows.length>1){
    const locCode=(rows[1][locIdx]||'').trim().toLowerCase().replace('-','_').replace('.','_');
    detectedMkt=LOCALE_MAP[locCode]||LOCALE_MAP[locCode.split('_')[0]]||null;
  }

  // Column finder — partial match, case insensitive
  function c(...pats){
    for(const p of pats){
      const i=hdr.findIndex(h=>h.toLowerCase().includes(p.toLowerCase()));
      if(i>=0)return i;
    }
    return -1;
  }

  const idx={
    asin:    c('ASIN'),
    ean:     c('Codes produit: EAN','Product Codes: EAN','codes produit: ean'),
    gtin:    c('Codes produit: GTIN','Product Codes: GTIN','codes produit: gtin'),
    upc:     c('Codes produit: UPC','Product Codes: UPC','codes produit: upc'),
    impBy:   c('Imported by Code'),  // often contains the EAN used to import
    title:   c('Titre','Title'),
    brand:   c('Marque','Brand'),
    bbCur:   c('Buy Box: Courant','Buy Box: Current'),
    bbAvg:   c('Buy Box: Moyenne sur 90','Buy Box: 90 days avg'),
    bbStock: c('Buy Box: Stock'),
    bbSell:  c('Buy Box: Buy Box Vendeur','Buy Box: Buy Box Seller'),
    amzPct:  c('Buy Box: % Amazon 90','% Amazon 90 jours'),
    bbWin:   c('Nombre de gagnants 90','90 day winner'),
    bsrCur:  c('Classement des ventes: Courant','Sales Rank: Current'),
    bsrAvg:  c('Classement des ventes: Moyenne sur 90','Sales Rank: 90 days avg'),
    bsrDrp:  c('Chutes au cours des 90','Sales Rank: Drops','Drops last 90'),
    fba:     c("Frais d'enlèvement et d'emballage","FBA Pick","Frais d'enlèvement"),
    ref:     c('% de frais de parrainage','Referral fee %'),
    cat:     c('Catégories: Principale','Categories: Root'),
  };

  const g=(row,i)=>i>=0&&i<row.length?cv(row[i]):'';
  const out={};
  let count=0;

  for(const row of rows.slice(1)){
    const asin=g(row,idx.asin);
    if(!asin||asin.length<5)continue;
    const bb=cn(g(row,idx.bbCur));
    if(!bb||bb<=0)continue;

    count++;
    const pd={
      asin,
      title:g(row,idx.title)||asin,
      brand:g(row,idx.brand)||'',
      bb_cur:bb,
      bb_avg:cn(g(row,idx.bbAvg))||bb,
      bsr_cur:parseInt(cn(g(row,idx.bsrCur))||0)||null,
      bsr_avg:parseInt(cn(g(row,idx.bsrAvg))||0)||null,
      bsr_drops:parseInt(cn(g(row,idx.bsrDrp))||0)||0,
      amazon_pct:cn(g(row,idx.amzPct))||0,
      bb_seller:g(row,idx.bbSell)||'N/A',
      bb_stock:g(row,idx.bbStock)||'N/A',
      bb_winners:parseInt(cn(g(row,idx.bbWin))||0)||0,
      fba_fee:cn(g(row,idx.fba)),
      ref_pct:cn(g(row,idx.ref)),
      category:g(row,idx.cat)||'',
    };

    // Register under ASIN (always reliable)
    out[normalizeId(asin)]=pd;

    // Register under ALL EAN variants (split by | and ,)
    const eanRaw=g(row,idx.ean);
    extractIds(eanRaw).forEach(e=>{
      out[e]=pd;
      // Also register with leading zero stripped (handles GTIN→EAN)
      if(e.startsWith('0'))out[e.replace(/^0+/,'')]=pd;
    });

    // Register under GTIN variants
    const gtinRaw=g(row,idx.gtin);
    extractIds(gtinRaw).forEach(g2=>{
      out[g2]=pd;
      // GTIN with leading zero stripped = EAN
      if(g2.startsWith('0'))out[g2.replace(/^0+/,'')]=pd;
    });

    // Register under UPC
    const upcRaw=g(row,idx.upc);
    extractIds(upcRaw).forEach(u=>out[u]=pd);

    // Register under "Imported by Code" (often the exact EAN used)
    const impRaw=g(row,idx.impBy);
    if(impRaw){const im=normalizeId(impRaw);if(im.length>=8)out[im]=pd;}
  }

  return{products:out, count};
}

// ════════════════════════════════════════════════════════════════
// LAYER 6 — BUILD PRODUCTS (match + calculate)
// ════════════════════════════════════════════════════════════════
function fbaEst(p){
  if(p<8)return 3.55;if(p<13)return 4.65;if(p<22)return 5.20;
  if(p<38)return 5.90;if(p<58)return 6.20;if(p<85)return 7.92;return 8.97;
}
function refPct(name,cat,raw){
  if(raw&&raw>0)return raw;
  const n=(name+' '+cat).toLowerCase();
  if(/mitigeur|robinet|douche|abattant|wc|lavabo|évier|evier|plomberie|flexible|douchette|sanitaire/.test(n))return 15;
  return 15;
}
function fbaForMkt(code,frPpf){
  const s=[3.55,4.65,5.20,5.90,6.20,7.92,8.97,9.38];
  let ti=s.length-1;
  for(let i=0;i<s.length;i++){if(frPpf<=s[i]+0.50){ti=i;break;}}
  const m=FBA[code];if(!m)return null;
  const idx=Math.min(ti,m.fees.length-1);
  const fee=Math.round(m.fees[idx][1]*FUEL*100)/100;
  return{fee,feeEur:Math.round(fee*m.rate*100)/100,sym:m.sym,
    tierG:FBA.FR.fees[Math.min(ti,FBA.FR.fees.length-1)][0]};
}
function stabCalc(bb,avg){
  if(!avg||avg<=0)return['Unknown',null];
  const d=Math.abs(bb-avg)/avg*100;
  return[d<5?'Stable':d<15?'Moderate':'Volatile',Math.round(d*10)/10];
}
function tierCalc(roi,amz,stab,drops){
  if(roi>=15&&amz<30&&['Stable','Moderate'].includes(stab)&&drops>=5)return 1;
  if(roi>=10)return 2;if(roi>0)return 3;return 4;
}

function buildProducts(supData,kpaData){
  const rows=[];
  let matched=0,noMatch=0,noBB=0;
  const seen=new Set();  // avoid duplicate products

  for(const[id,sp]of Object.entries(supData.products)){
    // Look up in Keepa using the normalized identifier
    const kd=kpaData.products[id];
    if(!kd){noMatch++;continue;}
    if(!kd.bb_cur||kd.bb_cur<=0){noBB++;continue;}

    // Deduplicate by ASIN — one product should appear once
    if(seen.has(kd.asin))continue;
    seen.add(kd.asin);
    matched++;

    const bb=kd.bb_cur,avg=kd.bb_avg;
    const ppf=kd.fba_fee||fbaEst(bb);
    const rp=refPct(sp.name,kd.category,kd.ref_pct);
    const[stab,stabDev]=stabCalc(bb,avg);
    const amz=kd.amazon_pct||0;
    const drops=kd.bsr_drops||0;
    const refFee=Math.round(bb*rp/100*100)/100;
    const profit=Math.round((bb-ppf-refFee-sp.pa_net)*100)/100;
    const roi=sp.pa_net>0?Math.round(profit/sp.pa_net*1000)/10:0;

    rows.push({
      ean:sp.ean,name:sp.name,pa_net:sp.pa_net,pvc:sp.pvc||0,
      asin:kd.asin,bb,bb_avg:avg,
      ppf:Math.round(ppf*100)/100,ref_pct:rp,ref_fee:refFee,
      profit,roi,stab,stab_dev:stabDev,
      amazon_pct:amz,bsr_cur:kd.bsr_cur,bsr_avg:kd.bsr_avg,
      bsr_drops:drops,bb_seller:kd.bb_seller,bb_stock:kd.bb_stock,
      bb_winners:kd.bb_winners,tier:tierCalc(roi,amz,stab,drops),
      brand:kd.brand||'',category:kd.category||'',
    });
  }
  rows.sort((a,b)=>b.roi-a.roi);
  return{rows,matched,noMatch,noBB,
    supTotal:new Set(Object.values(supData.products).map(p=>p.name)).size,
    kpaTotal:kpaData.count};
}

// ════════════════════════════════════════════════════════════════
// RUN ANALYSIS
// ════════════════════════════════════════════════════════════════
function runAnalysis(){
  showScreen('load');
  setTimeout(()=>{
    document.getElementById('load-step').textContent='Parsing supplier catalog…';
    setTimeout(()=>{
      const supData=parseSupplier();
      const supCount=Object.keys(supData.products).length;
      document.getElementById('load-step').textContent=
        `${supCount} supplier identifiers found — parsing Keepa…`;
      setTimeout(()=>{
        const kpaData=parseKeepa();
        document.getElementById('load-step').textContent=
          `${kpaData.count} Keepa products — matching and calculating…`;
        setTimeout(()=>{
          const res=buildProducts(supData,kpaData);
          PRODUCTS=res.rows;
          _matchStats=res;

          document.getElementById('dash-sub').textContent=
            `${res.supTotal} supplier products · ${res.kpaTotal} Keepa · ${new Date().toLocaleDateString('en-GB')}`;
          document.getElementById('dash-badge').textContent=
            `${res.matched} / ${res.supTotal} matched`;

          renderMatchReport(res);
          showDetectedMkt();
          updateKPIs();
          renderPresets();
          rstAll();
          showScreen('dash');
        },300);
      },300);
    },100);
  },100);
}

// ════════════════════════════════════════════════════════════════
// MATCH REPORT
// ════════════════════════════════════════════════════════════════
function renderMatchReport(res){
  document.getElementById('match-stats').innerHTML=[
    {cls:'ok',   val:res.matched,   lbl:'Products matched'},
    {cls:'info', val:res.kpaTotal,  lbl:'Keepa products'},
    {cls:'warn', val:res.noMatch,   lbl:'No Keepa match'},
    {cls:'bad',  val:res.noBB,      lbl:'No Buy Box price'},
  ].map(s=>`<div class="match-stat ${s.cls}">
    <div class="ms-val">${s.val}</div>
    <div class="ms-lbl">${s.lbl}</div>
  </div>`).join('');
}

// ════════════════════════════════════════════════════════════════
// MARKETPLACE (detected from CSV — display only)
// ════════════════════════════════════════════════════════════════
function showDetectedMkt(){
  const el=document.getElementById('mkt-detected');
  if(!detectedMkt){el.style.display='none';return;}
  el.style.display='flex';
  el.innerHTML=`
    <span class="mkt-det-lbl">Marketplace detected</span>
    <span class="mkt-det-flag">${detectedMkt.flag}</span>
    <div class="mkt-det-info">
      <div class="mkt-det-name">${detectedMkt.name}</div>
      <div class="mkt-det-domain">${detectedMkt.domain}</div>
    </div>
    <a class="mkt-det-link" href="https://www.${detectedMkt.domain}" target="_blank">🔗 ${detectedMkt.domain}</a>`;
}
function mktUrl(asin){const d=detectedMkt?detectedMkt.domain:'amazon.fr';return`https://www.${d}/dp/${asin}`;}

// ════════════════════════════════════════════════════════════════
// KPIs
// ════════════════════════════════════════════════════════════════
function updateKPIs(){
  const tc={1:0,2:0,3:0,4:0};
  PRODUCTS.forEach(r=>tc[r.tier]=(tc[r.tier]||0)+1);
  document.getElementById('kpi-row').innerHTML=[
    {cls:'t1',val:tc[1],lbl:'Tier 1 — Top picks'},
    {cls:'t2',val:tc[2],lbl:'Tier 2 — Viable'},
    {cls:'t3',val:tc[3],lbl:'Tier 3 — Marginal'},
    {cls:'ng',val:tc[4],lbl:'No-go'},
  ].map(k=>`<div class="kpi ${k.cls}"><div class="val">${k.val}</div><div class="lbl">${k.lbl}</div></div>`).join('');
}

// ════════════════════════════════════════════════════════════════
// HELPERS
// ════════════════════════════════════════════════════════════════
function ep(r){return Math.round((r.profit-fCst)*100)/100;}
function er(r){return r.pa_net>0?Math.round(ep(r)/r.pa_net*1000)/10:0;}
function rc(v){return v>=30?'rh':v>=15?'rm':'rl';}
function sc(s){return{Stable:'ss',Moderate:'smod',Volatile:'svol',Unknown:'sunk'}[s]||'sunk';}
function ac(p){return p<30?'al':p<60?'am':'ah';}
function fi(n){return n==null||n===0?'N/A':Number(n).toLocaleString();}
function tb(t){
  const m={1:'t1b 🥇 Tier 1',2:'t2b 🥈 Tier 2',3:'t3b 🥉 Tier 3',4:'t4b ❌ No-go'};
  const v=m[t]||'';const[cls,...rest]=v.split(' ');
  return`<span class="tier-badge ${cls}">${rest.join(' ')}</span>`;
}

// ════════════════════════════════════════════════════════════════
// FILTER PANEL
// ════════════════════════════════════════════════════════════════
function toggleFP(){
  const p=document.getElementById('fp');p.classList.toggle('open');
  document.querySelector('.fp-toggle-arr').textContent=p.classList.contains('open')?'▲':'▼';
}
function onSl(t,v){
  v=parseFloat(v);
  if(t==='roi'){fRoi=v;document.getElementById('v-roi').textContent=v===0?'No minimum — showing all':`ROI ≥ ${v}%`;}
  else if(t==='bb'){fBB=v;document.getElementById('v-bb').textContent=v===0?'No maximum — showing all':`Amazon BB ≤ ${v}%`;}
  else if(t==='drp'){fDrp=v;document.getElementById('v-drp').textContent=v===0?'No minimum — showing all':`Drops ≥ ${v}`;}
  else if(t==='cst'){fCst=v;document.getElementById('v-cst').textContent=v===0?'€0.00 — no extra cost':`€${v.toFixed(2)} extra per unit`;}
  updateSum();applyF();
}
function rst(t){
  const d={roi:0,bb:0,drp:0,cst:0};
  document.getElementById('sl-'+t).value=d[t];onSl(t,d[t]);
}
function rstAll(){
  ['roi','bb','drp','cst'].forEach(t=>rst(t));
  fSort='roi';document.getElementById('sort-sel').value='roi';
  const sb=document.getElementById('search');if(sb)sb.value='';
  document.querySelectorAll('thead th').forEach(t=>t.classList.remove('sorted'));
  const th=document.getElementById('th-roi');
  if(th){th.classList.add('sorted');th.querySelector('.sa').textContent='↓';}
  applyF();
}
function onSort(v){
  fSort=v;
  const m={roi:'roi',drp:'bsr_drops',pft:'profit',amz:'amazon_pct',stb:'stab'};
  document.querySelectorAll('thead th').forEach(t=>t.classList.remove('sorted'));
  const k=m[v];
  if(k){const th=document.getElementById('th-'+k);if(th){th.classList.add('sorted');th.querySelector('.sa').textContent=v==='amz'?'↑':'↓';}}
  applyF();
}
function updateSum(){
  const p=[];
  if(fRoi>0)p.push(`ROI ≥ ${fRoi}%`);
  if(fBB>0)p.push(`BB ≤ ${fBB}%`);
  if(fDrp>0)p.push(`Drops ≥ ${fDrp}`);
  if(fCst>0)p.push(`+€${fCst.toFixed(2)}`);
  document.getElementById('fp-sum').textContent=p.length?' — '+p.join(' · '):' — No filters active';
}

// ════════════════════════════════════════════════════════════════
// PRESETS
// ════════════════════════════════════════════════════════════════
function savePreset(){
  const name=document.getElementById('pname').value.trim();if(!name)return;
  const p=JSON.parse(localStorage.getItem('sv_presets')||'{}');
  p[name]={roi:fRoi,bb:fBB,drp:fDrp,cst:fCst,sort:fSort};
  localStorage.setItem('sv_presets',JSON.stringify(p));
  document.getElementById('pname').value='';renderPresets();
}
function loadPreset(name){
  const p=JSON.parse(localStorage.getItem('sv_presets')||'{}')[name];if(!p)return;
  document.getElementById('sl-roi').value=p.roi;onSl('roi',p.roi);
  document.getElementById('sl-bb').value=p.bb;onSl('bb',p.bb);
  document.getElementById('sl-drp').value=p.drp;onSl('drp',p.drp);
  document.getElementById('sl-cst').value=p.cst||0;onSl('cst',p.cst||0);
  fSort=p.sort||'roi';document.getElementById('sort-sel').value=fSort;onSort(fSort);
}
function delPreset(name){
  const p=JSON.parse(localStorage.getItem('sv_presets')||'{}');
  delete p[name];localStorage.setItem('sv_presets',JSON.stringify(p));renderPresets();
}
function renderPresets(){
  const p=JSON.parse(localStorage.getItem('sv_presets')||'{}');
  const keys=Object.keys(p);
  const el=document.getElementById('pl');
  if(!keys.length){el.innerHTML='';return;}
  el.innerHTML='<span class="plbl">Saved Presets</span>'+
    keys.map(n=>{
      const v=p[n];const safe=n.replace(/'/g,"\\'");
      return`<div class="pc"><span onclick="loadPreset('${safe}')">
        <span class="pn">${n}</span>
        <span class="pm">ROI≥${v.roi}% BB≤${v.bb}% D≥${v.drp}${v.cst>0?' +€'+v.cst.toFixed(2):''}</span>
      </span><button onclick="delPreset('${safe}')">×</button></div>`;
    }).join('');
}

// ════════════════════════════════════════════════════════════════
// STATS BAR
// ════════════════════════════════════════════════════════════════
function updateSB(vis){
  const el=document.getElementById('sb');
  if(!vis.length){el.className='sb nm';el.textContent='No products match your filters.';return;}
  el.className='sb';
  const avgR=(vis.reduce((s,r)=>s+er(r),0)/vis.length).toFixed(1);
  const avgD=Math.round(vis.reduce((s,r)=>s+r.bsr_drops,0)/vis.length);
  const avgB=(vis.reduce((s,r)=>s+r.amazon_pct,0)/vis.length).toFixed(1);
  const totP=vis.reduce((s,r)=>s+(ep(r)>0?ep(r):0),0).toFixed(0);
  el.innerHTML=`Showing <strong>${vis.length}</strong> of ${PRODUCTS.length} &nbsp;·&nbsp; `+
    `Avg ROI: <strong>${avgR}%</strong> &nbsp;·&nbsp; `+
    `Avg Drops: <strong>${avgD}</strong> &nbsp;·&nbsp; `+
    `Avg Amazon BB: <strong>${avgB}%</strong> &nbsp;·&nbsp; `+
    `Total profit: <strong>€${Number(totP).toLocaleString()}</strong>`+
    (fCst>0?` <span style="color:var(--a)">· incl. €${fCst.toFixed(2)}/unit</span>`:'');
}

// ════════════════════════════════════════════════════════════════
// FILTER + SORT
// ════════════════════════════════════════════════════════════════
function getVis(){
  const q=(document.getElementById('search').value||'').toLowerCase();
  return PRODUCTS.filter(r=>{
    if(er(r)<fRoi)return false;
    if(fBB>0&&r.amazon_pct>fBB)return false;
    if(r.bsr_drops<fDrp)return false;
    if(q&&!r.name.toLowerCase().includes(q)&&
       !(r.ean||'').includes(q)&&
       !(r.asin||'').toLowerCase().includes(q))return false;
    return true;
  });
}
const STAB={Stable:0,Moderate:1,Volatile:2,Unknown:3};
function sortVis(arr){
  return arr.slice().sort((a,b)=>{
    switch(fSort){
      case 'roi': return er(b)-er(a);
      case 'drp': return b.bsr_drops-a.bsr_drops;
      case 'pft': return ep(b)-ep(a);
      case 'amz': return a.amazon_pct-b.amazon_pct;
      case 'stb': return(STAB[a.stab]||3)-(STAB[b.stab]||3);
      default:
        if(fSort.startsWith('col_')){
          const pts=fSort.split('_');const dir=pts.pop();const key=pts.slice(1).join('_');
          if(key==='stab'){
            const diff=(STAB[a.stab]||3)-(STAB[b.stab]||3);
            return dir==='asc'?diff:-diff;
          }
          if(key==='amazon_pct'){
            return dir==='asc'?a.amazon_pct-b.amazon_pct:b.amazon_pct-a.amazon_pct;
          }
          let av=a[key],bv=b[key];
          if(av==null)av=dir==='asc'?Infinity:-Infinity;
          if(bv==null)bv=dir==='asc'?Infinity:-Infinity;
          if(typeof av==='string')return dir==='asc'?av.localeCompare(bv):bv.localeCompare(av);
          return dir==='asc'?av-bv:bv-av;
        }
        return er(b)-er(a);
    }
  });
}
function applyF(){renderTable();}
function sCol(key){
  const dir=_cs[key]==='desc'?'asc':'desc';_cs[key]=dir;
  fSort=`col_${key}_${dir}`;
  document.getElementById('sort-sel').value='roi';
  document.querySelectorAll('thead th').forEach(t=>t.classList.remove('sorted'));
  const th=document.getElementById(`th-${key}`);
  if(th){th.classList.add('sorted');th.querySelector('.sa').textContent=dir==='asc'?'↑':'↓';}
  applyF();
}

// ════════════════════════════════════════════════════════════════
// RENDER TABLE
// ════════════════════════════════════════════════════════════════
function renderTable(){
  const vis=sortVis(getVis());
  const tbody=document.getElementById('tbody');
  const nr=document.getElementById('nr');
  updateSB(vis);
  document.getElementById('cb').innerHTML=
    vis.length?`Showing <strong>${vis.length}</strong> of ${PRODUCTS.length} products`:'';
  if(!vis.length){tbody.innerHTML='';nr.style.display='block';return;}
  nr.style.display='none';
  tbody.innerHTML=vis.map((row,idx)=>{
    const epr=ep(row),ero=er(row);
    return`<tr onclick="togDet(${idx})" id="row-${idx}">
      <td>${tb(row.tier)}</td>
      <td title="${(row.name||'').replace(/"/g,'&quot;')}">${row.name}</td>
      <td>€${row.pa_net.toFixed(2)}</td>
      <td>€${row.bb.toFixed(2)}</td>
      <td>€${row.ppf.toFixed(2)}</td>
      <td>€${row.ref_fee.toFixed(2)} <span style="font-size:10px;color:var(--muted)">(${row.ref_pct.toFixed(0)}%)</span></td>
      <td class="${rc(ero)}">${ero.toFixed(1)}%</td>
      <td style="color:${epr>=0?'#22c55e':'#ef4444'}">€${epr.toFixed(2)}</td>
      <td><span class="db ${row.bsr_drops>=5?'dg':''}">${row.bsr_drops}</span></td>
      <td class="${ac(row.amazon_pct)}">${row.amazon_pct.toFixed(0)}%</td>
      <td class="${sc(row.stab)}">${row.stab}</td>
      <td><a href="${mktUrl(row.asin)}" target="_blank" onclick="event.stopPropagation()"
         style="color:var(--accent);font-size:11px">${row.asin}</a></td>
    </tr>`;
  }).join('');
  window._vis=vis;
}

// ════════════════════════════════════════════════════════════════
// DETAIL BOX
// ════════════════════════════════════════════════════════════════
function togDet(idx){
  const row=window._vis[idx];
  const tr=document.getElementById(`row-${idx}`);if(!tr)return;
  const ex=document.getElementById('det-exp');
  if(ex){const wi=parseInt(ex.dataset.idx);ex.remove();
    document.getElementById(`row-${wi}`)?.classList.remove('expanded');if(wi===idx)return;}
  tr.classList.add('expanded');
  const dt=document.createElement('tr');
  dt.className='detail-row';dt.id='det-exp';dt.dataset.idx=idx;
  dt.innerHTML=`<td colspan="12">${buildDet(row)}</td>`;
  tr.insertAdjacentElement('afterend',dt);
}

function buildDet(row){
  const epr=ep(row),ero=er(row);
  const bench=Object.entries(FBA).map(([code,mkt])=>{
    const r=fbaForMkt(code,row.ppf);if(!r)return'';
    const isFR=code==='FR';
    const diff=r.feeEur-row.ppf;
    const vsFR=isFR?'<span style="color:var(--muted)">baseline</span>'
      :diff<-0.01?`<span class="ok">save €${Math.abs(diff).toFixed(2)}</span>`
      :diff>0.01?`<span class="bad">+€${diff.toFixed(2)}</span>`
      :'<span style="color:var(--muted)">≈ same</span>';
    const rd=row.pa_net>0?(-diff/row.pa_net*100).toFixed(1):null;
    const rs=isFR||!rd?'':parseFloat(rd)>0?`<span class="ok">+${rd}pp</span>`:`<span class="bad">${rd}pp</span>`;
    return`<tr class="${isFR?'ar':''}">
      <td>${code}</td><td>${r.sym}${r.fee.toFixed(2)}</td>
      <td style="color:var(--muted);font-size:11px">${!isFR&&mkt.rate!==1?'≈€'+r.feeEur.toFixed(2):''}</td>
      <td>${vsFR}</td><td>${rs}</td></tr>`;
  }).join('');
  const tG=fbaForMkt('FR',row.ppf)?.tierG||'?';
  const xLine=fCst>0?`
    <p><span>Prep/Extra Cost</span><span style="color:var(--a)">−€${fCst.toFixed(2)}</span></p>
    <p><span>Adjusted Profit</span><span style="color:${epr>=0?'#22c55e':'#ef4444'}">€${epr.toFixed(2)}</span></p>
    <p><span>Adjusted ROI</span><span style="color:${ero>=15?'#22c55e':ero>0?'#f59e0b':'#ef4444'}">${ero.toFixed(1)}%</span></p>`:'';
  return`<div class="detail-box">
    <div class="ds">
      <h4>💰 Financials</h4>
      <p><span>Supplier Cost (PA NET)</span><span>€${row.pa_net.toFixed(2)}</span></p>
      <p><span>RRP (PVC)</span><span>€${row.pvc.toFixed(2)}</span></p>
      <p><span>Current BB Price</span><span>€${row.bb.toFixed(2)}</span></p>
      <p><span>90d Avg BB Price</span><span>${row.bb_avg?'€'+row.bb_avg.toFixed(2):'N/A'}</span></p>
      <p><span>FBA Pick &amp; Pack</span><span>€${row.ppf.toFixed(2)}</span></p>
      <p><span>Referral Fee (${row.ref_pct.toFixed(0)}%)</span><span>€${row.ref_fee.toFixed(2)}</span></p>
      <p><span>Net Profit</span><span style="color:${row.profit>=0?'#22c55e':'#ef4444'}">€${row.profit.toFixed(2)}</span></p>
      <p><span>ROI</span><span style="color:${row.roi>=15?'#22c55e':row.roi>0?'#f59e0b':'#ef4444'}">${row.roi.toFixed(1)}%</span></p>
      ${xLine}
    </div>
    <div class="ds">
      <h4>🛒 Buy Box &amp; Demand</h4>
      <p><span>ASIN</span><span><a href="${mktUrl(row.asin)}" target="_blank" style="color:var(--accent)">${row.asin}</a></span></p>
      <p><span>EAN</span><span>${row.ean||'—'}</span></p>
      <p><span>Brand</span><span>${row.brand||'—'}</span></p>
      <p><span>Amazon BB % (90d)</span><span class="${ac(row.amazon_pct)}">${row.amazon_pct.toFixed(0)}%</span></p>
      <p><span>BB Winners (90d)</span><span>${row.bb_winners}</span></p>
      <p><span>Current BB Holder</span><span>${row.bb_seller}</span></p>
      <p><span>BB Stock</span><span>${row.bb_stock}</span></p>
      <p><span>Current BSR</span><span>${fi(row.bsr_cur)}</span></p>
      <p><span>BSR Drops (90d)</span><span class="${row.bsr_drops>=5?'ok':row.bsr_drops>0?'warn':'bad'}">${row.bsr_drops}</span></p>
      <p><span>Price Stability</span><span class="${sc(row.stab)}">${row.stab}${row.stab_dev?` (±${row.stab_dev}%)`:''}</span></p>
    </div>
    <div class="ds">
      <h4>🌍 FBA Fee Benchmark <span style="font-weight:400;color:var(--muted);text-transform:none;letter-spacing:0;font-size:10px">est. ≤${tG}g +1.5% fuel</span></h4>
      <table class="sens-table">
        <thead><tr><th>Market</th><th>FBA Fee</th><th>EUR</th><th>vs FR</th><th>ROI Δ</th></tr></thead>
        <tbody>${bench}</tbody>
      </table>
    </div>
  </div>`;
}
</script>
</body>
</html>
"""

def main():
    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(HTML)
    print("[So Vizion V2.0] Dashboard ready!")
    print(f"  → {OUT_HTML}")
    webbrowser.open(f"file://{OUT_HTML}")
    print()
    print("MATCHING: EAN → GTIN → UPC → ASIN → SKU")
    print("All 3 Gemini fixes applied in normalizeId()")
    print("All sliders and filters fully working")

if __name__ == "__main__":
    main()