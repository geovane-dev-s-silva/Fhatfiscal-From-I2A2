# file_reader.py - ok passar

import pandas as pd
import xml.etree.ElementTree as ET
from PyPDF2 import PdfReader
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from PIL import Image
import logging


class FileReader:
    """
    Classe responsável por carregar e processar arquivos (CSV, XML, PDF).
    """

    # Mapeamento das estruturas de XML e seus métodos parsers
    ESTRUTURAS = {
        'nfe': '_carregar_nfe',
        'infnfe': '_carregar_nfe',
        'nfeproc': '_carregar_nfe',
        'nfce': '_carregar_nfe',
        'nfcescan': '_carregar_nfe',
        'nfse': '_carregar_nfse',
        'nfservico': '_carregar_nfse',
        'gerarnfseresposta': '_carregar_nfse',
        'cte': '_carregar_nfe',
        'infcte': '_carregar_nfe',
        'mdfe': '_carregar_nfe',
        'infmdfe': '_carregar_nfe',
        'bpe': '_carregar_nfe',
        'infbpe': '_carregar_nfe',
        'nfcom': '_carregar_nfe',
        'infnfcom': '_carregar_nfe',
        'nf3e': '_carregar_nfe',
        'infnf3e': '_carregar_nfe',
    }

    @staticmethod
    def carregar_csv(arquivo):
        try:
            return pd.read_csv(arquivo, encoding="latin1", sep=None, engine="python")
        except Exception as e:
            raise ValueError(f"Erro ao carregar arquivo CSV: {e}")

    @staticmethod
    def carregar_xml(arquivo):
        """
        Carrega um único XML, detecta o tipo e retorna DataFrame.
        """
        try:
            tree = ET.parse(arquivo)
            root = tree.getroot()
            root_tag = root.tag.split('}')[-1].lower()

            for chave, metodo in FileReader.ESTRUTURAS.items():
                if chave in root_tag:
                    return getattr(FileReader, metodo)(root)

            return FileReader._carregar_xml_achatado(root)

        except Exception as e:
            raise ValueError(f"Erro ao carregar arquivo XML: {e}")

    @staticmethod
    def carregar_varios_xml(arquivos):
        """
        Carrega vários arquivos XML de diferentes formatos,
        acumula todos os registros e retorna um único DataFrame.
        """
        todos_os_registros = []

        for arq in arquivos:
            tree = ET.parse(arq)
            root = tree.getroot()
            root_tag = root.tag.split('}')[-1].lower()

            # detecta parser
            for chave, metodo in FileReader.ESTRUTURAS.items():
                if chave in root_tag:
                    resultado = getattr(FileReader, metodo)(root)
                    break
            else:
                resultado = FileReader._carregar_xml_achatado(root)

            # converte resultado em lista de dicts
            if isinstance(resultado, pd.DataFrame):
                todos_os_registros.extend(resultado.to_dict(orient='records'))
            elif isinstance(resultado, list):
                todos_os_registros.extend(resultado)
            else:  # dict
                todos_os_registros.append(resultado)

        # DataFrame único
        df_final = pd.DataFrame(todos_os_registros)
        df_final = df_final.dropna(axis=1, how='all').reset_index(drop=True)
        return df_final

    @staticmethod
    def _carregar_xml_achatado(root):
        """Parser genérico: achata totalmente QUALQUER XML em uma única linha."""
        try:
            linha = {}

            def extrair_recursivamente(el, prefixo=""):
                tag = el.tag.split('}')[-1]
                caminho = f"{prefixo}_{tag}" if prefixo else tag
                if el.text and el.text.strip():
                    linha[caminho] = linha.get(caminho, el.text.strip())
                for attr, val in el.attrib.items():
                    linha[f"{caminho}_{attr}"] = linha.get(f"{caminho}_{attr}", val)
                for filho in el:
                    extrair_recursivamente(filho, caminho)

            extrair_recursivamente(root)
            df = pd.DataFrame([linha]).dropna(axis=1, how='all')
            return df[sorted(df.columns)]

        except Exception as e:
            raise ValueError(f"Erro ao processar XML achatado: {e}")

    @staticmethod
    def _carregar_nfse(root):
        """Parser para NFSe e GerarNfseResposta - VERSÃO COMPLETA."""
        try:
            dados = []
            nota_info = {}

            # 1. CAPTURAR TUDO DO BLOCO Nfse/InfNfse (informações principais)
            for bloco_busca in ['.//Nfse', './/nf', './/InfNfse', './/CompNfse']:
                bloco_nfse = root.find(bloco_busca)
                if bloco_nfse is not None:
                    for el in bloco_nfse.iter():
                        tag = el.tag.split('}')[-1]
                        # Pegar apenas elementos folha (sem filhos)
                        if el.text and el.text.strip() and len(list(el)) == 0:
                            nota_info[f"nfse_{tag}"] = el.text.strip()

            # 2. CAPTURAR VALORES (ValorServicos, Aliquota, ValorIss, BaseCalculo, etc.)
            for bloco_busca in ['.//Valores', './/valores', './/ValoresNfse']:
                bloco_valores = root.find(bloco_busca)
                if bloco_valores is not None:
                    for el in bloco_valores.iter():
                        tag = el.tag.split('}')[-1]
                        if el.text and el.text.strip() and len(list(el)) == 0:
                            nota_info[f"nfse_{tag}"] = el.text.strip()

            # 3. CAPTURAR SERVICO
            for bloco_busca in ['.//Servico', './/servico', './/DadosServico']:
                bloco_servico = root.find(bloco_busca)
                if bloco_servico is not None:
                    for el in bloco_servico.iter():
                        tag = el.tag.split('}')[-1]
                        if el.text and el.text.strip() and len(list(el)) == 0:
                            nota_info[f"servico_{tag}"] = el.text.strip()

            # 4. PRESTADOR (captura hierárquica)
            for bloco_busca in ['.//PrestadorServico', './/prestador', './/Prestador', './/IdentificacaoPrestador']:
                prest = root.find(bloco_busca)
                if prest is not None:
                    FileReader._extrair_hierarquico(prest, nota_info, 'prestador')

            # 5. TOMADOR (captura hierárquica)
            for bloco_busca in ['.//Tomador', './/tomador', './/TomadorServico', './/IdentificacaoTomador']:
                tomo = root.find(bloco_busca)
                if tomo is not None:
                    FileReader._extrair_hierarquico(tomo, nota_info, 'tomador')

            # 6. INTERMEDIARIO (se houver)
            for bloco_busca in ['.//Intermediario', './/intermediario', './/IntermediarioServico']:
                inter = root.find(bloco_busca)
                if inter is not None:
                    FileReader._extrair_hierarquico(inter, nota_info, 'intermediario')

            # 7. CONSTRUCAO CIVIL (se houver)
            const = root.find('.//ConstrucaoCivil')
            if const is not None:
                for el in const.iter():
                    tag = el.tag.split('}')[-1]
                    if el.text and el.text.strip() and len(list(el)) == 0:
                        nota_info[f"construcao_{tag}"] = el.text.strip()

            # 8. ITENS (se houver)
            listas = root.findall('.//itens//lista') or root.findall('.//Item') or root.findall('.//ItensServico')
            if not listas:
                dados.append(nota_info)
            else:
                for idx, item in enumerate(listas, 1):
                    linha = nota_info.copy()
                    linha['item_numero'] = idx
                    for el in item.iter():
                        tag = el.tag.split('}')[-1]
                        if el.text and el.text.strip() and len(list(el)) == 0:
                            linha[f"item_{tag}"] = el.text.strip()
                    dados.append(linha)

            # Criar DataFrame organizado
            df = pd.DataFrame(dados).dropna(axis=1, how='all').reset_index(drop=True)
            
            # Organizar colunas por categoria
            cols_nfse = sorted(c for c in df.columns if c.startswith('nfse_'))
            cols_servico = sorted(c for c in df.columns if c.startswith('servico_'))
            cols_prest = sorted(c for c in df.columns if c.startswith('prestador_'))
            cols_tomo = sorted(c for c in df.columns if c.startswith('tomador_'))
            cols_inter = sorted(c for c in df.columns if c.startswith('intermediario_'))
            cols_const = sorted(c for c in df.columns if c.startswith('construcao_'))
            cols_item = sorted(c for c in df.columns if c.startswith('item_') or c == 'item_numero')
            outras = [c for c in df.columns if c not in cols_nfse + cols_servico + cols_prest + cols_tomo + cols_inter + cols_const + cols_item]
            
            return df[cols_nfse + cols_servico + cols_prest + cols_tomo + cols_inter + cols_const + cols_item + sorted(outras)]

        except Exception as e:
            raise ValueError(f"Erro ao processar NFSe: {e}")

    @staticmethod
    def _extrair_hierarquico(elemento, dicionario, prefixo):
        """
        Extrai dados de forma hierárquica, identificando subgrupos
        (como Endereco, Contato, IdentificacaoCpfCnpj, etc.)
        """
        for el in elemento.iter():
            tag = el.tag.split('}')[-1]
            
            # Pular o próprio elemento raiz
            if el == elemento:
                continue
            
            # Pegar apenas elementos folha (sem filhos)
            if el.text and el.text.strip() and len(list(el)) == 0:
                # Identificar o pai para criar hierarquia
                parent = el.getparent() if hasattr(el, 'getparent') else None
                parent_tag = parent.tag.split('}')[-1].lower() if parent is not None else ''
                
                # Criar chave hierárquica
                if parent_tag in ['endereco', 'address', 'enderecoprestador', 'enderecotomador']:
                    chave = f"{prefixo}_endereco_{tag}"
                elif parent_tag in ['contato', 'contact', 'contatoprestador', 'contatomador']:
                    chave = f"{prefixo}_contato_{tag}"
                elif parent_tag in ['identificacaocpfcnpj', 'cpfcnpj', 'identificacao']:
                    chave = f"{prefixo}_{tag}"
                elif parent_tag in ['razaoSocial', 'nomerazaosocial']:
                    chave = f"{prefixo}_{tag}"
                else:
                    chave = f"{prefixo}_{tag}"
                
                dicionario[chave] = el.text.strip()

    @staticmethod
    def _carregar_nfe(root):
        """Parser específico para NFe, NFC-e, CT-e, MDF-e - VERSÃO COMPLETA."""
        try:
            dados = []
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            
            # Buscar notas em diferentes estruturas
            notas = root.findall('.//nfe:infNFe', ns) or root.findall('.//infNFe')
            if not notas:
                for est in ['.//NFe', './/nf', './/NotaFiscal', './/Nota', './/infCTe', './/infMDFe']:
                    notas = root.findall(est)
                    if notas:
                        break
            
            for nota in notas:
                cab = {}
                
                # Função auxiliar para extração completa
                def extrair(secao, prefixo):
                    if secao is None:
                        return
                    for el in secao.iter():
                        tag = el.tag.split('}')[-1]
                        # Pegar apenas elementos folha
                        if el.text and el.text.strip() and len(list(el)) == 0 and tag.lower() != prefixo:
                            chave = f"{prefixo}_{tag}"
                            cab.setdefault(chave, el.text.strip())
                
                # IDE - Identificação da NF-e
                extrair(nota.find('.//nfe:ide', ns) or nota.find('.//ide'), 'ide')
                
                # EMIT - Emitente
                extrair(nota.find('.//nfe:emit', ns) or nota.find('.//emit'), 'emit')
                
                # DEST - Destinatário
                extrair(nota.find('.//nfe:dest', ns) or nota.find('.//dest'), 'dest')
                
                # TOTAL - Totais
                extrair(nota.find('.//nfe:total', ns) or nota.find('.//total'), 'total')
                
                # TRANSP - Transporte
                extrair(nota.find('.//nfe:transp', ns) or nota.find('.//transp'), 'transp')
                
                # COBR - Cobrança
                extrair(nota.find('.//nfe:cobr', ns) or nota.find('.//cobr'), 'cobr')
                
                # PAGT - Pagamento
                extrair(nota.find('.//nfe:pag', ns) or nota.find('.//pag'), 'pag')
                
                # INFADIC - Informações Adicionais
                extrair(nota.find('.//nfe:infAdic', ns) or nota.find('.//infAdic'), 'infadic')
                
                # ITENS - Produtos/Serviços
                itens = nota.findall('.//nfe:det', ns) or nota.findall('.//det')
                if not itens:
                    dados.append(cab)
                else:
                    for idx, item in enumerate(itens, 1):
                        linha = cab.copy()
                        linha['item_numero'] = idx
                        
                        # Extrair TUDO do item (produto, imposto, etc.)
                        for el in item.iter():
                            tag = el.tag.split('}')[-1]
                            if el.text and el.text.strip() and len(list(el)) == 0 and tag.lower() != 'det':
                                chave = f"item_{tag}"
                                linha.setdefault(chave, el.text.strip())
                        
                        dados.append(linha)
            
            # Criar DataFrame
            df = (pd.DataFrame(dados)
                  .dropna(axis=1, how='all')
                  .drop_duplicates()
                  .reset_index(drop=True))
            
            # Organizar colunas
            cols_ide = sorted(c for c in df.columns if c.startswith('ide_'))
            cols_emit = sorted(c for c in df.columns if c.startswith('emit_'))
            cols_dest = sorted(c for c in df.columns if c.startswith('dest_'))
            cols_total = sorted(c for c in df.columns if c.startswith('total_'))
            cols_transp = sorted(c for c in df.columns if c.startswith('transp_'))
            cols_cobr = sorted(c for c in df.columns if c.startswith('cobr_'))
            cols_pag = sorted(c for c in df.columns if c.startswith('pag_'))
            cols_infadic = sorted(c for c in df.columns if c.startswith('infadic_'))
            cols_item = sorted(c for c in df.columns if c.startswith('item_'))
            outras = [c for c in df.columns if c not in cols_ide + cols_emit + cols_dest + cols_total + cols_transp + cols_cobr + cols_pag + cols_infadic + cols_item]
            
            return df[cols_ide + cols_emit + cols_dest + cols_total + cols_transp + cols_cobr + cols_pag + cols_infadic + cols_item + sorted(outras)]
            
        except Exception as e:
            raise ValueError(f"Erro ao processar NFe: {e}")

    @staticmethod
    def carregar_pdf(arquivo):
        try:
            reader = PdfReader(arquivo)
            texto = "".join(page.extract_text() or "" for page in reader.pages)
            return texto
        except Exception as e:
            raise ValueError(f"Erro ao carregar arquivo PDF: {e}")

    @staticmethod
    def carregar_imagem_com_ocr(arquivo):
        try:
            img = Image.open(arquivo)
            return pytesseract.image_to_string(img, lang="por")
        except Exception as e:
            raise ValueError(f"Erro ao processar imagem com OCR: {e}")
