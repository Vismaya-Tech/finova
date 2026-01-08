import requests
import feedparser
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

# -------------------------------------------------
# COMPANY RESOLUTION
# -------------------------------------------------
def resolve_company(company_input):
    """
    Returns:
    company_name → for filtering & display
    ticker       → for Yahoo Finance RSS
    aliases      → for safe matching
    """
    company_map = {
        "TCS": ("Tata Consultancy Services", "TCS.NS", ["tcs", "tata consultancy"]),
        "INFOSYS": ("Infosys", "INFY.NS", ["infosys"]),
        "RELIANCE": ("Reliance Industries", "RELIANCE.NS", ["reliance"]),
        "HDFC BANK": ("HDFC Bank", "HDFCBANK.NS", ["hdfc"]),
        "APPLE": ("Apple Inc", "AAPL", ["apple"]),
        "MICROSOFT": ("Microsoft", "MSFT", ["microsoft"]),
        "GOOGLE": ("Alphabet", "GOOGL", ["google", "alphabet"]),
        "AMAZON": ("Amazon", "AMZN", ["amazon"]),
        "TESLA": ("Tesla", "TSLA", ["tesla"])
    }

    key = company_input.upper().strip()
    if key in company_map:
        return company_map[key]

    # fallback → user-defined company
    return company_input, company_input, [company_input.lower()]


# -------------------------------------------------
# SMART COMPANY FILTER (BALANCED)
# -------------------------------------------------
def is_valid_company_news(text, company_name, aliases):
    text = text.lower()

    # must contain company name or alias
    if company_name.lower() in text:
        return True

    for a in aliases:
        if a in text:
            return True

    return False


# -------------------------------------------------
# YAHOO FINANCE NEWS (PRIMARY SOURCE)
# -------------------------------------------------
def fetch_yahoo_news(company_name, ticker, aliases, limit=60):
    news = []

    url = (
        f"https://feeds.finance.yahoo.com/rss/2.0/headline"
        f"?s={ticker}&region=US&lang=en-US"
    )

    feed = feedparser.parse(url)

    for entry in feed.entries:
        if len(news) >= limit:
            break

        title = entry.title
        summary = entry.summary if hasattr(entry, "summary") else ""
        full_text = f"{title} {summary}"

        if not is_valid_company_news(full_text, company_name, aliases):
            continue

        news.append({
            "company": company_name,
            "source": "Yahoo Finance",
            "title": title,
            "summary": summary,
            "published": entry.published if hasattr(entry, "published") else "",
            "collected_at": datetime.utcnow().isoformat()
        })

    return news


# -------------------------------------------------
# SEEKING ALPHA (HEADLINES ONLY – SAFE MODE)
# -------------------------------------------------
def fetch_seeking_alpha(company_name, aliases, limit=30):
    news = []

    url = f"https://seekingalpha.com/search?q={company_name}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        html = requests.get(url, headers=headers, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup.select("a[data-test-id='post-list-item-title']"):
            if len(news) >= limit:
                break

            title = tag.get_text(strip=True)

            if not is_valid_company_news(title, company_name, aliases):
                continue

            news.append({
                "company": company_name,
                "source": "Seeking Alpha",
                "title": title,
                "summary": "",
                "published": "",
                "collected_at": datetime.utcnow().isoformat()
            })

    except:
        pass

    return news


# -------------------------------------------------
# MAIN COLLECTOR
# -------------------------------------------------
def collect_finance_news(company_input):
    company_name, ticker, aliases = resolve_company(company_input)

    print(f"🔍 Collecting finance news for: {company_name}")

    data = []
    data.extend(fetch_yahoo_news(company_name, ticker, aliases))
    data.extend(fetch_seeking_alpha(company_name, aliases))

    if not data:
        print("❌ No news collected.")
        return

    df = pd.DataFrame(data)

    filename = f"{company_name.replace(' ', '_')}_finance_news.csv"
    df.to_csv(filename, index=False, encoding="utf-8")

    print(f"✅ Collected {len(df)} articles")
    print(f"📁 Saved to: {filename}")


# -------------------------------------------------
# RUN
# -------------------------------------------------
if __name__ == "__main__":
    company = input("Enter company name: ").strip()
    collect_finance_news(company)
