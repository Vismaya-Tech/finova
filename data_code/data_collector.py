import re
import json
import requests
from bs4 import BeautifulSoup
from difflib import get_close_matches
from collections import defaultdict
from math import pow

# ---------------- SYMBOL MAP ----------------
company_symbols = {
    "TCS": "TCS",
    "INFOSYS": "INFY",
    "RELIANCE": "RELIANCE",
    "HDFC BANK": "HDFCBANK"
}

def find_best_symbol(name):
    name = name.upper()
    if name in company_symbols:
        return company_symbols[name]
    match = get_close_matches(name, company_symbols.keys(), n=1, cutoff=0.6)
    return company_symbols.get(match[0], name) if match else name

# ---------------- HELPERS ----------------
def safe_num(v):
    if v is None:
        return None
    try:
        return float(v.replace(",", "").replace("%", ""))
    except:
        return None

def cagr(start, end, years):
    if not start or not end or years <= 0:
        return None
    return round((pow(end / start, 1 / years) - 1) * 100, 2)

def normalize_ratio_name(name):
    mapping = {
        "ROE": "ROE %",
        "ROCE": "ROCE %",
        "Interest Coverage Ratio": "Interest Coverage",
        "Price to Book Value": "P/B",
        "Stock P/E": "P/E",
        "Dividend Yield": "Dividend Yield %",
        "Current Price": "Current Price",
        "Market Cap": "Market Cap"
    }
    return mapping.get(name, name)

# ---------------- TABLE PARSER ----------------
def parse_table(table):
    if not table:
        return {}
    headers = [h.get_text(strip=True) for h in table.select("thead th")]
    years = headers[1:]
    data = defaultdict(dict)

    for row in table.select("tbody tr"):
        cols = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
        metric = cols[0]
        for i, y in enumerate(years):
            if i + 1 < len(cols):
                data[y][metric] = cols[i + 1]
    return data

# ---------------- TOP RATIOS ----------------
def parse_top_ratios(soup):
    ratios = {}
    for li in soup.select("#top-ratios li"):
        name_tag = li.select_one(".name")
        value_tag = li.select_one(".value")
        if name_tag and value_tag:
            ratios[normalize_ratio_name(name_tag.get_text(strip=True))] = value_tag.get_text(strip=True)
    return ratios

# ---------------- MAIN SCRAPER ----------------
def scrape_screener(symbol):
    url = f"https://www.screener.in/company/{symbol}/consolidated/"
    soup = BeautifulSoup(
        requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).text,
        "html.parser"
    )

    company_tag = soup.select_one("div.company-nav h1")
    company = company_tag.get_text(strip=True) if company_tag else symbol

    pl = parse_table(soup.select_one("#profit-loss table"))
    ratios = parse_table(soup.select_one("#ratios table"))
    shareholding = parse_table(soup.select_one("#shareholding table"))
    top_ratios = parse_top_ratios(soup)

    pros = [p.get_text(strip=True) for p in soup.select("div.pros li")]
    cons = [c.get_text(strip=True) for c in soup.select("div.cons li")]

    timeline = {}
    years = sorted(pl.keys())
    for y in years:
        timeline[y] = {
            "financial_statements": {
                k: pl[y].get(k) for k in [
                    "Sales+",
                    "Expenses+",
                    "Operating Profit",
                    "OPM %",
                    "Other Income+",
                    "Interest",
                    "Depreciation",
                    "Profit before tax",
                    "Tax %",
                    "Net Profit+",
                    "EPS in Rs"
                ]
            },
            "efficiency_risk_ratios": {
                "ROCE %": safe_num(ratios[y].get("ROCE %")),
                "ROE %": safe_num(ratios[y].get("ROE")),
                "Debt to Equity": safe_num(ratios[y].get("Debt to Equity")),
                "Interest Coverage": safe_num(ratios[y].get("Interest Coverage")),
                "Working Capital Days": safe_num(ratios[y].get("Working Capital Days"))
            },
            "shareholding_intelligence": {
                "Promoters %": safe_num(shareholding[y].get("Promoters")),
                "FII %": safe_num(shareholding[y].get("Foreign Institutions")),
                "DII %": safe_num(shareholding[y].get("Domestic Institutions")),
                "Public %": safe_num(shareholding[y].get("Public"))
            },
            "growth_metrics": {},
            "qualitative_analysis": {
                "pros": pros,
                "cons": cons
            }
        }

    # ---------------- VALUATION METRICS (CURRENT ONLY) ----------------
    valuation_metrics_map = {
        "Market Cap": "Market Cap",
        "Current Price": "Current Price",
        "P/E": "P/E",
        "P/B": "P/B",
        "Dividend Yield %": "Dividend Yield %"
    }
    valuation_metrics = {v: safe_num(top_ratios.get(k)) if "%" in v else top_ratios.get(k) for k, v in valuation_metrics_map.items()}

    # ---------------- CAGR CALCULATION ----------------
    if len(years) >= 2:
        y0, y1 = years[0], years[-1]
        n = len(years) - 1
        timeline[y1]["growth_metrics"] = {
            "Sales CAGR %": cagr(safe_num(pl[y0].get("Sales+")), safe_num(pl[y1].get("Sales+")), n),
            "Profit CAGR %": cagr(safe_num(pl[y0].get("Net Profit+")), safe_num(pl[y1].get("Net Profit+")), n),
            "EPS CAGR %": cagr(safe_num(pl[y0].get("EPS in Rs")), safe_num(pl[y1].get("EPS in Rs")), n)
        }

    return {
        "company_name": company,
        "valuation_metrics_current": valuation_metrics,
        "timeline_fundamentals": timeline
    }

# ---------------- DRIVER ----------------
if __name__ == "__main__":
    name = input("Enter company name or symbol: ")
    symbol = find_best_symbol(name)
    print(f"🔍 Scraping Screener → {symbol}")
    data = scrape_screener(symbol)

    with open(f"screener_timeline_{symbol}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("✅ Screener data scraped successfully (ML-ready, no null confusion)")
