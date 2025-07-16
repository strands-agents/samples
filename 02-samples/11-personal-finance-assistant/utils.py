"""
Utility functions for the Multi-Agent Portfolio Orchestrator
"""

from strands import tool
from typing import Dict, Any, List
import pandas as pd
import os
import yfinance as yf
import numpy as np
from datetime import datetime
import time
import matplotlib.pyplot as plt


def _load_comprehensive_stock_data_from_csv(csv_filename: str = "comprehensive_stock_data.csv") -> Dict[str, Any]:
    """
    Load comprehensive stock data from CSV (annual_return, volatility fields).
    
    Args:
        csv_filename: CSV filename to load
    
    Returns:
        Stock data with annual_return, volatility, sharpe_ratio
    """
    try:
        if not os.path.exists(csv_filename):
            return {
                'success': False,
                'error': f'CSV file {csv_filename} not found',
                'action': 'file_missing'
            }
        
        df = pd.read_csv(csv_filename, index_col='ticker')
        if df.empty:
            return {'success': False, 'error': 'CSV file is empty', 'action': 'empty_file'}
        
        stocks = {}
        period = df['period'].iloc[0] if 'period' in df.columns else 'Unknown'
        
        for ticker, row in df.iterrows():
            # ticker is now correctly the actual ticker symbol from the CSV index
            stocks[ticker] = {
                'company': row.get('company', 'Unknown'),
                'sector': row.get('sector', 'Unknown'),
                'annual_return': float(row.get('annual_return', 0)),
                'volatility': float(row.get('volatility', 0)),
                'sharpe_ratio': float(row.get('sharpe_ratio', 0)),
                'current_price': float(row.get('current_price', 0))
            }
        
        return {
            'success': True,
            'stocks': stocks,
            'period': period,
            'count': len(stocks),
            'source': 'csv_cache',
            'csv_filename': csv_filename
        }
        
    except Exception as e:
        return {'success': False, 'error': f'CSV load failed: {str(e)}', 'action': 'load_error'}


def _load_simple_stock_data_from_csv(csv_filename: str = "simple_stock_data.csv") -> Dict[str, Any]:
    """
    Load simple stock data from CSV (return_pct, volatility_pct fields).
    
    Args:
        csv_filename: CSV filename to load
    
    Returns:
        Stock data with return_pct, volatility_pct, sharpe_ratio
    """
    try:
        if not os.path.exists(csv_filename):
            return {
                'success': False,
                'error': f'CSV file {csv_filename} not found',
                'action': 'file_missing'
            }
        
        df = pd.read_csv(csv_filename, index_col='ticker')
        if df.empty:
            return {'success': False, 'error': 'CSV file is empty', 'action': 'empty_file'}
        
        stocks = {}
        period = df['period'].iloc[0] if 'period' in df.columns else 'Unknown'
        
        for ticker, row in df.iterrows():
            # ticker is now correctly the actual ticker symbol from the CSV index
            stocks[ticker] = {
                'company': row.get('company', 'Unknown'),
                'sector': row.get('sector', 'Unknown'),
                'return_pct': float(row.get('return_pct', 0)),
                'volatility_pct': float(row.get('volatility_pct', 0)),
                'sharpe_ratio': float(row.get('sharpe_ratio', 0)),
                'current_price': float(row.get('current_price', 0))
            }
        
        return {
            'success': True,
            'stocks': stocks,
            'period': period,
            'count': len(stocks),
            'source': 'csv_cache',
            'csv_filename': csv_filename
        }
        
    except Exception as e:
        return {'success': False, 'error': f'CSV load failed: {str(e)}', 'action': 'load_error'}


# Create tool versions for Strands
@tool
def load_comprehensive_stock_data_from_csv(csv_filename: str = "comprehensive_stock_data.csv") -> Dict[str, Any]:
    """Load comprehensive stock data from CSV (annual_return, volatility fields)."""
    return _load_comprehensive_stock_data_from_csv(csv_filename)


@tool  
def load_simple_stock_data_from_csv(csv_filename: str = "simple_stock_data.csv") -> Dict[str, Any]:
    """Load simple stock data from CSV (return_pct, volatility_pct fields)."""
    return _load_simple_stock_data_from_csv(csv_filename)


# Make the private functions importable for direct use
load_comprehensive_stock_data_from_csv_func = _load_comprehensive_stock_data_from_csv
load_simple_stock_data_from_csv_func = _load_simple_stock_data_from_csv


# Complex stock data fetching functions moved from lab3
# Global cache for stock data to prevent redundant API calls
_stock_data_cache = None
_cache_timestamp = None


@tool
def get_stock_data(tickers: List[str] = None, year: int = 2024, save_csv: bool = False, use_cache: bool = True) -> Dict[str, Any]:
    """
    Fetch real stock data INCLUDING DAILY PRICES with automatic CSV export when caching enabled.
    
    Args:
        tickers: List of stock symbols (defaults to major stocks across sectors)
        year: Year for data fetch (fetches from Jan 1 to Dec 31 of specified year)
        save_csv: Whether to force save CSV files (saves regardless of use_cache setting)
        use_cache: Whether to check/use CSV cache first (also enables auto-save to CSV)
    
    Returns:
        Stock performance data WITH daily prices and summary metrics
    """
    # Construct date range from year parameter
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    # Default to comprehensive set of major stocks if none provided
    if tickers is None:
        tickers = [
            'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA',  # Tech giants
            'JPM', 'V',                                # Financial
            'JNJ', 'PFE', 'MRK',                      # Healthcare  
            'WMT', 'KO', 'PG',                        # Consumer
            'META', 'NVDA'                            # Growth/AI
        ]
    
    # Try to load from cache first if enabled
    if use_cache:
        cache_result = load_comprehensive_stock_data_from_csv()
        if cache_result['success']:
            cached_tickers = set(cache_result['stocks'].keys())
            needed_tickers = set(tickers)
            
            if needed_tickers.issubset(cached_tickers):
                print(f"📁 Using cached comprehensive data with daily prices")
                filtered_stocks = {t: cache_result['stocks'][t] for t in tickers if t in cache_result['stocks']}
                return {
                    'success': True,
                    'stocks': filtered_stocks,
                    'period': cache_result['period'],
                    'source': 'cache'
                }
    
    # Fetch fresh data
    print("🌐 Fetching fresh comprehensive stock data with daily prices...")
    try:
        stock_data = {}
        daily_prices = {}
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(start=start_date, end=end_date)
                info = stock.info
                
                if len(hist) > 0:
                    start_price = hist['Close'].iloc[0]
                    end_price = hist['Close'].iloc[-1]
                    total_return = ((end_price - start_price) / start_price) * 100
                    
                    daily_returns = hist['Close'].pct_change().dropna()
                    volatility = daily_returns.std() * np.sqrt(252) * 100
                    
                    # Calculate annual return
                    years = len(hist) / 252
                    annual_return = total_return / years if years > 0 else total_return
                    sharpe_ratio = (annual_return - 2.0) / volatility if volatility > 0 else 0
                    
                    # Summary metrics
                    stock_data[ticker] = {
                        'company': info.get('longName', ticker),
                        'sector': info.get('sector', 'Unknown'),
                        'annual_return': round(annual_return, 2),
                        'volatility': round(volatility, 2),
                        'sharpe_ratio': round(sharpe_ratio, 2),
                        'current_price': round(end_price, 2)
                    }
                    
                    # Store DAILY PRICES (key difference from get_stock_analysis)
                    daily_prices[ticker] = hist['Close'].round(2).to_dict()
                    
            except Exception as e:
                print(f"Warning: Could not fetch data for {ticker}: {e}")
                continue
        
        result = {
            'success': True, 
            'stocks': stock_data, 
            'daily_prices': daily_prices,  # This is what makes it comprehensive
            'period': f"{start_date} to {end_date}", 
            'source': 'fresh'
        }
        
        # Save to CSV if caching is enabled OR explicitly requested
        if (use_cache or save_csv) and stock_data:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save summary data
            df = pd.DataFrame.from_dict(stock_data, orient='index')
            df.to_csv("comprehensive_stock_data.csv", index_label='ticker')
            
            # Save DAILY PRICES (comprehensive feature)
            if daily_prices:
                prices_df = pd.DataFrame(daily_prices)
                prices_df.to_csv(f"stock_daily_prices_{start_date}_to_{end_date}_{timestamp}.csv")
                print(f"💾 Comprehensive data + daily prices saved to CSV")
        
        return result
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


@tool
def get_stock_analysis(tickers: List[str] = None, period: str = "1y", use_cache: bool = True) -> Dict[str, Any]:
    """
    Simple stock analysis tool - SUMMARY METRICS ONLY (no daily prices).
    
    Args:
        tickers: List of stock symbols (defaults to major stocks)
        period: Time period for data ("1y", "6mo", "3mo")
        use_cache: Whether to check/use CSV cache first
    
    Returns:
        Stock analysis with SUMMARY METRICS ONLY (return_pct, volatility_pct)
    """
    # Default to major stocks if none provided
    if tickers is None:
        tickers = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'JPM', 'JNJ', 'V']
    
    # Try to load from cache first if enabled
    if use_cache:
        cache_result = load_simple_stock_data_from_csv()
        if cache_result['success']:
            cached_tickers = set(cache_result['stocks'].keys())
            needed_tickers = set(tickers)
            
            if needed_tickers.issubset(cached_tickers):
                print(f"📁 Using cached simple analysis (summary metrics only)")
                filtered_stocks = {t: cache_result['stocks'][t] for t in tickers if t in cache_result['stocks']}
                return {
                    'success': True,
                    'period': cache_result['period'],
                    'stocks': filtered_stocks,
                    'count': len(filtered_stocks),
                    'source': 'cache'
                }
    
    # Fetch fresh data
    print("🌐 Fetching fresh market data for summary analysis...")
    stock_data = {}
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            info = stock.info
            
            if len(hist) > 0:
                start_price = hist['Close'].iloc[0]
                end_price = hist['Close'].iloc[-1]
                total_return = ((end_price - start_price) / start_price) * 100
                
                daily_returns = hist['Close'].pct_change().dropna()
                volatility = daily_returns.std() * np.sqrt(252) * 100
                sharpe_ratio = (total_return - 2.0) / volatility if volatility > 0 else 0
                
                # SUMMARY METRICS ONLY (no daily prices)
                stock_data[ticker] = {
                    'company': info.get('longName', ticker),
                    'sector': info.get('sector', 'Unknown'),
                    'return_pct': round(total_return, 1),
                    'volatility_pct': round(volatility, 1),
                    'sharpe_ratio': round(sharpe_ratio, 2),
                    'current_price': round(end_price, 2)
                }
                
        except Exception as e:
            print(f"⚠️ Could not analyze {ticker}: {e}")
            continue
    
    result = {
        'success': len(stock_data) > 0,
        'period': period,
        'stocks': stock_data,
        'count': len(stock_data),
        'source': 'fresh'
        # Note: NO daily_prices key - this is summary only
    }
    
    # Save to CSV if enabled
    if result['success'] and use_cache:
        df = pd.DataFrame.from_dict(stock_data, orient='index')
        df.to_csv("simple_stock_data.csv", index_label='ticker')
        print(f"💾 Simple analysis (summary only) saved to CSV")
    
    return result


# Portfolio creation functions moved from lab3
@tool
def create_growth_portfolio(stock_analysis: Dict[str, Any] = None, allocation_count: int = 4, allocation_method: str = "performance_weighted") -> Dict[str, Any]:
    """
    Enhanced growth portfolio creator with multiple allocation strategies.
    
    Args:
        stock_analysis: Stock analysis data (if None, loads from cache)
        allocation_count: Number of stocks to include in portfolio
        allocation_method: "equal_weight", "performance_weighted", or "risk_adjusted"
    
    Returns:
        Dictionary with portfolio allocations and metrics
    """
    # Get stock analysis if not provided (load from cache)
    if stock_analysis is None:
        stock_analysis = load_simple_stock_data_from_csv()
    
    if not stock_analysis.get('success'):
        return {'success': False, 'error': 'No cached stock analysis available. Run stock_data_agent first.'}
    
    stocks = stock_analysis['stocks']
    
    # Sort stocks by return percentage (growth focus) - simple analysis uses return_pct
    sorted_stocks = sorted(stocks.items(), 
                          key=lambda x: x[1]['return_pct'], 
                          reverse=True)
    
    # Select top performers for growth portfolio
    selected_stocks = sorted_stocks[:allocation_count]
    
    portfolio = {}
    
    if allocation_method == "equal_weight":
        # Original simple equal-weight allocation
        allocation_pct = 100.0 / len(selected_stocks)
        for ticker, data in selected_stocks:
            portfolio[ticker] = round(allocation_pct, 1)
            
    elif allocation_method == "performance_weighted":
        # Weight by relative performance (higher returns get higher allocation)
        total_returns = sum(data['return_pct'] for _, data in selected_stocks)
        
        for ticker, data in selected_stocks:
            # Weight based on relative performance
            weight = (data['return_pct'] / total_returns) * 100
            # Apply minimum 10% and maximum 40% constraints for diversification
            weight = max(10.0, min(40.0, weight))
            portfolio[ticker] = round(weight, 1)
            
        # Normalize to ensure total = 100%
        total_weight = sum(portfolio.values())
        for ticker in portfolio:
            portfolio[ticker] = round((portfolio[ticker] / total_weight) * 100, 1)
            
    elif allocation_method == "risk_adjusted":
        # Weight by risk-adjusted returns (Sharpe-like ratio)
        risk_adjusted_scores = []
        
        for ticker, data in selected_stocks:
            # Calculate risk-adjusted score (return / volatility)
            risk_adj_score = data['return_pct'] / max(data['volatility_pct'], 1.0)  # Avoid division by zero
            risk_adjusted_scores.append((ticker, data, risk_adj_score))
        
        total_scores = sum(score for _, _, score in risk_adjusted_scores)
        
        for ticker, data, score in risk_adjusted_scores:
            # Weight based on risk-adjusted performance
            weight = (score / total_scores) * 100
            # Apply constraints for diversification
            weight = max(10.0, min(40.0, weight))
            portfolio[ticker] = round(weight, 1)
            
        # Normalize to ensure total = 100%
        total_weight = sum(portfolio.values())
        for ticker in portfolio:
            portfolio[ticker] = round((portfolio[ticker] / total_weight) * 100, 1)
    
    # Calculate portfolio metrics - simple analysis uses return_pct, volatility_pct
    total_return = sum(stocks[ticker]['return_pct'] * (portfolio[ticker]/100) 
                      for ticker in portfolio.keys())
    
    avg_volatility = sum(stocks[ticker]['volatility_pct'] * (portfolio[ticker]/100) 
                        for ticker in portfolio.keys())
    
    return {
        'success': True,
        'strategy': 'Growth',
        'allocation_method': allocation_method,
        'portfolio': portfolio,
        'expected_return': round(total_return, 1),
        'risk_level': 'High' if avg_volatility > 25 else 'Moderate',
        'stock_count': len(portfolio),
        'data_source': stock_analysis.get('source', 'unknown')
    }


@tool
def create_diversified_portfolio(stock_analysis: Dict[str, Any] = None, allocation_count: int = 5) -> Dict[str, Any]:
    """
    Enhanced diversified portfolio creator with CSV caching support.
    
    Args:
        stock_analysis: Stock analysis data (if None, loads from cache)
        allocation_count: Number of stocks to include in portfolio
    
    Returns:
        Dictionary with portfolio allocations and metrics
    """
    # Get stock analysis if not provided (load from cache)
    if stock_analysis is None:
        stock_analysis = load_simple_stock_data_from_csv()
    
    if not stock_analysis.get('success'):
        return {'success': False, 'error': 'No cached stock analysis available. Run stock_data_agent first.'}
    
    stocks = stock_analysis['stocks']
    
    # Sort stocks by Sharpe ratio (risk-adjusted returns for diversification)
    sorted_stocks = sorted(stocks.items(), 
                          key=lambda x: x[1]['sharpe_ratio'], 
                          reverse=True)
    
    # Select top risk-adjusted performers
    selected_stocks = sorted_stocks[:allocation_count]
    
    # Create sector-aware allocation (diversification focus)
    sectors = {}
    for ticker, data in selected_stocks:
        sector = data['sector']
        if sector not in sectors:
            sectors[sector] = []
        sectors[sector].append(ticker)
    
    # Allocate based on diversification principle
    portfolio = {}
    base_allocation = 100.0 / len(selected_stocks)
    
    for ticker, data in selected_stocks:
        # Slightly reduce allocation if sector is over-represented
        sector_count = len(sectors[data['sector']])
        total_sectors = len(sectors)
        
        # Diversification adjustment (simple but effective)
        if sector_count > 1 and total_sectors > 1:
            adjustment = 0.9  # Reduce by 10% for diversification
        else:
            adjustment = 1.0
            
        portfolio[ticker] = round(base_allocation * adjustment, 1)
    
    # Normalize to 100%
    total = sum(portfolio.values())
    portfolio = {k: round(v * 100 / total, 1) for k, v in portfolio.items()}
    
    # Calculate portfolio metrics - simple analysis uses return_pct, volatility_pct
    total_return = sum(stocks[ticker]['return_pct'] * (allocation/100) 
                      for ticker, allocation in portfolio.items())
    
    avg_volatility = sum(stocks[ticker]['volatility_pct'] * (allocation/100) 
                        for ticker, allocation in portfolio.items())
    
    return {
        'success': True,
        'strategy': 'Diversified',
        'portfolio': portfolio,
        'expected_return': round(total_return, 1),
        'risk_level': 'Low' if avg_volatility < 20 else 'Moderate',
        'sectors': len(sectors),
        'stock_count': len(portfolio),
        'data_source': stock_analysis.get('source', 'unknown')
    }


@tool
def calculate_portfolio_performance(portfolios: Dict[str, Dict[str, float]], investment_amount: float = 1000.0) -> Dict[str, Any]:
    """
    Enhanced portfolio performance calculator using cached data.
    
    Args:
        portfolios: Dictionary of strategy names to portfolio allocations
        investment_amount: Amount to invest (defaults to $1000)
    
    Returns:
        Dictionary with performance analysis for each portfolio
    """
    if not portfolios:
        return {'success': False, 'error': 'No portfolios provided'}
    
    # Get cached stock analysis for calculations
    stock_analysis = load_simple_stock_data_from_csv()
    if not stock_analysis.get('success'):
        return {'success': False, 'error': 'No cached stock analysis available. Run stock_data_agent first.'}
    
    stocks = stock_analysis['stocks']
    results = {}
    
    for strategy, allocation in portfolios.items():
        try:
            # Calculate weighted portfolio return
            total_return = 0.0
            total_volatility = 0.0
            
            for ticker, percentage in allocation.items():
                if ticker in stocks:
                    weight = percentage / 100.0
                    # Use simple analysis field names: return_pct, volatility_pct
                    total_return += stocks[ticker]['return_pct'] * weight
                    total_volatility += stocks[ticker]['volatility_pct'] * weight
            
            # Calculate investment outcome
            final_value = investment_amount * (1 + total_return / 100.0)
            profit = final_value - investment_amount
            
            # Risk assessment
            if total_volatility < 20:
                risk_level = "Low"
            elif total_volatility < 30:
                risk_level = "Moderate"
            else:
                risk_level = "High"
            
            results[strategy] = {
                'expected_return_pct': round(total_return, 1),
                'portfolio_volatility': round(total_volatility, 1),
                'risk_level': risk_level,
                'initial_investment': investment_amount,
                'final_value': round(final_value, 2),
                'profit': round(profit, 2),
                'profit_percentage': round((profit / investment_amount) * 100, 1),
                'data_source': stock_analysis.get('source', 'unknown')
            }
            
        except Exception as e:
            results[strategy] = {'error': f'Calculation failed: {str(e)}'}
    
    return {
        'success': True,
        'investment_amount': investment_amount,
        'results': results,
        'portfolio_count': len(results),
        'data_source': stock_analysis.get('source', 'unknown')
    }


# Visualization functions moved from lab3
@tool
def visualize_portfolio_allocation(portfolios: Dict[str, Dict[str, float]], title: str = "Portfolio Allocation Comparison") -> str:
    """
    Create visual charts comparing portfolio allocations across strategies.
    
    Args:
        portfolios: Dictionary of strategy names to allocation dictionaries
        title: Title for the visualization
    
    Returns:
        Confirmation message about visualization creation
    """
    try:
        # Clear any existing plots
        plt.clf()
        plt.close('all')
        
        # Validate input
        if not portfolios:
            return "❌ No portfolios provided for visualization"
        
        # Set up the figure with better spacing
        num_portfolios = len(portfolios)
        fig, axes = plt.subplots(1, num_portfolios, figsize=(6*num_portfolios, 8))
        
        # If only one portfolio, make axes a list for consistent handling
        if num_portfolios == 1:
            axes = [axes]
        
        # Color palette for stocks - distinct colors
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD']
        
        for idx, (strategy, allocations) in enumerate(portfolios.items()):
            ax = axes[idx]
            
            # Prepare data for pie chart
            tickers = list(allocations.keys())
            percentages = list(allocations.values())
            
            # Create pie chart with improved text positioning
            wedges, texts, autotexts = ax.pie(
                percentages, 
                labels=tickers, 
                colors=colors[:len(tickers)],
                autopct='%1.1f%%',
                startangle=90,
                textprops={'fontsize': 11, 'fontweight': 'bold'},
                labeldistance=1.15,  # Move labels further from center
                pctdistance=0.85     # Move percentages closer to center
            )
            
            # Customize the title with better spacing
            ax.set_title(f'{strategy}\\nTotal: {sum(percentages):.1f}%', 
                        fontsize=14, fontweight='bold', pad=30)
            
            # Make percentage text more readable
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(10)
                autotext.set_bbox(dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.7))
            
            # Make label text more readable  
            for text in texts:
                text.set_fontsize(11)
                text.set_fontweight('bold')
                text.set_color('black')
        
        # Overall title with better positioning
        fig.suptitle(title, fontsize=18, fontweight='bold', y=0.95)
        
        # Adjust layout with more padding
        plt.tight_layout()
        plt.subplots_adjust(top=0.80, bottom=0.1, left=0.1, right=0.9, wspace=0.3)
        
        # Show the plot
        plt.show()
        
        return f"✅ Portfolio visualization created successfully for {num_portfolios} strategies!"
        
    except Exception as e:
        return f"❌ Error creating portfolio visualization: {str(e)}"


@tool
def visualize_performance_comparison(performance_data: Dict[str, float], title: str = "Strategy Performance Comparison") -> str:
    """
    Create bar graphs comparing strategy performance metrics.
    
    Args:
        performance_data: Dictionary of strategy names to performance values (returns)
        title: Title for the visualization
    
    Returns:
        Confirmation message about visualization creation
    """
    try:
        # Clear any existing plots
        plt.clf()
        plt.close('all')
        
        # Validate input
        if not performance_data:
            return "❌ No performance data provided for visualization"
        
        # Prepare data
        strategies = list(performance_data.keys())
        returns = list(performance_data.values())
        
        # Calculate investment values for $1,000
        investment_values = [1000 * (1 + ret/100) for ret in returns]
        
        # Create figure with subplots and better spacing
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Color palette
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD']
        bar_colors = colors[:len(strategies)]
        
        # Bar chart 1: Annual Returns
        bars1 = ax1.bar(strategies, returns, color=bar_colors, alpha=0.8, edgecolor='black', linewidth=1)
        ax1.set_title('Annual Returns Comparison', fontsize=16, fontweight='bold', pad=25)
        ax1.set_ylabel('Annual Return (%)', fontsize=14)
        ax1.set_xlabel('Investment Strategy', fontsize=14)
        ax1.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars with better positioning
        for bar, value in zip(bars1, returns):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + max(returns)*0.02,
                    f'{value:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=12)
        
        # Bar chart 2: Investment Growth ($1,000 invested)
        bars2 = ax2.bar(strategies, investment_values, color=bar_colors, alpha=0.8, edgecolor='black', linewidth=1)
        ax2.set_title('$1,000 Investment Growth', fontsize=16, fontweight='bold', pad=25)
        ax2.set_ylabel('Final Value ($)', fontsize=14)
        ax2.set_xlabel('Investment Strategy', fontsize=14)
        ax2.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars with better positioning
        for bar, value in zip(bars2, investment_values):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + max(investment_values)*0.01,
                    f'${value:,.0f}', ha='center', va='bottom', fontweight='bold', fontsize=12)
        
        # Highlight the best performer
        max_return_idx = returns.index(max(returns))
        bars1[max_return_idx].set_edgecolor('gold')
        bars1[max_return_idx].set_linewidth(4)
        bars2[max_return_idx].set_edgecolor('gold')
        bars2[max_return_idx].set_linewidth(4)
        
        # Add winner crown with better positioning
        ax1.text(max_return_idx, max(returns) + max(returns)*0.08, '👑', ha='center', fontsize=24)
        ax2.text(max_return_idx, max(investment_values) + max(investment_values)*0.05, '👑', ha='center', fontsize=24)
        
        # Overall title with better positioning
        fig.suptitle(title, fontsize=20, fontweight='bold', y=0.95)
        
        # Adjust layout with proper spacing
        plt.tight_layout()
        plt.subplots_adjust(top=0.85, bottom=0.15, left=0.1, right=0.95, wspace=0.25)
        
        # Show the plot
        plt.show()
        
        return f"✅ Performance comparison charts created successfully for {len(strategies)} strategies!"
        
    except Exception as e:
        return f"❌ Error creating performance visualization: {str(e)}"


# Validation functions for portfolio analysis accuracy
@tool
def validate_portfolio_performance(portfolio_allocations: Dict[str, float], 
                                 validation_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Test portfolio performance using validation market data.
    
    Args:
        portfolio_allocations: Dictionary of stock tickers to percentage allocations
        validation_data: Stock performance data for validation (if None, fetches current data)
    
    Returns:
        Portfolio performance metrics calculated using validation market data
    """
    if not portfolio_allocations:
        return {'success': False, 'error': 'No portfolio allocations provided'}
    
    # Get validation data if not provided
    if validation_data is None:
        validation_data = get_stock_analysis()
    
    if not validation_data.get('success'):
        return {'success': False, 'error': 'No validation market data available'}
    
    validation_stocks = validation_data['stocks']
    
    # Calculate portfolio performance using validation data
    total_allocation = sum(portfolio_allocations.values())
    if total_allocation == 0:
        return {'success': False, 'error': 'No valid allocations'}
    
    # Normalize allocations to percentages
    normalized_alloc = {k: v/total_allocation for k, v in portfolio_allocations.items()}
    
    # Calculate weighted return using validation data
    actual_return = 0.0
    actual_volatility = 0.0
    valid_stocks = 0
    
    for ticker, weight in normalized_alloc.items():
        if ticker in validation_stocks:
            # Use return_pct from validation data
            actual_return += validation_stocks[ticker]['return_pct'] * weight
            actual_volatility += validation_stocks[ticker]['volatility_pct'] * weight
            valid_stocks += 1
    
    if valid_stocks == 0:
        return {'success': False, 'error': 'No valid stocks found in validation data'}
    
    # Calculate Sharpe ratio using validation data
    actual_sharpe = actual_return / actual_volatility if actual_volatility > 0 else 0
    
    # Determine risk level
    if actual_volatility < 20:
        risk_level = "Low"
    elif actual_volatility < 30:
        risk_level = "Moderate"
    else:
        risk_level = "High"
    
    return {
        'success': True,
        'actual_return': round(actual_return, 1),
        'actual_volatility': round(actual_volatility, 1),
        'actual_sharpe': round(actual_sharpe, 2),
        'risk_level': risk_level,
        'validation_period': validation_data.get('period', 'Current'),
        'stocks_validated': valid_stocks,
        'total_stocks': len(portfolio_allocations)
    }


@tool
def compare_analysis_accuracy(portfolios: Dict[str, Dict[str, float]], 
                              historical_data: Dict[str, Any] = None,
                              validation_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Compare portfolio analysis accuracy between historical analysis and validation data.
    
    Args:
        portfolios: Dictionary of strategy names to portfolio allocations
        historical_data: Historical market data used for analysis
        validation_data: Actual market data used for validation
    
    Returns:
        Comprehensive comparison of analysis accuracy for all portfolios
    """
    if not portfolios:
        return {'success': False, 'error': 'No portfolios provided'}
    
    # Get historical data if not provided
    if historical_data is None:
        historical_data = load_simple_stock_data_from_csv()
    
    # Get validation data if not provided  
    if validation_data is None:
        validation_data = get_stock_analysis()
    
    if not historical_data.get('success') or not validation_data.get('success'):
        return {'success': False, 'error': 'Missing historical or validation data'}
    
    validation_results = {}
    
    for strategy, allocations in portfolios.items():
        # Get analyzed performance (from historical data)
        analyzed_performance = calculate_portfolio_performance({strategy: allocations})
        
        # Get actual performance (from validation data)
        actual_performance = validate_portfolio_performance(allocations, validation_data)
        
        if (analyzed_performance.get('success') and 
            actual_performance.get('success') and 
            strategy in analyzed_performance.get('results', {})):
            
            analyzed_return = analyzed_performance['results'][strategy]['expected_return_pct']
            actual_return = actual_performance['actual_return']
            
            # Calculate accuracy metrics
            analysis_error = abs(analyzed_return - actual_return)
            analysis_accuracy = max(0, 100 - (analysis_error / max(abs(actual_return), 1) * 100))
            
            validation_results[strategy] = {
                'analyzed_return': analyzed_return,
                'actual_return': actual_return,
                'analysis_error': round(analysis_error, 1),
                'analysis_accuracy': round(analysis_accuracy, 1),
                'analyzed_risk': analyzed_performance['results'][strategy]['risk_level'],
                'actual_risk': actual_performance['risk_level'],
                'actual_sharpe': actual_performance['actual_sharpe']
            }
    
    if validation_results:
        # Calculate summary statistics
        avg_accuracy = sum(r['analysis_accuracy'] for r in validation_results.values()) / len(validation_results)
        best_analyzer = max(validation_results.keys(), 
                           key=lambda x: validation_results[x]['analysis_accuracy'])
        worst_analyzer = min(validation_results.keys(),
                            key=lambda x: validation_results[x]['analysis_accuracy'])
        
        return {
            'success': True,
            'validation_results': validation_results,
            'summary': {
                'average_accuracy': round(avg_accuracy, 1),
                'best_analyzer': best_analyzer,
                'worst_analyzer': worst_analyzer,
                'total_strategies': len(validation_results),
                'historical_period': historical_data.get('period', 'Historical'),
                'validation_period': validation_data.get('period', 'Current')
            }
        }
    else:
        return {'success': False, 'error': 'No successful validation results generated'}


@tool
def calculate_accuracy_metrics(expected_returns: Dict[str, float], 
                              actual_returns: Dict[str, float]) -> Dict[str, Any]:
    """
    Calculate accuracy metrics for portfolio analysis.
    
    Args:
        expected_returns: Dictionary of strategy names to expected returns
        actual_returns: Dictionary of strategy names to actual returns
    
    Returns:
        Accuracy metrics and analysis insights
    """
    if not expected_returns or not actual_returns:
        return {'success': False, 'error': 'Missing expected or actual returns data'}
    
    # Calculate metrics for matching strategies
    accuracy_metrics = {}
    errors = []
    
    for strategy in expected_returns:
        if strategy in actual_returns:
            expected = expected_returns[strategy]
            actual = actual_returns[strategy]
            
            error = abs(expected - actual)
            accuracy = max(0, 100 - (error / max(abs(actual), 1) * 100))
            
            accuracy_metrics[strategy] = {
                'expected': expected,
                'actual': actual,
                'error': round(error, 1),
                'accuracy': round(accuracy, 1)
            }
            errors.append(error)
    
    if not accuracy_metrics:
        return {'success': False, 'error': 'No matching strategies found'}
    
    # Calculate overall metrics
    mean_error = sum(errors) / len(errors)
    max_error = max(errors)
    min_error = min(errors)
    
    # Determine analysis quality
    avg_accuracy = sum(m['accuracy'] for m in accuracy_metrics.values()) / len(accuracy_metrics)
    
    if avg_accuracy >= 80:
        quality = "Excellent"
    elif avg_accuracy >= 60:
        quality = "Good"
    elif avg_accuracy >= 40:
        quality = "Fair"
    else:
        quality = "Poor"
    
    return {
        'success': True,
        'strategy_metrics': accuracy_metrics,
        'overall_metrics': {
            'mean_error': round(mean_error, 1),
            'max_error': round(max_error, 1),
            'min_error': round(min_error, 1),
            'average_accuracy': round(avg_accuracy, 1),
            'analysis_quality': quality
        },
        'insights': {
            'total_strategies': len(accuracy_metrics),
            'best_strategy': max(accuracy_metrics.keys(), 
                               key=lambda x: accuracy_metrics[x]['accuracy']),
            'worst_strategy': min(accuracy_metrics.keys(),
                                key=lambda x: accuracy_metrics[x]['accuracy'])
        }
    }


# Global state to track printed tool calls
printed_tools = set()

def simple_multi_agent_tracker(**kwargs):
    """
    Callback handler based on official Strands Agents streaming patterns
    Prevents duplicates by checking specific event states
    """
    try:
        # Track reasoning events with emoji
        if kwargs.get("reasoning") and "reasoningText" in kwargs:
            reasoning_text = kwargs["reasoningText"]
            if len(reasoning_text) > 100:
                reasoning_text = reasoning_text[:100] + "..."
            print(f"🧠 REASONING: {reasoning_text}")
        
        # Event loop lifecycle tracking
        elif kwargs.get("init_event_loop", False):
            print("🔄 Event loop initialized")
        elif kwargs.get("start_event_loop", False):
            print("▶️ Event loop cycle starting")
        elif kwargs.get("start", False):
            print("📝 New cycle started")
        elif kwargs.get("complete", False):
            print("✅ Cycle completed")
        
        # Tool usage tracking - only when tool name is present and complete
        elif ("current_tool_use" in kwargs and 
              kwargs["current_tool_use"].get("name") and
              not kwargs.get("data")):  # Avoid printing during text streaming
            
            tool_name = kwargs["current_tool_use"]["name"]
            
            # Agent-specific emojis
            agent_emojis = {
                'stock_data_agent': '📊',
                'growth_strategy_agent': '🚀', 
                'diversified_strategy_agent': '⚖️',
                'performance_calculator_agent': '💰',
                'visualization_agent': '🎨',
                'validation_agent': '🔍'
            }
            
            emoji = agent_emojis.get(tool_name, '🔧')
            print(f"{emoji} Using tool: {tool_name}")
            
    except Exception as e:
        print(f"⚠️ Callback error: {e}")


# Validation Agent
@tool
def validation_agent(query: str) -> str:
    """Validation specialist - tests portfolios against actual market performance and calculates accuracy"""
    from strands import Agent
    
    # Import the BedrockModel - we need to access it from the global scope
    # This assumes the model is available in the calling context
    try:
        # Try to get the model from the calling context
        import inspect
        frame = inspect.currentframe()
        while frame:
            if 'model' in frame.f_locals:
                model = frame.f_locals['model']
                break
            frame = frame.f_back
        
        if 'model' not in locals():
            # Fallback: create a new model instance
            from strands.models import BedrockModel
            model = BedrockModel(model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    except:
        # Final fallback
        from strands.models import BedrockModel
        model = BedrockModel(model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    
    agent = Agent(
        model=model,
        tools=[validate_portfolio_performance, compare_analysis_accuracy, calculate_accuracy_metrics, get_stock_analysis],
        system_prompt="""You are a Validation Specialist focused on testing portfolio analysis accuracy.

        Your responsibilities:
        1. Test portfolio strategies against actual market performance using validate_portfolio_performance()
        2. Compare expected returns from historical analysis vs actual market results using compare_analysis_accuracy()
        3. Calculate accuracy metrics to show how well the analysis predicted reality
        4. Provide educational insights about portfolio analysis limitations
        
        Available tools:
        - validate_portfolio_performance() - Tests portfolios against actual market data
        - compare_analysis_accuracy() - Compares expected vs actual performance across strategies
        - calculate_accuracy_metrics() - Calculates detailed accuracy statistics
        - get_stock_analysis() - Gets current market data for validation for year 2025
        
        Key principles:
        - Always emphasize that historical analysis does not guarantee future performance
        - Provide concrete accuracy percentages and error metrics
        - Explain what the accuracy results mean for investors
        - Show both successes and failures in analysis accuracy
        - Make it educational - this teaches about analysis limitations
        
        Focus on being honest about analysis limitations while providing valuable insights about portfolio methodology."""
    )
    return str(agent(query))
