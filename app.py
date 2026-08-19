import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import bcrypt
import smtplib
from email.mime.text import MIMEText

# ----------------- PAGE CONFIGURATION -----------------
st.set_page_config(
    page_title="Railway Earning Executive Dashboard", 
    page_icon="🚄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- SECURE DATABASE CREDENTIALS -----------------
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "postgresql://postgres.ggrpypensvabbvpyzqbx:pamcelllko2234723@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres").strip()
ADMIN_EMAIL = "adilrafeeque@gmail.com"

@st.cache_resource
def get_database_connection():
    return create_engine(SUPABASE_URL, pool_pre_ping=True)

engine = get_database_connection()

# ----------------- SUPABASE AUTH & EMAIL APPROVAL DB -----------------
def init_supabase_auth_db():
    with engine.connect() as conn:
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS user_auth (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING'
            );
        '''))
        conn.commit()

init_supabase_auth_db()

def send_approval_email(new_user):
    try:
        # Example SMTP Setup (Configure your email server in st.secrets if using Gmail SMTP)
        smtp_user = st.secrets.get("SMTP_USER", "noreply.dashboard@gmail.com")
        smtp_pass = st.secrets.get("SMTP_PASS", "")
        
        msg = MIMEText(f"A new user '{new_user}' has requested signup on Railway Earning Dashboard.\n\nTo approve this account, please click link or update status in Database.")
        msg['Subject'] = f"Action Required: New Dashboard Signup Request ({new_user})"
        msg['From'] = smtp_user
        msg['To'] = ADMIN_EMAIL

        if smtp_pass:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [ADMIN_EMAIL], msg.as_string())
            server.quit()
    except Exception as e:
        pass

def create_user(username, password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        with engine.connect() as conn:
            conn.execute(text('INSERT INTO user_auth (username, password, status) VALUES (:u, :p, :s)'), 
                         {'u': username, 'p': hashed, 's': 'PENDING'})
            conn.commit()
        send_approval_email(username)
        return True
    except Exception:
        return False

def verify_user(username, password):
    if username == "StationEarning" and password == "pamcell2234723":
        return True, "APPROVED"
    with engine.connect() as conn:
        res = conn.execute(text('SELECT password, status FROM user_auth WHERE username = :u'), {'u': username}).fetchone()
        if res:
            if bcrypt.checkpw(password.encode('utf-8'), res[0].encode('utf-8')):
                return True, res[1]
    return False, "INVALID"

# ----------------- CSS MATCHING EXACT IMAGE STYLING -----------------
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
        
        .block-container { 
            padding-top: 1.5rem !important; 
            padding-bottom: 1rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
            background-color: #f4f6f8 !important;
        }

        /* Image 1 Header Style */
        .header-box-img {
            background-color: #f0f4f6;
            padding: 10px 18px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 15px;
        }
        .header-title-img {
            font-size: 1.4rem !important;
            font-weight: 800 !important;
            color: #0d3b36 !important;
            letter-spacing: -0.2px;
        }

        /* Station Info Box */
        .stn-info-card {
            background-color: #ffffff;
            border-left: 5px solid #0d3b36;
            padding: 10px 16px;
            border-radius: 6px;
            margin-bottom: 15px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            font-size: 0.9rem;
            color: #1e293b;
        }

        /* Image 2 Table Container & Cream Background */
        .table-bg-container {
            background-color: #f7f3ed;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #e2dcd5;
        }

        /* Custom Tab Bar with Red Dividers */
        .tab-bar {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
            font-weight: 700;
            font-size: 0.92rem;
        }
        .tab-btn-active {
            background-color: #0d3b36;
            color: #ffffff !important;
            padding: 4px 16px;
            border-radius: 18px;
            text-transform: uppercase;
        }
        .tab-btn-inactive {
            color: #000000;
            padding: 4px 8px;
        }
        .divider-pipe {
            color: #dc2626;
            font-weight: 800;
        }

        /* Table Styling matching Image 2 */
        div[data-testid="stDataFrame"] table {
            background-color: #f7f3ed !important;
            border-collapse: collapse !important;
            width: 100% !important;
        }
        div[data-testid="stDataFrame"] th {
            background-color: #f7f3ed !important;
            color: #000000 !important;
            font-weight: 800 !important;
            border: 1px solid #e2dcd5 !important;
            text-align: center !important;
            font-size: 0.85rem !important;
        }
        div[data-testid="stDataFrame"] td {
            background-color: #f7f3ed !important;
            color: #000000 !important;
            border: 1px solid #e2dcd5 !important;
            text-align: center !important;
            font-size: 0.85rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# ----------------- HELPER FUNCTIONS -----------------
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
        if pd.isna(number) or number is None: return ""
        return str(int(round(float(number))))
    except Exception: return str(number)

def format_session(raw_s):
    s = str(raw_s).split('.')[0].strip()
    return f"{s[:4]}-{s[4:]}" if len(s) == 6 else s

def parse_session(fmt_s):
    return str(fmt_s).replace('-', '').strip()

# ----------------- LOGIN PAGE -----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.authenticated:
    st.markdown("<h2 style='text-align: center; color: #0d3b36; font-weight:800;'>🚄 Railway Earning Dashboard Access</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        auth_mode = st.radio("Choose Option", ["Login", "Sign Up / Create Account"], horizontal=True)
        if auth_mode == "Login":
            st.subheader("🔑 User Login")
            with st.form("login_form"):
                u_in = st.text_input("Username").strip()
                p_in = st.text_input("Password", type="password").strip()
                if st.form_submit_button("Login to Dashboard", use_container_width=True):
                    valid, status = verify_user(u_in, p_in)
                    if valid and status == 'APPROVED':
                        st.session_state.authenticated = True
                        st.session_state.username = u_in
                        st.success("Login Successful!")
                        st.rerun()
                    elif valid and status == 'PENDING':
                        st.warning("⚠️ Your account is PENDING approval from adilrafeeque@gmail.com.")
                    else:
                        st.error("Invalid Username or Password")
        else:
            st.subheader("📝 Create New Account")
            with st.form("signup_form"):
                nu = st.text_input("Choose Username").strip()
                np = st.text_input("Choose Password", type="password").strip()
                cp = st.text_input("Confirm Password", type="password").strip()
                if st.form_submit_button("Register Account", use_container_width=True):
                    if np != cp: st.error("Passwords do not match!")
                    elif create_user(nu, np):
                        st.success("✅ Signup Request Sent! Account will be active once approved by adilrafeeque@gmail.com.")
                    else: st.error("Username already exists.")
    st.stop()

# ----------------- SIDEBAR & FILTERS -----------------
st.sidebar.markdown(f"👤 **User:** `{st.session_state.username}`")
if st.sidebar.button("🔒 Logout", use_container_width=True):
    st.session_state.authenticated = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("🔍 Filters")

MONTH_ORDER = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']

# Station Select
try:
    with engine.connect() as conn:
        stns = sorted(pd.read_sql(text('SELECT DISTINCT "STATION_COD" FROM booking'), conn)['STATION_COD'].dropna().unique().tolist())
    selected_station = st.sidebar.selectbox("Select Station", stns)
except Exception as e:
    st.error(f"Error loading stations: {e}"); st.stop()

# Session Select
try:
    with engine.connect() as conn:
        raw_sess = [str(s).split('.')[0].strip() for s in pd.read_sql(text('SELECT DISTINCT "SESSION" FROM booking ORDER BY "SESSION" DESC'), conn)['SESSION'].dropna().tolist()]
        fmt_sess = [format_session(s) for s in raw_sess if len(s) == 6]
    selected_fmt_session = st.sidebar.selectbox("Select Session", fmt_sess)
    selected_raw_session = parse_session(selected_fmt_session)
except Exception as e:
    st.error(f"Error loading sessions: {e}"); st.stop()

# Station Details Lookup from Excel Synced Table
stn_details_html = ""
try:
    with engine.connect() as conn:
        df_stn_info = pd.read_sql(text(f"SELECT * FROM station_list WHERE UPPER(TRIM(\"STATION_CODE\")) = UPPER('{selected_station.strip()}') LIMIT 1"), conn)
        if not df_stn_info.empty:
            row = df_stn_info.iloc[0]
            stn_name = row.get('STATION_NAME', '')
            cat = row.get('CATEGORY', '')
            cmi_sec = row.get('CMI_SECTION', '')
            cmi_name = row.get('CMI_NAME', '')
            stn_details_html = f"<b>Station Name:</b> {stn_name} | <b>Category:</b> {cat} | <b>CMI Section:</b> {cmi_sec} | <b>CMI Name:</b> {cmi_name}"
except Exception:
    pass

# ----------------- HEADER (EXACT IMAGE 1 MATCH) -----------------
st.markdown("""
    <div class="header-box-img">
        <span style="font-size: 1.5rem;">🚂</span>
        <span class="header-title-img">Station Earning & Traffic Executive Dashboard 📈</span>
    </div>
""", unsafe_allow_html=True)

if stn_details_html:
    st.markdown(f'<div class="stn-info-card">📍 {stn_details_html}</div>', unsafe_allow_html=True)

# ----------------- TABLE FETCH & RENDER (EXACT IMAGE 2 MATCH) -----------------
def fetch_table_data(table_name):
    with engine.connect() as conn:
        q = f'''
            SELECT * FROM {table_name} 
            WHERE UPPER(TRIM(CAST("STATION_COD" AS TEXT))) = UPPER('{selected_station.strip()}') 
              AND CAST("SESSION" AS TEXT) = '{selected_raw_session}'
        '''
        try:
            df = pd.read_sql(text(q), conn)
            if not df.empty:
                df['FMT SESSION'] = selected_fmt_session
                return df
        except Exception: conn.rollback()
    return pd.DataFrame()

tabs = ["Booking", "PRS Org", "Combined Passenger", "Goods", "Parcel", "Reservation"]
selected_tab = st.radio("Select View", tabs, horizontal=True, label_visibility="collapsed")

# Custom Tab Bar with Red Dividers Pipe
tab_html = '<div class="tab-bar">'
for t in tabs:
    if t == selected_tab:
        tab_html += f'<span class="tab-btn-active">{t.upper()}</span>'
    else:
        tab_html += f'<span class="tab-btn-inactive">{t}</span>'
    if t != tabs[-1]:
        tab_html += '<span class="divider-pipe">|</span>'
tab_html += '</div>'

st.markdown(f'<div class="table-bg-container">{tab_html}', unsafe_allow_html=True)

tbl_name_map = {"Booking": "booking", "PRS Org": "reservation_org", "Goods": "goods", "Parcel": "parcel", "Reservation": "reservation"}
current_table = tbl_name_map.get(selected_tab, "booking")

df_data = fetch_table_data(current_table)

if not df_data.empty:
    num_cols = df_data.select_dtypes(include=['number']).columns
    total_row = {c: df_data[c].sum() for c in num_cols}
    if 'MONTH' in df_data.columns: total_row['MONTH'] = 'TOTAL'
    if 'FMT SESSION' in df_data.columns: total_row['FMT SESSION'] = ''

    df_totals = pd.concat([df_data, pd.DataFrame([total_row])], ignore_index=True)
    df_totals.columns = [str(c).replace('_', ' ').title() for c in df_totals.columns]

    column_config = {}
    for col in df_totals.columns:
        col_u = col.upper()
        if 'PASSENGER' in col_u:
            df_totals[col] = df_totals[col].apply(lambda x: format_plain_number(x) if pd.notnull(x) else "")
        elif any(kw in col_u for kw in ['EARNING', 'FREIGHT', 'AMOUNT', 'CASH']):
            df_totals[col] = df_totals[col].apply(lambda x: format_inr(x) if pd.notnull(x) else "")
        column_config[col] = st.column_config.TextColumn(col, alignment="center")

    st.dataframe(df_totals, use_container_width=True, hide_index=True, column_config=column_config, height=500)
else:
    st.info(f"No records for {selected_tab} in session {selected_fmt_session}")

st.markdown('</div>', unsafe_allow_html=True)
