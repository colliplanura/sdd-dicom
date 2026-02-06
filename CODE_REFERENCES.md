# Code References - Exemplos de Implementação Recomendada

**Data:** Fevereiro 2026  
**Status:** Exemplos de Referência (Fase 2 - Design)

---

## 1. Integração Google Drive API

### Exemplo Básico: Autenticação

```python
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from google.auth import default
import os

# Opção A: Service Account (RECOMENDADO para servidores)
def authenticate_service_account(credentials_path: str):
    """Autenticação com Service Account (sem interação)"""
    credentials = Credentials.from_service_account_file(
        credentials_path,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    service = build('drive', 'v3', credentials=credentials)
    return service

# Opção B: OAuth 2.0 (RECOMENDADO para usuários)
def authenticate_oauth():
    """Autenticação com OAuth 2.0 (primeira vez pede permissão)"""
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    
    SCOPES = ['https://www.googleapis.com/auth/drive']
    creds = None
    
    # Se existir token salvo, usar
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Se não, fazer login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Salvar token para próximas vezes
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    service = build('drive', 'v3', credentials=creds)
    return service
```

### Exemplo: Rate Limiting + Retry

```python
import time
import random
from functools import wraps
from typing import Callable, Any
from loguru import logger

class RateLimiter:
    """Implementar rate limiting (5-10 req/s)"""
    def __init__(self, requests_per_second: int = 5):
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
    
    def wait(self):
        """Aguardar se necessário"""
        elapsed = time.time() - self.last_request_time
        sleep_time = self.min_interval - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)
        self.last_request_time = time.time()

def retry_with_backoff(max_retries: int = 3):
    """Decorator para retry com exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed after {max_retries} attempts: {e}")
                        raise
                    
                    # Exponential backoff com jitter
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Attempt {attempt+1} failed, retrying in {wait_time:.2f}s: {e}")
                    time.sleep(wait_time)
        return wrapper
    return decorator

# Uso
rate_limiter = RateLimiter(requests_per_second=5)

@retry_with_backoff(max_retries=3)
def list_files_in_folder(service, folder_id: str):
    """Listar arquivos em pasta com rate limiting"""
    rate_limiter.wait()
    
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        pageSize=100,
        fields="files(id, name, size, mimeType, modifiedTime)"
    ).execute()
    
    return results.get('files', [])
```

### Exemplo: Download com Resume

```python
import os
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO
import hashlib

def download_file_with_resume(
    service,
    file_id: str,
    output_path: str,
    chunk_size: int = 1024*1024  # 1MB
):
    """Download com suporte a resume"""
    
    # Verificar se arquivo existe parcialmente
    resume_header = {}
    if os.path.exists(output_path):
        current_size = os.path.getsize(output_path)
        resume_header = {'Range': f'bytes={current_size}-'}
        logger.info(f"Resuming download from byte {current_size}")
    
    # Download
    request = service.files().get_media(fileId=file_id)
    
    with open(output_path, 'ab') as fh:
        downloader = MediaIoBaseDownload(
            fh,
            request,
            chunksize=chunk_size,
            resumable=True
        )
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                progress = 100 * status.progress()
                logger.info(f"Download progress: {progress:.1f}%")

def validate_checksum(file_path: str, expected_md5: str = None) -> bool:
    """Validar integridade com MD5"""
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5_hash.update(chunk)
    
    actual_md5 = md5_hash.hexdigest()
    
    if expected_md5 and actual_md5 != expected_md5:
        logger.error(f"Checksum mismatch: {actual_md5} != {expected_md5}")
        return False
    
    logger.info(f"Checksum validated: {actual_md5}")
    return True
```

---

## 2. Processamento DICOM com dcm2niix

### Exemplo: Wrapper Python

```python
import subprocess
import os
import json
from pathlib import Path
from typing import Optional, Dict
from loguru import logger

class DIOMConverter:
    """Wrapper para dcm2niix"""
    
    def __init__(self, dcm2niix_path: str = "dcm2niix"):
        """
        Inicializar converter
        
        Args:
            dcm2niix_path: Caminho para executável dcm2niix
        """
        self.dcm2niix_path = dcm2niix_path
        self._verify_installation()
    
    def _verify_installation(self) -> bool:
        """Verificar se dcm2niix está instalado"""
        try:
            result = subprocess.run(
                [self.dcm2niix_path, "-v"],
                capture_output=True,
                text=True,
                timeout=5
            )
            version = result.stdout.strip()
            logger.info(f"dcm2niix version: {version}")
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.error("dcm2niix not found or not accessible")
            return False
    
    def convert(
        self,
        input_dir: str,
        output_dir: str,
        output_filename_template: str = "%p_%t_%s",
        compress: bool = True,
        bids: bool = True,
        timeout: int = 300  # 5 minutos
    ) -> Optional[Dict]:
        """
        Converter série DICOM para NIfTI
        
        Args:
            input_dir: Diretório com arquivos DICOM
            output_dir: Diretório de saída
            output_filename_template: Template de nome (%p=patient, %t=time, %s=series)
            compress: Gerar .nii.gz (vs .nii)
            bids: Gerar sidecars JSON (BIDS)
            timeout: Timeout em segundos
        
        Returns:
            Dict com informações de output ou None se falhar
        """
        
        # Validar diretórios
        if not os.path.isdir(input_dir):
            logger.error(f"Input directory not found: {input_dir}")
            return None
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Construir comando
        cmd = [
            self.dcm2niix_path,
            "-f", output_filename_template,
            "-o", output_dir,
        ]
        
        if compress:
            cmd.append("-z")
            cmd.append("y")
        
        if bids:
            cmd.append("-b")
            cmd.append("y")
        
        cmd.append(input_dir)
        
        logger.info(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Conversion successful: {input_dir}")
                
                # Procurar outputs
                output_files = self._find_outputs(output_dir)
                return {
                    'status': 'success',
                    'files': output_files
                }
            else:
                logger.error(f"Conversion failed: {result.stderr}")
                return {
                    'status': 'error',
                    'error': result.stderr
                }
        
        except subprocess.TimeoutExpired:
            logger.error(f"Conversion timeout: {input_dir}")
            return {'status': 'timeout'}
        except Exception as e:
            logger.error(f"Conversion exception: {e}")
            return {'status': 'exception', 'error': str(e)}
    
    def _find_outputs(self, output_dir: str) -> Dict:
        """Encontrar arquivos gerados"""
        files = {}
        for ext in ['.nii.gz', '.nii', '.json', '.bvec', '.bval']:
            matches = list(Path(output_dir).glob(f'*{ext}'))
            if matches:
                files[ext] = [str(m) for m in matches]
        return files

# Uso
converter = DIOMConverter()
result = converter.convert(
    input_dir="/tmp/dicom_001",
    output_dir="/tmp/nifti_output",
    compress=True,
    bids=True
)
print(result)
```

---

## 3. Processamento Paralelo

### Exemplo: ThreadPool para Download + ProcessPool para Conversão

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import os
from pathlib import Path
from typing import List, Tuple
from loguru import logger
import tempfile

class ParallelPipeline:
    """Pipeline com execução paralela"""
    
    def __init__(
        self,
        download_workers: int = 5,
        conversion_workers: int = None,  # CPU count - 2
        upload_workers: int = 3
    ):
        import multiprocessing
        self.download_workers = download_workers
        self.conversion_workers = conversion_workers or max(1, multiprocessing.cpu_count() - 2)
        self.upload_workers = upload_workers
    
    def process_series_list(
        self,
        series_list: List[Tuple[str, str]],  # [(patient_id, series_id), ...]
        service,  # Google Drive service
        converter  # DIOMConverter instance
    ) -> List[Dict]:
        """
        Processar múltiplas séries em paralelo
        
        Args:
            series_list: Lista de (patient_id, series_id)
            service: Google Drive service
            converter: DIOMConverter instance
        
        Returns:
            Lista de resultados
        """
        
        results = []
        temp_root = tempfile.mkdtemp(prefix="dicom_conversion_")
        logger.info(f"Temp root: {temp_root}")
        
        try:
            # STAGE 1: Download paralelo
            logger.info(f"Stage 1: Downloading {len(series_list)} series...")
            download_tasks = {}
            
            with ThreadPoolExecutor(max_workers=self.download_workers) as executor:
                for patient_id, series_id in series_list:
                    future = executor.submit(
                        self._download_series,
                        service,
                        patient_id,
                        series_id,
                        temp_root
                    )
                    download_tasks[future] = (patient_id, series_id)
                
                for future in as_completed(download_tasks):
                    patient_id, series_id = download_tasks[future]
                    try:
                        local_path = future.result()
                        logger.info(f"✅ Downloaded: {patient_id}/{series_id}")
                    except Exception as e:
                        logger.error(f"❌ Download failed: {patient_id}/{series_id}: {e}")
            
            # STAGE 2: Conversão paralela
            logger.info(f"Stage 2: Converting series...")
            conversion_tasks = {}
            
            with ProcessPoolExecutor(max_workers=self.conversion_workers) as executor:
                for patient_id, series_id in series_list:
                    input_path = f"{temp_root}/{patient_id}/{series_id}"
                    if os.path.exists(input_path):
                        output_path = f"{temp_root}/nifti/{patient_id}"
                        
                        future = executor.submit(
                            self._convert_series,
                            converter,
                            input_path,
                            output_path
                        )
                        conversion_tasks[future] = (patient_id, series_id)
                
                for future in as_completed(conversion_tasks):
                    patient_id, series_id = conversion_tasks[future]
                    try:
                        result = future.result()
                        if result['status'] == 'success':
                            logger.info(f"✅ Converted: {patient_id}/{series_id}")
                            results.append(result)
                        else:
                            logger.error(f"❌ Conversion failed: {patient_id}/{series_id}")
                    except Exception as e:
                        logger.error(f"❌ Conversion exception: {patient_id}/{series_id}: {e}")
            
            # STAGE 3: Upload paralelo
            logger.info(f"Stage 3: Uploading {len(results)} files...")
            upload_tasks = {}
            
            with ThreadPoolExecutor(max_workers=self.upload_workers) as executor:
                for result in results:
                    if 'files' in result and '.nii.gz' in result['files']:
                        for nifti_file in result['files']['.nii.gz']:
                            future = executor.submit(
                                self._upload_file,
                                service,
                                nifti_file
                            )
                            upload_tasks[future] = nifti_file
                
                for future in as_completed(upload_tasks):
                    nifti_file = upload_tasks[future]
                    try:
                        file_id = future.result()
                        logger.info(f"✅ Uploaded: {Path(nifti_file).name}")
                    except Exception as e:
                        logger.error(f"❌ Upload failed: {nifti_file}: {e}")
        
        finally:
            # Cleanup
            import shutil
            logger.info(f"Cleaning up temporary files...")
            shutil.rmtree(temp_root, ignore_errors=True)
        
        return results
    
    def _download_series(self, service, patient_id: str, series_id: str, temp_root: str) -> str:
        """Download (será executado em ThreadPoolExecutor)"""
        # Implementar download com rate limiting
        pass
    
    def _convert_series(self, converter, input_path: str, output_path: str) -> dict:
        """Conversão (será executada em ProcessPoolExecutor)"""
        return converter.convert(input_path, output_path)
    
    def _upload_file(self, service, file_path: str) -> str:
        """Upload (será executado em ThreadPoolExecutor)"""
        # Implementar upload com rate limiting
        pass
```

---

## 4. Logging Estruturado com loguru

### Exemplo: Configuração Recomendada

```python
from loguru import logger
import sys

def setup_logging(log_level: str = "INFO", log_dir: str = "logs"):
    """Configurar logging com loguru"""
    
    import os
    os.makedirs(log_dir, exist_ok=True)
    
    # Remover logger padrão
    logger.remove()
    
    # Log para console (com cores)
    logger.add(
        sys.stderr,
        format="<level>{time:YYYY-MM-DD HH:mm:ss}</level> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )
    
    # Log para arquivo (sem cores, com rotação)
    logger.add(
        f"{log_dir}/conversion_{{time:YYYY-MM-DD}}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level=log_level,
        rotation="10 MB",  # Rotacionar ao atingir 10MB
        retention="30 days",  # Manter 30 dias
        compression="zip"  # Comprimir logs antigos
    )
    
    # Log JSON para integração com ELK (futuro)
    logger.add(
        f"{log_dir}/conversion_{{time:YYYY-MM-DD}}.json",
        format="{message}",
        level=log_level,
        rotation="100 MB",
        retention="14 days",
        serialize=True  # Saída em JSON
    )
    
    logger.info("Logging initialized")

# Uso
setup_logging(log_level="INFO")
logger.info("Starting DICOM conversion pipeline")
```

---

## 5. Tratamento de Erros Robusto

### Exemplo: Exceções Customizadas + Circuit Breaker

```python
from enum import Enum
from typing import Optional
import time

class ErrorSeverity(Enum):
    """Severidade de erro"""
    TEMPORARY = "temporary"  # Retry automático
    PERMANENT = "permanent"  # Skip + log
    FATAL = "fatal"  # Parar pipeline

class DICOMConversionError(Exception):
    """Base para erros de conversão DICOM"""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.PERMANENT,
        original_exception: Optional[Exception] = None
    ):
        self.message = message
        self.severity = severity
        self.original_exception = original_exception
        super().__init__(message)

class NetworkError(DICOMConversionError):
    """Erro de rede (retry automático)"""
    def __init__(self, message: str):
        super().__init__(message, ErrorSeverity.TEMPORARY)

class ConversionError(DICOMConversionError):
    """Erro de conversão (skip + log)"""
    def __init__(self, message: str):
        super().__init__(message, ErrorSeverity.PERMANENT)

class AuthenticationError(DICOMConversionError):
    """Erro de autenticação (fatal)"""
    def __init__(self, message: str):
        super().__init__(message, ErrorSeverity.FATAL)

class CircuitBreaker:
    """Circuit Breaker para Google Drive API"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        half_open_timeout: int = 300
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_timeout = half_open_timeout
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        """Executar função com circuit breaker"""
        
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.half_open_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker: HALF_OPEN (trying again)")
            else:
                raise DICOMConversionError(
                    "Circuit breaker is OPEN",
                    ErrorSeverity.TEMPORARY
                )
        
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise
    
    def _record_success(self):
        """Registrar sucesso"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _record_failure(self):
        """Registrar falha"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(f"Circuit breaker: OPEN (failures: {self.failure_count})")

# Uso
cb = CircuitBreaker(failure_threshold=5, timeout=60)

try:
    cb.call(list_files_in_folder, service, folder_id)
except NetworkError:
    logger.info("Temporary network error, will retry...")
except ConversionError:
    logger.warning("Conversion error, skipping this file...")
except AuthenticationError:
    logger.critical("Authentication failed, stopping pipeline!")
    raise
```

---

## 6. Exemplo Completo: Pipeline Mínima

```python
"""
main.py - Pipeline mínima DICOM to NIfTI
"""

import os
from pathlib import Path
from loguru import logger
from concurrent.futures import ThreadPoolExecutor
import tempfile

def main():
    """Pipeline mínima"""
    
    # Setup
    setup_logging("INFO")
    logger.info("Starting DICOM to NIfTI conversion pipeline")
    
    # Configuração
    DICOM_SOURCE = "Medicina/Doutorado IDOR/Exames/DICOM"
    NIFTI_DEST = "Medicina/Doutorado IDOR/Exames/NifTI"
    CREDENTIALS_FILE = "credentials.json"
    
    # Autenticar Google Drive
    logger.info("Authenticating with Google Drive...")
    service = authenticate_service_account(CREDENTIALS_FILE)
    
    # Inicializar converter
    converter = DIOMConverter()
    
    # Descobrir arquivos
    logger.info(f"Discovering DICOM files in {DICOM_SOURCE}...")
    series_list = discover_series(service, DICOM_SOURCE)
    logger.info(f"Found {len(series_list)} series")
    
    # Processar em paralelo
    with tempfile.TemporaryDirectory(prefix="dicom_") as temp_dir:
        logger.info(f"Using temp directory: {temp_dir}")
        
        pipeline = ParallelPipeline(
            download_workers=5,
            conversion_workers=None,  # auto
            upload_workers=3
        )
        
        results = pipeline.process_series_list(
            series_list,
            service,
            converter
        )
    
    # Relatório final
    logger.info(f"Pipeline complete: {len(results)} converted")
    
    # Estatísticas
    success_count = sum(1 for r in results if r.get('status') == 'success')
    logger.info(f"Success rate: {success_count}/{len(results)}")

if __name__ == "__main__":
    main()
```

---

## 📚 Referências para Implementação

- PyDICOM: https://pydicom.readthedocs.io/
- nibabel: https://nipy.org/nibabel/
- Google API Client: https://github.com/googleapis/google-api-python-client
- loguru: https://github.com/Delgan/loguru
- dcm2niix: https://github.com/rordenlab/dcm2niix

---

**Estes exemplos servem como referência. Código final será desenvolvido na Fase 3.**
