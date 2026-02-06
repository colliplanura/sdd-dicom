# 🏆 Boas Práticas para SDD-DICOM

## 1. Estrutura de Código

### ✅ Componentes Pequenos e Focados

Cada módulo tem uma responsabilidade clara:

```python
# ✅ BOM: Cada classe tem um propósito claro
class GoogleDriveClient:
    """Apenas interação com Google Drive"""
    def download_file(self, ...): pass
    def upload_file(self, ...): pass

class DIOMConverter:
    """Apenas conversão DICOM"""
    def convert(self, ...): pass

# ❌ RUIM: God object que faz tudo
class Processor:
    def auth_google_drive(self): pass
    def convert_dicom(self): pass
    def upload_results(self): pass
    def send_email(self): pass
    def update_database(self): pass
```

### ✅ Type Hints

```python
# ✅ BOM: Com type hints
def download_file(
    self,
    file_id: str,
    output_path: Path,
    timeout_seconds: int = 300
) -> bool:
    pass

# ❌ RUIM: Sem type hints
def download_file(self, file_id, output_path, timeout=300):
    pass
```

### ✅ Documentação

```python
# ✅ BOM: Docstring clara
def convert(
    self,
    input_dir: str,
    output_dir: str,
) -> Dict:
    """
    Converter série DICOM para NIfTI
    
    Args:
        input_dir: Diretório com arquivos DICOM
        output_dir: Diretório de saída
    
    Returns:
        Dict com {status, files} ou {status, error}
    """
    pass

# ❌ RUIM: Sem documentação
def convert(self, input_dir, output_dir):
    pass
```

---

## 2. Configuração

### ✅ Centralizada

```python
# ✅ BOM: Uma única fonte de verdade
class Config:
    MAX_WORKERS = os.getenv('MAX_WORKERS', 5)
    TIMEOUT_SECONDS = os.getenv('TIMEOUT', 300)

# Usar em todo o código
pipeline = BatchPipeline(max_workers=Config.MAX_WORKERS)
```

### ✅ Variáveis de Ambiente

```bash
# .env ou docker-compose
export MAX_WORKERS=5
export TIMEOUT=300
export LOG_LEVEL=INFO
export CREDENTIALS_PATH=./config/credentials.json
```

---

## 3. Logging

### ✅ Logging Estruturado

```python
# ✅ BOM: Com contexto
logger.info("Download iniciado", file_id=file_id, size_mb=size_mb)
logger.error("Falha no download", error=str(e), retry_count=attempt)

# ❌ RUIM: Sem contexto
logger.info(f"Fazendo download de {file_id}")
logger.error("Erro ao fazer download")
```

### ✅ Níveis Apropriados

```python
# DEBUG: Detalhes de execução
logger.debug("Rate limiter: waiting 0.2s")

# INFO: Eventos importantes
logger.info("✓ Download concluído")

# WARNING: Possíveis problemas
logger.warning("Timeout atingido, tentando retry")

# ERROR: Falhas
logger.error("Falha após 3 retries")
```

---

## 4. Tratamento de Erros

### ✅ Exceções Específicas

```python
# ✅ BOM: Exceções específicas
try:
    download_file(file_id)
except DownloadError:
    # Trata erro específico de download
    retry()
except AuthenticationError:
    # Autentica novamente
    pass

# ❌ RUIM: Exceção genérica
except Exception:
    pass
```

### ✅ Retry com Backoff

```python
# ✅ BOM: Retry automático com backoff
@retry_with_backoff(max_retries=3, backoff_factor=2)
def unreliable_operation():
    pass

# ❌ RUIM: Sem retry
def unreliable_operation():
    make_request()  # Pode falhar
```

---

## 5. Performance

### ✅ Paralelização Apropriada

```python
# ✅ BOM: I/O em threads, CPU em processos
with ThreadPoolExecutor(max_workers=5) as executor:
    # Download (I/O-bound)
    futures = [
        executor.submit(download_file, file_id)
        for file_id in file_ids
    ]

with ProcessPoolExecutor(max_workers=cpu_count()-2) as executor:
    # Conversão (CPU-bound)
    futures = [
        executor.submit(convert_dicom, input_path)
        for input_path in input_paths
    ]

# ❌ RUIM: Tudo em threads
for file_id in file_ids:
    download_file(file_id)  # Sequencial = lento
```

### ✅ Rate Limiting

```python
# ✅ BOM: Respeitar limite da API
limiter = RateLimiter(requests_per_second=5)

for file_id in file_ids:
    with limiter:
        api_request(file_id)

# ❌ RUIM: Sem rate limiting = pode levar a bans
for file_id in file_ids:
    api_request(file_id)  # 429 Too Many Requests
```

---

## 6. Testes

### ✅ Testar Componentes Isolados

```python
# ✅ BOM: Testar cada componente
def test_rate_limiter():
    limiter = RateLimiter(rps=5)
    # Testar behavior

def test_validator():
    validator = DIOMValidator()
    # Testar validação

# ❌ RUIM: Testar pipeline inteira
def test_everything():
    # Testa tudo junto = difícil debugar
```

### ✅ Usar Fixtures

```python
# ✅ BOM: Reutilizar setup
@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile() as f:
        yield f
        f.unlink()

def test_checksum(temp_file):
    checksum = calculate_checksum(temp_file)
    assert isinstance(checksum, str)
```

---

## 7. Deployment

### ✅ Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar dcm2niix
RUN apt-get update && apt-get install -y dcm2niix && rm -rf /var/lib/apt/lists/*

# Copiar código
COPY . .

# Executar
CMD ["python", "main.py", "--process"]
```

### ✅ .env.example

```env
# Google Drive
CREDENTIALS_PATH=./config/credentials.json
GD_FOLDER=Medicina/Doutorado IDOR/Exames/DICOM

# Processing
MAX_WORKERS_DL=5
MAX_WORKERS_PROC=6
TIMEOUT_DL=300
TIMEOUT_CONV=600

# Logging
LOG_LEVEL=INFO
LOG_FORMAT_JSON=false
```

---

## 8. Segurança

### ✅ Credenciais Seguras

```python
# ✅ BOM: Usar variáveis de ambiente
credentials_path = os.getenv('CREDENTIALS_PATH')

# ❌ RUIM: Hardcoded
credentials_path = './config/my-credentials.json'
# Então commitar no git!
```

### ✅ Validação de Input

```python
# ✅ BOM: Validar entrada
def download_file(file_id: str) -> bool:
    if not file_id or len(file_id) < 10:
        raise ValidationError("file_id inválido")

# ❌ RUIM: Sem validação
def download_file(file_id):
    # Pode causar erro no Google Drive
```

---

## 9. Monitoramento

### ✅ Métricas de Sucesso

```python
stats = {
    'total': 1000,
    'completed': 950,
    'failed': 30,
    'skipped': 20,
    'success_rate': 95.0,
    'duration': 180.5,
    'throughput': 5.3,  # files/second
}

logger.info("Pipeline stats", **stats)
```

---

## 10. Limpeza

### ✅ Cleanup de Recursos

```python
# ✅ BOM: Limpar recursos
try:
    pipeline.process_batch(tasks)
finally:
    clean_temp_directory(Config.TEMP_DIR)
    pipeline.close()

# ❌ RUIM: Deixar recursos abertos
pipeline.process_batch(tasks)
# Arquivos temporários ficam acumulando
```

---

## Checklist de Qualidade

- [ ] Código segue PEP 8
- [ ] Type hints em todas as funções públicas
- [ ] Docstrings em módulos, classes e funções
- [ ] Exceções específicas (não genéricas)
- [ ] Logging estruturado com contexto
- [ ] Retry com backoff para operações não-confiáveis
- [ ] Testes para componentes críticos
- [ ] Sem hardcoding de configurações
- [ ] Componentes podem ser testados isoladamente
- [ ] README.md e docs atualizados

---

**Próximo:** Deployment [../../README.md](../../README.md)
