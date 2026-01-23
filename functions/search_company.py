from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, WebDriverException
import time, re

class CompanyNotFound(Exception):
    pass

def _safe_click(driver, el):
    try:
        el.click(); return
    except Exception:
        pass
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        el.click(); return
    except (ElementClickInterceptedException, WebDriverException):
        driver.execute_script("arguments[0].click();", el)

def _open_search(driver, timeout):
    w = WebDriverWait(driver, timeout)
    w.until(lambda d: d.execute_script("return document.readyState") == "complete")
    for how, sel in [
        (By.CSS_SELECTOR, "div[class*='searchMobile']"),
        (By.XPATH,
         "//*[self::a or self::div or self::button]"
         "[contains(@class,'Navbar_search') or "
         " normalize-space()='Search Companies' or "
         " .//span[normalize-space()='Search Companies']]")
    ]:
        try:
            el = w.until(EC.presence_of_element_located((how, sel)))
            _safe_click(driver, el)
            return
        except TimeoutException:
            continue
    raise TimeoutException("Search control not found (searchMobile / Search Companies)")

def search_company(driver, wait: WebDriverWait, company_name: str, timeout: int = 10):
    w = WebDriverWait(driver, timeout)
    name = company_name.strip()
    lname = name.lower()

    # Ensure we are on /companies
    if "/companies" not in driver.current_url:
        driver.get("https://www.repvue.com/companies")
        w.until(lambda d: d.execute_script("return document.readyState") == "complete")

    # Open search dialog
    _open_search(driver, timeout)

    # Wait for dialog visible & find the input
    w.until(EC.visibility_of_element_located(
        (By.XPATH, "//div[@role='dialog' and not(contains(@style,'display: none'))]"))
    )
    try:
        search_input = w.until(EC.element_to_be_clickable((
            By.XPATH,
            "//div[@role='dialog']//input[(@type='text' or not(@type))]"
        )))
    except TimeoutException:
        raise TimeoutException("Search input not found")

    # Type query & give SPA a moment
    search_input.clear()
    search_input.send_keys(company_name)
    time.sleep(0.8)

    # Wait for at least one result row to appear
    w.until(EC.presence_of_element_located((
        By.XPATH, "//div[@role='dialog']//a[contains(@href,'/companies/')]"
    )))
    results = driver.find_elements(
        By.XPATH, "//div[@role='dialog']//a[contains(@href,'/companies/')]"
    )
    if not results:
        # explicit empty state?
        empty = driver.find_elements(By.XPATH,
            "//div[@role='dialog']//*[contains(.,'No results') or contains(.,'No companies')]"
        )
        if empty:
            raise CompanyNotFound(f"Company not found on RepVue: {company_name}")
        raise TimeoutException("Search results did not render")

    # ---------- EXACT MATCH FIRST ----------
    def first_line(el):
        txt = (el.get_attribute("textContent") or "").strip()
        # Use the first non-empty line as the title line
        for line in [t.strip() for t in re.split(r"[\r\n]+", txt) if t.strip()]:
            return line
        return txt

    exact = None
    for el in results:
        title = (first_line(el) or "").strip()
        if title.lower() == lname:  # exact case-insensitive match on the title line
            exact = el
            break

    target = exact
    if not target:
        # Fallback: pick the first reasonable partial where the title line starts with the name
        starts = [el for el in results if (first_line(el) or "").lower().startswith(lname)]
        if starts:
            target = starts[0]
        else:
            # Last resort: first result containing the name anywhere
            contains = [el for el in results if lname in (el.get_attribute("textContent") or "").lower()]
            target = contains[0] if contains else None

    if not target:
        raise CompanyNotFound(f"Company not found on RepVue: {company_name}")

    _safe_click(driver, target)

    # Confirm navigation
    w.until(EC.url_contains("/companies/"))
    return driver.current_url
