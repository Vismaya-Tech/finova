import re
import json
import requests
from bs4 import BeautifulSoup
from difflib import get_close_matches

# ------------------------- COMPANY SYMBOL MAPPING -------------------------
# Add company names and their Screener symbols here
company_symbols = {
    "TCS": "TCS",
    "INFOSYS": "INFY",
    "RELIANCE": "RELIANCE",
    "HDFC BANK": "HDFCBANK",
    "AMAZON": "AMZN",
    "GOOGLE": "GOOGL",
    "MICROSOFT": "MSFT"
}

def find_best_symbol(user_input: str) -> str:
    """Match user input to the closest company symbol."""
    user_input = user_input.upper()

    # Direct match by name
    if user_input in company_symbols:
        return company_symbols[user_input]

    # Match if input is already a symbol
    for name, symbol in company_symbols.items():
        if user_input == symbol.upper():
            return symbol

    # Fuzzy match against company names
    close_matches = get_close_matches(user_input, company_symbols.keys(), n=1, cutoff=0.6)
    if close_matches:
        return company_symbols[close_matches[0]]

    # Fuzzy match against symbols
    close_matches = get_close_matches(user_input, company_symbols.values(), n=1, cutoff=0.6)
    if close_matches:
        return close_matches[0]

    # Default to input (may fail if invalid)
    return user_input

# ------------------------- PARSERS -------------------------
def parse_company_name(soup) -> str:
    name_tag = soup.select_one("div.company-nav h1.h2.shrink-text")
    return name_tag.get_text(strip=True) if name_tag else "UnknownCompany"

def parse_table(table_tag):
    if not table_tag:
        return {}
    headers = [th.get_text(strip=True) for th in table_tag.select_one("thead tr").select("th")] if table_tag.select_one("thead tr") else []
    rows = []
    tbody = table_tag.select_one("tbody")
    if tbody:
        for tr in tbody.select("tr"):
            row_data = [td.get_text(strip=True) for td in tr.find_all(["th", "td"])]
            if any(row_data):
                rows.append(row_data)
    return {"headers": headers, "rows": rows}

def parse_summary_section(summary_soup):
    data = {}
    data["about"] = summary_soup.select_one("div.about").get_text(strip=True) if summary_soup.select_one("div.about") else ""
    data["key_points"] = summary_soup.select_one("div.sub.commentary").get_text(" ", strip=True) if summary_soup.select_one("div.sub.commentary") else ""
    ratio_data = []
    for r in summary_soup.select("#top-ratios > li"):
        name = r.select_one(".name")
        val = r.select_one(".value")
        if name and val:
            ratio_data.append({"ratio_name": name.get_text(strip=True), "ratio_value": val.get_text(strip=True)})
    data["top_ratios"] = ratio_data
    return data

def parse_analysis_section(analysis_soup):
    data = {"pros": [], "cons": []}
    pros_ul = analysis_soup.select_one("div.pros ul")
    cons_ul = analysis_soup.select_one("div.cons ul")
    if pros_ul:
        data["pros"] = [li.get_text(strip=True) for li in pros_ul.select("li")]
    if cons_ul:
        data["cons"] = [li.get_text(strip=True) for li in cons_ul.select("li")]
    return data

def parse_peers_section(peers_soup):
    data = {}
    table = peers_soup.select_one("table.data-table.text-nowrap.striped.mark-visited.no-scroll-right")
    if not table:
        data["peer_comparison"] = {"info": "No peer table found"}
        return data
    headers = [th.get_text(strip=True) for th in table.select("thead tr th")] if table.select_one("thead tr") else []
    rows, footer = [], []
    tbody = table.select_one("tbody")
    if tbody:
        for tr in tbody.select("tr"):
            row_text = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if any(row_text): rows.append(row_text)
    tfoot = table.select_one("tfoot")
    if tfoot:
        for tr in tfoot.select("tr"):
            row_text = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if any(row_text): footer.append(row_text)
    data["peer_comparison"] = {"headers": headers, "rows": rows, "footer": footer}
    return data

def parse_quarters_section(soup): return {"quarterly_results": parse_table(soup.select_one("table.data-table"))}
def parse_profit_loss_section(soup): return {"profit_loss": parse_table(soup.select_one("table.data-table"))}
def parse_balance_sheet_section(soup): return {"balance_sheet": parse_table(soup.select_one("table.data-table"))}
def parse_cash_flow_section(soup): return {"cash_flow": parse_table(soup.select_one("table.data-table"))}
def parse_ratios_section(soup): return {"ratios": parse_table(soup.select_one("table.data-table"))}
def parse_shareholding_section(soup): return {"shareholding": parse_table(soup.select_one("table.data-table"))}
def parse_documents_section(soup): return {"documents_info": soup.get_text(" ", strip=True)}

def parse_growth_tables(section_soup) -> dict:
    data = {}
    for tbl in section_soup.select("table.ranges-table"):
        heading_text, row_data = None, {}
        for row in tbl.select("tr"):
            th_el = row.find("th")
            if th_el:
                heading_text = th_el.get_text(strip=True)
                data[heading_text] = {}
                row_data = data[heading_text]
            else:
                tds = row.find_all("td")
                if len(tds) == 2 and heading_text:
                    label = tds[0].get_text(strip=True).rstrip(":")
                    value = tds[1].get_text(strip=True)
                    row_data[label] = value
    return data

def parse_commentary_html(commentary_html: str) -> dict:
    soup = BeautifulSoup(commentary_html, "html.parser")
    data = {}
    for heading in soup.select("div.strong.upper.letter-spacing"):
        next_sub = heading.find_next_sibling("div", class_="sub")
        if next_sub:
            data[heading.get_text(strip=True)] = next_sub.get_text(" ", strip=True)
    return data

def fetch_commentary_data(company_id: str) -> dict:
    commentary_url = f"https://www.screener.in/wiki/company/{company_id}/commentary/v2/"
    headers = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest", "Accept": "*/*", "Cache-Control": "no-cache", "Pragma": "no-cache"}
    cookies = {"csrftoken": "qqgI5LPMGQOwRyHbocfjYB0DiQDUypNX", "sessionid": "2dvmmu21airzcahg76vubryti9hs4wiz"}
    resp = requests.get(commentary_url, headers=headers, cookies=cookies)
    resp.raise_for_status()
    return parse_commentary_html(resp.text)

# ------------------------- MAIN SCRAPER -------------------------
def scrape_screener_data(url: str) -> dict:
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    results = {}

    results["company_name"] = parse_company_name(soup)

    # Extract company_id
    company_id = None
    for st in soup.find_all("style"):
        match = re.search(r'data-row-company-id="(\d+)"', st.text)
        if match:
            company_id = match.group(1)
            break
    results["company_id"] = company_id or "N/A"

    # Sub-nav sections
    sub_nav = soup.select_one("div.sub-nav-holder .sub-nav")
    if sub_nav:
        parser_map = {
            "Summary": parse_summary_section, "top": parse_summary_section, "Chart": None,
            "analysis": parse_analysis_section, "Analysis": parse_analysis_section,
            "peers": parse_peers_section, "Peers": parse_peers_section,
            "quarters": parse_quarters_section, "Quarters": parse_quarters_section,
            "profit-loss": parse_profit_loss_section, "Profit & Loss": parse_profit_loss_section,
            "balance-sheet": parse_balance_sheet_section, "Balance Sheet": parse_balance_sheet_section,
            "cash-flow": parse_cash_flow_section, "Cash Flow": parse_cash_flow_section,
            "ratios": parse_ratios_section, "Ratios": parse_ratios_section,
            "shareholding": parse_shareholding_section, "investors": parse_shareholding_section, "Investors": parse_shareholding_section,
            "documents": parse_documents_section, "Documents": parse_documents_section
        }
        for link in sub_nav.find_all("a", href=True):
            if not link["href"].startswith("#"):
                continue
            section_id = link["href"].lstrip("#")
            link_label = link.get_text(strip=True) or section_id
            section_tag = soup.select_one(f"section#{section_id}") or soup.select_one(f"div#{section_id}")
            if section_tag:
                parser_func = parser_map.get(link_label) or parser_map.get(section_id)
                results[link_label] = parser_func(section_tag) if parser_func else {"info": "No specialized parser for this section."}

    # Growth tables
    growth_div = soup.select_one("div[style*='grid-template-columns']")
    if growth_div:
        results["growth_metrics"] = parse_growth_tables(growth_div)

    # Commentary
    results["commentary"] = fetch_commentary_data(company_id) if company_id else {"info": "Company ID not found, commentary not fetched."}

    return results

# ------------------------- DRIVER -------------------------
if __name__ == "__main__":
    user_input = input("Enter your preferred company name or symbol (e.g., TCS, RELIANCE): ").strip()
    symbol = find_best_symbol(user_input)
    print(f"Using Screener symbol: {symbol}")

    url = f"https://www.screener.in/company/{symbol}/consolidated/"
    try:
        scraped_data = scrape_screener_data(url)

        company_name = scraped_data.get("company_name", symbol)
        safe_company_name = re.sub(r"[^a-zA-Z0-9]+", "_", company_name)
        filename = f"screener_cleaned_data_{safe_company_name}_with_growth_tables.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(scraped_data, f, indent=2, ensure_ascii=False)

        print(f"Scraped data (including growth tables) saved to {filename}")

    except requests.exceptions.HTTPError as e:
        print(f"Failed to fetch data for {symbol}: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
