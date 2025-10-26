# visualization.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from llm_utils import gerar_resposta_llm

class Visualization:
    """
    Classe responsável por gerar gráficos e visualizações interativas.
    """

    @staticmethod
    def gerar_grafico_barras(df: pd.DataFrame, x: str, y: str):
        plt.figure(figsize=(10, 6))
        sns.barplot(data=df, x=x, y=y)
        plt.title("Gráfico de Barras")
        plt.show()

    @staticmethod
    def gerar_grafico_linhas(df: pd.DataFrame, x: str, y: str):
        plt.figure(figsize=(10, 6))
        sns.lineplot(data=df, x=x, y=y)
        plt.title("Gráfico de Linhas")
        plt.show()

    @staticmethod
    def gerar_grafico_interativo(df: pd.DataFrame, x: str, y: str):
        fig = px.bar(df, x=x, y=y, title="Gráfico Interativo de Barras")
        fig.show()

def interpretar_pergunta_visualizacao(pergunta, df):
    """
    Usa LLM para interpretar a pergunta e sugerir foco, tipo de gráfico e insight.
    """
    colunas = ", ".join(df.columns[:20])
    amostra = df.head(3).to_dict(orient="records")

    prompt = f"""
Você é um analista fiscal com experiência em visualização de dados.

O usuário fez a seguinte pergunta: "{pergunta}"

Com base nos dados abaixo, identifique:
1. Qual coluna deve ser usada como foco da análise (ex: UF, produto, imposto, cfop, etc.)
2. Qual tipo de gráfico é mais adequado (escolha entre: barra, pizza, linha)
3. Gere um insight textual curto com base nessa análise

DADOS:
- Colunas disponíveis: {colunas}
- Amostra de dados: {amostra}

Responda no seguinte formato JSON:
{{
  "foco": "...",
  "tipo_grafico": "...",
  "insight": "..."
}}
"""

    resposta = gerar_resposta_llm(pergunta=prompt, df=df)

    try:
        resultado = eval(resposta)  # ou json.loads(resposta) se estiver bem formatado
        return resultado
    except Exception:
        return {
            "foco": df.columns[0],
            "tipo_grafico": "barra",
            "insight": "Visualização padrão gerada com base nos dados disponíveis."
        }

def gerar_grafico_visualizacao(tipo, df, foco):
    """
    Gera gráfico com base no tipo sugerido e na coluna foco.
    """
    try:
        # Se a coluna foco não existir, usa a primeira coluna
        if foco not in df.columns:
            foco = df.columns[0]
        
        # Tenta agrupar por contagem primeiro (mais comum em dados fiscais)
        if df[foco].dtype == 'object' or df[foco].dtype.name == 'category':
            # Para colunas categóricas, conta ocorrências
            agrupado = df[foco].value_counts().reset_index()
            agrupado.columns = [foco, 'Quantidade']
            y_coluna = 'Quantidade'
        else:
            # Para colunas numéricas, tenta somar valores
            agrupado = df.groupby(foco, as_index=False).agg({
                col: 'sum' for col in df.select_dtypes(include=['number']).columns if col != foco
            })
            
            # Se não houver colunas numéricas, conta ocorrências
            if len(agrupado.columns) <= 1:
                agrupado = df[foco].value_counts().reset_index()
                agrupado.columns = [foco, 'Quantidade']
                y_coluna = 'Quantidade'
            else:
                y_coluna = agrupado.columns[1]
        
        # Limita a 20 itens para melhor visualização
        if len(agrupado) > 20:
            agrupado = agrupado.nlargest(20, y_coluna)
        
        # Adiciona título personalizado
        titulo = f"Análise de {foco}"
        
        # Gera gráfico baseado no tipo
        if tipo == "barra":
            fig = px.bar(
                agrupado, 
                x=foco, 
                y=y_coluna,
                title=titulo,
                labels={y_coluna: 'Total', foco: foco},
                color=y_coluna,
                color_continuous_scale='Blues'
            )
            fig.update_traces(texttemplate='%{y}', textposition='outside')
            
        elif tipo == "pizza":
            fig = px.pie(
                agrupado, 
                names=foco, 
                values=y_coluna,
                title=titulo,
                hole=0.3  # Gráfico de rosca
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            
        elif tipo == "linha":
            fig = px.line(
                agrupado, 
                x=foco, 
                y=y_coluna,
                title=titulo,
                markers=True,
                labels={y_coluna: 'Total', foco: foco}
            )
            fig.update_traces(
                line=dict(width=3, color='#FFD700'),
                marker=dict(size=10, color='#FFD700')
            )
        else:
            fig = px.bar(agrupado, x=foco, y=y_coluna, title=titulo)
        
        # Estilização
        fig.update_layout(
            height=500,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            hovermode='x unified',
            showlegend=False
        )
        
        return fig
        
    except Exception as e:
        # Gráfico de fallback em caso de erro
        import plotly.graph_objects as go
        
        fig = go.Figure()
        fig.add_annotation(
            text=f"⚠️ Erro ao gerar gráfico: {str(e)}<br>Verifique se a coluna '{foco}' existe nos dados.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="orange"),
            align="center"
        )
        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        return fig

def carregar_dados_seguro(caminho_arquivo, separador=';'):
    """
    Lê um arquivo CSV com segurança, tratando erros de leitura e arquivos vazios.
    """
    try:
        df = pd.read_csv(caminho_arquivo, sep=separador)
        if df.empty or df.columns.size == 0:
            return None
        return df
    except pd.errors.EmptyDataError:
        return None
    except Exception:
        return None