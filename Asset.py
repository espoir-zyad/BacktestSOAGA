import pandas as pd
import numpy as np

class Asset:
    def __init__(self, excel_file):
        """Initialize Asset class with historical data from Excel file"""
        self.data = pd.read_excel(excel_file)
        self.data['Date'] = pd.to_datetime(self.data['Date'])
        self.benchmark_data = self.data[['Date', 'BRVM C']].set_index('Date')
        self.data = self.data.set_index('Date')
        # Ensure all price columns are numeric
        price_columns = self.data.columns.difference(['BRVM C'])
        self.data[price_columns] = self.data[price_columns].apply(pd.to_numeric, errors='coerce')

    def calculate_performance(self, date, months=6):
        """Calculate 6-month performance for all assets except ORAC and SNTS"""
        end_date = pd.to_datetime(date)
        start_date = end_date - pd.DateOffset(months=months)
        
        mask = (self.data.index >= start_date) & (self.data.index <= end_date)
        period_data = self.data[mask]
        
        if period_data.empty:
            raise ValueError(f"No data found between {start_date} and {end_date}")
            
        # Calculate performance using numeric values
        start_prices = period_data.iloc[0]
        end_prices = period_data.iloc[-1]
        performance = ((end_prices - start_prices) / start_prices * 100).astype(float)
        
        # Remove ORAC, SNTS and BRVM C from performance calculation
        performance = performance.drop(['ORAC', 'SNTS', 'BRVM C'], errors='ignore')
        
        return performance

    def get_top_performers(self, date, n=18):
        """Get top 18 performers excluding ORAC and SNTS"""
        performance = self.calculate_performance(date)
        performance = performance.astype(float)
        return performance.nlargest(n)

    def get_current_prices(self, date):
        """Get current prices for all assets at given date"""
        date = pd.to_datetime(date)
        try:
            prices = self.data.loc[date].drop('BRVM C')
            return prices.astype(float)
        except KeyError:
            raise KeyError(f"No data available for date {date}")

    def get_benchmark_data(self, start_date=None, end_date=None):
        """Return BRVM C benchmark data for specified date range"""
        if start_date and end_date:
           start_date = pd.to_datetime(start_date)
           end_date = pd.to_datetime(end_date)
           mask = (self.data.index >= start_date) & (self.data.index <= end_date)
           benchmark_data = self.data.loc[mask, 'BRVM C']
           # Rebase to 100
           benchmark_data = 100 * benchmark_data / benchmark_data.iloc[0]
           return benchmark_data
        return self.data['BRVM C']