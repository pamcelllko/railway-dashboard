import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# ----------------- PAGE CONFIGURATION -----------------
st.set_page_config(
    page_title="Railway Earning Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- CUSTOM CSS -----------------
st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
        div[data-testid="stMetricValue"] { font-size: 1.25rem !important; }
        .combined-card {
            background-color: #f0f2f6;
            border-radius: 8px;
            padding: 10px 14px;
            border-left: 5px solid #ff4b4b;
        }
        .stTabs [data-baseweb="tab-list"] { gap: 6px; }
        .stTabs [data-baseweb="tab"] { padding-top: 4px; padding-bottom: 4px; }
    </style>
""", unsafe_allow_html=True)

# ----------------- HELPER FUNCTIONS -----------------
def format_inr(number):
    try:
        if pd.isna(number) or number is None: return "0"
        val = float(number)
        s, *d = str(f"{val:.0f}").partition(".")
        r = ",".join([s[x-2:x] for x in range(3, len(s)+1, 2)][::-1] + [s[-3:]])
        return "".join([r] + d) if len(s) > 3 else s
    except Exception:
        return f"{number}"

def format_session(raw_s):
    s = str(raw_s).split('.')[0].strip()
    return f"{s[:4]}-{s[4:]}" if len(s) == 6 else s

def parse_session(fmt_s):
    return fmt_s.replace('-', '')

# ----------------- DATABASE CONNECTION -----------------
# Supabase Pooler Connection String
SUPABASE_URL = "postgresql://postgres.ggrpypensvabbvpyzqbx:pamcelllko2234723@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"

@st.cache_resource
def get_database_connection():
    return create_engine(SUPABASE_URL, pool_pre_ping=True)

engine = get_database_connection()

# ----------------- CONSTANTS & MAPPINGS -----------------
MONTH_DAYS = {'Apr': 30, 'May': 31, 'Jun': 30, 'Jul': 31, 'Aug': 31, 'Sep': 30, 'Oct': 31, 'Nov': 30, 'Dec': 31, 'Jan': 31, 'Feb': 28, 'Mar': 31}
MONTH_ORDER = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
QUARTERS = {
    'Q1 (Apr-Jun)': ['Apr', 'May', 'Jun'],
    'Q2 (Jul-Sep)': ['Jul', 'Aug', 'Sep'],
    'Q3 (Oct-Dec)': ['Oct', 'Nov', 'Dec'],
    'Q4 (Jan-Mar)': ['Jan', 'Feb', 'Mar']
}

st.title("🚄 Station Earning & Traffic Executive Dashboard")

# ----------------- SIDEBAR FILTERS -----------------
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
        fmt_sess = [format_session(s) for s in raw_sess if len(s) == 6]
    selected_fmt_session = st.sidebar.selectbox("Select Session", fmt_sess)
    selected_raw_session = parse_session(selected_fmt_session)
except Exception as e:
    st.error(f"Error loading sessions: {e}"); st.stop()

curr_yr = int(selected_raw_session[:4])
prev_raw_session = f"{curr_yr - 1:04d}{int(selected_raw_session[4:]) - 1:02d}"
prev_fmt_session = format_session(prev_raw_session)

# Time Filter Options
filter_type = st.sidebar.radio("Time Filter Type", ["Quarterly", "6 Months", "Full Year", "Last 3 Months", "Last 6 Months", "Custom Months"])

query_filters_curr = []
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

else: # Rolling Filters
    end_m = st.sidebar.selectbox("Current/Ending Month", MONTH_ORDER, index=3)
    n_months = 3 if filter_type == "Last 3 Months" else 6
    end_idx = MONTH_ORDER.index(end_m)
    
    if end_idx >= n_months - 1:
        curr_m_list = MONTH_ORDER[end_idx - n_months + 1 : end_idx + 1]
        query_filters_curr = [(selected_raw_session, curr_m_list)]
        query_filters_prev = [(prev_raw_session, curr_m_list)]
    else:
        overlap_prev_count = n_months - (end_idx + 1)
        prev_m_list = MONTH_ORDER[-overlap_prev_count:]
        curr_m_list = MONTH_ORDER[:end_idx + 1]
        
        query_filters_curr = [(prev_raw_session, prev_m_list), (selected_raw_session, curr_m_list)]
        prev_prev_raw_session = f"{curr_yr - 2:04d}{int(selected_raw_session[4:]) - 2:02d}"
        query_filters_prev = [(prev_prev_raw_session, prev_m_list), (prev_raw_session, curr_m_list)]

    display_period_text = f"{filter_type} (Ending {end_m})"

total_days = sum([sum([MONTH_DAYS.get(m, 30) for m in m_list]) for _, m_list in query_filters_curr])

# ----------------- 2-CRITERIA DATA FETCHING -----------------
def fetch_total(table_name, filters_list, col_name):
    total = 0.0
    with engine.connect() as conn:
        for sess, m_list in filters_list:
            if not m_list: continue
            m_str = "','".join(m_list)
            # Criteria 1: Session Match (e.g., 202526%)
            # Criteria 2: Month Exact Match (e.g., 'Apr', 'May')
            q = f'''
                SELECT SUM("{col_name}") as val FROM {table_name}
                WHERE "STATION_CODE" = '{selected_station}' 
                  AND CAST("SESSION" AS TEXT) LIKE '{sess}%' 
                  AND "MONTH" IN ('{m_str}')
            '''
            try:
                val = pd.read_sql(text(q), conn)['val'].iloc[0]
                if pd.notnull(val): total += float(val)
            except Exception: pass
    return total

# Dynamic Column Resolver for Passenger Counts
def get_pass_col(table_name):
    try:
        with engine.connect() as conn:
            cols = pd.read_sql(text(f'SELECT * FROM {table_name} LIMIT 1'), conn).columns
            cols = [c.upper() for c in cols]
            if 'PASSENGERS' in cols: return 'PASSENGERS'
            if 'PASSENGER' in cols: return 'PASSENGER'
    except Exception: pass
    return 'PASSENGERS'

pass_col_booking = get_pass_col('booking')
pass_col_prs = get_pass_col('reservation_org')

# Fetch Earnings & Passengers
b_ear_curr = fetch_total('booking', query_filters_curr, 'EARNING')
b_ear_prev = fetch_total('booking', query_filters_prev, 'EARNING')
b_pass_curr = fetch_total('booking', query_filters_curr, pass_col_booking)

p_ear_curr = fetch_total('reservation_org', query_filters_curr, 'EARNINGS')
p_ear_prev = fetch_total('reservation_org', query_filters_prev, 'EARNINGS')
p_pass_curr = fetch_total('reservation_org', query_filters_curr, pass_col_prs)

g_ear_curr = fetch_total('goods', query_filters_curr, 'OW_FRIEGHT')
g_ear_prev = fetch_total('goods', query_filters_prev, 'OW_FRIEGHT')

pr_ear_curr = fetch_total('parcel', query_filters_curr, 'OW_FRIEGHT')
pr_ear_prev = fetch_total('parcel', query_filters_prev, 'OW_FRIEGHT')

# Combined Passenger Calculation
comb_pass_curr = b_pass_curr + p_pass_curr
comb_ear_curr = b_ear_curr + p_ear_curr
comb_ear_prev = b_ear_prev + p_ear_prev

# ----------------- DISPLAY METRICS -----------------
st.markdown(f"### 📍 Station: **{selected_station}** | Period: **{display_period_text}**")
st.caption(f"🗓️ Current Period vs Previous Year Period ({total_days} Days Selected)")

# Metric Columns
c1, c2, c3, c4, c5 = st.columns([1.2, 1, 1, 1, 1])

with c1:
    comb_growth = ((comb_ear_curr - comb_ear_prev) / comb_ear_prev * 100) if comb_ear_prev > 0 else 0
    pass_per_day = comb_pass_curr / total_days if total_days > 0 else 0
    ear_per_day = comb_ear_curr / total_days if total_days > 0 else 0
    
    st.markdown(f"""
        <div class="combined-card">
            <div style="font-size: 0.85rem; font-weight: bold; color: #333;">👥 Combined Passenger (PRS+Booking)</div>
            <div style="font-size: 0.8rem; margin-top:2px;"><b>Pass:</b> {format_inr(comb_pass_curr)} | <b>Earning:</b> ₹ {format_inr(comb_ear_curr)}</div>
            <div style="font-size: 0.75rem; color: #555; margin-top:2px;"><b>Pass/Day:</b> {format_inr(pass_per_day)} | <b>Ear/Day:</b> ₹ {format_inr(ear_per_day)}</div>
            <div style="font-size: 0.75rem; color: {'green' if comb_growth>=0 else 'red'}; font-weight:bold;">{comb_growth:+.1f}% vs Prev. Year</div>
        </div>
    """, unsafe_allow_html=True)

def metric_box(col, title, curr, prev, days):
    per_day = curr / days if days > 0 else 0
    growth = ((curr - prev) / prev * 100) if prev > 0 else 0
    col.metric(label=title, value=f"₹ {format_inr(curr)}", delta=f"{growth:+.1f}% vs Prev. Year")
    col.caption(f"⏱️ **Ear/Day:** ₹ {format_inr(per_day)}")

metric_box(c2, "Booking (Ear)", b_ear_curr, b_ear_prev, total_days)
metric_box(c3, "PRS_ORG (Ear)", p_ear_curr, p_ear_prev, total_days)
metric_box(c4, "Goods Freight", g_ear_curr, g_ear_prev, total_days)
metric_box(c5, "Parcel Freight", pr_ear_curr, pr_ear_prev, total_days)

st.markdown("---")

# ----------------- DETAILED TABLES -----------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Booking", "PRS Org", "Combined Passenger", "Goods", "Parcel", "Reservation"
])

def fetch_table_filtered(table_name):
    frames = []
    with engine.connect() as conn:
        for sess, m_list in query_filters_curr:
            if not m_list: continue
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
            
    if not frames: return pd.DataFrame()
        
    full_df = pd.concat(frames, ignore_index=True)
    drop_cols = ['STATION_CODE', 'SESSION', 'station_code', 'session']
    full_df = full_df.drop(columns=[c for c in drop_cols if c in full_df.columns])
    
    if 'MONTH' in full_df.columns:
        full_df['MONTH_CAT'] = pd.Categorical(full_df['MONTH'], categories=MONTH_ORDER, ordered=True)
        full_df = full_df.sort_values(['FMT_SESSION', 'MONTH_CAT']).drop(columns=['MONTH_CAT'])
        
    return full_df

def render_table_with_totals(df, title):
    if df.empty:
        st.info(f"No records for {title} in selected period.")
        return
        
    num_cols = df.select_dtypes(include=['number']).columns
    total_row = {c: df[c].sum() for c in num_cols}
    
    if 'MONTH' in df.columns: total_row['MONTH'] = 'TOTAL'
    if 'FMT_SESSION' in df.columns: total_row['FMT_SESSION'] = 'ALL'
    
    df_totals = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
    
    # Format all numeric columns to Indian style numbers
    for c in num_cols:
        df_totals[c] = df_totals[c].apply(lambda x: format_inr(x) if pd.notnull(x) else x)

    st.dataframe(df_totals, use_container_width=True, hide_index=True)

with tab1:
    render_table_with_totals(fetch_table_filtered('booking'), "Booking")

with tab2:
    render_table_with_totals(fetch_table_filtered('reservation_org'), "PRS Org")

with tab3:
    df_b = fetch_table_filtered('booking')
    df_p = fetch_table_filtered('reservation_org')
    
    if not df_b.empty or not df_p.empty:
        if not df_b.empty: df_b.columns = [c.upper() for c in df_b.columns]
        if not df_p.empty: df_p.columns = [c.upper() for c in df_p.columns]
        
        m_df = pd.merge(df_b, df_p, on=['FMT_SESSION', 'MONTH'], how='outer', suffixes=('_BOOKING', '_PRS'))
        combined = pd.DataFrame()
        combined['Session'] = m_df['FMT_SESSION']
        combined['Month'] = m_df['MONTH']
        
        pass_b = m_df.get('PASSENGERS_BOOKING', m_df.get('PASSENGER_BOOKING', 0)).fillna(0)
        pass_p = m_df.get('PASSENGERS_PRS', m_df.get('PASSENGER_PRS', 0)).fillna(0)
        
        combined['Total Passengers'] = pass_b + pass_p
        combined['Booking Earning'] = m_df.get('EARNING', 0).fillna(0)
        combined['PRS Earning'] = m_df.get('EARNINGS', 0).fillna(0)
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
