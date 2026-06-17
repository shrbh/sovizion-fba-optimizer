"""
Keepa.com Automation Script
----------------------------
Automates the Keepa PRO Product Viewer workflow:
  1. Opens Keepa in Chrome with a custom download folder.
  2. Waits for the user to log in manually (no stored credentials).
  3. Selects the target marketplace (default: Amazon France).
  4. Navigates to PRO → Product Viewer.
  5. Auto-detects whether the CSV contains ASINs or UPC/EAN/GTIN codes.
  6. Pastes the cleaned list and clicks LOAD LIST.
  7. Dismisses any "Search result" popup if it appears.
  8. Clicks EXPORT and waits for the download to complete.
  9. Prints the path to the downloaded file.

Usage:
    python keepaautomation.py --csv products.csv --output ./downloads
    python keepaautomation.py --csv products.csv --output ./downloads --marketplace FR

Requirements:
    pip install -r requirements.txt
"""

import argparse
import csv
import logging
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("keepa-bot")

# ---------------------------------------------------------------------------
# Constants — adjust these if Keepa changes its UI
# ---------------------------------------------------------------------------
KEEPA_URL = "https://keepa.com"

# ---------------------------------------------------------------------------
# Credentials — stored here so login is fully automatic.
# ---------------------------------------------------------------------------
KEEPA_EMAIL    = "hosseini@sovizion.com"   # ← replace with your Keepa email
KEEPA_PASSWORD = "Metlika.8312"     # ← replace with your Keepa password

# Marketplace codes used by Keepa's URL hash / UI selector
# TODO: Verify these IDs by inspecting the marketplace dropdown in Keepa's UI.
#       Open DevTools → Elements and look for <option> or data attributes on
#       the marketplace selector when you click the flag icon.
MARKETPLACE_MAP = {
    "US": {"id": "1", "label": "amazon.com"},
    "UK": {"id": "2", "label": "amazon.co.uk"},
    "DE": {"id": "3", "label": "amazon.de"},
    "FR": {"id": "4", "label": "amazon.fr"},
    "JP": {"id": "5", "label": "amazon.co.jp"},
    "CA": {"id": "6", "label": "amazon.ca"},
    "IT": {"id": "8", "label": "amazon.it"},
    "ES": {"id": "9", "label": "amazon.es"},
    "IN": {"id": "10", "label": "amazon.in"},
    "MX": {"id": "11", "label": "amazon.com.mx"},
    "BR": {"id": "12", "label": "amazon.com.br"},
    "AU": {"id": "13", "label": "amazon.com.au"},
    "NL": {"id": "14", "label": "amazon.nl"},
    "SG": {"id": "15", "label": "amazon.sg"},
    "SA": {"id": "16", "label": "amazon.sa"},
    "TR": {"id": "17", "label": "amazon.com.tr"},
    "AE": {"id": "18", "label": "amazon.ae"},
    "SE": {"id": "19", "label": "amazon.se"},
    "PL": {"id": "20", "label": "amazon.pl"},
    "BE": {"id": "21", "label": "amazon.com.be"},
    "EG": {"id": "22", "label": "amazon.eg"},
    "ZA": {"id": "23", "label": "amazon.co.za"},
}

# Timeouts (seconds)
WAIT_LONG = 60       # For heavy page loads / downloads
WAIT_MEDIUM = 20     # For elements that take a moment to appear
WAIT_SHORT = 8       # For quick UI responses

# ---------------------------------------------------------------------------
# Step 1 — Read and clean the CSV
# ---------------------------------------------------------------------------

def load_csv(csv_path: str, column: str | None = None) -> list[str]:
    """
    Extract one column from a CSV and return all non-empty values.

    Column selection (in order of priority):
    1. --column argument: an exact header name or 0-based index.
    2. Auto-detect: scan the first header row for keywords like EAN, GTIN,
       ASIN, UPC, Barcode (case-insensitive). Uses the first match.
    3. Fallback: column index 0.

    No content validation is applied — the whole column is returned as-is so
    Keepa can receive exactly what the CSV contains.
    """
    path = Path(csv_path)
    if not path.exists():
        log.error("CSV file not found: %s", csv_path)
        sys.exit(1)

    # Try encodings in order — French supplier files are often cp1252
    encodings = ["utf-8-sig", "cp1252", "latin-1", "iso-8859-1"]
    fh = None
    for enc in encodings:
        try:
            fh = open(path, newline="", encoding=enc, errors="strict")
            fh.read()
            fh.seek(0)
            log.info("Reading CSV with encoding: %s", enc)
            break
        except (UnicodeDecodeError, LookupError):
            if fh:
                fh.close()
            fh = None
    if fh is None:
        log.error("Could not decode CSV with any of: %s", encodings)
        sys.exit(1)

    # Keywords that identify the target column by header name
    ID_KEYWORDS = re.compile(r"(ean|gtin|upc|asin|barcode|code.?ean|code.?barre)", re.IGNORECASE)

    with fh:
        reader = csv.reader(fh)
        rows = list(reader)

    if not rows:
        log.error("CSV is empty.")
        sys.exit(1)

    # --- Resolve target column index ---
    col_index: int | None = None

    if column is not None:
        # User provided --column: try as integer index first, then header name
        try:
            col_index = int(column)
            log.info("Using column index %d (from --column).", col_index)
        except ValueError:
            # Search all rows for a header row containing this name
            for row in rows:
                for i, cell in enumerate(row):
                    if cell.strip().lower() == column.strip().lower():
                        col_index = i
                        log.info("Using column '%s' at index %d (from --column).", column, col_index)
                        break
                if col_index is not None:
                    break
            if col_index is None:
                log.error("Column '%s' not found in CSV headers.", column)
                sys.exit(1)
    else:
        # Auto-detect: scan every row for a cell whose text matches ID_KEYWORDS
        for row in rows:
            for i, cell in enumerate(row):
                if ID_KEYWORDS.search(cell.strip()):
                    col_index = i
                    log.info("Auto-detected identifier column '%s' at index %d.", cell.strip(), col_index)
                    break
            if col_index is not None:
                break

    if col_index is None:
        col_index = 0
        log.warning("Could not detect identifier column — falling back to column 0.")

    # --- Extract all non-empty values from the target column ---
    values = []
    for row in rows:
        if len(row) <= col_index:
            continue
        val = row[col_index].strip()
        if val:
            values.append(val)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique = []
    for v in values:
        if v not in seen:
            seen.add(v)
            unique.append(v)

    log.info("Loaded %d values from column index %d.", len(unique), col_index)
    return unique


# ---------------------------------------------------------------------------
# Step 2 — Auto-detect list type
# ---------------------------------------------------------------------------

def detect_list_type(values: list[str]) -> str:
    """
    Return 'ASIN' or 'UPC' based on the content of the list.

    ASIN rules:
      - Exactly 10 characters
      - Starts with 'B' (most common) OR is a 10-char alphanumeric string
        that Amazon uses as an identifier (older ASINs may be purely numeric)

    UPC/EAN/GTIN rules:
      - Purely numeric
      - 8 digits (EAN-8), 12 digits (UPC-A), 13 digits (EAN-13), or 14 digits (GTIN-14)
    """
    asin_pattern = re.compile(r"^[A-Z0-9]{10}$", re.IGNORECASE)
    barcode_pattern = re.compile(r"^\d{8}$|^\d{12}$|^\d{13}$|^\d{14}$")

    asin_count = sum(1 for v in values if asin_pattern.match(v))
    barcode_count = sum(1 for v in values if barcode_pattern.match(v))

    if asin_count >= barcode_count:
        log.info("Detected list type: ASIN (%d matches vs %d barcode matches)", asin_count, barcode_count)
        return "ASIN"
    else:
        log.info("Detected list type: UPC/EAN/GTIN (%d barcode matches vs %d ASIN matches)", barcode_count, asin_count)
        return "UPC"


# ---------------------------------------------------------------------------
# Step 3 — Browser setup
# ---------------------------------------------------------------------------

def create_driver(download_dir: str) -> webdriver.Chrome:
    """Launch Chrome with a custom download directory."""
    abs_download = str(Path(download_dir).resolve())
    Path(abs_download).mkdir(parents=True, exist_ok=True)

    prefs = {
        "download.default_directory": abs_download,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "plugins.always_open_pdf_externally": True,
        # Disable "Save password?" popup
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
    }

    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", prefs)
    # Incognito ensures no cached session — script always logs in fresh
    chrome_options.add_argument("--incognito")
    # Keep browser visible (not headless)
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    # Suppress "Chrome is being controlled by automated software" banner
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    log.info("Launching Chrome (downloads → %s)", abs_download)
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options,
    )
    driver.implicitly_wait(0)  # We use explicit waits everywhere
    return driver


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def wait_for(driver, by, selector, timeout=WAIT_MEDIUM, condition="visible"):
    """
    Wait for an element and return it.
    condition: 'visible' | 'clickable' | 'present'
    """
    wait = WebDriverWait(driver, timeout)
    cond_map = {
        "visible": EC.visibility_of_element_located,
        "clickable": EC.element_to_be_clickable,
        "present": EC.presence_of_element_located,
    }
    return wait.until(cond_map[condition]((by, selector)))


def safe_click(driver, element, retries=3):
    """Click an element, scrolling into view and retrying on interception."""
    for attempt in range(retries):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
            time.sleep(0.3)
            element.click()
            return
        except (ElementClickInterceptedException, StaleElementReferenceException) as exc:
            log.warning("Click attempt %d failed (%s), retrying…", attempt + 1, exc)
            time.sleep(1)
    # Last resort — JavaScript click
    driver.execute_script("arguments[0].click();", element)


def take_screenshot(driver, label: str, output_dir: str):
    """Save a screenshot to the output directory for debugging."""
    filename = Path(output_dir) / f"error_{label}_{int(time.time())}.png"
    driver.save_screenshot(str(filename))
    log.error("Screenshot saved: %s", filename)


def wait_for_download(download_dir: str, before_files: set, timeout=WAIT_LONG) -> str | None:
    """
    Wait until a new fully-downloaded file appears in download_dir.
    Returns the file path, or None on timeout.
    Handles Chrome's temporary .crdownload extension.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        current = set(Path(download_dir).glob("*"))
        new_files = current - before_files
        completed = [f for f in new_files
                     if not f.name.endswith(".crdownload")
                     and not f.name.startswith(".com.google.Chrome")]
        if completed:
            return str(sorted(completed, key=lambda f: f.stat().st_mtime)[-1])
        time.sleep(1)
    return None


# ---------------------------------------------------------------------------
# Step 4 — Login
# ---------------------------------------------------------------------------

def ensure_logged_in(driver: webdriver.Chrome):
    """
    Open Keepa and log in automatically using KEEPA_EMAIL / KEEPA_PASSWORD.
    Falls back to manual login prompt if auto-login fails for any reason.

    Logged-in detection: #panelUserRegisterLogin text changes from
    "Log In / Register" to the username after a successful login.
    """
    LOGIN_BTN_SELECTOR = "#panelUserRegisterLogin"
    LOGIN_TEXT         = "Log In / Register"

    log.info("Opening %s", KEEPA_URL)
    driver.get(KEEPA_URL)
    WebDriverWait(driver, WAIT_LONG).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

    def is_logged_in(d):
        try:
            el = d.find_element(By.CSS_SELECTOR, LOGIN_BTN_SELECTOR)
            return LOGIN_TEXT not in el.text
        except Exception:
            return False

    if KEEPA_EMAIL and KEEPA_PASSWORD:
        try:
            log.info("Attempting automatic login…")

            login_link = wait_for(
                driver, By.CSS_SELECTOR, LOGIN_BTN_SELECTOR,
                timeout=WAIT_SHORT, condition="clickable",
            )
            safe_click(driver, login_link)
            log.info("Login panel opened.")
            time.sleep(1.5)

            email_field = wait_for(
                driver, By.CSS_SELECTOR, "#username",
                timeout=WAIT_MEDIUM, condition="clickable",
            )
            driver.execute_script("arguments[0].click();", email_field)
            time.sleep(0.2)
            email_field.send_keys(KEEPA_EMAIL)

            pw_field = wait_for(
                driver, By.CSS_SELECTOR, "#password",
                timeout=WAIT_SHORT, condition="clickable",
            )
            driver.execute_script("arguments[0].click();", pw_field)
            time.sleep(0.2)
            pw_field.send_keys(KEEPA_PASSWORD)
            pw_field.send_keys(Keys.RETURN)

            # Wait for #panelUserRegisterLogin text to change from "Log In / Register"
            WebDriverWait(driver, WAIT_MEDIUM).until(is_logged_in)
            log.info("Auto-login successful.")
            return

        except Exception as exc:
            log.warning("Auto-login failed (%s) — falling back to manual login.", exc)

    # Manual fallback
    log.info("=" * 60)
    log.info("Please log in to Keepa manually in the browser window.")
    log.info("Once logged in, press Enter (or click the button in the dashboard).")
    log.info("=" * 60)
    print("KEEPA_BOT::WAITING_FOR_LOGIN", flush=True)
    input()

    try:
        WebDriverWait(driver, WAIT_MEDIUM).until(is_logged_in)
        log.info("Login confirmed.")
    except TimeoutException:
        log.warning(
            "Could not confirm login. Continuing anyway — script may fail if not logged in."
        )


# ---------------------------------------------------------------------------
# Step 5 — Select marketplace
# ---------------------------------------------------------------------------

def select_marketplace(driver: webdriver.Chrome, marketplace_code: str):
    """
    Select the marketplace via Keepa's two-step dropdown.

    Step 1 — click the trigger to open the marketplace box:
        <span class="languageMenuImg" rel="domain">.fr</span>

    Step 2 — click the target marketplace inside the box:
        <span rel="domain" setting="N">...</span>
        where N is the marketplace ID from MARKETPLACE_MAP.
    """
    code = marketplace_code.upper()
    if code not in MARKETPLACE_MAP:
        log.error("Unknown marketplace code '%s'. Valid codes: %s", code, list(MARKETPLACE_MAP.keys()))
        sys.exit(1)

    mp = MARKETPLACE_MAP[code]
    log.info("Selecting marketplace: %s (%s)", code, mp["label"])

    # Step 1 — open the marketplace dropdown box.
    trigger = wait_for(
        driver, By.CSS_SELECTOR, "span.languageMenuImg[rel='domain']",
        timeout=WAIT_MEDIUM, condition="clickable",
    )
    safe_click(driver, trigger)
    log.info("Marketplace box opened.")

    # Step 2 — click the target marketplace span inside the box.
    css = f"span[rel='domain'][setting='{mp['id']}']"
    option = wait_for(driver, By.CSS_SELECTOR, css, timeout=WAIT_MEDIUM, condition="clickable")
    safe_click(driver, option)
    log.info("Marketplace '%s' selected (setting=%s).", code, mp["id"])
    time.sleep(1)


# ---------------------------------------------------------------------------
# Step 6 — Navigate to PRO → Product Viewer
# ---------------------------------------------------------------------------

def navigate_to_product_viewer(driver: webdriver.Chrome):
    """
    Click PRO in the navigation, then click Product Viewer.

    TODO: Keepa's navigation structure may change. Use DevTools to inspect:
          - The "PRO" nav item (often <a> or <li> with text "PRO")
          - The "Product Viewer" sub-item that appears after clicking PRO
          Update the selectors below if the script cannot find these elements.
    """
    log.info("Navigating to PRO → Product Viewer.")

    # --- Click PRO nav item ---
    # Confirmed from live DOM:
    #   <a href="#!data"><i id="menuData" class="fa fa-cube"></i><span>Pro</span></a>
    # Two reliable anchors: the href value and the unique id on the inner <i>.
    PRO_SELECTORS = [
        "a[href='#!data']",   # most specific — exact href match
        "#menuData",           # unique id on the icon inside the link
    ]

    pro_element = None
    for sel in PRO_SELECTORS:
        try:
            pro_element = wait_for(driver, By.CSS_SELECTOR, sel, timeout=WAIT_SHORT, condition="clickable")
            break
        except TimeoutException:
            continue

    if pro_element is None:
        log.error("Could not find the PRO nav item (tried: %s).", PRO_SELECTORS)
        raise RuntimeError("PRO nav item not found")

    safe_click(driver, pro_element)
    log.info("Clicked PRO.")

    # --- Click Product Viewer sub-item ---
    # Confirmed from live DOM:
    #   <a href="#!viewer"><span>Product Viewer</span></a>
    PRODUCT_VIEWER_SELECTORS = [
        "a[href='#!viewer']",  # exact href — most reliable
    ]

    pv_element = None
    for sel in PRODUCT_VIEWER_SELECTORS:
        try:
            pv_element = wait_for(driver, By.CSS_SELECTOR, sel, timeout=WAIT_SHORT, condition="clickable")
            break
        except TimeoutException:
            continue

    if pv_element is None:
        log.error("Could not find 'Product Viewer' (tried: %s).", PRODUCT_VIEWER_SELECTORS)
        raise RuntimeError("Product Viewer item not found")

    safe_click(driver, pv_element)
    log.info("Clicked Product Viewer.")

    # Wait for Product Viewer UI to load
    # TODO: Replace this with a wait for a stable element inside Product Viewer,
    #       e.g., the list-type radio buttons or the text input area.
    WebDriverWait(driver, WAIT_MEDIUM).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    time.sleep(1)


# ---------------------------------------------------------------------------
# Step 7 — Select list type (ASIN or UPC/EAN/GTIN)
# ---------------------------------------------------------------------------

def select_list_type(driver: webdriver.Chrome, list_type: str):
    """
    Choose between the ASIN and EAN/UPC radio buttons in the Product Viewer form.

    Confirmed from live DOM:
        ASIN  → <input type="radio" id="asinCh-radio" name="type">
        EAN   → <input type="radio" id="upcCh-radio"  name="type">

    Note: the radio inputs are MDC-styled and may be visually hidden behind a
    ripple overlay. We click via JavaScript if a normal click is intercepted.
    """
    log.info("Selecting list type: %s", list_type)

    radio_id = "asinCh-radio" if list_type == "ASIN" else "upcCh-radio"
    element = wait_for(driver, By.CSS_SELECTOR, f"#{radio_id}", timeout=WAIT_MEDIUM, condition="present")

    # MDC radio buttons are often covered by a sibling span; use JS click to be safe.
    driver.execute_script("arguments[0].click();", element)
    log.info("List type '%s' selected (#%s).", list_type, radio_id)


# ---------------------------------------------------------------------------
# Step 8 — Paste the list into the input area
# ---------------------------------------------------------------------------

def _copy_to_clipboard(text: str):
    """Copy text to the OS clipboard using native tools (no extra dependencies)."""
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
    elif system == "Windows":
        subprocess.run(["clip"], input=text.encode("utf-16"), check=True)
    else:
        for cmd in [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
            try:
                subprocess.run(cmd, input=text.encode("utf-8"), check=True)
                return
            except FileNotFoundError:
                continue
        raise RuntimeError("No clipboard utility found on Linux — install xclip or xsel.")


def paste_list(driver: webdriver.Chrome, values: list[str]):
    """
    Enter the identifiers into the Product Viewer input field.

    Confirmed from live DOM:
        <input type="text" id="importInputUpc" class="mdc-text-field__input"
               pattern=".*(([BC][A-Z0-9]{9}|\\d{9}(!?X|\\d))).*" name="text">

    Despite the id name, this same field is used for both ASINs and EAN/UPC codes
    (the active radio button controls how Keepa interprets the input).

    Values are joined with newlines and pasted via the system clipboard.
    Direct JS value-injection strips newlines from <input type="text"> elements,
    causing all EAN codes to concatenate into one string — Keepa then mis-parses
    the boundaries and digits appear to "shift" between adjacent codes.
    """
    log.info("Pasting %d values into the identifier input field.", len(values))

    INPUT_SELECTORS = [
        "#importInputAsin",
        "#importInputUpc",
        "#importInputEan",
        "#importInputGtin",
        "#importInput",
        "form input.mdc-text-field__input[type='text']",
        "input.mdc-text-field__input[type='text']",
    ]
    field = None
    for sel in INPUT_SELECTORS:
        try:
            field = wait_for(driver, By.CSS_SELECTOR, sel, timeout=WAIT_SHORT, condition="clickable")
            log.info("Found input field via selector: %s", sel)
            break
        except TimeoutException:
            continue
    if field is None:
        raise RuntimeError("Could not find the list input field — share the EAN input element so we can lock in its selector")

    text = "\n".join(values)
    _copy_to_clipboard(text)

    driver.execute_script("arguments[0].focus();", field)
    time.sleep(0.2)

    mod = Keys.COMMAND if platform.system() == "Darwin" else Keys.CONTROL
    ActionChains(driver).key_down(mod).send_keys("a").key_up(mod).perform()
    time.sleep(0.1)
    ActionChains(driver).key_down(mod).send_keys("v").key_up(mod).perform()
    time.sleep(0.3)

    log.info("Values pasted via clipboard successfully.")


# ---------------------------------------------------------------------------
# Step 9 — Click LOAD LIST
# ---------------------------------------------------------------------------

def click_load_list(driver: webdriver.Chrome):
    """
    Click the Load List button to submit the identifiers.

    Confirmed from live DOM:
        <button id="importSubmit" class="mdc-button mdc-button--raised ...">Load List</button>
    """
    log.info("Clicking Load List.")

    element = wait_for(driver, By.CSS_SELECTOR, "#importSubmit", timeout=WAIT_MEDIUM, condition="clickable")
    safe_click(driver, element)
    log.info("Load List clicked. Waiting for results to load…")

    # Wait for the button to become clickable again as a proxy for load completion.
    # TODO: Once you can inspect the results table that appears after loading,
    #       replace this with a wait on that table's selector for a tighter signal.
    try:
        WebDriverWait(driver, WAIT_LONG).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#importSubmit"))
        )
        log.info("Loading complete.")
    except TimeoutException:
        log.info("Load timeout — continuing anyway.")
        time.sleep(3)


# ---------------------------------------------------------------------------
# Step 10 — Dismiss 'Search result' popup
# ---------------------------------------------------------------------------

def dismiss_search_result_popup(driver: webdriver.Chrome):
    """
    Wait for the 'Search result' popup and close it.

    Confirmed from live DOM:
        Overlay:     <div class="hidden generalOverlay" style="display: block;">
        Title:       <div id="popupTitle4">Search result</div>
        Close button: <div id="shareChartOverlay-close4"><i class="fa fa-times-circle fa-2x"></i></div>

    The overlay is always rendered in the DOM but hidden; Keepa sets
    display:block via inline style when it activates it, so we wait for
    visibility rather than presence.
    """
    log.info("Waiting up to %ds for 'Search result' popup…", WAIT_LONG)
    try:
        # Wait for the overlay to become visible
        WebDriverWait(driver, WAIT_LONG).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.generalOverlay"))
        )
        log.info("'Search result' popup appeared.")

        # Click the confirmed close button
        close_btn = wait_for(
            driver, By.CSS_SELECTOR, "#shareChartOverlay-close4",
            timeout=WAIT_SHORT, condition="clickable",
        )
        driver.execute_script("arguments[0].click();", close_btn)
        log.info("Dismissed 'Search result' popup.")

        # Wait for the overlay to disappear before continuing
        WebDriverWait(driver, WAIT_SHORT).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.generalOverlay"))
        )
    except TimeoutException:
        log.info("No popup appeared — continuing.")


# ---------------------------------------------------------------------------
# Step 11 — Click EXPORT and wait for download
# ---------------------------------------------------------------------------

def click_export_and_wait(driver: webdriver.Chrome, download_dir: str) -> str:
    """
    Click the Export button and wait for the file to download.
    Returns the path of the downloaded file.

    Confirmed from live DOM:
        <span class="trigger">
            <i class="fa fa-download fa-lg"></i> Export
        </span>

    We target the icon inside to be maximally specific, then click the
    parent span.trigger via JavaScript so the event fires on the right element.
    """
    log.info("Capturing existing files in download directory before export.")
    before_files = set(Path(download_dir).glob("*"))

    # Find the download icon inside the trigger span, then click its parent.
    icon = wait_for(
        driver,
        By.CSS_SELECTOR,
        "span.trigger i.fa-download",
        timeout=WAIT_MEDIUM,
        condition="present",
    )
    trigger = driver.execute_script("return arguments[0].closest('span.trigger');", icon)
    if trigger is None:
        raise RuntimeError("Export span.trigger not found — could not climb from fa-download icon")

    driver.execute_script("arguments[0].click();", trigger)
    log.info("Export popup opened.")

    # Confirmed from live DOM: a confirmation popup appears with:
    #   <button id="exportSubmit" class="mdc-button mdc-button--raised ...">Export</button>
    # Click it to actually start the download.
    confirm_btn = wait_for(driver, By.CSS_SELECTOR, "#exportSubmit", timeout=WAIT_MEDIUM, condition="clickable")
    driver.execute_script("arguments[0].click();", confirm_btn)
    log.info("Export confirmed. Waiting for download to complete (up to %ds)…", WAIT_LONG)

    downloaded = wait_for_download(download_dir, before_files, timeout=WAIT_LONG)
    if downloaded:
        log.info("Download complete: %s", downloaded)
        return downloaded
    else:
        log.error("Download did not complete within %d seconds.", WAIT_LONG)
        raise RuntimeError("Download timed out")


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def run(csv_path: str, output_dir: str, marketplace: str = "FR", column: str | None = None, no_wait: bool = False):
    driver = None
    try:
        # --- Load and clean the CSV ---
        values = load_csv(csv_path, column=column)
        if not values:
            log.error("No values found in CSV. Exiting.")
            sys.exit(1)

        # --- Detect list type ---
        list_type = detect_list_type(values)

        # --- Launch browser ---
        driver = create_driver(output_dir)

        # Force silent downloads in incognito (prefs are ignored there)
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": str(Path(output_dir).resolve()),
        })

        # --- Login ---
        ensure_logged_in(driver)

        # --- Select marketplace ---
        select_marketplace(driver, marketplace)

        # --- Navigate to PRO → Product Viewer ---
        navigate_to_product_viewer(driver)

        # --- Select list type ---
        select_list_type(driver, list_type)

        # --- Paste the list ---
        paste_list(driver, values)

        # --- Click LOAD LIST ---
        click_load_list(driver)

        # --- Dismiss popup (optional) ---
        dismiss_search_result_popup(driver)

        # --- Export ---
        downloaded_file = click_export_and_wait(driver, output_dir)

        print(f"\n✓ Export complete.\n  File saved to: {downloaded_file}\n")

    except Exception as exc:
        log.error("Script failed: %s", exc, exc_info=True)
        if driver:
            take_screenshot(driver, "fatal_error", output_dir)
        sys.exit(1)

    finally:
        if driver:
            if not no_wait:
                log.info("Keeping browser open for inspection. Close it manually when done.")
                input("Press Enter to close the browser → ")
            driver.quit()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Keepa.com Product Viewer automation — exports data for a list of ASINs or barcodes."
    )
    parser.add_argument(
        "--csv",
        required=True,
        help="Path to the CSV file containing ASINs or UPC/EAN/GTIN codes (first column used).",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Directory where the exported file will be saved.",
    )
    parser.add_argument(
        "--marketplace",
        default="FR",
        choices=list(MARKETPLACE_MAP.keys()),
        help="Keepa marketplace code (default: FR for Amazon France).",
    )
    parser.add_argument(
        "--column",
        default=None,
        help="Column to read from the CSV — header name (e.g. 'Code EAN') or 0-based index (e.g. '3'). "
             "Auto-detected from header keywords if omitted.",
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        dest="no_wait",
        help="Skip terminal prompts — used when called from the Flask server.",
    )
    args = parser.parse_args()

    run(csv_path=args.csv, output_dir=args.output, marketplace=args.marketplace,
        column=args.column, no_wait=args.no_wait)
