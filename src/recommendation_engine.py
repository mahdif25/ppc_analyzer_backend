import pandas as pd

class RecommendationEngine:
    def __init__(self, kpi_data, keyword_data):
        """
        Initializes the RecommendationEngine with KPI summary and keyword-level performance data.
        kpi_data: A dictionary containing overall campaign KPIs (e.g., from MetricsAnalysisEngine.get_campaign_performance_summary()).
        keyword_data: A pandas DataFrame with keyword-level metrics (e.g., from MetricsAnalysisEngine.get_keyword_performance()).
        """
        self.kpi_data = kpi_data
        self.keyword_data = keyword_data
        self.recommendations = []

    def generate_recommendations(self):
        """Generates actionable recommendations based on PPC data and predefined rules."""
        self.recommendations = [] # Clear previous recommendations

        # Rule 1: High ACOS Keywords - Suggest pausing or bid reduction
        # Assuming kpi_data has an 'Advertising Cost of Sales (ACOS)' field and keyword_data has 'ACOS' and 'Keyword or Product Targeting'
        # This example uses a threshold of 50% ACOS as "high". This should be configurable.
        if 'ACOS' in self.keyword_data.columns:
            high_acos_keywords = self.keyword_data[self.keyword_data['ACOS'] > 50]
            if not high_acos_keywords.empty:
                for index, row in high_acos_keywords.iterrows():
                    keyword = row['Keyword or Product Targeting']
                    campaign = row['Campaign Name']
                    acos = row['ACOS']
                    self.recommendations.append(
                        f"High ACOS Alert: Keyword acility_name{keyword}\" in campaign acility_name{campaign}\" has an ACOS of {acos:.2f}%. Consider pausing or reducing bid."
                    )

        # Rule 2: Low CTR Keywords - Suggest reviewing ad copy or targeting
        # Assuming keyword_data has 'CTR' (Click-Through Rate) and 'Impressions'
        # This example uses a threshold of < 1% CTR for keywords with significant impressions (>1000) as "low".
        if 'CTR' in self.keyword_data.columns and 'Total_Impressions' in self.keyword_data.columns:
            low_ctr_keywords = self.keyword_data[(self.keyword_data['CTR'] < 1) & (self.keyword_data['Total_Impressions'] > 1000)]
            if not low_ctr_keywords.empty:
                for index, row in low_ctr_keywords.iterrows():
                    keyword = row['Keyword or Product Targeting']
                    campaign = row['Campaign Name']
                    ctr = row['CTR']
                    self.recommendations.append(
                        f"Low CTR: Keyword acility_name{keyword}\" in campaign acility_name{campaign}\" has a CTR of {ctr:.2f}%. Review ad copy/relevance or consider pausing."
                    )

        # Rule 3: High Performing Keywords (Low ACOS, High Sales/Orders) - Suggest increasing bid or budget
        if 'ACOS' in self.keyword_data.columns and 'Total_Sales' in self.keyword_data.columns:
            # Example: ACOS < 20% and Sales > some threshold (e.g., 1000 in currency)
            # For simplicity, let's assume 'Total_Sales' is a numeric value indicative of high performance.
            # A more robust implementation would define "high sales" based on context.
            high_performing_keywords = self.keyword_data[(self.keyword_data['ACOS'] < 20) & (self.keyword_data['Total_Sales'] > 100)] # Assuming sales > 100 is good
            if not high_performing_keywords.empty:
                for index, row in high_performing_keywords.iterrows():
                    keyword = row['Keyword or Product Targeting']
                    campaign = row['Campaign Name']
                    self.recommendations.append(
                        f"High Performer: Keyword acility_name{keyword}\" in campaign acility_name{campaign}\" is performing well (ACOS: {row['ACOS']:.2f}%, Sales: {row['Total_Sales']}). Consider increasing bid/budget."
                    )
        
        # Rule 4: Keywords with high spend but low conversion (Orders/Clicks)
        if 'Total_Spend' in self.keyword_data.columns and 'Total_Orders' in self.keyword_data.columns and 'Total_Clicks' in self.keyword_data.columns:
            # Example: Spend > 50 (currency) and Orders < 1, but Clicks > 10
            ineffective_spend_keywords = self.keyword_data[
                (self.keyword_data['Total_Spend'] > 50) & 
                (self.keyword_data['Total_Orders'] < 1) & 
                (self.keyword_data['Total_Clicks'] > 10)
            ]
            if not ineffective_spend_keywords.empty:
                for index, row in ineffective_spend_keywords.iterrows():
                    keyword = row['Keyword or Product Targeting']
                    campaign = row['Campaign Name']
                    self.recommendations.append(
                        f"Ineffective Spend: Keyword acility_name{keyword}\" in campaign acility_name{campaign}\" has high spend ({row['Total_Spend']}) with low/no orders. Review landing page or keyword relevance."
                    )

        if not self.recommendations:
            self.recommendations.append("No specific recommendations based on current data and rules. Campaign performance appears stable or data is insufficient.")

        return self.recommendations

    def get_formatted_recommendations(self):
        if not self.recommendations:
            self.generate_recommendations() # Ensure recommendations are generated
        
        formatted_output = "## PPC Campaign Recommendations:\n\n"
        if not self.recommendations or self.recommendations[0].startswith("No specific recommendations"):
             formatted_output += "- No specific recommendations based on current data and rules. Campaign performance appears stable or data is insufficient."
             return formatted_output

        for i, rec in enumerate(self.recommendations):
            formatted_output += f"{i+1}. {rec}\n"
        return formatted_output

# Example Usage (after running analysis_engine.py to get kpi_summary and keyword_df):
# Assuming kpi_summary and keyword_df are populated pandas DataFrames/dict

# Sample Data (replace with actual data from MetricsAnalysisEngine)
# kpi_summary_sample = {'Total Impressions': 10000, 'Total Clicks': 500, 'Total Spend': 200, 'Total Sales': 1000, 'Total Orders': 50, 'CTR': 5.0, 'CPC': 0.4, 'CVR': 10.0, 'ACOS': 20.0, 'ROAS': 5.0}
# keyword_data_sample = pd.DataFrame({
# 'Campaign Name': ['Campaign A', 'Campaign B', 'Campaign A', 'Campaign C'],
# 'Keyword or Product Targeting': ['keyword1', 'keyword2', 'keyword3', 'keyword4'],
# 'Total_Impressions': [1000, 1500, 500, 2000],
# 'Total_Clicks': [100, 120, 40, 180],
# 'Total_Spend': [50, 60, 25, 90],
# 'Total_Sales': [200, 150, 100, 400],
# 'Total_Orders': [10, 8, 5, 20],
# 'CTR': [10.0, 8.0, 8.0, 9.0],
# 'CPC': [0.5, 0.5, 0.625, 0.5],
# 'CVR': [10.0, 6.67, 12.5, 11.11],
# 'ACOS': [25.0, 40.0, 25.0, 22.5],
# 'ROAS': [4.0, 2.5, 4.0, 4.44]
# })

# rec_engine = RecommendationEngine(kpi_summary_sample, keyword_data_sample)
# recommendations = rec_engine.generate_recommendations()
# formatted_recommendations = rec_engine.get_formatted_recommendations()
# print(formatted_recommendations)

