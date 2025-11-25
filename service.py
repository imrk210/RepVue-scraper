# service.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

# use your existing driver factory
from functions.make_driver import make_driver

# reuse your existing helpers
from functions.login import login_repVue
from functions.search_company import search_company
from functions.company_url_path import extract_company_url
from functions.navigate_link import navigation
from functions.general_info import scrape_general_info
from functions.performance_info import scrape_performance_table
from functions.salaries_table import scrape_salaries_table


@dataclass
class RepVueService:
    driver: WebDriver
    timeout: int = 20

    def __post_init__(self):
        self.wait = WebDriverWait(self.driver, self.timeout)

    # ---- factory that uses your existing make_driver() ----
    @classmethod
    def create(cls) -> "RepVueService":
        """RepVueService.create(headless=True, browser='chrome', ...) -> service"""
        drv = make_driver()
        return cls(drv)

    # ---- high-level actions ----
    def login(self, email: str, password: str) -> str:
        return login_repVue(self.driver, email, password, timeout=self.timeout)

    def search(self, company_name: str, timeout: Optional[int] = None) -> str:
        w = self.wait if timeout is None else WebDriverWait(self.driver, timeout)
        url = search_company(self.driver, w, company_name)
        return url

    def company_slug(self) -> Optional[str]:
        return extract_company_url(self.driver)

    def go(self, page: str = None, company: Optional[str] = None) -> None:
        """page: 'salaries', 'reviews', etc. company is slug; if None, inferred from URL."""
        slug = company or self.company_slug()
        if not slug:
            raise RuntimeError("No company slug found. Run search() first or pass company='Slug'.")
        navigation(self.driver, self.wait, slug, page)

    # ---- scrapers ----
    def general_info(self) -> Dict[str, Any]:
        return scrape_general_info(self.driver, self.wait)

    def performance(self) -> Dict[str, Any]:
        return scrape_performance_table(self.driver, self.wait)

    def salaries(self) -> List[Dict[str, Any]]:
        return scrape_salaries_table(self.driver, self.wait)

    # ---- lifecycle ----
    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass

    def __enter__(self) -> "RepVueService":
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
