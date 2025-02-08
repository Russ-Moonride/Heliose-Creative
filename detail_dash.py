import streamlit as st
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
from google.oauth2 import service_account
import gspread

st.set_page_config(page_title="Heliose Creative Report", layout="wide", page_icon="🔬")

scope = [
    "https://www.googleapis.com/auth/bigquery",
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
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

    df.rename(columns={"Ad_Name__Facebook_Ads" : "Ad Name", "Ad_Set_Name__Facebook_Ads" : "Ad Set", "Campaign_Name__Facebook_Ads" : "Campaign Name", "Link_Clicks__Facebook_Ads" : "Clicks", "Impressions__Facebook_Ads" : "Impressions", "Amount_Spent__Facebook_Ads" : "Cost", 
                         "n_3_Second_Video_Views__Facebook_Ads" : "3 Sec Views", "Video_Watches_at_100__Facebook_Ads" : "Thruplays", "Leads__Facebook_Ads" : "Leads"}, inplace=True)
    return df

# Function to filter data based on start and end date
def filter_data(df, start_date, end_date):
    return df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

# Function to load data from Google Sheets
@st.cache_data
def load_gsheet_data():
    try:
        # Open the Google Sheet
        spreadsheet_id = "1-bBXJqtKJBqMwuTzuAjP_XwR35lNZQGe3iwr5plGqiU"  # Replace with your actual ID
        spreadsheet = gs_client.open_by_key(spreadsheet_id)


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
    data = load_data()

    # Load Ref table from google sheets
    ref_data = load_gsheet_data()

    # Map variables to ad names
    merged_data = pd.merge(data, ref_data, on="Ad Name", how="left")  # 'left' keeps all BigQuery data

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
    filtered_df = filter_data(merged_data, start_date, end_date)

    # Display filtered data
    st.write("### Creative Detail")
    # List of categorical variables to choose from
    categorical_vars = ["Batch", "Medium", "Hook", "Secondary Message", "Primary Imagery Style", "Secondary Imagery Style", "Copy Style", "Aesthetic", "Concept Description", "Video Duration", "Video Audio: Voice Over", "Video Audio: BG Music", "Video Close Message"]
    
    st.title("Dynamic Breakdown Dashboard")
    
    # User selects the breakdown order
    selected_vars = st.multiselect("Select breakdown order:", categorical_vars, default=["Batch", "Medium"])
    
    if selected_vars:
        # Group data dynamically based on selection
        grouped_data = merged_data.groupby(selected_vars).agg({"Clicks": "sum", "Impressions": "sum", "Cost" : "sum", "3 Sec Views" : "sum", "Thruplays" : "sum", "Leads" : "sum"}).reset_index()
    
        # Display results
        st.write("### Breakdown by Selected Variables")
        st.dataframe(grouped_data)
    else:
        st.write("Please select at least one variable to break down by.")

    st.divider()

if __name__ == "__main__":
    main()
