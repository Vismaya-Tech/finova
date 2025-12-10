import requests
from bs4 import BeautifulSoup
from youtube_comment_downloader import YoutubeCommentDownloader
import feedparser
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()


# -------------------------------------------
# Helper: Sentiment Score
# -------------------------------------------
def get_sentiment(text):
    return analyzer.polarity_scores(text)["compound"]


# -------------------------------------------
# 1. TWITTER USING NITTER (Python 3.14 safe)
# -------------------------------------------
def fetch_twitter(company, limit=150):
    nitter_instances = [
        "https://nitter.net",
        "https://nitter.privacydev.net",
        "https://nitter.lacontrevoie.fr"
    ]

    tweets = []
    for instance in nitter_instances:
        try:
            url = f"{instance}/search?f=tweets&q={company}"
            html = requests.get(url, timeout=10).text
            soup = BeautifulSoup(html, "html.parser")

            for tweet in soup.select(".tweet-content"):
                if len(tweets) >= limit:
                    return tweets
                tweets.append(tweet.get_text(strip=True))

            if tweets:
                return tweets
        except:
            continue

    return tweets


# -------------------------------------------
# 2. YOUTUBE COMMENTS
# -------------------------------------------
def fetch_youtube_comments(company, limit=150):
    try:
        search_url = f"https://www.youtube.com/results?search_query={company}+review"
        html = requests.get(search_url).text

        idx = html.find("watch?v=")
        if idx == -1:
            return []

        video_id = html[idx + 8 : idx + 19]
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        downloader = YoutubeCommentDownloader()
        gen = downloader.get_comments_from_url(video_url)

        comments = []
        for i, c in enumerate(gen):
            if i >= limit:
                break
            comments.append(c["text"])

        return comments
    except:
        return []


# -------------------------------------------
# 3. GOOGLE NEWS
# -------------------------------------------
def fetch_google_news(company, limit=40):
    url = f"https://news.google.com/rss/search?q={company}"
    feed = feedparser.parse(url)

    return [(entry.title + " " + entry.summary) for entry in feed.entries[:limit]]


# -------------------------------------------
# 4. HACKER NEWS
# -------------------------------------------
def fetch_hackernews(company):
    try:
        url = f"https://hn.algolia.com/api/v1/search?query={company}"
        data = requests.get(url).json()
        return [hit["title"] or "" for hit in data["hits"]]
    except:
        return []


# -------------------------------------------
# MAIN PIPELINE
# -------------------------------------------
def run(company):
    print(f"🔍 Collecting data for: {company}")

    data = {
        "twitter": fetch_twitter(company),
        "youtube": fetch_youtube_comments(company),
        "news": fetch_google_news(company),
        "hackernews": fetch_hackernews(company),
    }

    all_rows = []

    for source, items in data.items():
        print(f"✔ {source}: {len(items)}")

        for text in items:
            all_rows.append({
                "source": source,
                "text": text,
                "sentiment": get_sentiment(text)
            })

    if not all_rows:
        print("\n❌ No data collected.")
        return

    df = pd.DataFrame(all_rows)

    csv_file = f"{company}_sentiment.csv"
    json_file = f"{company}_sentiment.json"

    df.to_csv(csv_file, index=False)
    df.to_json(json_file, orient="records", indent=4)

    print(f"\n📁 CSV saved: {csv_file}")
    print(f"📁 JSON saved: {json_file}")

    final_score = df["sentiment"].mean()
    print(f"\n📊 FINAL SENTIMENT SCORE for {company}: {round(final_score, 3)}")


# -------------------------------------------
# USER INPUT
# -------------------------------------------
if __name__ == "__main__":
    company = input("Enter company name: ")
    run(company)
