# driver_factory.py
import os, shutil, tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def make_driver(headless=True):
    opts = Options()

    # Headless is usually faster/stabler in WSL
    if headless:
        for a in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"):
            opts.add_argument(a)
    else:
        for a in ("--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"):
            opts.add_argument(a)

    # Load earlier: stop waiting for every subresource
    opts.page_load_strategy = "eager"   # "none" also works, but "eager" is a nice balance

    # Less-automated look
    opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--disable-blink-features=AutomationControlled")

    # Kill password/autofill UI
    opts.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "autofill.profile_enabled": False,
        "autofill.credit_card_enabled": False,
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.cookies": 1,
    })
    opts.add_argument("--disable-features=AutofillServerCommunication,PasswordManagerOnboarding")

    # Fresh ephemeral profile
    tmp_profile = tempfile.mkdtemp(prefix="chrome-profile-")
    opts.add_argument(f"--user-data-dir={tmp_profile}")

    # Normal UA
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")

    # Chrome binary for WSL
    chrome_bin = os.getenv("CHROME_BIN") or shutil.which("google-chrome") or shutil.which("google-chrome-stable")
    if chrome_bin:
        opts.binary_location = chrome_bin

    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(120)   # give navigation breathing room
    driver.set_script_timeout(30)
    driver.implicitly_wait(0)
    return driver