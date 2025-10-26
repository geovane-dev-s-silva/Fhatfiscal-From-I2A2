import streamlit as st
import pandas as pd
from painel_inteligente import analise_inteligente

st.title("🧠 Análise Inteligente Fiscal")

arquivo = st.file_uploader("Envie um arquivo fiscal (CSV)", type="csv")

if arquivo:
    df = pd.read_csv(arquivo, sep=';')
    insights = analise_inteligente(df)

    st.subheader("🔍 Insights Gerados")
    for item in insights:
        st.write(item)