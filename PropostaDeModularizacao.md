📘 Estratégia de Modularização e Melhoria do Sistema “ChatFiscal”
Sumário

Visão Geral

Estrutura Hierárquica

Proposta de Módulos

Fluxo de Trabalho

Tecnologias e Ferramentas

Benefícios da Modularização

Módulo de Memória

Implementações e Status Atual

Próximos Passos

1. Visão Geral

A proposta de modularização visa tornar o ChatFiscal uma plataforma robusta, flexível e escalável, facilitando manutenção, integração e expansão de funcionalidades.
A arquitetura segue o padrão de Agente Pai (coordenador) e Módulos Filhos (especializados).

2. Estrutura Hierárquica
Agente Pai

Coordena os módulos filhos e centraliza a comunicação.

Recebe solicitações do usuário e delega tarefas ao módulo apropriado.

Consolida as respostas e apresenta uma visão unificada ao usuário.

Módulos Filhos

Cada módulo é especializado em uma função.

Comunicação feita por interfaces bem definidas.

Módulos podem ser executados de forma independente.

3. Proposta de Módulos
3.1 Módulo Leitor de Arquivos

Responsabilidade: Reconhecer, carregar e resumir arquivos (CSV, XML, PDF, imagem com OCR).
Tecnologias: pandas, xml.etree.ElementTree, PyPDF2, Tesseract.
Saída: DataFrame padronizado e resumo dos dados.

3.2 Módulo Validação Fiscal

Responsabilidade: Validar dados fiscais (CFOP, alíquotas, valores negativos).
Tecnologias: Pydantic (validação de schemas).
Saída: Relatório de inconsistências.

3.3 Módulo Respostas Inteligentes

Responsabilidade: Responder perguntas em linguagem natural com base nos dados carregados.
Tecnologias: LangChain, LlamaIndex, google.generativeai.
Saída: Texto formatado e contextualizado.

3.4 Módulo Visualização

Responsabilidade: Gerar gráficos e dashboards interativos.
Tecnologias: matplotlib, seaborn, plotly, Streamlit.
Saída: Visualizações e gráficos dinâmicos.

3.5 Módulo Exportação

Responsabilidade: Exportar dados e relatórios.
Formatos: .docx, .csv, .json.
Tecnologias: python-docx, pandas.
Saída: Arquivos prontos para download.

3.6 Módulo Integração com ERPs (MODULO REMOVIDO ✅, NÂO APLICAR À VERSÃO ATUAL DO AGENTE)

Responsabilidade: Conectar o ChatFiscal aos principais ERPs (Domínio, Alterdata, Protheus).
Tecnologias: APIs específicas dos ERPs.
Saída: Dados sincronizados entre o ChatFiscal e o ERP.

4. Fluxo de Trabalho

Entrada do Usuário
O Agente Pai identifica se é um arquivo ou uma pergunta.

Processamento Modular
O módulo correspondente executa sua tarefa e retorna o resultado.

Integração e Resposta
O Agente Pai consolida e apresenta a resposta final.

5. Tecnologias e Ferramentas
Categoria	Ferramentas
Linguagem	Python
Interface	Streamlit
NLP / IA	LangChain, LlamaIndex, google.generativeai
Validação	Pydantic
Manipulação de Dados	pandas, numpy
Visualização	matplotlib, seaborn, plotly
OCR	Tesseract, PaddleOCR
Exportação	python-docx, json
Banco de Dados / Persistência	Redis, SQLite (opcional)
6. Benefícios da Modularização

Escalabilidade: novos módulos podem ser adicionados sem impacto nos existentes.

Manutenibilidade: módulos independentes simplificam correções e melhorias.

Reutilização: componentes reaproveitáveis em outros projetos.

Clareza: responsabilidades bem definidas e documentação limpa.

7. Módulo de Memória
7.1 Função

Responsável por armazenar dados temporários e persistentes, além de facilitar a comunicação entre módulos.

7.2 Estratégia Recomendada

Memória Híbrida, combinando:

Compartilhada: para dados globais (arquivos, histórico de perguntas).

Dedicada: para resultados específicos de cada módulo.

7.3 Estrutura de Implementação
# Memória Compartilhada
class MemoriaCompartilhada:
    def __init__(self):
        self.dados = {}

    def salvar(self, chave, valor):
        self.dados[chave] = valor

    def obter(self, chave):
        return self.dados.get(chave)

# Memória Dedicada
class MemoriaDedicada:
    def __init__(self):
        self.dados = {}

    def salvar(self, chave, valor):
        self.dados[chave] = valor

    def obter(self, chave):
        return self.dados.get(chave)


Exemplo de Uso:

memoria_compartilhada = MemoriaCompartilhada()
memoria_compartilhada.salvar("arquivo_carregado", df)

memoria_dedicada = MemoriaDedicada()
memoria_dedicada.salvar("resumo", "Resumo dos dados gerado.")


Controle de Concorrência: usar threading.Lock para evitar conflitos.

8. Implementações e Status Atual
Módulo	Descrição	Status	Ação Necessária
file_reader.py	Leitor de CSV, XML, PDF e OCR	✅ Sem erros	—
data_validator.py	Validação fiscal com Pydantic	✅ Sem erros	—
visualization.py	Gráficos e dashboards	✅ Dependências faltando	pip install seaborn plotly
exporter.py	Exportação para CSV, JSON, Word	✅ Dependência python-docx	Instalar biblioteca
erp_integration.py	Integração com ERPs	✅ Sem erros	—
llm_utils.py	Geração de respostas inteligentes	✅ Integrado ao AgentManager	—
agent_manager.py	Coordenação e integração de módulos	✅ Implementado	—
memory_module.py	Memória compartilhada e dedicada	✅ Criado	—
9. Próximos Passos
Planejamento

Definir interfaces e responsabilidades entre módulos.

Criar um diagrama de arquitetura mostrando as interações.

Implementação

Finalizar o módulo leitor e integrar ao agente pai.

Validar a comunicação entre módulos.

Testes

Testes unitários em cada módulo.

Testes integrados entre módulos e o agente pai.

Documentação

Documentar arquitetura, interfaces e exemplos de uso.

Criar um guia rápido de instalação e configuração.