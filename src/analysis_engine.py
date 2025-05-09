import pandas as pd
import numpy as np

class MetricsAnalysisEngine:
    def __init__(self, dataframe):
        """
        Initializes the MetricsAnalysisEngine with a pandas DataFrame.
        The DataFrame is expected to have columns like 'Date', 'Campaign Name', 
        'Impressions', 'Clicks', 'Spend', 'Sales', 'Orders', etc.
        """
        if not isinstance(dataframe, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        self.df = dataframe.copy()
        self._preprocess_data()

    def _preprocess_data(self):
        """Basic preprocessing for essential numeric columns."""
        numeric_cols = ['Impressions', 'Clicks', 'Spend', 'Sales', 'Orders']
        for col in numeric_cols:
            if col in self.df.columns:
                # Convert to numeric, coercing errors to NaN, then fill NaN with 0
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
            else:
                # If an essential column is missing, create it and fill with 0
                # This makes the class more robust to slightly different CSVs
                # but a warning should be logged in a real scenario.
                print(f"Warning: Column '{col}' not found. Initializing with zeros.")
                self.df[col] = 0

        # Ensure 'Date' column is in datetime format if it exists
        if 'Date' in self.df.columns:
            try:
                self.df['Date'] = pd.to_datetime(self.df['Date'])
            except Exception as e:
                print(f"Warning: Could not parse 'Date' column: {e}. Date-based filtering might not work as expected.")

    def get_total_impressions(self):
        return self.df['Impressions'].sum()

    def get_total_clicks(self):
        return self.df['Clicks'].sum()

    def get_total_spend(self):
        return self.df['Spend'].sum()

    def get_total_sales(self):
        return self.df['Sales'].sum()

    def get_total_orders(self):
        return self.df['Orders'].sum()

    def calculate_ctr(self):
        """Click-Through Rate = (Total Clicks / Total Impressions) * 100"""
        impressions = self.get_total_impressions()
        clicks = self.get_total_clicks()
        return (clicks / impressions) * 100 if impressions > 0 else 0

    def calculate_cpc(self):
        """Cost Per Click = Total Spend / Total Clicks"""
        spend = self.get_total_spend()
        clicks = self.get_total_clicks()
        return spend / clicks if clicks > 0 else 0

    def calculate_cvr(self):
        """Conversion Rate = (Total Orders / Total Clicks) * 100"""
        orders = self.get_total_orders()
        clicks = self.get_total_clicks()
        return (orders / clicks) * 100 if clicks > 0 else 0

    def calculate_acos(self):
        """Advertising Cost of Sales = (Total Spend / Total Sales) * 100"""
        spend = self.get_total_spend()
        sales = self.get_total_sales()
        return (spend / sales) * 100 if sales > 0 else 0
    
    def calculate_roas(self):
        """Return on Ad Spend = Total Sales / Total Spend"""
        sales = self.get_total_sales()
        spend = self.get_total_spend()
        return sales / spend if spend > 0 else 0

    def get_campaign_performance_summary(self):
        """Returns a dictionary of all key performance indicators."""
        summary = {
            'Total Impressions': self.get_total_impressions(),
            'Total Clicks': self.get_total_clicks(),
            'Total Spend': self.get_total_spend(),
            'Total Sales': self.get_total_sales(),
            'Total Orders': self.get_total_orders(),
            'Click-Through Rate (CTR)': self.calculate_ctr(),
            'Cost Per Click (CPC)': self.calculate_cpc(),
            'Conversion Rate (CVR)': self.calculate_cvr(),
            'Advertising Cost of Sales (ACOS)': self.calculate_acos(),
            'Return on Ad Spend (ROAS)': self.calculate_roas()
        }
        return summary

    def get_keyword_performance(self, keyword_column='Keyword or Product Targeting', campaign_column='Campaign Name'):
        """
        Analyzes performance at the keyword level.
        Returns a DataFrame grouped by keyword, with aggregated metrics.
        Assumes 'Keyword or Product Targeting' and 'Campaign Name' columns exist.
        """
        if keyword_column not in self.df.columns or campaign_column not in self.df.columns:
            print(f"Warning: Required columns for keyword performance ('{keyword_column}', '{campaign_column}') not found.")
            return pd.DataFrame() # Return empty DataFrame

        # Ensure essential numeric columns exist for aggregation, fill with 0 if not
        agg_cols = ['Impressions', 'Clicks', 'Spend', 'Sales', 'Orders']
        for col in agg_cols:
            if col not in self.df.columns:
                self.df[col] = 0
        
        keyword_data = self.df.groupby([campaign_column, keyword_column]).agg(
            Total_Impressions=('Impressions', 'sum'),
            Total_Clicks=('Clicks', 'sum'),
            Total_Spend=('Spend', 'sum'),
            Total_Sales=('Sales', 'sum'),
            Total_Orders=('Orders', 'sum')
        ).reset_index()

        keyword_data['CTR'] = (keyword_data['Total_Clicks'] / keyword_data['Total_Impressions']) * 100
        keyword_data['CPC'] = keyword_data['Total_Spend'] / keyword_data['Total_Clicks']
        keyword_data['CVR'] = (keyword_data['Total_Orders'] / keyword_data['Total_Clicks']) * 100
        keyword_data['ACOS'] = (keyword_data['Total_Spend'] / keyword_data['Total_Sales']) * 100
        keyword_data['ROAS'] = keyword_data['Total_Sales'] / keyword_data['Total_Spend']

        # Handle potential NaN/inf values from division by zero
        keyword_data.replace([np.inf, -np.inf], np.nan, inplace=True)
        keyword_data.fillna(0, inplace=True)

        return keyword_data

# Example Usage (assuming you have a pandas DataFrame named `ppc_data`):
# engine = MetricsAnalysisEngine(ppc_data)
# summary_kpis = engine.get_campaign_performance_summary()
# print(summary_kpis)
# keyword_details = engine.get_keyword_performance()
# print(keyword_details.head())

