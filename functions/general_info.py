import re, math
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def _text_of(driver, el):
    # headless-safe text
    txt = (el.text or "").strip()
    if not txt:
        txt = (driver.execute_script(
            "return (arguments[0].innerText || arguments[0].textContent || '').trim();", el
        ) or "").strip()
    return txt

def _first_present(driver, wait, locators, timeout_each=4):
    """Try locators in order; return first present element or None."""
    for how, sel in locators:
        try:
            return WebDriverWait(driver, timeout_each).until(
                EC.presence_of_element_located((how, sel))
            )
        except TimeoutException:
            continue
    return None

def scrape_company_size_and_trend(driver, wait):
    """Scrape company size (currentCount) and trend percentage dynamically."""
    # Locate the current size element directly (dynamic class substring)
    try:
        size_el = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='_currentCount']"))
        )
        size_txt = _text_of(driver, size_el)
        current_size = int(re.sub(r"[^\d]", "", size_txt)) if size_txt else None
    except TimeoutException:
        current_size = None

    # Trend (percentage up/down, optional)
    try:
        trend_el = driver.find_element(By.CSS_SELECTOR, "div[class*='_trend']")
        trend_txt = _text_of(driver, trend_el)
        m = re.search(r"([+\-−]?\d+(?:\.\d+)?)\s*%", trend_txt)
        trend_pct = float(m.group(1).replace("−", "-")) if m else None
    except Exception:
        trend_pct = None

    return {"current_size": current_size, "trend_pct": trend_pct}

def scrape_employee_ratings(driver, wait: WebDriverWait, timeout=8):
    """Scrape employee ratings count from `_ratings_employees`."""
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='_ratings_employees']"))
        )
        txt = _text_of(driver, el)  # e.g. "3,612 Employee Ratings"
        m = re.search(r"\d[\d,]*", txt)
        return int(m.group(0).replace(",", "")) if m else None
    except TimeoutException:
        # Fallback: search full page text
        body_txt = (driver.find_element(By.TAG_NAME, "body").get_attribute("textContent") or "")
        m = re.search(r"(\d[\d,]*)\s*Employee Ratings", body_txt, re.I)
        return int(m.group(1).replace(",", "")) if m else None

def scrape_general_info(driver, wait):
    general_info = {}

    # 0) Make sure the company page is actually loaded (header/title present)
    wait.until(EC.any_of(
        EC.presence_of_element_located((By.CSS_SELECTOR, "h1")),
        EC.url_contains("/comp")  # tolerant for /companies/<slug> routes
    ))

    # 1) RepVue Score (unchanged)
    score_el = _first_present(driver, wait, [
        (By.XPATH, "//*[self::h5 or self::h4][contains(.,'RepVue Score')]/following::*[self::h1 or self::h2 or self::div][1]"),
        (By.XPATH, "//*[contains(.,'RepVue Score')]/following::*[self::h1 or self::h2 or self::div][1]"),
    ])
    if score_el:
        raw = _text_of(driver, score_el)
        m = re.search(r"\d+(?:[.,]\d+)?", raw)
        general_info['RepVue score'] = float(m.group(0).replace(",", ".")) if m else None
    else:
        general_info['RepVue score'] = None

    # 2) Star rating — FIRST find the stars container, THEN its adjacent rating
    #    avoids picking up "Employee Ratings" count.
    rating = None
    try:
        # stars container, e.g. <div class="...__stars"> ... </div>
        stars_el = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='__stars']"))
        )

        # rating is the immediate following sibling with class __rating
        # search relative to stars to avoid unrelated _rating nodes
        try:
            rating_el = stars_el.find_element(
                By.XPATH, "following-sibling::div[contains(@class,'__rating')][1]"
            )
        except Exception:
            # fallback: look within the same parent container
            container = stars_el.find_element(By.XPATH, "ancestor::div[1]")
            rating_el = container.find_element(By.CSS_SELECTOR, "div[class*='__rating']")

        txt = _text_of(driver, rating_el)
        # accept only values in the plausible rating range
        nums = re.findall(r"\d+(?:[.,]\d+)?", txt)
        for s in nums:
            v = float(s.replace(",", "."))
            if 0 < v <= 5.0:
                rating = v
                break
    except TimeoutException:
        rating = None
    general_info['star_rating'] = rating

    # 3) Employee ratings (N) — unchanged
    general_info['Employee ratings (N)'] = scrape_employee_ratings(driver, wait)

    # 4) Company size + trend — unchanged
    general_info.update(scrape_company_size_and_trend(driver, wait))

    return general_info
