import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import bcrypt
import smtplib
from email.mime.text import MIMEText
import base64
import os

# ----------------- PAGE CONFIGURATION -----------------
st.set_page_config(
    page_title="Railway Earning Executive Dashboard", 
    page_icon="🚄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- SECURE DATABASE CREDENTIALS -----------------
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "postgresql://postgres.ggrpypensvabbvpyzqbx:2234723pamcell@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require").strip()
ADMIN_NAME = "Mohammed Rafik"
ADMIN_EMAIL = "adilrafeeque@gmail.com"

@st.cache_resource
def get_database_connection():
    return create_engine(
        SUPABASE_URL, 
        pool_size=15,
        max_overflow=25,
        pool_pre_ping=True,  # Automatically reconnects dropped/stale connections
        isolation_level="AUTOCOMMIT"
    )

engine = get_database_connection()

# ----------------- DATABASE KEEP-ALIVE HEALTH CHECK -----------------
def keep_db_alive():
    """Executes a lightweight ping query to keep Supabase active during cron pings"""
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
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="36" height="36" style="vertical-align: middle; fill: #1d4ed8; margin-right:8px;">
      <path d="M480 384c0 13.255-10.745 24-24 24H56c-13.255 0-24-10.745-24-24s10.745-24 24-24h400c13.255 0 24 10.745 24 24zM88 320l-48 96h432l-48-96H88zm320-192c0-35.346-28.654-64-64-64H168c-35.346 0-64 28.654-64 64v160h304V128zm-224 0h144v48H184v-48z"/>
    </svg>
    """

# ----------------- SUPABASE AUTH & EMAIL APPROVAL DB -----------------
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
    # 1. HARDCODED MASTER LOGINS (Always works 100% even if DB is paused/unreachable)
    if username == "computercell" and password == "pamcell2234723":
        return True, "APPROVED", "Master Admin User"
    if username == "StationEarning" and password == "pamcell2234723":
        return True, "APPROVED", "Master Admin User"
        
    # 2. DATABASE AUTHENTICATION
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

# ----------------- ADVANCED ROBOTO TYPOGRAPHY & UI CSS -----------------
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700;900&display=swap');
        
        :root {
            --bg-card: #ffffff;
            --border-card: #e2e8f0;
            --text-main: #0f172a;
            --text-sub: #334155;
            --text-muted: #64748b;
            --table-header-bg: #f8fafc;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --bg-card: #1e293b;
                --border-card: #334155;
                --text-main: #f8fafc;
                --text-sub: #cbd5e1;
                --text-muted: #94a3b8;
                --table-header-bg: #0f172a;
            }
        }

        .block-container { 
            padding-top: 2.8rem !important; 
            padding-bottom: 1rem !important;
            padding-left: 1.2rem !important;
            padding-right: 1.2rem !important;
            max-width: 100% !important;
        }
        
        html, body, [class*="css"], h1, h2, h3, h4, h5, h6, div, span, p {
            font-family: 'Roboto', sans-serif !important;
        }

        .main-title {
            font-family: 'Roboto', sans-serif !important;
            font-size: 1.45rem !important;
            font-weight: 900 !important;
            color: var(--text-main) !important;
            letter-spacing: -0.2px;
            line-height: 1.3 !important;
            display: flex;
            align-items: center;
        }
        .station-subtitle {
            font-family: 'Roboto', sans-serif !important;
            font-size: 0.9rem !important;
            color: var(--text-sub) !important;
            font-weight: 500 !important;
            margin-top: 4px !important;
        }
        .station-meta-info {
            font-family: 'Roboto', sans-serif !important;
            font-size: 0.85rem !important;
            color: #1d4ed8 !important;
            font-weight: 700 !important;
            margin-top: 6px !important;
            background-color: #eff6ff;
            padding: 5px 12px;
            border-radius: 6px;
            border: 1px solid #bfdbfe;
            display: inline-block;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        }
        .highlight-badge {
            background-color: #1e3a8a;
            color: #ffffff !important;
            padding: 2px 8px;
            border-radius: 5px;
            font-weight: 700;
        }
        .days-badge {
            font-family: 'Roboto', sans-serif !important;
            font-size: 0.85rem;
            font-weight: 700;
            background-color: var(--bg-card);
            color: var(--text-main);
            padding: 7px 16px;
            border-radius: 8px;
            border: 1px solid var(--border-card);
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            display: inline-block;
        }

        .metric-card {
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 10px;
            padding: 12px 8px;
            text-align: center !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            min-height: 142px !important;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            align-items: center;
            transition: transform 0.15s ease;
        }
        .metric-card:hover {
            transform: translateY(-2px);
        }
        .metric-title {
            font-family: 'Roboto', sans-serif !important;
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--text-sub);
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }
        .metric-value {
            font-family: 'Roboto', sans-serif !important;
            font-size: 1.22rem;
            font-weight: 900;
            color: var(--text-main);
            letter-spacing: -0.5px;
            margin: 2px 0;
        }
        .metric-sub {
            font-family: 'Roboto', sans-serif !important;
            font-size: 0.72rem;
            color: var(--text-muted);
            font-weight: 500;
        }
        .metric-delta-pos {
            font-family: 'Roboto', sans-serif !important;
            font-size: 0.75rem !important;
            font-weight: 700 !important;
            color: #15803d !important;
            background-color: #dcfce7 !important;
            padding: 2px 10px !important;
            border-radius: 20px !important;
            border: 1px solid #16a34a !important;
        }
        .metric-delta-neg {
            font-family: 'Roboto', sans-serif !important;
            font-size: 0.75rem !important;
            font-weight: 700 !important;
            color: #b91c1c !important;
            background-color: #fee2e2 !important;
            padding: 2px 10px !important;
            border-radius: 20px !important;
            border: 1px solid #ef4444 !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 6px !important;
            border-bottom: none !important;
            margin-bottom: 10px !important;
        }
        .stTabs [data-baseweb="tab"] {
            font-family: 'Roboto', sans-serif !important;
            height: 34px;
            padding: 0 16px !important;
            font-weight: 700 !important;
            font-size: 0.82rem !important;
            border-radius: 20px !important;
            color: var(--text-sub) !important;
            background-color: var(--bg-card) !important;
            border: 1px solid var(--border-card) !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1d4ed8 !important;
            color: #ffffff !important;
            border-color: #1d4ed8 !important;
        }

        div[data-testid="stDataFrame"] th, div[data-testid="stDataFrame"] th * {
            font-family: 'Roboto', sans-serif !important;
            text-align: center !important;
            justify-content: center !important;
            background-color: var(--table-header-bg) !important;
            color: var(--text-main) !important;
            font-weight: 700 !important;
            font-size: 0.82rem !important;
        }
        div[data-testid="stDataFrame"] td, div[data-testid="stDataFrame"] td * {
            font-family: 'Roboto', sans-serif !important;
            text-align: center !important;
            justify-content: center !important;
            font-size: 0.82rem !important;
            color: var(--text-main) !important;
        }
    </style>
""", unsafe_allow_html=True)

# ----------------- LOGIN PAGE -----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.authenticated:
    st.markdown("<h2 style='text-align: center; color: var(--text-main); font-weight:800; font-family: Roboto;'>🚄 Railway Earning Dashboard Access</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        auth_mode = st.radio("Choose Option", ["Login", "Sign Up / Reset Account Password"], horizontal=True)
        if auth_mode == "Login":
            st.subheader("🔑 User Login")
            with st.form("login_form"):
                u_in = st.text_input("Username").strip()
                p_in = st.text_input("Password", type="password").strip()
                submit_login = st.form_submit_button("Login to Dashboard", use_container_width=True)
                
                if submit_login:
                    valid, status, msg = verify_user(u_in, p_in)
                    if valid and status == 'APPROVED':
                        st.session_state.authenticated = True
                        st.session_state.username = u_in
                        st.success("Login Successful!")
                        st.rerun()
                    elif valid and status == 'PENDING':
                        st.warning(f"⚠️ Account '{u_in}' is PENDING approval. Please re-register in Sign Up option to approve immediately.")
                    elif status == "INVALID_PASSWORD":
                        st.error("Incorrect Password! If you forgot password, reset it using the Sign Up option.")
                    elif status == "USER_NOT_FOUND":
                        st.error("Username does not exist. Please create an account in Sign Up.")
                    else:
                        st.error(f"Login failed: {msg}")
                        
        else:
            st.subheader("📝 Create / Reset Account")
            st.caption("Enter username & new password. If user exists, password will be reset and APPROVED automatically.")
            with st.form("signup_form"):
                nu = st.text_input("Choose / Existing Username").strip()
                np = st.text_input("Choose Password", type="password").strip()
                cp = st.text_input("Confirm Password", type="password").strip()
                
                if st.form_submit_button("Register / Update Password", use_container_width=True):
                    if not nu or not np:
                        st.error("Username and Password cannot be empty!")
                    elif np != cp:
                        st.error("Passwords do not match!")
                    else:
                        ok, res_status = create_or_update_user(nu, np, auto_approve=True)
                        if ok:
                            st.success(f"✅ Account '{nu}' created/updated and APPROVED! You can now login directly.")
                        else:
                            st.error(f"❌ Error updating account: {res_status}")
    st.stop()
