# 📚 Documentação do SDD-DICOM

## Estrutura de Navegação

### 🚀 [01 - Getting Started](01-getting-started/)
**Para quem quer começar rapidamente**
- `START_HERE.md` - Ponto de entrada (10 min)
- `README.md` - Visão geral do projeto (15 min)
- `QUICK_START.md` - Setup inicial

### 🏗️ [02 - Architecture](02-architecture/)
**Para entender o design do sistema**
- `SYSTEM_DESIGN.md` - Arquitetura de alto nível
- `COMPONENTS.md` - Componentes principais
- `DATA_FLOW.md` - Fluxo de dados

### 📋 [03 - Technical Specs](03-technical-specs/)
**Especificação técnica completa**
- `PRD.yaml` - Product Requirements Document
- `REQUIREMENTS.md` - Requisitos funcionais e não-funcionais
- `TECH_STACK.md` - Stack tecnológico recomendado

### 📊 [04 - Decision Analysis](04-decision-analysis/)
**Justificativa das decisões técnicas**
- `DECISION_MATRIX.md` - Análise comparativa
- `ALTERNATIVES.md` - Alternativas consideradas
- `RATIONALE.md` - Explicação das escolhas

### 💻 [05 - Examples](05-examples/)
**Exemplos de código e best practices**
- `CODE_REFERENCES.md` - Exemplos de implementação
- `PRACTICAL_EXAMPLES.md` - Exemplos práticos
- `BEST_PRACTICES.md` - Boas práticas

---

## 📖 Leitura Recomendada

### Iniciante (30 minutos)
1. [01 - Getting Started/START_HERE.md](01-getting-started/)
2. [01 - Getting Started/README.md](01-getting-started/)
3. [02 - Architecture/SYSTEM_DESIGN.md](02-architecture/)

### Desenvolvedor (1-2 horas)
1. [03 - Technical Specs/PRD.yaml](03-technical-specs/)
2. [04 - Decision Analysis/DECISION_MATRIX.md](04-decision-analysis/)
3. [05 - Examples/CODE_REFERENCES.md](05-examples/)

### Revisor Técnico (2-3 horas)
1. Tudo acima
2. [04 - Decision Analysis/RATIONALE.md](04-decision-analysis/)
3. [05 - Examples/BEST_PRACTICES.md](05-examples/)

---

## 🔍 Busca Rápida

| Pergunta | Documento |
|----------|-----------|
| O que é este projeto? | [README.md](01-getting-started/README.md) |
| Como começar? | [QUICK_START.md](01-getting-started/QUICK_START.md) |
| Qual é a arquitetura? | [SYSTEM_DESIGN.md](02-architecture/SYSTEM_DESIGN.md) |
| Quais são os requisitos? | [PRD.yaml](03-technical-specs/PRD.yaml) |
| Por que usar dcm2niix? | [DECISION_MATRIX.md](04-decision-analysis/DECISION_MATRIX.md) |
| Como implementar? | [CODE_REFERENCES.md](05-examples/CODE_REFERENCES.md) |
| Exemplos práticos? | [PRACTICAL_EXAMPLES.md](05-examples/PRACTICAL_EXAMPLES.md) |

---

## 📁 Estrutura do Projeto

```
sdd-dicom/
├── docs/                          # 📚 Documentação organizada
│   ├── 01-getting-started/        # Início rápido
│   ├── 02-architecture/           # Design do sistema
│   ├── 03-technical-specs/        # Especificações
│   ├── 04-decision-analysis/      # Análise de decisões
│   └── 05-examples/               # Exemplos de código
│
├── src/                           # 💻 Código-fonte
│   ├── core/                      # Módulos core
│   ├── google_drive/              # Integração Google Drive
│   ├── dicom/                     # Processamento DICOM
│   ├── pipeline/                  # Orquestração
│   └── utils/                     # Utilidades
│
├── tests/                         # ✅ Testes
├── config/                        # ⚙️ Configuração
└── README.md                      # 📖 Projeto raiz
```

---

**Status:** ✅ Fase 1 - Coleta de Dados (Completa)  
**Próximo:** Fase 2 - Arquitetura e Design
