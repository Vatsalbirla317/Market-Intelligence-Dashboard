from pytrends.request import TrendReq
from textblob import TextBlob
import time
import requests
from fake_useragent import UserAgent

pytrends = TrendReq(hl="en-US", tz=330)

# Generate a random User-Agent
ua = UserAgent()

def get_trend_data(topic):
    """
    Fetch Google Trends data for the given topic.
    """
    try:
        time.sleep(5)  # Avoid rate limits

        pytrends.build_payload([topic], cat=0, timeframe="now 7-d", geo="US", gprop="")
        data = pytrends.interest_over_time()

        if data.empty:
            print("⚠ No trend data found. Try a broader topic.")
            return None
        else:
            print(f"\n📊 Trending data for '{topic}':")
            print(data.tail(5))  # Show last 5 records
            return data
    except Exception as e:
        print(f"❌ Error fetching trends: {str(e)}")
        if "429" in str(e):
            print("🚨 Too many requests! Waiting 30 minutes before retrying...")
            time.sleep(1800)  # Wait 30 minutes
            return get_trend_data(topic)  # Retry after delay
        elif "400" in str(e):
            print("🚨 Invalid request! Check the topic name.")
        return None

def get_news_headlines(topic):
    """
    Fetch news headlines related to the topic from NewsAPI.
    """
    API_KEY = "1e9bc8cee5d44e18a44f39eec1cf8788"  # Replace with your NewsAPI key
    url = f"https://newsapi.org/v2/everything?q={topic}&language=en&apiKey={API_KEY}"
    
    try:
        response = requests.get(url, headers={"User-Agent": ua.random})
        news_data = response.json()
        
        if news_data["status"] != "ok":
            print("❌ Error fetching news articles!")
            return []
        
        articles = news_data["articles"][:5]  # Get top 5 news headlines
        headlines = [article["title"] for article in articles]
        return headlines
    except Exception as e:
        print(f"❌ Error fetching news: {str(e)}")
        return []

def analyze_sentiment(text):
    """
    Perform sentiment analysis on the text using TextBlob.
    """
    analysis = TextBlob(text)
    if analysis.sentiment.polarity > 0:
        return "positive"
    elif analysis.sentiment.polarity < 0:
        return "negative"
    else:
        return "neutral"

def main():
    """
    Main function to run the trend and sentiment analysis.
    """
    topic = input("🔍 Enter the topic you want to analyze: ").strip()
    
    # Fetch Google Trends data
    trend_data = get_trend_data(topic)
    
    if trend_data is None or trend_data.empty:
        return

    # Fetch news headlines related to the topic
    headlines = get_news_headlines(topic)
    
    if not headlines:
        print("⚠ No news headlines found for sentiment analysis.")
        return
    
    # Perform sentiment analysis on news headlines
    sentiments = [analyze_sentiment(headline) for headline in headlines]

    # Count sentiment results
    positive_count = sentiments.count("positive")
    negative_count = sentiments.count("negative")
    neutral_count = sentiments.count("neutral")

    total = len(sentiments)
    print("\n📈 **Sentiment Analysis Results:**")
    print(f"✅ Positive: {100 * positive_count / total:.2f}%")
    print(f"❌ Negative: {100 * negative_count / total:.2f}%")
    print(f"😐 Neutral: {100 * neutral_count / total:.2f}%")

    # Display example headlines with sentiment
    print("\n🟢 **Positive Headlines:**")
    for i, headline in enumerate(headlines):
        if sentiments[i] == "positive":
            print(f"- {headline}")

    print("\n🔴 **Negative Headlines:**")
    for i, headline in enumerate(headlines):
        if sentiments[i] == "negative":
            print(f"- {headline}")

    # Add delay to avoid API rate limits
    time.sleep(10)

if __name__ == "__main__":
    main()
