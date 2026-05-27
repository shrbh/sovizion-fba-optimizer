#!/usr/bin/env python3
"""
Test: 🛒 Amazon Buy Box % Maximum filter
Mirrors the JavaScript logic from generate_dashboard_v2.1.py exactly.

JS source (line 1444-1445):
  if(fBB>0 && r.amazon_pct > fBB) return false;
JS source (line 1303-1305):
  else if(t==='bb'){fBB=v; document.getElementById('v-bb').textContent =
    v===0 ? 'No maximum — showing all' : `Amazon BB ≤ ${v}%`;}
"""

PASS = "\033[32m✓ PASS\033[0m"
FAIL = "\033[31m✗ FAIL\033[0m"
errors = 0


def label(fBB):
    """Mirrors the onSl display label for 'bb'."""
    return "No maximum — showing all" if fBB == 0 else f"Amazon BB ≤ {fBB}%"


def passes_bb_filter(amazon_pct, fBB):
    """
    Mirrors the JS condition in getVis():
      if(fBB>0 && r.amazon_pct > fBB) return false;
    Returns True if the product is kept (passes the filter).
    """
    if fBB > 0 and amazon_pct > fBB:
        return False
    return True


def check(desc, got, want):
    global errors
    status = PASS if got == want else FAIL
    if got != want:
        errors += 1
        print(f"  {status}  {desc}\n         got={got!r}  want={want!r}")
    else:
        print(f"  {status}  {desc}")


print("\n══ Filter label tests ══")
check("fBB=0  → 'No maximum — showing all'",
      label(0), "No maximum — showing all")
check("fBB=30 → 'Amazon BB ≤ 30%'", label(30), "Amazon BB ≤ 30%")
check("fBB=100 → 'Amazon BB ≤ 100%'", label(100), "Amazon BB ≤ 100%")

print("\n══ Filter OFF (fBB=0) — slider at minimum ══")
for pct in [0, 10, 50, 75, 99, 100]:
    check(f"fBB=0, amazon_pct={pct}% → kept (no filter)",
          passes_bb_filter(pct, 0), True)

print("\n══ Filter ON: fBB=30% ══")
cases_30 = [
    (0,   True,  "0% ≤ 30 → kept"),
    (15,  True,  "15% ≤ 30 → kept"),
    (30,  True,  "30% = 30 → kept (inclusive boundary)"),
    (31,  False, "31% > 30 → excluded"),
    (50,  False, "50% > 30 → excluded"),
    (100, False, "100% > 30 → excluded"),
]
for pct, want, desc in cases_30:
    check(f"fBB=30, amazon_pct={pct}% — {desc}",
          passes_bb_filter(pct, 30), want)

print("\n══ Filter ON: fBB=100% (widest active setting) ══")
for pct in [0, 50, 99, 100]:
    check(f"fBB=100, amazon_pct={pct}% → kept (100% lets everything through)",
          passes_bb_filter(pct, 100), True)

print("\n══ Filter ON: fBB=1% (strictest non-zero setting) ══")
check("fBB=1, amazon_pct=0% → kept", passes_bb_filter(0, 1), True)
check("fBB=1, amazon_pct=1% → kept (boundary)", passes_bb_filter(1, 1), True)
check("fBB=1, amazon_pct=2% → excluded", passes_bb_filter(2, 1), False)

print("\n══ Reset default ══")
check("rst('bb') sets fBB=0 → label is 'No maximum — showing all'",
      label(0), "No maximum — showing all")

print("\n══ Integration: full product list simulation ══")
products = [
    {"name": "Product A", "amazon_pct": 0},
    {"name": "Product B", "amazon_pct": 15},
    {"name": "Product C", "amazon_pct": 30},
    {"name": "Product D", "amazon_pct": 45},
    {"name": "Product E", "amazon_pct": 80},
    {"name": "Product F", "amazon_pct": 100},
]

def get_vis(fBB):
    return [p for p in products if passes_bb_filter(p["amazon_pct"], fBB)]

# fBB=0: all 6 products visible
result = get_vis(0)
check("fBB=0: all 6 products shown", len(result), 6)

# fBB=30: products with amazon_pct ≤ 30 → A(0), B(15), C(30)
result = get_vis(30)
check("fBB=30: 3 products shown (amazon_pct ≤ 30)", len(result), 3)
check("fBB=30: correct products kept",
      [p["name"] for p in result], ["Product A", "Product B", "Product C"])

# fBB=15: A(0), B(15)
result = get_vis(15)
check("fBB=15: 2 products shown", len(result), 2)

# fBB=1: only A(0)
result = get_vis(1)
check("fBB=1: 1 product shown (amazon_pct ≤ 1)", len(result), 1)

# fBB=100: all 6 shown
result = get_vis(100)
check("fBB=100: all 6 products shown", len(result), 6)

print()
if errors == 0:
    print("\033[32m══ ALL TESTS PASSED ✓ ══\033[0m")
else:
    print(f"\033[31m══ {errors} TEST(S) FAILED ══\033[0m")
    raise SystemExit(1)
