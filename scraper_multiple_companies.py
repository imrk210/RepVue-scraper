import os
import time
import pandas as pd
from dotenv import load_dotenv
from service import RepVueService
from functions.exceptions import CompanyNotFound

# -------------------- CONFIG --------------------
load_dotenv()

email_id = os.getenv("REPVUE_EMAIL")
password = os.getenv("REPVUE_PASS")

companies = [
    "Salesforce", "Trimble Inc.", "Hubspot"
]
output_file = "repvue_data.xlsx"


# -------------------- HELPERS --------------------
def safe_sheet_name(name: str, suffix: str) -> str:
    """Excel sheet name limit is 31 chars and cannot contain: : \ / ? * [ ]"""
    bad = {":", "\\", "/", "?", "*", "[", "]"}
    base = "".join(ch for ch in name if ch not in bad).strip() or "Sheet"
    max_base_len = 31 - (len(suffix) + 1)
    base = base[:max_base_len] if max_base_len > 0 else base[:25]
    return f"{base}_{suffix}"


def to_df_info(info: dict) -> pd.DataFrame:
    return pd.DataFrame([info]) if info else pd.DataFrame()


def to_df_perf(perf) -> pd.DataFrame:
    """Flatten list[dict] or dict to table."""
    if not perf:
        return pd.DataFrame()
    if isinstance(perf, list):
        df = pd.DataFrame(perf)
    elif isinstance(perf, dict):
        df = pd.DataFrame([perf])
    else:
        return pd.DataFrame()

    order = ["category", "score", "industry_percentile", "industry_rank"]
    cols = [c for c in order if c in df.columns] + [c for c in df.columns if c not in order]
    return df[cols]


def to_df_salaries(salaries) -> pd.DataFrame:
    """Handle list[list] or list[dict]."""
    if not salaries:
        return pd.DataFrame()
    if isinstance(salaries[0], dict):
        return pd.DataFrame(salaries)
    return pd.DataFrame(salaries)


# -------------------- MAIN --------------------
try:
    with RepVueService.create() as svc:
        svc.driver.get("https://www.repvue.com/login")
        svc.login(email_id, password)
        print("Login successful.")

        with pd.ExcelWriter(output_file, engine="openpyxl", mode="w") as writer:
            wrote_any_sheet = False
            summary_rows = []

            for company in companies:
                print(f"\n🔍 Processing {company}...")
                start = time.time()

                try:
                    url = svc.search(company)
                    print("Navigated to:", url)
                except CompanyNotFound:
                    print(f"❌ Company '{company}' not found. Skipping.")
                    summary_rows.append({"company": company, "status": "Not Found"})
                    continue

                # Wait briefly for page load; replace with svc wait if available
                time.sleep(1)

                info = svc.general_info() or {}
                perf = svc.performance() or {}

                salaries = []
                slug = svc.company_slug()
                if slug:
                    svc.go("salaries", slug)
                    salaries = svc.salaries() or []

                # Convert to DataFrames (tabular)
                df_info = pd.DataFrame([info]) if info else pd.DataFrame()

                # Flatten performance data: list[dict] → DataFrame
                if isinstance(perf, list):
                    df_perf = pd.DataFrame(perf)
                elif isinstance(perf, dict):
                    df_perf = pd.DataFrame([perf])
                else:
                    df_perf = pd.DataFrame()

                # Flatten salaries if it's list-of-lists or list-of-dicts
                if salaries:
                    if isinstance(salaries[0], dict):
                        df_salaries = pd.DataFrame(salaries)
                    else:
                        df_salaries = pd.DataFrame(salaries)
                else:
                    df_salaries = pd.DataFrame()


                # Write to Excel sheets
                if not df_info.empty:
                    df_info.to_excel(writer, sheet_name=safe_sheet_name(company, "Info"), index=False)
                    wrote_any_sheet = True
                if not df_perf.empty:
                    df_perf.to_excel(writer, sheet_name=safe_sheet_name(company, "Perf"), index=False)
                    wrote_any_sheet = True
                if not df_salaries.empty:
                    df_salaries.to_excel(writer, sheet_name=safe_sheet_name(company, "Salaries"), index=False)
                    wrote_any_sheet = True

                summary_rows.append({
                    "company": company,
                    "url": svc.driver.current_url,
                    "info_keys": len(df_info.columns),
                    "perf_rows": len(df_perf),
                    "salary_rows": len(df_salaries),
                    "seconds": round(time.time() - start, 2),
                })

                print(f"✅ Saved {company} (Info/Perf/Salaries)")

            # Fallback if nothing written
            if not wrote_any_sheet:
                pd.DataFrame({"Status": ["No valid data scraped"]}).to_excel(
                    writer, sheet_name="Empty", index=False
                )

            # Add summary sheet
            if summary_rows:
                pd.DataFrame(summary_rows).to_excel(writer, sheet_name="Summary", index=False)

        svc.driver.close()

finally:
    print(f"\n✅ Scraping complete. Data saved to {output_file}")
