import streamlit as st
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
from google.oauth2 import service_account
import gspread

st.set_page_config(page_title="Heliose Creative Report", layout="wide", page_icon="🔬")

scope = [
    "https://www.googleapis.com/auth/bigquery",
    "https://www.googleapis.com/auth/cloud-platform"
]

# Set up Google Cloud credentials with correct scope
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes = scope
)



# Initialize separate clients
bq_client = bigquery.Client(credentials=credentials)  # BigQuery
gs_client = gspread.authorize(credentials)  # Google Sheets

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
    try:
        # Open the Google Sheet
        spreadsheet = gs_client.open("Heliose Ad Tracking Creative Performance")  # Ensure this is the correct sheet name

        # Select the first worksheet (or specify by name)
        sheet = spreadsheet.worksheet("Meta_AdName_REF")  # You can also use: spreadsheet.worksheet("Sheet Name")

        # Get all records
        data = sheet.get_all_records()

        # Convert to DataFrame
        return pd.DataFrame(data)

    except Exception as e:
        st.error(f"Error loading Google Sheets data: {e}")
        return pd.DataFrame()  # Return an empty dataframe on failure

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
