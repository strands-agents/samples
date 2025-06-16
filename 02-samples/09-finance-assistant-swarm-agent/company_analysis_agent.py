#!/usr/bin/env python3
"""
Company Analysis Tool

A command-line tool that uses the Strands Agent SDK to provide comprehensive company analysis.
"""

import datetime as dt
import urllib.parse
from typing import Dict, Union

# Third-party imports
from bs4 import BeautifulSoup
import yfinance as yf
import requests
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import think, http_request


@tool
def get_company_info(ticker: str) -> Union[Dict, str]:
    """Fetches comprehensive company information and financials using Yahoo Finance."""
    try:
        if not ticker.strip():
            return {"status": "error", "message": "Ticker symbol is required"}

        stock = yf.Ticker(ticker)
        info = stock.info

        # Get company information
        company_data = {
            "status": "success",
            "data": {
                "symbol": ticker,
                "company_name": info.get("longName", "N/A"),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "description": info.get("longBusinessSummary", "N/A"),
                "website": info.get("website", "N/A"),
                "market_cap": info.get("marketCap", "N/A"),
                "employees": info.get("fullTimeEmployees", "N/A"),
                "country": info.get("country", "N/A"),
                "headquarters": info.get("city", "N/A"),
                "date": dt.datetime.now().strftime("%Y-%m-%d"),
            },
        }

        return company_data

    except Exception as e:
        return {"status": "error", "message": f"Error fetching company info: {str(e)}"}


@tool
def get_stock_news(ticker: str) -> Union[Dict, str]:
    """Fetches stock news from multiple sources for comprehensive coverage."""
    try:
        if not ticker.strip():
            return {"status": "error", "message": "Ticker symbol is required"}

        # Get company name for better search results
        try:
            stock = yf.Ticker(ticker)
            company_name = (
                stock.info.get("shortName") or stock.info.get("longName") or ticker
            )
        except Exception:
            company_name = ticker

        print(f"Searching news for {ticker} ({company_name})")

        all_news = []
        sources_tried = []

        # 1. Try Yahoo Finance news API directly
        sources_tried.append("Yahoo Finance API")
        try:
            stock = yf.Ticker(ticker)
            news_data = stock.news

            if news_data and len(news_data) > 0:
                for item in news_data[:5]:
                    news_item = {
                        "title": item.get("title", ""),
                        "summary": (
                            item.get("summary", "")[:300] if item.get("summary") else ""
                        ),
                        "url": item.get("link", ""),
                        "source": item.get("publisher", "Yahoo Finance"),
                        "date": dt.datetime.fromtimestamp(
                            item.get("providerPublishTime", 0)
                        ).strftime("%Y-%m-%d"),
                    }
                    if news_item["title"] and news_item["url"]:
                        all_news.append(news_item)

                print(f"Found {len(all_news)} news items from Yahoo Finance API")
        except Exception as e:
            print(f"Error with Yahoo Finance API: {str(e)}")

        # 2. Try MarketWatch
        if len(all_news) < 5:
            sources_tried.append("MarketWatch")
            try:
                url = f"https://www.marketwatch.com/investing/stock/{ticker.lower()}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,images/webp,*/*;q=0.8",
                }

                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")

                    # Look for news articles
                    articles = soup.select(".article__content")

                    for article in articles[:5]:
                        title_elem = article.select_one(".article__headline")
                        link_elem = article.select_one("a.link")

                        if title_elem and link_elem:
                            title = title_elem.text.strip()
                            link = link_elem.get("href", "")

                            # Make sure link is absolute
                            if link and not link.startswith("http"):
                                link = f"https://www.marketwatch.com{link}"

                            news_item = {
                                "title": title,
                                "summary": "",  # MarketWatch doesn't show summaries in the list
                                "url": link,
                                "source": "MarketWatch",
                                "date": dt.datetime.now().strftime("%Y-%m-%d"),
                            }

                            if (
                                news_item["title"]
                                and news_item["url"]
                                and news_item not in all_news
                            ):
                                all_news.append(news_item)

                    print(f"Found {len(articles)} news items from MarketWatch")
            except Exception as e:
                print(f"Error with MarketWatch: {str(e)}")

        # 3. Try CNBC
        if len(all_news) < 5:
            sources_tried.append("CNBC")
            try:
                # Use search to find news about the company
                search_query = f"{company_name} stock"
                url = f"https://www.cnbc.com/search/?query={urllib.parse.quote(search_query)}&qsearchterm={urllib.parse.quote(search_query)}"

                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,images/webp,*/*;q=0.8",
                }

                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")

                    # Look for search results
                    articles = soup.select(".SearchResult-searchResultContent")

                    for article in articles[:5]:
                        title_elem = article.select_one(".Card-title")
                        link_elem = article.select_one("a.resultlink")

                        if title_elem and link_elem:
                            title = title_elem.text.strip()
                            link = link_elem.get("href", "")

                            news_item = {
                                "title": title,
                                "summary": "",
                                "url": link,
                                "source": "CNBC",
                                "date": dt.datetime.now().strftime("%Y-%m-%d"),
                            }

                            if (
                                news_item["title"]
                                and news_item["url"]
                                and news_item not in all_news
                            ):
                                all_news.append(news_item)

                    print(f"Found {len(articles)} news items from CNBC")
            except Exception as e:
                print(f"Error with CNBC: {str(e)}")

        # 4. Try Seeking Alpha
        if len(all_news) < 5:
            sources_tried.append("Seeking Alpha")
            try:
                url = f"https://seekingalpha.com/symbol/{ticker.upper()}/news"

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,images/webp,*/*;q=0.8",
                }

                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")

                    # Look for news articles
                    articles = soup.select("article")

                    for article in articles[:5]:
                        title_elem = article.select_one(
                            'a[data-test-id="post-list-item-title"]'
                        )

                        if title_elem:
                            title = title_elem.text.strip()
                            link = title_elem.get("href", "")

                            # Make sure link is absolute
                            if link and not link.startswith("http"):
                                link = f"https://seekingalpha.com{link}"

                            news_item = {
                                "title": title,
                                "summary": "",
                                "url": link,
                                "source": "Seeking Alpha",
                                "date": dt.datetime.now().strftime("%Y-%m-%d"),
                            }

                            if (
                                news_item["title"]
                                and news_item["url"]
                                and news_item not in all_news
                            ):
                                all_news.append(news_item)

                    print(f"Found {len(articles)} news items from Seeking Alpha")
            except Exception as e:
                print(f"Error with Seeking Alpha: {str(e)}")

        # 5. Try Google News as a fallback
        if len(all_news) < 5:
            sources_tried.append("Google News")
            try:
                search_query = f"{company_name} stock news"
                url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}&tbm=nws"

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,images/webp,*/*;q=0.8",
                }

                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")

                    # Try different selectors for Google News
                    news_elements = []
                    selectors = [
                        "div.SoaBEf",
                        "div.dbsr",
                        "g-card",
                        ".WlydOe",
                        ".ftSUBd",
                    ]

                    for selector in selectors:
                        if not news_elements:
                            news_elements = soup.select(selector)

                    # If still no results, try to find any links with news-like content
                    if not news_elements:
                        all_links = soup.find_all("a")
                        for link in all_links:
                            href = link.get("href", "")
                            if (
                                "news" in href.lower()
                                and link.text
                                and len(link.text.strip()) > 20
                            ):
                                news_elements.append(link)

                    for element in news_elements[:5]:
                        # Try to find title and link
                        title = None
                        link = None

                        # If it's a link element directly
                        if element.name == "a":
                            title = element.text.strip()
                            link = element.get("href", "")
                            if link.startswith("/url?q="):
                                link = link.split("/url?q=")[1].split("&")[0]
                        else:
                            # Try to find a link inside the element
                            link_elem = element.find("a")
                            if link_elem:
                                title = link_elem.text.strip()
                                link = link_elem.get("href", "")
                                if link.startswith("/url?q="):
                                    link = link.split("/url?q=")[1].split("&")[0]

                        if title and link and len(title) > 10:
                            news_item = {
                                "title": title,
                                "summary": "",
                                "url": link,
                                "source": "Google News",
                                "date": dt.datetime.now().strftime("%Y-%m-%d"),
                            }

                            if (
                                news_item["title"]
                                and news_item["url"]
                                and news_item not in all_news
                            ):
                                all_news.append(news_item)

                    print(f"Found {len(news_elements)} news items from Google News")
            except Exception as e:
                print(f"Error with Google News: {str(e)}")

        # Print the news items we found
        if all_news:
            print(
                f"\nFound a total of {len(all_news)} news items from {', '.join(sources_tried)}"
            )
            for idx, item in enumerate(all_news[:5], 1):
                print(f"\nNews {idx}:")
                print(f"Title: {item['title']}")
                print(f"Source: {item['source']}")
                print(f"URL: {item['url']}")
                if item["summary"]:
                    print(f"Summary: {item['summary'][:100]}...")

            return {
                "status": "success",
                "data": {
                    "symbol": ticker,
                    "company_name": company_name,
                    "recent_news": all_news[:5],  # Return at most 5 news items
                    "sources_checked": sources_tried,
                    "date": dt.datetime.now().strftime("%Y-%m-%d"),
                },
            }
        else:
            # If no news found, return an empty list
            print(
                f"\nNo news found for {ticker} after checking {', '.join(sources_tried)}"
            )
            return {
                "status": "no_results",
                "message": f"No news found for {ticker} after checking {', '.join(sources_tried)}",
                "data": {
                    "symbol": ticker,
                    "company_name": company_name,
                    "recent_news": [],
                    "sources_checked": sources_tried,
                    "date": dt.datetime.now().strftime("%Y-%m-%d"),
                },
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error fetching news: {str(e)}",
            "data": {
                "symbol": ticker,
                "recent_news": [],
                "date": dt.datetime.now().strftime("%Y-%m-%d"),
            },
        }


def create_initial_messages():
    """Create initial conversation messages."""
    return [
        {
            "role": "user",
            "content": [{"text": "Hello, I need help analyzing a company."}],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "text": "I'm ready to help you analyze a company. Please provide a ticker symbol."
                }
            ],
        },
    ]


def create_company_analysis_agent():
    """Create and configure the company analysis agent."""
    return Agent(
        system_prompt="""You are a comprehensive company analysis specialist. Follow these steps:

<input>
When user provides a company ticker:
1. Use get_company_info to fetch company overview
3. Use get_stock_news to assess market conditions
4. Provide detailed analysis in the format below
</input>

<output_format>
1. Company Overview:
   - Company Name and Industry
   - Business Description
   - Market Position
   - Key Facts

2. Financial Analysis:
   - Key Financial Metrics
   - Important Ratios
   - Cash Flow Assessment
   - Profitability Analysis

3. Market Analysis:
   - Technical Indicators
   - Recent News Impact
   - Market Position
   - Risk Assessment (Beta)

4. Summary and Recommendations:
   - Key Strengths
   - Potential Risks
   - Overall Assessment
</output_format>""",
        model=BedrockModel(model_id="us.amazon.nova-pro-v1:0", region="us-east-1"),
        tools=[get_company_info, get_stock_news, http_request, think],
    )


def main():
    """Main function to run the company analysis tool."""
    # Create and initialize the agent
    company_analysis_agent = create_company_analysis_agent()
    company_analysis_agent.messages = create_initial_messages()

    print("\n🏢 Company Analysis Tool 🔍\n")

    while True:
        query = input("\nEnter ticker symbol> ").strip()

        if query.lower() == "exit":
            print("\nGoodbye! 👋")
            break

        print("\nAnalyzing...\n")

        try:
            # Create the user message with proper Nova format
            user_message = {
                "role": "user",
                "content": [
                    {"text": f"Please provide a comprehensive analysis for: {query}"}
                ],
            }

            # Add message to conversation
            company_analysis_agent.messages.append(user_message)

            # Get response
            response = company_analysis_agent(user_message["content"][0]["text"])
            print(f"Analysis Results:\n{response}\n")

        except Exception as e:
            print(f"Error: {str(e)}\n")
        finally:
            # Reset conversation after each query
            company_analysis_agent.messages = create_initial_messages()


if __name__ == "__main__":
    main()
