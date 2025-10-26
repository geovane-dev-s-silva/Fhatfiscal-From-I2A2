import streamlit as st
import pandas as pd
from visualizacao.visualization import interpretar_pergunta_visualizacao, gerar_grafico_visualizacao

def exibir_visualizacao(df):
    st.subheader("📊 Visualizações Inteligentes")

    if df is None or df.empty or df.columns.size == 0:
        st.warning("⚠️ Nenhum dado fiscal válido foi carregado. Verifique o arquivo enviado.")
        return

    pergunta = st.text_input("Digite uma pergunta sobre os dados fiscais:", key="pergunta_visualizacao")

    if pergunta:
        resultado = interpretar_pergunta_visualizacao(pergunta, df)

        st.markdown(f"**Insight gerado:** {resultado['insight']}")
        st.markdown(f"**Foco:** `{resultado['foco']}` | **Gráfico:** `{resultado['tipo_grafico']}`")

        grafico = gerar_grafico_visualizacao(resultado['tipo_grafico'], df, resultado['foco'])
        st.plotly_chart(grafico, use_container_width=True)