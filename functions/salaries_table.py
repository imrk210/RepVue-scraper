from selenium.webdriver.support.ui import WebDriverWait

def scrape_salaries_table(driver, wait: WebDriverWait, timeout=12):
    """
    Scrape the salaries overview in one JS shot.
    Returns a list of dicts with:
      role, ratings_count,
      median_base_pay, median_base_pay_is_range, median_base_pay_min, median_base_pay_max,
      median_ote,       median_ote_is_range,       median_ote_min,       median_ote_max,
      top_performers,   top_performers_is_range,   top_performers_min,   top_performers_max,
      quota_attainment_pct, link

    NOTE:
    - For *_is_range == True, the singular field is the midpoint of [min,max].
    - For single values, *_min == *_max == value and *_is_range == False.
    """
    js = r"""
    const norm = s => (s||"").replace(/\s+/g," ").trim();
    const lc   = s => norm(s).toLowerCase();

    // Parse "$120k", "120,000", "$1.2m", etc. -> integer (USD-like, but unit-agnostic).
    function tokenToInt(tok){
      if (!tok) return null;
      tok = tok.replace(/[$,]/g,"").trim().toLowerCase();
      const m = tok.match(/^(\d+(?:\.\d+)?)([kmb])?$/i);
      if (!m) return null;
      let n = parseFloat(m[1]);
      const unit = (m[2]||"").toLowerCase();
      if (unit === "k") n *= 1e3;
      else if (unit === "m") n *= 1e6;
      else if (unit === "b") n *= 1e9;
      return Math.round(n);
    }

    // Extract one or more money tokens from a string; supports ranges:
    // "$120k–$140k", "$120k - 140k", "120,000 to 140,000"
    function parseMoneyOrRange(s){
      if (!s) return {value:null, is_range:false, min:null, max:null};
      const cleaned = s.replace(/[^\d\.\-,kmb$–—\s]/gi, s => s); // keep most separators
      // Match money tokens with optional unit; allow forms like "$120k" or "140k"
      const re = /\$?\s*\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*[kmb]?/gi;
      const tokens = (cleaned.match(re) || []).map(t => tokenToInt(t)).filter(n => Number.isFinite(n));
      if (tokens.length === 0) {
        return {value:null, is_range:false, min:null, max:null};
      }
      let min = Math.min(...tokens);
      let max = Math.max(...tokens);
      const is_range = (tokens.length >= 2 && min !== max);
      if (!is_range){
        min = max = tokens[0];
      }
      const mid = Math.round((min + max) / 2);
      return {value: mid, is_range, min, max};
    }

    // Candidate rows = anchors that link to a role under /companies/.../salaries/...
    const candidates = [...document.querySelectorAll("a[href^='/companies/'][href*='/salaries/']")];

    // Keep only the rows that look like salary rows (contain "Salary data from")
    const rows = candidates.filter(a => /salary data from/i.test(a.textContent));

    function valueBlockAfterLabel(root, label){
      // Find a label <span> containing the label (case-insensitive, substring)
      const spans = [...root.querySelectorAll("span")];
      const lab = spans.find(s => lc(s.textContent).includes(lc(label)));
      const vEl = lab ? lab.nextElementSibling : null;
      return vEl ? norm(vEl.textContent) : null;
    }

    function extractMonetary(root, label){
      const raw = valueBlockAfterLabel(root, label);
      const p = parseMoneyOrRange(raw);
      return {
        value: p.value,
        is_range: p.is_range,
        min: p.min,
        max: p.max,
        raw: raw
      };
    }

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

      // Monetary fields (handle single or range)
      const base = extractMonetary(a, "Base Pay");
      const ote  = extractMonetary(a, "OTE");
      const top  = extractMonetary(a, "Top Performers");

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

        // Backward-compatible single-number fields (midpoint if range)
        median_base_pay: base.value,
        median_ote: ote.value,
        top_performers: top.value,

        // Range metadata
        median_base_pay_is_range: base.is_range,
        median_base_pay_min: base.min,
        median_base_pay_max: base.max,

        median_ote_is_range: ote.is_range,
        median_ote_min: ote.min,
        median_ote_max: ote.max,

        top_performers_is_range: top.is_range,
        top_performers_min: top.min,
        top_performers_max: top.max,

        quota_attainment_pct: quota,
        link: a.href
      };
    });
    """

    try:
        data = WebDriverWait(driver, timeout, poll_frequency=0.2).until(
            lambda d: (lambda r: r if r is not None else [])(d.execute_script(js))
        )
    except Exception:
        data = []

    return [r for r in data if r.get("role")]
