import pandas as pd
import logging

logger = logging.getLogger(__name__)


def analisar_qualidade_dados(df):
    """Analisa a qualidade dos dados e retorna um relatório estruturado."""
    if df is None or df.empty:
        return None
    
    analise = {
        "total_linhas": len(df),
        "total_colunas": len(df.columns),
        "duplicatas": df.duplicated().sum(),
        "campos_nulos": df.isnull().sum().to_dict(),
        "problemas": [],
        "avisos": [],
        "dicas_fiscais": [],
        "explicacoes_null": []
    }
    
    if len(df) == 0:
        analise["problemas"].append("Nenhuma linha de dados")
    
    if df.duplicated().sum() > 0:
        pct = (df.duplicated().sum() / len(df)) * 100
        analise["problemas"].append(f"⚠️ {df.duplicated().sum()} linhas duplicadas ({pct:.1f}%)")
    
    # Linhas completamente vazias (NULL ou strings vazias)
    def linha_vazia(row):
        """Verifica se uma linha está vazia (None, NaN ou string vazia)."""
        return all(pd.isna(v) or (isinstance(v, str) and v.strip() == '') for v in row)
    
    linhas_vazias_mask = df.apply(linha_vazia, axis=1)
    linhas_vazias = linhas_vazias_mask.sum()
    
    logger.info(f"DEBUG: Linhas vazias: {linhas_vazias}")
    
    if linhas_vazias > 0:
        indices = df[linhas_vazias_mask].index.tolist()
        analise["explicacoes_null"].append(
            f"\n📋 **{linhas_vazias} linha(s) completamente vazia(s)** (índices: {indices})\n"
            f"   • Ocorre ao carregar XMLs de diferentes formatos (NFe + NFSe)\n"
            f"   • Cada tipo tem campos específicos que não existem no outro\n"
            f"   • Exemplo: NFe tem 'ide_*', 'emit_*' / NFSe tem 'prestador_*', 'nfse_*'\n"
            f"   • ✅ NORMAL ao consolidar diferentes tipos de notas fiscais\n"
        )
    
    # Detecta tipo de documento
    has_nfse = any('nfse' in c.lower() or 'prestador' in c.lower() for c in df.columns)
    has_nfe = any('ide_' in c.lower() or 'emit_' in c.lower() for c in df.columns)
    
    if has_nfse and has_nfe:
        tipo_doc = 'MISTO (NFe + NFSe)'
    elif has_nfse:
        tipo_doc = 'NFSe'
    elif has_nfe:
        tipo_doc = 'NFe'
    else:
        tipo_doc = None
    
    logger.info(f"DEBUG: Tipo: {tipo_doc}")
    
    colunas_com_nulos = df.columns[df.isnull().any()].tolist()
    logger.info(f"DEBUG: {len(colunas_com_nulos)} colunas com null")
    
    if colunas_com_nulos and tipo_doc:
        analise["explicacoes_null"].append(f"\n💡 **EXPLICAÇÃO CAMPOS VAZIOS ({tipo_doc}):**\n")
        
        explicacoes = {
            'MISTO (NFe + NFSe)': {
                'prestador_': '✓ "prestador_*" vazio: pertence só a NFSe',
                'ide_': '✓ "ide_*" vazio: pertence só a NFe',
                'emit_': '✓ "emit_*" vazio: pertence só a NFe',
                'dest_': '✓ "dest_*" vazio: pertence só a NFe',
                'tomador_': '✓ "tomador_*" vazio: pertence só a NFSe',
                'nfse_': '✓ "nfse_*" vazio: pertence só a NFSe',
                'icms': '✓ ICMS vazio em NFSe: serviço não paga ICMS',
                'cfop': '✓ CFOP vazio em NFSe: só para mercadorias',
                'cst': '✓ CST vazio em NFSe: específico de ICMS',
                'total_': '✓ "total_*" vazio em NFSe: estrutura de NFe',
            },
            'NFSe': {
                'ide_': '✓ "ide_*" vazio: estrutura exclusiva de NFe',
                'emit_': '✓ "emit_*" vazio: NFSe usa "prestador_*"',
                'dest_': '✓ "dest_*" vazio: NFSe usa "tomador_*"',
                'icms': '✓ ICMS vazio: serviços não pagam ICMS',
                'cfop': '✓ CFOP vazio: só para circulação de mercadorias',
            },
            'NFe': {
                'nfse_': '✓ "nfse_*" vazio: estrutura exclusiva de NFSe',
                'prestador_': '✓ "prestador_*" vazio: NFe usa "emit_*"',
                'tomador_': '✓ "tomador_*" vazio: NFe usa "dest_*"',
                'iss': '✓ ISS vazio: produtos pagam ICMS, não ISS',
            }
        }
        
        for col in colunas_com_nulos[:20]:
            count = df[col].isnull().sum()
            pct = (count / len(df)) * 100
            
            if tipo_doc in explicacoes:
                for padrao, exp in explicacoes[tipo_doc].items():
                    if padrao.lower() in col.lower():
                        analise["explicacoes_null"].append(f"   • {col} ({count}, {pct:.0f}%): {exp}")
                        break
    
    # Resumo
    nulos_totais = df.isnull().sum().sum()
    if nulos_totais > 0:
        analise["avisos"].append(f"ℹ️ Total: {nulos_totais} campos vazios - veja explicação abaixo")
    
    # Validações fiscais BRASIL 2025
    for col in df.columns:
        if 'cfop' in col.lower():
            try:
                cfops = pd.to_numeric(df[col], errors='coerce').dropna()
                if len(cfops) > 0:
                    ext = [c for c in cfops.unique() if str(int(c)).startswith('6')]
                    if ext:
                        analise["dicas_fiscais"].append(f"📦 **CFOP 6xxx**: Operação interestadual detectada")
            except:
                pass
        
        if 'cst' in col.lower():
            try:
                csts = df[col].dropna().unique()
                if any(str(c) in ['40','41'] for c in csts):
                    analise["dicas_fiscais"].append(f"🆓 **CST 40/41**: Operação não tributada")
            except:
                pass
        
        if 'issretido' in col.lower():
            try:
                retidos = df[col].dropna().unique()
                if '2' in [str(r) for r in retidos]:
                    analise["dicas_fiscais"].append(f"💰 **ISS Retido**: Retenção na fonte detectada")
            except:
                pass
    
    # Reforma Tributária 2026
    if has_nfe:
        analise["dicas_fiscais"].append(
            f"🔔 **Reforma Tributária 2026**: Campos IBS, CBS e IS serão obrigatórios a partir de janeiro/2026"
        )
    
    logger.info(f"DEBUG: {len(analise['explicacoes_null'])} explicações geradas")
    return analise


def formatar_relatorio_qualidade(analise):
    """Formata a análise em texto legível."""
    if not analise:
        return ""
    
    logger.info(f"DEBUG formatar: {len(analise.get('explicacoes_null',[]))} explicações")
    
    relatorio = f"""
📊 ANÁLISE DE QUALIDADE DOS DADOS
─────────────────────────────────
Total: {analise['total_linhas']} linhas | {analise['total_colunas']} colunas
Duplicatas: {analise['duplicatas']} linhas
Campos vazios: {sum(1 for v in analise['campos_nulos'].values() if v > 0)} colunas afetadas


"""
    
    if analise["avisos"]:
        relatorio += "⚠️ AVISOS:\n"
        for aviso in analise["avisos"]:
            relatorio += f"  {aviso}\n"
        relatorio += "\n"
    
    if analise.get("explicacoes_null"):
        logger.info("DEBUG: Adicionando explicações")
        for exp in analise["explicacoes_null"]:
            relatorio += f"{exp}\n"
        relatorio += "\n"
    
    return relatorio


def gerar_dica_corujito_inteligente(df, contexto_empresa="", historico=None):
    """Análise fiscal completa com validações automáticas + LLM."""
    if df is None or df.empty:
        return "⚠️ Nenhum dado fornecido."
    
    logger.info("DEBUG: Iniciando Corujito")
    
    analise_qualidade = analisar_qualidade_dados(df)
    relatorio = formatar_relatorio_qualidade(analise_qualidade)
    
    if analise_qualidade["problemas"]:
        return relatorio + "\n⚠️ Resolva os problemas acima."
    
    from llm_utils import gerar_resposta_llm
    
    colunas = ", ".join(df.columns.tolist()[:30])
    amostra = df.head(3).to_dict(orient="records")
    
    insights = "\n".join(analise_qualidade["dicas_fiscais"]) if analise_qualidade["dicas_fiscais"] else "Nenhum."
    
    prompt = f"""
Especialista fiscal brasileiro com conhecimento profundo sobre NFe, NFSe, ICMS, ISS e legislação 2025-2026.

DADOS: {len(df)} registros
Colunas: {colunas}

Amostra: {str(amostra)[:1200]}

INSIGHTS DETECTADOS: {insights}

Gere análise fiscal COMPLEMENTAR (máximo 3 pontos):
1. Identifique padrões ou anomalias fiscais não detectados automaticamente
2. Sugira ações preventivas ou corretivas específicas
3. Destaque oportunidades de economia tributária ou compliance

Seja objetivo, técnico e cite valores/campos específicos.
"""
    
    try:
        resposta_llm = gerar_resposta_llm(pergunta=prompt, df=df, contexto_pdf=None, historico=historico)
        
        if analise_qualidade["dicas_fiscais"]:
            resultado = relatorio + "\n📌 INSIGHTS FISCAIS:\n"
            for i, dica in enumerate(analise_qualidade["dicas_fiscais"], 1):
                resultado += f"{i}. {dica}\n"
            resultado += f"\n🧠 ANÁLISE INTELIGENTE (LLM):\n{resposta_llm or 'Indisponível'}"
        else:
            resultado = relatorio + f"\n🧠 ANÁLISE INTELIGENTE (LLM):\n{resposta_llm or 'Indisponível'}"
        
        return resultado
    except Exception as e:
        logger.error(f"Erro LLM: {e}")
        return relatorio + "\n⚠️ Análise LLM indisponível."


def gerar_dica_rapida(df):
    """Versão rápida sem LLM."""
    analise = analisar_qualidade_dados(df)
    return formatar_relatorio_qualidade(analise)
