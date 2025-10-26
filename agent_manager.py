# agent_manager.py - VERSÃO COM MEMÓRIA INTELIGENTE INTEGRADA

import os
import sys
import pandas as pd
import logging
import tempfile
import PyPDF2
import streamlit as st
from datetime import datetime
from typing import List, Dict

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from file_reader import FileReader
from llm_utils import gerar_resposta_llm as llm_resposta
# ✅ CORREÇÃO: Importa AMBAS as classes
from memory_module import MemoriaInteligente, MemoriaCompartilhada

# ══════════════════════════════════════════════════════════════
# ✅ CORREÇÃO 1: CONFIGURAÇÃO DE LOGGING COM UTF-8 PARA WINDOWS
# ══════════════════════════════════════════════════════════════

# Força UTF-8 no ambiente Python (Windows)
if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'

# Configuração do logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Remove handlers existentes para evitar duplicação
if logger.hasHandlers():
    logger.handlers.clear()

# Handler para console com UTF-8
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Tenta configurar UTF-8 (Python 3.7+)
try:
    console_handler.stream.reconfigure(encoding='utf-8')
except AttributeError:
    # Fallback para versões antigas - não faz nada
    pass

# Formatador
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# ══════════════════════════════════════════════════════════════
# CLASSE AgentManager
# ══════════════════════════════════════════════════════════════

class AgentManager:
    def __init__(self):
        self.persist_directory = "vectorstore"
        os.makedirs(self.persist_directory, exist_ok=True)

        # ✅ CORREÇÃO 2: ESPECIFICA DISPOSITIVO CPU EXPLICITAMENTE
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': False}
            )
            logger.info("Embeddings carregados com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar embeddings: {e}")
            raise

        self.vetorstore_list = []
        self.arquivos_processados = set()
        
        # INICIALIZA MEMÓRIAS
        try:
            self.memoria_inteligente = MemoriaInteligente(persist_dir="memoria_chatfiscal")
            self.memoria_compartilhada = MemoriaCompartilhada()
            logger.info("Memoria Inteligente inicializada")
        except Exception as e:
            logger.warning(f"Erro ao inicializar memoria: {e}")
            self.memoria_inteligente = None
            self.memoria_compartilhada = None
        
        logger.info("AgentManager inicializado com memoria inteligente")

    def carregar_arquivo(self, arquivo):
        """Carrega arquivo CSV, XML ou PDF"""
        nome = arquivo.name.lower()
        logger.info(f"Carregando arquivo: {nome}")

        try:
            if nome.endswith(".csv"):
                df = FileReader.carregar_csv(arquivo)
                return self._processar_df(df, nome)

            elif nome.endswith(".xml"):
                df = FileReader.carregar_xml(arquivo)
                return self._processar_df(df, nome)

            elif nome.endswith(".pdf"):
                return self._processar_arquivo_pdf(arquivo)

            else:
                return "Formato nao suportado (apenas CSV, XML, PDF)"

        except Exception as e:
            logger.error(f"Erro ao carregar arquivo {nome}: {e}")
            return f"Erro ao carregar arquivo: {e}"

    def _processar_df(self, df, nome):
        """Processa DataFrame e sincroniza com session state"""
        if df is None or df.empty:
            logger.warning(f"Arquivo {nome} vazio ou invalido")
            return None
        
        if nome in self.arquivos_processados:
            logger.warning(f"Arquivo {nome} ja foi processado. Ignorando")
            return df
        
        self.arquivos_processados.add(nome)
        
        if "dados_tabulares" not in st.session_state:
            st.session_state["dados_tabulares"] = []
        
        if len(self.arquivos_processados) == 1:
            st.session_state["dados_tabulares"] = []
        
        st.session_state["dados_tabulares"].append(df)
        
        if len(st.session_state["dados_tabulares"]) > 0:
            df_final = pd.concat(st.session_state["dados_tabulares"], ignore_index=True)
            df_final = df_final.drop_duplicates().reset_index(drop=True)
            st.session_state["df_csv_unificado"] = df_final
        
        # SALVA NA MEMÓRIA COMPARTILHADA
        if self.memoria_compartilhada:
            self.memoria_compartilhada.salvar(f"arquivo_{nome}", {
                "nome": nome,
                "tipo": "CSV/XML",
                "registros": len(df),
                "colunas": df.columns.tolist(),
                "timestamp": datetime.now().isoformat()
            })
        
        logger.info(f"'{nome}' adicionado com {len(df)} linhas. Total: {len(st.session_state['df_csv_unificado'])} linhas unicas")
        return df

    def _processar_arquivo_pdf(self, arquivo):
        """Processa PDF e indexa com FAISS"""
        logger.info(f"Processando PDF: {arquivo.name}")
        temp_path = None
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                temp_pdf.write(arquivo.read())
                temp_path = temp_pdf.name

            docs = []
            try:
                loader = PyPDFLoader(temp_path)
                docs = loader.load()
                logger.info(f"PDF carregado: {len(docs)} paginas")
            except Exception as e:
                logger.warning(f"PyPDFLoader falhou, tentando PyPDF2: {e}")
                
                try:
                    pdf_reader = PyPDF2.PdfReader(temp_path)
                    for i, page in enumerate(pdf_reader.pages):
                        texto = page.extract_text()
                        if texto.strip():
                            docs.append(
                                Document(
                                    page_content=texto,
                                    metadata={"page": i + 1, "arquivo": arquivo.name}
                                )
                            )
                    logger.info(f"PDF carregado com PyPDF2: {len(docs)} paginas")
                except Exception as e2:
                    logger.error(f"Erro com PyPDF2: {e2}")
                    return f"Nao foi possivel ler o PDF {arquivo.name}"

            if not docs:
                logger.warning(f"PDF sem conteudo textual: {arquivo.name}")
                return f"PDF '{arquivo.name}' nao contem texto extraivel"

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", " ", ""]
            )
            chunks = splitter.split_documents(docs)
            
            if not chunks:
                logger.warning(f"Nenhum chunk extraido: {arquivo.name}")
                return f"Nenhum conteudo pode ser indexado em '{arquivo.name}'"

            faiss_index = FAISS.from_documents(chunks, self.embeddings)
            self.vetorstore_list.append(faiss_index)

            if "pdf_list" not in st.session_state:
                st.session_state["pdf_list"] = []
            if "pdf_metadata" not in st.session_state:
                st.session_state["pdf_metadata"] = []
            if "texto_pdf_list" not in st.session_state:
                st.session_state["texto_pdf_list"] = []

            st.session_state["pdf_list"].append(faiss_index)
            st.session_state["pdf_metadata"].append({
                "nome": arquivo.name,
                "chunks": len(chunks),
                "timestamp": datetime.now().isoformat(),
                "status": "indexado"
            })
            st.session_state["texto_pdf_list"].append({
                "nome": arquivo.name,
                "texto": "\n".join([c.page_content for c in chunks])
            })

            # SALVA NA MEMÓRIA COMPARTILHADA
            if self.memoria_compartilhada:
                self.memoria_compartilhada.salvar(f"arquivo_{arquivo.name}", {
                    "nome": arquivo.name,
                    "tipo": "PDF",
                    "chunks": len(chunks),
                    "timestamp": datetime.now().isoformat()
                })

            logger.info(f"PDF '{arquivo.name}' indexado com {len(chunks)} chunks")
            return f"PDF '{arquivo.name}' indexado com {len(chunks)} blocos"

        except Exception as e:
            logger.error(f"Erro ao processar PDF {arquivo.name}: {str(e)}")
            return f"Erro ao processar PDF: {str(e)}"

        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass

    def get_contexto_pdf(self):
        """Retorna o texto completo de todos os PDFs carregados"""
        texto_pdf_list = st.session_state.get("texto_pdf_list", [])
        if not texto_pdf_list:
            return None

        contexto = ""
        for item in texto_pdf_list:
            contexto += f"\n[{item['nome']}]\n{item['texto']}\n"
        
        return contexto if contexto.strip() else None

    def get_contexto_csv(self):
        """Retorna contexto dos dados CSV/XML carregados"""
        df = st.session_state.get("df_csv_unificado")
        if df is None or df.empty:
            return None
        
        contexto = f"Total de registros: {len(df)}\n"
        contexto += f"Colunas: {', '.join(df.columns)}\n"
        contexto += f"Amostra:\n{df.head(3).to_string()}"
        return contexto

    def debug_colunas_disponiveis(self):
        """Método de debug: mostra todas as colunas e seus tipos"""
        df = st.session_state.get("df_csv_unificado")
        
        if df is None or df.empty:
            return "Nenhum DataFrame"
        
        info = f"\n{'='*60}\n"
        info += f"ANALISE DE COLUNAS - Total: {len(df.columns)}\n"
        info += f"{'='*60}\n\n"
        
        for col in df.columns:
            dtype = df[col].dtype
            non_null = df[col].notna().sum()
            sample = str(df[col].iloc[0])[:50] if len(df) > 0 else "N/A"
            
            info += f"{col}\n"
            info += f"   Tipo: {dtype} | Nao-nulos: {non_null}/{len(df)} | Sample: {sample}\n\n"
        
        logger.info(info)
        return info

    def calcular_soma_valores(self):
        """
        Calcula soma total de TODOS os valores (CSV + XML).
        VERSÃO FINAL - Evita duplicação escolhendo APENAS UMA coluna por registro
        """
        df = st.session_state.get("df_csv_unificado")
        
        if df is None or df.empty:
            logger.warning("Nenhum DataFrame carregado")
            return None
        
        # PRIORIDADE - Define ordem de preferência (evita duplicação)
        prioridade = [
            'valor',                    # CSV genérico (máxima prioridade)
            'total_vnf',                # NF-e - Valor total oficial
            'nfse_valorliquidonfse',    # NFS-e - Valor líquido
            'nfse_valorservicos',       # NFS-e - Valor dos serviços
            'total_vprod',              # NF-e - Total de produtos
            'servico_valorservicos',    # NFS-e alternativo
            'item_vprod',               # NF-e - Produtos por item
        ]
        
        # Colunas que NÃO são valores principais (impostos/taxas/controle)
        colunas_ignorar = [
            'aliquota', 'percentual', 'taxa',
            'vicms', 'vipi', 'vpis', 'vcofins', 'vbc', 'vbcst', 'vtottrib',
            'valoriss', 'valorir', 'valorcsll', 'valorinss',
            'quantidade', 'qtd', 'numero', 'id', 'data', 'cnpj', 'cpf',
            'codigo', 'ncm', 'endereco', 'nome', 'razao'
        ]
        
        soma_total = 0
        valores_encontrados = {}
        
        logger.info(f"Analisando {len(df)} registros com {len(df.columns)} colunas")
        
        # Para cada linha, escolhe APENAS UMA coluna de valor (sem duplicação)
        for idx, row in df.iterrows():
            melhor_coluna = None
            melhor_valor = 0
            melhor_prioridade = 999
            
            for coluna in df.columns:
                coluna_lower = coluna.lower()
                
                # Ignora colunas de controle/impostos
                if any(termo in coluna_lower for termo in colunas_ignorar):
                    continue
                
                # Verifica se é coluna de valor
                eh_valor = any(termo in coluna_lower for termo in [
                    'valor', 'vtotal', 'vnf', 'vprod', 'price', 'amount'
                ])
                
                if not eh_valor:
                    continue
                
                try:
                    # Converte valor
                    val_str = str(row[coluna]).replace(',', '.')
                    val = pd.to_numeric(val_str, errors='coerce')
                    
                    if pd.isna(val) or val == 0:
                        continue
                    
                    # Verifica prioridade
                    prioridade_atual = 999
                    for i, col_prior in enumerate(prioridade):
                        if col_prior in coluna_lower:
                            prioridade_atual = i
                            break
                    
                    # Escolhe coluna com MAIOR prioridade (menor índice)
                    if prioridade_atual < melhor_prioridade:
                        melhor_prioridade = prioridade_atual
                        melhor_coluna = coluna
                        melhor_valor = val
                    elif prioridade_atual == melhor_prioridade and val > melhor_valor:
                        # Mesma prioridade: escolhe maior valor
                        melhor_coluna = coluna
                        melhor_valor = val
                
                except Exception as e:
                    logger.debug(f"Erro ao processar {coluna}: {e}")
                    continue
            
            # Adiciona valor escolhido
            if melhor_coluna and melhor_valor > 0:
                if melhor_coluna not in valores_encontrados:
                    valores_encontrados[melhor_coluna] = []
                valores_encontrados[melhor_coluna].append(melhor_valor)
                logger.debug(f"Registro {idx}: {melhor_coluna} = R$ {melhor_valor:.2f}")
        
        # Consolida resultados
        detalhes = []
        for coluna, valores in valores_encontrados.items():
            soma_coluna = sum(valores)
            soma_total += soma_coluna
            
            detalhes.append({
                'coluna': coluna,
                'soma': soma_coluna,
                'registros': len(valores),
                'media': soma_coluna / len(valores) if len(valores) > 0 else 0,
                'minimo': min(valores),
                'maximo': max(valores)
            })
            
            logger.info(f"'{coluna}': R$ {soma_coluna:,.2f} ({len(valores)} registros)")
        
        if not detalhes:
            logger.warning("Nenhum valor encontrado")
            return None
        
        # Ordena por soma (maior primeiro)
        detalhes.sort(key=lambda x: x['soma'], reverse=True)
        
        logger.info(f"SOMA TOTAL SEM DUPLICACAO: R$ {soma_total:,.2f}")
        
        return {
            'soma_total': soma_total,
            'detalhes': detalhes,
            'total_registros': len(df),
            'total_colunas_valor': len(detalhes)
        }

    def contar_notas_fiscais(self):
        """Retorna contagem exata de notas fiscais"""
        df = st.session_state.get("df_csv_unificado")
        if df is None or df.empty:
            return {
                'total': 0,
                'nfe': 0,
                'nfse': 0,
                'tipo': 'Nenhum'
            }
        
        total = len(df)
        
        tem_nfe = any(col.startswith(('emit_', 'dest_', 'ide_')) or 'cfop' in col.lower() for col in df.columns)
        tem_nfse = any(col.startswith(('prestador_', 'tomador_', 'nfse_')) or 'iss' in col.lower() for col in df.columns)
        
        nfe_count = 0
        nfse_count = 0
        
        if tem_nfe and tem_nfse:
            nfe_count = df[df.apply(lambda row: any(pd.notna(row[col]) for col in df.columns if 'emit_' in col or col == 'cfop'), axis=1)].shape[0]
            nfse_count = df[df.apply(lambda row: any(pd.notna(row[col]) for col in df.columns if 'prestador_' in col or 'nfse_' in col), axis=1)].shape[0]
            tipo = 'MISTO'
        elif tem_nfe:
            nfe_count = total
            tipo = 'NFe'
        elif tem_nfse:
            nfse_count = total
            tipo = 'NFSe'
        else:
            tipo = 'Desconhecido'
        
        return {
            'total': total,
            'nfe': nfe_count,
            'nfse': nfse_count,
            'tipo': tipo
        }

    def gerar_resposta(self, pergunta):
        """
        Gera resposta com base no tipo de pergunta
        AGORA COM MEMÓRIA INTELIGENTE INTEGRADA
        """
        logger.info(f"Pergunta: {pergunta[:60]}")
        
        df = st.session_state.get("df_csv_unificado")
        pdf_list = st.session_state.get("pdf_list", [])
        
        # BUSCA CONTEXTO RELEVANTE NA MEMÓRIA
        contexto_memoria = ""
        if self.memoria_inteligente:
            try:
                contexto_memoria = self.memoria_inteligente.buscar_contexto_relevante(pergunta, k=3)
                if contexto_memoria:
                    logger.info("Contexto relevante recuperado da memoria")
            except Exception as e:
                logger.warning(f"Erro ao buscar memoria: {e}")
        
        pergunta_lower = pergunta.lower()
        
        # Verificação de soma
        termos_soma = [
            'soma', 'total', 'somar', 'quanto é', 'valor total',
            'soma dos valores', 'some', 'calcular', 'quanto dá',
            'somatório', 'consolidado', 'totalizar'
        ]
        
        if any(termo in pergunta_lower for termo in termos_soma):
            logger.info("Detectada pergunta sobre soma de valores")
            
            resultado = self.calcular_soma_valores()
            
            if resultado is None:
                resposta = "Nenhum dado com valores numéricos foi encontrado nos arquivos carregados."
            else:
                soma_total = resultado['soma_total']
                detalhes = resultado['detalhes']
                total_registros = resultado['total_registros']
                total_colunas = resultado['total_colunas_valor']
                
                resposta = f"**Soma total consolidada (CSV + XML): R$ {soma_total:,.2f}**\n\n"
                resposta += f"**Detalhamento ({total_colunas} coluna(s) com valores):**\n\n"
                
                for i, item in enumerate(detalhes, 1):
                    resposta += f"**{i}. {item['coluna']}**\n"
                    resposta += f"   Soma: R$ {item['soma']:,.2f}\n"
                    resposta += f"   Media: R$ {item['media']:,.2f}\n"
                    resposta += f"   Registros: {item['registros']}\n"
                    resposta += f"   Range: R$ {item['minimo']:,.2f} a R$ {item['maximo']:,.2f}\n\n"
                
                resposta += f"**Total de registros processados: {total_registros}**"
            
            # SALVA NA MEMÓRIA
            if self.memoria_inteligente:
                self.memoria_inteligente.salvar_contexto(
                    pergunta=pergunta,
                    resposta=resposta,
                    metadados_extras={"tipo": "calculo_soma"}
                )
            
            return resposta
        
        # Verificação de quantidade de notas
        termos_quantidade = [
            'quantas notas', 'quantos registros', 'total de notas',
            'número de notas', 'quantidade de notas', 'há notas',
            'foram carregadas'
        ]

        if any(termo in pergunta_lower for termo in termos_quantidade):
            contagem = self.contar_notas_fiscais()
            
            if contagem['total'] == 0:
                resposta = "Nenhuma nota fiscal foi carregada ainda."
            else:
                if contagem['total'] == 1:
                    resposta = f"**1 nota fiscal** foi carregada.\n\n"
                else:
                    resposta = f"**{contagem['total']} notas fiscais** foram carregadas.\n\n"
                
                if contagem['tipo'] == 'MISTO':
                    resposta += f"**Distribuicao:**\n"
                    resposta += f"- **NF-e:** {contagem['nfe']} nota(s)\n"
                    resposta += f"- **NFS-e:** {contagem['nfse']} nota(s)"
                elif contagem['tipo'] == 'NFe':
                    resposta += f"Sao **NF-e** (Notas Fiscais Eletronicas)"
                elif contagem['tipo'] == 'NFSe':
                    resposta += f"Sao **NFS-e** (Notas Fiscais de Servico)"
            
            # SALVA NA MEMÓRIA
            if self.memoria_inteligente:
                self.memoria_inteligente.salvar_contexto(
                    pergunta=pergunta,
                    resposta=resposta,
                    metadados_extras={"tipo": "contagem_notas"}
                )
            
            return resposta
        
        tipo_pergunta = self._detectar_tipo_pergunta(pergunta)
        
        # Gera resposta
        if tipo_pergunta == 'conjunta':
            resposta = self._responder_conjunta(pergunta, df, pdf_list, contexto_memoria)
        elif tipo_pergunta == 'pdf':
            resposta = self._responder_pdf(pergunta, pdf_list, contexto_memoria)
        elif tipo_pergunta == 'csv':
            resposta = self._responder_csv(pergunta, df, contexto_memoria)
        else:
            resposta = "Nenhum dado disponível."
        
        # SALVA NA MEMÓRIA AUTOMATICAMENTE
        if self.memoria_inteligente and resposta and not resposta.startswith("Nenhum"):
            try:
                self.memoria_inteligente.salvar_contexto(
                    pergunta=pergunta,
                    resposta=resposta,
                    metadados_extras={
                        "tipo_pergunta": tipo_pergunta,
                        "tem_csv": df is not None and not df.empty,
                        "tem_pdf": len(pdf_list) > 0
                    }
                )
                logger.info("Conversa salva na memoria inteligente")
            except Exception as e:
                logger.warning(f"Erro ao salvar na memoria: {e}")
        
        return resposta

    def _detectar_tipo_pergunta(self, pergunta: str) -> str:
        """Detecta o tipo de pergunta"""
        pergunta_lower = pergunta.lower()
        
        palavras_pdf_forte = ['documento', 'pdf', 'página', 'diz no', 'menciona no']
        palavras_csv_forte = ['tabela', 'coluna', 'dados', 'registro', 'csv', 'xml', 'emitente', 'valor', 'empresa']
        
        menciona_pdf = any(palavra in pergunta_lower for palavra in palavras_pdf_forte)
        menciona_csv = any(palavra in pergunta_lower for palavra in palavras_csv_forte)
        
        if menciona_pdf and not menciona_csv:
            return 'pdf'
        if menciona_csv and not menciona_pdf:
            return 'csv'
        if menciona_csv and menciona_pdf:
            return 'conjunta'
        
        df = st.session_state.get("df_csv_unificado")
        pdf_list = st.session_state.get("pdf_list", [])
        
        if df is not None and not df.empty and pdf_list:
            return 'csv'
        elif df is not None and not df.empty:
            return 'csv'
        elif pdf_list:
            return 'pdf'
        else:
            return 'nenhum'

    def _responder_conjunta(self, pergunta, df, pdf_list, contexto_memoria=""):
        """Responde com dados conjuntos + memória"""
        try:
            contexto = f"Total registros: {len(df)}\n"
            contexto += f"Amostra:\n{df.head(3).to_string()}\n\n"

            for i, vetorstore in enumerate(pdf_list):
                resultados = vetorstore.similarity_search(pergunta, k=3)
                if resultados:
                    contexto += f"\nPDF {i+1}:\n"
                    contexto += "\n".join([r.page_content for r in resultados])
            
            # Adiciona contexto da memória
            if contexto_memoria:
                contexto += f"\n\nCONTEXTO DE CONVERSAS ANTERIORES:\n{contexto_memoria}"

            return llm_resposta(pergunta, df=df, contexto_pdf=contexto)
        except Exception as e:
            return f"Erro: {str(e)}"

    def _responder_csv(self, pergunta, df, contexto_memoria=""):
        """Responde com dados CSV/XML + memória"""
        if df is None or df.empty:
            return "Nenhum dado tabular carregado."
        
        # Se há contexto da memória, adiciona como "contexto_pdf" (workaround)
        if contexto_memoria:
            contexto_extra = f"CONVERSAS ANTERIORES RELEVANTES:\n{contexto_memoria}"
            return llm_resposta(pergunta, df=df, contexto_pdf=contexto_extra)
        
        return llm_resposta(pergunta, df=df)

    def _responder_pdf(self, pergunta, pdf_list, contexto_memoria=""):
        """Responde com PDFs + memória"""
        if not pdf_list:
            return "Nenhum PDF carregado."
        
        pergunta_lower = pergunta.lower()
        
        palavras_produto = ['produto', 'item', 'mercadoria', 'caro', 'barato', 'tabela', 'mais', 'menos']
        eh_pergunta_produto = any(palavra in pergunta_lower for palavra in palavras_produto)
        
        contexto = ""
        
        if eh_pergunta_produto:
            logger.info("Detectada pergunta sobre produtos")
            for vetorstore in pdf_list:
                termos_busca = [
                    "DADOS DOS PRODUTOS SERVIÇOS",
                    "DESCRIÇÃO DOS PRODUTOS",
                    "VALOR UNIT",
                    "QUANTIDADE VALOR"
                ]
                
                for termo in termos_busca:
                    resultados = vetorstore.similarity_search(termo, k=5)
                    if resultados:
                        contexto += "\n".join([r.page_content for r in resultados])
                        contexto += "\n\n"
        
        for vetorstore in pdf_list:
            resultados = vetorstore.similarity_search(pergunta, k=5)
            if resultados:
                contexto += "\n".join([r.page_content for r in resultados])
        
        # Adiciona contexto da memória
        if contexto_memoria:
            contexto += f"\n\nCONTEXTO DE CONVERSAS ANTERIORES:\n{contexto_memoria}"

        return llm_resposta(pergunta, contexto_pdf=contexto)

    def limpar_todos_pdfs(self):
        """Limpa todos os PDFs e dados"""
        st.session_state["pdf_list"] = []
        st.session_state["pdf_metadata"] = []
        st.session_state["texto_pdf_list"] = []
        st.session_state["dados_tabulares"] = []
        st.session_state["df_csv_unificado"] = None
        self.vetorstore_list = []
        self.arquivos_processados = set()
        
        # LIMPA MEMÓRIA COMPARTILHADA (mas mantém memória inteligente persistente)
        if self.memoria_compartilhada:
            self.memoria_compartilhada.limpar()
        
        logger.info("Todos os dados foram limpos (memoria inteligente preservada)")
    
    # NOVOS MÉTODOS PARA GERENCIAR MEMÓRIA
    
    def obter_estatisticas_memoria(self):
        """Retorna estatísticas da memória inteligente"""
        if not self.memoria_inteligente:
            return None
        return self.memoria_inteligente.estatisticas()
    
    def obter_historico_conversas(self, ultimos_n=10):
        """Retorna histórico formatado das últimas conversas"""
        if not self.memoria_inteligente:
            return "Memoria inteligente nao disponivel"
        return self.memoria_inteligente.obter_historico_formatado(ultimos_n)
    
    def limpar_memoria_inteligente(self):
        """Limpa completamente a memória inteligente (inclusive disco)"""
        if self.memoria_inteligente:
            self.memoria_inteligente.limpar(limpar_disco=True)
            logger.info("Memoria inteligente completamente limpa")
