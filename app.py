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
ADMIN_NAME = "Mohammed Rafik"
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
        smtp_user = st.secrets.get("SMTP_USER", "")
        smtp_pass = st.secrets.get("SMTP_PASS", "")
        
        if smtp_user and smtp_pass:
            email_body = f"""Respected {ADMIN_NAME},

A user '{new_user}' has requested access to the Railway Earning & Traffic Executive Dashboard.

Username: {new_user}
Status: Pending Approval

Please approve or manage this user directly in your Supabase Database (user_auth table).
"""
            msg = MIMEText(email_body)
            msg['Subject'] = f"Action Required: Dashboard Signup Request ({new_user})"
            msg['From'] = smtp_user
            msg['To'] = ADMIN_EMAIL

            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [ADMIN_EMAIL], msg.as_string())
            server.quit()
            return True, "Approval Email Sent Successfully!"
        else:
            return False, "SMTP Credentials (SMTP_USER/SMTP_PASS) not found in Streamlit Secrets."
    except Exception as e:
        return False, f"Email sending failed: {str(e)}"

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

# ----------------- CSS STYLING -----------------
st.markdown("""
    <style>
        @import url('[https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap](https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap)');
        
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

        .table-bg-container {
            background-color: #f7f3ed;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #e2dcd5;
        }

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

def format_plain_number
