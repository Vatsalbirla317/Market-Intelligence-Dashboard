📊 Market Intelligence Dashboard
Market Intelligence Dashboard is a powerful Python-based Streamlit tool that analyzes brand reputation using Google Trends, news sentiment, and stock data. It helps users monitor public perception of brands, products, or individuals in real time.

🔗 Live App: Try it here 🚀

🚀 Features
✅ Fetch Google Trends data by keyword

✅ Scrape live news headlines (Google News RSS)

✅ Perform sentiment analysis using VADER and SpaCy

✅ Generate WordClouds (Positive & Negative)

✅ Track stock performance via Yahoo Finance

✅ View geo-sentiment using interactive Choropleth Maps

✅ Download PDF reports with trends, news, sentiment, and stock charts

✅ Clean and responsive UI with custom dark theme CSS

🛠 Installation


git clone https://github.com/yourusername/market-intelligence-dashboard.git
cd market-intelligence-dashboard
pip install -r requirements.txt
⚡ Usage


streamlit run app.py
Then open the URL provided in your terminal (usually http://localhost:8501) to interact with the dashboard.

📝 Example Output
📈 Sentiment Breakdown
💚 Positive: 62%
🔴 Negative: 28%
⚪ Neutral: 10%

📊 Google Trends Line Chart
☁️ WordClouds for Positive & Negative News
🌍 Geo-Sentiment Choropleth Maps
📉 Stock Price Trend for selected companies
📄 One-click downloadable PDF Report

📌 Dependencies
streamlit – UI Framework

pytrends – Google Trends API

vaderSentiment – Sentiment Analysis

spacy – Named Entity Recognition

beautifulsoup4 – HTML/XML parsing

plotly – Interactive charts

yfinance – Stock data

wordcloud, matplotlib – Visualizations

fpdf – PDF Report Generation

pandas, numpy – Data Analysis

requests – HTTP Requests

Install all dependencies with:


pip install -r requirements.txt
🔒 API Key Setup
No external API key is required (uses open Google News RSS and Yahoo Finance).
If you want to integrate NewsAPI, create a .env file and add:


NEWS_API_KEY=your_api_key_here
👨‍💻 Contributing
Feel free to fork the repo, raise issues, or submit pull requests for improvements!
Let’s build smarter tools for market and brand analysis together. 🚀

Optional Enhancements:
📸 Screenshots/GIF preview section
🌐 Deployment instructions (e.g., Render, Hugging Face Spaces)
🔗 Badges (e.g., Made with Python, MIT License, Streamlit)

Let me know if you'd like help adding any of those!
