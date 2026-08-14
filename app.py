import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Page Configuration
st.set_page_config(
    page_title="Railway Earning Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to reduce top whitespace and make tables compact
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            padding-top: 4px;
            padding-bottom: 4px;
        }
    </style>
""", unsafe_allow_html=True)

# Supabase Connection
SUPABASE_URL = "postgresql://postgres.ggrpypensvabbvpyzqbx:pamcelllko2234723@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"

@st.cache_resource
def get_database_connection():
    return create_engine(SUPABASE_URL)

engine = get_database_connection()

# Mapping Helpers
MONTH_DAYS = {
    'Apr': 30, 'May': 31, 'Jun': 30, 'Jul': 31, 'Aug': 31, 'Sep': 30, 
    'Oct': 31, 'Nov': 30, 'Dec': 31, 'Jan': 31, 'Feb': 28, 'Mar': 31
}

MONTH_ORDER = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']

QUARTERS = {
    'Q1 (Apr-Jun)': ['Apr', 'May', 'Jun'],
    'Q2 (Jul-Sep)': ['Jul', 'Aug', 'Sep'],
    'Q3 (Oct-Dec)': ['Oct', 'Nov', 'Dec'],
    'Q4 (Jan-Mar)': ['Jan', 'Feb', 'Mar']
}

def format_session(raw_session):
    try:
        s = str(raw_session).split('.')[0].strip()
        if len(s) == 6:
            return f"{s[:4]}-{s[4:]}"
        return s
    except Exception:
        return str(raw_session)

def parse_session_to_raw(formatted_session):
    return formatted_session.replace('-', '')

st.title("🚄 Station Earning & Traffic Executive Dashboard")

# ----------------- SIDEBAR FILTERS -----------------
st.sidebar.header("🔍 Filter Options")

# Fetch Available Stations
try:
    with engine.connect() as conn:
        stations_df = pd.read_sql(text('SELECT DISTINCT "STATION_CODE" FROM booking'), conn)
        stations = sorted([str(s).strip() for s in stations_df['STATION_CODE'].dropna().unique().tolist()])
    selected_station = st.sidebar.selectbox("Select Station", stations)
except Exception as e:
    st.error(f"Error loading stations: {e}")
    st.stop()

# Fetch Available Sessions
try:
    with engine.connect() as conn:
        sessions_df = pd.read_sql(text('SELECT DISTINCT "SESSION" FROM booking ORDER BY "SESSION" DESC'), conn)
        raw_sessions = [str(s).split('.')[0].strip() for s in sessions_df['SESSION'].dropna().tolist()]
        formatted_sessions = [format_session(s) for s in raw_sessions]
    
    selected_formatted_session = st.sidebar.selectbox("Select Session", formatted_sessions)
    selected_raw_session = parse_session_to_raw(selected_formatted_session)
except Exception as e:
    st.error(f"Error loading sessions: {e}")
    st.stop()

# Calculate Previous Session
try:
    curr_yr = int(selected_raw_session[:4])
    prev_raw_session = f"{curr_yr - 1:04d}{int(selected_raw_session[4:]) - 1:02d}"
    prev_formatted_session = format_session(prev_raw_session)
except Exception:
    prev_raw_session = selected_raw_session
    prev_formatted_session = selected_formatted_session

# Time Filter Options
filter_type = st.sidebar.radio("Time Filter Type", ["Quarterly", "6 Months", "Full Year", "Last 3 Months", "Last 6 Months", "Custom Months"])

selected_months = []
if filter_type == "Quarterly":
    q = st.sidebar.selectbox("Select Quarter", list(QUARTERS.keys()))
    selected_months = QUARTERS[q]
elif filter_type == "6 Months":
    h = st.sidebar.selectbox("Select Half", ["H1 (Apr-Sep)", "H2 (Oct-Mar)"])
    selected_months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'] if "H1" in h else ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
elif filter_type == "Full Year":
    selected_months = MONTH_ORDER
elif filter_type == "Last 3 Months":
    end_m = st.sidebar.selectbox("Ending Month", MONTH_ORDER, index=5)
    idx = MONTH_ORDER.index(end_m)
    selected_months = MONTH_ORDER[max(0, idx-2):idx+1]
elif filter_type == "Last 6 Months":
    end_m = st.sidebar.selectbox("Ending Month", MONTH_ORDER, index=5)
    idx = MONTH_ORDER.index(end_m)
    selected_months = MONTH_ORDER[max(0, idx-5):idx+1]
else:
    selected_months = st.sidebar.multiselect("Select Months", MONTH_ORDER, default=['Apr', 'May', 'Jun'])

total_days = sum([MONTH_DAYS.get(m, 30) for m in selected_months])

# ----------------- DATA FETCHING -----------------
def fetch_head_earning(table_name, station, session, months, earning_col='EARNING'):
    if not months:
        return 0.0
    months_str = "','".join(months)
    query = f'''
        SELECT SUM("{earning_col}") as total_earning 
        FROM {table_name} 
        WHERE "STATION_CODE" = '{station}' 
          AND CAST("SESSION" AS TEXT) LIKE '{session}%' 
          AND "MONTH" IN ('{months_str}')
    '''
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
            val = df['total_earning'].iloc[0]
            return float(val) if pd.notnull(val) else 0.0
    except Exception:
        return 0.0

# Earnings Calculation
booking_curr = fetch_head_earning('booking', selected_station, selected_raw_session, selected_months, 'EARNING')
prs_curr = fetch_head_earning('reservation_org', selected_station, selected_raw_session, selected_months, 'EARNINGS')
goods_curr = fetch_head_earning('goods', selected_station, selected_raw_session, selected_months, 'OW_FRIEGHT')
parcel_curr = fetch_head_earning('parcel', selected_station, selected_raw_session, selected_months, 'OW_FRIEGHT')

booking_prev = fetch_head_earning('booking', selected_station, prev_raw_session, selected_months, 'EARNING')
prs_prev = fetch_head_earning('reservation_org', selected_station, prev_raw_session, selected_months, 'EARNINGS')
goods_prev = fetch_head_earning('goods', selected_station, prev_raw_session, selected_months, 'OW_FRIEGHT')
parcel_prev = fetch_head_earning('parcel', selected_station, prev_raw_session, selected_months, 'OW_FRIEGHT')

# ----------------- DASHBOARD DISPLAY -----------------
st.markdown(f"### 📍 Station: **{selected_station}** | Session: **{selected_formatted_session}** vs **{prev_formatted_session}**")

col1, col2, col3, col4 = st.columns(4)

def display_metric(col, title, curr, prev, days):
    per_day = curr / days if days > 0 else 0
    growth = ((curr - prev) / prev * 100) if prev > 0 else 0
    
    col.metric(
        label=f"{title} Total", 
        value=f"₹ {curr:,.0f}", 
        delta=f"{growth:+.1f}% vs Prev. Year"
    )
    col.caption(f"⏱️ **Per Day:** ₹ {per_day:,.0f} / day")

display_metric(col1, "Booking (Passenger)", booking_curr, booking_prev, total_days)
display_metric(col2, "PRS (Originating)", prs_curr, prs_prev, total_days)
display_metric(col3, "Goods Freight", goods_curr, goods_prev, total_days)
display_metric(col4, "Parcel Freight", parcel_curr, parcel_prev, total_days)

st.markdown("---")

# Detailed Data Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Booking", "PRS Org", "Goods", "Parcel", "Reservation"])

def show_tab_data(table_name):
    q = f'''
        SELECT * FROM {table_name} 
        WHERE "STATION_CODE" = '{selected_station}' 
          AND CAST("SESSION" AS TEXT) LIKE '{selected_raw_session}%'
    '''
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(q), conn)
            
            if df.empty:
                st.info("No records found for the selected station and session.")
                return

            # Drop unnecessary columns to save screen space
            drop_cols = ['STATION_CODE', 'SESSION', 'station_code', 'session']
            df = df.drop(columns=[c for c in drop_cols if c in df.columns])
            
            # Sort by Month Order
            if 'MONTH' in df.columns:
                df['MONTH_CAT'] = pd.Categorical(df['MONTH'], categories=MONTH_ORDER, ordered=True)
                df = df.sort_values('MONTH_CAT').drop(columns=['MONTH_CAT'])
                
            st.dataframe(
                df, 
                use_container_width=True, 
                hide_index=True
            )
    except Exception as e:
        st.warning(f"Unable to load table: {e}")

with tab1: show_tab_data('booking')
with tab2: show_tab_data('reservation_org')
with tab3: show_tab_data('goods')
with tab4: show_tab_data('parcel')
with tab5: show_tab_data('reservation')
