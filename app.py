import streamlit as st
from pytrends.request import TrendReq
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# ----------------- Page Configuration -----------------
st.set_page_config(
    page_title="Brand Reputation Analyzer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ----------------- Custom CSS for the "Crazy" Look -----------------
def load_css():
    st.markdown("""
        <style>
            /* Main app background */
            .stApp {
                background-color: #0E1117;
                color: #FAFAFA;
            }

            /* --- Main Title --- */
            .title-text {
                font-size: 3.5rem !important;
                font-weight: 700;
                color: #FFFFFF;
                text-align: center;
                padding: 20px;
                background: -webkit-linear-gradient(45deg, #FF4B4B, #4B79FF, #3CFFD1);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-family: 'monospace', sans-serif;
            }

            /* --- Input Box --- */
            [data-testid="stTextInput"] > div > div > input {
                border-radius: 20px;
                border: 2px solid #4B79FF;
                color: #FAFAFA;
                background-color: #1A1C2A;
                padding: 10px 15px;
            }

            /* --- Custom Containers (Cards) --- */
            .st-emotion-cache-1r4qj8v { /* This targets the container with border */
                background-color: rgba(40, 43, 54, 0.7);
                border: 1px solid #4B79FF;
                border-radius: 10px;
                padding: 20px !important;
                box-shadow: 0 4px 12px 0 rgba(0, 0, 0, 0.2);
                transition: transform 0.2s ease-in-out;
            }
            .st-emotion-cache-1r4qj8v:hover {
                transform: scale(1.02);
                border-color: #3CFFD1;
            }

            /* --- Metric Cards --- */
            [data-testid="stMetric"] {
                background-color: #1A1C2A;
                border: 1px solid #262730;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            }
            [data-testid="stMetricLabel"] {
                font-size: 1.1rem;
                font-weight: 600;
                color: #A0A0A0;
            }
            [data-testid="stMetricValue"] {
                font-size: 2.5rem !important;
                font-weight: 800;
            }
            
            /* --- Section Headers --- */
            .section-header {
                font-size: 1.8rem;
                font-weight: 700;
                color: #FFFFFF;
                border-bottom: 2px solid #4B79FF;
                padding-bottom: 10px;
                margin-top: 40px;
                margin-bottom: 20px;
            }
            
            /* --- News Article Links --- */
            .news-title a {
                color: #3CFFD1 !important;
                text-decoration: none;
                font-size: 1.2rem;
                font-weight: 600;
            }
            .news-title a:hover {
                text-decoration: underline;
                color: #FFFFFF !important;
            }
            
            /* --- Footer --- */
            .footer {
                text-align: center;
                padding: 20px;
                color: #A0A0A0;
                font-family: 'monospace';
            }
        </style>
    """, unsafe_allow_html=True)

# ----------------- Backend Functions (Your Original Code) -----------------

analyzer = SentimentIntensityAnalyzer()

@st.cache_data(ttl=600) # Cache data for 10 minutes
def fetch_google_trends(keyword):
    pytrends = TrendReq(hl='en-US', tz=330)
    try:
        pytrends.build_payload([keyword], cat=0, timeframe='now 1-d', geo='', gprop='')
        data = pytrends.interest_over_time()
        return data[[keyword]] if not data.empty else None
    except Exception as e:
        st.error(f"Could not fetch Google Trends data. Error: {e}")
        return None

@st.cache_data(ttl=600) # Cache data for 10 minutes
def fetch_news_data(keyword):
    news_items = []
    try:
        url = f"https://news.google.com/rss/search?q={keyword}&hl=en-US&gl=US&ceid=US:en"
        res = requests.get(url)
        res.raise_for_status() # Will raise an HTTPError for bad responses
        soup = BeautifulSoup(res.content, features="xml")
        items = soup.find_all('item')

        for item in items:
            title = item.title.text
            link = item.link.text
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
                'link': link
            })
    except requests.exceptions.RequestException as e:
        st.error(f"Could not fetch news data. Error: {e}")
    except Exception as e:
        st.error(f"An error occurred while parsing news. Error: {e}")
        
    return news_items

def sentiment_summary(news_items):
    counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    for item in news_items:
        counts[item['sentiment']] += 1
    total = sum(counts.values())
    if total == 0:
        return {k: 0 for k in counts}
    return {k: round((v / total) * 100, 2) for k, v in counts.items()}

# ----------------- Streamlit UI -----------------

load_css()

st.markdown('<h1 class="title-text">🧠 Brand Reputation Analyzer</h1>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #A0A0A0; font-size: 1.1rem;'>Enter any brand, product, or topic to instantly analyze its public perception and search interest.</p>", unsafe_allow_html=True)

keyword = st.text_input("", placeholder="Enter a topic to analyze (e.g., NVIDIA, OpenAI, Tesla)...", label_visibility="collapsed")

if keyword:
    with st.spinner(f"Analyzing '{keyword}'... This may take a moment."):
        
        # Create main layout
        main_col1, main_col2 = st.columns((5, 4), gap="large")

        with main_col1:
            st.markdown('<h2 class="section-header">📈 Google Trends (Last 24 Hours)</h2>', unsafe_allow_html=True)
            trends_data = fetch_google_trends(keyword)
            if trends_data is not None and not trends_data.empty:
                st.line_chart(trends_data, use_container_width=True, color="#FF4B4B")
            else:
                st.info("No Google Trends data available for this topic in the last 24 hours.")

        news_items = fetch_news_data(keyword)
        
        with main_col2:
            st.markdown('<h2 class="section-header">📰 News Sentiment Summary</h2>', unsafe_allow_html=True)
            if news_items:
                summary = sentiment_summary(news_items)
                
                # Custom colors for metric values
                st.markdown(f"""
                <style>
                [data-testid="stMetricValue"] {{ color: #FFFFFF; }}
                #metric-Positive [data-testid="stMetricValue"] {{ color: #3CFFD1; }}
                #metric-Negative [data-testid="stMetricValue"] {{ color: #FF4B4B; }}
                </style>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown('<div id="metric-Positive">', unsafe_allow_html=True)
                    st.metric("👍 Positive", f"{summary['Positive']}%")
                    st.markdown('</div>', unsafe_allow_html=True)
                with col2:
                    st.metric("😐 Neutral", f"{summary['Neutral']}%")
                with col3:
                    st.markdown('<div id="metric-Negative">', unsafe_allow_html=True)
                    st.metric("👎 Negative", f"{summary['Negative']}%")
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("No recent news articles found to analyze sentiment.")

        # Display News Articles below the main dashboard
        if news_items:
            st.markdown('<h2 class="section-header">📝 Latest News Breakdown</h2>', unsafe_allow_html=True)

            sentiment_map = {
                "Positive": "👍 Positive",
                "Neutral": "😐 Neutral",
                "Negative": "👎 Negative",
            }
            
            # Use columns for better layout
            news_cols = st.columns(3)
            col_idx = 0

            for sentiment_category, display_name in sentiment_map.items():
                filtered_news = [n for n in news_items if n['sentiment'] == sentiment_category]
                if filtered_news:
                    with news_cols[col_idx % 3]:
                        st.markdown(f"### {display_name}")
                        for news in filtered_news[:3]: # Show top 3 for each category
                            with st.container(border=True):
                                st.markdown(f"<p class='news-title'><a href='{news['link']}' target='_blank'>{news['title']}</a></p>", unsafe_allow_html=True)
                                st.caption(news['description'])
                    col_idx += 1


# --- Footer ---
st.markdown("---")
st.markdown("<p class='footer'>Developed with ❤️ using Streamlit & Python</p>", unsafe_allow_html=True)