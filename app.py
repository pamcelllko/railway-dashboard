import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import bcrypt
import smtplib
from email.mime.text import MIMEText

# ----------------- PAGE CONFIGURATION -----------------
st.set_page_config(
    page_title="Railway Earning Executive Dashboard", 
    page_icon="```python
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

# ----------------- ADVANCED DYNAMIC CSS -----------------
st.markdown("""
    <style>
        @import url('[https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap](https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap)');
        
        :root {
            --bg-card: #ffffff;
            --border-card: #cbd5e1;
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
            padding-top: 2rem !important; 
            padding-bottom: 1rem !important;
            padding-left: 1.2rem !important;
            padding-right: 1.2rem !important;
            max-width: 100% !important;
        }
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
        }

        /* Header Title Area */
        .main-header-container {
            padding: 4px 0px 12px 0px;
            border-bottom: 2px solid var(--border-card);
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }
        .main-title {
            font-size: 1.35rem !important;
            font-weight: 900 !important;
            color: var(--text-main) !important;
            letter-spacing: -0.3px;
        }
        .station-subtitle {
            font-size: 0.9rem !important;
            color: var(--text-sub) !important;
            font-weight: 600 !important;
            margin-top: 3px !important;
        }
        .station-meta-info {
            font-size: 0.83rem !important;
            color: #2563eb !important;
            font-weight: 700 !important;
            margin-top: 2px !important;
        }
        .highlight-badge {
            background-color: #1e3a8a;
            color: #ffffff !important;
            padding: 2px
