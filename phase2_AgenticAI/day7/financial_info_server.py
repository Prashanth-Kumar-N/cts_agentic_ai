'''
FastMCP is a Python-based framework for building Model Context Protocol (MCP) servers and clients quickly and efficiently.
MCP is a standard that allows Large Language Models (LLMs) to securely interact with external tools, APIs,
and data sources.
'''

# MCP Server used: yfinance
# yfinance is very good for learning, prototyping, and basic analysis — but not reliable enough for production or trading systems.

from mcp.server.fastmcp import FastMCP
import yfinance as yf, feedparser, pandas as pd

''' similar to yfinance
AlphaVantage
Finnhub
TwelveData
EOD Historical Data
Financial Modelling Prep
pandas-datareader (yahoo/fred/world bank/OECD)
'''

mcp = FastMCP("MCP-1 Bank Financial Info Server")

@mcp.tool()
def get_bank_financial_info(ticker: str) -> dict:
    """
    Fetch financial information of a listed bank.
    Example ticker:
    - HDFCBANK.NS
    - ICICIBANK.NS
    - SBIN.NS
    - JPM
    - BAC

    Commodities
    ------------
    GC=F SI=F
    """
    # bank = yf.Ticker(ticker)
    # info = bank.info
    data = yf.Ticker(ticker).history(period="1d")
    if len(data) > 0:
        return { "ticker": ticker, "data": data }
    else:
        return {"ticker": ticker, "data": "Invalid Ticker"}

@mcp.tool()
def get_geopolitical_news(country: str, max_items: int = 3) -> dict:
    """
    Fetch latest geopolitical news summary for a given country.
    Example:
    country = "India"
    country = "China"
    country = "Russia"
    """

    query = f"{country} geopolitical news"
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"

    feed = feedparser.parse(rss_url)

    articles = []

    for entry in feed.entries[:max_items]:
        articles.append({
            "title": entry.title,
            "source": entry.get("source", {}).get("title", "Unknown"),
            "published": entry.get("published", ""),
            "link": entry.link
        })

    return (pd.DataFrame({"country": country,
                          "topic": "Geopolitical News",
                          "article_count": len(articles),
                          "articles": articles})
            )

# run the Server
if __name__ == "__main__":
    mcp.run(transport="stdio")