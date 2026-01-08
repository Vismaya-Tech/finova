

import requests
import pandas as pd
import sys
import re
import time
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# ==================== CONFIGURATION ====================
class Config:
    OUTPUT_FILE = "screener_normalized_data.csv"
    SOURCE = "Screener.in"
    MAX_YEARS = 6
    REQUEST_DELAY = 1.0  # Delay between requests
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

# ==================== INPUT HANDLING ====================
def get_company_input() -> List[str]:
    """Get company names or NSE symbols from user input (interactive or CSV)"""
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.endswith(".csv"):
            # Read company names from CSV file
            df = pd.read_csv(arg)
            # Expect column 'Company' in CSV
            return [str(c) for c in df['Company'].dropna()]
        else:
            return [arg.strip()]
    
    # Interactive input
    user_input = input("Enter company names or NSE symbols (comma-separated): ").strip()
    if not user_input:
        raise ValueError("Input cannot be empty")
    return [x.strip() for x in user_input.split(",")]

# ==================== SYMBOL RESOLUTION ====================
def resolve_nse_symbol(company_name: str) -> str:
    """Fully automatic detection of NSE symbol from any company name or keyword."""
    if not company_name or not company_name.strip():
        raise ValueError("Company name cannot be empty")

    name = company_name.strip().lower()
    
    # Common patterns first (fastest)
    common_patterns = {
        "ambuja": "AMBUJACEM",
        "tcs": "TCS",
        "tata consultancy services": "TCS",
        "infosys": "INFY",
        "reliance": "RELIANCE",
        "hdfc bank": "HDFCBANK",
        "icici bank": "ICICIBANK",
        "wipro": "WIPRO",
        "hcl tech": "HCLTECH",
        "tech mahindra": "TECHM",
        "axis bank": "AXISBANK",
        "kotak bank": "KOTAKBANK"
    }
    
    if name in common_patterns:
        return common_patterns[name]

    # 1. Try Yahoo Finance
    yahoo_symbol = search_yahoo_symbol(name)
    if yahoo_symbol:
        return yahoo_symbol

    # 2. Try Screener.in search API
    screener_symbol = search_screener_symbol(name)
    if screener_symbol:
        return screener_symbol

    # 3. Try partial name search (split by space)
    for token in name.split():
        yahoo_symbol = search_yahoo_symbol(token)
        if yahoo_symbol:
            return yahoo_symbol

        screener_symbol = search_screener_symbol(token)
        if screener_symbol:
            return screener_symbol

    # 4. Last-resort fallback
    return generate_symbol_fallback(name)

def search_yahoo_symbol(query: str) -> str:
    """Search Yahoo Finance for NSE symbol."""
    try:
        url = "https://query2.finance.yahoo.com/v1/finance/search"
        params = {"q": query, "quotesCount": 10, "newsCount": 0}
        time.sleep(Config.REQUEST_DELAY)
        r = requests.get(url, params=params, headers=Config.HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        for q in data.get("quotes", []):
            symbol = q.get("symbol", "")
            exch = q.get("exchange", "")
            if symbol.endswith(".NS") or exch == "NSI":
                return symbol.replace(".NS", "")
    except Exception:
        pass
    return ""

def search_screener_symbol(query: str) -> str:
    """Use Screener.in search API to find symbol dynamically."""
    try:
        url = "https://www.screener.in/api/company/search/"
        params = {"q": query}
        r = requests.get(url, params=params, headers=Config.HEADERS, timeout=10)
        r.raise_for_status()
        results = r.json()
        if isinstance(results, list) and results:
            symbol = results[0].get("symbol", "")
            if symbol:
                return symbol.upper()
    except Exception:
        pass
    return ""

def generate_symbol_fallback(name: str) -> str:
    """Fallback: generate symbol from company name."""
    name_clean = re.sub(r"[^A-Za-z]", "", name).upper()
    return name_clean[:7]

# ==================== DATA FETCHING ====================
def fetch_screener_data(symbol: str) -> Tuple[str, Dict]:
    """Fetch financial data from Screener.in"""
    url = f"https://www.screener.in/company/{symbol}/consolidated/"
    try:
        response = requests.get(url, headers=Config.HEADERS, timeout=20)
        response.raise_for_status()
    except Exception as e:
        raise ValueError(f"Failed to fetch Screener data for {symbol}: {e}")

    soup = BeautifulSoup(response.text, "html.parser")
    company_tag = soup.select_one("h1")
    company_name = company_tag.get_text(strip=True) if company_tag else symbol

    tables = {
        "Profit & Loss": {"Summary": parse_financial_table(soup.select_one("#profit-loss table"))},
        "Balance Sheet": {"Summary": parse_financial_table(soup.select_one("#balance-sheet table"))},
        "Cash Flow": {"Summary": parse_financial_table(soup.select_one("#cash-flow table"))},
        "Ratios": {"Summary": parse_financial_table(soup.select_one("#ratios table"))},
    }

    return company_name, tables

def parse_financial_table(table) -> Dict[str, Dict[str, str]]:
    """Parse table into {metric: {year: value}}"""
    if not table:
        return {}
    headers = [h.get_text(strip=True) for h in table.select("thead th")]
    years = [re.search(r"(20\d{2})", h).group(1) for h in headers[1:] if re.search(r"(20\d{2})", h)]
    years = years[-Config.MAX_YEARS:]

    data = {}
    for row in table.select("tbody tr"):
        cols = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
        if len(cols) < 2:
            continue
        metric = cols[0]
        values = cols[1:]
        data[metric] = {}
        for i, year in enumerate(years):
            data[metric][year] = clean_numeric_value(values[i]) if i < len(values) else ""
    return data

def clean_numeric_value(value: str) -> str:
    if not value or value.strip() in ("", "-", "NA", "N/A"):
        return ""
    cleaned = value.strip().replace(",", "").replace("%", "").replace("₹", "").replace("$", "")
    cleaned = re.sub(r"[^\d.-]", "", cleaned)
    return cleaned

def clean_metric_name(metric: str) -> str:
    if not metric:
        return ""
    cleaned = metric.strip().replace("+", "").replace("*", "").replace("#", "")
    return re.sub(r"\s+", " ", cleaned)

# ==================== UNIT INFERENCE ====================
def infer_unit(metric_name: str, statement: str) -> str:
    metric_lower = clean_metric_name(metric_name).lower()
    if any(word in metric_lower for word in ["sales","revenue","profit","income","expense","asset","liability","equity","cash","borrowing","investment","market cap","reserves","fixed assets","current assets","total assets","total liabilities"]):
        return "INR Crores"
    if any(word in metric_lower for word in ["eps","dividend","book value","face value"]):
        return "INR"
    if any(word in metric_lower for word in ["margin","roe","roce","roa","ratio","yield","coverage","payout","growth","tax %","opm %"]):
        return "Percentage"
    if any(word in metric_lower for word in ["debt to equity","current ratio","quick ratio","p/e","p/b","ev/ebitda","interest coverage"]):
        return "Ratio"
    if any(word in metric_lower for word in ["days","turnover","cycle","debtor days","inventory days","working capital days"]):
        return "Days"
    if any(word in metric_lower for word in ["price","current price"]):
        return "INR"
    return "Number"

# ==================== DATA NORMALIZATION ====================
def create_normalized_rows(company_name: str, symbol: str, tables: Dict) -> List[Dict]:
    rows = []
    all_years = ["2019","2020","2021","2022","2023","2024","2025"]
    for statement_name, sections in tables.items():
        for section_name, metrics in sections.items():
            for metric_name, year_values in metrics.items():
                for year in all_years:
                    value = year_values.get(year,"")
                    if value:
                        rows.append({
                            "Company": company_name,
                            "Symbol": symbol,
                            "Statement": statement_name,
                            "Section": section_name,
                            "Metric": clean_metric_name(metric_name),
                            "Year": int(year),
                            "Value": value,
                            "Unit": infer_unit(metric_name, statement_name),
                            "Source": Config.SOURCE
                        })
    return rows

# ==================== CSV EXPORT ====================
def export_to_csv(rows: List[Dict], filename: str) -> None:
    if not rows:
        print("⚠ No data to export")
        return
    schema = ["Company","Symbol","Statement","Section","Metric","Year","Value","Unit","Source"]
    df = pd.DataFrame(rows)
    for col in schema:
        if col not in df.columns:
            df[col] = ""
    df = df[schema].sort_values(["Company","Statement","Section","Metric","Year"])
    df.to_csv(filename, index=False)
    print(f"✅ Exported {len(rows)} records to {filename}")

# ==================== MAIN PIPELINE ====================
def run_financial_pipeline():
    start_time = datetime.now()
    print("🎯 PRODUCTION-GRADE FINANCIAL DATA PIPELINE")
    print("="*60)
    try:
        company_inputs = get_company_input()
        all_rows = []
        for company_input in company_inputs:
            print(f"\n📖 Input: {company_input}")
            symbol = resolve_nse_symbol(company_input)
            print(f"🔍 Symbol: {symbol}")
            company_name, tables = fetch_screener_data(symbol)
            print(f"📈 Company: {company_name}")
            rows = create_normalized_rows(company_name, symbol, tables)
            print(f"📋 Records created: {len(rows)}")
            all_rows.extend(rows)
        export_to_csv(all_rows, Config.OUTPUT_FILE)
        duration = (datetime.now() - start_time).total_seconds()
        print(f"\n📊 PIPELINE SUMMARY:")
        print(f"   Companies processed: {len(company_inputs)}")
        print(f"   Total Records: {len(all_rows)}")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Output: {Config.OUTPUT_FILE}")
        print(f"\n✅ PIPELINE COMPLETED SUCCESSFULLY!")
        return True
    except Exception as e:
        print(f"\n❌ PIPELINE FAILED! Error: {e}")
        return False

# ==================== EXECUTION ====================
if __name__ == "__main__":
    success = run_financial_pipeline()
    sys.exit(0 if success else 1)
