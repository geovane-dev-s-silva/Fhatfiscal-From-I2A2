# main/interface.py - Versão com Dica Inteligente Integrada

import streamlit as st
import time
from io import BytesIO
import os
from datetime import datetime


# 🎨 Estilo global da página
def aplicar_estilo():
    st.markdown(
        """
        <style>
            .stApp {
                background-color: #0D1B2A !important;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #FFD700 !important;
            }
            p, span, div, label, .stTextInput, .stTextArea, .stSelectbox, .stDownloadButton, .stButton {
                color: #222 !important;
            }
            /* Corrige cor do texto dentro de caixas de input */
            .stTextInput input, .stTextArea textarea {
                color: #222 !important;
                background: #fff !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )


# 🖼️ Logo do ChatFiscal (fixo no topo)
def exibir_logo():
    with st.container():
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        if os.path.exists("assets/logo_chatfiscal.png"):
            st.image("assets/logo_chatfiscal.png", width=260)
        st.markdown("</div>", unsafe_allow_html=True)


# 💬 Boas-vindas como popup (toast)
def boas_vindas():
    if "boas_vindas_exibida" not in st.session_state:
        st.toast("👋 Bem-vindo(a) ao ChatFiscal! Seu parceiro inteligente para análise tributária.", icon="💼")
        st.session_state["boas_vindas_exibida"] = True


# 📢 Introdução institucional (exibe uma vez)
def introducao_chatfiscal():
    if "introducao_exibida" not in st.session_state:
        st.markdown(
            """
            <div style='text-align: center; margin-top: 10px; margin-bottom: 20px;'>
                <p style='color: #FFD700; font-size: 18px; font-weight: 500;'>
                    O <strong>ChatFiscal</strong> é mais que um assistente tributário — é uma inteligência fiscal que transforma dados em decisões.  
                    Ele interpreta arquivos complexos, identifica inconsistências, responde dúvidas sobre ICMS, CFOP, CST e muito mais.  
                    Tudo isso com agilidade, precisão e uma linguagem que você entende.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.session_state["introducao_exibida"] = True


# 🦉 Dica do Corujito com VERSÃO INTELIGENTE (animação + download)
def exibir_dica_corujito(dica):
    """
    Exibe a dica do Corujito com animação de digitação e botão de download.
    
    Args:
        dica (str): Texto da dica (pode vir de gerar_dica_corujito_inteligente)
    """
    st.markdown("<div style='margin-top: 20px;'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 10])
    
    with col1:
        # Avatar do Corujito
        if os.path.exists("assets/mascote_corujito.png"):
            st.image("assets/mascote_corujito.png", width=80)
        else:
            st.markdown("🦉", unsafe_allow_html=True)
    
    with col2:
        # Container para animação de digitação
        container = st.empty()
        texto = ""
        
        # Animação de digitação (mais rápida para textos longos)
        velocidade = 0.01 if len(dica) > 500 else 0.03
        
        for letra in dica:
            texto += letra
            container.markdown(
                f"""
                <div style='background-color: #0D1B2A; border: 2px solid #FFD700; 
                            padding: 12px; border-radius: 10px; box-shadow: 0 0 10px rgba(255, 215, 0, 0.3);'>
                    <p style='color: #FFD700; font-size: 16px; font-weight: bold; margin-bottom: 8px;'>
                        💡 Dica do Corujito Fiscal:
                    </p>
                    <p style='color: #FFF; font-size: 15px; font-family: monospace; 
                              line-height: 1.6; white-space: pre-wrap;'>{texto}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            time.sleep(velocidade)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Botões de ação
    col_download, col_expandir = st.columns([1, 1])
    
    with col_download:
        # Botão de download da dica como .txt
        buffer = BytesIO()
        buffer.write(dica.encode("utf-8"))
        buffer.seek(0)
        
        st.download_button(
            label="📥 Baixar dica (.txt)",
            data=buffer,
            file_name=f"dica_corujito_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col_expandir:
        # Botão para exibir versão expandida (sem animação)
        if st.button("📋 Ver texto completo", use_container_width=True):
            with st.expander("📜 Texto Completo da Dica", expanded=True):
                st.markdown(f"``````")
    
    st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)


# 🦉 Versão SEM animação (para textos muito longos ou rápida exibição)
def exibir_dica_corujito_rapida(dica):
    """
    Versão sem animação para exibição instantânea.
    Útil quando a dica é muito longa ou quando a animação não é desejada.
    """
    st.markdown("<div style='margin-top: 20px;'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 10])
    
    with col1:
        if os.path.exists("assets/mascote_corujito.png"):
            st.image("assets/mascote_corujito.png", width=80)
        else:
            st.markdown("🦉", unsafe_allow_html=True)
    
    with col2:
        st.markdown(
            f"""
            <div style='background-color: #0D1B2A; border: 2px solid #FFD700; 
                        padding: 12px; border-radius: 10px; box-shadow: 0 0 10px rgba(255, 215, 0, 0.3);'>
                <p style='color: #FFD700; font-size: 16px; font-weight: bold; margin-bottom: 8px;'>
                    💡 Dica do Corujito Fiscal:
                </p>
                <p style='color: #FFF; font-size: 15px; font-family: monospace; 
                          line-height: 1.6; white-space: pre-wrap;'>{dica}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Botão de download
    buffer = BytesIO()
    buffer.write(dica.encode("utf-8"))
    buffer.seek(0)
    
    st.download_button(
        label="📥 Baixar dica (.txt)",
        data=buffer,
        file_name=f"dica_corujito_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )
    
    st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)


# 🧠 Resposta com avatar do agente fiscal
def exibir_resposta_agente(pergunta, resposta):
    """Exibe resposta do agente fiscal com avatar."""
    col1, col2 = st.columns([1, 10])
    
    with col1:
        if os.path.exists("assets/avatar_agente.png"):
            st.image("assets/avatar_agente.png", width=50)
        else:
            st.markdown("👨‍💼", unsafe_allow_html=True)
    
    with col2:
        st.markdown(
            f"""
            <div style='background-color: #0D1B2A; border: 2px solid #FFD700; 
                        padding: 10px; border-radius: 10px; box-shadow: 0 0 10px #FFD700;'>
                <strong style='color: #FFD700;'>Agente Fiscal:</strong><br>
                <span style='color: #FFF;'>{resposta}</span>
            </div>
            """,
            unsafe_allow_html=True
        )


# ⚠️ Pop-ups de alerta, erro e sucesso
def mostrar_alerta(mensagem):
    st.warning(f"⚠️ {mensagem}")


def mostrar_erro(mensagem):
    st.error(f"❌ {mensagem}")


def mostrar_sucesso(mensagem):
    st.success(f"✅ {mensagem}")


# 📌 Rodapé institucional com texto completo e logo ampliado
def exibir_rodape():
    st.markdown("---")
    col1, col2 = st.columns([1, 5])
    
    with col1:
        if os.path.exists("assets/logo_alquimistas.jpg"):
            st.image("assets/logo_alquimistas.jpg", width=120)
        else:
            st.markdown("🔬", unsafe_allow_html=True)
    
    with col2:
        st.markdown(
            """
            <div style='margin-top: 6px;'>
                <p style='color: #222; font-size: 16px; margin-bottom: 6px;'>
                    <strong>Projeto desenvolvido pelos Alquimistas Digitais, através da I2a2 — Instituto de Inteligência Artificial Aplicada</strong>
                </p>
                <p style='color: #222; font-size: 14px; margin-bottom: 4px;'>
                    Este agente fiscal autônomo é fruto de uma iniciativa educacional que desafia alunos a criar soluções inteligentes e inovadoras.
                </p>
                <p style='color: #FFD700; font-size: 14px; margin-bottom: 4px;'>
                    Versão 2.0 — Outubro de 2025
                </p>
                <p style='color: #222; font-size: 14px;'>
                    Feito com muito carinho, lógica afiada e uma pitada de criatividade.  
                    <br>© Alquimistas Digitais. Todos os direitos reservados.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )


# 🧩 Monta o topo da interface
def montar_interface():
    """Inicializa todos os elementos visuais do topo da página."""
    aplicar_estilo()
    exibir_logo()
    boas_vindas()
    introducao_chatfiscal()


# 🎯 Função auxiliar para gerar e exibir dica inteligente
def gerar_e_exibir_dica_inteligente(df, contexto_empresa="", historico=None, com_animacao=True):
    """
    Gera e exibe a dica inteligente do Corujito.
    
    Args:
        df: DataFrame com os dados fiscais
        contexto_empresa: Informações da empresa (ex: "SP | Comércio")
        historico: Histórico de perguntas/respostas
        com_animacao: Se True, usa animação de digitação
    
    Returns:
        str: Texto da dica gerada
    """
    try:
        # Importa a função inteligente
        from dicas_corujito import gerar_dica_corujito_inteligente
        
        # Gera a dica
        with st.spinner("🦉 Corujito analisando seus dados..."):
            dica = gerar_dica_corujito_inteligente(
                df=df,
                contexto_empresa=contexto_empresa,
                historico=historico
            )
        
        # Exibe com ou sem animação
        if com_animacao and len(dica) < 1000:  # Animação apenas para textos menores
            exibir_dica_corujito(dica)
        else:
            exibir_dica_corujito_rapida(dica)
        
        return dica
        
    except ImportError:
        # Fallback para versão básica
        dica_basica = f"""
📊 **ANÁLISE RÁPIDA DOS DADOS**
─────────────────────────────────
✅ Total de registros: {len(df)}
✅ Total de campos: {len(df.columns)}
✅ Campos vazios: {df.isnull().sum().sum()}

💡 **Pronto para análise!** Faça sua primeira pergunta ao Corujito.
        """
        
        if com_animacao:
            exibir_dica_corujito(dica_basica)
        else:
            exibir_dica_corujito_rapida(dica_basica)
        
        return dica_basica
    
    except Exception as e:
        st.error(f"❌ Erro ao gerar dica: {str(e)}")
        return None

# Upload do arquivo fiscal
arquivo = st.file_uploader("Envie seu arquivo fiscal", type=["csv", "xml", "pdf"])

# Criação das abas
aba_dados, aba_historico, aba_auditoria, aba_visualizacoes, aba_painel = st.tabs([
    "Dados do Chat", "Histórico", "Auditoria", "Visualizações", "Painel"
])

# Conteúdo da aba Painel
with aba_painel:
    st.subheader("📊 Painel Fiscal Inteligente")

    opcao = st.radio(
        "Escolha o que deseja visualizar:",
        [
            "Gráfico",
            "Tabela",
            "Resumo",
            "📊 Métrica CFOP",
            "📁 Métrica SPED",
            "🧠 Insights Inteligentes",
            "🔧 Sugestões de Correção",
            "📥 Exportar Alertas"
        ],
        key="visualizacao_1"
    )

    if arquivo:
        df = pd.read_csv(arquivo, sep=';')
        # ... restante do painel fiscal