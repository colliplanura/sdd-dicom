# 🏗️ Arquitetura do Sistema

## Visão de Alto Nível

```
┌─────────────────────────────────────┐
│      Google Drive API               │
│  (auth + list + download + upload) │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   Google Drive Manager              │
│  (abstração + credenciais + cache)  │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   Batch Pipeline                    │
│  (ThreadPoolExecutor + rate limit)  │
└────────────┬────────────────────────┘
             │
      ┌──────┴──────────┐
      │                 │
┌─────▼──────┐  ┌───────▼──────────┐
│  Download  │  │ Process (Stages) │
│ (5 workers)│  │ - Convert DICOM  │
│            │  │ - Validate       │
│            │  │ - Compress       │
└─────┬──────┘  └────────┬─────────┘
      │                  │
      └────────┬─────────┘
               ▼
         Upload Results
        (3-5 workers)
               │
               ▼
    ┌─────────────────────────────────────┐
    │   Logging Estruturado               │
    │  (loguru + JSON + alertas)          │
    └─────────────────────────────────────┘
```

---

## Componentes Principais

### 1. **GoogleDriveClient**
Abstração para interação com Google Drive
- Autenticação (OAuth 2.0 + Service Account)
- Listagem de arquivos com cache
- Download com resume
- Upload com validação
- Rate limiting integrado
- Retry automático

### 2. **DIOMConverter**
Wrapper para dcm2niix
- Detecção automática de instalação
- Execução com timeout
- Captura de stderr/stdout
- Validação de saída
- Tratamento de erros

### 3. **BatchPipeline**
Orquestrador de processamento
- Fila de tarefas
- ThreadPoolExecutor para I/O
- ProcessPoolExecutor para CPU
- Monitoramento de progresso
- Recuperação de falhas

### 4. **Logging**
Sistema centralizado de logs
- loguru com rotação automática
- Console + arquivo
- JSON output opcional
- Métricas de performance

---

## Fluxo de Dados

```
ENTRADA (Google Drive)
        │
        ▼
    [DESCOBERTA] → Listar arquivos DICOM
        │
        ├─→ Validação de estrutura
        ├─→ Cache por 24h
        └─→ Geração de fila
        │
        ▼
    [LOOP PARALELO] ThreadPoolExecutor
        │
        ├─→ [DOWNLOAD]
        │   ├─→ Streaming (eficiente)
        │   ├─→ Checksum MD5
        │   └─→ Retry automático
        │
        ├─→ [VALIDAÇÃO DICOM]
        │   ├─→ Magic number
        │   ├─→ Integridade
        │   └─→ Metadados obrigatórios
        │
        ├─→ [CONVERSÃO] ProcessPoolExecutor
        │   ├─→ dcm2niix -z y -f
        │   ├─→ Gerar JSON (BIDS)
        │   ├─→ Timeout 5 min
        │   └─→ Capturar logs
        │
        ├─→ [VALIDAÇÃO NIfTI]
        │   ├─→ Magic number
        │   ├─→ Integridade
        │   └─→ Dimensões
        │
        └─→ [UPLOAD]
            ├─→ Streaming
            ├─→ Checksum
            ├─→ Retry
            └─→ Validação
        │
        ▼
    [LOGGING]
        │
        ├─→ Arquivo estruturado
        ├─→ Alertas
        └─→ Métricas
        │
        ▼
    SAÍDA (Google Drive)
```

---

## Padrões de Design

### 1. **Camadas de Abstração**
```
CLI/Config
    ↓
Application Layer
    ↓
Domain Layer (Pipeline)
    ↓
Infrastructure Layer (Google Drive, DICOM)
    ↓
External Services (Google Drive API, dcm2niix)
```

### 2. **Dependency Injection**
Componentes recebem dependências como parâmetros.

### 3. **Error Handling**
- Custom exceptions por tipo de erro
- Retry automático com backoff exponencial
- Circuit breaker para Google Drive
- Graceful degradation

### 4. **Logging Strategy**
- DEBUG: Detalhes de execução
- INFO: Eventos importantes
- WARNING: Possíveis problemas
- ERROR: Falhas

---

## Performance Targets

```
Hardware: 8-core CPU, 16GB RAM
Workers: 5 paralelos

100 arquivos (10MB cada):
├─ Download: ~2-3 min
├─ Conversão: ~10-15 min
├─ Upload: ~2-3 min
└─ Total: ~15-20 min

1000 arquivos (10MB cada):
├─ Download: ~20-30 min
├─ Conversão: ~100-150 min
├─ Upload: ~20-30 min
└─ Total: ~2.5-3.5 horas
```

---

## Escalabilidade

### Fase 3 (Atual)
- ThreadPoolExecutor + ProcessPoolExecutor
- Single machine
- ~1000 arquivos/ciclo

### Fase 4-5 (Futuro)
- Celery para distribuição
- Multi-machine processing
- Queue com priorização
- ~10k+ arquivos/ciclo

---

**Próximo:** [COMPONENTS.md](COMPONENTS.md)
