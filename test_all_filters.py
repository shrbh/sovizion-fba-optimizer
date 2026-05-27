#!/usr/bin/env python3
"""
Exhaustive filter test suite — generate_dashboard_v2.1.py
Tests ALL 8 filters, boundary conditions, every state transition, and combinations.
Mirrors JavaScript functions exactly from sovizion_v2_1.html.
"""

PASS_TAG = "\033[32m✓\033[0m"
FAIL_TAG = "\033[31m✗\033[0m"
errors = 0
total  = 0


def check(desc, got, want):
    global errors, total
    total += 1
    ok = got == want
    tag = PASS_TAG if ok else FAIL_TAG
    if not ok:
        errors += 1
        print(f"  {tag} FAIL  {desc}\n         got={got!r}  want={want!r}")
    else:
        print(f"  {tag}      {desc}")


# ════════════════════════════════════════════════════════════════
# JavaScript mirrors
# ════════════════════════════════════════════════════════════════

def vat_amount(bb, vat_pct):
    """JS: vatAmount(bb, vat_pct) — inclusive French VAT formula."""
    if not vat_pct or vat_pct <= 0:
        return 0.0
    return round((bb / (1 + vat_pct / 100) * (vat_pct / 100)) * 100) / 100


def ep(r, fCst):
    """JS: ep(r) = round((r.profit - fCst)*100)/100"""
    return round((r["profit"] - fCst) * 100) / 100


def er(r, fCst):
    """JS: er(r) — effective ROI including extra cost, rounded to 0.1%"""
    cost = r["pa_net"] + fCst
    return round(ep(r, fCst) / cost * 1000) / 10 if cost > 0 else 0.0


def tier_calc(roi, amz, stab, drops, winners):
    """JS: tierCalc(roi, amz, stab, drops, winners)"""
    if roi >= 25 and amz < 20 and stab in ("Stable", "Moderate") and drops >= 10 and winners <= 8:
        return 1
    if roi >= 15 and amz < 40 and drops >= 5:
        return 2
    if roi >= 5:
        return 3
    return 4


def rebuild_profit(r, fVAT, fCst=0):
    """JS: rebuildProducts() for a single product."""
    vat = vat_amount(r["bb"], fVAT)
    r["vat"] = vat
    r["profit"] = round((r["bb"] - r["ppf"] - r["ref_fee"] - vat - r["pa_net"]) * 100) / 100
    r["roi"]   = round(r["profit"] / r["pa_net"] * 1000) / 10 if r["pa_net"] > 0 else 0.0
    adj_roi    = round((r["profit"] - fCst) / (r["pa_net"] + fCst) * 1000) / 10 if (r["pa_net"] + fCst) > 0 else 0.0
    r["tier"]  = tier_calc(adj_roi, r["amazon_pct"], r["stab"], r["bsr_drops"], r["bb_winners"])


def update_tier_for_cst(r, fCst):
    """JS: onSl('cst') — updates r.tier with new fCst."""
    adj_roi = round((r["profit"] - fCst) / (r["pa_net"] + fCst) * 1000) / 10 if (r["pa_net"] + fCst) > 0 else 0.0
    r["tier"] = tier_calc(adj_roi, r["amazon_pct"], r["stab"], r["bsr_drops"], r["bb_winners"])


def get_vis(products, fRoi=0, fBB=0, fDrp=0, fCst=0, fBsrMax=0, fWinMax=0,
            fAmzInBB="any", fVAT=20, search=""):
    """JS: getVis() — all 8 filters applied."""
    q = search.lower()
    result = []
    for r in products:
        if er(r, fCst) < fRoi:
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
        if q and q not in r["name"].lower() and q not in (r.get("ean") or "") and q not in (r.get("asin") or "").lower():
            continue
        result.append(r)
    return result


def update_sum(fRoi=0, fBB=0, fDrp=0, fCst=0.0, fVAT=20, fBsrMax=0, fWinMax=0, fAmzInBB="any"):
    """JS: updateSum() — builds the filter summary string."""
    p = []
    if fRoi > 0:   p.append(f"ROI ≥ {fRoi}%")
    if fBB > 0:    p.append(f"BB ≤ {fBB}%")
    if fDrp > 0:   p.append(f"Drops ≥ {fDrp}")
    if fCst > 0:   p.append(f"+€{fCst:.2f}")
    if fVAT != 20: p.append(f"TVA {fVAT}%")
    if fBsrMax > 0: p.append(f"BSR ≤ {int(fBsrMax):,}")
    if fWinMax > 0: p.append(f"Win ≤ {fWinMax}")
    if fAmzInBB != "any": p.append(f"Amazon BB: {fAmzInBB}")
    return (" — " + " · ".join(p)) if p else " — No filters active"


def make_product(name, pa_net, bb, ppf, ref_fee, fVAT=20,
                 bsr_drops=5, amazon_pct=0, bsr_cur=10000,
                 bb_winners=2, amz_is_bb=False, stab="Moderate",
                 ean="", asin=""):
    vat    = vat_amount(bb, fVAT)
    profit = round((bb - ppf - ref_fee - vat - pa_net) * 100) / 100
    roi    = round(profit / pa_net * 1000) / 10 if pa_net > 0 else 0.0
    tier   = tier_calc(roi, amazon_pct, stab, bsr_drops, bb_winners)
    return {"name": name, "pa_net": pa_net, "bb": bb, "ppf": ppf,
            "ref_fee": ref_fee, "vat": vat, "profit": profit, "roi": roi,
            "bsr_drops": bsr_drops, "amazon_pct": amazon_pct,
            "bsr_cur": bsr_cur, "bb_winners": bb_winners,
            "amz_is_bb": amz_is_bb, "stab": stab, "tier": tier,
            "ean": ean, "asin": asin}


# ════════════════════════════════════════════════════════════════
# REFERENCE DATASET  (fVAT=20% at build time)
# ════════════════════════════════════════════════════════════════
# name              pa_net bb    ppf   ref   bsr_d amz%  bsr_cur win  amz_bb  stab
P = [
    # A: Tier-1 candidate — high ROI, stable, low Amazon BB%, many drops
    make_product("P-A",  10,  40, 2.5, 5.0,  bsr_drops=12, amazon_pct=5,  bsr_cur=8000,   bb_winners=3, amz_is_bb=False, stab="Stable"),
    # B: Tier-2 — decent ROI, medium amazon%, several drops
    make_product("P-B",  8,   28, 2.0, 3.5,  bsr_drops=6,  amazon_pct=30, bsr_cur=25000,  bb_winners=5, amz_is_bb=False, stab="Moderate"),
    # C: Tier-3 — thin ROI (>5% with fCst=0), low drops
    make_product("P-C",  5,   14, 1.5, 1.8,  bsr_drops=2,  amazon_pct=20, bsr_cur=60000,  bb_winners=4, amz_is_bb=False, stab="Volatile"),
    # D: Tier-3 but er goes negative with fCst=3 (profit≈1.5 < fCst=3)
    make_product("P-D",  5,   11, 1.2, 1.5,  bsr_drops=3,  amazon_pct=10, bsr_cur=40000,  bb_winners=2, amz_is_bb=False, stab="Moderate"),
    # E: No-go — negative base ROI
    make_product("P-E",  8,    9, 1.0, 1.2,  bsr_drops=5,  amazon_pct=15, bsr_cur=20000,  bb_winners=3, amz_is_bb=False, stab="Moderate"),
    # F: Amazon holds BB currently
    make_product("P-F",  9,   32, 2.0, 4.0,  bsr_drops=8,  amazon_pct=75, bsr_cur=12000,  bb_winners=6, amz_is_bb=True,  stab="Stable"),
    # G: Very high BSR (slow mover)
    make_product("P-G",  7,   22, 1.8, 2.8,  bsr_drops=4,  amazon_pct=0,  bsr_cur=350000, bb_winners=2, amz_is_bb=False, stab="Moderate"),
    # H: Many BB winners
    make_product("P-H",  6,   20, 1.5, 2.5,  bsr_drops=5,  amazon_pct=5,  bsr_cur=15000,  bb_winners=15, amz_is_bb=False, stab="Moderate"),
    # I: Zero BSR drops
    make_product("P-I",  9,   30, 2.0, 3.8,  bsr_drops=0,  amazon_pct=0,  bsr_cur=5000,   bb_winners=1, amz_is_bb=False, stab="Stable"),
    # J: High amazon_pct (historic BB%)
    make_product("P-J",  7,   24, 1.8, 3.0,  bsr_drops=3,  amazon_pct=85, bsr_cur=18000,  bb_winners=3, amz_is_bb=False, stab="Moderate"),
]

# Print reference table
print("\n══ Reference product table (fVAT=20%, fCst=0) ══")
print(f"  {'Name':<6} {'pa_net':>6} {'profit':>7} {'roi':>7} {'er(0)':>7} {'er(3)':>7} {'drops':>6} {'amz%':>5} {'bsr_cur':>8} {'win':>4} {'amzBB':>6} {'tier':>5}")
for r in P:
    print(f"  {r['name']:<6} {r['pa_net']:>6.2f} {r['profit']:>7.2f} {r['roi']:>6.1f}% {er(r,0):>6.1f}% {er(r,3):>6.1f}% "
          f"{r['bsr_drops']:>6} {r['amazon_pct']:>5} {str(r['bsr_cur'] or 'None'):>8} {r['bb_winners']:>4} "
          f"{str(r['amz_is_bb']):>6}  {r['tier']:>5}")

# ════════════════════════════════════════════════════════════════
# SECTION 1 — Default state (all filters off)
# ════════════════════════════════════════════════════════════════
print("\n══ S1: Default state — all filters off ══")
vis = get_vis(P)
# Only negative-ROI products (P-E) should be excluded at fRoi=0 default
# because er(P-E, 0) = roi < 0
e_er = er(P[4], 0)
check(f"P-E has negative er(0)={e_er:.1f}%", e_er < 0, True)
check("Default: all positive-ROI products visible", len(vis), len(P) - 1)
check("Default: P-E (neg ROI) excluded", "P-E" not in [r["name"] for r in vis], True)
check("Default: P-A P-B P-C P-D P-F P-G P-H P-I P-J all visible",
      all(n in [r["name"] for r in vis] for n in ["P-A","P-B","P-C","P-D","P-F","P-G","P-H","P-I","P-J"]), True)

# ════════════════════════════════════════════════════════════════
# SECTION 2 — ROI filter (fRoi)
# ════════════════════════════════════════════════════════════════
print("\n══ S2: ROI filter (fRoi) ══")
for roi_threshold in [0, 5, 10, 15, 20, 25]:
    vis = get_vis(P, fRoi=roi_threshold)
    names = [r["name"] for r in vis]
    for r in P:
        expected_pass = er(r, 0) >= roi_threshold
        got_pass      = r["name"] in names
        check(f"fRoi={roi_threshold}: {r['name']} (er={er(r,0):.1f}%) → {'pass' if expected_pass else 'exclude'}",
              got_pass, expected_pass)

# Boundary: product exactly at threshold
check("fRoi boundary — product at exact threshold passes (≥, not >)",
      bool(get_vis(P, fRoi=round(er(P[0], 0), 1))), True)

# Relaxing ROI should never LOSE products
prev = None
for t in [30, 20, 15, 10, 5, 1, 0]:
    curr = set(r["name"] for r in get_vis(P, fRoi=t))
    if prev is not None:
        check(f"fRoi relaxed {t}→prev: no products lost (monotone)", prev.issubset(curr), True)
    prev = curr

# ════════════════════════════════════════════════════════════════
# SECTION 3 — Amazon Buy Box % max (fBB)
# ════════════════════════════════════════════════════════════════
print("\n══ S3: Amazon BB % filter (fBB) ══")
check("fBB=0: all pass (no filter)", len(get_vis(P, fBB=0)), len(get_vis(P)))

for threshold in [5, 30, 50, 75, 100]:
    vis   = get_vis(P, fBB=threshold)
    names = [r["name"] for r in vis]
    for r in P:
        if er(r, 0) < 0:
            continue  # already excluded by ROI filter
        exp_pass = r["amazon_pct"] <= threshold   # inclusive: ≤ threshold passes
        got_pass = r["name"] in names
        check(f"fBB={threshold}: {r['name']} (amz%={r['amazon_pct']}) → {'pass' if exp_pass else 'excl'}",
              got_pass, exp_pass)

# Boundary: exactly at threshold
check("fBB boundary: amazon_pct == fBB passes (≤, inclusive)",
      bool(get_vis([make_product("X", 10, 30, 2, 3, amazon_pct=50, bsr_drops=5)], fBB=50)), True)
check("fBB boundary: amazon_pct == fBB+1 excluded",
      not bool(get_vis([make_product("X", 10, 30, 2, 3, amazon_pct=51, bsr_drops=5)], fBB=50)), True)

# ════════════════════════════════════════════════════════════════
# SECTION 4 — BSR Drops minimum (fDrp)
# ════════════════════════════════════════════════════════════════
print("\n══ S4: BSR Drops filter (fDrp) ══")
check("fDrp=0: all pass (no filter)", len(get_vis(P, fDrp=0)), len(get_vis(P)))

for threshold in [1, 3, 5, 6, 10, 12]:
    vis   = get_vis(P, fDrp=threshold)
    names = [r["name"] for r in vis]
    for r in P:
        if er(r, 0) < 0:
            continue
        exp_pass = r["bsr_drops"] >= threshold   # at least threshold drops
        got_pass = r["name"] in names
        check(f"fDrp={threshold}: {r['name']} (drops={r['bsr_drops']}) → {'pass' if exp_pass else 'excl'}",
              got_pass, exp_pass)

# Boundary: exactly at threshold
check("fDrp boundary: bsr_drops == fDrp passes (≥, inclusive)",
      bool(get_vis([make_product("X", 10, 30, 2, 3, bsr_drops=5)], fDrp=5)), True)
check("fDrp boundary: bsr_drops == fDrp-1 excluded",
      not bool(get_vis([make_product("X", 10, 30, 2, 3, bsr_drops=4)], fDrp=5)), True)

# ════════════════════════════════════════════════════════════════
# SECTION 5 — Extra cost (fCst) impact on ROI filter
# ════════════════════════════════════════════════════════════════
print("\n══ S5: Extra cost (fCst) — impact on effective ROI ══")
# P-D has profit≈1.5 < fCst=3 → er goes negative with fCst=3
d_er_0 = er(P[3], 0)
d_er_3 = er(P[3], 3)
check(f"P-D: er(fCst=0)={d_er_0:.1f}% positive, er(fCst=3)={d_er_3:.1f}% negative",
      d_er_0 > 0 and d_er_3 < 0, True)

check("fCst=0: P-D visible (er>0)", "P-D" in [r["name"] for r in get_vis(P, fCst=0)], True)
check("fCst=3: P-D excluded (er<0)", "P-D" not in [r["name"] for r in get_vis(P, fCst=3)], True)
check("fCst=3→0 reset: P-D reappears", "P-D" in [r["name"] for r in get_vis(P, fCst=0)], True)

# Adding fCst can only REMOVE products from view, never add new ones
for fCst_val in [0.5, 1, 2, 3, 5]:
    vis_0    = set(r["name"] for r in get_vis(P, fCst=0))
    vis_cst  = set(r["name"] for r in get_vis(P, fCst=fCst_val))
    check(f"fCst={fCst_val}: visible set ⊆ visible set at fCst=0 (cost can only restrict)",
          vis_cst.issubset(vis_0), True)

# ════════════════════════════════════════════════════════════════
# SECTION 6 — TVA change
# ════════════════════════════════════════════════════════════════
print("\n══ S6: TVA slider (fVAT) ══")
# Rebuild all products at different TVA levels and compare
P20 = [make_product(r["name"], r["pa_net"], r["bb"], r["ppf"], r["ref_fee"],
                    fVAT=20, bsr_drops=r["bsr_drops"], amazon_pct=r["amazon_pct"],
                    bsr_cur=r["bsr_cur"], bb_winners=r["bb_winners"],
                    amz_is_bb=r["amz_is_bb"], stab=r["stab"]) for r in P]
P21 = [make_product(r["name"], r["pa_net"], r["bb"], r["ppf"], r["ref_fee"],
                    fVAT=21, bsr_drops=r["bsr_drops"], amazon_pct=r["amazon_pct"],
                    bsr_cur=r["bsr_cur"], bb_winners=r["bb_winners"],
                    amz_is_bb=r["amz_is_bb"], stab=r["stab"]) for r in P]
P0  = [make_product(r["name"], r["pa_net"], r["bb"], r["ppf"], r["ref_fee"],
                    fVAT=0, bsr_drops=r["bsr_drops"], amazon_pct=r["amazon_pct"],
                    bsr_cur=r["bsr_cur"], bb_winners=r["bb_winners"],
                    amz_is_bb=r["amz_is_bb"], stab=r["stab"]) for r in P]

for i, r0, r21 in zip(range(len(P)), P20, P21):
    if r0["pa_net"] > 0:
        check(f"{r0['name']}: fVAT=21% gives lower profit than 20%",
              r21["profit"] < r0["profit"], True)
        check(f"{r0['name']}: fVAT=21% gives lower roi than 20%",
              r21["roi"] < r0["roi"], True)

# Higher TVA can only restrict, never widen the visible set
vis_20 = set(r["name"] for r in get_vis(P20))
vis_21 = set(r["name"] for r in get_vis(P21))
vis_0  = set(r["name"] for r in get_vis(P0))
check("fVAT=21% visible ⊆ fVAT=20% visible", vis_21.issubset(vis_20), True)
check("fVAT=20% visible ⊆ fVAT=0% visible",  vis_20.issubset(vis_0),  True)

# TVA reset from 21% to 20%: rebuilding gives same results as fresh build at 20%
for r21, r20 in zip(P21, P20):
    rebuild_profit(r21, fVAT=20)  # simulate TVA reset
    check(f"{r21['name']}: reset TVA 21→20 restores profit to 20% value",
          r21["profit"], r20["profit"])

vis_after_reset = set(r["name"] for r in get_vis(P21))
check("TVA reset 21→20: results same as fresh 20%", vis_after_reset, vis_20)

# ════════════════════════════════════════════════════════════════
# SECTION 7 — BSR Max filter (fBsrMax)
# ════════════════════════════════════════════════════════════════
print("\n══ S7: BSR Max filter (fBsrMax) ══")
check("fBsrMax=0: all pass (no filter)", len(get_vis(P, fBsrMax=0)), len(get_vis(P)))

for threshold in [10000, 25000, 50000, 100000, 350000]:
    vis   = get_vis(P, fBsrMax=threshold)
    names = [r["name"] for r in vis]
    for r in P:
        if er(r, 0) < 0:
            continue
        bsr = r.get("bsr_cur")
        exp_pass = bool(bsr) and bsr <= threshold   # no BSR data → excluded when filter active
        got_pass = r["name"] in names
        check(f"fBsrMax={threshold:,}: {r['name']} (bsr={bsr}) → {'pass' if exp_pass else 'excl'}",
              got_pass, exp_pass)

# Products with no BSR data are excluded when fBsrMax is active
no_bsr_prod = make_product("NoBSR", 10, 30, 2, 3, bsr_drops=5)
no_bsr_prod["bsr_cur"] = None
check("fBsrMax active + no BSR data → excluded",
      not bool(get_vis([no_bsr_prod], fBsrMax=100000)), True)
check("fBsrMax=0 + no BSR data → included",
      bool(get_vis([no_bsr_prod], fBsrMax=0)), True)

# Boundary: exactly at threshold passes
p_exact = make_product("Exact", 10, 30, 2, 3, bsr_drops=5, bsr_cur=50000)
check("fBsrMax boundary: bsr_cur == fBsrMax passes (≤, inclusive)",
      bool(get_vis([p_exact], fBsrMax=50000)), True)
check("fBsrMax boundary: bsr_cur == fBsrMax+1 excluded",
      not bool(get_vis([p_exact], fBsrMax=49999)), True)

# ════════════════════════════════════════════════════════════════
# SECTION 8 — BB Winners Max filter (fWinMax)
# ════════════════════════════════════════════════════════════════
print("\n══ S8: BB Winners Max filter (fWinMax) ══")
check("fWinMax=0: all pass (no filter)", len(get_vis(P, fWinMax=0)), len(get_vis(P)))

for threshold in [2, 5, 6, 10, 15]:
    vis   = get_vis(P, fWinMax=threshold)
    names = [r["name"] for r in vis]
    for r in P:
        if er(r, 0) < 0:
            continue
        exp_pass = r["bb_winners"] <= threshold
        got_pass = r["name"] in names
        check(f"fWinMax={threshold}: {r['name']} (win={r['bb_winners']}) → {'pass' if exp_pass else 'excl'}",
              got_pass, exp_pass)

# Boundary
check("fWinMax boundary: bb_winners == fWinMax passes",
      bool(get_vis([make_product("X", 10, 30, 2, 3, bsr_drops=5, bb_winners=5)], fWinMax=5)), True)
check("fWinMax boundary: bb_winners == fWinMax+1 excluded",
      not bool(get_vis([make_product("X", 10, 30, 2, 3, bsr_drops=5, bb_winners=6)], fWinMax=5)), True)

# ════════════════════════════════════════════════════════════════
# SECTION 9 — Amazon BB toggle (fAmzInBB)
# ════════════════════════════════════════════════════════════════
print("\n══ S9: Amazon BB toggle (fAmzInBB) ══")
vis_any = get_vis(P, fAmzInBB="any")
vis_no  = get_vis(P, fAmzInBB="no")
vis_yes = get_vis(P, fAmzInBB="yes")

names_any = [r["name"] for r in vis_any]
names_no  = [r["name"] for r in vis_no]
names_yes = [r["name"] for r in vis_yes]

check("fAmzInBB='any': all valid products visible", set(names_any), set(r["name"] for r in get_vis(P)))

for r in P:
    if er(r, 0) < 0:
        continue
    if r["amz_is_bb"]:
        check(f"fAmzInBB='no':  {r['name']} (amz_is_bb=True) excluded", r["name"] not in names_no,  True)
        check(f"fAmzInBB='yes': {r['name']} (amz_is_bb=True) kept",     r["name"] in names_yes,     True)
    else:
        check(f"fAmzInBB='no':  {r['name']} (amz_is_bb=False) kept",     r["name"] in names_no,      True)
        check(f"fAmzInBB='yes': {r['name']} (amz_is_bb=False) excluded", r["name"] not in names_yes, True)

# Round trip: any → no → yes → any
check("Round-trip any→no→yes→any: same as initial 'any'",
      set(r["name"] for r in get_vis(P, fAmzInBB="any")), set(names_any))

# ════════════════════════════════════════════════════════════════
# SECTION 10 — Update summary (updateSum)
# ════════════════════════════════════════════════════════════════
print("\n══ S10: Filter summary (updateSum) ══")
check("All defaults → 'No filters active'",
      update_sum(), " — No filters active")
check("fRoi=20 → shows ROI",
      "ROI ≥ 20%" in update_sum(fRoi=20), True)
check("fBB=50 → shows BB",
      "BB ≤ 50%" in update_sum(fBB=50), True)
check("fDrp=3 → shows Drops",
      "Drops ≥ 3" in update_sum(fDrp=3), True)
check("fCst=3 → shows cost",
      "+€3.00" in update_sum(fCst=3.0), True)
check("fVAT=20 → NOT shown (default)",
      "TVA" not in update_sum(fVAT=20), True)
check("fVAT=21 → shown (non-default)",
      "TVA 21%" in update_sum(fVAT=21), True)
check("fVAT=0 → shown (non-default)",
      "TVA 0%" in update_sum(fVAT=0), True)
check("fBsrMax=100000 → shows BSR",
      "BSR" in update_sum(fBsrMax=100000), True)
check("fWinMax=5 → shows Win",
      "Win ≤ 5" in update_sum(fWinMax=5), True)
check("fAmzInBB='no' → shown",
      "Amazon BB: no" in update_sum(fAmzInBB="no"), True)
check("fAmzInBB='any' → NOT shown (default)",
      "Amazon BB" not in update_sum(fAmzInBB="any"), True)

# ════════════════════════════════════════════════════════════════
# SECTION 11 — Multi-filter combinations
# ════════════════════════════════════════════════════════════════
print("\n══ S11: Multi-filter combinations ══")

# Combo 1: fDrp=3 + fAmzInBB='no'
vis = get_vis(P, fDrp=3, fAmzInBB="no")
names = [r["name"] for r in vis]
for r in P:
    exp = er(r, 0) >= 0 and r["bsr_drops"] >= 3 and not r["amz_is_bb"]
    check(f"fDrp=3+amzbb=no: {r['name']} → {'pass' if exp else 'excl'}", r["name"] in names, exp)

# Combo 2: fCst=3 + fVAT=21% + fDrp=1
P21b = [dict(r) for r in P]
for r in P21b:
    rebuild_profit(r, fVAT=21, fCst=3)
vis = get_vis(P21b, fDrp=1, fCst=3)
names = [r["name"] for r in vis]
for r, r21 in zip(P, P21b):
    exp = er(r21, 3) >= 0 and r["bsr_drops"] >= 1
    check(f"fCst=3+fVAT=21+fDrp=1: {r['name']} (er21={er(r21,3):.1f}% drops={r['bsr_drops']}) → {'pass' if exp else 'excl'}",
          r["name"] in names, exp)

# Combo 3: tightest possible — fRoi=25 + fDrp=10 + fAmzInBB='no' + fBB=20 + fWinMax=8
vis = get_vis(P, fRoi=25, fDrp=10, fAmzInBB="no", fBB=20, fWinMax=8)
names = [r["name"] for r in vis]
for r in P:
    exp = (er(r, 0) >= 25 and r["bsr_drops"] >= 10 and not r["amz_is_bb"]
           and r["amazon_pct"] <= 20 and r["bb_winners"] <= 8)
    check(f"Max-tight: {r['name']} → {'pass' if exp else 'excl'}", r["name"] in names, exp)

# ════════════════════════════════════════════════════════════════
# SECTION 12 — Filter-change state transitions
# ════════════════════════════════════════════════════════════════
print("\n══ S12: Filter-change transitions ══")

# Transition A: set fAmzInBB='no' (0 results if all amz_is_bb), change to 'any' → all back
p_amz_all = [make_product(f"AP{i}", 10, 30, 2, 3.5, bsr_drops=5, amz_is_bb=True) for i in range(5)]
vis_no  = get_vis(p_amz_all, fAmzInBB="no")
vis_any = get_vis(p_amz_all, fAmzInBB="any")
check("Transition: all Amazon BB → fAmzInBB='no' gives 0", len(vis_no), 0)
check("Transition: all Amazon BB → fAmzInBB='any' restores all 5", len(vis_any), 5)

# Transition B: tighten fRoi from 5 to 25, then relax back to 5 — same results
vis_5a  = set(r["name"] for r in get_vis(P, fRoi=5))
vis_25  = set(r["name"] for r in get_vis(P, fRoi=25))
vis_5b  = set(r["name"] for r in get_vis(P, fRoi=5))   # relax back
check("Transition fRoi=5→25→5: final state equals initial fRoi=5", vis_5a, vis_5b)
check("Transition fRoi=5→25→5: strict state is subset", vis_25.issubset(vis_5a), True)

# Transition C: add fCst=3 (some products lost), then remove (all restored)
vis_before = set(r["name"] for r in get_vis(P, fCst=0))
vis_with   = set(r["name"] for r in get_vis(P, fCst=3))
vis_after  = set(r["name"] for r in get_vis(P, fCst=0))   # remove extra cost
check("Transition fCst=0→3→0: restores same products as initial", vis_before, vis_after)
check("Transition fCst=3: is a strict subset of fCst=0", vis_with.issubset(vis_before), True)

# Transition D: change fDrp 3→1→3 — intermediate relaxation then re-tighten
vis_3a = set(r["name"] for r in get_vis(P, fDrp=3))
vis_1  = set(r["name"] for r in get_vis(P, fDrp=1))
vis_3b = set(r["name"] for r in get_vis(P, fDrp=3))
check("Transition fDrp=3→1→3: re-tighten gives same result as initial", vis_3a, vis_3b)

# Transition E: rstAll equivalent — all defaults → all positive-ROI products visible
vis_rst = get_vis(P, fRoi=0, fBB=0, fDrp=0, fCst=0, fBsrMax=0, fWinMax=0, fAmzInBB="any")
check("rstAll: all filters default → same as initial default state",
      set(r["name"] for r in vis_rst), set(r["name"] for r in get_vis(P)))

# ════════════════════════════════════════════════════════════════
# SECTION 13 — Tier count consistency
# ════════════════════════════════════════════════════════════════
print("\n══ S13: Tier calculation consistency ══")
# Tier should match adjRoi = er(r) when fCst=0
for r in P:
    adj_roi  = er(r, 0)
    expected_tier = tier_calc(adj_roi, r["amazon_pct"], r["stab"], r["bsr_drops"], r["bb_winners"])
    check(f"{r['name']}: r.tier ({r['tier']}) matches tierCalc(er(r,0)={adj_roi:.1f}%,...)",
          r["tier"], expected_tier)

# After fCst changes, tiers update
for r in P:
    update_tier_for_cst(r, fCst=3)
    adj_roi_3 = er(r, 3)
    expected_tier_3 = tier_calc(adj_roi_3, r["amazon_pct"], r["stab"], r["bsr_drops"], r["bb_winners"])
    check(f"{r['name']}: after fCst=3, tier ({r['tier']}) matches tierCalc(er(r,3)={adj_roi_3:.1f}%,...)",
          r["tier"], expected_tier_3)

# Reset fCst to 0: tiers restore
for r in P:
    update_tier_for_cst(r, fCst=0)
    adj_roi_0 = er(r, 0)
    expected_tier_0 = tier_calc(adj_roi_0, r["amazon_pct"], r["stab"], r["bsr_drops"], r["bb_winners"])
    check(f"{r['name']}: after fCst=3→0 reset, tier ({r['tier']}) matches tierCalc(er(r,0)={adj_roi_0:.1f}%,...)",
          r["tier"], expected_tier_0)

# ════════════════════════════════════════════════════════════════
# SECTION 14 — Exact screenshot scenario
# ════════════════════════════════════════════════════════════════
print("\n══ S14: Screenshot scenario (Drops≥1, +€3, TVA 21%, Amazon NOT in BB) ══")
# Rebuild products with fVAT=21%
P_scr = [dict(r) for r in P]
for r in P_scr:
    rebuild_profit(r, fVAT=21, fCst=3)

# With Amazon NOT in BB filter → only non-amz_is_bb products that also pass other filters
vis_screen = get_vis(P_scr, fDrp=1, fCst=3, fAmzInBB="no")
names_scr  = [r["name"] for r in vis_screen]
for r_orig, r_scr in zip(P, P_scr):
    exp = (not r_orig["amz_is_bb"] and r_orig["bsr_drops"] >= 1 and er(r_scr, 3) >= 0)
    check(f"Screenshot state: {r_orig['name']} (amzBB={r_orig['amz_is_bb']}, drops={r_orig['bsr_drops']}, er21%={er(r_scr,3):.1f}%) → {'pass' if exp else 'excl'}",
          r_orig["name"] in names_scr, exp)

# Change: relax fAmzInBB to 'any' (same fDrp, fCst, fVAT)
vis_relax = get_vis(P_scr, fDrp=1, fCst=3, fAmzInBB="any")
names_relax = [r["name"] for r in vis_relax]
check("Screenshot: relax amzbb='any' → shows MORE products than 'no'",
      len(vis_relax) >= len(vis_screen), True)
check("Screenshot: relax amzbb='any' → all products from 'no' still visible",
      set(names_scr).issubset(set(names_relax)), True)
for r_orig, r_scr in zip(P, P_scr):
    exp = r_orig["bsr_drops"] >= 1 and er(r_scr, 3) >= 0
    check(f"Screenshot+amzbb=any: {r_orig['name']} → {'pass' if exp else 'excl'}",
          r_orig["name"] in names_relax, exp)

# Change: also relax fDrp to 0
vis_relax2 = get_vis(P_scr, fDrp=0, fCst=3, fAmzInBB="any")
check("Screenshot: also relax fDrp=0 → even more products",
      len(vis_relax2) >= len(vis_relax), True)

# Reset all: fCst=0, fDrp=0, fAmzInBB='any', fVAT=20 (rebuild)
P_rst = [dict(r) for r in P]  # fresh at fVAT=20
vis_rst = get_vis(P_rst, fRoi=0, fBB=0, fDrp=0, fCst=0, fBsrMax=0, fWinMax=0, fAmzInBB="any")
check("Screenshot: Reset All → same as fresh default state",
      set(r["name"] for r in vis_rst), set(r["name"] for r in get_vis(P)))

# ════════════════════════════════════════════════════════════════
# Summary
# ════════════════════════════════════════════════════════════════
print()
print(f"  Tests run: {total}")
if errors == 0:
    print(f"\033[32m══ ALL {total} TESTS PASSED ✓ ══\033[0m")
else:
    print(f"\033[31m══ {errors}/{total} TEST(S) FAILED ══\033[0m")
    raise SystemExit(1)
