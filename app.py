import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import bcrypt
import base64
import os
from datetime import datetime

# ----------------- PAGE CONFIGURATION -----------------
st.set_page_config(
    page_title="Railway Earning Executive Dashboard", 
    page_icon="🚄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- SECURE DATABASE CREDENTIALS -----------------
DEFAULT_DB_URL = "postgresql+psycopg2://postgres.ggrpypensvabbvpyzqbx:2234723pamcell@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
SUPABASE_URL = st.secrets.get("SUPABASE_URL", DEFAULT_DB_URL).strip()

ADMIN_NAME = "Mohammed Rafik"
ADMIN_EMAIL = "adilrafeeque@gmail.com"

@st.cache_resource
def get_database_connection():
    return create_engine(
        SUPABASE_URL, 
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=300,
        isolation_level="AUTOCOMMIT"
    )

engine = get_database_connection()

# ----------------- DATABASE KEEP-ALIVE HEALTH CHECK -----------------
def keep_db_alive():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
    except Exception:
        pass

keep_db_alive()

# ----------------- IMAGE & TRAIN LOGO ENCODING -----------------
def get_train_logo_html():
    img_path = "transport.png"
    if os.path.exists(img_path):
        try:
            with open(img_path, "rb") as image_file:
                encoded = base64.b64encode(image_file.read()).decode()
            return f'<img src="data:image/png;base64,{encoded}" style="width:38px; height:38px; vertical-align:middle; margin-right:8px;">'
        except Exception: pass
    
    return """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="36" height="36" style="vertical-align: middle; fill: #0B49B5; margin-right:8px;">
      <path d="M480 384c0 13.255-10.745 24-24 24H56c-13.255 0-24-10.745-24-24s10.745-24 24-24h400c13.255 0 24 10.745 24 24zM88 320l-48 96h432l-48-96H88zm320-192c0-35.346-28.654-64-64-64H168c-35.346 0-64 28.654-64 64v160h304V128zm-224 0h144v48H184v-48z"/>
    </svg>
    """

# ----------------- SUPABASE AUTH DB -----------------
def init_supabase_auth_db():
    try:
        with engine.connect() as conn:
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS user_auth (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'APPROVED'
                );
            '''))
    except Exception: pass

init_supabase_auth_db()

def create_or_update_user(username, password, auto_approve=True):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    status = 'APPROVED' if auto_approve else 'PENDING'
    try:
        with engine.connect() as conn:
            conn.execute(text('''
                INSERT INTO user_auth (username, password, status)
                VALUES (:u, :p, :s)
                ON CONFLICT (username) 
                DO UPDATE SET password = :p, status = :s;
            '''), {'u': username, 'p': hashed, 's': status})
        return True, status
    except Exception as e:
        return False, str(e)

def verify_user(username, password):
    if username in ["computercell", "StationEarning"] and password == "pamcell2234723":
        return True, "APPROVED", "Master Admin User"
        
    try:
        with engine.connect() as conn:
            res = conn.execute(text('SELECT password, status FROM user_auth WHERE username = :u'), {'u': username}).fetchone()
            if res:
                stored_hash, status = res[0], res[1]
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                    return True, status, "DB User"
                else:
                    return False, "INVALID_PASSWORD", "Password does not match"
            else:
                return False, "USER_NOT_FOUND", "Username does not exist"
    except Exception as e:
        return False, "ERROR", str(e)

# ----------------- GLOBAL STYLES & DASHBOARD STYLING -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Roboto:wght@300;400;500;700;900&display=swap');
    
    :root {
        --primary: #0B49B5;
        --secondary: #17366F;
        --background: #F4F8FD;
        --cardBackground: #FFFFFF;
        --textColor: #10234B;
        --mutedText: #526987;
        --borderColor: #DCE4EF;
        --borderRadius: 16px;
    }

    .block-container { 
        padding-top: 1.8rem !important;
        padding-bottom: 1rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }
    
    html, body, [class*="css"] {
        font-family: 'Inter', 'Roboto', sans-serif !important;
    }

    div[data-testid="stTextInput"] label {
        font-weight: 600 !important;
        color: #10234B !important;
        font-size: 0.9rem !important;
    }

    div[data-testid="stTextInput"] input {
        border-radius: 10px !important;
        border: 1px solid #DCE4EF !important;
        padding: 10px 14px !important;
        font-size: 0.92rem !important;
    }

    div[data-testid="stForm"] button {
        background-color: #0B49B5 !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        border-radius: 10px !important;
        padding: 10px 0 !important;
        border: none !important;
        width: 100% !important;
        box-shadow: 0 4px 12px rgba(11, 73, 181, 0.22) !important;
    }

    div[data-testid="stForm"] button:hover {
        background-color: #17366F !important;
    }

    /* DASHBOARD HEADERS & METRIC CARDS */
    .main-title {
        font-size: 1.45rem !important;
        font-weight: 900 !important;
        color: var(--textColor) !important;
        display: flex;
        align-items: center;
    }
    .station-subtitle {
        font-size: 0.9rem !important;
        color: var(--mutedText) !important;
        font-weight: 500 !important;
        margin-top: 4px !important;
    }
    .station-meta-info {
        font-size: 0.85rem !important;
        color: var(--primary) !important;
        font-weight: 700 !important;
        margin-top: 6px !important;
        background-color: #eff6ff;
        padding: 5px 12px;
        border-radius: 6px;
        border: 1px solid #bfdbfe;
        display: inline-block;
    }
    .highlight-badge {
        background-color: var(--secondary);
        color: #ffffff !important;
        padding: 2px 8px;
        border-radius: 5px;
        font-weight: 700;
    }
    .days-badge {
        font-size: 0.85rem;
        font-weight: 700;
        background-color: var(--cardBackground);
        color: var(--textColor);
        padding: 7px 16px;
        border-radius: 8px;
        border: 1px solid var(--borderColor);
        display: inline-block;
    }

    .metric-card {
        background: var(--cardBackground);
        border: 1px solid var(--borderColor);
        border-radius: 10px;
        padding: 12px 8px;
        text-align: center !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        min-height: 142px !important;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        align-items: center;
    }
    .metric-title {
        font-size: 0.75rem;
        font-weight: 700;
        color: var(--mutedText);
        text-transform: uppercase;
    }
    .metric-value {
        font-size: 1.22rem;
        font-weight: 900;
        color: var(--textColor);
        margin: 2px 0;
    }
    .metric-sub {
        font-size: 0.72rem;
        color: var(--mutedText);
        font-weight: 500;
    }
    .metric-delta-pos {
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        color: #15803d !important;
        background-color: #dcfce7 !important;
        padding: 2px 10px !important;
        border-radius: 20px !important;
    }
    .metric-delta-neg {
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        color: #b91c1c !important;
        background-color: #fee2e2 !important;
        padding: 2px 10px !important;
        border-radius: 20px !important;
    }

    /* CUSTOM HTML TABLE */
    .custom-dashboard-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
        margin-top: 8px;
        background-color: var(--cardBackground);
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid var(--borderColor);
    }
    .custom-dashboard-table th {
        background-color: #f1f5f9 !important;
        color: #475569 !important;
        font-weight: 700 !important;
        text-align: center !important;
        padding: 10px 14px !important;
        border: 1px solid var(--borderColor) !important;
    }
    .custom-dashboard-table td {
        text-align: center !important;
        padding: 9px 12px !important;
        border: 1px solid var(--borderColor) !important;
        color: var(--textColor) !important;
    }
    .custom-dashboard-table tr.total-row td {
        font-weight: 800 !important;
        border-top: 2px solid #cbd5e1 !important;
    }
    .period-info-box {
        background-color: #eff6ff;
        border: 1px solid #bfdbfe;
        color: #1e40af;
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 12px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- LOGIN PAGE -----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.authenticated:
    col_left, col_right = st.columns([1.1, 0.9], gap="large")
    
    with col_left:
        banner_html = """
        <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 50%, #93c5fd 100%); padding: 2.5rem; border-radius: 16px; box-shadow: 0 10px 25px rgba(11, 73, 181, 0.08);">
            <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 12px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="#0B49B5"><path d="M12 2c-4 0-8 .5-8 4v9.5C4 17.43 5.57 19 7.5 19L6 20.5v.5h12v-.5L16.5 19c1.93 0 3.5-1.57 3.5-3.5V6c0-3.5-4-4-8-4zm0 2c3.71 0 5.8 0 6 2H6c.2-2 2.29-2 6-2zm-5 6.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm10 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5-1.5zm-5 6.5c-2.76 0-5-1.12-5-2.5h10c0 1.38-2.24 2.5-5 2.5z"/></svg>
                <div style="font-size: 1.85rem; font-weight: 800; color: #10234B; line-height: 1.2;">Railway Earning<br>Dashboard Access</div>
            </div>
            <div style="font-size: 0.95rem; color: #526987; font-weight: 500; margin-bottom: 2rem;">
                Track your earnings, manage your account and stay connected with the railway ecosystem.
            </div>
            <div style="display: flex; gap: 16px; margin-bottom: 2rem; text-align: center;">
                <div style="flex: 1;">
                    <div style="width: 48px; height: 48px; border-radius: 50%; background: #dbeafe; color: #0B49B5; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px auto; font-size: 1.2rem; font-weight: bold;">📊</div>
                    <div style="font-size: 0.8rem; font-weight: 600; color: #10234B;">View Earnings Reports</div>
                </div>
                <div style="flex: 1;">
                    <div style="width: 48px; height: 48px; border-radius: 50%; background: #dcfce7; color: #16a34a; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px auto; font-size: 1.2rem; font-weight: bold;">🛡️</div>
                    <div style="font-size: 0.8rem; font-weight: 600; color: #10234B;">Secure & Reliable Access</div>
                </div>
                <div style="flex: 1;">
                    <div style="width: 48px; height: 48px; border-radius: 50%; background: #f3e8ff; color: #9333ea; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px auto; font-size: 1.2rem; font-weight: bold;">👤</div>
                    <div style="font-size: 0.8rem; font-weight: 600; color: #10234B;">Manage Your Account</div>
                </div>
            </div>
            <div>
                <img src="https://images.unsplash.com/photo-1532105956626-9569c03602f6?q=80&w=1000&auto=format&fit=crop" style="width: 100%; border-radius: 12px; box-shadow: 0 10px 25px rgba(16, 35, 75, 0.15); max-height: 320px; object-fit: cover;" alt="Train Image">
            </div>
        </div>
        """
        st.markdown(banner_html, unsafe_allow_html=True)

    with col_right:
        auth_mode = st.radio("Access Mode", ["Login", "Sign Up / Reset Password"], horizontal=True, label_visibility="collapsed")
        
        st.markdown("""
        <div style="text-align: center; margin-top: 10px; margin-bottom: 15px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="46" height="46" viewBox="0 0 24 24" fill="#0B49B5"><path d="M12 2c-4 0-8 .5-8 4v9.5C4 17.43 5.57 19 7.5 19L6 20.5v.5h12v-.5L16.5 19c1.93 0 3.5-1.57 3.5-3.5V6c0-3.5-4-4-8-4zm0 2c3.71 0 5.8 0 6 2H6c.2-2 2.29-2 6-2zm-5 6.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm10 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5-1.5zm-5 6.5c-2.76 0-5-1.12-5-2.5h10c0 1.38-2.24 2.5-5 2.5z"/></svg>
            <div style="font-size: 1.75rem; font-weight: 800; color: #10234B; margin-top: 6px;">Welcome Back</div>
            <div style="font-size: 0.88rem; color: #526987;">Login to your Railway Earning Dashboard to continue</div>
        </div>
        """, unsafe_allow_html=True)

        if auth_mode == "Login":
            with st.form("login_form"):
                u_in = st.text_input("Username", placeholder="Enter your username").strip()
                p_in = st.text_input("Password", type="password", placeholder="Enter your password").strip()
                
                c_rem, c_forgot = st.columns([1, 1])
                with c_rem:
                    remember_me = st.checkbox("Remember me", value=True)
                with c_forgot:
                    st.markdown("<div style='text-align:right; font-size:0.85rem; padding-top:4px;'><a href='#' style='color:#0B49B5; text-decoration:none; font-weight:600;'>Reset Password</a></div>", unsafe_allow_html=True)
                
                submit_login = st.form_submit_button("Login  →")
                
                if submit_login:
                    valid, status, msg = verify_user(u_in, p_in)
                    if valid and status == 'APPROVED':
                        st.session_state.authenticated = True
                        st.session_state.username = u_in
                        st.success("Login Successful!")
                        st.rerun()
                    elif valid and status == 'PENDING':
                        st.warning(f"⚠️ Account '{u_in}' is PENDING approval.")
                    elif status == "INVALID_PASSWORD":
                        st.error("Incorrect Password!")
                    elif status == "USER_NOT_FOUND":
                        st.error("Username does not exist.")
                    else:
                        st.error(f"Login failed: {msg}")
                        
            st.markdown('<div style="text-align: center; font-size: 0.8rem; color: #526987; margin-top: 1.2rem;">Not a member? Contact your administrator</div>', unsafe_allow_html=True)
            
        else:
            with st.form("signup_form"):
                nu = st.text_input("Username", placeholder="Choose or enter existing username").strip()
                np = st.text_input("New Password", type="password", placeholder="Enter new password").strip()
                cp = st.text_input("Confirm Password", type="password", placeholder="Confirm new password").strip()
                
                if st.form_submit_button("Register / Reset Password  →"):
                    if not nu or not np:
                        st.error("Username and Password cannot be empty!")
                    elif np != cp:
                        st.error("Passwords do not match!")
                    else:
                        ok, res_status = create_or_update_user(nu, np, auto_approve=True)
                        if ok:
                            st.success(f"✅ Account '{nu}' created/updated & APPROVED! You can login now.")
                        else:
                            st.error(f"❌ Error updating account: {res_status}")

    st.stop()

# ----------------- DASHBOARD HELPER FUNCTIONS -----------------
def format_inr(number):
    try:
        if pd.isna(number) or number is None: return "0"
        val = round(float(number))
        is_neg = val < 0
        s = str(abs(val))
        res = s if len(s) <= 3 else s[-3:]
        s = s[:-3] if len(s) > 3 else ""
        while len(s) > 0:
            res = s[-2:] + "," + res
            s = s[:-2]
        return f"-{res}" if is_neg else res
    except Exception: return str(number)

def format_plain_number(number):
    try:
        if pd.isna(number) or number is None: return "0"
        return str(int(round(float(number))))
    except Exception: return str(number)

def format_session(raw_s):
    s = str(raw_s).split('.')[0].strip()
    return f"{s[:4]}-{s[4:]}" if len(s) == 6 else s

def parse_session(fmt_s):
    return str(fmt_s).replace('-', '').strip()

def safe_get_station_col(conn, table_name='booking'):
    try:
        df_cols = pd.read_sql(text(f'SELECT * FROM "{table_name}" LIMIT 1'), conn).columns
        for c in df_cols:
            c_clean = str(c).upper().replace('_', '').replace(' ', '').strip()
            if c_clean in ['STATION', 'STATIONCODE', 'STNCODE', 'STATIONCOD']:
                return c
    except Exception: pass
    return 'STATION'

# ----------------- CACHED DATABASE QUERIES -----------------
@st.cache_data(ttl=3600, show_spinner=False)
def load_all_stations():
    with engine.connect() as conn:
        try:
            stn_col = safe_get_station_col(conn, 'booking')
            q = f'SELECT DISTINCT "{stn_col}" AS stn FROM booking'
            df = pd.read_sql(text(q), conn)
            return sorted(df['stn'].dropna().unique().tolist())
        except Exception:
            return ["ABP", "BSB", "LKO"]

@st.cache_data(ttl=3600, show_spinner=False)
def load_all_sessions():
    with engine.connect() as conn:
        try:
            df = pd.read_sql(text('SELECT DISTINCT "SESSION" FROM booking ORDER BY "SESSION" DESC'), conn)
            raw_sess = [str(s).split('.')[0].strip() for s in df['SESSION'].dropna().tolist()]
            return [format_session(s) for s in raw_sess if len(s) == 6]
        except Exception:
            return ["2026-27", "2025-26"]

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_station_details(station_code):
    try:
        with engine.connect() as conn:
            df_stn = pd.read_sql(text('SELECT * FROM "station_list"'), conn)
            norm_map = {str(c).upper().replace('_', '').replace(' ', '').strip(): c for c in df_stn.columns}
            code_col = norm_map.get('STATION', norm_map.get('STATIONCODE', norm_map.get('STNCODE', None)))
            
            if code_col:
                matched = df_stn[df_stn[code_col].astype(str).str.strip().str.upper() == station_code.strip().upper()]
                if not matched.empty:
                    r = matched.iloc[0]
                    row_map = {str(k).upper().replace('_', '').replace(' ', '').strip(): v for k, v in r.items()}
                    return (
                        row_map.get('STATIONNAME', row_map.get('STNAME', '')),
                        row_map.get('CATEGORY', row_map.get('CAT', '')),
                        row_map.get('SECTION', row_map.get('CMISECTION', '')),
                        row_map.get('CMINAME', row_map.get('CMI', ''))
                    )
    except Exception: pass
    return "", "", "", ""

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_aggregated_metric(table_name, station_code, sess, months_tuple, col_name):
    if not months_tuple: return 0.0
    m_str = "','".join([m.upper().strip() for m in months_tuple])
    with engine.connect() as conn:
        stn_c = safe_get_station_col(conn, table_name)
        q = f'''
            SELECT SUM("{col_name}") as val FROM "{table_name}"
            WHERE UPPER(TRIM(CAST("{stn_c}" AS TEXT))) = UPPER('{station_code.strip()}') 
              AND CAST("SESSION" AS TEXT) = '{sess}'
              AND UPPER(TRIM(CAST("MONTH" AS TEXT))) IN ('{m_str}')
        '''
        try:
            val = pd.read_sql(text(q), conn)['val'].iloc[0]
            return float(val) if pd.notnull(val) else 0.0
        except Exception: 
            return 0.0

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_multi_station_summary(stations_tuple, filters_tuple):
    if not stations_tuple or not filters_tuple:
        return pd.DataFrame()
    
    stn_str = "','".join([s.strip().upper() for s in stations_tuple])
    b_frames = []
    p_frames = []
    
    with engine.connect() as conn:
        b_stn_c = safe_get_station_col(conn, 'booking')
        p_stn_c = safe_get_station_col(conn, 'reservation_org')
        
        for sess, m_list in filters_tuple:
            if not m_list: continue
            m_str = "','".join([m.upper().strip() for m in m_list])
            
            qb = f'''
                SELECT CAST("{b_stn_c}" AS TEXT) AS stn,
                       SUM("PASSENGERS") AS b_pass,
                       SUM("EARNING") AS b_earn
                FROM booking
                WHERE UPPER(TRIM(CAST("{b_stn_c}" AS TEXT))) IN ('{stn_str}')
                  AND CAST("SESSION" AS TEXT) = '{sess}'
                  AND UPPER(TRIM(CAST("MONTH" AS TEXT))) IN ('{m_str}')
                GROUP BY 1
            '''
            qp = f'''
                SELECT CAST("{p_stn_c}" AS TEXT) AS stn,
                       SUM("PASSENGERS") AS p_pass,
                       SUM("EARNINGS") AS p_earn
                FROM reservation_org
                WHERE UPPER(TRIM(CAST("{p_stn_c}" AS TEXT))) IN ('{stn_str}')
                  AND CAST("SESSION" AS TEXT) = '{sess}'
                  AND UPPER(TRIM(CAST("MONTH" AS TEXT))) IN ('{m_str}')
                GROUP BY 1
            '''
            try:
                df_b = pd.read_sql(text(qb), conn)
                if not df_b.empty: b_frames.append(df_b)
            except Exception: pass
            
            try:
                df_p = pd.read_sql(text(qp), conn)
                if not df_p.empty: p_frames.append(df_p)
            except Exception: pass

    all_stns = pd.DataFrame({'stn': [s.strip().upper() for s in stations_tuple]})
    
    if b_frames:
        cat_b = pd.concat(b_frames, ignore_index=True).groupby('stn', as_index=False).sum()
        all_stns = pd.merge(all_stns, cat_b, on='stn', how='left')
    else:
        all_stns['b_pass'] = 0; all_stns['b_earn'] = 0.0
        
    if p_frames:
        cat_p = pd.concat(p_frames, ignore_index=True).groupby('stn', as_index=False).sum()
        all_stns = pd.merge(all_stns, cat_p, on='stn', how='left')
    else:
        all_stns['p_pass'] = 0; all_stns['p_earn'] = 0.0

    all_stns = all_stns.fillna(0)
    all_stns['Booking Passengers'] = all_stns['b_pass']
    all_stns['Prs Passenger'] = all_stns['p_pass']
    all_stns['Total Passengers'] = all_stns['b_pass'] + all_stns['p_pass']
    all_stns['Booking Earning'] = all_stns['b_earn']
    all_stns['Prs Earning'] = all_stns['p_earn']
    all_stns['Total Earning'] = all_stns['b_earn'] + all_stns['p_earn']
    
    all_stns = all_stns.rename(columns={'stn': 'Station Code'})
    res_cols = ['Station Code', 'Booking Passengers', 'Prs Passenger', 'Total Passengers', 'Booking Earning', 'Prs Earning', 'Total Earning']
    return all_stns[res_cols].sort_values('Total Earning', ascending=False)

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_tab_filtered_data(table_name, station_code, filters_tuple):
    frames = []
    with engine.connect() as conn:
        stn_c = safe_get_station_col(conn, table_name)
        for sess, m_list in filters_tuple:
            if not m_list: continue
            m_str = "','".join([m.upper().strip() for m in m_list])
            q = f'''
                SELECT * FROM "{table_name}" 
                WHERE UPPER(TRIM(CAST("{stn_c}" AS TEXT))) = UPPER('{station_code.strip()}') 
                  AND CAST("SESSION" AS TEXT) = '{sess}'
                  AND UPPER(TRIM(CAST("MONTH" AS TEXT))) IN ('{m_str}')
            '''
            try:
                df = pd.read_sql(text(q), conn)
                if not df.empty:
                    df['Fmt Session'] = format_session(sess)
                    if 'MONTH' in df.columns:
                        df['MONTH'] = df['MONTH'].astype(str).str.strip()
                    frames.append(df)
            except Exception: pass
            
    if not frames: return pd.DataFrame()
    full_df = pd.concat(frames, ignore_index=True)
    drop_cols = ['STATION', 'SESSION', 'station', 'session', 'STATION_CODE', 'STATION_COD', 'ROPD', 'ropd', 'Ropd']
    full_df = full_df.drop(columns=[c for c in drop_cols if c in full_df.columns])
    return full_df

# ----------------- CONSTANTS & CHRONOLOGICAL MONTH ORDER -----------------
MONTH_DAYS = {'Apr': 30, 'May': 31, 'Jun': 30, 'Jul': 31, 'Aug': 31, 'Sep': 30, 'Oct': 31, 'Nov': 30, 'Dec': 31, 'Jan': 31, 'Feb': 28, 'Mar': 31}
MONTH_ORDER = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
QUARTERS = {
    'Q1 (Apr-Jun)': ['Apr', 'May', 'Jun'],
    'Q2 (Jul-Sep)': ['Jul', 'Aug', 'Sep'],
    'Q3 (Oct-Dec)': ['Oct', 'Nov', 'Dec'],
    'Q4 (Jan-Mar)': ['Jan', 'Feb', 'Mar']
}

now = datetime.now()
current_month_num = now.month
prev_month_num = 12 if current_month_num == 1 else current_month_num - 1
month_num_to_abbr = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
default_ending_month = month_num_to_abbr.get(prev_month_num, 'Aug')

# ----------------- SIDEBAR & FILTERS -----------------
st.sidebar.markdown(f"👤 **User:** `{st.session_state.username}`")
if st.sidebar.button("🔒 Logout", use_container_width=True):
    st.session_state.authenticated = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("🔍 Dashboard Filters")

# Station Select
try:
    stns = load_all_stations()
    selected_station = st.sidebar.selectbox("Select Station", stns)
except Exception as e:
    st.error(f"Error loading stations: {e}"); st.stop()

selected_multi_stations = st.sidebar.multiselect("Select Multiple Stations (Summary Tab)", stns, default=stns[:5] if len(stns) >= 5 else stns)

# Session Select
try:
    fmt_sess = load_all_sessions()
    selected_fmt_session = st.sidebar.selectbox("Select Session", fmt_sess)
    selected_raw_session = parse_session(selected_fmt_session)
except Exception as e:
    st.error(f"Error loading sessions: {e}"); st.stop()

start_yr = int(selected_raw_session[:4])
end_yr = int(selected_raw_session[4:])
prev_raw_session = f"{start_yr - 1:04d}{end_yr - 1:02d}"

filter_type = st.sidebar.radio("Time Filter Type", ["Quarterly", "6 Months", "Full Year", "Last 3 Months", "Last 6 Months", "Custom Months"])

query_filters_curr = []
query_filters_prev = []

if filter_type in ["Quarterly", "6 Months", "Full Year", "Custom Months"]:
    if filter_type == "Quarterly":
        selected_months = QUARTERS[st.sidebar.selectbox("Select Quarter", list(QUARTERS.keys()))]
    elif filter_type == "6 Months":
        h = st.sidebar.selectbox("Select Half", ["H1 (Apr-Sep)", "H2 (Oct-Mar)"])
        selected_months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'] if "H1" in h else ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
    elif filter_type == "Full Year":
        selected_months = MONTH_ORDER
    else:
        selected_months = st.sidebar.multiselect("Select Months", MONTH_ORDER, default=['Apr', 'May', 'Jun'])

    query_filters_curr = [(selected_raw_session, tuple(selected_months))]
    query_filters_prev = [(prev_raw_session, tuple(selected_months))]
    display_period_text = f"Months: {', '.join(selected_months)}"
else:
    def_idx = MONTH_ORDER.index(default_ending_month) if default_ending_month in MONTH_ORDER else 4
    end_m = st.sidebar.selectbox("Current/Ending Month", MONTH_ORDER, index=def_idx)
    n_months = 3 if filter_type == "Last 3 Months" else 6
    end_idx = MONTH_ORDER.index(end_m)
    
    if end_idx >= n_months - 1:
        curr_m_list = tuple(MONTH_ORDER[end_idx - n_months + 1 : end_idx + 1])
        query_filters_curr = [(selected_raw_session, curr_m_list)]
        query_filters_prev = [(prev_raw_session, curr_m_list)]
    else:
        overlap_prev_count = n_months - (end_idx + 1)
        prev_m_list = tuple(MONTH_ORDER[-overlap_prev_count:])
        curr_m_list = tuple(MONTH_ORDER[:end_idx + 1])
        query_filters_curr = [(prev_raw_session, prev_m_list), (selected_raw_session, curr_m_list)]
        query_filters_prev = [(f"{start_yr - 2:04d}{end_yr - 2:02d}", prev_m_list), (prev_raw_session, curr_m_list)]

    display_period_text = f"{filter_type} (Ending {end_m})"

total_days = sum([sum([MONTH_DAYS.get(m, 30) for m in m_list]) for _, m_list in query_filters_curr])

period_range_desc_parts = []
for sess, m_list in query_filters_curr:
    if m_list:
        period_range_desc_parts.append(f"{format_session(sess)} {m_list[0]} to {format_session(sess)} {m_list[-1]}")
period_range_desc = " | ".join(period_range_desc_parts)

stn_name, cat, cmi_sec, cmi_name = fetch_station_details(selected_station)

# METRICS
def get_total_fast(table_name, filters_list, col_name):
    t = 0.0
    for sess, m_tuple in filters_list:
        t += fetch_aggregated_metric(table_name, selected_station, sess, m_tuple, col_name)
    return t

b_ear_curr = get_total_fast('booking', query_filters_curr, 'EARNING')
b_ear_prev = get_total_fast('booking', query_filters_prev, 'EARNING')
b_pass_curr = get_total_fast('booking', query_filters_curr, 'PASSENGERS')

p_ear_curr = get_total_fast('reservation_org', query_filters_curr, 'EARNINGS')
p_ear_prev = get_total_fast('reservation_org', query_filters_prev, 'EARNINGS')
p_pass_curr = get_total_fast('reservation_org', query_filters_curr, 'PASSENGERS')

g_ear_curr = get_total_fast('goods', query_filters_curr, 'OW_FREIGHT')
g_ear_prev = get_total_fast('goods', query_filters_prev, 'OW_FREIGHT')

pr_ear_curr = get_total_fast('parcel', query_filters_curr, 'OW_FREIGHT')
pr_ear_prev = get_total_fast('parcel', query_filters_prev, 'OW_FREIGHT')

comb_pass_curr = b_pass_curr + p_pass_curr
comb_ear_curr = b_ear_curr + p_ear_curr
comb_ear_prev = b_ear_prev + p_ear_prev

# HEADER
head_col1, head_col2 = st.columns([4, 1.1])

with head_col1:
    train_icon = get_train_logo_html()
    st.markdown(f'''
        <div class="main-title">
            {train_icon} STATION EARNING & TRAFFIC EXECUTIVE DASHBOARD
        </div>
    ''', unsafe_allow_html=True)
    st.markdown(f'<div class="station-subtitle">Station: <span class="highlight-badge">{selected_station}</span> | Session: <b>{selected_fmt_session}</b> | {display_period_text}</div>', unsafe_allow_html=True)
    if stn_name or cat or cmi_sec or cmi_name:
        st.markdown(f'<div class="station-meta-info">📍 Name: <b>{stn_name}</b> | Cat: <b>{cat}</b> | CMI Sec: <b>{cmi_sec}</b> | CMI Name: <b>{cmi_name}</b></div>', unsafe_allow_html=True)

with head_col2:
    st.markdown(f'<div class="days-badge">🗓️ <b>{total_days} Days Selected</b></div>', unsafe_allow_html=True)

st.markdown("<hr style='margin: 8px 0 14px 0; border:none; border-bottom:1px solid #cbd5e1;'>", unsafe_allow_html=True)

# METRIC CARDS
c1, c2, c3, c4, c5 = st.columns(5)

def render_centered_metric(col, title, curr, prev, days, is_combined=False, pass_val=0):
    per_day = curr / days if days > 0 else 0
    growth = ((curr - prev) / prev * 100) if prev > 0 else 0
    delta_class = "metric-delta-pos" if growth >= 0 else "metric-delta-neg"
    
    if is_combined:
        pass_per_day = pass_val / days if days > 0 else 0
        content = f"""
            <div class="metric-card" style="border-top: 4px solid #0B49B5;">
                <div class="metric-title">👥 COMBINED PASSENGER</div>
                <div class="metric-value">₹ {format_inr(curr)}</div>
                <div class="metric-sub">Pass: {format_plain_number(pass_val)} | P/Day: {format_plain_number(pass_per_day)}</div>
                <div class="metric-sub">Ear/Day: ₹ {format_inr(per_day)}</div>
                <div class="{delta_class}">{growth:+.1f}% vs Prev. Year</div>
            </div>
        """
    else:
        content = f"""
            <div class="metric-card">
                <div class="metric-title">{title}</div>
                <div class="metric-value">₹ {format_inr(curr)}</div>
                <div style="flex-grow:1;"></div>
                <div class="metric-sub">Ear/Day: ₹ {format_inr(per_day)}</div>
                <div class="{delta_class}">{growth:+.1f}% vs Prev. Year</div>
            </div>
        """
    col.markdown(content, unsafe_allow_html=True)

render_centered_metric(c1, "Combined", comb_ear_curr, comb_ear_prev, total_days, is_combined=True, pass_val=comb_pass_curr)
render_centered_metric(c2, "BOOKING EARNING", b_ear_curr, b_ear_prev, total_days)
render_centered_metric(c3, "PRS ORG EARNING", p_ear_curr, p_ear_prev, total_days)
render_centered_metric(c4, "GOODS FREIGHT", g_ear_curr, g_ear_prev, total_days)
render_centered_metric(c5, "PARCEL FREIGHT", pr_ear_curr, pr_ear_prev, total_days)

st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

# TABS
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Booking", "PRS Org", "Combined Passenger", "Goods", "Parcel", "Reservation", "Multiple Stations Summary"
])

def render_table_with_totals(df, title):
    if df.empty:
        st.info(f"No records available for {title} in selected period.")
        return
    
    if 'MONTH' in df.columns:
        df['MONTH'] = df['MONTH'].astype(str).str.strip().str.title()
        df['MONTH'] = pd.Categorical(df['MONTH'], categories=MONTH_ORDER, ordered=True)
        
        sort_cols = []
        if 'Fmt Session' in df.columns:
            sort_cols.append('Fmt Session')
        elif 'SESSION' in df.columns:
            sort_cols.append('SESSION')
        sort_cols.append('MONTH')
        
        df = df.sort_values(sort_cols).dropna(subset=['MONTH'])
        
    num_cols = df.select_dtypes(include=['number']).columns
    total_row = {c: df[c].sum() for c in num_cols}
    
    if 'MONTH' in df.columns: total_row['MONTH'] = 'TOTAL'
    if 'Fmt Session' in df.columns: total_row['Fmt Session'] = 'ALL'
    if 'Station Code' in df.columns: total_row['Station Code'] = 'TOTAL'
    
    df_totals = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
    df_totals.columns = [str(c).replace('_', ' ').title() for c in df_totals.columns]

    formatted_df = df_totals.copy()
    for col in formatted_df.columns:
        col_u = col.upper()
        if any(kw in col_u for kw in ['PASSENGER', 'REQUISITION', 'SLIP', 'COUNT', 'TICKET', 'TONNAGE', 'WAGON', 'RAKE']):
            formatted_df[col] = formatted_df[col].apply(lambda x: format_plain_number(x) if pd.notna(x) else "0")
        elif any(kw in col_u for kw in ['EARNING', 'FREIGHT', 'AMOUNT', 'CASH', 'NET']):
            formatted_df[col] = formatted_df[col].apply(lambda x: format_inr(x) if pd.notna(x) else "0")
        else:
            if col in num_cols:
                formatted_df[col] = formatted_df[col].apply(lambda x: format_plain_number(x) if pd.notna(x) else "0")

    html_code = '<table class="custom-dashboard-table"><thead><tr>'
    for col in formatted_df.columns:
        html_code += f'<th>{col}</th>'
    html_code += '</tr></thead><tbody>'

    for i, row in formatted_df.iterrows():
        is_last = (i == len(formatted_df) - 1)
        row_class = ' class="total-row"' if is_last else ''
        html_code += f'<tr{row_class}>'
        for val in row:
            html_code += f'<td>{val}</td>'
        html_code += '</tr>'
    
    html_code += '</tbody></table>'
    st.markdown(html_code, unsafe_allow_html=True)

tuple_curr_filters = tuple(query_filters_curr)

with tab1:
    render_table_with_totals(fetch_tab_filtered_data('booking', selected_station, tuple_curr_filters), "Booking")

with tab2:
    render_table_with_totals(fetch_tab_filtered_data('reservation_org', selected_station, tuple_curr_filters), "PRS Org")

with tab3:
    df_b = fetch_tab_filtered_data('booking', selected_station, tuple_curr_filters)
    df_p = fetch_tab_filtered_data('reservation_org', selected_station, tuple_curr_filters)
    
    if not df_b.empty or not df_p.empty:
        if not df_b.empty: 
            df_b.columns = [c.upper().strip() for c in df_b.columns]
            if 'MONTH' in df_b.columns: df_b['MONTH'] = df_b['MONTH'].astype(str).str.strip().str.title()
        if not df_p.empty: 
            df_p.columns = [c.upper().strip() for c in df_p.columns]
            if 'MONTH' in df_p.columns: df_p['MONTH'] = df_p['MONTH'].astype(str).str.strip().str.title()
        
        m_df = pd.merge(df_b, df_p, on=['FMT SESSION', 'MONTH'], how='outer', suffixes=('_BOOKING', '_PRS'))
        combined = pd.DataFrame()
        
        combined['Fmt Session'] = m_df['FMT SESSION']
        combined['MONTH'] = m_df['MONTH']
        
        pass_b = m_df.get('PASSENGERS_BOOKING', m_df.get('PASSENGER_BOOKING', 0)).fillna(0)
        pass_p = m_df.get('PASSENGERS_PRS', m_df.get('PASSENGER_PRS', 0)).fillna(0)
        combined['Booking Passengers'] = pass_b
        combined['Prs Passenger'] = pass_p
        combined['Total Passengers'] = pass_b + pass_p
        
        earn_b = m_df.get('EARNING', 0).fillna(0)
        earn_p = m_df.get('EARNINGS', 0).fillna(0)
        combined['Booking Earning'] = earn_b
        combined['Prs Earning'] = earn_p
        combined['Total Earning'] = earn_b + earn_p
        
        desired_cols = [
            'Fmt Session', 'MONTH', 'Booking Passengers', 'Prs Passenger', 
            'Total Passengers', 'Booking Earning', 'Prs Earning', 'Total Earning'
        ]
        combined = combined[desired_cols]
        
        combined['MONTH'] = pd.Categorical(combined['MONTH'], categories=MONTH_ORDER, ordered=True)
        combined = combined.sort_values(['Fmt Session', 'MONTH']).dropna(subset=['MONTH'])
        
        render_table_with_totals(combined, "Combined Passenger")
    else:
        st.info("Combined data unavailable for selected period.")

with tab4:
    render_table_with_totals(fetch_tab_filtered_data('goods', selected_station, tuple_curr_filters), "Goods")

with tab5:
    render_table_with_totals(fetch_tab_filtered_data('parcel', selected_station, tuple_curr_filters), "Parcel")

with tab6:
    df_res = fetch_tab_filtered_data('reservation', selected_station, tuple_curr_filters)
    if not df_res.empty:
        cols_to_drop = []
        for col in df_res.columns:
            c_clean = str(col).upper().replace('_', '').replace(' ', '').strip()
            if c_clean in ['EARNING', 'EARNINGS', 'ROPD', 'ROPDCASH']:
                cols_to_drop.append(col)
        if cols_to_drop:
            df_res = df_res.drop(columns=[c for c in cols_to_drop if c in df_res.columns])
            
    render_table_with_totals(df_res, "Reservation")

with tab7:
    st.markdown(f'<div class="period-info-box">🗓️ <b>Data Period:</b> {period_range_desc}</div>', unsafe_allow_html=True)
    if not selected_multi_stations:
        st.warning("Please select at least one station from sidebar 'Select Multiple Stations (Summary Tab)' to view results.")
    else:
        df_multi_res = fetch_multi_station_summary(tuple(selected_multi_stations), tuple_curr_filters)
        render_table_with_totals(df_multi_res, "Multiple Stations Summary")
