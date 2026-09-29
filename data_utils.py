from pathlib import Path
import pandas as pd
import streamlit as st

@st.cache_data  # cache so the CSV is only read once, not on every rerun
def load_data() -> pd.DataFrame:
    path = Path(__file__).parent / "data" / "reservoirs.csv"
    df = pd.read_csv(path)
    return df

print(df.head())
print(df.dtypes)