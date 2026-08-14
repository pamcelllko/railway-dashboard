import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Page Configuration
st.set_page_config(
    page_title="Railway Earning Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- SECURE LOGIN SYSTEM -----------------
def check_authentication():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.markdown("## 🔒 Railway Dashboard Login")
        st.info("Direct access is restricted. Please enter your credentials below.")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.button("Login")

            if login_btn:
                valid_user = st.secrets.get("APP_USER", "StationEarning")
                valid_pass = st.secrets.get("APP_PASSWORD", "pamcell2234723")
                
                if username == valid_user and password == valid_pass:
                    st.session_state["authenticated"] = True
                    st.success("Login Successful!")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password!")
        return False
    return True

if not check_authentication():
    st.stop()

# ----------------- STYLING & UTILS -----------------
st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
        div[data-testid="stMetricValue"] { font-size: 1.2rem !important; }
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

# Helper function for Indian Currency/Number Format
def format_inr(number):
    try:
        if pd.isna(number) or number is None: return "0"
        val = float(number)
        s, *d = str(f"{val:.0f}").partition(".")
        r = ",".join([s[x-2:x] for x in range(3, len(s)+1, 2)][::-1] + [s[-3:]])
        return "".join([r] + d) if len(s) > 3 else s
    except Exception:
        return f"{number}"

# SECURE SUPABASE CONNECTION
@st.cache_resource
def get_database_connection():
    db_url = st.secrets["SUPABASE_URL"]
    return create_engine(db_url, pool_pre_ping=True)

engine = get_database_connection()

# Constants
MONTH_DAYS = {'Apr': 30, 'May': 31, 'Jun': 30, 'Jul': 31, 'Aug': 31, 'Sep': 30, 'Oct': 31, 'Nov': 30, 'Dec': 31, 'Jan': 31, 'Feb': 28, 'Mar': 31}
MONTH_ORDER = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
QUARTERS = {
    'Q1 (Apr-Jun)': ['Apr', 'May', 'Jun'],
    'Q2 (Jul-Sep)': ['Jul', 'Aug', 'Sep'],
    'Q3 (Oct-Dec)': ['Oct', 'Nov', 'Dec'],
    'Q4 (Jan-Mar)': ['Jan', 'Feb', 'Mar']
}

# Sidebar Header
st.sidebar.markdown("### 👤 Logged in: **StationEarning**")
if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.rerun()

st.title("🚄 Station Earning & Traffic Executive Dashboard")

# ----------------- SIDEBAR FILTERS -----------------
st.sidebar.header("🔍 Filter Options")

# Station Selection with Reliable Fallback List
stns = ['SHG', 'LKO', 'BBK', 'FD', 'AMH', 'AY', 'JNU', 'SLN']
try:
    with engine.connect() as conn:
        db_stns = pd.read_sql(text('SELECT DISTINCT "STATION_CODE" FROM booking'), conn)['STATION_CODE'].dropna().unique().tolist()
        if db_stns:
            stns = sorted(list(set(stns + db_stns)))
except Exception:
    pass

selected_station = st.sidebar.selectbox("Select Station", stns)

# Session Mapping
session_options = ["2026-27", "2025-26", "2024-25"]
selected_fmt_session = st.sidebar.selectbox("Select Session", session_options)

curr_yr = int(selected_fmt_session.split('-')[0])
curr_session_raw = f"{curr_yr}{str(curr_yr+1)[2:]}" # e.g. 202627
prev_session_raw = f"{curr_yr-1}{str(curr_yr)[2:]}" # e.g. 202526 for Jan-Mar

# Time Filters
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
    end_m = st.sidebar.selectbox("Ending Month", MONTH_ORDER, index=3) # Jul
    idx = MONTH_ORDER.index(end_m)
    selected_months = MONTH_ORDER[max(0, idx-2):idx+1]
elif filter_type == "Last 6 Months":
    end_m = st.sidebar.selectbox("Ending Month", MONTH_ORDER, index=3) # Jul
    idx = MONTH_ORDER.index(end_m)
    if idx >= 5:
        selected_months = MONTH_ORDER[idx-5:idx+1]
    else:
        selected_months = MONTH_ORDER[idx-5:] + MONTH_ORDER[:idx+1]
else:
    selected_months = st.sidebar.multiselect("Select Months", MONTH_ORDER, default=['Apr', 'May', 'Jun', 'Jul'])

total_days = sum([MONTH_DAYS.get(m, 30) for m in selected_months])

# ----------------- FAIL-SAFE DATA FETCHING -----------------
def fetch_exact_data(table_name, station, target_sess, prev_sess, months):
    if not months: return pd.DataFrame()
    
    # Simple & Fast Base Query
    q = f'SELECT * FROM {table_name} WHERE "STATION_CODE" = \'{station}\''
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(q), conn)
            if df.empty: return pd.DataFrame()
            
            # 1. Column Uniformity
            df.columns = [c.upper().strip() for c in df.columns]
            
            # 2. Robust Session Filtering
            if 'SESSION' in df.columns:
                df['SESS_STR'] = df['SESSION'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                
                # Check for Jan-Mar cross session filter
                jan_mar = [m for m in months if m in ['Jan', 'Feb', 'Mar']]
                apr_dec = [m for m in months if m not in ['Jan', 'Feb', 'Mar']]
                
                conds = []
                if apr_dec:
                    conds.append((df['SESS_STR'] == str(target_sess)) & (df['MONTH'].str.strip().str.title().isin(apr_dec)))
                if jan_mar:
                    conds.append((df['SESS_STR'] == str(target_sess)) & (df['MONTH'].str.strip().str.title().isin(jan_mar)))
                
                if conds:
                    final_cond = conds[0]
                    for c in conds[1:]:
                        final_cond = final_cond | c
                    df = df[final_cond]
                else:
                    df = df[df['SESS_STR'] == str(target_sess)]
            
            # 3. Month Clean Up
            if 'MONTH' in df.columns and not df.empty:
                df['MONTH'] = df['MONTH'].astype(str).str.strip().str.title()
                df = df[df['MONTH'].isin(months)]
                
            # 4. Numeric Formatting
            num_cols = ['PASSENGER', 'PASSENGERS', 'EARNING', 'EARNINGS', 'OW_FRIEGHT', 'NET_CASH']
            for col in num_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            return df.drop_duplicates()
    except Exception:
        return pd.DataFrame()

# Fetch Cleaned Data
df_booking = fetch_exact_data('booking', selected_station, curr_session_raw, prev_session_raw, selected_months)
df_prs_org = fetch_exact_data('reservation_org', selected_station, curr_session_raw, prev_session_raw, selected_months)
df_goods = fetch_exact_data('goods', selected_station, curr_session_raw, prev_session_raw, selected_months)
df_parcel = fetch_exact_data('parcel', selected_station, curr_session_raw, prev_session_raw, selected_months)

pass_col_b = 'PASSENGER' if 'PASSENGER' in df_booking.columns else ('PASSENGERS' if 'PASSENGERS' in df_booking.columns else None)
pass_col_p = 'PASSENGER' if 'PASSENGER' in df_prs_org.columns else ('PASSENGERS' if 'PASSENGERS' in df_prs_org.columns else None)

b_ear_curr = df_booking['EARNING'].sum() if 'EARNING' in df_booking.columns and not df_booking.empty else 0.0
b_pass_curr = df_booking[pass_col_b].sum() if pass_col_b and not df_booking.empty else 0.0

p_ear_curr = df_prs_org['EARNINGS'].sum() if 'EARNINGS' in df_prs_org.columns and not df_prs_org.empty else 0.0
p_pass_curr = df_prs_org[pass_col_p].sum() if pass_col_p and not df_prs_org.empty else 0.0

g_ear_curr = df_goods['OW_FRIEGHT'].sum() if 'OW_FRIEGHT' in df_goods.columns and not df_goods.empty else 0.0
pr_ear_curr = df_parcel['OW_FRIEGHT'].sum() if 'OW_FRIEGHT' in df_parcel.columns and not df_parcel.empty else 0.0

comb_pass_curr = b_pass_curr + p_pass_curr
comb_ear_curr = b_ear_curr + p_ear_curr

# ----------------- DISPLAY METRICS -----------------
st.markdown(f"### 📍 Station: **{selected_station}** | Session: **{selected_fmt_session}** | Months: **{', '.join(selected_months)}**")

c1, c2, c3, c4, c5 = st.columns([1.2, 1, 1, 1, 1])

with c1:
    pass_per_day = comb_pass_curr / total_days if total_days > 0 else 0
    ear_per_day = comb_ear_curr / total_days if total_days > 0 else 0
    
    st.markdown(f"""
        <div class="combined-card">
            <div style="font-size: 0.85rem; font-weight: bold; color: #333;">👥 Combined Passenger (PRS+Booking)</div>
            <div style="font-size: 0.8rem; margin-top:2px;"><b>Pass:</b> {format_inr(comb_pass_curr)} | <b>Earning:</b> ₹ {format_inr(comb_ear_curr)}</div>
            <div style="font-size: 0.75rem; color: #555; margin-top:2px;"><b>Pass/Day:</b> {format_inr(pass_per_day)} | <b>Ear/Day:</b> ₹ {format_inr(ear_per_day)}</div>
        </div>
    """, unsafe_allow_html=True)

def metric_box(col, title, curr, days):
    per_day = curr / days if days > 0 else 0
    col.metric(label=title, value=f"₹ {format_inr(curr)}")
    col.caption(f"⏱️ **Ear/Day:** ₹ {format_inr(per_day)}")

metric_box(c2, "Booking (Ear)", b_ear_curr, total_days)
metric_box(c3, "PRS_ORG (Ear)", p_ear_curr, total_days)
metric_box(c4, "Goods Freight", g_ear_curr, total_days)
metric_box(c5, "Parcel Freight", pr_ear_curr, total_days)

st.markdown("---")

# ----------------- DETAILED TABLES -----------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Booking", "PRS Org", "Combined Passenger", "Goods", "Parcel", "Reservation"
])

def render_table_clean(df, title):
    if df.empty:
        st.info(f"No records found for {title} in Session {selected_fmt_session}.")
        return
        
    drop_cols = ['STATION_CODE', 'SESSION', 'SESS_STR']
    clean_df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors='ignore')
    
    if 'MONTH' in clean_df.columns:
        clean_df['MONTH_CAT'] = pd.Categorical(clean_df['MONTH'], categories=MONTH_ORDER, ordered=True)
        clean_df = clean_df.sort_values('MONTH_CAT').drop(columns=['MONTH_CAT'])
        
    num_cols = clean_df.select_dtypes(include=['number']).columns
    total_row = {c: clean_df[c].sum() for c in num_cols}
    if 'MONTH' in clean_df.columns: total_row['MONTH'] = 'TOTAL'
    
    df_totals = pd.concat([clean_df, pd.DataFrame([total_row])], ignore_index=True)
    
    for c in num_cols:
        df_totals[c] = df_totals[c].apply(lambda x: format_inr(x) if pd.notnull(x) else x)

    st.dataframe(df_totals, use_container_width=True, hide_index=True)

with tab1: render_table_clean(df_booking, "Booking")
with tab2: render_table_clean(df_prs_org, "PRS Org")

with tab3:
    if not df_booking.empty or not df_prs_org.empty:
        merged = pd.merge(df_booking, df_prs_org, on='MONTH', how='outer', suffixes=('_Booking', '_PRS'))
        comb = pd.DataFrame()
        comb['Month'] = merged['MONTH']
        
        b_p_col = f"{pass_col_b}_Booking" if f"{pass_col_b}_Booking" in merged.columns else pass_col_b
        p_p_col = f"{pass_col_p}_PRS" if f"{pass_col_p}_PRS" in merged.columns else pass_col_p
        
        comb['Booking Passengers'] = merged.get(b_p_col, 0).fillna(0)
        comb['PRS Passengers'] = merged.get(p_p_col, 0).fillna(0)
        comb['Total Passengers'] = comb['Booking Passengers'] + comb['PRS Passengers']
        comb['Booking Earning'] = merged.get('EARNING', 0).fillna(0)
        comb['PRS Earning'] = merged.get('EARNINGS', 0).fillna(0)
        comb['Total Earning'] = comb['Booking Earning'] + comb['PRS Earning']
        
        render_table_clean(comb, "Combined Passenger")
    else:
        st.info("No data available.")

with tab4: render_table_clean(df_goods, "Goods")
with tab5: render_table_clean(df_parcel, "Parcel")
with tab6:
    df_res = fetch_exact_data('reservation', selected_station, curr_session_raw, prev_session_raw, selected_months)
    if 'NET_CASH' in df_res.columns:
        df_res = df_res.rename(columns={'NET_CASH': 'EARNING (NET_CASH)'})
    render_table_clean(df_res, "Reservation")
