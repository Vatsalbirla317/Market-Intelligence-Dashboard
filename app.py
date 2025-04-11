import streamlit as st
from pytrends.request import TrendReq
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

analyzer = SentimentIntensityAnalyzer()

def fetch_google_trends(keyword):
    pytrends = TrendReq(hl='en-US', tz=330)
    pytrends.build_payload([keyword], cat=0, timeframe='now 1-d', geo='', gprop='')
    data = pytrends.interest_over_time()
    return data[[keyword]] if not data.empty else None

def fetch_news_data(keyword):
    url = f"https://news.google.com/rss/search?q={keyword}"
    res = requests.get(url)
    soup = BeautifulSoup(res.content, features="xml")
    items = soup.find_all('item')

    news_items = []
    for item in items:
        title = item.title.text
        link = item.link.text  # Extract article link
        description = BeautifulSoup(item.description.text, "html.parser").get_text()
        clean_desc = re.sub(r'\s+', ' ', description).strip()
        if len(clean_desc) > 250:
            clean_desc = clean_desc[:247] + "..."

        combined_text = f"{title} {clean_desc}"
        sentiment_score = analyzer.polarity_scores(combined_text)["compound"]
        sentiment_category = (
            "Positive" if sentiment_score > 0.1
            else "Negative" if sentiment_score < -0.1
            else "Neutral"
        )

        news_items.append({
            'title': title,
            'description': clean_desc,
            'sentiment': sentiment_category,
            'link': link  # Include the link
        })
    return news_items

def sentiment_summary(news_items):
    counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    for item in news_items:
        counts[item['sentiment']] += 1
    total = sum(counts.values())
    return {k: round((v / total) * 100, 2) for k, v in counts.items()}

# ----------------- Streamlit UI -----------------

st.title("🧠 Brand Reputation Analyzer")
keyword = st.text_input("Enter a topic to analyze (e.g., Nike):")

if keyword:
    with st.spinner("Fetching data..."):

        # Google Trends
        trends = fetch_google_trends(keyword)
        if trends is not None:
            st.subheader("📈 Google Trends (last 24 hours)")
            st.line_chart(trends)
        else:
            st.info("No trend data available.")

        # News + Sentiment
        news_items = fetch_news_data(keyword)
        if news_items:
            st.subheader("📊 Sentiment Summary")
            summary = sentiment_summary(news_items)
            st.write(summary)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Positive", f"{summary['Positive']}%")
            with col2:
                st.metric("Neutral", f"{summary['Neutral']}%")
            with col3:
                st.metric("Negative", f"{summary['Negative']}%")

            # Display News by Sentiment
            for sentiment in ["Positive", "Neutral", "Negative"]:
                st.markdown(f"### 🔸 {sentiment} News")
                for news in [n for n in news_items if n['sentiment'] == sentiment][:2]:
                    st.markdown(f"**[{news['title']}]({news['link']})**")
                    st.caption(news['description'])
        else:
            st.warning("No news articles found.")
