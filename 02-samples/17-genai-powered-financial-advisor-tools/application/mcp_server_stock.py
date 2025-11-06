#This sample application is intended solely for educational and knowledge-sharing purposes. It is not designed to provide investment guidance or financial advice.
#Stock MCP Server by utilizing yfinance data

import datetime as dt
from typing import Dict, Union, Optional
import yfinance as yf
import sys
import logging
from mcp.server.fastmcp import FastMCP
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from datetime import datetime
import os

# Global variable to store chart filenames for Streamlit display
_chart_storage = {
    "filename": None,
    "filepath": None
}

logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s:%(lineno)d | %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("stock_mcp")

try:
    mcp = FastMCP(
        name="stock_tools",
    )
    logger.info("✅ Stock MCP server initialized successfully")
except Exception as e:
    err_msg = f"Error: {str(e)}"
    logger.error(f"{err_msg}")

#Get stock pricing infomration
@mcp.tool()
async def get_stock_prices(ticker: str) -> Union[Dict, str]:
    """Fetches current and historical stock price data for a given ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AMZN', 'GOOGL', 'TSLA')
    
    Returns:
        Dictionary containing current stock price information including:
        - Current price and previous close
        - Price change (absolute and percentage)
        - Trading volume
        - 90-day high and low prices
        - Analysis date
        
    Example:
        get_stock_prices("AMZN") returns current Apple stock data with price movements
    """
    try:
        if not ticker.strip():
            return {"status": "error", "message": "Ticker symbol is required"}

        stock = yf.Ticker(ticker)
        data = stock.history(period="3mo")

        if data.empty:
            return {"status": "error", "message": f"No data found for ticker {ticker}"}

        current_price = float(data["Close"].iloc[-1])
        previous_close = float(data["Close"].iloc[-2])
        price_change = current_price - previous_close
        price_change_percent = (price_change / previous_close) * 100

        return {
            "status": "success",
            "data": {
                "symbol": ticker,
                "current_price": round(current_price, 2),
                "previous_close": round(previous_close, 2),
                "price_change": round(price_change, 2),
                "price_change_percent": round(price_change_percent, 2),
                "volume": int(data["Volume"].iloc[-1]),
                "high_90d": round(float(data["High"].max()), 2),
                "low_90d": round(float(data["Low"].min()), 2),
                "date": dt.datetime.now().strftime("%Y-%m-%d"),
            },
        }

    except Exception as e:
        return {"status": "error", "message": f"Error fetching price data: {str(e)}"}

#Get financial metrics data of the selected stock
@mcp.tool()
async def get_financial_metrics(ticker: str) -> Union[Dict, str]:
    """Fetches comprehensive financial metrics and ratios for a given stock ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'MSFT')
    
    Returns:
        Dictionary containing key financial metrics including:
        - Valuation metrics: P/E ratio, PEG ratio, Price-to-Book
        - Market data: Market cap, Beta
        - Profitability: Profit margins, Return on Equity
        - Growth indicators: Revenue growth
        - Financial health: Debt-to-Equity, Current ratio
        - Income metrics: Dividend yield (as percentage)
        
    Example:
        get_financial_metrics("AMZN") returns Apple's financial ratios and metrics
    """
    try:
        if not ticker.strip():
            return {"status": "error", "message": "Ticker symbol is required"}

        stock = yf.Ticker(ticker)
        info = stock.info

        try:
            metrics = {
                "status": "success",
                "data": {
                    "symbol": ticker,
                    "market_cap": info.get("marketCap", "N/A"),
                    "pe_ratio": info.get("trailingPE", "N/A"),
                    "forward_pe": info.get("forwardPE", "N/A"),
                    "peg_ratio": info.get("pegRatio", "N/A"),
                    "price_to_book": info.get("priceToBook", "N/A"),
                    "dividend_yield": info.get("dividendYield", "N/A"),
                    "profit_margins": info.get("profitMargins", "N/A"),
                    "revenue_growth": info.get("revenueGrowth", "N/A"),
                    "debt_to_equity": info.get("debtToEquity", "N/A"),
                    "return_on_equity": info.get("returnOnEquity", "N/A"),
                    "current_ratio": info.get("currentRatio", "N/A"),
                    "beta": info.get("beta", "N/A"),
                    "date": dt.datetime.now().strftime("%Y-%m-%d"),
                },
            }

            for key in [
                "dividend_yield",
                "profit_margins",
                "revenue_growth",
                "return_on_equity",
            ]:
                if (
                    isinstance(metrics["data"][key], (int, float))
                    and metrics["data"][key] != "N/A"
                ):
                    metrics["data"][key] = round(metrics["data"][key] * 100, 2)

            return metrics

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error processing financial data: {str(e)}",
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error fetching financial metrics: {str(e)}",
        }

#download dialy historycal stock pricing data that will be used for creating stock chart
@mcp.tool()
async def download_daily_historical_stock_data(ticker: str, period: Optional[str] = None) -> Union[Dict, str]:
    """Downloads daily stock pricing data for a specified ticker and period.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
        period: Time period for data (e.g., '1y', '2y', '5y', '10y', 'max'). Defaults to '1y' if not provided.
    
    Returns:
        Dictionary containing daily stock data with OHLCV information
    """
    try:
        if not ticker.strip():
            return {"status": "error", "message": "Ticker symbol is required"}
        
        if not period:
            period = "1y"
        
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        
        if data.empty:
            return {"status": "error", "message": f"No data found for ticker {ticker} with period {period}"}
        
        daily_data = []
        for date, row in data.iterrows():
            daily_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })
        
        return {
            "status": "success",
            "data": {
                "symbol": ticker,
                "period": period,
                "total_days": len(daily_data),
                "start_date": daily_data[0]["date"] if daily_data else None,
                "end_date": daily_data[-1]["date"] if daily_data else None,
                "daily_prices": daily_data,
            },
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Error downloading daily stock data: {str(e)}"}

# Create a chart that has single stock
@mcp.tool()
async def create_chart(ticker: str, period: Optional[str] = None, chart_type: Optional[str] = "line") -> Union[Dict, str]:
    """Creates and saves a stock price chart for a given ticker and period.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AMZN', 'GOOGL')
        period: Time period for data (e.g., '1y', '2y', '5y', '10y', 'max'). Defaults to '1y'
        chart_type: Type of chart ('line', 'candlestick', 'ohlc', 'volume'). Defaults to 'line'
    
    Returns:
        Dictionary containing chart creation status and file path
    """
    try:
        _chart_storage["filename"] = None
        _chart_storage["filepath"] = None
        
        data_result = await download_daily_historical_stock_data(ticker, period)
 
        if data_result.get("status") != "success":
            return data_result
        
        stock_data = data_result["data"]
        daily_prices = stock_data["daily_prices"]
        
        df = pd.DataFrame(daily_prices)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(12, 8))
        
        if chart_type.lower() == "line":
            ax.plot(df.index, df['close'], linewidth=2, color='#1f77b4', label=f'{ticker} Close Price')
            ax.set_ylabel('Price ($)', fontsize=12)
            ax.set_title(f'{ticker} Stock Price - {period or "1y"}', fontsize=16, fontweight='bold')
            
        elif chart_type.lower() == "candlestick":
            for i, (date, row) in enumerate(df.iterrows()):
                color = 'green' if row['close'] >= row['open'] else 'red'
                ax.plot([date, date], [row['low'], row['high']], color='black', linewidth=1)
                height = abs(row['close'] - row['open'])
                bottom = min(row['open'], row['close'])
                ax.bar(date, height, bottom=bottom, width=pd.Timedelta(days=0.6), 
                      color=color, alpha=0.7, edgecolor='black', linewidth=0.5)
            
            ax.set_ylabel('Price ($)', fontsize=12)
            ax.set_title(f'{ticker} Candlestick Chart - {period or "1y"}', fontsize=16, fontweight='bold')
            
        elif chart_type.lower() == "ohlc":
            ax.plot(df.index, df['open'], label='Open', alpha=0.7)
            ax.plot(df.index, df['high'], label='High', alpha=0.7)
            ax.plot(df.index, df['low'], label='Low', alpha=0.7)
            ax.plot(df.index, df['close'], label='Close', linewidth=2)
            ax.legend()
            ax.set_ylabel('Price ($)', fontsize=12)
            ax.set_title(f'{ticker} OHLC Chart - {period or "1y"}', fontsize=16, fontweight='bold')
            
        elif chart_type.lower() == "volume":
            ax2 = ax.twinx()
            ax.plot(df.index, df['close'], linewidth=2, color='#1f77b4', label=f'{ticker} Price')
            ax2.bar(df.index, df['volume'], alpha=0.3, color='orange', label='Volume')
            
            ax.set_ylabel('Price ($)', fontsize=12, color='#1f77b4')
            ax2.set_ylabel('Volume', fontsize=12, color='orange')
            ax.set_title(f'{ticker} Price & Volume - {period or "1y"}', fontsize=16, fontweight='bold')
            
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.xticks(rotation=45)
        
        ax.grid(True, alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        current_price = df['close'].iloc[-1]
        price_change = df['close'].iloc[-1] - df['close'].iloc[0]
        price_change_pct = (price_change / df['close'].iloc[0]) * 100
        
        stats_text = f'Current: ${current_price:.2f}\nChange: ${price_change:.2f} ({price_change_pct:+.1f}%)'
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
        os.makedirs("outputs/charts", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{ticker.lower()}_{chart_type}_{period or '1y'}_{timestamp}.png"
        filepath = os.path.join("outputs/charts/", filename)
        
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        _chart_storage["filename"] = filename
        _chart_storage["filepath"] = filepath
        
        return {
            "status": "success",
            "data": {
                "symbol": ticker,
                "chart_type": chart_type,
                "period": period or "1y",
                "filename": filename,
                "filepath": filepath,
                "data_points": len(daily_prices),
                "date_range": f"{stock_data['start_date']} to {stock_data['end_date']}",
                "current_price": current_price,
                "total_return": f"{price_change_pct:+.2f}%"
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Error creating stock chart: {str(e)}"}

# Create a chart that has multiple stocks
@mcp.tool()
async def create_comparison_chart(tickers: str, period: Optional[str] = None) -> Union[Dict, str]:
    """Creates a comparison chart for multiple stock tickers.
    
    Args:
        tickers: Comma-separated stock ticker symbols (e.g., 'AAPL,GOOGL,MSFT')
        period: Time period for data (e.g., '1y', '2y', '5y', '10y', 'max'). Defaults to '1y'
    
    Returns:
        Dictionary containing chart creation status and comparison metrics
    """
    try:
        ticker_list = [t.strip().upper() for t in tickers.split(',')]
        
        if len(ticker_list) < 2:
            return {"status": "error", "message": "At least 2 tickers required for comparison"}
        
        if len(ticker_list) > 5:
            return {"status": "error", "message": "Maximum 5 tickers allowed for comparison"}
        
        all_data = {}
        for ticker in ticker_list:
            data_result = await download_daily_historical_stock_data(ticker, period)
            if data_result.get("status") == "success":
                all_data[ticker] = data_result["data"]["daily_prices"]
            else:
                return {"status": "error", "message": f"Failed to get data for {ticker}"}
        
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(12, 8))
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        comparison_stats = {}
        
        for i, (ticker, data) in enumerate(all_data.items()):
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            
            first_price = df['close'].iloc[0]
            pct_change = ((df['close'] - first_price) / first_price) * 100
            
            ax.plot(df['date'], pct_change, linewidth=2, color=colors[i], 
                   label=f'{ticker}', marker='o', markersize=1)
            
            comparison_stats[ticker] = {
                "total_return": f"{pct_change.iloc[-1]:+.2f}%",
                "volatility": f"{pct_change.std():.2f}%",
                "max_gain": f"{pct_change.max():+.2f}%",
                "max_loss": f"{pct_change.min():+.2f}%"
            }
        
        ax.set_ylabel('Percentage Change (%)', fontsize=12)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_title(f'Stock Comparison - {", ".join(ticker_list)} ({period or "1y"})', 
                    fontsize=16, fontweight='bold')
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.xticks(rotation=45)
        
        ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comparison_{'_'.join(ticker_list)}_{period or '1y'}_{timestamp}.png"
        filepath = os.path.join("outputs/charts/", filename)
        print(f"\nfilepath: {filepath}")
        
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        _chart_storage["filename"] = filename
        _chart_storage["filepath"] = filepath
        
        return {
            "status": "success",
            "data": {
                "tickers": ticker_list,
                "period": period or "1y",
                "filename": filename,
                "filepath": filepath,
                "comparison_stats": comparison_stats
            }
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Error creating comparison chart: {str(e)}"}

@mcp.tool()
async def get_stored_chart() -> Union[Dict, str]:
    """Retrieves the currently stored chart information for Streamlit display.
    
    Returns:
        Dictionary containing stored chart filename and filepath, or None if no chart is stored
    """
    try:
        if _chart_storage["filename"] and _chart_storage["filepath"]:
            return {
                "status": "success",
                "data": {
                    "filename": _chart_storage["filename"],
                    "filepath": _chart_storage["filepath"]
                }
            }
        else:
            return {"status": "success", "data": None}
    except Exception as e:
        return {"status": "error", "message": f"Error retrieving stored chart: {str(e)}"}

@mcp.tool()
async def clear_stored_chart() -> Union[Dict, str]:
    """Clears the stored chart information after it has been displayed.
    
    Returns:
        Dictionary confirming the chart storage has been cleared
    """
    try:
        _chart_storage["filename"] = None
        _chart_storage["filepath"] = None
        return {"status": "success", "message": "Chart storage cleared successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Error clearing stored chart: {str(e)}"}


if __name__ == "__main__":
    mcp.run()