import requests
import pandas as pd
from datetime import datetime, timedelta
from polygon import RESTClient
import yfinance as yf
import time
from config import Config

class PolygonDataFetcher:
    """
    Handles all data fetching from Polygon.io API and other sources
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key or Config.POLYGON_API_KEY
        if self.api_key == "YOUR_POLYGON_API_KEY_HERE":
            print("WARNING: Please set your Polygon.io API key in .env file (POLYGON_API_KEY=your_key_here)")
        self.client = RESTClient(self.api_key) if self.api_key != "YOUR_POLYGON_API_KEY_HERE" else None
    
    def get_stock_data(self, ticker, start_date, end_date):
        """
        Fetch OHLCV data for a ticker
        """
        try:
            if self.client:
                # Use Polygon.io for premium data with pagination
                data = []
                next_url = None
                max_pages = 100  # Safety limit to prevent infinite loops
                page_count = 0
                
                while page_count < max_pages:
                    try:
                        if next_url:
                            # Fetch next page using the next_url
                            import requests
                            headers = {"Authorization": f"Bearer {self.api_key}"}
                            response = requests.get(next_url, headers=headers, timeout=10)
                            response.raise_for_status()
                            # Parse response manually when using next_url
                            json_data = response.json()
                            if 'results' in json_data:
                                for result in json_data['results']:
                                    data.append({
                                        'date': datetime.fromtimestamp(result['t'] / 1000).date(),
                                        'open': result['o'],
                                        'high': result['h'],
                                        'low': result['l'],
                                        'close': result['c'],
                                        'volume': result['v']
                                    })
                            
                            # Check for next page
                            next_url = json_data.get('next_url')
                            
                        else:
                            # Initial request using the polygon client
                            aggs_response = self.client.get_aggs(
                                ticker=ticker,
                                multiplier=1,
                                timespan="day",
                                from_=start_date,
                                to=end_date
                            )
                            
                            # Process initial batch of results
                            for agg in aggs_response:
                                data.append({
                                    'date': datetime.fromtimestamp(agg.timestamp / 1000).date(),
                                    'open': agg.open,
                                    'high': agg.high,
                                    'low': agg.low,
                                    'close': agg.close,
                                    'volume': agg.volume
                                })
                            
                            # Check if there's more data by looking at the response object
                            # The polygon client response may have a next_url attribute
                            if hasattr(aggs_response, 'next_url') and aggs_response.next_url:
                                next_url = aggs_response.next_url
                            else:
                                # Try to access underlying response data
                                try:
                                    if hasattr(aggs_response, '_raw_response'):
                                        raw_data = aggs_response._raw_response
                                        next_url = raw_data.get('next_url')
                                    else:
                                        # No pagination info available, exit loop
                                        break
                                except:
                                    break
                        
                        page_count += 1
                        
                        # Exit if no more pages
                        if not next_url:
                            break
                            
                        # Rate limiting between requests
                        time.sleep(0.1)
                        
                    except requests.exceptions.RequestException as e:
                        print(f"Network error fetching page {page_count} for {ticker}: {e}")
                        # Try to continue with partial data
                        break
                    except Exception as e:
                        print(f"Error processing page {page_count} for {ticker}: {e}")
                        break
                
                return pd.DataFrame(data)
            else:
                # Fallback to Yahoo Finance (free but limited)
                stock = yf.Ticker(ticker)
                df = stock.history(start=start_date, end=end_date)
                df.reset_index(inplace=True)
                df.columns = [col.lower() for col in df.columns]
                df['date'] = df['date'].dt.date
                return df[['date', 'open', 'high', 'low', 'close', 'volume']]
                
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return pd.DataFrame()
    
    def get_pre_market_data(self, ticker, date):
        """
        Fetch pre-market trading data with pagination support
        """
        try:
            if self.client:
                # Get pre-market data (4 AM - 9:30 AM ET)
                start_time = f"{date}T04:00:00-04:00"
                end_time = f"{date}T09:30:00-04:00"
                
                total_volume = 0
                next_url = None
                max_pages = 20  # Reasonable limit for minute data
                page_count = 0
                
                while page_count < max_pages:
                    try:
                        if next_url:
                            # Fetch next page using the next_url
                            headers = {"Authorization": f"Bearer {self.api_key}"}
                            response = requests.get(next_url, headers=headers)
                            response.raise_for_status()
                            
                            # Parse response manually
                            json_data = response.json()
                            if 'results' in json_data:
                                for result in json_data['results']:
                                    total_volume += result.get('v', 0)  # 'v' is volume
                            
                            # Check for next page
                            next_url = json_data.get('next_url')
                            
                        else:
                            # Initial request
                            aggs = self.client.get_aggs(
                                ticker=ticker,
                                multiplier=1,
                                timespan="minute",
                                from_=start_time,
                                to=end_time
                            )
                            
                            if aggs:
                                # Process initial results
                                for agg in aggs:
                                    total_volume += agg.volume
                                
                                # Check for pagination
                                if hasattr(aggs, 'next_url') and aggs.next_url:
                                    next_url = aggs.next_url
                                else:
                                    try:
                                        if hasattr(aggs, '_raw_response'):
                                            raw_data = aggs._raw_response
                                            next_url = raw_data.get('next_url')
                                        else:
                                            break
                                    except:
                                        break
                            else:
                                break
                        
                        page_count += 1
                        
                        # Exit if no more pages
                        if not next_url:
                            break
                            
                        # Rate limiting
                        time.sleep(0.05)  # Shorter delay for minute data
                        
                    except requests.exceptions.RequestException as e:
                        print(f"Network error fetching pre-market page {page_count} for {ticker}: {e}")
                        break
                    except Exception as e:
                        print(f"Error processing pre-market page {page_count} for {ticker}: {e}")
                        break
                
                return total_volume
            
            return 0  # Return 0 if no pre-market data available
            
        except Exception as e:
            print(f"Error fetching pre-market data for {ticker}: {e}")
            return 0
    
    def get_float_data(self, ticker):
        """
        Get float data for a stock
        Note: This is a simplified version. In practice, you might need
        a specialized financial data service for accurate float data.
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get shares outstanding and float
            shares_outstanding = info.get('sharesOutstanding', 0)
            float_shares = info.get('floatShares', shares_outstanding * 0.8)  # Estimate if not available
            
            return {
                'shares_outstanding': shares_outstanding,
                'float_shares': float_shares,
                'float_millions': float_shares / 1_000_000 if float_shares else 0
            }
            
        except Exception as e:
            print(f"Error fetching float data for {ticker}: {e}")
            return {'shares_outstanding': 0, 'float_shares': 0, 'float_millions': 0}
    
    def calculate_gap_percentage(self, current_open, previous_close):
        """
        Calculate gap percentage
        """
        if previous_close == 0:
            return 0
        return ((current_open - previous_close) / previous_close) * 100
    
    def calculate_dollar_block(self, df, consolidation_range_days=5):
        """
        Calculate Steven Dux's dollar block metric
        Dollar block = Average Consolidation Price × Volume Traded in That Range
        """
        if len(df) < consolidation_range_days:
            return 0
        
        # Get the last N days for consolidation analysis
        recent_data = df.tail(consolidation_range_days)
        
        # Calculate average price during consolidation
        avg_consolidation_price = (recent_data['high'] + recent_data['low']).mean() / 2
        
        # Calculate total volume during consolidation
        total_consolidation_volume = recent_data['volume'].sum()
        
        # Dollar block calculation
        dollar_block = avg_consolidation_price * total_consolidation_volume
        
        return dollar_block
    
    def get_historical_data_batch(self, tickers, start_date, end_date):
        """
        Fetch historical data for multiple tickers
        """
        all_data = {}
        
        for ticker in tickers:
            print(f"Fetching data for {ticker}...")
            data = self.get_stock_data(ticker, start_date, end_date)
            
            if not data.empty:
                # Add float data
                float_info = self.get_float_data(ticker)
                data['float_millions'] = float_info['float_millions']
                
                # Calculate additional metrics
                data['gap_percent'] = 0.0
                data['volume_millions'] = data['volume'] / 1_000_000
                data['dollar_block'] = 0.0
                data['rotation'] = 0.0
                
                # Calculate gaps and dollar blocks
                for i in range(1, len(data)):
                    data.loc[i, 'gap_percent'] = self.calculate_gap_percentage(
                        data.loc[i, 'open'], 
                        data.loc[i-1, 'close']
                    )
                    
                    # Calculate dollar block for each day
                    if i >= 5:  # Need at least 5 days for consolidation analysis
                        consolidation_data = data.iloc[i-4:i+1]  # 5-day window
                        data.loc[i, 'dollar_block'] = self.calculate_dollar_block(consolidation_data)
                    
                    # Calculate float rotation (Volume / Float)
                    if data.loc[i, 'float_millions'] > 0:
                        data.loc[i, 'rotation'] = data.loc[i, 'volume_millions'] / data.loc[i, 'float_millions']
                
                all_data[ticker] = data
            
            # Rate limiting
            time.sleep(0.1)  # Small delay to avoid rate limits
        
        return all_data
    
    def _handle_polygon_pagination(self, initial_response, process_func, max_pages=100, rate_limit_delay=0.1):
        """
        Helper method to handle Polygon API pagination
        
        Args:
            initial_response: The initial API response from polygon client
            process_func: Function to process each result item (takes json result dict)
            max_pages: Maximum number of pages to fetch
            rate_limit_delay: Delay between requests in seconds
            
        Returns:
            List of processed results
        """
        results = []
        next_url = None
        page_count = 0
        
        # Process initial response
        if initial_response:
            for item in initial_response:
                results.append(process_func(item))
            
            # Check for pagination info
            if hasattr(initial_response, 'next_url') and initial_response.next_url:
                next_url = initial_response.next_url
            else:
                try:
                    if hasattr(initial_response, '_raw_response'):
                        raw_data = initial_response._raw_response
                        next_url = raw_data.get('next_url')
                except:
                    pass
        
        # Handle pagination
        while next_url and page_count < max_pages:
            try:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = requests.get(next_url, headers=headers)
                response.raise_for_status()
                
                json_data = response.json()
                if 'results' in json_data:
                    for result in json_data['results']:
                        results.append(process_func(result))
                
                # Get next page URL
                next_url = json_data.get('next_url')
                page_count += 1
                
                # Rate limiting
                if next_url:
                    time.sleep(rate_limit_delay)
                    
            except requests.exceptions.RequestException as e:
                print(f"Network error during pagination (page {page_count}): {e}")
                break
            except Exception as e:
                print(f"Error processing paginated response (page {page_count}): {e}")
                break
        
        return results