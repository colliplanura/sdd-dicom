# 💻 Exemplos Práticos de Código

## 1. Exemplo Mínimo: Conectar ao Google Drive

```python
from src.google_drive import GoogleDriveClient

# Conectar (primeira vez pede permissão no navegador)
client = GoogleDriveClient(
    credentials_path='config/credentials.json'
)

# Listar primeiros 10 arquivos
files = client.list_files(
    folder_name='Medicina/Doutorado IDOR/Exames/DICOM',
    max_results=10
)

for f in files:
    print(f"- {f['name']} ({f['size']} bytes)")
```

---

## 2. Download de Arquivo

```python
from src.google_drive import GoogleDriveClient

client = GoogleDriveClient()

# Download simples
client.download_file(
    file_id='seu_file_id_aqui',
    output_path='local_file.dcm'
)
```

---

## 3. Conversão DICOM → NIfTI

```python
from src.dicom import DIOMConverter

converter = DIOMConverter()

# Converter pasta com DICOM
result = converter.convert(
    input_dir='/path/to/dicom',
    output_dir='/path/to/nifti',
    compress=True,        # .nii.gz
    bids=True,           # JSON sidecars
    timeout_seconds=600  # 10 minutos
)

if result['status'] == 'success':
    print(f"Arquivos gerados: {result['files']}")
else:
    print(f"Erro: {result['error']}")
```

---

## 4. Validação de Arquivos

```python
from src.dicom import DIOMValidator

validator = DIOMValidator()

# Validar DICOM
is_valid_dicom = validator.validate_dicom_file('file.dcm')

# Validar NIfTI
is_valid_nifti = validator.validate_nifti_file('file.nii.gz')

print(f"DICOM válido: {is_valid_dicom}")
print(f"NIfTI válido: {is_valid_nifti}")
```

---

## 5. Pipeline Completa

```python
from src.core import Config, setup_logging
from src.google_drive import GoogleDriveClient
from src.dicom import DIOMConverter
from src.pipeline import BatchPipeline, ProcessingTask

# Setup
Config.ensure_paths()
setup_logging()

# Componentes
client = GoogleDriveClient()
converter = DIOMConverter()

# Criar pipeline
pipeline = BatchPipeline(
    google_drive_client=client,
    dicom_converter=converter
)

# Listar arquivos
files = client.list_files(
    folder_name='Medicina/Doutorado IDOR/Exames/DICOM',
    max_results=100
)

# Criar tarefas
tasks = [
    ProcessingTask(
        file_id=f['id'],
        file_name=f['name'],
        patient_id=f"P{i:03d}",
        size_mb=f.get('size', 0) / (1024**2)
    )
    for i, f in enumerate(files, 1)
]

# Processar lote
results = pipeline.process_batch(tasks)

# Resultados
for r in results:
    print(f"{r['patient_id']}: {r['status']}")
```

---

## 6. Rate Limiting e Retry

```python
from src.google_drive import RateLimiter
from src.utils import retry_with_backoff

# Rate limiter
limiter = RateLimiter(requests_per_second=5)

# Usar em requisições
with limiter:
    # Fazer requisição para Google Drive
    pass

# Decorator para retry automático
@retry_with_backoff(max_retries=3, backoff_factor=2)
def my_operation():
    # Operação que pode falhar
    pass

try:
    my_operation()
except Exception:
    print("Falhou após 3 tentativas")
```

---

## 7. Logging Estruturado

```python
from loguru import logger
from src.core import setup_logging

# Setup de logging
setup_logging()

# Usar em qualquer lugar do código
logger.info("Operação iniciada", operation="download", file_id="123")
logger.debug("Detalhes", chunk=1024)
logger.warning("Possível problema", error_count=5)
logger.error("Falha crítica", exc_info=True)
```

---

## 8. Tratamento de Erros

```python
from src.core.exceptions import (
    GoogleDriveError,
    DIOMConversionError,
    ValidationError,
)

try:
    files = client.list_files(folder_name='Inexistente')
except GoogleDriveError as e:
    print(f"Erro Google Drive: {e}")

try:
    result = converter.convert(input_dir)
except DIOMConversionError as e:
    print(f"Erro na conversão: {e}")
```

---

## 9. Checksum e Validação

```python
from src.utils import calculate_checksum, validate_checksum
from pathlib import Path

# Calcular checksum
checksum = calculate_checksum(Path('file.dcm'), algorithm='md5')
print(f"Checksum: {checksum}")

# Validar checksum
is_valid = validate_checksum(
    Path('file.dcm'),
    expected_checksum='abc123...',
    algorithm='md5'
)
```

---

## 10. Circuit Breaker

```python
from src.utils import CircuitBreaker

# Criar circuit breaker
cb = CircuitBreaker(
    failure_threshold=5,
    timeout_seconds=60,
    success_threshold=2
)

def google_drive_operation():
    # Operação que pode falhar
    pass

try:
    result = cb.call(google_drive_operation)
except RuntimeError:
    print("Circuit breaker está OPEN - serviço indisponível")
```

---

**Próximo:** [BEST_PRACTICES.md](BEST_PRACTICES.md)
