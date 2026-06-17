#!/usr/bin/env python3
"""
batch_keepa.py — Batch Keepa automation for all Sourcing AMZ catalogues
------------------------------------------------------------------------
Walks Sourcing AMZ/ recursively, finds every supplier catalogue (CSV or XLSX),
runs keepaautomation.py for each one, and saves the Keepa export to the
mirrored path inside keepa vs keepa/.

Run:
    python batch_keepa.py
    python batch_keepa.py --dry-run   # preview what will be processed
"""

import argparse
import csv
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import openpyxl

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR    = Path(__file__).parent
SOURCING_DIR  = Path("/Users/soso/Desktop/Sourcing AMZ ")
KEEPA_OUT_DIR = Path("/Users/soso/keepa vs keepa")
PYTHON        = str(SCRIPT_DIR / ".venv/bin/python")
KEEPA_SCRIPT  = str(SCRIPT_DIR / "keepaautomation.py")
TEMP_DIR      = Path("/tmp/sovizion/batch")

# ── Marketplace detection — folder name keywords → Keepa marketplace code ──────
MARKETPLACE_KEYWORDS = {
    "france": "FR",
    "germany": "DE",
    "uk":      "UK",
    "spain":   "ES",
    "italy":   "IT",
    "netherlands": "NL",
    "belgium": "BE",
    "sweden":  "SE",
    "poland":  "PL",
}

# ── Output file name prefixes that are NOT supplier catalogues ─────────────────
SKIP_PREFIXES = ("keepaexport", "sovizion_po", "sovizion po")

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("batch-keepa")


# ── Helpers ────────────────────────────────────────────────────────────────────

def detect_marketplace(path: Path) -> str:
    """Return the Keepa marketplace code based on a country folder in the path."""
    for part in path.parts:
        lower = part.lower()
        for keyword, code in MARKETPLACE_KEYWORDS.items():
            if keyword in lower:
                return code
    return "FR"


def is_supplier_file(f: Path) -> bool:
    """True if the file is a supplier catalogue (not a Keepa or PO output)."""
    if f.suffix.lower() not in (".csv", ".xlsx"):
        return False
    name = f.name.lower()
    return not any(name.startswith(p) for p in SKIP_PREFIXES)


def find_supplier_files(folder: Path) -> list[Path]:
    """
    Return supplier files in this folder.
    Prefers CSVs over XLSXs — if any supplier CSV exists in the folder,
    skip all XLSXs (they are just the original before CSV conversion).
    """
    candidates = [f for f in folder.iterdir() if f.is_file() and is_supplier_file(f)]
    csvs  = [f for f in candidates if f.suffix.lower() == ".csv"]
    xlsxs = [f for f in candidates if f.suffix.lower() == ".xlsx"]
    return csvs if csvs else xlsxs


def xlsx_to_temp_csv(xlsx_path: Path) -> Path:
    """Convert the first sheet of an XLSX to a temp CSV and return its path."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb.active
    tmp = TEMP_DIR / f"{xlsx_path.stem}.csv"
    with open(tmp, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        for row in ws.iter_rows(values_only=True):
            writer.writerow(["" if v is None else str(v) for v in row])
    wb.close()
    log.info("  Converted XLSX → temp CSV: %s", tmp.name)
    return tmp


def collect_jobs() -> list[tuple[Path, Path, str]]:
    """
    Walk SOURCING_DIR and return a list of (supplier_file, output_dir, marketplace).
    """
    jobs = []
    for folder in sorted(SOURCING_DIR.rglob("*")):
        if not folder.is_dir():
            continue
        files = find_supplier_files(folder)
        if not files:
            continue
        marketplace = detect_marketplace(folder)
        relative    = folder.relative_to(SOURCING_DIR)
        output_dir  = KEEPA_OUT_DIR / relative
        for f in files:
            jobs.append((f, output_dir, marketplace))
    return jobs


def run_keepa(supplier_file: Path, output_dir: Path, marketplace: str) -> bool:
    """Run keepaautomation.py for one supplier file. Returns True on success."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convert XLSX to temp CSV if needed
    if supplier_file.suffix.lower() == ".xlsx":
        csv_path = xlsx_to_temp_csv(supplier_file)
    else:
        csv_path = supplier_file

    proc = subprocess.run(
        [PYTHON, KEEPA_SCRIPT,
         "--csv",         str(csv_path),
         "--output",      str(output_dir),
         "--marketplace", marketplace,
         "--no-wait"],
    )

    success = proc.returncode == 0
    if success:
        log.info("  ✓ Done")
    else:
        log.error("  ✗ Failed (exit code %d)", proc.returncode)
    return success


def main():
    parser = argparse.ArgumentParser(description="Batch Keepa automation for all Sourcing AMZ catalogues.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed without running.")
    args = parser.parse_args()

    if not SOURCING_DIR.exists():
        log.error("Sourcing folder not found: %s", SOURCING_DIR)
        sys.exit(1)

    jobs = collect_jobs()
    if not jobs:
        log.info("No supplier files found in %s", SOURCING_DIR)
        return

    log.info("=" * 64)
    log.info("  Batch Keepa — %s", datetime.now().strftime("%Y-%m-%d %H:%M"))
    log.info("  %d supplier file(s) found", len(jobs))
    log.info("=" * 64)

    for i, (supplier_file, output_dir, marketplace) in enumerate(jobs, 1):
        rel = supplier_file.relative_to(SOURCING_DIR)
        log.info("[%d/%d] %s  [%s]", i, len(jobs), rel, marketplace)
        log.info("  Output → %s", output_dir.relative_to(KEEPA_OUT_DIR.parent))

        if args.dry_run:
            continue

        run_keepa(supplier_file, output_dir, marketplace)

    if args.dry_run:
        log.info("Dry run complete — nothing was executed.")
        return

    ok   = sum(1 for j in jobs if True)   # recount not needed — just summary
    log.info("=" * 64)
    log.info("  Batch complete — %d file(s) processed", len(jobs))
    log.info("=" * 64)


if __name__ == "__main__":
    main()
