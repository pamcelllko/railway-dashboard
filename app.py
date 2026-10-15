
# ----------------- LOGIN PAGE -----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.authenticated:

    # Professional login page styling
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #edf5ff, #f8fbff);
    }

    .block-container {
        padding-top: 2rem !important;
        max-width: 1400px !important;
    }

    .login-banner {
        background: linear-gradient(145deg, #eff7ff, #d9ebff);
        border: 1px solid #dce4ef;
        border-radius: 24px;
        padding: 35px 30px;
        box-shadow: 0 15px 40px rgba(35,70,120,.08);
    }

    .login-brand {
        color: #4774b5;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 2px;
        margin-bottom: 12px;
    }

    .login-title {
        color: #10234b;
        font-size: 34px;
        font-weight: 800;
        line-height: 1.2;
        margin-bottom: 18px;
    }

    .login-description {
        color: #526987;
        font-size: 15px;
        line-height: 1.8;
        margin-bottom: 26px;
    }

    .login-feature {
        background: rgba(255,255,255,.7);
        border: 1px solid rgba(220,228,239,.8);
        border-radius: 12px;
        padding: 15px;
        margin: 12px 0;
        color: #10234b;
        font-size: 14px;
        font-weight: 600;
    }

    .login-card {
        background: white;
        border: 1px solid #e1e8f1;
        border-radius: 22px;
        padding: 25px 10px;
        box-shadow: 0 18px 55px rgba(35,70,120,.08);
    }

    div[data-testid="stTextInput"] label {
        color: #10234b !important;
        font-weight: 650 !important;
    }

    div[data-testid="stTextInput"] input {
        border-radius: 10px !important;
        min-height: 45px !important;
        border: 1px solid #dce4ef !important;
    }

    div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(100deg,#0b49b5,#1763d3) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        min-height: 48px !important;
        font-weight: 700 !important;
        width: 100% !important;
    }

    div[data-testid="stFormSubmitButton"] button:hover {
        box-shadow: 0 8px 18px rgba(11,73,181,.2);
        border: none !important;
    }

    .login-footer {
        text-align: center;
        color: #7c8da5;
        font-size: 12px;
        margin-top: 25px;
    }

    @media(max-width: 700px) {
        .login-title { font-size: 27px; }
        .login-banner { padding: 25px 20px; }
    }
    </style>
    """, unsafe_allow_html=True)

    left, right = st.columns([1.05, 0.95], gap="large")

    # LEFT: Branding and features
    with left:
        st.markdown("""
        <div class="login-banner">
            <div class="login-brand">🚄 SMART RAILWAY TOOLS</div>

            <div class="login-title">
                Railway Earning<br>
                Dashboard Access
            </div>

            <div class="login-description">
                Track your earnings, manage your account,
                and stay connected with the railway ecosystem.
            </div>

            <div class="login-feature">
                📊 &nbsp; View Earnings Reports
                <div style="font-size:11px;color:#6a7f9e;
                            font-weight:400;margin-top:5px">
                    Clear and organized earning insights
                </div>
            </div>

            <div class="login-feature">
                🛡️ &nbsp; Secure &amp; Reliable Access
                <div style="font-size:11px;color:#6a7f9e;
                            font-weight:400;margin-top:5px">
                    Secure account verification
                </div>
            </div>

            <div class="login-feature">
                👤 &nbsp; Manage Your Account
                <div style="font-size:11px;color:#6a7f9e;
                            font-weight:400;margin-top:5px">
                    Your railway workspace in one place
                </div>
            </div>

            <div style="margin-top:22px;
                        color:#56708f;font-size:11px">
                ● &nbsp; Railway Earning Dashboard
            </div>
        </div>
        """, unsafe_allow_html=True)

    # RIGHT: Existing authentication logic
    with right:
        st.markdown("""
        <div style="
            background:white;
            border:1px solid #e1e8f1;
            border-radius:22px;
            padding:30px 25px 15px;
            box-shadow:0 18px 55px rgba(35,70,120,.08);
            margin-bottom:15px;
        ">
            <div style="font-size:11px;font-weight:800;
                        letter-spacing:1.7px;color:#4774b5">
                WELCOME BACK
            </div>
            <div style="font-size:27px;font-weight:800;
                        color:#10234b;margin-top:8px">
                Sign in to your account
            </div>
            <div style="font-size:13px;color:#60728f;
                        margin-top:9px">
                Enter your credentials to continue to the dashboard.
            </div>
        </div>
        """, unsafe_allow_html=True)

        auth_mode = st.radio(
            "Account Access",
            ["Login", "Sign Up / Reset Password"],
            horizontal=True,
            label_visibility="collapsed",
            key="auth_mode"
        )

        if auth_mode == "Login":

            with st.form("login_form", clear_on_submit=False):
                u_in = st.text_input(
                    "Username",
                    placeholder="Enter your username",
                    key="login_username"
                ).strip()

                p_in = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    key="login_password"
                )

                remember_me = st.checkbox(
                    "Remember me",
                    value=False
                )

                submit_login = st.form_submit_button(
                    "Login to Dashboard  →",
                    use_container_width=True
                )

                if submit_login:
                    if not u_in or not p_in:
                        st.error("Please enter both username and password.")
                    else:
                        valid, status, msg = verify_user(u_in, p_in)

                        if valid and status == "APPROVED":
                            st.session_state.authenticated = True
                            st.session_state.username = u_in
                            st.rerun()

                        elif valid and status == "PENDING":
                            st.warning(
                                f"Account '{u_in}' is pending approval."
                            )

                        elif status == "INVALID_PASSWORD":
                            st.error("Incorrect password.")

                        elif status == "USER_NOT_FOUND":
                            st.error("Username does not exist.")

                        else:
                            st.error(f"Login failed: {msg}")

            st.markdown("""
            <div class="login-footer">
                🔒 Your account access is managed securely.<br><br>
                Need access? Contact your administrator.
            </div>
            """, unsafe_allow_html=True)

        else:
            with st.form("signup_form"):
                nu = st.text_input(
                    "Username",
                    placeholder="Enter username"
                ).strip()

                np = st.text_input(
                    "New Password",
                    type="password",
                    placeholder="Enter new password"
                )

                cp = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Confirm new password"
                )

                if st.form_submit_button(
                    "Register / Reset Password  →",
                    use_container_width=True
                ):
                    if not nu or not np:
                        st.error("Username and password are required.")

                    elif np != cp:
                        st.error("Passwords do not match.")

                    else:
                        ok, result = create_or_update_user(
                            nu, np, auto_approve=True
                        )

                        if ok:
                            st.success(
                                f"Account '{nu}' updated successfully. "
                                "You can now log in."
                            )
                        else:
                            st.error(f"Account update failed: {result}")

    st.stop()

# ----------------- DASHBOARD HELPER FUNCTIONS -----------------
