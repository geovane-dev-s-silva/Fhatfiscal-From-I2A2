# gerar_pdf.py - Gerador de Relatório de Auditoria em PDFpasar

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from datetime import datetime
import io
import pandas as pd


def gerar_relatorio_pdf(dados_sessao):
    """
    Gera relatório de auditoria fiscal em PDF
    
    Args:
        dados_sessao (dict): Dicionário com dados da sessão
            - dados_tabulares: list de DataFrames
            - arquivos_carregados: set de nomes de arquivos
            - past: list de perguntas
            - pdf_list: list de PDFs carregados
    
    Returns:
        bytes: Conteúdo do PDF em bytes
    """
    # Cria buffer para o PDF
    buffer = io.BytesIO()
    
    # Configuração do documento
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
    elementos = []
    styles = getSampleStyleSheet()
    
    # ===== TÍTULO =====
    titulo = Paragraph(
        "<b>RELATÓRIO DE AUDITORIA FISCAL</b>",
        styles['Title']
    )
    elementos.append(titulo)
    elementos.append(Spacer(1, 0.3*inch))
    
    # ===== CABEÇALHO =====
    cabecalho = Paragraph(
        f"<b>Sistema:</b> ChatFiscal - Análise Fiscal Automatizada<br/>"
        f"<b>Data/Hora:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        styles['Normal']
    )
    elementos.append(cabecalho)
    elementos.append(Spacer(1, 0.3*inch))
    
    # ===== 1. MÉTRICAS PRINCIPAIS =====
    elementos.append(Paragraph("<b>1. MÉTRICAS PRINCIPAIS</b>", styles['Heading2']))
    elementos.append(Spacer(1, 0.1*inch))
    
    metricas_data = [
        ['Métrica', 'Valor'],
        ['Arquivos Processados', str(len(dados_sessao.get("arquivos_carregados", set())))],
        ['Registros Fiscais', str(_calcular_total_registros(dados_sessao))],
        ['Consultas Realizadas', str(len(dados_sessao.get("past", [])))],
        ['PDFs Carregados', str(len(dados_sessao.get("pdf_list", [])))],
    ]
    
    tabela_metricas = Table(metricas_data, colWidths=[3.5*inch, 2*inch])
    tabela_metricas.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elementos.append(tabela_metricas)
    elementos.append(Spacer(1, 0.4*inch))
    
    # ===== 2. ANÁLISE DE QUALIDADE =====
    if dados_sessao.get("dados_tabulares"):
        elementos.append(Paragraph("<b>2. ANÁLISE DE QUALIDADE DOS DADOS</b>", styles['Heading2']))
        elementos.append(Spacer(1, 0.1*inch))
        
        df_unif = pd.concat(dados_sessao["dados_tabulares"], ignore_index=True)
        tipo_nf = _detectar_tipo_nf(df_unif)
        
        total_celulas = len(df_unif) * len(df_unif.columns)
        campos_vazios = df_unif.isnull().sum().sum()
        completude = ((total_celulas - campos_vazios) / total_celulas * 100) if total_celulas > 0 else 0
        
        qualidade_data = [
            ['Indicador', 'Valor', 'Status'],
            ['Tipo de Documento', tipo_nf, 'OK'],
            ['Total de Campos', str(len(df_unif.columns)), 'OK'],
            ['Total de Registros', str(len(df_unif)), 'OK'],
            ['Completude dos Dados', f'{completude:.1f}%', 'OK' if completude >= 60 else 'Atenção'],
            ['Duplicados', str(df_unif.duplicated().sum()), 'OK' if df_unif.duplicated().sum() == 0 else 'Atenção'],
        ]
        
        tabela_qualidade = Table(qualidade_data, colWidths=[3*inch, 1.5*inch, 1*inch])
        tabela_qualidade.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elementos.append(tabela_qualidade)
        elementos.append(Spacer(1, 0.2*inch))
        
        # Observação para MISTO
        if "MISTO" in tipo_nf:
            obs = Paragraph(
                f"<i><b>Observação:</b> A completude de {completude:.1f}% é esperada para "
                "documentos MISTO (NF-e + NFS-e), pois cada tipo possui campos específicos.</i>",
                styles['Normal']
            )
            elementos.append(obs)
            elementos.append(Spacer(1, 0.3*inch))
    
    # ===== 3. ARQUIVOS PROCESSADOS =====
    elementos.append(Paragraph("<b>3. ARQUIVOS PROCESSADOS</b>", styles['Heading2']))
    elementos.append(Spacer(1, 0.1*inch))
    
    if dados_sessao.get("arquivos_carregados"):
        arquivos_lista = list(dados_sessao["arquivos_carregados"])[:15]  # Limita a 15
        
        arquivos_data = [['Arquivo', 'Tipo', 'Status']]
        for arq in arquivos_lista:
            tipo = arq.split(".")[-1].upper()
            arquivos_data.append([arq[:40] + '...' if len(arq) > 40 else arq, tipo, 'Processado'])
        
        tabela_arquivos = Table(arquivos_data, colWidths=[3.5*inch, 1*inch, 1*inch])
        tabela_arquivos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elementos.append(tabela_arquivos)
    else:
        elementos.append(Paragraph("<i>Nenhum arquivo processado.</i>", styles['Normal']))
    
    elementos.append(Spacer(1, 0.5*inch))
    
    # ===== RODAPÉ =====
    rodape = Paragraph(
        f"<i>Relatório gerado automaticamente pelo ChatFiscal em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</i>",
        styles['Italic']
    )
    elementos.append(rodape)
    
    # Constrói o PDF
    doc.build(elementos)
    
    # Retorna bytes do PDF
    buffer.seek(0)
    return buffer.getvalue()


# ===== FUNÇÕES AUXILIARES =====

def _calcular_total_registros(dados_sessao):
    """Calcula total de registros fiscais"""
    if dados_sessao.get("dados_tabulares"):
        df_unif = pd.concat(dados_sessao["dados_tabulares"], ignore_index=True)
        return len(df_unif)
    return 0


def _detectar_tipo_nf(df):
    """Detecta se é NFe, NFSe ou Misto"""
    if df is None or df.empty:
        return "Não especificado"
    
    tem_nfe = any(col.startswith(('emit_', 'dest_', 'ide_')) or 'cfop' in col.lower() for col in df.columns)
    tem_nfse = any(col.startswith(('prestador_', 'tomador_')) or 'iss' in col.lower() for col in df.columns)
    
    if tem_nfe and tem_nfse:
        return "MISTO (NF-e + NFS-e)"
    elif tem_nfe:
        return "NF-e"
    elif tem_nfse:
        return "NFS-e"
    else:
        return "Não especificado"
