import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

st.set_page_config(page_title="SHG Data Inspector", layout="wide")

SUPABASE_URL = "postgresql://postgres.ggrpypensvabbvpyzqbx:pamcelllko2234723@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"

@st.cache_resource
def get_database_connection():
    return create_engine(SUPABASE_URL, pool_pre_ping=True)

engine = get_database_connection()

st.title("🔍 SHG Station Database Inspector")

try:
    with engine.connect() as conn:
        st.subheader("1. Station Codes in Booking Table")
        stns = pd.read_sql(text('SELECT DISTINCT "STATION_CODE" FROM booking'), conn)
        st.dataframe(stns)

        st.subheader("2. Sample Data for SHG in Booking Table")
        df_b = pd.read_sql(text('SELECT * FROM booking WHERE "STATION_CODE" LIKE \'%SHG%\' LIMIT 10'), conn)
        st.dataframe(df_b)

        st.subheader("3. Sample Data for SHG in Reservation Org Table")
        df_p = pd.read_sql(text('SELECT * FROM reservation_org WHERE "STATION_CODE" LIKE \'%SHG%\' LIMIT 10'), conn)
        st.dataframe(df_p)

except Exception as e:
    st.error(f"Database Error: {e}")
