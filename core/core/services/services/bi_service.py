import streamlit as st
import pandas as pd

def generate_dashboard():
    data = {
        "Projeto": ["A", "B", "C"],
        "Custo": [10000, 15000, 7000],
        "Prazo": [30, 45, 20]
    }

    df = pd.DataFrame(data)

    st.dataframe(df)
    st.bar_chart(df.set_index("Projeto")["Custo"])
