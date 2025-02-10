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

def format_percentage(value):

    if pd.isna(value):  # Handle NaN values
        return "N/A"
    return f"{value:.1%}"  # Converts 0.25 to '25.0%'


def format_dollar(value):

    if pd.isna(value):  # Handle NaN values
        return "N/A"
    return f"${value:,.2f}"  # Converts 1234.56 to '$1,234.56'


# Streamlit app
def main():
    st.title("Heliose Creative Report")

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
    st.write("### Creative Detail Breakdown")
    # List of categorical variables to choose from
    categorical_vars = ["Batch", "Medium", "Hook", "Secondary Message", "Primary Imagery Style", "Secondary Imagery Style", "Copy Style", "Aesthetic", "Concept Description", "Video Duration", "Video Audio: Voice Over", "Video Audio: BG Music", "Video Close Message"]
    
    # User selects the breakdown order
    selected_vars = st.multiselect("Select breakdown order:", categorical_vars, default=["Batch", "Medium"])
    
    if selected_vars:
        # Group data dynamically based on selection
        grouped_data = merged_data.groupby(selected_vars).agg({"Clicks": "sum", "Impressions": "sum", "Cost" : "sum", "3 Sec Views" : "sum", "Thruplays" : "sum", "Leads" : "sum"}).reset_index()

        # Make the columns we need
        grouped_data["CTR"] = round(grouped_data["Clicks"]/grouped_data["Impressions"], 4).apply(format_percentage)
        grouped_data["CPC"] = round(grouped_data["Cost"] / grouped_data["Clicks"], 2)
        grouped_data["CPM"] = round((grouped_data["Cost"] / grouped_data["Impressions"]) * 1000, 2)
        grouped_data["3 Sec View Rate"] = round(grouped_data["3 Sec Views"] / grouped_data["Impressions"], 2)
        grouped_data["Vid Complete Rate"] = round(grouped_data["Thruplays"] / grouped_data["Impressions"], 2)
        grouped_data["CPL"] = round(grouped_data["Cost"] / grouped_data["Leads"], 2)
        grouped_data["CVR (Click)"] = round(grouped_data["Leads"] / grouped_data["Clicks"], 2)

        

        # Organize cols
        metric_order = ["Impressions", "Clicks", "CTR", "Cost", "CPC", "CPM", "3 Sec Views", "3 Sec View Rate", "Thruplays", "Vid Complete Rate", "Leads", "CPL", "CVR (Click)"]
        grouped_data = grouped_data[selected_vars + metric_order]
        
        # Display results
        st.write("### Breakdown by Selected Variables")
        st.dataframe(grouped_data, use_container_width=True)

    else:
        st.write("Please select at least one variable to break down by.")

    st.divider()

if __name__ == "__main__":
    main()
