# llm_utils.py - VERSÃO COM MEMÓRIA INTELIGENTE INTEGRADA

import os
import pandas as pd
import logging
import re
from datetime import datetime
from typing import Optional, Tuple
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# ✨ IMPORTA MEMÓRIA INTELIGENTE
from memory_module import MemoriaInteligente

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chatfiscal.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LLMInteligente:
    """
    LLM com suporte a CSV, XML, PDF (individual e consolidado)
    🧠 AGORA COM MEMÓRIA INTELIGENTE INTEGRADA
    """

    def __init__(self):
        try:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("⚠️ GOOGLE_API_KEY ou GEMINI_API_KEY não encontrada")

            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=api_key,
                temperature=0.3
            )
            
            # ✨ INICIALIZA MEMÓRIA INTELIGENTE
            self.memoria = MemoriaInteligente(persist_dir="memoria_chatfiscal")
            logger.info("✅ LLM Gemini v2.0-flash + MemoriaInteligente inicializados")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar LLM: {e}")
            raise

    # ✅ ADICIONE ESTES MÉTODOS QUE ESTAVAM COM "..."
    
    def _criar_sistema_prompt(self, tipo_resposta):
        """Cria prompt do sistema baseado no tipo de resposta"""
        
        if tipo_resposta == "csv":
            return """Você é um analista fiscal especializado em notas fiscais eletrônicas.

IMPORTANTE: Responda APENAS o que foi perguntado de forma natural e direta.

Regras:
- Use APENAS os dados JSON fornecidos
- Responda de forma natural, sem mencionar "dados estruturados", "registros" ou "com base em"
- Cite valores específicos dos dados JSON quando relevante
- Use terminologia fiscal profissional quando apropriado
- Se um dado não está disponível no JSON, informe de forma clara e direta
- Seja conciso e objetivo
- NUNCA use tags HTML na resposta
- Responda em português brasileiro
- Para perguntas sobre prestador/tomador/emitente: use os campos correspondentes do JSON"""

        elif tipo_resposta == "pdf":
            return """Você é um especialista em análise de documentos fiscais.

Regras:
- Responda com base APENAS no documento fornecido
- Não mencione "no documento" ou "segundo o PDF" - responda diretamente
- Cite páginas apenas se for relevante para localização
- Se a informação não está disponível, informe claramente
- Use linguagem técnica mas natural
- NUNCA use tags HTML na resposta
- Responda em português brasileiro"""

        elif tipo_resposta == "consolidada":
            return """Você é um analista fiscal avançado com acesso a múltiplas fontes.

Regras:
- Cruze informações entre registros eletrônicos e documentos quando relevante
- Responda de forma natural, sem mencionar explicitamente as fontes em cada frase
- Cite a origem apenas se houver discrepância ou for essencial
- Use terminologia fiscal profissional
- Seja conciso e direto
- NUNCA use tags HTML na resposta
- Responda em português brasileiro"""

        else:
            return "Você é um assistente fiscal profissional."

    def _formatar_nome_campo(self, campo):
        """Formata nome de campo técnico para apresentação profissional"""
        campo = campo.replace('prestador_', '').replace('tomador_', '').replace('emit_', '').replace('dest_', '')
        campo = campo.replace('ide_', '').replace('nfse_', '').replace('item_', '')
        campo = campo.replace('_', ' ')
        
        palavras_especiais = {
            'email': 'E-mail', 'telefone': 'Telefone', 'cnpj': 'CNPJ', 'cpf': 'CPF',
            'ie': 'IE', 'im': 'IM', 'cep': 'CEP', 'uf': 'UF', 'icms': 'ICMS',
            'iss': 'ISS', 'cfop': 'CFOP', 'cst': 'CST', 'csosn': 'CSOSN',
            'valor': 'Valor', 'total': 'Total', 'numero': 'Número', 'data': 'Data',
            'emissao': 'Emissão', 'contato': 'Contato', 'endereco': 'Endereço',
            'razao': 'Razão', 'social': 'Social', 'fantasia': 'Nome Fantasia',
            'codigo': 'Código', 'municipio': 'Município', 'complemento': 'Complemento',
            'bairro': 'Bairro', 'logradouro': 'Logradouro', 'nfe': 'NF-e',
            'nfse': 'NFS-e', 'pis': 'PIS', 'cofins': 'COFINS', 'ipi': 'IPI',
            'aliquota': 'Alíquota', 'base': 'Base', 'calculo': 'Cálculo',
            'produto': 'Produto', 'servico': 'Serviço', 'descricao': 'Descrição',
            'quantidade': 'Quantidade', 'unitario': 'Unitário'
        }
        
        palavras = campo.lower().split()
        palavras_formatadas = []
        
        for palavra in palavras:
            if palavra in palavras_especiais:
                palavras_formatadas.append(palavras_especiais[palavra])
            else:
                palavras_formatadas.append(palavra.capitalize())
        
        return ' '.join(palavras_formatadas)

    def _eh_saudacao_pura(self, pergunta):
        """
        Detecta se é APENAS uma saudação vazia.
        Retorna True apenas para saudações simples SEM pergunta.
        """
        saudacoes_simples = {
            'oi', 'olá', 'ola', 'hey', 'hi', 'e aí', 'e ai',
            'bom dia', 'boa tarde', 'boa noite', 'boa madrugada'
        }
        
        pergunta_lower = pergunta.lower().strip()
        
        if pergunta_lower in saudacoes_simples:
            return True
        
        if '?' in pergunta:
            return False
        
        if len(pergunta.split()) > 5:
            return False
        
        return False

    def gerar_resposta_llm(self, pergunta, df=None, contexto_pdf=None, historico=None):
        """
        Gera resposta baseado no que está disponível.
        🧠 AGORA COM BUSCA SEMÂNTICA AUTOMÁTICA
        """
        
        tem_csv = df is not None and not df.empty
        tem_pdf = contexto_pdf is not None and contexto_pdf.strip()
        
        if not tem_csv and not tem_pdf:
            return "❌ Nenhum dado disponível. Carregue um arquivo CSV/XML ou PDF para começar."
        
        if self._eh_saudacao_pura(pergunta):
            return """Olá! 👋 Sou o assistente fiscal do ChatFiscal.

**Estou pronto para analisar seus dados fiscais!**

Você pode me fazer perguntas como:
- Quantas notas fiscais foram carregadas?
- Qual é o valor total das operações?
- Quem é o emitente da NF-e?
- Qual a alíquota de ISS aplicada?
- Liste todos os prestadores de serviço
- Quais são os CFOPs utilizados?

**Como posso ajudar?**"""
        
        # ✨ BUSCA CONTEXTO RELEVANTE DA MEMÓRIA
        contexto_memoria = self.memoria.buscar_contexto_relevante(pergunta, k=3)
        
        if contexto_memoria:
            logger.info(f"🧠 Contexto relevante encontrado na memória")
            # Adiciona contexto da memória ao contexto PDF
            if contexto_pdf:
                contexto_pdf += f"\n\n📚 CONVERSAS ANTERIORES RELACIONADAS:\n{contexto_memoria}"
            else:
                contexto_pdf = f"📚 CONVERSAS ANTERIORES RELACIONADAS:\n{contexto_memoria}"
        
        if tem_csv and tem_pdf:
            tipo_resposta = "consolidada"
        elif tem_pdf:
            tipo_resposta = "pdf"
        else:
            tipo_resposta = "csv"

        logger.info(f"📋 Tipo de resposta: {tipo_resposta}")
        
        try:
            sistema_prompt = SystemMessagePromptTemplate.from_template(
                self._criar_sistema_prompt(tipo_resposta)
            )

            if tipo_resposta == "csv":
                resposta = self._responder_csv(pergunta, df, sistema_prompt)
            elif tipo_resposta == "pdf":
                resposta = self._responder_pdf(pergunta, contexto_pdf, sistema_prompt)
            elif tipo_resposta == "consolidada":
                resposta = self._responder_consolidado(pergunta, df, contexto_pdf, sistema_prompt)
            
            # ✨ SALVA CONVERSA NA MEMÓRIA AUTOMATICAMENTE
            self.memoria.salvar_contexto(
                pergunta=pergunta,
                resposta=resposta,
                metadados_extras={
                    "tipo_resposta": tipo_resposta,
                    "tem_csv": tem_csv,
                    "tem_pdf": tem_pdf
                }
            )
            logger.info("💾 Conversa salva na memória inteligente")
            
            return resposta

        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")
            return f"Erro ao processar pergunta: {str(e)}"

    # ✅ ADICIONE OS MÉTODOS _responder_*
    
    def _responder_csv(self, pergunta, df, sistema_prompt):
        """Responde usando APENAS dados estruturados - VERSÃO CORRIGIDA"""
        logger.info("📊 Modo: Dados Estruturados")
        
        try:
            tem_nfe = any(col.startswith('emit_') for col in df.columns)
            tem_nfse = any(col.startswith('prestador_') for col in df.columns)
            
            dados_json = df.head(50).to_json(orient='records', force_ascii=False, indent=2)
            
            total_registros = len(df)
            resumo_colunas = ", ".join(df.columns.tolist())
            
            colunas_valor = [col for col in df.columns if 'valor' in col.lower() or 'total' in col.lower()]
            estatisticas = ""
            if colunas_valor:
                for col in colunas_valor:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        try:
                            estatisticas += f"\n{col}: Soma={df[col].sum():.2f}, Média={df[col].mean():.2f}, Min={df[col].min():.2f}, Max={df[col].max():.2f}"
                        except:
                            pass
            
            contexto_estrutural = f"""
📊 ESTRUTURA DOS DADOS:
- Total de registros: {total_registros}
- Total de campos: {len(df.columns)}
"""
            
            if tem_nfe:
                contexto_estrutural += "🔵 **Contém NF-e (Nota Fiscal Eletrônica)**\n"
            
            if tem_nfse:
                contexto_estrutural += "🟣 **Contém NFS-e (Nota Fiscal de Serviço)**\n"
            
            template_usuario = """
{contexto_estrutural}

📋 COLUNAS DISPONÍVEIS:
{resumo_colunas}

📈 ESTATÍSTICAS:
{estatisticas}

📄 REGISTROS COMPLETOS (JSON):
{dados_json}

─────────────────────────
🔍 PERGUNTA DO USUÁRIO: {pergunta}

─────────────────────────
INSTRUÇÕES CRÍTICAS:
1. Use APENAS os dados JSON acima para responder
2. Cite valores EXATOS dos registros JSON
3. Se a pergunta menciona "prestador", "tomador", "emitente", "destinatário": busque nos campos correspondentes do JSON
4. Para perguntas sobre valores: use as estatísticas e dados JSON
5. Para perguntas sobre quantidade: use total_registros
6. Responda de forma direta e natural
7. NÃO invente dados - use apenas o que está no JSON
8. Se não encontrar no JSON, diga claramente que o dado não está disponível
"""
            
            human_prompt = HumanMessagePromptTemplate.from_template(template_usuario)
            chat_prompt = ChatPromptTemplate.from_messages([sistema_prompt, human_prompt])

            chain = (
                RunnablePassthrough.assign(
                    contexto_estrutural=lambda x: contexto_estrutural,
                    resumo_colunas=lambda x: resumo_colunas,
                    estatisticas=lambda x: estatisticas if estatisticas else "Nenhuma coluna numérica de valor encontrada",
                    dados_json=lambda x: dados_json,
                    pergunta=lambda x: x["pergunta"]
                )
                | chat_prompt
                | self.llm
                | StrOutputParser()
            )

            resposta = chain.invoke({"pergunta": pergunta})
            resposta = re.sub(r'<[^>]+>', '', resposta)
            resposta = resposta.strip()
            
            if not resposta or len(resposta) < 10:
                resposta = "Desculpe, não consegui processar sua pergunta com os dados disponíveis."
            
            logger.info("✅ Resposta gerada com sucesso")
            return resposta

        except Exception as e:
            logger.error(f"Erro ao responder: {e}")
            return f"Erro ao processar consulta: {str(e)}"

    def _responder_pdf(self, pergunta, contexto_pdf, sistema_prompt):
        """Responde usando APENAS documentos PDF"""
        logger.info("📄 Modo: PDF")
        
        try:
            template_usuario = """
📄 CONTEXTO DO DOCUMENTO PDF
─────────────────────────
{contexto_pdf}

─────────────────────────
PERGUNTA: {pergunta}

INSTRUÇÕES:
- Use APENAS as informações do documento acima
- Responda de forma direta
- Não mencione "segundo o PDF" ou "no documento"
- Se não encontrar, diga claramente
- Sem tags HTML
"""
            
            human_prompt = HumanMessagePromptTemplate.from_template(template_usuario)
            chat_prompt = ChatPromptTemplate.from_messages([sistema_prompt, human_prompt])

            chain = (
                RunnablePassthrough.assign(
                    contexto_pdf=lambda x: contexto_pdf,
                    pergunta=lambda x: x["pergunta"]
                )
                | chat_prompt
                | self.llm
                | StrOutputParser()
            )

            resposta = chain.invoke({"pergunta": pergunta})
            resposta = re.sub(r'<[^>]+>', '', resposta)
            resposta = resposta.strip()
            
            logger.info("✅ Resposta PDF gerada")
            return resposta

        except Exception as e:
            logger.error(f"Erro ao responder PDF: {e}")
            return f"Erro ao analisar documento: {str(e)}"

    def _responder_consolidado(self, pergunta, df, contexto_pdf, sistema_prompt):
        """Responde usando DADOS + PDFs juntos"""
        logger.info("🔀 Modo: Consolidado")
        
        try:
            tem_nfe = any(col.startswith('emit_') for col in df.columns)
            tem_nfse = any(col.startswith('prestador_') for col in df.columns)
            
            contexto_estrutural = f"Total de registros: {len(df)}\n"
            if tem_nfe:
                contexto_estrutural += "🔵 Contém NF-e\n"
            if tem_nfse:
                contexto_estrutural += "🟣 Contém NFS-e\n"
            
            colunas_originais = df.columns.tolist()
            colunas_formatadas = [self._formatar_nome_campo(col) for col in colunas_originais[:30]]
            
            dados_json = df.head(30).to_json(orient='records', force_ascii=False, indent=2)
            
            template_usuario = """
📊 REGISTROS FISCAIS ELETRÔNICOS
─────────────────────────
{contexto_estrutural}

Campos: {colunas}

Dados JSON:
{dados_json}

───────────────────────────
📄 DOCUMENTOS FISCAIS (PDF)
─────────────────────────
{contexto_pdf}

───────────────────────────
PERGUNTA: {pergunta}

INSTRUÇÕES:
- Analise ambas as fontes
- Responda de forma integrada
- Cite origem apenas se houver discrepância
- Sem tags HTML
"""
            
            human_prompt = HumanMessagePromptTemplate.from_template(template_usuario)
            chat_prompt = ChatPromptTemplate.from_messages([sistema_prompt, human_prompt])

            chain = (
                RunnablePassthrough.assign(
                    contexto_estrutural=lambda x: contexto_estrutural,
                    colunas=lambda x: ", ".join(colunas_formatadas),
                    dados_json=lambda x: dados_json,
                    contexto_pdf=lambda x: contexto_pdf[:1500],
                    pergunta=lambda x: x["pergunta"]
                )
                | chat_prompt
                | self.llm
                | StrOutputParser()
            )

            resposta = chain.invoke({"pergunta": pergunta})
            resposta = re.sub(r'<[^>]+>', '', resposta)
            resposta = resposta.strip()
            
            logger.info("✅ Resposta consolidada gerada")
            return resposta

        except Exception as e:
            logger.error(f"Erro ao responder consolidado: {e}")
            return f"Erro ao analisar dados consolidados: {str(e)}"


# ✨ INSTÂNCIA GLOBAL COM MEMÓRIA
try:
    llm_inteligente = LLMInteligente()
    logger.info("✅ Instância LLMInteligente criada com memória")
except Exception as e:
    logger.error(f"❌ Falha ao inicializar LLM: {e}")
    llm_inteligente = None


def gerar_resposta_llm(pergunta, df=None, contexto_pdf=None, historico=None):
    """
    Wrapper compatível - 🧠 AGORA COM MEMÓRIA AUTOMÁTICA
    O parâmetro 'historico' não é mais necessário (mantido por compatibilidade)
    """
    if llm_inteligente is None:
        return "Erro: LLM não foi inicializado"

    # O histórico agora é gerenciado automaticamente pela MemoriaInteligente
    return llm_inteligente.gerar_resposta_llm(pergunta, df, contexto_pdf)
