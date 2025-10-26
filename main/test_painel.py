# test_painel.py
import streamlit as st
import pandas as pd
from painel_inteligente import gerar_alertas

st.title("🔍 Teste de Alertas Fiscais")

# Simulação de upload
arquivo = st.file_uploader("Envie um arquivo fiscal (CSV)", type="csv")

if arquivo:
    df = pd.read_csv(arquivo, sep=';')
    alertas = gerar_alertas(df)

    st.subheader("⚠️ Alertas Gerados")
    for alerta in alertas:
        st.warning(alerta)