import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def _to_float(s):
    if not s: return None
    m = re.search(r"\d+(?:\.\d+)?", s.replace(",", ""))
    return float(m.group()) if m else None

def _to_int(s):
    if not s: return None
    m = re.search(r"\d+", s.replace(",", ""))
    return int(m.group()) if m else None

def _text_or_none(node, by, value):
    try:
        return node.find_element(by, value).text.strip()
    except Exception:
        return None

def scrape_performance_table(driver, wait):
    # Anchor on the table container (don’t rely on the exact hash)
    table = wait.until(EC.presence_of_element_located((
        By.XPATH,
        "//div[contains(@class,'performance-table') and .//div[normalize-space()='Category Score']]"
    )))

    # **Only** cells that actually contain a category name
    cells = table.find_elements(
        By.XPATH,
        ".//div[contains(@class,'performance-table__cell') and "
        ".//div[contains(@class,'category-data__name')]]"
    )

    out = []
    for cell in cells:
        # Left column
        name = _text_or_none(cell, By.XPATH, ".//div[contains(@class,'category-data__name')]")
        score_txt = _text_or_none(cell, By.XPATH, ".//div[contains(@class,'category-data__value')]")
        score = _to_float(score_txt)

        # Middle column (percentile)
        pct_txt = _text_or_none(
            cell, By.XPATH,
            ".//div[contains(@class,'industry-percentile')]//*[contains(.,'%')]"
        )
        percentile = _to_float(pct_txt)

        # Right column (rank)
        rank_txt = _text_or_none(
            cell, By.XPATH,
            ".//div[contains(@class,'industry-data')]//*[contains(normalize-space(),'#')]"
        )
        rank = _to_int(rank_txt or "")

        out.append({
            "category": name,
            "score": score,
            "industry_percentile": percentile,
            "industry_rank": rank,
        })

    return out
