import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Railway Earning Dashboard", layout="wide")

SUPABASE_URL = "postgresql://postgres.ggrpypensvabbvpyzqbx:pamcelllko2234723@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"

@st.cache_resource
def get_database_connection():
    return create_engine(SUPABASE_URL)

engine = get_database_connection()

st.title("🔍 Columns Inspector")

try:
    with engine.connect() as conn:
        tables = ['booking', 'goods', 'parcel', 'reservation', 'reservation_org']
        
        for t in tables:
            st.write(f"### 📋 Table: `{t}`")
            sample_df = pd.read_sql(text(f'SELECT * FROM "{t}" LIMIT 2'), conn)
            st.write("**Columns:**", list(sample_df.columns))
            st.dataframe(sample_df)
            st.divider()

except Exception as e:
    st.error(f"Error fetching columns: {e}")
