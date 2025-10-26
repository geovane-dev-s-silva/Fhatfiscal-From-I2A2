import streamlit as st
import pandas as pd
from painel_inteligente import gerar_metrica_sped

st.title("📁 Métrica de SPED Fiscal")

arquivo = st.file_uploader("Envie um arquivo fiscal (CSV)", type="csv")

if arquivo:
    df = pd.read_csv(arquivo, sep=';')
    metrica = gerar_metrica_sped(df)

    if metrica.empty:
        st.warning("⚠️ Nenhuma coluna relacionada ao SPED foi encontrada no arquivo.")
    else:
        st.subheader("📊 Vínculo com SPED")
        st.dataframe(metrica)