# Decision Matrix - Seleção de Tecnologias

**Data:** Fevereiro 2026  
**Etapa:** Coleta de Dados (SDD)  

---

## 1. DICOM → NIfTI Converter

### Opções Avaliadas

#### Opção A: dcm2niix (RECOMENDADO ✅)

| Critério | Avaliação |
|----------|-----------|
| **Vendor** | Independente (todos supportados) |
| **Performance** | 5/5 - Excelente (C++) |
| **BIDS Compliance** | 5/5 - Nativo |
| **Edge Cases** | 5/5 - Robusto |
| **Popularidade** | 5/5 - 1100+ stars GitHub |
| **Documentação** | 4/5 - Excelente NITRC wiki |
| **Suporte Ativo** | 5/5 - Mantido ativamente |
| **Facilidade Integração** | 4/5 - CLI simples |
| **Custo** | 5/5 - Open source (BSD) |
| **Comunidade** | 5/5 - Pesquisa neuroimagem |

**SCORE:** 47/50 ✅

**Decisão:**
- ✅ **USAR COMO PRIMARY**
- Integrar via subprocess em Python
- Wrapper com error handling

---

#### Opção B: nibabel + pydicom

| Critério | Avaliação |
|----------|-----------|
| **Vendor** | 3/5 - Siemens principalmente |
| **Performance** | 2/5 - Lento (Python puro) |
| **BIDS Compliance** | 2/5 - Manual |
| **Edge Cases** | 3/5 - Limitado |
| **Popularidade** | 5/5 - 500+ stars |
| **Documentação** | 4/5 - Boa |
| **Suporte Ativo** | 5/5 - NiPy project |
| **Facilidade Integração** | 5/5 - Native Python |
| **Custo** | 5/5 - Open source (MIT) |
| **Comunidade** | 5/5 - Pesquisa neuroimagem |

**SCORE:** 37/50

**Decisão:**
- ⚠️ **USAR COMO FALLBACK**
- Prototipagem e testes
- Edge cases não suportados

---

#### Opção C: SimpleITK

| Critério | Avaliação |
|----------|-----------|
| **Vendor** | 4/5 - Multi-vendor |
| **Performance** | 3/5 - Boa (C++ binding) |
| **BIDS Compliance** | 0/5 - Não nativo |
| **Edge Cases** | 3/5 - Limitado |
| **Popularidade** | 5/5 - 500+ stars |
| **Documentação** | 4/5 - Boa |
| **Suporte Ativo** | 5/5 - ITK project |
| **Facilidade Integração** | 4/5 - Python API |
| **Custo** | 5/5 - Open source (Apache) |
| **Comunidade** | 4/5 - Processamento imagens |

**SCORE:** 33/50

**Decisão:**
- ⏳ **CONSIDERAR PARA FUTURO**
- Pós-processamento (resampling, etc)
- Não como primary converter

---

### Recomendação Final para Conversão

```
┌─────────────────────────────────────┐
│ PRIMARY: dcm2niix                   │
│ • CLI via subprocess                │
│ • Wrapper Python                    │
│ • Error handling robusto            │
└─────────────────────────────────────┘
         ↑
         │ SE FALHAR
         ↓
┌─────────────────────────────────────┐
│ FALLBACK: nibabel.nicom             │
│ • Suporta slices DICOM individuais  │
│ • Construir volume manualmente      │
└─────────────────────────────────────┘
         ↑
         │ SE FALHAR
         ↓
┌─────────────────────────────────────┐
│ ÚLTIMO RECURSO: SimpleITK           │
│ • Conversão genérica                │
│ • Sem garantias BIDS                │
└─────────────────────────────────────┘
```

---

## 2. Google Drive Integration

### Opções Avaliadas

#### Opção A: google-api-python-client (RECOMENDADO ✅)

| Critério | Avaliação |
|----------|-----------|
| **Documentação** | 5/5 - Official Google |
| **Features** | 5/5 - Completo |
| **Performance** | 5/5 - Otimizado |
| **Rate Limiting** | 5/5 - Controle fino |
| **Error Handling** | 5/5 - Robusto |
| **Maintenance** | 5/5 - Google mantém |
| **Community** | 5/5 - Muitos exemplos |
| **Cost** | 5/5 - Open source (Apache) |
| **Learning Curve** | 3/5 - Um pouco complexo |
| **Async Support** | 4/5 - Suporta com aiohttp |

**SCORE:** 42/50 ✅

**Decisão:**
- ✅ **USAR COMO PRIMARY**
- OAuth 2.0 + Service Account
- Implementar rate limiting manual

---

#### Opção B: pydrive2

| Critério | Avaliação |
|----------|-----------|
| **Documentação** | 3/5 - Básica |
| **Features** | 4/5 - Essencial |
| **Performance** | 3/5 - OK |
| **Rate Limiting** | 2/5 - Limitado |
| **Error Handling** | 3/5 - Básico |
| **Maintenance** | 2/5 - Menos ativo |
| **Community** | 3/5 - Razoável |
| **Cost** | 5/5 - Open source (Apache) |
| **Learning Curve** | 5/5 - Muito simples |
| **Async Support** | 1/5 - Não nativo |

**SCORE:** 31/50

**Decisão:**
- ⚠️ **USAR PARA PROTOTIPAGEM**
- Mais simples para MVP
- Upgrade para google-api-python-client em produção

---

### Recomendação Final para Google Drive

```
PRODUÇÃO: google-api-python-client
├─ Authentication: Service Account
├─ Rate Limiting: 5-10 req/s manual
├─ Retry: exponential backoff
├─ Streaming: para grandes arquivos
└─ Checksum: validation pós-transferência

PROTOTIPAGEM: pydrive2
├─ Setup mais rápido
├─ Menos configuração
└─ Upgrade em fase 3
```

---

## 3. Parallelização Strategy

### Opções Avaliadas

#### Opção A: ThreadPoolExecutor para I/O + ProcessPoolExecutor para CPU (RECOMENDADO ✅)

| Aspecto | Avaliação |
|--------|-----------|
| **Download/Upload** | ThreadPoolExecutor (5 workers) |
| **Conversão DICOM** | ProcessPoolExecutor (N-2 workers) |
| **Validação** | ProcessPoolExecutor |
| **Overhead** | Baixo (built-in Python) |
| **GIL Impact** | Otimizado para cada caso |
| **Scalability** | Até ~16 workers |
| **Debugging** | Fácil com stack traces |

**SCORE:** 48/50 ✅

**Decisão:**
- ✅ **USAR COMO PRIMARY**
- Executores separados por tipo de task
- Pipelining entre estágios

---

#### Opção B: asyncio

| Aspecto | Avaliação |
|--------|-----------|
| **I/O Concurrency** | 5/5 - Excelente |
| **CPU Parallelism** | 0/5 - Não funciona (GIL) |
| **Learning Curve** | 1/5 - Muito difícil |
| **Debugging** | 2/5 - Stack traces complexas |
| **Scalability** | 5/5 - Milhares de coroutines |

**SCORE:** 13/50 (inadequado para este caso)

**Decisão:**
- ⏳ **CONSIDERAR PARA FUTURO**
- Apenas quando escalar para servidores
- Com uvloop para performance

---

#### Opção C: Celery + Redis

| Aspecto | Avaliação |
|--------|-----------|
| **Distributed** | 5/5 - Suporta múltiplas máquinas |
| **Scalability** | 5/5 - Ilimitado |
| **Learning Curve** | 1/5 - Muito complexo |
| **Operational Complexity** | 1/5 - Redis, workers, etc |
| **For Single Machine** | 0/5 - Overkill |

**SCORE:** 12/50 (prematuro para fase inicial)

**Decisão:**
- ⏳ **CONSIDERAR PARA FASE 5**
- Apenas quando escalar a múltiplas máquinas
- Phase 3-4 com ThreadPoolExecutor é suficiente

---

### Recomendação Final para Paralelização

```
FASE 3 (ATUAL): ThreadPoolExecutor + ProcessPoolExecutor
├─ Download: ThreadPoolExecutor(max_workers=5)
├─ Conversion: ProcessPoolExecutor(max_workers=cpu_count()-2)
├─ Upload: ThreadPoolExecutor(max_workers=3-5)
└─ Simples, eficiente, debugável

FASE 5+ (FUTURO): Considerar Celery
├─ Se escalar para múltiplas máquinas
├─ Se volume > 100k arquivos/dia
└─ Upgrade path definido
```

---

## 4. Logging Solution

### Opções Avaliadas

#### Opção A: loguru (RECOMENDADO ✅)

| Critério | Avaliação |
|----------|-----------|
| **Performance** | 5/5 - 10x mais rápido |
| **Syntax** | 5/5 - Muito simples |
| **Rotation** | 5/5 - Automática |
| **JSON Output** | 5/5 - Nativo |
| **Filtering** | 5/5 - Poderoso |
| **Learning Curve** | 5/5 - Fácil |
| **Documentation** | 5/5 - Excelente |
| **Active Development** | 5/5 - Mantido |
| **Community** | 4/5 - Crescente |

**SCORE:** 44/50 ✅

**Decisão:**
- ✅ **USAR COMO PRIMARY**
- Simples de configurar
- Perfeito para batch processing

---

#### Opção B: logging (built-in)

| Critério | Avaliação |
|----------|-----------|
| **Performance** | 2/5 - Mais lento |
| **Syntax** | 2/5 - Verboso |
| **Rotation** | 3/5 - Complexo de configurar |
| **JSON Output** | 2/5 - Requer setup |
| **Learning Curve** | 2/5 - Confuso |
| **Documentation** | 3/5 - Verbose |
| **Active Development** | 5/5 - Python stdlib |

**SCORE:** 19/50

**Decisão:**
- ❌ **NÃO USAR**
- Overhead desnecessário
- loguru é alternativa superior

---

#### Opção C: structlog

| Critério | Avaliação |
|----------|-----------|
| **Structured Output** | 5/5 - Excelente |
| **JSON** | 5/5 - Nativo |
| **Performance** | 4/5 - Bom |
| **Learning Curve** | 2/5 - Complexo |
| **Documentation** | 4/5 - Boa |
| **For Our Case** | 2/5 - Overkill |

**SCORE:** 22/50 (overengineered)

**Decisão:**
- ⏳ **CONSIDERAR PARA FUTURO**
- Se integrar com ELK stack
- Fase 4+ quando tiver infraestrutura

---

### Recomendação Final para Logging

```python
# FASE 3: loguru (simples e poderoso)
from loguru import logger

logger.remove()
logger.add(
    "logs/conversion_{time:YYYY-MM-DD}.log",
    format="{time} | {level: <8} | {name}:{function} | {message}",
    rotation="10 MB",
    retention="30 days",
    compression="zip"
)

logger.info("Processing {patient}", patient=123)

# FASE 5+: Se tiver ELK stack
# - Upgrade para structlog
# - JSON output para Elasticsearch
```

---

## 5. Error Handling Strategy

### Opções Avaliadas

#### Opção A: Try-Catch + Custom Exception Hierarchy (RECOMENDADO ✅)

```python
class DIOMError(Exception):
    """Base DICOM conversion exception"""
    
class DIOMNetworkError(DIOMError):
    """Temporary network error - RETRY"""
    
class DIOMConversionError(DIOMError):
    """Permanent conversion error - SKIP"""
    
class DIOMAuthError(DIOMError):
    """Authentication error - FATAL"""
```

**Decisão:** ✅ **USAR**
- Diferenciação entre erros temporários vs permanentes
- Retry automático para network errors
- Skip + log para conversion errors

---

#### Opção B: Circuit Breaker Pattern

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
    
    def call(self, func, *args, **kwargs):
        if self.is_open():
            raise CircuitBreakerOpen("Circuit is open")
        try:
            result = func(*args, **kwargs)
            self.reset()
            return result
        except Exception as e:
            self.record_failure()
            raise
```

**Decisão:** ✅ **USAR PARA GOOGLE DRIVE**
- Proteção contra rate limiting
- Evita tempestades de requisições
- Backoff automático

---

### Recomendação Final para Error Handling

```
Estratégia em Cascata:

1️⃣ TEMPORARY ERRORS (Retry automático)
   ├─ Network timeout → Retry (3x)
   ├─ Google Drive 429 → Exponential backoff
   └─ Partial download → Resume

2️⃣ PERMANENT ERRORS (Skip + Log)
   ├─ Corrupted DICOM → Skip, log warning
   ├─ Unsupported format → Skip, log
   └─ Conversion failed → Skip, log error

3️⃣ FATAL ERRORS (Parar pipeline)
   ├─ Authentication failure → Exit
   ├─ Disk full → Cleanup + Exit
   └─ Out of memory → Exit

4️⃣ CIRCUIT BREAKER (Google Drive)
   ├─ Falhas > 5 em 60s → Abrir
   ├─ Aguardar 5min → Tentar reset
   └─ Se persistir → Notificar usuário
```

---

## 6. Testing Strategy

### Opções Avaliadas

#### Opção A: pytest + pytest-cov (RECOMENDADO ✅)

| Critério | Avaliação |
|----------|-----------|
| **Frameworks** | 5/5 - Mais moderno |
| **Coverage** | 5/5 - Excelente |
| **Plugins** | 5/5 - Muitos disponíveis |
| **Community** | 5/5 - Standard Python |
| **Learning Curve** | 5/5 - Fácil |

**SCORE:** 25/25 ✅

**Decisão:** ✅ **USAR**

---

#### Opção B: unittest (built-in)

| Critério | Avaliação |
|----------|-----------|
| **Frameworks** | 3/5 - Mais verbose |
| **Coverage** | 2/5 - Requer coverage.py |
| **Learning Curve** | 2/5 - Confuso |

**SCORE:** 7/25

**Decisão:** ❌ **NÃO USAR**

---

### Recomendação Final para Testing

```yaml
Unit Tests (pytest):
  - coverage_target: > 80%
  - fixtures: Para dados DICOM
  - mocking: Google Drive API

Integration Tests:
  - Docker containers
  - Real DICOM samples

E2E Tests:
  - Subset da pipeline real
  - 10-50 arquivos reais

Performance Tests:
  - Benchmarks baseline
  - 100, 1000, 10k arquivos
```

---

## 7. CI/CD Pipeline

### Recomendação

```yaml
GitHub Actions + Docker:
  
  on_push:
    - Linter (black, flake8)
    - Type checks (mypy)
    - Unit tests (pytest)
    - Coverage report
  
  on_pull_request:
    - Acima + integration tests
    - Build Docker image
  
  on_merge_to_main:
    - Acima + E2E tests
    - Deploy staging
    - Build production image
```

---

## 📊 Resumo de Decisões

| Componente | Escolha | Score | Fase |
|-----------|---------|-------|------|
| Conversão DICOM | dcm2niix | 47/50 | 3 |
| Google Drive | google-api-python-client | 42/50 | 3 |
| Paralelização | ThreadPool + ProcessPool | 48/50 | 3 |
| Logging | loguru | 44/50 | 3 |
| Error Handling | Custom exceptions + Circuit Breaker | 45/50 | 3 |
| Testing | pytest + pytest-cov | 25/25 | 3 |
| CI/CD | GitHub Actions + Docker | - | 4 |

---

**Todas as decisões estão registradas em PRD.yaml com justificativas detalhadas.**
