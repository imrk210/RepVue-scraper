from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait

def _safe_click(driver, el):
    try:
        el.click()
        return
    except Exception:
        pass
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        el.click()
        return
    except (ElementClickInterceptedException, WebDriverException):
        driver.execute_script("arguments[0].click();", el)

def login_repVue(driver, email, password, timeout=15):
    w = WebDriverWait(driver, timeout)
    driver.get("https://www.repvue.com/login")

    # 1. Dismiss cookie / consent banners
    try:
        btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(.,'Accept') or contains(.,'Got it') or contains(.,'Agree') or contains(.,'OK')]"
            ))
        )
        _safe_click(driver, btn)
    except TimeoutException:
        pass  # no banner

    # 2. Wait for form fields
    email_el = w.until(EC.visibility_of_element_located((By.ID, "email-sign-in")))
    email_el.clear()
    email_el.send_keys(email)

    pwd_el = w.until(EC.visibility_of_element_located((By.ID, "password-field")))
    pwd_el.clear()
    pwd_el.send_keys(password)
    pwd_el.send_keys(Keys.TAB)

    # 3. Click submit
    try:
        submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    except Exception:
        submit = driver.find_element(By.XPATH, "//button[normalize-space()='Sign In' or normalize-space()='Log In']")

    _safe_click(driver, submit)

    # 4. Wait for post-login confirmation
    try:
        WebDriverWait(driver, 20).until(
            EC.any_of(
                EC.url_contains("/dashboard"),
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='searchMobile']")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='Navbar']"))
            )
        )
    except TimeoutException:
        # Save artifacts for debugging
        driver.save_screenshot("/tmp/login_fail.png")
        with open("/tmp/login_fail.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        raise TimeoutException("Login did not complete — check /tmp/login_fail.png and .html")

    return driver.current_url
