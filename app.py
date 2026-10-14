import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import bcrypt
import base64
import os
from datetime import datetime

# ----------------- PAGE CONFIGURATION -----------------
st.set_page_config(
    page_title="Railway Earning Dashboard Access", 
    page_icon="🚄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------- SECURE DATABASE CREDENTIALS -----------------
DEFAULT_DB_URL = "postgresql+psycopg2://postgres.ggrpypensvabbvpyzqbx:2234723pamcell@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
SUPABASE_URL = st.secrets.get("SUPABASE_URL", DEFAULT_DB_URL).strip()

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
    if username == "computercell" and password == "pamcell2234723":
        return True, "APPROVED", "Master Admin User"
    if username == "StationEarning" and password == "pamcell2234723":
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

# ----------------- CUSTOM CSS FOR LAYOUT & RESPONSIVENESS -----------------
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
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
            padding: 1rem 2rem !important;
            max-width: 100% !important;
        }
        
        html, body, [class*="css"], h1, h2, h3, h4, h5, h6, div, span, p {
            font-family: 'Inter', sans-serif !important;
        }

        /* LEFT PANEL STYLING */
        .login-left-banner {
            background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 50%, #93c5fd 100%);
            padding: 2.2rem 2.5rem;
            border-radius: var(--borderRadius);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: 0 10px 30px rgba(11, 73, 181, 0.08);
            margin-bottom: 1rem;
        }

        .banner-logo-title {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.8rem;
            font-weight: 800;
            color: var(--textColor);
            line-height: 1.2;
            margin-bottom: 10px;
        }

        .banner-subtext {
            font-size: 0.92rem;
            color: var(--mutedText);
            font-weight: 500;
            line-height: 1.45;
            margin-bottom: 1.8rem;
        }

        .banner-features-grid {
            display: flex;
            gap: 15px;
            margin-bottom: 1.8rem;
        }

        .feature-box {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            flex: 1;
        }

        .feature-icon-circle {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 6px;
            font-size: 1.1rem;
            box-shadow: 0 4px 10px rgba(0,0,0,0.04);
        }

        .feature-title-text {
            font-size: 0.78rem;
            font-weight: 600;
            color: var(--textColor);
            line-height: 1.2;
        }

        .banner-train-image {
            width: 100%;
            border-radius: 12px;
            box-shadow: 0 8px 20px rgba(16, 35, 75, 0.12);
            object-fit: cover;
            max-height: 280px;
        }

        /* RIGHT PANEL STYLING */
        .login-right-panel {
            background-color: var(--cardBackground);
            border: 1px solid var(--borderColor);
            border-radius: var(--borderRadius);
            padding: 2rem 2.2rem;
            box-shadow: 0 10px 25px rgba(16, 35, 75, 0.05);
        }

        .card-top-icon {
            text-align: center;
            margin-bottom: 8px;
        }

        .card-title {
            font-size: 1.65rem;
            font-weight: 800;
            color: var(--textColor);
            text-align: center;
            margin-bottom: 4px;
        }

        .card-desc {
            font-size: 0.85rem;
            color: var(--mutedText);
            text-align: center;
            margin-bottom: 1.5rem;
        }

        /* INPUT OVERRIDES */
        div[data-testid="stTextInput"] label {
            font-weight: 600 !important;
            color: var(--textColor) !important;
            font-size: 0.85rem !important;
            margin-bottom: 4px !important;
        }

        div[data-testid="stTextInput"] input {
            border-radius: 8px !important;
            border: 1px solid var(--borderColor) !important;
            padding: 8px 12px !important;
            font-size: 0.9rem !important;
        }

        div[data-testid="stForm"] button {
            background-color: var(--primary) !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            border-radius: 8px !important;
            padding: 10px 0 !important;
            border: none !important;
            width: 100% !important;
            margin-top: 10px !important;
        }

        .card-footer-note {
            text-align: center;
            font-size: 0.78rem;
            color: var(--mutedText);
            margin-top: 1.2rem;
        }
    </style>
""", unsafe_allow_html=True)

# ----------------- LOGIN PAGE -----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.authenticated:
    p_left, p_right = st.columns([1, 1], gap="medium")
    
    with p_left:
        st.markdown('''
            <div class="login-left-banner">
                <div>
                    <div class="banner-logo-title">
                        <svg xmlns="http://www.w3.org/2000/svg" width="38" height="38" viewBox="0 0 24 24" fill="#0B49B5"><path d="M12 2c-4 0-8 .5-8 4v9.5C4 17.43 5.57 19 7.5 19L6 20.5v.5h12v-.5L16.5 19c1.93 0 3.5-1.57 3.5-3.5V6c0-3.5-4-4-8-4zm0 2c3.71 0 5.8 0 6 2H6c.2-2 2.29-2 6-2zm-5 6.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm10 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5-1.5zm-5 6.5c-2.76 0-5-1.12-5-2.5h10c0 1.38-2.24 2.5-5 2.5z"/></svg>
                        <div>Railway Earning<br>Dashboard Access</div>
                    </div>
                    <div class="banner-subtext">
                        Track your earnings, manage your account and stay connected with the railway ecosystem.
                    </div>
                </div>
                
                <div class="banner-features-grid">
                    <div class="feature-box">
                        <div class="feature-icon-circle" style="background-color: #dbeafe; color: #0B49B5;">📊</div>
                        <div class="feature-title-text">View Earnings Reports</div>
                    </div>
                    <div class="feature-box">
                        <div class="feature-icon-circle" style="background-color: #dcfce7; color: #16a34a;">🛡️</div>
                        <div class="feature-title-text">Secure & Reliable Access</div>
                    </div>
                    <div class="feature-box">
                        <div class="feature-icon-circle" style="background-color: #f3e8ff; color: #9333ea;">👤</div>
                        <div class="feature-title-text">Manage Your Account</div>
                    </div>
                </div>
                
                <div>
                    <img src="https://images.unsplash.com/photo-1532105956626-9569c03602f6?q=80&w=1000&auto=format&fit=crop" class="banner-train-image" alt="Railway Train">
                </div>
            </div>
        ''', unsafe_allow_html=True)

    with p_right:
        auth_mode = st.radio("Access Mode", ["Login", "Sign Up / Reset Password"], horizontal=True)
        
        if auth_mode == "Login":
            st.markdown('''
                <div class="login-right-panel">
                    <div class="card-top-icon">
                        <svg xmlns="http://www.w3.org/2000/svg" width="42" height="42" viewBox="0 0 24 24" fill="#0B49B5"><path d="M12 2c-4 0-8 .5-8 4v9.5C4 17.43 5.57 19 7.5 19L6 20.5v.5h12v-.5L16.5 19c1.93 0 3.5-1.57 3.5-3.5V6c0-3.5-4-4-8-4zm0 2c3.71 0 5.8 0 6 2H6c.2-2 2.29-2 6-2zm-5 6.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm10 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5-1.5zm-5 6.5c-2.76 0-5-1.12-5-2.5h10c0 1.38-2.24 2.5-5 2.5z"/></svg>
                    </div>
                    <div class="card-title">Welcome Back</div>
                    <div class="card-desc">Login to your Railway Earning Dashboard to continue</div>
                </div>
            ''', unsafe_allow_html=True)
            
            with st.form("login_form"):
                u_in = st.text_input("Username", placeholder="Enter your username").strip()
                p_in = st.text_input("Password", type="password", placeholder="Enter your password").strip()
                
                c_rem, c_forgot = st.columns([1, 1])
                with c_rem:
                    remember_me = st.checkbox("Remember me", value=True)
                with c_forgot:
                    st.markdown("<div style='text-align:right; font-size:0.8rem; padding-top:4px;'><a href='#' style='color:#0B49B5; text-decoration:none; font-weight:600;'>Reset Password</a></div>", unsafe_allow_html=True)
                
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
                        
            st.markdown('<div class="card-footer-note">Not a member? Contact your administrator</div>', unsafe_allow_html=True)
            
        else:
            st.markdown('''
                <div class="login-right-panel">
                    <div class="card-title">Create / Reset Account</div>
                    <div class="card-desc">Enter credentials to register or reset password</div>
                </div>
            ''', unsafe_allow_html=True)
            
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

# ----------------- MAIN DASHBOARD CODE BELOW -----------------
st.sidebar.markdown(f"👤 **User:** `{st.session_state.username}`")
if st.sidebar.button("🔒 Logout", use_container_width=True):
    st.session_state.authenticated = False
    st.rerun()

st.title("🚄 Station Earning & Traffic Executive Dashboard")
st.write("Welcome to the executive dashboard!")
