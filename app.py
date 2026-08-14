import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

st.set_page_config(page_title="SHG Data Diagnostic", layout="wide")

SUPABASE_URL = "postgresql://postgres.ggrpypensvabbvpyzqbx:pamcelllko2234723@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"

@st.cache_resource
def get_database_connection():
    return create_engine(SUPABASE_URL)

engine = get_database_connection()

st.title("🔍 SHG Station Database Inspector")

try:
    with engine.connect() as conn:
        st.subheader("1. Booking Table Data for SHG")
        df_b = pd.read_sql(text("SELECT * FROM booking WHERE \"STATION_CODE\" LIKE '%SHG%'"), conn)
        st.dataframe(df_b)
        
        st.subheader("2. Reservation Org Table Data for SHG")
        df_p = pd.read_sql(text("SELECT * FROM reservation_org WHERE \"STATION_CODE\" LIKE '%SHG%'"), conn)
        st.dataframe(df_p)

except Exception as e:
    st.error(f"Error checking database: {e}")
