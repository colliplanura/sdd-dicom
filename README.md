# SDD-DICOM: Sistema Automático de Conversão DICOM para NIfTI

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Production Ready](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

**Projeto:** Sistema Automático de Conversão de Exames de Tomografia  
**Instituição:** Instituto IDOR - Doutorado em Medicina  
**Data:** Fevereiro 2026  
**Status:** ✅ Fase 1 - Coleta de Dados (Completa) → **Fase 2 - Implementação** ✨

---

## � DOCUMENTAÇÃO

**Toda a documentação está organizada em:** [`docs/`](docs/)

### 🚀 Comece por aqui:
- **[START_HERE](docs/01-getting-started/START_HERE.md)** - Guia de orientação (10 min)
- **[README](docs/01-getting-started/README.md)** - Visão geral (15 min)
- **[QUICK_START](docs/01-getting-started/QUICK_START.md)** - Setup rápido (5 min)

### 🏗️ Entenda a arquitetura:
- **[SYSTEM_DESIGN](docs/02-architecture/SYSTEM_DESIGN.md)** - Arquitetura de alto nível
- **[COMPONENTS](docs/02-architecture/COMPONENTS.md)** - Componentes em detalhe

### 📋 Especificações técnicas:
- **[PRD.yaml](docs/03-technical-specs/PRD.yaml)** - Documento de requisitos (principal)

### 📊 Análise de decisões:
- **[DECISION_MATRIX](docs/04-decision-analysis/DECISION_MATRIX.md)** - Por que cada tecnologia foi escolhida

### 💻 Exemplos e boas práticas:
- **[CODE_REFERENCES](docs/05-examples/CODE_REFERENCES.md)** - Exemplos de código
- **[BEST_PRACTICES](docs/05-examples/BEST_PRACTICES.md)** - Guia de qualidade

---

## 📋 O que é?

Pipeline completa e pronta para produção que:
- ✅ Baixa automaticamente exames DICOM do Google Drive
- ✅ Converte para formato NIfTI (.nii.gz) para análise em Deep Learning
- ✅ Faz upload dos resultados de volta ao Google Drive
- ✅ Processa grandes volumes em paralelo (~1000 arquivos em 3 horas)
- ✅ Registra tudo com logging estruturado
- ✅ Recuperação automática de falhas
- ✅ Taxa de sucesso > 99%

---

## 🎯 Stack Recomendado

| Componente | Tecnologia | Score |
|-----------|------------|-------|
| Conversão DICOM | **dcm2niix** | 47/50 |
| Google Drive | **google-api-python-client** | 42/50 |
| Paralelização | **ThreadPool + ProcessPool** | 48/50 |
| Logging | **loguru** | 44/50 |
| Tratamento de Erros | **Custom exceptions + Circuit Breaker** | 45/50 |

---

## 📈 Performance Esperada

```
1000 arquivos × 10MB:
├─ Download:  20-30 min (5 workers)
├─ Conversão: 100-150 min (N-2 CPUs)  
├─ Upload:    20-30 min (3-5 workers)
└─ TOTAL:     ~2.5-3.5 horas

Taxa de sucesso: > 99%
```

---

## 📖 Estrutura de Documentação

```
docs/
├── 01-getting-started/     ← COMECE AQUI
│   ├── START_HERE.md
│   ├── README.md
│   └── QUICK_START.md
├── 02-architecture/
│   ├── SYSTEM_DESIGN.md
│   └── COMPONENTS.md
├── 03-technical-specs/
│   └── PRD.yaml
├── 04-decision-analysis/
│   └── DECISION_MATRIX.md
└── 05-examples/
    ├── CODE_REFERENCES.md
    └── BEST_PRACTICES.md
```

---

**→ [Acesse a documentação completa](docs/01-getting-started/START_HERE.md)**

---

*Projeto SDD-DICOM - Fevereiro 2026*

