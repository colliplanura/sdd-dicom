# 📦 Componentes do Sistema

## Estrutura dos Módulos

```
src/
├── core/                      # Funcionalidades básicas
│   ├── __init__.py           
│   ├── config.py             # Configuração centralizada
│   ├── exceptions.py         # Exceções customizadas
│   ├── logging_config.py     # Setup de logging
│   └── types.py              # Type hints compartilhados
│
├── google_drive/              # Integração Google Drive
│   ├── __init__.py
│   ├── auth.py               # Autenticação
│   ├── client.py             # Cliente principal
│   ├── rate_limiter.py       # Rate limiting
│   └── models.py             # Modelos de dados
│
├── dicom/                     # Processamento DICOM
│   ├── __init__.py
│   ├── converter.py          # Wrapper dcm2niix
│   ├── validator.py          # Validação DICOM
│   └── metadata.py           # Extração de metadados
│
├── pipeline/                  # Orquestração
│   ├── __init__.py
│   ├── batch_pipeline.py     # Coordenador principal
│   ├── stages.py             # Estágios de processamento
│   ├── executor.py           # Gerenciador de threads/processos
│   └── progress.py           # Rastreamento de progresso
│
└── utils/                     # Utilidades
    ├── __init__.py
    ├── file_utils.py         # Operações com arquivos
    ├── checksum.py           # Validação de integridade
    ├── retry.py              # Lógica de retry
    └── circuit_breaker.py    # Circuit breaker pattern
```

---

## Componentes Detalhados

### 1. **core/config.py**
Configuração centralizada do aplicativo.

**Responsabilidades:**
- Carregar variáveis de ambiente
- Validar configurações
- Prover defaults seguros

**Exemplo:**
```python
class Config:
    google_drive_folder = "Medicina/Doutorado IDOR/Exames/DICOM"
    max_workers = 5
    timeout_seconds = 300
```

### 2. **core/exceptions.py**
Exceções customizadas para tratamento específico.

**Tipos:**
- `ConfigurationError`
- `AuthenticationError`
- `DIOMConversionError`
- `GoogleDriveError`
- `ValidationError`

### 3. **google_drive/auth.py**
Gerenciamento de autenticação.

**Responsabilidades:**
- OAuth 2.0 + Service Account
- Refresh automático de tokens
- Armazenamento seguro

### 4. **google_drive/client.py**
Cliente principal para Google Drive.

**Métodos principais:**
- `list_files(folder_id, recursive=True)`
- `download_file(file_id, output_path)`
- `upload_file(file_path, folder_id)`
- `validate_file(file_id)`

### 5. **google_drive/rate_limiter.py**
Controle de taxa de requisições.

**Estratégia:**
- 5-10 req/s (limite Google)
- Exponential backoff em 429 Too Many Requests
- Jitter para evitar thundering herd

### 6. **dicom/converter.py**
Wrapper para dcm2niix.

**Responsabilidades:**
- Detectar instalação
- Executar com timeout
- Capturar erros
- Validar output

**Exemplo:**
```python
converter = DIOMConverter()
result = converter.convert(
    input_dir="/path/to/dicom",
    output_dir="/path/to/nifti"
)
```

### 7. **dicom/validator.py**
Validação de arquivos DICOM e NIfTI.

**Validações:**
- Magic numbers
- Integridade de arquivo
- Metadados obrigatórios
- Dimensões e tipos de dados

### 8. **pipeline/batch_pipeline.py**
Coordenador central do processamento.

**Responsabilidades:**
- Orquestrar fluxo completo
- Gerenciar threads/processos
- Tratar erros e retry
- Coletar estatísticas

**Interface:**
```python
pipeline = BatchPipeline(config)
results = pipeline.process_batch([
    {"file_id": "xxx", "patient_id": "P001"},
    {"file_id": "yyy", "patient_id": "P002"},
])
```

### 9. **pipeline/executor.py**
Gerenciador de concorrência.

**Tipos de executores:**
- `ThreadPoolExecutor` para I/O (download/upload)
- `ProcessPoolExecutor` para CPU (conversão)

### 10. **pipeline/progress.py**
Rastreamento de progresso.

**Funcionalidades:**
- Contadores de sucesso/falha
- ETA de conclusão
- Callback de atualizações

### 11. **utils/retry.py**
Lógica de retry com backoff.

**Estratégia:**
- Exponential backoff: 2^n + random jitter
- Máximo 3 retries por operação
- Diferenciação entre erros permanentes/temporários

### 12. **utils/circuit_breaker.py**
Proteção contra falhas em cascata.

**Estados:**
- CLOSED: Normal
- OPEN: Bloqueando requisições
- HALF_OPEN: Testando recuperação

---

## Interações Entre Componentes

```
main()
  ├─→ config.load()
  ├─→ logging_config.setup()
  ├─→ GoogleDriveAuth.authenticate()
  ├─→ GoogleDriveClient(auth)
  ├─→ DIOMConverter()
  ├─→ BatchPipeline(client, converter, config)
  │
  ├─→ pipeline.discover_files()
  │   └─→ client.list_files() + rate_limiter
  │
  ├─→ pipeline.process_batch()
  │   ├─→ download_stage()
  │   │   └─→ client.download_file() + retry
  │   │
  │   ├─→ validate_stage()
  │   │   └─→ validator.validate()
  │   │
  │   ├─→ convert_stage()
  │   │   └─→ converter.convert() + timeout
  │   │
  │   ├─→ upload_stage()
  │   │   └─→ client.upload_file() + retry
  │   │
  │   └─→ progress.update()
  │
  └─→ logger.info("Pipeline completed")
```

---

## Garantias de Design

✅ **Single Responsibility:** Cada módulo tem uma responsabilidade clara  
✅ **Composability:** Componentes podem ser testados isoladamente  
✅ **Observability:** Logging em todos os pontos críticos  
✅ **Resilience:** Retry, circuit breaker, timeout  
✅ **Extensibility:** Fácil adicionar novos conversores/validadores

---

**Próximo:** [DATA_FLOW.md](DATA_FLOW.md)
