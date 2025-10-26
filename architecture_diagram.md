# Diagrama de Arquitetura do ChatFiscal

## Visão Geral
O ChatFiscal segue uma arquitetura modular composta por um Agente Pai (`AgentManager`) e módulos especializados. Abaixo está o diagrama representando as interações entre os componentes principais:

```mermaid
graph TD
    A[Interface do Usuário (Streamlit)] -->|Solicitações| B[AgentManager]
    B -->|Carregar Arquivo| C[FileReader]
    B -->|Validar Dados| D[DataValidator]
    B -->|Gerar Resposta| E[LLMUtils]
    B -->|Gerar Visualizações| F[Visualization]
    B -->|Exportar Relatórios| G[Exporter]

    subgraph Módulos
        C
        D
        E
        F
        G
    end

    C -->|Retorna DataFrame| B
    D -->|Retorna Relatório| B
    E -->|Retorna Resposta| B
    F -->|Retorna Gráficos| B
    G -->|Retorna Arquivos| B
```

## Descrição dos Componentes

### **AgentManager**
- **Função**: Coordenar os módulos filhos e consolidar as respostas.
- **Interações**:
  - Recebe solicitações da interface do usuário.
  - Delegar tarefas aos módulos especializados.
  - Consolidar os resultados e retornar à interface.

### **Módulos Filhos**
1. **FileReader**:
   - Processa arquivos CSV e XML.
   - Retorna um DataFrame padronizado.

2. **DataValidator**:
   - Valida dados fiscais (CFOP, valores negativos).
   - Retorna um relatório de inconsistências.

3. **LLMUtils**:
   - Gera respostas em linguagem natural com base nos dados carregados.

4. **Visualization**:
   - Gera gráficos interativos e dashboards.

5. **Exporter**:
   - Exporta relatórios e dados em formatos como CSV, JSON e Word.

---

Este diagrama e descrição ajudam a entender como os componentes do ChatFiscal interagem para fornecer uma experiência integrada ao usuário.

