import streamlit as st
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_info(
          st.secrets["gcp_service_account"]
      )

Account = "Freedom Solar"
client = bigquery.Client(credentials=credentials)

# Cache the data to avoid reloading on every interaction
@st.cache_data
def load_data():
    query = """
    SELECT * 
    FROM `heliose.heliose_segments.meta_adlevel`
    """  # Replace with actual table name
    df = client.query(query).to_dataframe()
    return df

# Function to filter data based on start and end date
def filter_data(df, start_date, end_date):
    df["Date"] = pd.to_datetime(df["Date"])  # Adjust to match your date column
    return df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

# Streamlit app
def main():
    st.title("BigQuery Data Dashboard")

    # Load data once at the beginning
    df = load_data()

    # Date filters
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.today())
    with col2:
        end_date = st.date_input("End Date", datetime.today())

    # Ensure valid date selection
    if start_date > end_date:
        st.error("End date must be after start date.")
        return

    # Filter the loaded data
    filtered_df = filter_data(df, start_date, end_date)

    # Display filtered data
    st.write("### Data Preview")
    st.dataframe(filtered_df)

if __name__ == "__main__":
    main()
