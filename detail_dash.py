import streamlit as st
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
from google.oauth2 import service_account
import gspread

st.set_page_config(page_title="Heliose Creative Report", layout="wide", page_icon="🔬")

# Set up Google Cloud credentials
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)

# Separate BigQuery client
bq_client = bigquery.Client(credentials=credentials)

# Separate Google Sheets client
gs_client = gspread.authorize(credentials)

# Cache the data to avoid reloading on every interaction
@st.cache_data
def load_data():
    query = """
    SELECT * 
    FROM `heliose.heliose_segments.meta_adlevel`
    """  # Replace with actual table name
    df = bq_client.query(query).to_dataframe()  # Use `bq_client` instead of `client`
    return df

# Function to filter data based on start and end date
def filter_data(df, start_date, end_date):
    return df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

# Function to load data from Google Sheets
@st.cache_data
def load_gsheet_data():
    sheet = gs_client.open("Your Google Sheet Name").sheet1  # Change as needed
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Streamlit app
def main():
    st.title("BigQuery & Google Sheets Data Dashboard")

    # Load BigQuery data
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
    st.write("### BigQuery Data Preview")
    st.dataframe(filtered_df)

    st.divider()

    # Load Google Sheets data
    ref_data = load_gsheet_data()
    st.write("### Google Sheets Data Preview")
    st.dataframe(ref_data)

if __name__ == "__main__":
    main()
