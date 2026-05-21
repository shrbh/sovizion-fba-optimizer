"""
So Vizion — Flask Integration Server
Serves the FBA Optimizer dashboard and orchestrates Keepa automation.

Run:  python app.py
Open: http://localhost:5001
"""

import csv
import io
import re
import subprocess
import threading
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, jsonify, request

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR        = Path(__file__).parent
KEEPA_EXPORTS_DIR = Path("/Users/soso/keepa vs keepa")
TEMP_DIR          = Path("/tmp/sovizion")
PYTHON            = str(SCRIPT_DIR / ".venv/bin/python")
KEEPA_SCRIPT      = str(SCRIPT_DIR / "keepaautomation.py")

KEEPA_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# ── Flask app ──────────────────────────────────────────────────────────────────
app  = Flask(__name__)
jobs: dict = {}   # job_id → {status, logs, result_file, error, proc}


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return _HTML


@app.route("/api/run-keepa", methods=["POST"])
def api_run_keepa():
    if "csv" not in request.files:
        return jsonify(error="No CSV file provided"), 400

    job_id  = uuid.uuid4().hex[:8]
    tmp_csv = TEMP_DIR / f"{job_id}.csv"
    request.files["csv"].save(str(tmp_csv))

    jobs[job_id] = dict(status="running", logs=[], result_file=None, error=None, proc=None)

    def _run():
        proc = subprocess.Popen(
            [PYTHON, KEEPA_SCRIPT,
             "--csv", str(tmp_csv),
             "--output", str(KEEPA_EXPORTS_DIR),
             "--no-wait"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        jobs[job_id]["proc"] = proc
        result_file = None
        for raw in proc.stdout:
            line = raw.rstrip()
            jobs[job_id]["logs"].append(line)
            if "File saved to:" in line:
                result_file = line.split("File saved to:")[-1].strip()
        proc.wait()

        if result_file and Path(result_file).exists():
            ts  = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            dst = KEEPA_EXPORTS_DIR / f"keepa_export_{ts}.csv"
            Path(result_file).rename(dst)
            jobs[job_id]["result_file"] = dst.name
            jobs[job_id]["status"]      = "complete"
        else:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"]  = "Automation failed — check the log above for details"

    threading.Thread(target=_run, daemon=True).start()
    return jsonify(job_id=job_id)


@app.route("/api/keepa-status/<job_id>")
def api_keepa_status(job_id):
    j = jobs.get(job_id)
    if not j:
        return jsonify(error="Job not found"), 404
    return jsonify(status=j["status"], logs=j["logs"],
                   result_file=j["result_file"], error=j["error"])


@app.route("/api/confirm-login/<job_id>", methods=["POST"])
def api_confirm_login(job_id):
    j = jobs.get(job_id)
    if j and j.get("proc"):
        try:
            j["proc"].stdin.write("\n")
            j["proc"].stdin.flush()
        except OSError:
            pass
    return jsonify(ok=True)


@app.route("/api/keepa-exports")
def api_keepa_exports():
    files = sorted(
        KEEPA_EXPORTS_DIR.glob("keepa_export_*.csv"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    return jsonify([
        {"name": f.name,
         "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")}
        for f in files
    ])


@app.route("/api/read-keepa/<path:filename>")
def api_read_keepa(filename):
    f = KEEPA_EXPORTS_DIR / Path(filename).name   # strip any path traversal
    if not f.exists():
        return "Not found", 404
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return Response(f.read_text(encoding=enc),
                            mimetype="text/plain; charset=utf-8")
        except UnicodeDecodeError:
            continue
    return "Encoding error", 500


@app.route("/api/compare", methods=["POST"])
def api_compare():
    data     = request.get_json()
    old_data = _parse_keepa(KEEPA_EXPORTS_DIR / data["old_file"])
    new_data = _parse_keepa(KEEPA_EXPORTS_DIR / data["new_file"])

    changes = []
    for asin, nr in new_data.items():
        if asin not in old_data:
            continue
        or_         = old_data[asin]
        bb_delta    = round((nr["bb"] or 0) - (or_["bb"] or 0), 2)
        drops_delta = (nr["drops"] or 0) - (or_["drops"] or 0)
        bsr_delta   = (nr["bsr"]   or 0) - (or_["bsr"]   or 0)

        if abs(bb_delta) > 0.01 or drops_delta != 0 or abs(bsr_delta) > 50:
            changes.append(dict(
                asin=asin, title=nr["title"],
                old_bb=or_["bb"],     new_bb=nr["bb"],     bb_delta=bb_delta,
                old_drops=or_["drops"], new_drops=nr["drops"], drops_delta=drops_delta,
                old_bsr=or_["bsr"],   new_bsr=nr["bsr"],   bsr_delta=bsr_delta,
            ))

    changes.sort(key=lambda x: abs(x["bb_delta"]), reverse=True)
    return jsonify(changes=changes)


# ── Keepa CSV parser (comparison only) ────────────────────────────────────────

def _parse_keepa(path: Path) -> dict:
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = path.read_text(encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        return {}

    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return {}

    hdr = [h.strip() for h in rows[0]]

    def _col(*pats):
        for p in pats:
            for i, h in enumerate(hdr):
                if p.lower() in h.lower():
                    return i
        return -1

    i_asin  = _col("ASIN")
    i_title = _col("Titre", "Title")
    i_bb    = _col("Buy Box: Courant", "Buy Box: Current")
    i_drops = _col("Chutes au cours des 90", "Sales Rank: Drops", "Drops last 90")
    i_bsr   = _col("Classement des ventes: Courant", "Sales Rank: Current")

    if i_asin < 0:
        return {}

    def _num(s):
        try:
            return float(re.sub(r"[^\d.,]", "", s or "").replace(",", ".") or "0")
        except ValueError:
            return 0.0

    result = {}
    for row in rows[1:]:
        def g(i): return row[i].strip() if 0 <= i < len(row) else ""
        asin = g(i_asin)
        if not asin or len(asin) < 5:
            continue
        bb    = _num(g(i_bb))    if i_bb    >= 0 else 0.0
        drops = int(_num(g(i_drops))) if i_drops >= 0 else 0
        bsr   = int(_num(g(i_bsr)))   if i_bsr   >= 0 else 0
        result[asin] = dict(title=g(i_title) or asin,
                            bb=bb or None, drops=drops, bsr=bsr or None)
    return result


# ── HTML builder — injects new screens into the existing dashboard ─────────────

_OLD_KEEPA_CARD = """    <div class="upload-card">
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
    </div>"""

_NEW_KEEPA_CARD = """    <div class="upload-card">
      <div class="uc-title"><span class="ico">📊</span>Keepa Data</div>
      <div class="uc-desc">Choose how to load Keepa data for this analysis.</div>
      <div class="kmode-tabs">
        <button class="kmode-btn active" id="kmode-auto" onclick="setKeepaMode('auto')">🤖 Run Automation</button>
        <button class="kmode-btn" id="kmode-manual" onclick="setKeepaMode('manual')">📂 Upload CSV</button>
      </div>
      <div id="kpa-auto-section">
        <div class="uc-desc" style="margin-top:8px">
          Browser automation runs using your supplier file.<br>
          <strong>You'll be prompted to log in to Keepa once</strong> via the button that appears.
        </div>
        <div class="dz" id="dz-auto-ready" style="display:none;margin-top:12px">
          <div class="dz-ico">🤖</div>
          <div class="dz-txt">Ready — click Analyze to start</div>
          <div class="dz-hint">Supplier CSV loaded</div>
        </div>
      </div>
      <div id="kpa-manual-section" style="display:none">
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
    </div>"""

_NEW_CSS = """
/* ── Keepa mode tabs ──────────────────────────────── */
.kmode-tabs{display:flex;gap:8px;margin-bottom:14px;}
.kmode-btn{flex:1;padding:9px;border-radius:8px;border:1px solid var(--border);background:none;color:var(--muted);font-size:12px;font-weight:600;cursor:pointer;transition:all .15s;}
.kmode-btn:hover{border-color:var(--accent);color:var(--accent);}
.kmode-btn.active{border-color:var(--accent);background:rgba(108,99,255,.12);color:var(--accent);}
/* ── Keepa progress screen ────────────────────────── */
.kp-wrap{min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px 28px;}
.kp-card{background:var(--card);border:1px solid var(--border);border-radius:14px;width:100%;max-width:780px;margin-bottom:20px;overflow:hidden;}
.kp-log-title{font-family:monospace;font-size:9px;color:var(--b);letter-spacing:3px;text-transform:uppercase;padding:10px 16px;border-bottom:1px solid var(--border);}
.kp-log{height:280px;overflow-y:auto;padding:12px 16px;font-family:monospace;font-size:12px;color:var(--muted);line-height:1.8;}
.kp-log div{border-bottom:1px solid #ffffff04;padding:1px 0;}
.kp-login-prompt{background:rgba(0,217,255,.06);border:1px solid rgba(0,217,255,.3);border-radius:12px;padding:20px 28px;max-width:780px;width:100%;text-align:center;margin-bottom:20px;color:var(--text);font-size:14px;}
.kp-login-btn{margin-top:14px;padding:12px 32px;border-radius:10px;border:none;background:var(--green);color:#fff;font-size:14px;font-weight:700;cursor:pointer;transition:opacity .15s;}
.kp-login-btn:hover{opacity:.85;}
/* ── Comparison screen ────────────────────────────── */
.cmp-table{width:100%;border-collapse:collapse;font-size:12px;}
.cmp-table th{background:var(--card);color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.5px;padding:9px 12px;border-bottom:2px solid var(--border);white-space:nowrap;text-align:right;position:sticky;top:0;z-index:5;}
.cmp-table th:first-child{text-align:left;}
.cmp-table td{padding:9px 12px;border-bottom:1px solid var(--border);text-align:right;font-family:monospace;font-size:12px;}
.cmp-table td:first-child{text-align:left;font-family:inherit;font-weight:500;color:var(--text);max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.cmp-table tr:hover td{background:#ffffff04;}
.cmp-up{color:var(--green);font-weight:700;}
.cmp-dn{color:var(--red);font-weight:700;}
.cmp-same{color:var(--muted);}
.cmp-info-bar{display:flex;align-items:center;gap:12px;background:rgba(108,99,255,.06);border:1px solid rgba(108,99,255,.2);border-radius:10px;padding:12px 18px;margin-bottom:18px;font-size:12px;flex-wrap:wrap;}
.cmp-info-bar strong{color:var(--text);}
.cmp-info-bar span{color:var(--muted);}
"""

_NEW_SCREENS = """
<!-- ══ SCREEN 5: KEEPA PROGRESS ══ -->
<div id="s-keepa" class="screen">
<div class="kp-wrap">
  <div class="logo" style="margin-bottom:24px">
    <h1>Keepa <span>Automation</span></h1>
    <p>Browser is running — do not close it</p>
  </div>
  <div class="kp-login-prompt" id="kp-login-prompt" style="display:none">
    <div>🔐 Please log in to Keepa in the browser window, then click the button below.</div>
    <button class="kp-login-btn" onclick="confirmLogin()">✅ I've logged in — continue</button>
  </div>
  <div class="kp-card">
    <div class="kp-log-title">▸ Live Log</div>
    <div class="kp-log" id="kp-log"></div>
  </div>
  <div style="display:flex;align-items:center;gap:14px;justify-content:center">
    <div class="spinner" id="kp-spinner"></div>
    <div class="load-msg" id="kp-msg">Starting automation…</div>
  </div>
  <button class="btn-back" onclick="cancelKeepa()" style="margin-top:24px">← Cancel</button>
</div>
</div>

<!-- ══ SCREEN 6: KEEPA COMPARISON ══ -->
<div id="s-compare" class="screen">
<div class="map-wrap" style="max-width:1260px">
  <div class="map-header">
    <h2>📊 Keepa Export Comparison</h2>
    <p id="cmp-summary" style="color:var(--muted);margin-top:4px"></p>
  </div>
  <div class="cmp-info-bar" id="cmp-info-bar"></div>
  <div style="overflow-x:auto;margin-bottom:24px">
    <table class="cmp-table">
      <thead><tr>
        <th style="min-width:210px;text-align:left">Product</th>
        <th>Prev BB</th><th>New BB</th><th>Δ BB</th>
        <th>Prev Drops</th><th>New Drops</th><th>Δ Drops</th>
        <th>Prev BSR</th><th>New BSR</th><th>Δ BSR</th>
      </tr></thead>
      <tbody id="cmp-tbody"></tbody>
    </table>
  </div>
  <div class="map-actions">
    <button class="btn-back" onclick="usePrevExport()">⬅ Use Previous Export</button>
    <button class="btn-confirm" onclick="useNewExport()">Use New Export ➡</button>
  </div>
  <p style="text-align:center;color:var(--muted);font-size:11px;margin-top:10px">
    Previous = most recent prior export &nbsp;·&nbsp; New = just downloaded
  </p>
</div>
</div>
"""

_NEW_JS = r"""
// ════════════════════════════════════════════════════════════════
// KEEPA AUTOMATION INTEGRATION  (injected by app.py)
// ════════════════════════════════════════════════════════════════
let keepaMode = 'auto';
let currentJobId = null;
let _supFile = null;
let _newKeepaFilename = null;
let _prevKeepaFilename = null;
let _pollTimer = null;

// Capture the supplier File object alongside the existing readFile flow
const _orig_onFile = window.onFile;
window.onFile = function(inp, type) {
  if (type === 'sup' && inp.files[0]) _supFile = inp.files[0];
  _orig_onFile(inp, type);
};

// Override checkReady: Keepa not required when automation mode is active
window.checkReady = function() {
  const hasSupplier = !!supText;
  const hasKeepa    = keepaMode === 'manual' ? !!kpaText : true;
  document.getElementById('btn-go').classList.toggle('ready', hasSupplier && hasKeepa);
  const ar = document.getElementById('dz-auto-ready');
  if (ar) ar.style.display = hasSupplier && keepaMode === 'auto' ? '' : 'none';
};

function setKeepaMode(mode) {
  keepaMode = mode;
  document.getElementById('kmode-auto').classList.toggle('active', mode === 'auto');
  document.getElementById('kmode-manual').classList.toggle('active', mode === 'manual');
  document.getElementById('kpa-auto-section').style.display  = mode === 'auto'   ? '' : 'none';
  document.getElementById('kpa-manual-section').style.display = mode === 'manual' ? '' : 'none';
  checkReady();
}

// Analyze button now calls goMain() instead of goToMapping()
function goMain() {
  keepaMode === 'auto' ? startKeepaAutomation() : goToMapping();
}

async function startKeepaAutomation() {
  if (!_supFile) { alert('Please upload the supplier CSV first.'); return; }
  showScreen('keepa');
  document.getElementById('kp-log').innerHTML = '';
  document.getElementById('kp-login-prompt').style.display = 'none';
  document.getElementById('kp-spinner').style.display = '';
  document.getElementById('kp-msg').textContent = 'Starting automation…';

  const fd = new FormData();
  fd.append('csv', _supFile);
  try {
    const data = await (await fetch('/api/run-keepa', { method: 'POST', body: fd })).json();
    if (data.error) throw new Error(data.error);
    currentJobId = data.job_id;
    _schedulePoll();
  } catch (e) {
    alert('Failed to start: ' + e.message);
    showScreen('upload');
  }
}

function _schedulePoll() { _pollTimer = setTimeout(_poll, 1500); }

async function _poll() {
  if (!currentJobId) return;
  try {
    const d = await (await fetch('/api/keepa-status/' + currentJobId)).json();

    // Update live log (hide internal markers from user)
    const logEl = document.getElementById('kp-log');
    logEl.innerHTML = d.logs
      .filter(l => !l.startsWith('KEEPA_BOT::'))
      .map(l => '<div>' + _esc(l) + '</div>').join('');
    logEl.scrollTop = logEl.scrollHeight;

    // Show login button only while waiting and before confirmation
    const needsLogin = d.logs.some(l => l === 'KEEPA_BOT::WAITING_FOR_LOGIN');
    const loginDone  = d.logs.some(l => l.includes('Login confirmed') || l.includes('Already logged in'));
    document.getElementById('kp-login-prompt').style.display =
      needsLogin && !loginDone ? '' : 'none';

    if (d.status === 'complete') {
      document.getElementById('kp-spinner').style.display = 'none';
      document.getElementById('kp-msg').textContent = 'Download complete!';
      _newKeepaFilename = d.result_file;
      await _afterKeepaComplete(d.result_file);
    } else if (d.status === 'error') {
      document.getElementById('kp-spinner').style.display = 'none';
      document.getElementById('kp-msg').textContent = 'Error — see log above';
      alert('Keepa automation failed.\n' + (d.error || '') +
            '\n\nSwitch to manual CSV upload to continue.');
      setKeepaMode('manual');
      showScreen('upload');
    } else {
      _schedulePoll();
    }
  } catch (_) { _schedulePoll(); }
}

async function confirmLogin() {
  document.getElementById('kp-login-prompt').style.display = 'none';
  document.getElementById('kp-msg').textContent = 'Logged in — continuing…';
  await fetch('/api/confirm-login/' + currentJobId, { method: 'POST' });
}

function cancelKeepa() {
  clearTimeout(_pollTimer);
  currentJobId = null;
  showScreen('upload');
}

async function _afterKeepaComplete(newFilename) {
  // Load the new Keepa CSV into browser memory for analysis
  kpaText = await (await fetch('/api/read-keepa/' + encodeURIComponent(newFilename))).text();

  // Check for previous exports
  const exports = await (await fetch('/api/keepa-exports')).json();
  const prev    = exports.filter(e => e.name !== newFilename);

  if (!prev.length) { goToMapping(); return; }

  // Compare against the most recent previous export
  _prevKeepaFilename = prev[0].name;
  const cmp = await (await fetch('/api/compare', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ old_file: _prevKeepaFilename, new_file: newFilename }),
  })).json();

  if (!cmp.changes || !cmp.changes.length) { goToMapping(); return; }

  _renderComparison(cmp.changes, newFilename, _prevKeepaFilename);
  showScreen('compare');
}

function _renderComparison(changes, newFile, prevFile) {
  document.getElementById('cmp-summary').textContent =
    changes.length + ' product' + (changes.length !== 1 ? 's' : '') + ' changed';
  document.getElementById('cmp-info-bar').innerHTML =
    '<span>New export:</span> <strong>' + _esc(newFile) + '</strong>' +
    ' &nbsp;·&nbsp; <span>Compared against:</span> <strong>' + _esc(prevFile) + '</strong>';

  const fBB = v => v != null ? '€' + v.toFixed(2) : '—';
  const fN  = v => v != null ? Number(v).toLocaleString() : '—';
  // BB delta: neutral color (price direction isn't inherently good/bad for reseller)
  // Drops delta: positive = more sales = green
  // BSR delta: negative = rank improved = green
  const cls = (v, posGood) =>
    !v && v !== 0 ? 'cmp-same' :
    v === 0       ? 'cmp-same' :
    posGood       ? (v > 0 ? 'cmp-up' : 'cmp-dn') :
                    (v < 0 ? 'cmp-up' : 'cmp-dn');

  document.getElementById('cmp-tbody').innerHTML = changes.map(c => `
    <tr>
      <td title="${_esc(c.title)}">${_esc(c.title.slice(0, 48))}${c.title.length > 48 ? '…' : ''}</td>
      <td>${fBB(c.old_bb)}</td>
      <td>${fBB(c.new_bb)}</td>
      <td><span class="${cls(c.bb_delta, null)}">${c.bb_delta > 0 ? '+' : ''}${c.bb_delta != null ? c.bb_delta.toFixed(2) : '—'}</span></td>
      <td>${fN(c.old_drops)}</td>
      <td>${fN(c.new_drops)}</td>
      <td><span class="${cls(c.drops_delta, true)}">${c.drops_delta > 0 ? '+' : ''}${c.drops_delta}</span></td>
      <td>${fN(c.old_bsr)}</td>
      <td>${fN(c.new_bsr)}</td>
      <td><span class="${cls(c.bsr_delta, false)}">${c.bsr_delta > 0 ? '+' : ''}${fN(c.bsr_delta)}</span></td>
    </tr>`).join('');
}

async function useNewExport() {
  // kpaText is already set from the new file — go to supplier column mapping
  goToMapping();
}

async function usePrevExport() {
  kpaText = await (await fetch('/api/read-keepa/' + encodeURIComponent(_prevKeepaFilename))).text();
  goToMapping();
}

function _esc(s) {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
"""


def _build_html() -> str:
    src        = (SCRIPT_DIR / "generate_dashboard_v2.1.py").read_text(encoding="utf-8")
    html_start = src.index('HTML = r"""') + len('HTML = r"""')
    html_end   = src.index('\n"""\n\ndef main():')
    html       = src[html_start:html_end]

    html = html.replace("</style>", _NEW_CSS + "\n</style>", 1)
    html = html.replace(_OLD_KEEPA_CARD, _NEW_KEEPA_CARD, 1)
    html = html.replace('onclick="goToMapping()"', 'onclick="goMain()"', 1)
    html = html.replace(
        "<!-- ══ SCREEN 2: COLUMN MAPPING ══ -->",
        _NEW_SCREENS + "\n<!-- ══ SCREEN 2: COLUMN MAPPING ══ -->",
        1,
    )
    html = html.replace("</script>", _NEW_JS + "\n</script>", 1)
    return html


# Build and cache once at startup
_HTML = _build_html()


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import threading as _th
    import webbrowser

    _th.Timer(1.2, lambda: webbrowser.open("http://localhost:5001")).start()
    print("=" * 60)
    print("  So Vizion FBA Optimizer — http://localhost:5001")
    print(f"  Keepa exports → {KEEPA_EXPORTS_DIR}")
    print("=" * 60)
    app.run(port=5001, debug=False, use_reloader=False)
