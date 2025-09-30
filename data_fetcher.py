import requests
import pandas as pd
from datetime import datetime, timedelta
from polygon import RESTClient
import yfinance as yf
import time
import os
from config import Config

class PolygonDataFetcher:
    """
    Handles all data fetching from Polygon.io API and other sources
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key or Config.POLYGON_API_KEY
        if self.api_key == "YOUR_POLYGON_API_KEY_HERE" or not self.api_key:
            print("WARNING: Please set your Polygon.io API key in .env file (POLYGON_API_KEY=your_key_here)")
            print("Falling back to Yahoo Finance (limited data, rate limits apply)")
            self.client = None
        else:
            print(f"✓ Using Polygon.io API (key: ...{self.api_key[-4:]})")
            self.client = RESTClient(self.api_key)
        
        # Setup data caching
        self.data_dir = os.path.join(os.getcwd(), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        print(f"📁 Data cache directory: {self.data_dir}")
    
    def get_stock_data(self, ticker, start_date, end_date):
        """
        Fetch OHLCV data for a ticker with caching system
        Checks cache first, then fetches missing data from API
        """
        # Convert dates to datetime objects if they're strings
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Check cache first
        cached_data = self._load_cached_data(ticker)
        
        if cached_data is not None and not cached_data.empty:
            # Check if we have the required date range
            cached_start = cached_data['date'].min().date()
            cached_end = cached_data['date'].max().date()
            
            if cached_start <= start_date and cached_end >= end_date:
                print(f"💾 Using cached data for {ticker} ({len(cached_data)} bars)")
                # Filter to requested date range
                mask = (cached_data['date'].dt.date >= start_date) & (cached_data['date'].dt.date <= end_date)
                return cached_data[mask].reset_index(drop=True)
            else:
                print(f"📊 Cache exists for {ticker} but need to fetch additional data...")
                # Need to fetch additional data
                return self._fetch_and_update_cache(ticker, start_date, end_date, cached_data)
        else:
            print(f"📊 No cache found for {ticker}, fetching from API...")
            # No cache, fetch all data
            return self._fetch_and_save_cache(ticker, start_date, end_date)
    
    def _fetch_polygon_data(self, ticker, start_date, end_date):
        """
        Fetch data from Polygon.io with proper pagination and error handling
        """
        try:
            all_data = []
            
            # Initial request
            aggs = self.client.get_aggs(
                ticker=ticker,
                multiplier=1,
                timespan="day",
                from_=start_date,
                to=end_date,
                adjusted=True,
                sort="asc",
                limit=5000
            )
            
            # Convert aggregates to list
            if aggs:
                for agg in aggs:
                    all_data.append({
                        'date': datetime.fromtimestamp(agg.timestamp / 1000).date(),
                        'open': agg.open,
                        'high': agg.high,
                        'low': agg.low,
                        'close': agg.close,
                        'volume': agg.volume
                    })
            
            if all_data:
                df = pd.DataFrame(all_data)
                df['date'] = pd.to_datetime(df['date'])
                return df.sort_values('date').reset_index(drop=True)
            
            return pd.DataFrame()
            
        except Exception as e:
            print(f"Polygon API error for {ticker}: {e}")
            return None
    
    def _fetch_yahoo_data_with_retry(self, ticker, start_date, end_date, max_retries=3):
        """
        Fetch from Yahoo Finance with retry logic and rate limiting
        """
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = min(2 ** attempt, 10)  # Exponential backoff, max 10s
                    print(f"⏳ Rate limited, waiting {delay}s before retry {attempt + 1}...")
                    time.sleep(delay)
                
                print(f"📊 Fetching {ticker} from Yahoo Finance...")
                stock = yf.Ticker(ticker)
                df = stock.history(start=start_date, end=end_date)
                
                if df.empty:
                    print(f"❌ No data available for {ticker}")
                    return pd.DataFrame()
                
                df.reset_index(inplace=True)
                df.columns = [col.lower() for col in df.columns]
                df['date'] = df['date'].dt.date
                
                # Small delay to avoid rate limits
                time.sleep(0.5)
                
                print(f"✅ Got {len(df)} bars for {ticker} from Yahoo Finance")
                return df[['date', 'open', 'high', 'low', 'close', 'volume']]
                
            except Exception as e:
                print(f"❌ Yahoo Finance attempt {attempt + 1} failed for {ticker}: {e}")
                if attempt == max_retries - 1:
                    print(f"💥 All attempts failed for {ticker}")
                    return pd.DataFrame()
                    
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
        Get float data for a stock with retry logic and rate limiting
        """
        max_retries = 2
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = 2 ** attempt
                    time.sleep(delay)
                
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Get shares outstanding and float
                shares_outstanding = info.get('sharesOutstanding', 0)
                float_shares = info.get('floatShares', shares_outstanding * 0.8 if shares_outstanding else 50_000_000)
                
                # Default values for penny stocks if no data
                if not float_shares:
                    float_shares = 50_000_000  # 50M default
                
                time.sleep(0.3)  # Rate limiting
                
                return {
                    'shares_outstanding': shares_outstanding,
                    'float_shares': float_shares,
                    'float_millions': float_shares / 1_000_000
                }
                
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Error fetching float data for {ticker}: {e}")
                    # Return reasonable defaults for penny stocks
                    return {
                        'shares_outstanding': 100_000_000,
                        'float_shares': 50_000_000,
                        'float_millions': 50.0
                    }
                    
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
        Fetch historical data for multiple tickers with better progress tracking
        """
        all_data = {}
        total_tickers = len(tickers)
        
        print(f"🔄 Fetching historical data for {total_tickers} tickers...")
        
        for i, ticker in enumerate(tickers, 1):
            print(f"📈 [{i}/{total_tickers}] Processing {ticker}...")
            
            try:
                data = self.get_stock_data(ticker, start_date, end_date)
                
                if not data.empty:
                    # Add float data with error handling
                    try:
                        float_info = self.get_float_data(ticker)
                        data['float_millions'] = float_info['float_millions']
                    except Exception as e:
                        print(f"⚠️ Float data error for {ticker}: {e}, using defaults")
                        data['float_millions'] = 50.0  # Default 50M float
                    
                    # Calculate additional metrics
                    data['gap_percent'] = 0.0
                    data['volume_millions'] = data['volume'] / 1_000_000
                    data['dollar_block'] = 0.0
                    data['rotation'] = 0.0
                    
                    # Calculate gaps and dollar blocks
                    for j in range(1, len(data)):
                        try:
                            data.loc[data.index[j], 'gap_percent'] = self.calculate_gap_percentage(
                                data.iloc[j]['open'], 
                                data.iloc[j-1]['close']
                            )
                            
                            # Calculate dollar block for each day
                            if j >= 5:  # Need at least 5 days for consolidation analysis
                                consolidation_data = data.iloc[j-4:j+1]  # 5-day window
                                data.loc[data.index[j], 'dollar_block'] = self.calculate_dollar_block(consolidation_data)
                            
                            # Calculate float rotation (Volume / Float)
                            if data.iloc[j]['float_millions'] > 0:
                                data.loc[data.index[j], 'rotation'] = data.iloc[j]['volume_millions'] / data.iloc[j]['float_millions']
                        except Exception as e:
                            print(f"⚠️ Calculation error for {ticker} day {j}: {e}")
                            continue
                    
                    all_data[ticker] = data
                    print(f"✅ Successfully processed {ticker} ({len(data)} bars)")
                else:
                    print(f"❌ No data available for {ticker}")
            
            except Exception as e:
                print(f"💥 Failed to process {ticker}: {e}")
                continue
            
            # Rate limiting between tickers
            if i < total_tickers:  # Don't delay after last ticker
                time.sleep(0.2)
        
        print(f"🎉 Completed! Successfully fetched data for {len(all_data)}/{total_tickers} tickers")
        return all_data
    
    def _get_cache_filepath(self, ticker):
        """Get the filepath for a ticker's cache file"""
        return os.path.join(self.data_dir, f"{ticker.upper()}.csv")
    
    def _load_cached_data(self, ticker):
        """Load cached data from CSV file"""
        cache_file = self._get_cache_filepath(ticker)
        
        if os.path.exists(cache_file):
            try:
                df = pd.read_csv(cache_file)
                df['date'] = pd.to_datetime(df['date'])
                print(f"📂 Loaded cached data for {ticker}: {len(df)} bars ({df['date'].min().date()} to {df['date'].max().date()})")
                return df
            except Exception as e:
                print(f"⚠️ Error loading cache for {ticker}: {e}")
                return None
        return None
    
    def _save_cached_data(self, ticker, data):
        """Save data to CSV cache file"""
        if data.empty:
            return
            
        cache_file = self._get_cache_filepath(ticker)
        try:
            # Sort by date and remove duplicates
            data_sorted = data.sort_values('date').drop_duplicates(subset=['date']).reset_index(drop=True)
            data_sorted.to_csv(cache_file, index=False)
            print(f"💾 Saved {len(data_sorted)} bars to cache: {cache_file}")
        except Exception as e:
            print(f"⚠️ Error saving cache for {ticker}: {e}")
    
    def _fetch_and_save_cache(self, ticker, start_date, end_date):
        """Fetch data from API and save to cache"""
        # Check if we're trying to fetch today's data (which might not be available yet)
        today = datetime.now().date()
        if end_date >= today:
            print(f"⚠️ Adjusting end date for {ticker} from {end_date} to {today - timedelta(days=1)} (market data delay)")
            end_date = today - timedelta(days=1)
        
        # Don't fetch if date range is invalid
        if start_date > end_date:
            print(f"⚠️ Invalid date range for {ticker}: {start_date} to {end_date}")
            return pd.DataFrame()
        
        # Fetch data from API
        data = self._fetch_from_api(ticker, start_date, end_date)
        
        if not data.empty:
            # Save to cache
            self._save_cached_data(ticker, data)
            
            # Filter to requested date range (use original requested range for filtering)
            original_end = datetime.now().date() if end_date == today - timedelta(days=1) else end_date
            mask = (data['date'].dt.date >= start_date) & (data['date'].dt.date <= original_end)
            return data[mask].reset_index(drop=True)
        
        return pd.DataFrame()
    
    def _fetch_and_update_cache(self, ticker, start_date, end_date, cached_data):
        """Fetch additional data and update cache"""
        cached_start = cached_data['date'].min().date()
        cached_end = cached_data['date'].max().date()
        
        # Determine what additional data we need
        fetch_ranges = []
        
        if start_date < cached_start:
            fetch_ranges.append((start_date, cached_start - timedelta(days=1)))
        
        if end_date > cached_end:
            # Don't fetch if it's the same day or very recent (likely market not closed)
            days_diff = (end_date - cached_end).days
            if days_diff > 0:
                # Only fetch if there's at least 1 day gap and not trying to get today's data
                today = datetime.now().date()
                if end_date < today or days_diff > 1:
                    fetch_ranges.append((cached_end + timedelta(days=1), end_date))
                else:
                    print(f"⚠️ Skipping fetch for {ticker}: requested end date {end_date} is too recent (today: {today})")
        
        # Fetch additional data
        new_data_parts = [cached_data]
        
        for fetch_start, fetch_end in fetch_ranges:
            # Additional safety check: don't fetch if range is too small or recent
            days_in_range = (fetch_end - fetch_start).days + 1
            if days_in_range < 1:
                print(f"⚠️ Skipping invalid date range for {ticker}: {fetch_start} to {fetch_end}")
                continue
                
            print(f"📊 Fetching additional data for {ticker}: {fetch_start} to {fetch_end}")
            additional_data = self._fetch_from_api(ticker, fetch_start, fetch_end)
            if not additional_data.empty:
                new_data_parts.append(additional_data)
        
        # Combine all data
        if len(new_data_parts) > 1:
            combined_data = pd.concat(new_data_parts, ignore_index=True)
            combined_data = combined_data.sort_values('date').drop_duplicates(subset=['date']).reset_index(drop=True)
            
            # Update cache
            self._save_cached_data(ticker, combined_data)
            
            # Filter to requested date range
            mask = (combined_data['date'].dt.date >= start_date) & (combined_data['date'].dt.date <= end_date)
            return combined_data[mask].reset_index(drop=True)
        
        # If no additional data was fetched, return filtered cached data
        print(f"💾 Using existing cached data for {ticker}")
        mask = (cached_data['date'].dt.date >= start_date) & (cached_data['date'].dt.date <= end_date)
        return cached_data[mask].reset_index(drop=True)
    
    def _fetch_from_api(self, ticker, start_date, end_date):
        """Fetch data from API (Polygon.io or Yahoo Finance)"""
        # Try Polygon.io first if available
        if self.client:
            try:
                data = self._fetch_polygon_data(ticker, start_date, end_date)
                if data is not None and not data.empty:
                    print(f"✅ Got {len(data)} bars for {ticker} from Polygon.io")
                    return data
                print(f"⚠️ No Polygon data for {ticker}, falling back to Yahoo Finance...")
            except Exception as e:
                print(f"❌ Polygon.io error for {ticker}: {e}, falling back to Yahoo Finance...")
        
        # Fallback to Yahoo Finance with rate limiting
        return self._fetch_yahoo_data_with_retry(ticker, start_date, end_date)
    
    def clear_cache(self, ticker=None):
        """Clear cache for specific ticker or all tickers"""
        if ticker:
            cache_file = self._get_cache_filepath(ticker)
            if os.path.exists(cache_file):
                os.remove(cache_file)
                print(f"🗑️ Cleared cache for {ticker}")
            else:
                print(f"⚠️ No cache file found for {ticker}")
        else:
            # Clear all cache files
            cache_files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
            for cache_file in cache_files:
                os.remove(os.path.join(self.data_dir, cache_file))
            print(f"🗑️ Cleared all cache files ({len(cache_files)} files)")
    
    def get_cache_info(self):
        """Get information about cached data"""
        cache_files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
        
        if not cache_files:
            print("📭 No cached data found")
            return
        
        print(f"📊 Found {len(cache_files)} cached files:")
        
        for cache_file in sorted(cache_files):
            ticker = cache_file.replace('.csv', '')
            try:
                df = pd.read_csv(os.path.join(self.data_dir, cache_file))
                df['date'] = pd.to_datetime(df['date'])
                file_size = os.path.getsize(os.path.join(self.data_dir, cache_file)) / 1024  # KB
                print(f"  {ticker}: {len(df)} bars ({df['date'].min().date()} to {df['date'].max().date()}) - {file_size:.1f} KB")
            except Exception as e:
                print(f"  {ticker}: Error reading file - {e}")
    
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