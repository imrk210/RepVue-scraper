import re

def extract_company_url  (driver):  
    overview_url = driver.current_url

    cleaned_comp = re.search(r"/companies/([^/?#]+)", overview_url)
    company = cleaned_comp.group(1) if cleaned_comp else None
    return company