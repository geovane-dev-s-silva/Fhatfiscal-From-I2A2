import pandas as pd
import re

def gerar_alertas(df):
    alertas = []
    if df.isnull().sum().sum() > 0:
        alertas.append("⚠️ Existem campos vazios no arquivo. Isso pode comprometer a análise fiscal.")
    if len(df) < 10:
        alertas.append("⚠️ O arquivo possui poucos registros. Pode não representar o período completo.")
    return alertas

def gerar_metrica_cfop(df):
    col_cfop = next((col for col in df.columns if 'cfop' in col.lower()), None)
    if col_cfop:
        cfop_counts = df[col_cfop].astype(str).value_counts().reset_index()
        cfop_counts.columns = ['CFOP', 'Quantidade']
        return cfop_counts
    return pd.DataFrame()

def gerar_metrica_sped(df):
    col_sped = next((col for col in df.columns if 'sped' in col.lower()), None)
    if col_sped:
        vinculados = df[col_sped].notnull().sum()
        desvinculados = df[col_sped].isnull().sum()
        return pd.DataFrame({
            'Status': ['Vinculado', 'Não Vinculado'],
            'Quantidade': [vinculados, desvinculados]
        })
    return pd.DataFrame()

def analise_inteligente(df):
    insights = []
    col_valor = next((col for col in df.columns if 'valor' in col.lower()), None)
    col_cfop = next((col for col in df.columns if 'cfop' in col.lower()), None)
    col_sped = next((col for col in df.columns if 'sped' in col.lower()), None)

    def limpar_valor(valor):
        if pd.isna(valor):
            return 0.0
        valor_str = str(valor)
        valor_str = re.sub(r'[^\d,.-]', '', valor_str)
        valor_str = valor_str.replace(',', '.')
        try:
            return float(valor_str)
        except:
            return 0.0

    if col_valor:
        total = df[col_valor].apply(limpar_valor).sum()
        insights.append(f"💰 O valor total movimentado no período é de aproximadamente R$ {total:,.2f}.")

    if col_cfop:
        cfop_counts = df[col_cfop].astype(str).value_counts()
        top_cfop = cfop_counts.idxmax()
        top_count = cfop_counts.max()
        insights.append(f"📦 O CFOP mais utilizado é {top_cfop}, com {top_count} ocorrências.")
        if any(cfop_counts.index.str.len() != 4):
            insights.append("⚠️ Foram encontrados CFOPs com estrutura inválida (diferente de 4 dígitos).")

    if col_sped:
        vinculados = df[col_sped].notnull().sum()
        total_registros = len(df)
        percentual = (vinculados / total_registros) * 100
        insights.append(f"📁 Cerca de {percentual:.1f}% dos registros estão vinculados ao SPED Fiscal.")
        if percentual < 50:
            insights.append("⚠️ Menos da metade dos registros estão vinculados ao SPED. Isso pode indicar risco de inconsistência fiscal.")

    if not insights:
        insights.append("ℹ️ Nenhum padrão fiscal relevante foi detectado no arquivo enviado.")

    return insights

def sugerir_correcao(df):
    sugestoes = []
    col_cfop = next((col for col in df.columns if 'cfop' in col.lower()), None)
    col_valor = next((col for col in df.columns if 'valor' in col.lower()), None)
    col_sped = next((col for col in df.columns if 'sped' in col.lower()), None)

    if col_cfop:
        cfop_counts = df[col_cfop].astype(str).value_counts()
        cfops_invalidos = [cfop for cfop in cfop_counts.index if len(cfop) != 4]
        if cfops_invalidos:
            sugestoes.append("🔧 Alguns CFOPs têm estrutura inválida. Recomenda-se revisar os códigos: " + ", ".join(cfops_invalidos))

    if col_valor:
        valores_nulos = df[col_valor].isnull().sum()
        if valores_nulos > 0:
            sugestoes.append(f"🔧 Existem {valores_nulos} registros sem valor total. Isso pode comprometer a apuração de impostos.")

    if col_sped:
        desvinculados = df[col_sped].isnull().sum()
        if desvinculados > 0:
            sugestoes.append(f"🔧 Existem {desvinculados} registros sem vínculo com o SPED. Recomenda-se revisar esses lançamentos.")

    if not sugestoes:
        sugestoes.append("✅ Nenhuma sugestão de correção fiscal foi gerada.")

    return sugestoes