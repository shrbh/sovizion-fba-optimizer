#!/usr/bin/env python3
"""
Test: Filter-change correctness in generate_dashboard_v2.1.py
Reproduces the bug where results become wrong after changing an initial filter set.

All logic mirrors the JavaScript in generate_dashboard_v2.1.py exactly.
"""

PASS = "\033[32m✓ PASS\033[0m"
FAIL = "\033[31m✗ FAIL\033[0m"
errors = 0


def check(desc, got, want):
    global errors
    ok = got == want
    tag = PASS if ok else FAIL
    if not ok:
        errors += 1
        print(f"  {tag}  {desc}\n         got={got!r}  want={want!r}")
    else:
        print(f"  {tag}  {desc}")


# ── mirror JS helpers ──────────────────────────────────────────────────────────

def vat_amount(bb, fVAT):
    """JS: vatAmount(bb, fVAT) → bb * fVAT / (100 + fVAT), inclusive-price formula"""
    if fVAT == 0:
        return 0.0
    return round(bb * fVAT / (100 + fVAT) * 100) / 100


def ep(r, fCst):
    """JS: ep(r) = round((r.profit - fCst) * 100) / 100"""
    return round((r["profit"] - fCst) * 100) / 100


def er(r, fCst):
    """JS: er(r) = cost>0 ? round(ep(r)/cost*1000)/10 : 0  where cost = pa_net + fCst"""
    cost = r["pa_net"] + fCst
    if cost > 0:
        return round(ep(r, fCst) / cost * 1000) / 10
    return 0.0


def rebuild_profit(r, fVAT):
    """JS rebuildProducts(): recomputes r.vat, r.profit, r.roi from current fVAT."""
    vat = vat_amount(r["bb"], fVAT)
    r["vat"] = vat
    r["profit"] = round((r["bb"] - r["ppf"] - r["ref_fee"] - vat - r["pa_net"]) * 100) / 100
    r["roi"] = round(r["profit"] / r["pa_net"] * 1000) / 10 if r["pa_net"] > 0 else 0.0


def get_vis_buggy(products, fRoi, fBB, fDrp, fBsrMax, fWinMax, fAmzInBB, fCst):
    """
    Mirrors the CURRENT (buggy) getVis() — generate_dashboard_v2.1.py line 1444.
    When fRoi==0 it compares r.roi (base ROI) instead of er(r) (cost-adjusted ROI).
    """
    result = []
    for r in products:
        # BUG: inconsistent ROI check — switches from er(r) to r.roi at fRoi=0
        if fRoi > 0:
            if er(r, fCst) < fRoi:
                continue
        else:
            if r["roi"] < 0:        # ← uses r.roi, ignores fCst entirely
                continue
        if fBB > 0 and r["amazon_pct"] > fBB:
            continue
        if r["bsr_drops"] < fDrp:
            continue
        if fBsrMax > 0 and (not r.get("bsr_cur") or r["bsr_cur"] > fBsrMax):
            continue
        if fWinMax > 0 and r["bb_winners"] > fWinMax:
            continue
        if fAmzInBB == "no" and r["amz_is_bb"]:
            continue
        if fAmzInBB == "yes" and not r["amz_is_bb"]:
            continue
        result.append(r)
    return result


def get_vis_fixed(products, fRoi, fBB, fDrp, fBsrMax, fWinMax, fAmzInBB, fCst):
    """
    Mirrors the FIXED getVis(): always use er(r) consistently, matching index.html.
    Fix: replace the ternary with simply  if(er(r) < fRoi) return false
    """
    result = []
    for r in products:
        if er(r, fCst) < fRoi:      # ← always uses er(r), consistent
            continue
        if fBB > 0 and r["amazon_pct"] > fBB:
            continue
        if r["bsr_drops"] < fDrp:
            continue
        if fBsrMax > 0 and (not r.get("bsr_cur") or r["bsr_cur"] > fBsrMax):
            continue
        if fWinMax > 0 and r["bb_winners"] > fWinMax:
            continue
        if fAmzInBB == "no" and r["amz_is_bb"]:
            continue
        if fAmzInBB == "yes" and not r["amz_is_bb"]:
            continue
        result.append(r)
    return result


# ── test dataset ───────────────────────────────────────────────────────────────

def make_product(name, pa_net, bb, ppf, ref_fee, fVAT=20,
                 bsr_drops=5, amazon_pct=0, bsr_cur=10000,
                 bb_winners=2, amz_is_bb=False):
    """Build a product dict identical to what rebuildProducts() produces."""
    vat = vat_amount(bb, fVAT)
    profit = round((bb - ppf - ref_fee - vat - pa_net) * 100) / 100
    roi = round(profit / pa_net * 1000) / 10 if pa_net > 0 else 0.0
    return {
        "name": name, "pa_net": pa_net, "bb": bb, "ppf": ppf,
        "ref_fee": ref_fee, "vat": vat, "profit": profit, "roi": roi,
        "bsr_drops": bsr_drops, "amazon_pct": amazon_pct,
        "bsr_cur": bsr_cur, "bb_winners": bb_winners, "amz_is_bb": amz_is_bb,
    }


# Products are designed to expose the specific bug scenarios
PRODUCTS = [
    # A: HIGH margin — er(fCst=3) stays well above 20% even with extra cost
    #    bb=35, ppf=2, ref_fee=4.5, vat20=5.83, pa_net=10 → profit=12.67, roi=127%
    #    er(3) = (12.67-3)/(10+3) = 74.4%
    make_product("Product A", pa_net=10.0, bb=35.0, ppf=2.0, ref_fee=4.5,
                 bsr_drops=5, amazon_pct=0, amz_is_bb=False),

    # B: THIN margin — r.roi is positive but er(fCst=3) is NEGATIVE
    #    This is the "ghost product" that the bug incorrectly shows at fRoi=0
    #    bb=12, ppf=1.5, ref_fee=1.8, vat20=2.0, pa_net=5 → profit=1.7, roi=34%
    #    er(3) = (1.7-3)/(5+3) = -16.25%
    make_product("Product B", pa_net=5.0, bb=12.0, ppf=1.5, ref_fee=1.8,
                 bsr_drops=3, amazon_pct=5, amz_is_bb=False),

    # C: NEGATIVE base ROI — must always be filtered at fRoi=0 by both buggy and fixed
    #    bb=8, ppf=2, ref_fee=1.2, vat20=1.33, pa_net=6 → profit=-2.53, roi=-42%
    make_product("Product C", pa_net=6.0, bb=8.0, ppf=2.0, ref_fee=1.2,
                 bsr_drops=4, amazon_pct=10, amz_is_bb=False),

    # D: Amazon holds Buy Box — filtered when fAmzInBB='no'
    #    Good ROI: profit≈9, er(3)>50%
    make_product("Product D", pa_net=10.0, bb=35.0, ppf=2.0, ref_fee=4.5,
                 bsr_drops=6, amazon_pct=100, amz_is_bb=True),

    # E: high BSR (slow mover) — filtered by fBsrMax
    make_product("Product E", pa_net=10.0, bb=35.0, ppf=2.0, ref_fee=4.5,
                 bsr_drops=7, amazon_pct=0, bsr_cur=400000, amz_is_bb=False),
]

# Print reference table so test output is self-documenting
print("\n══ Product reference table (fVAT=20%) ══")
print(f"  {'Name':<12} {'pa_net':>7} {'profit':>8} {'r.roi':>8} {'er(fCst=0)':>12} {'er(fCst=3)':>12} {'amz_is_bb':>10}")
for r in PRODUCTS:
    print(f"  {r['name']:<12} {r['pa_net']:>7.2f} {r['profit']:>8.2f} "
          f"{r['roi']:>8.1f}% {er(r,0.0):>11.1f}% {er(r,3.0):>11.1f}% {str(r['amz_is_bb']):>10}")

# ── SECTION 1: Baseline — no extra cost, no bug ───────────────────────────────
print("\n══ S1: ROI filter — fCst=0.00 (baseline, no bug) ══")
fCst = 0.0

r0 = get_vis_buggy(PRODUCTS, fRoi=0, fBB=0, fDrp=0, fBsrMax=0, fWinMax=0, fAmzInBB="any", fCst=fCst)
names0 = [r["name"] for r in r0]
check("fRoi=0 fCst=0: negative-ROI product C excluded", "Product C" not in names0, True)
check("fRoi=0 fCst=0: products A,B,D,E shown",
      all(n in names0 for n in ["Product A", "Product B", "Product D", "Product E"]), True)

r20 = get_vis_buggy(PRODUCTS, fRoi=20, fBB=0, fDrp=0, fBsrMax=0, fWinMax=0, fAmzInBB="any", fCst=fCst)
names20 = [r["name"] for r in r20]
check("fRoi=20 fCst=0: high-ROI products A,B,D,E kept (all roi>20%)",
      sorted(names20), sorted(["Product A", "Product B", "Product D", "Product E"]))
check("fRoi=20 fCst=0: zero/neg ROI excluded", "Product C" not in names20, True)

# reset from 20 to 0 — should match fresh fRoi=0
r_reset = get_vis_buggy(PRODUCTS, fRoi=0, fBB=0, fDrp=0, fBsrMax=0, fWinMax=0, fAmzInBB="any", fCst=fCst)
check("fRoi=0 after reset: same as fresh fRoi=0",
      sorted(r["name"] for r in r_reset) == sorted(names0), True)

# ── SECTION 2: Core bug — extra cost makes er(r) negative while r.roi stays + ─
print("\n══ S2: ROI filter — fCst=3.00 (core bug in line 1444) ══")
fCst = 3.0

b_er_val = er(PRODUCTS[1], fCst)
a_er_val = er(PRODUCTS[0], fCst)
check(f"Product A sanity: er(fCst=3)={a_er_val:.1f}% is positive", a_er_val > 0, True)
check(f"Product B sanity: er(fCst=3)={b_er_val:.1f}% is NEGATIVE while r.roi={PRODUCTS[1]['roi']:.1f}% > 0",
      b_er_val < 0 and PRODUCTS[1]["roi"] > 0, True)

buggy0 = [r["name"] for r in get_vis_buggy(PRODUCTS, fRoi=0, fBB=0, fDrp=0, fBsrMax=0, fWinMax=0, fAmzInBB="any", fCst=fCst)]
fixed0 = [r["name"] for r in get_vis_fixed(PRODUCTS, fRoi=0, fBB=0, fDrp=0, fBsrMax=0, fWinMax=0, fAmzInBB="any", fCst=fCst)]

check("BUG — fRoi=0 fCst=3: buggy code WRONGLY includes Product B (er<0 but roi>0)",
      "Product B" in buggy0, True)
check("FIX — fRoi=0 fCst=3: fixed code correctly EXCLUDES Product B (er<0)",
      "Product B" not in fixed0, True)

check("BUG — fRoi=0 fCst=3: buggy shows extra products vs fixed",
      set(buggy0) != set(fixed0), True)
check("FIX — fRoi=0 fCst=3: fixed code only shows products with er(r)>=0",
      all(er(r, fCst) >= 0 for r in get_vis_fixed(PRODUCTS, fRoi=0, fBB=0, fDrp=0, fBsrMax=0, fWinMax=0, fAmzInBB="any", fCst=fCst)),
      True)

# ── SECTION 3: The exact user scenario — set filters, then change them ────────
print("\n══ S3: User scenario — set fRoi=20 then reset to fRoi=0 ══")
fCst = 3.0

# Step 1: user sets fRoi=20 with fCst=3
r_step1 = get_vis_fixed(PRODUCTS, fRoi=20, fBB=0, fDrp=0, fBsrMax=0, fWinMax=0, fAmzInBB="any", fCst=fCst)
names_step1 = sorted(r["name"] for r in r_step1)
# A, D, E all have er(3)=74.4% >= 20%; B (er=-16%) and C (er=-61%) excluded
check("Step 1 fRoi=20 fCst=3: A, D, E (er=74%) pass; B (er=-16%) and C (er=-61%) excluded",
      names_step1, sorted(["Product A", "Product D", "Product E"]))

# Step 2: user resets fRoi to 0 — expects to see all er>=0 products
buggy_step2 = sorted(r["name"] for r in get_vis_buggy(PRODUCTS, fRoi=0, fBB=0, fDrp=0, fBsrMax=0, fWinMax=0, fAmzInBB="any", fCst=fCst))
fixed_step2 = sorted(r["name"] for r in get_vis_fixed(PRODUCTS, fRoi=0, fBB=0, fDrp=0, fBsrMax=0, fWinMax=0, fAmzInBB="any", fCst=fCst))

# Correct result: A (er=74%), D (er≈74%, amz_is_bb but no amzbb filter), E (er≈74%, high BSR but no bsrmax filter)
# B has er=-16%, C has er=-61% → should be excluded
check("BUG — after reset to fRoi=0, buggy code incorrectly shows Product B (er<0)",
      "Product B" in buggy_step2, True)
check("FIX — after reset to fRoi=0, fixed code excludes Product B (er<0)",
      "Product B" not in fixed_step2, True)
check("FIX — after reset to fRoi=0, fixed code still shows Product A (er>0)",
      "Product A" in fixed_step2, True)

# ── SECTION 4: Changing fCst — extra cost reset should not break results ──────
print("\n══ S4: Extra-cost slider change 3.00 → 0.00 ══")

# With fCst=3: B should be hidden (er=-16%)
with_cost = [r["name"] for r in get_vis_fixed(PRODUCTS, fRoi=0, fBB=0, fDrp=0, fBsrMax=0, fWinMax=0, fAmzInBB="any", fCst=3.0)]
check("fCst=3: Product B excluded (er=-16%)",   "Product B" not in with_cost, True)
check("fCst=3: Product A included (er=74%)",    "Product A" in with_cost,     True)

# Reset fCst=0: B should reappear (roi=34% > 0)
no_cost = [r["name"] for r in get_vis_fixed(PRODUCTS, fRoi=0, fBB=0, fDrp=0, fBsrMax=0, fWinMax=0, fAmzInBB="any", fCst=0.0)]
check("fCst=0 after reset: Product B reappears (roi=34% now er=34%)",
      "Product B" in no_cost, True)
check("fCst=0 after reset: Product C (base roi=-42%) still excluded",
      "Product C" not in no_cost, True)

# ── SECTION 5: Monotonicity — relaxing fRoi should never LOSE products ────────
print("\n══ S5: Monotonicity — relaxing fRoi can only ADD products, never remove ══")
fCst = 3.0

prev_names_fixed = None
prev_names_buggy = None
non_monotone_buggy = False

for fRoi_val in [50, 30, 20, 10, 5, 1, 0]:
    vf = set(r["name"] for r in get_vis_fixed(PRODUCTS, fRoi=fRoi_val, fBB=0, fDrp=0, fBsrMax=0, fWinMax=0, fAmzInBB="any", fCst=fCst))
    vb = set(r["name"] for r in get_vis_buggy(PRODUCTS, fRoi=fRoi_val, fBB=0, fDrp=0, fBsrMax=0, fWinMax=0, fAmzInBB="any", fCst=fCst))
    if prev_names_fixed is not None:
        check(f"FIXED fRoi={fRoi_val}: visible ⊇ visible@fRoi={prev_fRoi} (monotone)",
              prev_names_fixed.issubset(vf), True)
    if prev_names_buggy is not None and not prev_names_buggy.issubset(vb):
        non_monotone_buggy = True
    prev_names_fixed = vf
    prev_names_buggy = vb
    prev_fRoi = fRoi_val

check("BUG — buggy code is monotone only by accident; it gains WRONG products at fRoi=0",
      "Product B" in prev_names_buggy, True)  # B is wrongly in result at fRoi=0
check("FIX — fixed code does NOT include Product B at fRoi=0 (er<0)",
      "Product B" not in prev_names_fixed, True)

# ── SECTION 6: TVA change then filter change ──────────────────────────────────
print("\n══ S6: TVA change followed by BSR drops filter ══")

tva_prod = make_product("TVA-Test", pa_net=10.0, bb=25.0, ppf=3.0, ref_fee=3.5,
                        fVAT=20, bsr_drops=2, amazon_pct=0, amz_is_bb=False)
roi_20 = tva_prod["roi"]
rebuild_profit(tva_prod, fVAT=21)
roi_21 = tva_prod["roi"]
check("TVA 21% reduces ROI vs 20%", roi_21 < roi_20, True)

r = get_vis_fixed([tva_prod], fRoi=0, fBB=0, fDrp=3, fBsrMax=0, fWinMax=0, fAmzInBB="any", fCst=0)
check("After TVA change: fDrp=3 excludes product with 2 drops", len(r), 0)
r = get_vis_fixed([tva_prod], fRoi=0, fBB=0, fDrp=2, fBsrMax=0, fWinMax=0, fAmzInBB="any", fCst=0)
check("After TVA change: fDrp=2 includes product with 2 drops", len(r), 1)

# ── SECTION 7: Amazon BB toggle round-trip ────────────────────────────────────
print("\n══ S7: Amazon BB toggle — 'any' → 'no' → 'yes' → 'any' ══")

bb_prods = [
    make_product("No-Amz", pa_net=8, bb=20, ppf=2.5, ref_fee=2.8, amz_is_bb=False, bsr_drops=5),
    make_product("Amz-BB", pa_net=8, bb=20, ppf=2.5, ref_fee=2.8, amz_is_bb=True,  bsr_drops=5),
]
r_any  = get_vis_fixed(bb_prods, fRoi=0, fBB=0, fDrp=0, fBsrMax=0, fWinMax=0, fAmzInBB="any", fCst=0)
r_no   = get_vis_fixed(bb_prods, fRoi=0, fBB=0, fDrp=0, fBsrMax=0, fWinMax=0, fAmzInBB="no",  fCst=0)
r_yes  = get_vis_fixed(bb_prods, fRoi=0, fBB=0, fDrp=0, fBsrMax=0, fWinMax=0, fAmzInBB="yes", fCst=0)
r_back = get_vis_fixed(bb_prods, fRoi=0, fBB=0, fDrp=0, fBsrMax=0, fWinMax=0, fAmzInBB="any", fCst=0)
check("amzbb='any': both products shown",      len(r_any),  2)
check("amzbb='no': only non-Amazon product",   [r["name"] for r in r_no],  ["No-Amz"])
check("amzbb='yes': only Amazon product",      [r["name"] for r in r_yes], ["Amz-BB"])
check("amzbb back to 'any': both shown again", len(r_back), 2)

# ── SECTION 8: Multi-filter combination then partial reset ────────────────────
print("\n══ S8: Multi-filter combination → partial reset ══")
fCst = 3.0

# All filters on: fRoi=20, fAmzInBB='no', fBsrMax=50000
r_all = get_vis_fixed(PRODUCTS, fRoi=20, fBB=0, fDrp=0, fBsrMax=50000, fWinMax=0, fAmzInBB="no", fCst=fCst)
names_all = [r["name"] for r in r_all]
check("All filters: Product D excluded (amz_is_bb=True)", "Product D" not in names_all, True)
check("All filters: Product E excluded (bsr_cur=400000 > 50000)", "Product E" not in names_all, True)
check("All filters: only Product A (er=74%>20, not amz, bsr<50k) passes", names_all, ["Product A"])

# Relax amzbb to 'any' — D should appear (er=74%, bsr<50k, no bsr_drops filter)
r_no_amzbb = get_vis_fixed(PRODUCTS, fRoi=20, fBB=0, fDrp=0, fBsrMax=50000, fWinMax=0, fAmzInBB="any", fCst=fCst)
names_no_amzbb = sorted(r["name"] for r in r_no_amzbb)
check("Relax amzbb='any': Product D appears (was blocked by amzbb='no')",
      "Product D" in names_no_amzbb, True)
check("Relax amzbb='any': Product E still excluded (bsr>50k)",
      "Product E" not in names_no_amzbb, True)
check("Relax amzbb='any': Product B still excluded (er<0 < fRoi=20)",
      "Product B" not in names_no_amzbb, True)

# ── Summary ───────────────────────────────────────────────────────────────────
print()
if errors == 0:
    print("\033[32m══ ALL TESTS PASSED ✓ ══\033[0m")
else:
    print(f"\033[31m══ {errors} TEST(S) FAILED — see details above ══\033[0m")
    raise SystemExit(1)
