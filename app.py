import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import sqlite3
import bcrypt

# ----------------- PAGE CONFIGURATION -----------------
st.set_page_config(
    page_title="Railway Earning & Traffic Executive Dashboard", 
    page_icon="🚄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- LOCAL USER AUTH DATABASE (SQLITE) -----------------
def init_auth_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_auth_db()

def create_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def verify_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username = ?', (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return bcrypt.checkpw(password.encode('utf-8'), row[0].encode('utf-8'))
    return False

# ----------------- CUSTOM PROFESSIONAL CSS -----------------
st.markdown("""
    <style>
        /* Main Layout & Density Optimizations for Zero Scroll */
        .block-container { 
            padding-top: 1rem !important; 
            padding-bottom: 0.5rem !important;
            max-width: 98% !important;
        }
        
        /* Typography */
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        /* Metric Card Container Styling */
        .metric-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 12px 8px;
            text-align: center !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            transition: all 0.2s ease-in-out;
            height: 100%;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
            border-color: #cbd5e1;
        }
        
        .metric-title {
            font-size: 0.82rem;
            font-weight: 700;
            color: #334155;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
            text-align: center;
        }
        .metric-value {
            font-size: 1.25rem;
            font-weight: 800;
            color: #0f172a;
            margin: 2px 0;
            text-align: center;
        }
        .metric-sub {
            font-size: 0.75rem;
            color: #64748b;
            font-weight: 500;
            text-align: center;
        }
        .metric-delta-pos {
            font-size: 0.75rem;
            font-weight: 700;
            color: #16a34a;
            background-color: #dcfce7;
            padding: 2px 6px;
            border-radius: 12px;
            display: inline-block;
            margin-top: 4px;
        }
        .metric-delta-neg {
            font-size: 0.75rem;
            font-weight: 700;
            color: #dc2626;
            background-color: #fee2e2;
            padding: 2px 6px;
            border-radius: 12px;
            display: inline-block;
            margin-top: 4px;
        }

        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-bottom: 2px solid #e2e8f0;
        }
        .stTabs [data-baseweb="tab"] {
            height: 38px;
            padding: 0 16px;
            font-weight: 600;
            border-radius: 6px 6px 0 0;
            color: #64748b;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1e293b !important;
            color: #ffffff !important;
        }

        /* Center Align Table Content & Headers */
        div[data-testid="stDataFrame"] table {
            text-align: center !important;
            width: 100% !important;
        }
        div[data-testid="stDataFrame"] th {
            text-align: center !important;
            background-color: #f1f5f9 !important;
            color: #1e293b !important;
            font-weight: 700 !important;
            font-size: 0.8rem !important;
            padding: 6px !important;
        }
        div[data-testid="stDataFrame"] td {
            text-align: center !important;
            font-size: 0.8rem !important;
            padding: 4px 6px !important;
        }
        
        /* Compact Header Banner */
        .header-banner {
            background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
            color: white;
            padding: 10px 18px;
            border-radius: 10px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
    </style>
""", unsafe_allow_html=True)

# ----------------- HELPER FUNCTIONS -----------------
def format_inr(number):
    try:
        if pd.isna(number) or number is None: 
            return "0"
        val = round(float(number))
        is_negative = val < 0
        s = str(abs(val))
        if len(s) <= 3:
            res = s
        else:
            res = s[-3:]
            s = s[:-3]
            while len(s) > 0:
                res = s[-2:] + "," + res
                s = s[:-2]
        return f"-{res}" if is_negative else res
    except Exception:
        return str(number)

def format_session(raw_s):
    s = str(raw_s).split('.')[0].strip()
    if len(s) == 6:
        return f"{s[:4]}-{s[4:]}"
    return s

def parse_session(fmt_s):
    return str(fmt_s).replace('-', '').strip()

# ----------------- SECURE DATABASE CREDENTIALS -----------------
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "postgresql://postgres.ggrpypensvabbvpyzqbx:2234723pamcell@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres").strip()

# ----------------- AUTHENTICATION PAGE (LOGIN / SIGNUP) -----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.authenticated:
    st.markdown("<h2 style='text-align: center; color: #0f172a;'>🚄 Railway Earning Dashboard Access</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        auth_mode = st.radio("Choose Option", ["Login", "Sign Up / Create Account"], horizontal=True, label_visibility="collapsed")
        
        if auth_mode == "Login":
            st.subheader("🔑 User Login")
            with st.form("login_form"):
                user_input = st.text_input("Username").strip()
                pass_input = st.text_input("Password", type="password").strip()
                submit_login = st.form_submit_button("Login to Dashboard", use_container_width=True)

                if submit_login:
                    if verify_user(user_input, pass_input):
                        st.session_state.authenticated = True
                        st.session_state.username = user_input
                        st.success("Login Successful!")
                        st.rerun()
                    else:
                        st.error("Invalid Username or Password")

        else:
            st.subheader("📝 Create New Account")
            with st.form("signup_form"):
                new_user = st.text_input("Choose Username").strip()
                new_pass = st.text_input("Choose Password", type="password").strip()
                confirm_pass = st.text_input("Confirm Password", type="password").strip()
                submit_signup = st.form_submit_button("Register Account", use_container_width=True)

                if submit_signup:
                    if not new_user or not new_pass:
                        st.warning("Username and Password cannot be empty.")
                    elif new_pass != confirm_pass:
                        st.error("Passwords do not match!")
                    else:
                        if create_user(new_user, new_pass):
                            st.success("Account created successfully! Please switch to Login.")
                        else:
                            st.error("Username already exists. Choose a different one.")
    st.stop()

# ----------------- DATABASE CONNECTION -----------------
@st.cache_resource
def get_database_connection():
    return create_engine(SUPABASE_URL, pool_pre_ping=True)

engine = get_database_connection()

# ----------------- DYNAMIC COLUMN FINDERS -----------------
def get_station_col(conn, table_name='booking'):
    try:
        cols = pd.read_sql(text(f'SELECT * FROM {table_name} LIMIT 1'), conn).columns
        for c in cols:
            if c.upper() in ['STATION_COD', 'STATION_CODE', 'STN_CODE']:
                return c
    except Exception: 
        pass
    return 'STATION_COD'

def get_pass_col(table_name):
    try:
        with engine.connect() as conn:
            cols = pd.read_sql(text(f'SELECT * FROM {table_name} LIMIT 1'), conn).columns
            cols = [c.upper() for c in cols]
            if 'PASSENGERS' in cols: return 'PASSENGERS'
            if 'PASSENGER' in cols: return 'PASSENGER'
    except Exception: 
        pass
    return 'PASSENGER'

def get_freight_col(table_name):
    try:
        with engine.connect() as conn:
            cols = pd.read_sql(text(f'SELECT * FROM {table_name} LIMIT 1'), conn).columns
            cols = [c.upper() for c in cols]
            if 'OW_FRIEGHT' in cols: return 'OW_FRIEGHT'
            if 'OW_FREIGHT' in cols: return 'OW_FREIGHT'
    except Exception:
        pass
    return 'OW_FRIEGHT'

# ----------------- CONSTANTS & MAPPINGS -----------------
MONTH_DAYS = {'Apr': 30, 'May': 31, 'Jun': 30, 'Jul': 31, 'Aug': 31, 'Sep': 30, 'Oct': 31, 'Nov': 30, 'Dec': 31, 'Jan': 31, 'Feb': 28, 'Mar': 31}
MONTH_ORDER = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
QUARTERS = {
    'Q1 (Apr-Jun)': ['Apr', 'May', 'Jun'],
    'Q2 (Jul-Sep)': ['Jul', 'Aug', 'Sep'],
    'Q3 (Oct-Dec)': ['Oct', 'Nov', 'Dec'],
    'Q4 (Jan-Mar)': ['Jan', 'Feb', 'Mar']
}

# ----------------- SIDEBAR FILTERS -----------------
st.sidebar.markdown(f"👤 **User:** `{st.session_state.username}`")
if st.sidebar.button("🔒 Logout", use_container_width=True):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("🔍 Dashboard Filters")

# Fetch Stations
try:
    with engine.connect() as conn:
        stn_col = get_station_col(conn, 'booking')
        stns = sorted(pd.read_sql(text(f'SELECT DISTINCT "{stn_col}" FROM booking'), conn)[stn_col].dropna().unique().tolist())
    selected_station = st.sidebar.selectbox("Select Station", stns)
except Exception as e:
    st.error(f"Error loading stations: {e}")
    st.stop()

# Fetch Sessions
try:
    with engine.connect() as conn:
        raw_sess = [str(s).split('.')[0].strip() for s in pd.read_sql(text('SELECT DISTINCT "SESSION" FROM booking ORDER BY "SESSION" DESC'), conn)['SESSION'].dropna().tolist()]
        fmt_sess = [format_session(s) for s in raw_sess if len(s) == 6]
    selected_fmt_session = st.sidebar.selectbox("Select Session", fmt_sess)
    selected_raw_session = parse_session(selected_fmt_session)
except Exception as e:
    st.error(f"Error loading sessions: {e}")
    st.stop()

# Previous Session Logic
start_yr = int(selected_raw_session[:4])
end_yr = int(selected_raw_session[4:])
prev_raw_session = f"{start_yr - 1:04d}{end_yr - 1:02d}"

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
        prev_prev_raw_session = f"{start_yr - 2:04d}{end_yr - 2:02d}"
        query_filters_prev = [(prev_prev_raw_session, prev_m_list), (prev_raw_session, curr_m_list)]

    display_period_text = f"{filter_type} (Ending {end_m})"

total_days = sum([sum([MONTH_DAYS.get(m, 30) for m in m_list]) for _, m_list in query_filters_curr])

# ----------------- DATA FETCHING -----------------
def fetch_total(table_name, filters_list, col_name):
    total = 0.0
    for sess, m_list in filters_list:
        if not m_list: 
            continue
        m_str = "','".join([m.upper() for m in m_list])
        
        with engine.connect() as conn:
            stn_c = get_station_col(conn, table_name)
            q = f'''
                SELECT SUM("{col_name}") as val FROM {table_name}
                WHERE UPPER(TRIM(CAST("{stn_c}" AS TEXT))) = UPPER('{selected_station.strip()}') 
                  AND CAST("SESSION" AS TEXT) = '{sess}'
                  AND UPPER(TRIM("MONTH")) IN ('{m_str}')
            '''
            try:
                val = pd.read_sql(text(q), conn)['val'].iloc[0]
                if pd.notnull(val): 
                    total += float(val)
            except Exception:
                conn.rollback()
    return total

pass_col_booking = get_pass_col('booking')
pass_col_prs = get_pass_col('reservation_org')
goods_freight_col = get_freight_col('goods')
parcel_freight_col = get_freight_col('parcel')

# Fetch Earnings & Passengers
b_ear_curr = fetch_total('booking', query_filters_curr, 'EARNING')
b_ear_prev = fetch_total('booking', query_filters_prev, 'EARNING')
b_pass_curr = fetch_total('booking', query_filters_curr, pass_col_booking)

p_ear_curr = fetch_total('reservation_org', query_filters_curr, 'EARNINGS')
p_ear_prev = fetch_total('reservation_org', query_filters_prev, 'EARNINGS')
p_pass_curr = fetch_total('reservation_org', query_filters_curr, pass_col_prs)

g_ear_curr = fetch_total('goods', query_filters_curr, goods_freight_col)
g_ear_prev = fetch_total('goods', query_filters_prev, goods_freight_col)

pr_ear_curr = fetch_total('parcel', query_filters_curr, parcel_freight_col)
pr_ear_prev = fetch_total('parcel', query_filters_prev, parcel_freight_col)

# Combined Calculations
comb_pass_curr = b_pass_curr + p_pass_curr
comb_ear_curr = b_ear_curr + p_ear_curr
comb_ear_prev = b_ear_prev + p_ear_prev

# ----------------- DASHBOARD HEADER BANNER -----------------
st.markdown(f"""
    <div class="header-banner">
        <div>
            <h3 style="margin:0; font-weight:800; font-size:1.2rem;">🚄 STATION EARNING & TRAFFIC EXECUTIVE DASHBOARD</h3>
            <span style="font-size:0.8rem; opacity:0.85;">Station: <b>{selected_station}</b> | Session: <b>{selected_fmt_session}</b> | {display_period_text}</span>
        </div>
        <div style="text-align:right; font-size:0.8rem; opacity:0.9;">
            🗓️ <b>{total_days} Days Selected</b>
        </div>
    </div>
""", unsafe_allow_html=True)

# ----------------- CENTERED TOP METRIC CARDS -----------------
c1, c2, c3, c4, c5 = st.columns(5)

def render_centered_metric(col, title, curr, prev, days, is_combined=False, pass_val=0):
    per_day = curr / days if days > 0 else 0
    growth = ((curr - prev) / prev * 100) if prev > 0 else 0
    delta_class = "metric-delta-pos" if growth >= 0 else "metric-delta-neg"
    
    if is_combined:
        pass_per_day = pass_val / days if days > 0 else 0
        content = f"""
            <div class="metric-card" style="border-left: 4px solid #3b82f6;">
                <div class="metric-title">👥 COMBINED PASSENGER</div>
                <div class="metric-value">₹ {format_inr(curr)}</div>
                <div class="metric-sub"><b>Pass:</b> {format_inr(pass_val)} | <b>P/Day:</b> {format_inr(pass_per_day)}</div>
                <div class="metric-sub"><b>Ear/Day:</b> ₹ {format_inr(per_day)}</div>
                <div class="{delta_class}">{growth:+.1f}% vs Prev. Year</div>
            </div>
        """
    else:
        content = f"""
            <div class="metric-card">
                <div class="metric-title">{title}</div>
                <div class="metric-value">₹ {format_inr(curr)}</div>
                <div class="metric-sub"><b>Ear/Day:</b> ₹ {format_inr(per_day)}</div>
                <div class="{delta_class}">{growth:+.1f}% vs Prev. Year</div>
            </div>
        """
    col.markdown(content, unsafe_allow_html=True)

render_centered_metric(c1, "Combined", comb_ear_curr, comb_ear_prev, total_days, is_combined=True, pass_val=comb_pass_curr)
render_centered_metric(c2, "BOOKING EARNING", b_ear_curr, b_ear_prev, total_days)
render_centered_metric(c3, "PRS ORG EARNING", p_ear_curr, p_ear_prev, total_days)
render_centered_metric(c4, "GOODS FREIGHT", g_ear_curr, g_ear_prev, total_days)
render_centered_metric(c5, "PARCEL FREIGHT", pr_ear_curr, pr_ear_prev, total_days)

st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

# ----------------- COMPACT DETAILED TABLES -----------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Booking", "PRS Org", "Combined Passenger", "Goods", "Parcel", "Reservation"
])

def fetch_table_filtered(table_name):
    frames = []
    for sess, m_list in query_filters_curr:
        if not m_list: 
            continue
        m_str = "','".join([m.upper() for m in m_list])
        
        with engine.connect() as conn:
            stn_c = get_station_col(conn, table_name)
            q = f'''
                SELECT * FROM {table_name} 
                WHERE UPPER(TRIM(CAST("{stn_c}" AS TEXT))) = UPPER('{selected_station.strip()}') 
                  AND CAST("SESSION" AS TEXT) = '{sess}'
                  AND UPPER(TRIM("MONTH")) IN ('{m_str}')
            '''
            try:
                df = pd.read_sql(text(q), conn)
                if not df.empty:
                    df['FMT_SESSION'] = format_session(sess)
                    frames.append(df)
            except Exception:
                conn.rollback()
            
    if not frames: 
        return pd.DataFrame()
        
    full_df = pd.concat(frames, ignore_index=True)
    drop_cols = ['STATION_CODE', 'STATION_COD', 'SESSION', 'station_code', 'station_cod', 'session']
    full_df = full_df.drop(columns=[c for c in drop_cols if c in full_df.columns])
    
    if 'MONTH' in full_df.columns:
        full_df['MONTH_CAT'] = pd.Categorical(full_df['MONTH'], categories=MONTH_ORDER, ordered=True)
        full_df = full_df.sort_values(['FMT_SESSION', 'MONTH_CAT']).drop(columns=['MONTH_CAT'])
        
    return full_df

def render_table_with_totals(df, title):
    if df.empty:
        st.info(f"No records available for {title} in selected period.")
        return
        
    num_cols = df.select_dtypes(include=['number']).columns
    total_row = {c: df[c].sum() for c in num_cols}
    
    if 'MONTH' in df.columns: total_row['MONTH'] = 'TOTAL'
    if 'FMT_SESSION' in df.columns: total_row['FMT_SESSION'] = 'ALL'
    
    df_totals = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
    
    for c in num_cols:
        df_totals[c] = df_totals[c].apply(lambda x: format_inr(x) if pd.notnull(x) else x)

    # Render table optimized for no vertical/horizontal scrolling
    st.dataframe(
        df_totals, 
        use_container_width=True, 
        hide_index=True,
        height=min(420, (len(df_totals) + 1) * 35) # Dynamic height fitting screen perfectly
    )

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
