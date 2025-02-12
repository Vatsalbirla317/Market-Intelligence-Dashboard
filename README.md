# 📊 Brand Reputation Analyzer

Brand Reputation Analyzer is a Python-based tool that uses Google Trends and News Sentiment Analysis to evaluate the public perception of a given topic (e.g., a brand, product, or person).

🚀 Features

✅ Fetches Google Trends data for a topic✅ Scrapes news headlines related to the topic using NewsAPI✅ Performs sentiment analysis on news articles using TextBlob✅ Displays sentiment breakdown (Positive, Negative, Neutral)

🛠 Installation

Clone the repository:

git clone https://github.com/yourusername/brand-reputation-analyzer.git  
cd brand-reputation-analyzer  

Install dependencies:

pip install -r requirements.txt  

Set up your NewsAPI key in a .env file:

NEWS_API_KEY=your_api_key_here

Run the script:

python brand_reputation_analysis.py  

⚡ Usage

Enter a topic (e.g., "Tesla", "Apple iPhone 15")

The script fetches Google Trends data and recent news articles

It analyzes sentiment from the news headlines

Outputs the sentiment breakdown and sample headlines

📝 Example Output

🔍 Enter the topic you want to analyze: Tesla

📊 Trending data for 'Tesla':
(date-wise trend graph)

📈 **Sentiment Analysis Results:**
💪 Positive: 60.00%
❌ Negative: 30.00%
😐 Neutral: 10.00%

🟢 **Positive Headlines:**
- "Tesla stock surges after strong earnings report"
- "Tesla's new battery technology could revolutionize EVs"

🔴 **Negative Headlines:**
- "Tesla recalls thousands of vehicles due to safety concerns"

📌 Dependencies

pytrends (Google Trends API)

requests (Fetching news from NewsAPI)

textblob (Sentiment analysis)

fake_useragent (Random User-Agent for requests)

Install all dependencies using:

pip install -r requirements.txt  

🔒 API Key Setup

Replace the placeholder with your NewsAPI key inside .env:

NEWS_API_KEY=your_api_key_here

👨‍💻 Contributing

Feel free to open issues or submit PRs for improvements! 🚀
