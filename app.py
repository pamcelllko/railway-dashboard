import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# Page Configuration
st.set_page_config(page_title="Railway Earning Dashboard", layout="wide")

# Supabase Connection
SUPABASE_URL = "postgresql://postgres:YOUR_PASSWORD_HERE@db.xxxxxxx.supabase.co:5432/postgres"

@st.cache_resource
def get_database_connection():
    return create_engine(SUPABASE_URL)

engine = get_database_connection()

# Days in Months Mapping
MONTH_DAYS = {
    'Apr': 30, 'May': 31, 'Jun': 30, 'Jul': 31, 'Aug': 31, 'Sep': 30, 
    'Oct': 31, 'Nov': 30, 'Dec': 31, 'Jan': 31, 'Feb': 28, 'Mar': 31
}
QUARTERS = {
    'Q1 (Apr-Jun)': ['Apr', 'May', 'Jun'],
    'Q2 (Jul-Sep)': ['Jul', 'Aug', 'Sep'],
    'Q3 (Oct-Dec)': ['Oct', 'Nov', 'Dec'],
    'Q4 (Jan-Mar)': ['Jan', 'Feb', 'Mar']
}

st.title("🚄 Station Earning & Traffic Executive Dashboard")

# ----------------- SIDEBAR FILTERS -----------------
st.sidebar.header("🔍 Filter Options")

# Fetch Available Stations
try:
    stations = pd.read_sql("SELECT DISTINCT station_cod FROM booking", engine)['station_cod'].tolist()
    selected_station = st.sidebar.selectbox("Select Station", sorted(stations))
except Exception as e:
    st.error("Error loading stations. Please check database connection.")
    st.stop()

# Fetch Available Sessions
sessions = pd.read_sql("SELECT DISTINCT session FROM booking ORDER BY session DESC", engine)['session'].tolist()
selected_session = st.sidebar.selectbox("Select Current Session", sessions)

# Previous Session Logic (e.g. 202425 -> 202324)
curr_yr = int(selected_session[:4])
prev_session = f"{curr_yr - 1:04d}{int(selected_session[4:]) - 1:02d}"

# Filter Type
filter_type = st.sidebar.radio("Time Filter Type", ["Quarterly", "6 Months", "Full Year", "Custom Months"])

selected_months = []
if filter_type == "Quarterly":
    q = st.sidebar.selectbox("Select Quarter", list(QUARTERS.keys()))
    selected_months = QUARTERS[q]
elif filter_type == "6 Months":
    h = st.sidebar.selectbox("Select Half", ["H1 (Apr-Sep)", "H2 (Oct-Mar)"])
    selected_months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'] if "H1" in h else ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
elif filter_type == "Full Year":
    selected_months = list(MONTH_DAYS.keys())
else:
    selected_months = st.sidebar.multiselect("Select Months", list(MONTH_DAYS.keys()), default=['Apr', 'May', 'Jun'])

# Calculate Total Days
total_days = sum([MONTH_DAYS.get(m, 30) for m in selected_months])

# ----------------- DATA FETCHING & COMPUTATION -----------------
def fetch_head_earning(table_name, station, session, months, earning_col='earning'):
    months_str = "','".join(months)
    query = f"""
        SELECT SUM({earning_col}) as total_earning 
        FROM {table_name} 
        WHERE station_cod = '{station}' 
          AND session = '{session}' 
          AND month IN ('{months_str}')
    """
    df = pd.read_sql(query, engine)
    val = df['total_earning'].iloc[0]
    return float(val) if val is not None else 0.0

# Current Year Earnings
booking_curr = fetch_head_earning('booking', selected_station, selected_session, selected_months, 'earning')
prs_curr = fetch_head_earning('reservation_org', selected_station, selected_session, selected_months, 'earnings')
goods_curr = fetch_head_earning('goods', selected_station, selected_session, selected_months, 'ow_friegh')
parcel_curr = fetch_head_earning('parcel', selected_station, selected_session, selected_months, 'ow_friegh')

# Last Year Earnings (Corresponding Period)
booking_prev = fetch_head_earning('booking', selected_station, prev_session, selected_months, 'earning')
prs_prev = fetch_head_earning('reservation_org', selected_station, prev_session, selected_months, 'earnings')
goods_prev = fetch_head_earning('goods', selected_station, prev_session, selected_months, 'ow_friegh')
parcel_prev = fetch_head_earning('parcel', selected_station, prev_session, selected_months, 'ow_friegh')

# ----------------- DASHBOARD DISPLAY -----------------
st.subheader(f"📍 Station: {selected_station} | Session: {selected_session} vs {prev_session}")

col1, col2, col3, col4 = st.columns(4)

def display_metric(col, title, curr, prev, days):
    per_day = curr / days if days > 0 else 0
    growth = ((curr - prev) / prev * 100) if prev > 0 else 0
    
    col.metric(
        label=f"{title} Total", 
        value=f"₹ {curr:,.0f}", 
        delta=f"{growth:+.1f}% vs Last Year"
    )
    col.caption(f"⏱️ **Per Day:** ₹ {per_day:,.0f} / day")

display_metric(col1, "Booking (Passenger)", booking_curr, booking_prev, total_days)
display_metric(col2, "PRS (Originating)", prs_curr, prs_prev, total_days)
display_metric(col3, "Goods Freight", goods_curr, goods_prev, total_days)
display_metric(col4, "Parcel Freight", parcel_curr, parcel_prev, total_days)

st.divider()

# Detailed Data Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Booking", "PRS Org", "Goods", "Parcel", "Reservation"])

def show_tab_data(table_name):
    q = f"SELECT * FROM {table_name} WHERE station_cod = '{selected_station}' AND session = '{selected_session}'"
    df = pd.read_sql(q, engine)
    st.dataframe(df, use_container_width=True)

with tab1: show_tab_data('booking')
with tab2: show_tab_data('reservation_org')
with tab3: show_tab_data('goods')
with tab4: show_tab_data('parcel')
with tab5: show_tab_data('reservation')
