import pandas as pd
from main.dicas_corujito import gerar_dica_corujito

def test_cfop_incomum():
    df = pd.DataFrame({"cfop": ["1910", "5102", "3949"]})
    dica = gerar_dica_corujito(df)
    print("Dica CFOP:", dica)
    assert isinstance(dica, str)
    assert "CFOP" in dica or "cfop" in dica or "❌ Erro" in dica

def test_cst_substituicao():
    df = pd.DataFrame({"cst": ["060", "000", "070"]})
    dica = gerar_dica_corujito(df)
    print("Dica CST:", dica)
    assert isinstance(dica, str)
    assert "substituição" in dica or "CST" in dica or "❌ Erro" in dica

def test_icms_zerado():
    df = pd.DataFrame({"cfop": ["5102", "5102"], "valor_icms": [0, 0]})
    dica = gerar_dica_corujito(df)
    print("Dica ICMS:", dica)
    assert isinstance(dica, str)
    assert "ICMS" in dica or "zerado" in dica or "❌ Erro" in dica

def test_dica_padrao():
    df = pd.DataFrame({"cfop": ["5102"], "cst": ["000"], "valor_icms": [10]})
    dica = gerar_dica_corujito(df)
    print("Dica padrão:", dica)
    assert isinstance(dica, str)
    assert "✅" in dica or "Tudo parece em ordem" in dica or "❌ Erro" in dica