from selenium.webdriver.support.ui import WebDriverWait

def scrape_salaries_table(driver, wait: WebDriverWait, timeout=12):
    """
    Scrape the salaries overview in one JS shot.
    Returns a list of dicts with:
      role, ratings_count, median_base_pay, median_ote, top_performers, quota_attainment_pct, link
    """
    js = r"""
    const norm = s => (s||"").replace(/\s+/g," ").trim();
    const lc   = s => norm(s).toLowerCase();
    const moneyToInt = (s) => {
      s = (s||"").replace(/[$,]/g,"").toLowerCase();
      const m = s.match(/(\d+(?:\.\d+)?)([km]?)/);
      if (!m) return null;
      let n = parseFloat(m[1]);
      if (m[2]==="k") n*=1000;
      else if (m[2]==="m") n*=1000000;
      return Math.round(n);
    };

    // Candidate rows = anchors that link to a role under /companies/.../salaries/...
    const candidates = [...document.querySelectorAll("a[href^='/companies/'][href*='/salaries/']")];

    // Keep only the rows that look like salary rows (contain "Salary data from")
    const rows = candidates.filter(a => /salary data from/i.test(a.textContent));

    return rows.map(a => {
      // Role: text up to "Salary data from"
      let role = null;
      const cell = a.querySelector("div"); // first block in the row
      const cellText = norm(cell ? cell.textContent : a.textContent);
      const mRole = cellText.match(/^(.*?)\s*salary data from/i);
      if (mRole) role = norm(mRole[1]);

      // Ratings
      let ratings_count = null;
      const mRatings = cellText.match(/salary data from\s+(\d[\d,]*)\s+ratings?/i);
      if (mRatings) ratings_count = parseInt(mRatings[1].replace(/,/g,""));

      // Monetary cols: find span labels "Base Pay" / "OTE" / "Top Performers" and take next sibling
      function valByLabel(label){
        const lab = [...a.querySelectorAll("span")]
          .find(s => lc(s.textContent) === lc(label));
        const vEl = lab ? lab.nextElementSibling : null;
        return vEl ? moneyToInt(vEl.textContent) : null;
      }
      const base = valByLabel("Base Pay");
      const ote  = valByLabel("OTE");
      const top  = valByLabel("Top Performers");

      // Quota: prefer aria-valuenow; fallback to parsing "%"
      let quota = null;
      const pb = a.querySelector("[role='progressbar']");
      if (pb && pb.getAttribute("aria-valuenow")) {
        quota = parseFloat(pb.getAttribute("aria-valuenow"));
      } else {
        const qtxt = a.textContent;
        const mq = qtxt && qtxt.match(/(\d+(?:\.\d+)?)\s*%/);
        if (mq) quota = parseFloat(mq[1]);
      }

      return {
        role,
        ratings_count,
        median_base_pay: base,
        median_ote: ote,
        top_performers: top,
        quota_attainment_pct: quota,
        link: a.href
      };
    });
    """

    # Wait until the JS can actually see rows (or return empty if none after timeout)
    try:
        data = WebDriverWait(driver, timeout, poll_frequency=0.2).until(
            lambda d: (lambda r: r if r is not None else [])(d.execute_script(js))
        )
    except Exception:
        data = []

    # Filter out any null roles (stray anchors)
    return [r for r in data if r.get("role")]
