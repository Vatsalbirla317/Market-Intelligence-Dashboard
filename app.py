import streamlit as st
from pytrends.request import TrendReq
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from collections import Counter
from io import BytesIO
import plotly.express as px
import yfinance as yf
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import spacy
from fpdf import FPDF
import numpy as np

# ----------------- Page Configuration -----------------
st.set_page_config(page_title="Market Intelligence Dashboard", page_icon="🧠", layout="wide")

# ----------------- Load Models & Analyzer (with Caching) -----------------
@st.cache_resource
def load_spacy_model():
    return spacy.load("en_core_web_sm")

@st.cache_resource
def load_sentiment_analyzer():
    return SentimentIntensityAnalyzer()

nlp = load_spacy_model()
analyzer = load_sentiment_analyzer()

# ----------------- Custom CSS -----------------
def load_css():
    st.markdown("""
        <style>
            .stApp { background-color: #0E1117; color: #FAFAFA; }
            .title-text { font-size: 3.5rem; font-weight: 700; color: #FFFFFF; text-align: center; padding-bottom: 20px; background: -webkit-linear-gradient(45deg, #FF4B4B, #4B79FF, #3CFFD1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-family: 'monospace', sans-serif; }
            .section-header { font-size: 1.8rem; font-weight: 700; color: #FFFFFF; border-bottom: 2px solid #4B79FF; padding-bottom: 10px; margin-top: 40px; margin-bottom: 20px; }
            [data-testid="stMetric"] { background-color: #1A1C2A; border: 1px solid #262730; border-radius: 8px; padding: 15px; text-align: center; }
            .stTabs [data-baseweb="tab-list"] { gap: 24px; }
            .stTabs [data-baseweb="tab"] { height: 50px; background-color: #1A1C2A; border-radius: 8px; gap: 8px; padding: 10px 20px; }
            .stTabs [data-baseweb="tab"]:hover { background-color: #262730; }
            .stTabs [aria-selected="true"] { background-color: #4B79FF; }
        </style>
    """, unsafe_allow_html=True)

# ----------------- Backend Data Fetching Functions (Cached) -----------------
@st.cache_data(ttl=600)
def fetch_google_trends(keywords, timeframe='today 1-m', geo=''):
    if not keywords:
        return None
    pytrends = TrendReq(hl='en-US', tz=330)
    try:
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo, gprop='')
        data = pytrends.interest_over_time()
        if 'isPartial' in data.columns:
            data = data.drop(columns=['isPartial'])
        return data
    except Exception:
        return None

@st.cache_data(ttl=600)
def fetch_news_data(keyword, geo='US'):
    news_items = []
    try:
        url = f"https://news.google.com/rss/search?q={keyword}&hl=en-{geo}&gl={geo}&ceid={geo}:en"
        res = requests.get(url)
        res.raise_for_status()
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
            sentiment_category = ("Positive" if sentiment_score > 0.1 else "Negative" if sentiment_score < -0.1 else "Neutral")
            news_items.append({'title': title, 'link': link, 'description': clean_desc, 'sentiment_category': sentiment_category, 'sentiment_score': sentiment_score, 'source': item.source.text if item.source else 'N/A'})
    except Exception:
        return []
    return news_items

@st.cache_data(ttl=600)
def fetch_stock_data(tickers, period='1y'):
    try:
        tickers_str = " ".join(tickers)
        if not tickers_str:
            return None
        data = yf.download(tickers_str, period=period, group_by='ticker', auto_adjust=True)
        return data if not data.empty else None
    except Exception:
        return None

# ----------------- Analysis & Visualization Functions -----------------
def get_sentiment_summary(news_items):
    counts = Counter(item['sentiment_category'] for item in news_items)
    total = sum(counts.values())
    return {k: round((counts.get(k, 0) / total) * 100, 1) if total > 0 else 0 for k in ["Positive", "Neutral", "Negative"]}

def generate_wordcloud(text, title):
    if not text:
        return None
    wc = WordCloud(width=800, height=400, background_color="rgba(255, 255, 255, 0)", mode="RGBA", collocations=False).generate(text)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    plt.title(title, color='white', fontsize=16)
    fig.patch.set_alpha(0.0)
    return fig

COUNTRY_CODES_MAP = {'US': 'USA', 'GB': 'GBR', 'CA': 'CAN', 'AU': 'AUS', 'IN': 'IND'}

@st.cache_data(ttl=1800)
def get_geo_sentiment(keyword):
    countries = {'US': 'United States', 'GB': 'United Kingdom', 'CA': 'Canada', 'AU': 'Australia', 'IN': 'India'}
    geo_data = []
    for code, name in countries.items():
        news = fetch_news_data(keyword, geo=code)
        if news:
            summary_cats = get_sentiment_summary(news)
            avg_score = np.mean([item['sentiment_score'] for item in news])
            geo_data.append({'country': name, 'iso_alpha': COUNTRY_CODES_MAP.get(code), **summary_cats, 'avg_score': avg_score})
    return pd.DataFrame(geo_data) if geo_data else None

@st.cache_data(ttl=1800)
def get_all_geo_data(keywords):
    all_data_list = []
    for keyword in keywords:
        geo_df = get_geo_sentiment(keyword)
        if geo_df is not None and not geo_df.empty:
            geo_df['keyword'] = keyword
            all_data_list.append(geo_df)
    if not all_data_list:
        return None
    return pd.concat(all_data_list, ignore_index=True)

# *** THIS IS THE FINAL, ROBUST VERSION OF THE PDF FUNCTION ***
def create_pdf_report(keywords, trends_fig, sentiment_data, wordclouds, stock_fig):
    def sanitize_text(text):
        return text.encode('latin-1', 'replace').decode('latin-1')

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, sanitize_text(f"Brand Reputation Report for: {', '.join(keywords)}"), 0, 1, 'C')
    pdf.ln(10)

    # --- Resilient Image Generation for Trends ---
    try:
        if trends_fig:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Google Trends Analysis", 0, 1)
            trends_img = BytesIO()
            trends_fig.write_image(trends_img, format='png', scale=2)
            pdf.image(trends_img, x=10, w=190)
            pdf.ln(5)
    except Exception as e:
        pdf.set_font("Arial", 'I', 10)
        pdf.set_text_color(255, 75, 75) # Red text for error
        pdf.cell(0, 10, sanitize_text("(Chart generation failed. Kaleido engine unavailable on server.)"), 0, 1, 'C')
        pdf.set_text_color(0, 0, 0)
        print(f"PDF Error (Trends): {e}")

    # --- Resilient Image Generation for Word Clouds and Stock ---
    for keyword, data in sentiment_data.items():
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, sanitize_text(f"Sentiment for '{keyword}'"), 0, 1)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 8, f"  - Positive: {data['summary']['Positive']}% | Neutral: {data['summary']['Neutral']}% | Negative: {data['summary']['Negative']}%", 0, 1)
        
        try:
            has_pos_wc = 'positive' in wordclouds[keyword] and wordclouds[keyword]['positive'] is not None
            if has_pos_wc:
                wc_pos_img = BytesIO()
                wordclouds[keyword]['positive'].savefig(wc_pos_img, format='png', dpi=150)
                pdf.image(wc_pos_img, x=10, w=90)
        except Exception as e:
            print(f"PDF Error (Positive WC): {e}")

        try:
            has_neg_wc = 'negative' in wordclouds[keyword] and wordclouds[keyword]['negative'] is not None
            if has_neg_wc:
                wc_neg_img = BytesIO()
                wordclouds[keyword]['negative'].savefig(wc_neg_img, format='png', dpi=150)
                pdf.image(wc_neg_img, x=110, w=90)
        except Exception as e:
            print(f"PDF Error (Negative WC): {e}")
        
        pdf.ln(60)

    try:
        if stock_fig:
            pdf.add_page()
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Stock Market Performance", 0, 1)
            stock_img = BytesIO()
            stock_fig.write_image(stock_img, format='png', scale=2)
            pdf.image(stock_img, x=10, w=190)
    except Exception as e:
        pdf.set_font("Arial", 'I', 10)
        pdf.set_text_color(255, 75, 75)
        pdf.cell(0, 10, sanitize_text(f"(Chart generation failed. Kaleido engine unavailable on server.)"), 0, 1, 'C')
        pdf.set_text_color(0, 0, 0)
        print(f"PDF Error (Stock): {e}")

    raw_output = pdf.output()
    if isinstance(raw_output, str):
        return raw_output.encode('latin-1')
    return bytes(raw_output)

# ----------------- STREAMLIT UI -----------------
load_css()
st.markdown('<h1 class="title-text">🧠 Market Intelligence Dashboard</h1>', unsafe_allow_html=True)

if 'keywords' not in st.session_state:
    st.session_state.keywords = ["Tesla", "NVIDIA"]
if 'tickers' not in st.session_state:
    st.session_state.tickers = ["TSLA", "NVDA"]
if 'suggestions' not in st.session_state:
    st.session_state.suggestions = []
if 'new_topic_input' not in st.session_state:
    st.session_state.new_topic_input = ""

with st.sidebar:
    st.header("⚙️ Configuration")
    st.write("#### Currently Analyzing Topics")
    st.session_state.keywords = st.multiselect("Topics", list(set(st.session_state.keywords)), st.session_state.keywords, label_visibility="collapsed")
    
    st.write("#### Stock Tickers to Track")
    ticker_input_str = st.text_input("Tickers", ", ".join(st.session_state.tickers), help="Comma-separated list (e.g., TSLA, PUM.DE, AAPL)", label_visibility="collapsed")
    st.session_state.tickers = [t.strip().upper() for t in ticker_input_str.split(',') if t.strip()]

    def add_suggestion_to_keywords(title):
        if title not in st.session_state.keywords:
            st.session_state.keywords.append(title)
        st.session_state.suggestions = []
        st.session_state.new_topic_input = ""
    def search_for_suggestions():
        if st.session_state.new_topic_input:
            st.session_state.suggestions = get_google_suggestions(st.session_state.new_topic_input)
    
    st.write("#### Add a New Topic")
    st.text_input("Type topic and press Enter", key="new_topic_input", on_change=search_for_suggestions, placeholder="e.g., Puma, Shah Rukh Khan...")

    if st.session_state.suggestions:
        st.write("Select the best match to add:")
        for sugg in st.session_state.suggestions:
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.write(f"**{sugg['title']}** ({sugg['type']})")
            with col2:
                st.button("➕", key=f"add_{sugg['mid']}", on_click=add_suggestion_to_keywords, args=(sugg['title'],))

    TIMEFRAME_MAP = {'now 1-d': '1d', 'today 1-m': '1mo', 'today 3-m': '3mo', 'today 12-m': '1y'}
    timeframe = st.selectbox("Trends Timeframe", list(TIMEFRAME_MAP.keys()), index=2)
    geo = st.selectbox("Trends Region", ['US', 'GB', 'CA', 'AU', 'IN', ''], index=0, format_func=lambda x: "Worldwide" if x=='' else x)
    
    st.markdown("---")
    
    st.header("💡 Discover What's Trending")
    with st.expander("Today's Top Google Searches"):
        trends = fetch_trending_searches(geo if geo else 'US')
        if trends:
            for trend in trends[:10]:
                if st.button(f"Analyze: {trend}", key=f"trend_btn_{trend}", use_container_width=True):
                    if trend not in st.session_state.keywords:
                        st.session_state.keywords.append(trend)
                    st.rerun()
        else:
            st.write("Could not fetch trends.")

keywords = st.session_state.keywords
if not keywords:
    st.warning("Please add a brand/topic in the sidebar to begin analysis.")
else:
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Comparison Dashboard", "🌍 Geo-Sentiment Map", "📰 News Feed", "📄 Download Report"])
    
    stock_period = TIMEFRAME_MAP.get(timeframe)
    trends_data = fetch_google_trends(keywords, timeframe, geo)
    stock_data = fetch_stock_data(st.session_state.tickers, period=stock_period)
    
    sentiment_data = {}
    wordcloud_figs = {}
    for keyword in keywords:
        news = fetch_news_data(keyword)
        sentiment_data[keyword] = {'summary': get_sentiment_summary(news), 'articles': news}
        wordcloud_figs[keyword] = {
            'positive': generate_wordcloud(" ".join(n['description'] for n in news if n['sentiment_category'] == 'Positive'), "Positive"),
            'negative': generate_wordcloud(" ".join(n['description'] for n in news if n['sentiment_category'] == 'Negative'), "Negative")
        }
    
    with tab1:
        st.markdown('<h2 class="section-header">🔍 Side-by-Side Analysis</h2>', unsafe_allow_html=True)
        cols = st.columns(len(keywords) if keywords else 1)
        for i, keyword in enumerate(keywords):
            with cols[i]:
                st.subheader(f"Analysis for '{keyword}'")
                summary = sentiment_data[keyword]['summary']
                st.metric("👍 Positive", f"{summary['Positive']}%")
                st.metric("👎 Negative", f"{summary['Negative']}%")
                st.metric("😐 Neutral", f"{summary['Neutral']}%")
                st.markdown("---")
                if wordcloud_figs[keyword]['positive']:
                    st.pyplot(wordcloud_figs[keyword]['positive'], use_container_width=True)
                if wordcloud_figs[keyword]['negative']:
                    st.pyplot(wordcloud_figs[keyword]['negative'], use_container_width=True)
        
        st.markdown('<h2 class="section-header">📈 Trend & Stock Comparison</h2>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Google Search Trends")
            if trends_data is not None and not trends_data.empty:
                fig = px.line(trends_data, title="Interest Over Time")
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No trend data available.")
        with col2:
            st.subheader("Stock Market Performance")
            if stock_data is not None and not stock_data.empty:
                if isinstance(stock_data.columns, pd.MultiIndex):
                    close_prices = stock_data.xs('Close', level=1, axis=1)
                else:
                    close_prices = stock_data[['Close']]
                
                fig = px.line(close_prices, title="Stock Price (Close)")
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No stock data found for the provided tickers.")

    with tab2:
        st.markdown('<h2 class="section-header">🌍 Global Sentiment Comparison</h2>', unsafe_allow_html=True)
        map_type = st.radio("Select Map Type:", ("Dominant Sentiment", "Sentiment Score", "Competitive Leader"), horizontal=True)
        st.markdown("---")
        with st.spinner("Fetching and processing regional data..."):
            all_geo_data = get_all_geo_data(keywords)
        if all_geo_data is None or all_geo_data.empty:
            st.warning("Could not retrieve regional data.")
        else:
            if map_type == "Dominant Sentiment":
                selected_keyword = st.selectbox("Select a brand:", options=keywords, key="dominant_select")
                df_view = all_geo_data[all_geo_data['keyword'] == selected_keyword].copy()
                if not df_view.empty:
                    df_view['dominant_sentiment'] = df_view[['Positive', 'Negative', 'Neutral']].idxmax(axis=1)
                    map_fig = px.choropleth(df_view, locations='iso_alpha', color='dominant_sentiment', hover_name='country', hover_data={'iso_alpha': False, 'Positive': ':.1f', 'Negative': ':.1f', 'Neutral': ':.1f'}, color_discrete_map={'Positive':'#3CFFD1', 'Negative':'#FF4B4B', 'Neutral':'#A0A0A0'}, title=f"Dominant News Sentiment for '{selected_keyword}'")
                    map_fig.update_layout(geo=dict(bgcolor='rgba(0,0,0,0)'), paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(map_fig, use_container_width=True)
            elif map_type == "Sentiment Score":
                selected_keyword = st.selectbox("Select a brand:", options=keywords, key="score_select")
                df_view = all_geo_data[all_geo_data['keyword'] == selected_keyword]
                if not df_view.empty:
                    map_fig = px.choropleth(df_view, locations='iso_alpha', color='avg_score', hover_name='country', color_continuous_scale=px.colors.diverging.RdYlGn, range_color=[-0.5, 0.5], title=f"Average Sentiment Score for '{selected_keyword}'")
                    map_fig.update_layout(geo=dict(bgcolor='rgba(0,0,0,0)'), paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(map_fig, use_container_width=True)
            else: # Competitive Leader
                if len(keywords) < 2:
                    st.warning("Please select at least two brands for comparison.")
                else:
                    pivot_df = all_geo_data.pivot(index='iso_alpha', columns='keyword', values='avg_score')
                    pivot_df['winner'] = pivot_df.idxmax(axis=1)
                    pivot_df = pivot_df.reset_index().merge(all_geo_data[['iso_alpha', 'country']].drop_duplicates(), on='iso_alpha')
                    brand_colors = px.colors.qualitative.Plotly
                    color_map = {keyword: brand_colors[i % len(brand_colors)] for i, keyword in enumerate(keywords)}
                    st.info("Map shows which brand has the highest average sentiment score in each region.")
                    map_fig = px.choropleth(pivot_df, locations='iso_alpha', color='winner', hover_name='country', color_discrete_map=color_map, title='Geographic Sentiment Leader')
                    map_fig.update_layout(geo=dict(bgcolor='rgba(0,0,0,0)'), paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(map_fig, use_container_width=True)

    with tab3:
        st.markdown('<h2 class="section-header">📰 Latest News Feed</h2>', unsafe_allow_html=True)
        if keywords:
            selected_keyword_news = st.selectbox("Select a brand to view recent articles:", options=keywords, key="news_select")
            if selected_keyword_news in sentiment_data:
                articles = sentiment_data[selected_keyword_news]['articles']
                if articles:
                    pos_col, neu_col, neg_col = st.columns(3)
                    with pos_col:
                        st.subheader("👍 Positive")
                        for article in [a for a in articles if a['sentiment_category'] == 'Positive'][:5]:
                            st.markdown(f"**[{article['title']}]({article['link']})**")
                            st.caption(f"Source: {article['source']}")
                            st.markdown("---")
                    with neu_col:
                        st.subheader("😐 Neutral")
                        for article in [a for a in articles if a['sentiment_category'] == 'Neutral'][:5]:
                            st.markdown(f"**[{article['title']}]({article['link']})**")
                            st.caption(f"Source: {article['source']}")
                            st.markdown("---")
                    with neg_col:
                        st.subheader("👎 Negative")
                        for article in [a for a in articles if a['sentiment_category'] == 'Negative'][:5]:
                            st.markdown(f"**[{article['title']}]({article['link']})**")
                            st.caption(f"Source: {article['source']}")
                            st.markdown("---")
                else:
                    st.warning(f"No news articles found for '{selected_keyword_news}'.")
    
    with tab4:
        st.markdown('<h2 class="section-header">📄 Generate & Download Report</h2>', unsafe_allow_html=True)
        st.info("Click below to generate a PDF summary of the current analysis.")
        trends_fig_for_pdf = px.line(trends_data) if trends_data is not None and not trends_data.empty else None
        
        stock_fig_for_pdf = None
        if stock_data is not None and not stock_data.empty:
            if isinstance(stock_data.columns, pd.MultiIndex):
                close_prices_pdf = stock_data.xs('Close', level=1, axis=1)
            else:
                close_prices_pdf = stock_data[['Close']]
            stock_fig_for_pdf = px.line(close_prices_pdf)

        pdf_bytes = create_pdf_report(keywords, trends_fig_for_pdf, sentiment_data, wordcloud_figs, stock_fig_for_pdf)
        st.download_button(label="📥 Download PDF Report", data=pdf_bytes, file_name=f"brand_report_{'_'.join(keywords)}.pdf", mime="application/pdf")