import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Page Configuration
st.set_page_config(
    page_title="Railway Earning Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
        div[data-testid="stMetricValue"] { font-size: 1.4rem !important; }
        .stTabs [data-baseweb="tab-list"] { gap: 6px; }
        .stTabs [data-baseweb="tab"] { padding-top: 4px; padding-bottom: 4px; }
    </style>
""", unsafe_allow_html=True)

# Supabase Connection
SUPABASE_URL = "postgresql://postgres.ggrpypensvabbvpyzqbx:pamcelllko2234723@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"

@st.cache_resource
def get_database_connection():
    return create_engine(SUPABASE_URL)

engine = get_database_connection()

# Constants & Mappings
MONTH_DAYS = {'Apr': 30, 'May': 31, 'Jun': 30, 'Jul': 31, 'Aug': 31, 'Sep': 30, 'Oct': 31, 'Nov': 30, 'Dec': 31, 'Jan': 31, 'Feb': 28, 'Mar': 31}
MONTH_ORDER = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
QUARTERS = {
    'Q1 (Apr-Jun)': ['Apr', 'May', 'Jun'],
    'Q2 (Jul-Sep)': ['Jul', 'Aug', 'Sep'],
    'Q3 (Oct-Dec)': ['Oct', 'Nov', 'Dec'],
    'Q4 (Jan-Mar)': ['Jan', 'Feb', 'Mar']
}

def format_session(raw_s):
    s = str(raw_s).split('.')[0].strip()
    return f"{s[:4]}-{s[4:]}" if len(s) == 6 else s

def parse_session(fmt_s):
    return fmt_s.replace('-', '')

st.title("🚄 Station Earning & Traffic Executive Dashboard")

# ----------------- SIDEBAR -----------------
st.sidebar.header("🔍 Filter Options")

# Fetch Stations
try:
    with engine.connect() as conn:
        stns = sorted(pd.read_sql(text('SELECT DISTINCT "STATION_CODE" FROM booking'), conn)['STATION_CODE'].dropna().unique().tolist())
    selected_station = st.sidebar.selectbox("Select Station", stns)
except Exception as e:
    st.error(f"Error loading stations: {e}"); st.stop()

# Fetch Sessions
try:
    with engine.connect() as conn:
        raw_sess = [str(s).split('.')[0].strip() for s in pd.read_sql(text('SELECT DISTINCT "SESSION" FROM booking ORDER BY "SESSION" DESC'), conn)['SESSION'].dropna().tolist()]
        fmt_sess = [format_session(s) for s in raw_sess]
    selected_fmt_session = st.sidebar.selectbox("Select Session", fmt_sess)
    selected_raw_session = parse_session(selected_fmt_session)
except Exception as e:
    st.error(f"Error loading sessions: {e}"); st.stop()

# Calculate Prev Session
curr_yr = int(selected_raw_session[:4])
prev_raw_session = f"{curr_yr - 1:04d}{int(selected_raw_session[4:]) - 1:02d}"
prev_fmt_session = format_session(prev_raw_session)

# Time Filter Options
filter_type = st.sidebar.radio("Time Filter Type", ["Quarterly", "6 Months", "Full Year", "Last 3 Months", "Last 6 Months", "Custom Months"])

# Filter Logic Builder
query_filters_curr = [] # List of tuples: (session, month_list)
query_filters_prev = []
display_period_text = ""

if filter_type in ["Quarterly", "6 Months", "Full Year", "Custom Months"]:
    if filter_type == "Quarterly":
        q = st.sidebar.selectbox("Select Quarter", list(QUARTERS.keys()))
        selected_months = QUARTERS[q]
    elif filter_type == "6 Months":
        h = st.sidebar.selectbox("Select Half", ["H1 (Apr-Sep)", "H2 (Oct-Mar)"])
        selected_months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'] if "H1" in h else ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
    elif filter_type == "Full Year":
        selected_months = MONTH_ORDER
    else:
        selected_months = st.sidebar.multiselect("Select Months", MONTH_ORDER, default=['Apr', 'May', 'Jun'])

    query_filters_curr = [(selected_raw_session, selected_months)]
    query_filters_prev = [(prev_raw_session, selected_months)]
    display_period_text = f"Months: {', '.join(selected_months)}"

else: # Rolling Filters (Last 3 or Last 6 Months across sessions if needed)
    end_m = st.sidebar.selectbox("Current/Ending Month", MONTH_ORDER, index=3) # Default Jul
    n_months = 3 if filter_type == "Last 3 Months" else 6
    end_idx = MONTH_ORDER.index(end_m)
    
    if end_idx >= n_months - 1:
        # Fits inside same session
        curr_m_list = MONTH_ORDER[end_idx - n_months + 1 : end_idx + 1]
        query_filters_curr = [(selected_raw_session, curr_m_list)]
        query_filters_prev = [(prev_raw_session, curr_m_list)]
    else:
        # Crosses financial year (e.g., Feb, Mar of prev session + Apr, May, Jun, Jul of current)
        overlap_prev_count = n_months - (end_idx + 1)
        prev_m_list = MONTH_ORDER[-overlap_prev_count:]
        curr_m_list = MONTH_ORDER[:end_idx + 1]
        
        query_filters_curr = [(prev_raw_session, prev_m_list), (selected_raw_session, curr_m_list)]
        
        # Corresponding prev period calculation
        prev_prev_raw_session = f"{curr_yr - 2:04d}{int(selected_raw_session[4:]) - 2:02d}"
        query_filters_prev = [(prev_prev_raw_session, prev_m_list), (prev_raw_session, curr_m_list)]

    display_period_text = f"{filter_type} (Ending {end_m})"

# Total Days Calculation
total_days = 0
for sess, m_list in query_filters_curr:
    total_days += sum([MONTH_DAYS.get(m, 30) for m in m_list])

# ----------------- FETCHING DATA -----------------
def fetch_total_earning(table_name, filters_list, earning_col='EARNING'):
    total = 0.0
    with engine.connect() as conn:
        for sess, m_list in filters_list:
            if not m_list: continue
            m_str = "','".join(m_list)
            q = f'''
                SELECT SUM("{earning_col}") as val FROM {table_name}
                WHERE "STATION_CODE" = '{selected_station}' 
                  AND CAST("SESSION" AS TEXT) LIKE '{sess}%' 
                  AND "MONTH" IN ('{m_str}')
            '''
            try:
                val = pd.read_sql(text(q), conn)['val'].iloc[0]
                if pd.notnull(val): total += float(val)
            except Exception: pass
    return total

# Earnings
b_curr = fetch_total_earning('booking', query_filters_curr, 'EARNING')
p_curr = fetch_total_earning('reservation_org', query_filters_curr, 'EARNINGS')
g_curr = fetch_total_earning('goods', query_filters_curr, 'OW_FRIEGHT')
pr_curr = fetch_total_earning('parcel', query_filters_curr, 'OW_FRIEGHT')

b_prev = fetch_total_earning('booking', query_filters_prev, 'EARNING')
p_prev = fetch_total_earning('reservation_org', query_filters_prev, 'EARNINGS')
g_prev = fetch_total_earning('goods', query_filters_prev, 'OW_FRIEGHT')
pr_prev = fetch_total_earning('parcel', query_filters_prev, 'OW_FRIEGHT')

# ----------------- DISPLAY -----------------
st.markdown(f"### 📍 Station: **{selected_station}** | Period: **{display_period_text}**")
st.caption(f"🗓️ Comparing Current Period vs Previous Year Period ({total_days} Days Selected)")

col1, col2, col3, col4 = st.columns(4)

def metric_box(col, title, curr, prev, days):
    per_day = curr / days if days > 0 else 0
    growth = ((curr - prev) / prev * 100) if prev > 0 else 0
    col.metric(label=f"{title}", value=f"₹ {curr:,.0f}", delta=f"{growth:+.1f}% vs Last Year")
    col.caption(f"⏱️ **Per Day:** ₹ {per_day:,.0f}/day")

metric_box(col1, "Booking (Passenger)", b_curr, b_prev, total_days)
metric_box(col2, "PRS (Originating)", p_curr, p_prev, total_days)
metric_box(col3, "Goods Freight (O/W)", g_curr, g_prev, total_days)
metric_box(col4, "Parcel Freight (O/W)", pr_curr, pr_prev, total_days)

st.markdown("---")

# ----------------- TABLES SECTION -----------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Booking", "PRS Org", "Combined Passenger", "Goods", "Parcel", "Reservation"
])

def fetch_table_filtered(table_name):
    frames = []
    with engine.connect() as conn:
        for sess, m_list in query_filters_curr:
            m_str = "','".join(m_list)
            q = f'''
                SELECT * FROM {table_name} 
                WHERE "STATION_CODE" = '{selected_station}' 
                  AND CAST("SESSION" AS TEXT) LIKE '{sess}%' 
                  AND "MONTH" IN ('{m_str}')
            '''
            try:
                df = pd.read_sql(text(q), conn)
                if not df.empty:
                    df['FMT_SESSION'] = format_session(sess)
                    frames.append(df)
            except Exception: pass
            
    if not frames:
        return pd.DataFrame()
        
    full_df = pd.concat(frames, ignore_index=True)
    drop_cols = ['STATION_CODE', 'SESSION', 'station_code', 'session']
    full_df = full_df.drop(columns=[c for c in drop_cols if c in full_df.columns])
    
    # Sort logically
    if 'MONTH' in full_df.columns:
        full_df['MONTH_CAT'] = pd.Categorical(full_df['MONTH'], categories=MONTH_ORDER, ordered=True)
        full_df = full_df.sort_values(['FMT_SESSION', 'MONTH_CAT']).drop(columns=['MONTH_CAT'])
        
    return full_df

def render_table_with_totals(df, title):
    if df.empty:
        st.info(f"No records for {title} in selected period.")
        return
        
    # Calculate Numeric Totals
    num_cols = df.select_dtypes(include=['number']).columns
    total_row = {c: df[c].sum() for c in num_cols}
    
    if 'MONTH' in df.columns: total_row['MONTH'] = 'TOTAL'
    if 'FMT_SESSION' in df.columns: total_row['FMT_SESSION'] = 'ALL'
    
    df_totals = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
    st.dataframe(df_totals, use_container_width=True, hide_index=True)

with tab1:
    render_table_with_totals(fetch_table_filtered('booking'), "Booking")

with tab2:
    render_table_with_totals(fetch_table_filtered('reservation_org'), "PRS Org")

with tab3: # Combined Passenger Table (Booking + PRS Org)
    df_b = fetch_table_filtered('booking')
    df_p = fetch_table_filtered('reservation_org')
    
    if not df_b.empty and not df_p.empty:
        # Merge on Session and Month
        m_df = pd.merge(df_b, df_p, on=['FMT_SESSION', 'MONTH'], suffixes=('_Booking', '_PRS'))
        combined = pd.DataFrame()
        combined['Session'] = m_df['FMT_SESSION']
        combined['Month'] = m_df['MONTH']
        combined['Total Passengers'] = m_df.get('PASSENGERS_Booking', 0) + m_df.get('PASSENGERS', 0)
        combined['Booking Earning'] = m_df.get('EARNING', 0)
        combined['PRS Earning'] = m_df.get('EARNINGS', 0)
        combined['Total Earning'] = combined['Booking Earning'] + combined['PRS Earning']
        
        render_table_with_totals(combined, "Combined Passenger")
    else:
        st.info("Combined data unavailable for selected period.")

with tab4:
    render_table_with_totals(fetch_table_filtered('goods'), "Goods")

with tab5:
    render_table_with_totals(fetch_table_filtered('parcel'), "Parcel")

with tab6:
    df_res = fetch_table_filtered('reservation')
    if 'NET_CASH' in df_res.columns:
        df_res = df_res.rename(columns={'NET_CASH': 'EARNING (NET_CASH)'})
    render_table_with_totals(df_res, "Reservation")
