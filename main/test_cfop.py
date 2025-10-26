import streamlit as st
import pandas as pd
from painel_inteligente import gerar_metrica_cfop

st.title("📊 Métrica de CFOPs")

arquivo = st.file_uploader("Envie um arquivo fiscal (CSV)", type="csv")

if arquivo:
    df = pd.read_csv(arquivo, sep=';')
    metrica = gerar_metrica_cfop(df)

    st.subheader("🔢 CFOPs mais utilizados")
    st.dataframe(metrica)