from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def navigation(driver, wait, company, page):
    try:
        # FIXED selector (closed quote)
        link = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR, f"a[href$='/companies/{company}/{page}']"
        )))
        driver.execute_script("arguments[0].click();", link)
    except TimeoutException:
        # Fallback: navigate directly (SPA-safe)
        driver.get(f"https://www.repvue.com/companies/{company}/{page}")

    # Robust URL wait (allows trailing slash or extras)
    wait.until(EC.url_matches(rf"/companies/[^/]+/{page}(?:/|$)"))
