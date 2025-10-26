# chatfiscal
Agente fiscal inteligente para análise de notas fiscais com Streamlit.

ChatFiscal — Agente Inteligente para Auditoria de Notas Fiscais
O ChatFiscal é um aplicativo interativo desenvolvido com Streamlit que simula um agente fiscal inteligente. Ele analisa arquivos de notas fiscais (CSV ou XML), detecta inconsistências, responde perguntas em linguagem natural e gera gráficos e relatórios automáticos.

O agente fiscal é capaz de:
•	Ler arquivos CSV e XML com dados fiscais
•	Detectar colunas como valor, emitente, data e CFOP automaticamente
•	Responder perguntas como:
o	Qual emitente tem maior valor?
o	Qual CFOP mais utilizado?
o	Qual o faturamento por mês?
•	Realizar auditorias automáticas:
o	Valores negativos
o	CFOPs inválidos
o	Notas sem emitente
•	Gerar gráficos interativos com filtros
•	Exportar relatórios e histórico de perguntas

🧠 Funcionalidades Principais

Aba: Dados & Perguntas
Descrição: Upload de arquivos, visualização dos dados e campo para perguntas ao agente

Aba: Histórico
Descrição: Registro das perguntas e respostas feitas ao agente, com opção de exportar

Aba: Auditoria
Descrição: Verificação automática de inconsistências fiscais

Aba: Visualizações
Descrição: Gráficos interativos com filtros por período, CFOP e emitente

Aba: Painel Inteligente
Descrição: Destaques automáticos, alertas e análises personalizadas via comando

Estrutura do Código
1.	carregar_arquivo(arquivo)
Lê arquivos .csv ou .xml e retorna um DataFrame com os dados fiscais.

2.	detectar_coluna(df, alternativas)
Detecta automaticamente colunas com nomes variados (ex: "valor", "vl_total", "total").

3.	gerar_resposta_llm(pergunta, df)
Gera respostas inteligentes com base na pergunta do usuário e nos dados carregados.

4.	Simulação de dados
Gera 200 notas fiscais fictícias com valores, datas, CFOPs e emitentes aleatórios.

5.	Auditoria fiscal
Detecta automaticamente:
o	Valores negativos
o	CFOPs com formato inválido
o	Notas sem emitente

6.	Visualizações
Gera gráficos de faturamento mensal, ranking de emitentes e permite exportar os dados filtrados.

7.	Painel Inteligente
Exibe destaques automáticos, alertas e permite comandos personalizados.

8.	Histórico
Armazena todas as perguntas e respostas feitas ao agente, com opção de exportar como .docx.

## 🚀 Como Executar o Projeto

### 🔧 Requisitos
- Python 3.8+
- Docker (opcional, para execução via container)

### 🖥️ Execução Local
1. Clone o repositório:
   ```bash
   git clone https://github.com/amandapraca/chatfiscal.git
   cd chatfiscal
   ```

2. (Opcional) Crie um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate   # Windows
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Execute o aplicativo:
   ```bash
   streamlit run app.py
   ```

5. Acesse o aplicativo no navegador em: `http://localhost:8501`

### 🐳 Execução com Docker
1. Construa a imagem Docker:
   ```bash
   docker-compose build
   ```

2. Inicie o container:
   ```bash
   docker-compose up
   ```

3. Acesse o aplicativo no navegador em: `http://localhost:8501`

4. Para parar o container:
   ```bash
   docker-compose down
   ```

## 📂 Exemplos de Arquivos

### Exemplo de Arquivo CSV
```csv
Emitente,Data,Valor,CFOP
Empresa A,2025-10-01,1000.00,5102
Empresa B,2025-10-02,-500.00,6101
Empresa C,2025-10-03,200.00,INVALIDO
```

### Exemplo de Arquivo XML
```xml
<NotasFiscais>
    <Nota>
        <Emitente>Empresa A</Emitente>
        <Data>2025-10-01</Data>
        <Valor>1000.00</Valor>
        <CFOP>5102</CFOP>
    </Nota>
    <Nota>
        <Emitente>Empresa B</Emitente>
        <Data>2025-10-02</Data>
        <Valor>-500.00</Valor>
        <CFOP>6101</CFOP>
    </Nota>
    <Nota>
        <Emitente>Empresa C</Emitente>
        <Data>2025-10-03</Data>
        <Valor>200.00</Valor>
        <CFOP>INVALIDO</CFOP>
    </Nota>
</NotasFiscais>
```

Requisitos
•	Python 3.8 ou superior
•	Navegador moderno (Chrome, Firefox, Edge)

Instalação
1.	Clone o repositório: git clone (https://github.com/amandapraca/chatfiscal.git)
cd chatfiscal
2.	Crie um ambiente virtual (opcional): python -m venv venv
source venv/bin/activate (Linux/macOS)
venv\Scripts\activate (Windows)
3.	Instale as dependências: pip install -r requirements.txt
ou
pip install streamlit pandas numpy python-docx

4.	🚀 Como Executar
1.	Instale as dependências:
pip install streamlit pandas numpy python-docx 
2.	Execute o app:
streamlit run app.py 
3.	Acesse no navegador:
http://localhost:8501 

Formatos Suportados
•	Arquivos .csv com separador automático
•	Arquivos .xml com estrutura baseada em 

Importações utilizadas
•	streamlit
•	pandas
•	numpy
•	xml.etree.ElementTree
•	unicodedata
•	random
•	datetime
•	io
•	python-docx

Tratamento de Erros
•	O app nunca quebra com arquivos incompletos
•	Usa st.stop() para interromper execuções inválidas com segurança
•	Mensagens amigáveis orientam o usuário em caso de erro

## 🛠️ Arquitetura Modular

O ChatFiscal segue uma arquitetura modular composta por um Agente Pai (`AgentManager`) e módulos especializados. Abaixo está uma visão geral:

### **Agente Pai (`AgentManager`)**
- **Função**: Coordenar os módulos filhos e consolidar as respostas.
- **Métodos Principais**:
  - `carregar_arquivo(arquivo)`: Processa arquivos CSV ou XML e retorna um DataFrame.
  - `validar_arquivo()`: Valida os dados carregados e retorna um relatório de inconsistências.
  - `gerar_resposta(pergunta)`: Gera respostas inteligentes com base nos dados carregados.

### **Módulos Filhos**
1. **Leitor de Arquivos**:
   - **Responsabilidade**: Processar arquivos CSV e XML.
   - **Tecnologias**: `pandas`, `xml.etree.ElementTree`.
   - **Exemplo de Uso**:
     ```python
     from agent_manager import AgentManager
     manager = AgentManager()
     df = manager.carregar_arquivo("exemplo.csv")
     print(df.head())
     ```

2. **Validação Fiscal**:
   - **Responsabilidade**: Validar dados fiscais (CFOP, valores negativos).
   - **Tecnologias**: `Pydantic`.
   - **Exemplo de Uso**:
     ```python
     relatorio = manager.validar_arquivo()
     print(relatorio)
     ```

3. **Respostas Inteligentes**:
   - **Responsabilidade**: Responder perguntas em linguagem natural.
   - **Tecnologias**: `LangChain`, `LlamaIndex`.
   - **Exemplo de Uso**:
     ```python
     resposta = manager.gerar_resposta("Qual o faturamento total?")
     print(resposta)
     ```

4. **Visualização**:
   - **Responsabilidade**: Gerar gráficos interativos.
   - **Tecnologias**: `seaborn`, `plotly`.

5. **Exportação**:
   - **Responsabilidade**: Exportar relatórios e dados.
   - **Tecnologias**: `python-docx`, `pandas`.

## 📘 Exemplos de Uso

### **Carregar Arquivo**
```python
from agent_manager import AgentManager
manager = AgentManager()
df = manager.carregar_arquivo("exemplo.csv")
print(df.head())
```

### **Validar Arquivo**
```python
relatorio = manager.validar_arquivo()
print(relatorio)
```

### **Gerar Resposta**
```python
resposta = manager.gerar_resposta("Qual o faturamento total?")
print(resposta)
```

## ✅ Testes e Validação

O projeto inclui testes unitários para validar as principais funcionalidades. Para executar os testes, use o comando:

```bash
python -m unittest discover
```

### Cobertura dos Testes
1. **Carregamento de Arquivos**:
   - Verifica se arquivos CSV e XML são processados corretamente.
2. **Validação de Dados**:
   - Garante que inconsistências fiscais sejam detectadas.
3. **Geração de Respostas**:
   - Testa a capacidade de responder perguntas com base nos dados carregados.

Os testes garantem a integridade do sistema e podem ser expandidos conforme novas funcionalidades forem adicionadas.


# 🦉 Função do Corujito — Validação Fiscal Inteligente

O **Corujito** é o assistente fiscal do ChatFiscal, responsável por analisar os dados carregados e gerar dicas inteligentes com base em regras tributárias. Ele combina validações técnicas com linguagem natural, oferecendo orientações claras e contextualizadas para quem trabalha com documentos fiscais.

---

## 🎯 Objetivo

A função `gerar_dica_corujito(df)` tem como objetivo inspecionar o conteúdo de um DataFrame fiscal e identificar inconsistências, padrões suspeitos ou pontos de atenção. A partir disso, ela gera uma dica personalizada que pode ser exibida na interface do ChatFiscal.

---

## 🧠 Como funciona

- **Análise técnica dos dados**  
  A função verifica CFOPs incomuns, CSTs de substituição tributária, campos obrigatórios nulos, ICMS zerado em operações internas, duplicidade de notas fiscais, entre outros.

- **Contexto tributário**  
  Também considera regras específicas por estado (ex: SP) e regime tributário (ex: Simples Nacional).

- **Geração de linguagem natural com LLM**  
  As observações técnicas são transformadas em uma dica amigável e compreensível por meio de uma LLM (Large Language Model), tornando a comunicação mais clara para o usuário.

---

## 📋 Exemplos de dicas geradas

- ⚠️ Foram encontrados CFOPs incomuns como 1910 e 3949. Verifique se são válidos para sua operação.  
- 🔍 Há registros com CST 060, que indicam substituição tributária. Certifique-se de que estão corretamente aplicados.  
- 📉 Alguns valores de ICMS estão zerados em operações que deveriam gerar imposto. Pode haver erro de cálculo.  
- 🧾 Os seguintes campos obrigatórios possuem valores nulos: cfop, cst, valor_total.  
- 📌 Foram encontradas notas fiscais duplicadas. Verifique se há registros repetidos.  
- 📍 Em SP, CSTs 040 e 041 indicam isenção. Verifique se estão corretamente aplicados.  
- ✅ Nenhuma inconsistência aparente. Mas continue atento aos detalhes fiscais!

---

## 🧪 Testes automatizados

A função é acompanhada por testes unitários que simulam cenários fiscais e verificam se as dicas estão sendo geradas corretamente. Os testes foram desenvolvidos com `pytest` e cobrem os principais casos de validação.

---

## 💾 Interatividade

O Corujito permite que o usuário **salve** ou **ignore** cada dica exibida. Isso torna possível:

- Criar um histórico de validações por arquivo ou data  
- Gerar relatórios com base nas dicas salvas  
- Evitar repetição de mensagens já vistas  
- Integrar com filtros do Painel Inteligente

---

> O Corujito não substitui o Painel Inteligente — ele o complementa com uma visão narrativa e contextual, ajudando o usuário a interpretar os dados com mais clareza e agilidade.
