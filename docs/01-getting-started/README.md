# SDD-DICOM: Sistema Automático de Conversão DICOM para NIfTI

**Projeto:** Sistema Automático de Conversão de Exames de Tomografia  
**Instituição:** Instituto IDOR - Doutorado em Medicina  
**Data:** Fevereiro 2026  
**Status:** ✅ Fase 1 - Coleta de Dados (Completa)

---

## 📋 O que é este projeto?

Sistema automatizado para converter exames de tomografia (DICOM) armazenados no Google Drive para formato NIfTI (.nii.gz) para análise em modelos de deep learning.

### Estrutura de Dados

```
Google Drive:
├── Entrada: Medicina/Doutorado IDOR/Exames/DICOM/
│   ├── Paciente_001/
│   ├── Paciente_002/
│   └── ...
│
└── Saída: Medicina/Doutorado IDOR/Exames/NifTI/
    ├── paciente_001_study_001_series_001.nii.gz
    ├── paciente_001_study_001_series_001.json
    └── ...
```

---

## 🎯 Objetivos

- ✅ **Automação:** Download, conversão e upload sem interação humana
- ✅ **Performance:** Processar 1000 arquivos em ~3 horas
- ✅ **Confiabilidade:** 99.9% uptime, recovery automático
- ✅ **Escalabilidade:** Suportar > 10k arquivos
- ✅ **Observabilidade:** Logging completo e monitoramento

---

## 📚 Próximas Leituras

| Documento | Tempo | Para quem |
|-----------|-------|-----------|
| [QUICK_START.md](QUICK_START.md) | 5 min | Todos |
| [../02-architecture/SYSTEM_DESIGN.md](../02-architecture/SYSTEM_DESIGN.md) | 15 min | Arquitetos |
| [../03-technical-specs/PRD.yaml](../03-technical-specs/PRD.yaml) | 45 min | Desenvolvedores |
| [../05-examples/CODE_REFERENCES.md](../05-examples/CODE_REFERENCES.md) | 20 min | Implementadores |

---

**Próximo:** [QUICK_START.md](QUICK_START.md)
