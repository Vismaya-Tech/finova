# FINOVA — Financial + Sentiment Insights

This project collects complete fundamental data from Screener.in and also performs multi-platform sentiment analysis (YouTube, Google News, Twitter via Nitter, Hacker News).

## Features
- Financial data extraction
- Sentiment pipeline
- JSON and CSV outputs
- Multi-source text analysis

## How to Run
pip install -r requirements.txt
python data_collector.py
python senti_analys.py

## Outputs
- <company>_sentiment.csv
- <company>_sentiment.json
- screener_cleaned_data_<company>.json
