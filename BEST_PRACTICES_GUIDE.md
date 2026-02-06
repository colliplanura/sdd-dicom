# Guia Completo: Google Drive + Processamento em Lote em Python

## 1. INTEGRAÇÃO COM GOOGLE DRIVE EM PYTHON

### 1.1 Bibliotecas Recomendadas

| Biblioteca | Uso | Recomendação |
|-----------|-----|-------------|
| **google-api-python-client** | API oficial do Google Drive | ⭐⭐⭐⭐⭐ Melhor opção |
| **google-auth-oauthlib** | Autenticação OAuth 2.0 | ⭐⭐⭐⭐⭐ Necessária |
| **google-auth-httplib2** | Transport HTTP para autenticação | ⭐⭐⭐⭐⭐ Necessária |
| **PyDrive2** | Wrapper simplificado | ⭐⭐⭐ Para casos simples |
| **google-cloud-storage** | Integração com Cloud Storage | ⭐⭐⭐⭐ Para grandes volumes |

### 1.2 Instalação

```bash
# Opção 1: Google API Client (Recomendado)
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2

# Opção 2: Completo com suporte a Cloud Storage
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2 google-cloud-storage
```

### 1.3 Autenticação e Gerenciamento de Credenciais

#### A. Fluxo OAuth 2.0 (Aplicações Desktop/Web)

```python
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Escopos: https://developers.google.com/drive/scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive',  # Acesso completo
    # ou
    'https://www.googleapis.com/auth/drive.file',  # Apenas arquivos criados pela app
    'https://www.googleapis.com/auth/drive.readonly',  # Apenas leitura
]

class GoogleDriveAuth:
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds = None
    
    def authenticate(self):
        """Realiza autenticação e cria/atualiza token"""
        # Carrega token existente
        if os.path.exists(self.token_file):
            self.creds = Credentials.from_authorized_user_file(
                self.token_file, SCOPES
            )
        
        # Se não há credenciais válidas, faz login
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                # Renova token expirado
                self.creds.refresh(Request())
            else:
                # Fluxo de autenticação inicial
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            
            # Salva credenciais para próxima execução
            with open(self.token_file, 'w') as token:
                token.write(self.creds.to_json())
        
        return self.creds
    
    def get_service(self):
        """Retorna o serviço autenticado do Google Drive"""
        if not self.creds:
            self.authenticate()
        return build('drive', 'v3', credentials=self.creds)

# Uso
auth = GoogleDriveAuth()
service = auth.get_service()
```

**Prós e Contras:**
- ✅ Seguro (credenciais armazenadas localmente)
- ✅ Autorização de primeiro acesso com UI
- ❌ Requer interaction do usuário na primeira execução
- ⚠️ Token pode expirar e precisa ser renovado

#### B. Autenticação com Service Account (Servidores/Automação)

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

class GoogleDriveServiceAccount:
    def __init__(self, service_account_file='service-account.json'):
        self.service_account_file = service_account_file
        self.creds = None
    
    def authenticate(self):
        """Autentica usando Service Account"""
        self.creds = service_account.Credentials.from_service_account_file(
            self.service_account_file,
            scopes=SCOPES
        )
        return self.creds
    
    def get_service(self):
        if not self.creds:
            self.authenticate()
        return build('drive', 'v3', credentials=self.creds)

# Uso em servidores
auth = GoogleDriveServiceAccount()
service = auth.get_service()
```

**Prós e Contras:**
- ✅ Totalmente automático (sem interação)
- ✅ Ideal para servidores/automação
- ❌ Requer arquivo JSON com credenciais
- ❌ Credenciais devem ser protegidas

### 1.4 Download/Upload Automatizado

#### A. Download de Arquivos

```python
import io
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

class GoogleDriveDownloader:
    def __init__(self, service):
        self.service = service
    
    def download_file(self, file_id, output_path):
        """Download de um arquivo individual"""
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.FileIO(output_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"Download {int(status.progress() * 100)}%")
            
            print(f"✓ Arquivo baixado: {output_path}")
            return True
        except HttpError as error:
            print(f"✗ Erro ao baixar arquivo: {error}")
            return False
    
    def download_folder(self, folder_id, output_dir):
        """Download recursivo de pasta"""
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Lista arquivos na pasta
            results = self.service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                spaces='drive',
                fields='files(id, name, mimeType)',
                pageSize=1000
            ).execute()
            
            items = results.get('files', [])
            
            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # Recursão para subpastas
                    subfolder_path = os.path.join(output_dir, item['name'])
                    self.download_folder(item['id'], subfolder_path)
                else:
                    # Download do arquivo
                    file_path = os.path.join(output_dir, item['name'])
                    self.download_file(item['id'], file_path)
            
            return True
        except HttpError as error:
            print(f"✗ Erro ao baixar pasta: {error}")
            return False

# Uso
service = auth.get_service()
downloader = GoogleDriveDownloader(service)

# Download de arquivo único
downloader.download_file('file_id_aqui', 'local_path.pdf')

# Download de pasta completa
downloader.download_folder('folder_id_aqui', './downloads')
```

#### B. Upload de Arquivos

```python
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload

class GoogleDriveUploader:
    def __init__(self, service):
        self.service = service
    
    def upload_file(self, file_path, parent_folder_id=None, mime_type=None):
        """Upload de um arquivo"""
        try:
            file_name = os.path.basename(file_path)
            
            file_metadata = {'name': file_name}
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
            
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            
            request = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, size'
            )
            
            # Upload resumível para arquivos grandes
            response = None
            while response is None:
                try:
                    status, response = request.next_chunk()
                    if status:
                        print(f"Upload {int(status.progress() * 100)}%")
                except HttpError as error:
                    print(f"Erro no upload: {error}")
                    return None
            
            print(f"✓ Arquivo enviado: {response['name']} (ID: {response['id']})")
            return response['id']
        except Exception as error:
            print(f"✗ Erro ao enviar arquivo: {error}")
            return None
    
    def upload_folder(self, local_dir, parent_folder_id=None):
        """Upload recursivo de pasta"""
        uploaded_ids = []
        
        for root, dirs, files in os.walk(local_dir):
            # Cria pastas no Drive
            for dir_name in dirs:
                local_path = os.path.join(root, dir_name)
                folder_id = self.create_folder(dir_name, parent_folder_id)
                if folder_id:
                    uploaded_ids.append(folder_id)
                    # Upload recursivo dos arquivos na subpasta
                    self.upload_folder(local_path, folder_id)
            
            # Upload dos arquivos
            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_id = self.upload_file(file_path, parent_folder_id)
                if file_id:
                    uploaded_ids.append(file_id)
        
        return uploaded_ids
    
    def create_folder(self, folder_name, parent_folder_id=None):
        """Cria pasta no Drive"""
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            return folder['id']
        except HttpError as error:
            print(f"✗ Erro ao criar pasta: {error}")
            return None

# Uso
uploader = GoogleDriveUploader(service)

# Upload de arquivo único
file_id = uploader.upload_file('local_file.pdf', parent_folder_id='folder_id')

# Upload de pasta completa
uploader.upload_folder('./local_folder', parent_folder_id='parent_id')
```

### 1.5 Tratamento de Grandes Volumes

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class GoogleDriveBatchProcessor:
    def __init__(self, service, max_workers=5):
        self.service = service
        self.max_workers = max_workers
        self.rate_limiter = RateLimiter(requests_per_second=10)
    
    def batch_download(self, file_ids, output_dir, max_retries=3):
        """Download paralelo com controle de taxa"""
        downloader = GoogleDriveDownloader(self.service)
        results = {'success': [], 'failed': []}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            for file_id in file_ids:
                self.rate_limiter.wait()  # Respeita rate limit
                future = executor.submit(
                    self._download_with_retry,
                    downloader,
                    file_id,
                    output_dir,
                    max_retries
                )
                futures[future] = file_id
            
            for future in as_completed(futures):
                file_id = futures[future]
                try:
                    success = future.result()
                    if success:
                        results['success'].append(file_id)
                    else:
                        results['failed'].append(file_id)
                except Exception as e:
                    print(f"Erro ao processar {file_id}: {e}")
                    results['failed'].append(file_id)
        
        return results
    
    def _download_with_retry(self, downloader, file_id, output_dir, max_retries):
        """Download com retry automático"""
        for attempt in range(max_retries):
            try:
                # Obter metadados do arquivo
                file_metadata = self.service.files().get(
                    fileId=file_id,
                    fields='name'
                ).execute()
                
                output_path = os.path.join(output_dir, file_metadata['name'])
                return downloader.download_file(file_id, output_path)
            except HttpError as e:
                if e.resp.status == 429:  # Rate limit
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Rate limit atingido. Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                elif attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return False
        
        return False

# Rate Limiter
class RateLimiter:
    def __init__(self, requests_per_second=10):
        self.requests_per_second = requests_per_second
        self.last_request = time.time()
    
    def wait(self):
        elapsed = time.time() - self.last_request
        min_interval = 1.0 / self.requests_per_second
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self.last_request = time.time()

# Uso
processor = GoogleDriveBatchProcessor(service, max_workers=5)
results = processor.batch_download(
    file_ids=['id1', 'id2', 'id3', ...],
    output_dir='./downloads'
)
print(f"Sucesso: {len(results['success'])}, Falhas: {len(results['failed'])}")
```

---

## 2. PROCESSAMENTO EM LOTE (BATCH PROCESSING)

### 2.1 Comparação: Threading vs Multiprocessing vs Asyncio

| Aspecto | Threading | Multiprocessing | Asyncio |
|--------|-----------|-----------------|---------|
| **GIL** | Bloqueado ❌ | Livre ✅ | N/A ✅ |
| **CPU-bound** | ❌ Ruim | ✅ Excelente | ❌ Ruim |
| **I/O-bound** | ✅ Ótimo | ⚠️ Overhead | ✅ Ótimo |
| **Overhead** | Baixo | Alto | Muito baixo |
| **Simplicidade** | ✅ Simples | ⚠️ Média | ⚠️ Complexa |
| **Compartilhamento de dados** | ✅ Fácil | ❌ Difícil | ✅ Fácil |
| **Escalabilidade** | ~100 threads | ~CPUs × 4 | 1000s coroutines |

### 2.2 Implementações Práticas

#### A. ThreadPoolExecutor (Para I/O - Recomendado para Google Drive)

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from loguru import logger

class BatchProcessorThreads:
    def __init__(self, max_workers=5):
        self.max_workers = max_workers
    
    def process_batch(self, items, process_func):
        """Processa itens em paralelo com ThreadPoolExecutor"""
        results = {'success': [], 'failed': []}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submeter todas as tarefas
            futures = {
                executor.submit(process_func, item): item 
                for item in items
            }
            
            # Processar resultados conforme completam
            for future in as_completed(futures):
                item = futures[future]
                try:
                    result = future.result(timeout=30)
                    results['success'].append(result)
                    logger.info(f"✓ Processado: {item}")
                except TimeoutError:
                    results['failed'].append(item)
                    logger.error(f"✗ Timeout: {item}")
                except Exception as e:
                    results['failed'].append(item)
                    logger.error(f"✗ Erro em {item}: {e}")
        
        return results
    
    def process_batch_with_progress(self, items, process_func):
        """Versão com barra de progresso"""
        from tqdm import tqdm
        results = {'success': [], 'failed': []}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(process_func, item): item 
                for item in items
            }
            
            # Usar tqdm para progresso
            for future in tqdm(as_completed(futures), total=len(items)):
                item = futures[future]
                try:
                    result = future.result(timeout=30)
                    results['success'].append(result)
                except Exception as e:
                    results['failed'].append(item)
                    logger.error(f"Erro: {e}")
        
        return results

# Uso
processor = BatchProcessorThreads(max_workers=5)

def download_and_process_file(file_id):
    """Função de processamento"""
    # Simular download e processamento
    logger.info(f"Iniciando processamento de {file_id}")
    time.sleep(2)  # Simular I/O
    return {'id': file_id, 'status': 'processed'}

results = processor.process_batch(
    items=['file1', 'file2', 'file3'],
    process_func=download_and_process_file
)
```

**Prós:**
- ✅ Ideal para I/O-bound (Google Drive API calls)
- ✅ Simples de implementar
- ✅ Suporta timeout
- ✅ Compartilhamento de dados fácil

**Contras:**
- ❌ Não paraleliza CPU-bound
- ❌ Limitado a ~100 threads

#### B. ProcessPoolExecutor (Para CPU-Bound)

```python
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

class BatchProcessorProcesses:
    def __init__(self, max_workers=None):
        # Usa número de CPUs por padrão
        self.max_workers = max_workers or multiprocessing.cpu_count()
    
    def process_batch(self, items, process_func):
        """Processa itens com ProcessPoolExecutor"""
        results = {'success': [], 'failed': []}
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(process_func, item): item 
                for item in items
            }
            
            for future in as_completed(futures):
                item = futures[future]
                try:
                    result = future.result(timeout=300)
                    results['success'].append(result)
                    logger.info(f"✓ Processado: {item}")
                except Exception as e:
                    results['failed'].append(item)
                    logger.error(f"✗ Erro em {item}: {e}")
        
        return results

def cpu_intensive_task(data):
    """Deve ser picklable (sem lambdas, métodos internos, etc)"""
    # Processamento pesado (e.g., análise de imagem DICOM)
    result = sum(data) * 2
    return result

# Uso
processor = BatchProcessorProcesses()
results = processor.process_batch(
    items=[[1, 2, 3], [4, 5, 6], [7, 8, 9]],
    process_func=cpu_intensive_task
)
```

**Prós:**
- ✅ True parallelism (múltiplos CPUs)
- ✅ Ideal para CPU-bound
- ✅ Bom para volumes muito grandes

**Contras:**
- ❌ Overhead de criação de processos
- ❌ Serialização de dados (lento com grandes objetos)
- ❌ Compartilhamento de dados difícil
- ❌ Função deve ser picklable

#### C. Asyncio (Para muitos I/O concorrentes)

```python
import asyncio
from aiohttp import ClientSession
import aiofiles

class BatchProcessorAsync:
    def __init__(self, max_concurrent=10):
        self.max_concurrent = max_concurrent
    
    async def process_batch(self, items, process_func):
        """Processa itens com Asyncio"""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def bounded_process(item):
            async with semaphore:
                try:
                    result = await process_func(item)
                    logger.info(f"✓ Processado: {item}")
                    return result
                except Exception as e:
                    logger.error(f"✗ Erro em {item}: {e}")
                    raise
        
        # Executar todas as tarefas
        tasks = [bounded_process(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success = [r for r in results if not isinstance(r, Exception)]
        failed = [r for r in results if isinstance(r, Exception)]
        
        return {'success': success, 'failed': failed}
    
    def run(self, items, process_func):
        """Wrapper para usar em código síncrono"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.process_batch(items, process_func))

# Uso com função async
async def async_download_file(file_id):
    """Simula download assíncrono"""
    logger.info(f"Iniciando {file_id}")
    await asyncio.sleep(2)  # Simula I/O
    return {'id': file_id, 'status': 'ok'}

processor = BatchProcessorAsync(max_concurrent=10)
results = processor.run(
    items=['file1', 'file2', 'file3'],
    process_func=async_download_file
)
```

**Prós:**
- ✅ Altamente escalável (1000s de tarefas)
- ✅ Overhead muito baixo
- ✅ Ideal para muitos I/O concorrentes

**Contras:**
- ❌ Código mais complexo
- ❌ Requer funções async
- ❌ Debugging mais difícil

### 2.3 Frameworks Recomendados

#### A. Celery (Para sistemas distribuídos)

```python
from celery import Celery, group, chain, chord
from celery.result import AsyncResult
import time

# Configurar Celery com Redis
app = Celery(
    'drive_processor',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos
)

@app.task(bind=True, max_retries=3)
def download_file_task(self, file_id):
    """Tarefa de download com retry automático"""
    try:
        logger.info(f"Baixando {file_id}")
        # Lógica de download
        time.sleep(2)
        return {'file_id': file_id, 'status': 'success'}
    except Exception as exc:
        logger.error(f"Erro em {file_id}: {exc}")
        # Retry com backoff exponencial
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

@app.task(bind=True)
def process_file_task(self, file_data):
    """Tarefa de processamento"""
    logger.info(f"Processando {file_data['file_id']}")
    # Lógica de processamento
    return {'status': 'processed'}

# Usar pipeline de tarefas
def batch_process_pipeline(file_ids):
    """Pipeline: download -> process"""
    # Executar downloads em paralelo
    download_tasks = group(
        download_file_task.s(file_id) for file_id in file_ids
    )
    
    # Depois processar resultados
    pipeline = chord(download_tasks)(process_file_task.s())
    
    return pipeline.id

# Monitorar progresso
result_id = batch_process_pipeline(['id1', 'id2', 'id3'])
result = AsyncResult(result_id)
print(result.state)  # PENDING, PROGRESS, SUCCESS, FAILURE
print(result.result)
```

**Prós:**
- ✅ Distribuído e escalável
- ✅ Retry automático
- ✅ Agendamento de tarefas
- ✅ Pipeline de processamento

**Contras:**
- ❌ Overhead (requer broker Redis/RabbitMQ)
- ❌ Complexidade maior
- ❌ Overhead para pequenos volumes

#### B. Dask (Para processamento paralelo simples)

```python
import dask
from dask import delayed
import dask.dataframe as dd

class DaskBatchProcessor:
    def __init__(self, n_workers=4):
        self.n_workers = n_workers
    
    def process_batch_delayed(self, items, process_func):
        """Usar delayed para lazy evaluation"""
        # Criar tarefas delayed
        tasks = [delayed(process_func)(item) for item in items]
        
        # Computar em paralelo
        results = dask.compute(*tasks, num_workers=self.n_workers)
        
        return results
    
    def process_with_dataframe(self, data_dict, process_func):
        """Processar com Dask DataFrame"""
        df = dd.from_dict(data_dict, npartitions=4)
        
        result = df.map_partitions(
            lambda partition: partition.apply(process_func, axis=1)
        ).compute()
        
        return result

# Uso
processor = DaskBatchProcessor(n_workers=4)

@delayed
def process_item(item):
    logger.info(f"Processando {item}")
    time.sleep(1)
    return item * 2

results = processor.process_batch_delayed(
    items=[1, 2, 3, 4, 5],
    process_func=process_item
)
```

**Prós:**
- ✅ Simples de usar
- ✅ Escalável
- ✅ Bom para arrays/dataframes

**Contras:**
- ❌ Menos controle fino
- ❌ Overhead moderado

#### C. Ray (Para ML/Data Science)

```python
import ray

@ray.remote
def process_file(file_id):
    """Tarefa remota Ray"""
    logger.info(f"Ray processando {file_id}")
    time.sleep(1)
    return {'file_id': file_id, 'status': 'ok'}

# Inicializar Ray
ray.init(num_cpus=4)

# Executar tarefas
futures = [process_file.remote(f"file_{i}") for i in range(10)]
results = ray.get(futures)

ray.shutdown()
```

**Prós:**
- ✅ Otimizado para ML
- ✅ Distribuição automática
- ✅ Muito escalável

**Contras:**
- ❌ Overkill para casos simples
- ❌ Curva de aprendizado

### 2.4 Recomendação por Caso de Uso

```python
# GOOGLE DRIVE + DICOM + 100-1000 arquivos
# ✅ MELHOR: ThreadPoolExecutor + loguru
from concurrent.futures import ThreadPoolExecutor

processor = ThreadPoolExecutor(max_workers=5)  # API limits

# DICOM + 1000+ arquivos com processamento CPU
# ✅ MELHOR: ProcessPoolExecutor
from concurrent.futures import ProcessPoolExecutor

processor = ProcessPoolExecutor(max_workers=cpu_count())

# Processamento distribuído (múltiplas máquinas)
# ✅ MELHOR: Celery + Redis
from celery import Celery

app = Celery('app', broker='redis://localhost')

# Muitos I/O concorrentes (10000+)
# ✅ MELHOR: Asyncio
import asyncio

asyncio.run(main())
```

---

## 3. GESTÃO DE RECURSOS

### 3.1 Limites de Rate Limiting do Google Drive

```python
"""
Limites oficiais Google Drive API:
- 1,000,000,000 queries/dia (quase ilimitado)
- ~10 requisições/segundo por usuário
- ~100 requisições/segundo por aplicação
"""

class GoogleDriveRateLimiter:
    def __init__(self, requests_per_second=10):
        self.rps = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
    
    def wait(self):
        """Aguarda se necessário para respeitar limite"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()
    
    def __call__(self, func):
        """Decorator para aplicar rate limit"""
        def wrapper(*args, **kwargs):
            self.wait()
            return func(*args, **kwargs)
        return wrapper

# Usar como decorator
rate_limiter = GoogleDriveRateLimiter(requests_per_second=5)

@rate_limiter
def api_call():
    # Faz chamada à API
    pass

# Ou manualmente
rate_limiter = GoogleDriveRateLimiter()
for file_id in file_ids:
    rate_limiter.wait()
    download_file(file_id)
```

### 3.2 Estratégias de Cache

```python
import pickle
import hashlib
from datetime import datetime, timedelta

class FileMetadataCache:
    def __init__(self, cache_dir='./.cache', ttl_hours=24):
        self.cache_dir = cache_dir
        self.ttl = timedelta(hours=ttl_hours)
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_cache_key(self, folder_id):
        """Gera chave de cache única"""
        return hashlib.md5(folder_id.encode()).hexdigest()
    
    def get_cache_path(self, folder_id):
        return os.path.join(self.cache_dir, f"{self.get_cache_key(folder_id)}.pkl")
    
    def get(self, folder_id):
        """Obtém metadados do cache se válido"""
        cache_path = self.get_cache_path(folder_id)
        
        if os.path.exists(cache_path):
            # Verificar se expirou
            mtime = os.path.getmtime(cache_path)
            if datetime.now() - datetime.fromtimestamp(mtime) < self.ttl:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
        
        return None
    
    def set(self, folder_id, data):
        """Armazena metadados em cache"""
        cache_path = self.get_cache_path(folder_id)
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
    
    def invalidate(self, folder_id):
        """Remove cache específico"""
        cache_path = self.get_cache_path(folder_id)
        if os.path.exists(cache_path):
            os.remove(cache_path)

# Uso
cache = FileMetadataCache(ttl_hours=24)

def list_files_cached(service, folder_id):
    # Verificar cache
    cached = cache.get(folder_id)
    if cached:
        logger.info("✓ Usando cache")
        return cached
    
    # Buscar da API
    logger.info("→ Buscando da API...")
    results = service.files().list(
        q=f"'{folder_id}' in parents",
        fields='files(id, name, size)',
        pageSize=1000
    ).execute()
    
    files = results.get('files', [])
    cache.set(folder_id, files)
    return files
```

### 3.3 Limpeza de Arquivos Temporários

```python
import shutil
from pathlib import Path

class TemporaryFileManager:
    def __init__(self, temp_dir='./temp', max_age_hours=24):
        self.temp_dir = temp_dir
        self.max_age = timedelta(hours=max_age_hours)
        os.makedirs(temp_dir, exist_ok=True)
    
    def cleanup_old_files(self):
        """Remove arquivos temporários antigos"""
        now = datetime.now()
        removed_count = 0
        
        for file_path in Path(self.temp_dir).iterdir():
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if now - mtime > self.max_age:
                try:
                    if file_path.is_dir():
                        shutil.rmtree(file_path)
                    else:
                        file_path.unlink()
                    logger.info(f"Removido: {file_path}")
                    removed_count += 1
                except Exception as e:
                    logger.error(f"Erro ao remover {file_path}: {e}")
        
        logger.info(f"Limpeza: {removed_count} arquivos removidos")
        return removed_count
    
    def cleanup_on_error(self, file_path):
        """Remove arquivo em caso de erro"""
        try:
            Path(file_path).unlink()
            logger.info(f"Removido após erro: {file_path}")
        except Exception as e:
            logger.warning(f"Não foi possível remover {file_path}: {e}")

# Agendar limpeza periódica
from apscheduler.schedulers.background import BackgroundScheduler

def setup_cleanup_scheduler():
    scheduler = BackgroundScheduler()
    temp_manager = TemporaryFileManager()
    
    scheduler.add_job(
        temp_manager.cleanup_old_files,
        'interval',
        hours=1,
        id='cleanup_temp_files'
    )
    
    scheduler.start()
    return scheduler
```

---

## 4. MONITORAMENTO E LOGGING

### 4.1 Configuração Loguru (Recomendado)

```python
from loguru import logger
import sys

# Remover handler padrão
logger.remove()

# Adicionar logger para console
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
    colorize=True
)

# Adicionar logger para arquivo
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="500 MB",  # Rotaciona ao atingir 500MB
    retention="10 days",  # Mantém últimos 10 dias
    compression="zip"  # Comprime arquivos antigos
)

# Adicionar logger estruturado para erros
logger.add(
    "logs/errors_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="ERROR",
    rotation="daily"
)

# Uso
logger.debug("Mensagem de debug")
logger.info("Operação iniciada")
logger.warning("Aviso importante")
logger.error("Erro ocorreu")
logger.critical("Erro crítico")

# Com contexto
with logger.contextualize(request_id="12345", user="admin"):
    logger.info("Processando requisição")  # Incluirá contexto nos logs
```

**Prós:**
- ✅ Muito mais simples que logging padrão
- ✅ Formatação bonita
- ✅ Rotação automática
- ✅ Contexto estruturado
- ✅ Async-safe

**Contras:**
- ❌ Dependency adicional
- ❌ Menos histórico que logging padrão

### 4.2 Logging Estruturado para Batch Processing

```python
from loguru import logger
import json
from datetime import datetime

class BatchLogger:
    def __init__(self, batch_id, log_file='batch_log.jsonl'):
        self.batch_id = batch_id
        self.log_file = log_file
        self.start_time = datetime.now()
    
    def log_task_start(self, task_id, description):
        """Log estruturado de início de tarefa"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'batch_id': self.batch_id,
            'event': 'task_start',
            'task_id': task_id,
            'description': description
        }
        logger.info(json.dumps(event))
        self._write_to_file(event)
    
    def log_task_complete(self, task_id, status, duration, result=None):
        """Log estruturado de conclusão de tarefa"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'batch_id': self.batch_id,
            'event': 'task_complete',
            'task_id': task_id,
            'status': status,
            'duration_seconds': duration,
            'result': result
        }
        logger.info(json.dumps(event))
        self._write_to_file(event)
    
    def log_batch_summary(self, total, success, failed, duration):
        """Log resumo do batch"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'batch_id': self.batch_id,
            'event': 'batch_complete',
            'total_tasks': total,
            'successful': success,
            'failed': failed,
            'success_rate': success / total * 100 if total > 0 else 0,
            'duration_seconds': duration
        }
        logger.info(json.dumps(summary))
        self._write_to_file(summary)
    
    def _write_to_file(self, event):
        """Escreve evento em arquivo JSONL"""
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(event) + '\n')

# Uso
batch_logger = BatchLogger(batch_id="batch_001")

import time
start = time.time()
batch_logger.log_task_start('task_1', 'Baixando arquivo X')
time.sleep(2)
batch_logger.log_task_complete('task_1', 'success', time.time() - start)

# Resumo
batch_logger.log_batch_summary(
    total=100,
    success=95,
    failed=5,
    duration=120
)
```

### 4.3 Notificações de Erro

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger

class ErrorNotifier:
    def __init__(self, smtp_server, sender_email, sender_password, recipient_emails):
        self.smtp_server = smtp_server
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.recipients = recipient_emails
    
    def send_error_notification(self, subject, error_details, batch_id=None):
        """Envia notificação de erro por email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(self.recipients)
            msg['Subject'] = f"[ERRO] {subject}"
            
            # Corpo do email
            body = f"""
            Erro Detectado em Processamento em Lote
            
            Batch ID: {batch_id or 'N/A'}
            Assunto: {subject}
            Timestamp: {datetime.now().isoformat()}
            
            Detalhes do Erro:
            {error_details}
            
            Por favor, verifique os logs para mais informações.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Enviar
            with smtplib.SMTP(self.smtp_server, 587) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"✓ Notificação de erro enviada")
        except Exception as e:
            logger.error(f"✗ Falha ao enviar notificação: {e}")
    
    def send_batch_summary(self, summary):
        """Envia resumo do batch após conclusão"""
        # Similar ao send_error_notification
        pass

# Usar com handler de exceção
notifier = ErrorNotifier(
    smtp_server='smtp.gmail.com',
    sender_email='seu_email@gmail.com',
    sender_password='sua_senha_de_app',
    recipient_emails=['admin@empresa.com', 'ops@empresa.com']
)

def process_with_notification(batch_id, items, process_func):
    try:
        # Processamento...
        pass
    except Exception as e:
        notifier.send_error_notification(
            subject="Falha no Processamento",
            error_details=str(e),
            batch_id=batch_id
        )
        raise
```

### 4.4 Exemplo Completo Integrado

```python
from loguru import logger
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from datetime import datetime

# Configurar logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/batch_{time:YYYY-MM-DD}.log", level="DEBUG")

class DicomProcessingPipeline:
    def __init__(self, service, max_workers=5):
        self.service = service
        self.max_workers = max_workers
        self.auth = GoogleDriveAuth()
        self.batch_logger = BatchLogger(batch_id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.notifier = ErrorNotifier(...)
    
    def process_batch(self, folder_id):
        """Pipeline completo com logging estruturado"""
        batch_start = time.time()
        
        try:
            # 1. Listar arquivos
            logger.info(f"Iniciando processamento da pasta: {folder_id}")
            files = self._list_files(folder_id)
            logger.info(f"✓ {len(files)} arquivos encontrados")
            
            # 2. Download em paralelo
            logger.info("Iniciando downloads em paralelo...")
            downloaded_files = self._parallel_download(files)
            
            # 3. Processar DICOM
            logger.info("Iniciando processamento DICOM...")
            results = self._process_dicom_files(downloaded_files)
            
            # 4. Log resumo
            duration = time.time() - batch_start
            success_count = len([r for r in results if r['status'] == 'success'])
            
            self.batch_logger.log_batch_summary(
                total=len(files),
                success=success_count,
                failed=len(files) - success_count,
                duration=duration
            )
            
            logger.info(f"✓ Batch concluído em {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"✗ Erro no batch: {e}", exc_info=True)
            self.notifier.send_error_notification(
                subject="Falha no Processamento DICOM",
                error_details=str(e),
                batch_id=self.batch_logger.batch_id
            )
            raise
    
    def _parallel_download(self, files):
        """Download paralelo com logging"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._download_file, f): f['id']
                for f in files
            }
            
            for future in as_completed(futures):
                file_id = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.debug(f"✓ Downloaded: {file_id}")
                except Exception as e:
                    logger.error(f"✗ Download falhou: {file_id} - {e}")
                    results.append({'id': file_id, 'status': 'failed'})
        
        return results
    
    def _download_file(self, file_info):
        """Download individual com timing"""
        start = time.time()
        try:
            # Lógica de download
            self.batch_logger.log_task_start(file_info['id'], f"Baixando {file_info['name']}")
            # ... download logic ...
            duration = time.time() - start
            self.batch_logger.log_task_complete(file_info['id'], 'success', duration)
            return {'id': file_info['id'], 'status': 'success'}
        except Exception as e:
            logger.error(f"Erro ao baixar {file_info['id']}: {e}")
            return {'id': file_info['id'], 'status': 'failed', 'error': str(e)}
```

---

## 5. EXEMPLO FINAL COMPLETO

```python
"""
Sistema completo de processamento de DICOM do Google Drive
"""

import os
import sys
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json

from loguru import logger
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

# ===== CONFIGURAÇÃO DE LOGGING =====
logger.remove()
logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>", level="INFO")
logger.add("logs/pipeline_{time:YYYY-MM-DD}.log", level="DEBUG", rotation="500 MB", retention="7 days")

# ===== CLASSES PRINCIPAIS =====

class GoogleDriveManager:
    """Gerenciador de Google Drive com autenticação e operações"""
    
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds = None
        self.service = None
    
    def authenticate(self):
        """Autentica com Google Drive API"""
        if os.path.exists(self.token_file):
            self.creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open(self.token_file, 'w') as token:
                token.write(self.creds.to_json())
        
        self.service = build('drive', 'v3', credentials=self.creds)
        logger.info("✓ Autenticado no Google Drive")
        return self.service
    
    def list_files(self, folder_id, file_type=None):
        """Lista arquivos em uma pasta"""
        try:
            query = f"'{folder_id}' in parents and trashed=false"
            
            if file_type:
                query += f" and mimeType='{file_type}'"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, mimeType, size, modifiedTime)',
                pageSize=1000
            ).execute()
            
            return results.get('files', [])
        except HttpError as e:
            logger.error(f"Erro ao listar arquivos: {e}")
            return []
    
    def download_file(self, file_id, output_path):
        """Baixa um arquivo do Google Drive"""
        try:
            # Obter metadados
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields='name, size'
            ).execute()
            
            # Download
            request = self.service.files().get_media(fileId=file_id)
            fh = io.FileIO(output_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request, chunksize=10*1024*1024)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            logger.debug(f"✓ Arquivo baixado: {file_metadata['name']}")
            return True
        except Exception as e:
            logger.error(f"Erro ao baixar arquivo {file_id}: {e}")
            return False

class DicomProcessor:
    """Processa arquivos DICOM"""
    
    def __init__(self):
        self.stats = {'total': 0, 'success': 0, 'failed': 0}
    
    def process_file(self, file_path):
        """Processa arquivo DICOM"""
        try:
            # Lógica de processamento DICOM
            logger.debug(f"Processando: {file_path}")
            time.sleep(0.5)  # Simular processamento
            
            self.stats['success'] += 1
            return {'status': 'success', 'file': file_path}
        except Exception as e:
            logger.error(f"Erro ao processar {file_path}: {e}")
            self.stats['failed'] += 1
            return {'status': 'failed', 'file': file_path, 'error': str(e)}

class BatchPipeline:
    """Pipeline de processamento em lote"""
    
    def __init__(self, google_drive, dicom_processor, max_workers=5, temp_dir='./temp'):
        self.drive = google_drive
        self.processor = dicom_processor
        self.max_workers = max_workers
        self.temp_dir = temp_dir
        self.batch_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        os.makedirs(temp_dir, exist_ok=True)
    
    def run(self, folder_id):
        """Executa pipeline completo"""
        logger.info(f"Iniciando batch {self.batch_id}")
        start_time = time.time()
        
        try:
            # 1. Listar arquivos DICOM
            logger.info("Etapa 1: Listando arquivos...")
            files = self.drive.list_files(
                folder_id,
                file_type='application/dicom'  # ou use extensão
            )
            logger.info(f"✓ {len(files)} arquivos DICOM encontrados")
            
            if not files:
                logger.warning("Nenhum arquivo DICOM encontrado")
                return
            
            # 2. Download paralelo
            logger.info("Etapa 2: Download paralelo...")
            downloaded = self._parallel_download(files)
            
            # 3. Processamento DICOM paralelo
            logger.info("Etapa 3: Processamento DICOM...")
            self._parallel_process(downloaded)
            
            # 4. Limpeza
            logger.info("Etapa 4: Limpeza...")
            self._cleanup()
            
            # 5. Resumo
            duration = time.time() - start_time
            self._print_summary(duration)
            
        except Exception as e:
            logger.error(f"✗ Erro no batch: {e}", exc_info=True)
            raise
    
    def _parallel_download(self, files):
        """Download paralelo"""
        downloaded = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._download_file, f): f['id']
                for f in files
            }
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        downloaded.append(result)
                except Exception as e:
                    logger.error(f"Erro no download: {e}")
        
        logger.info(f"✓ {len(downloaded)} arquivos baixados")
        return downloaded
    
    def _download_file(self, file_info):
        """Download individual com retry"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                file_path = os.path.join(self.temp_dir, file_info['name'])
                success = self.drive.download_file(file_info['id'], file_path)
                if success:
                    return file_path
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Tentativa {attempt + 1}/{max_retries} para {file_info['name']}")
                    time.sleep(2 ** attempt)
        
        return None
    
    def _parallel_process(self, files):
        """Processamento paralelo"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.processor.process_file, f): f
                for f in files
            }
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Erro no processamento: {e}")
    
    def _cleanup(self):
        """Remove arquivos temporários"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.debug("✓ Limpeza realizada")
        except Exception as e:
            logger.warning(f"Erro na limpeza: {e}")
    
    def _print_summary(self, duration):
        """Exibe resumo do batch"""
        total = self.processor.stats['success'] + self.processor.stats['failed']
        success_rate = (self.processor.stats['success'] / total * 100) if total > 0 else 0
        
        logger.info(f"""
        ╔════════════════════════════════════════╗
        ║        RESUMO DO BATCH {self.batch_id}        ║
        ╠════════════════════════════════════════╣
        ║ Total de arquivos: {total:25} ║
        ║ Sucesso: {self.processor.stats['success']:31} ║
        ║ Falhas: {self.processor.stats['failed']:32} ║
        ║ Taxa de sucesso: {success_rate:.1f}%{' ':27}║
        ║ Duração: {duration:.2f}s{' ':30}║
        ╚════════════════════════════════════════╝
        """)

# ===== MAIN =====

def main():
    try:
        # Inicializar componentes
        drive = GoogleDriveManager()
        drive.authenticate()
        
        processor = DicomProcessor()
        
        pipeline = BatchPipeline(
            drive,
            processor,
            max_workers=5,
            temp_dir='./temp'
        )
        
        # Executar pipeline
        folder_id = 'PASTA_ID_AQUI'  # Substituir com ID real
        pipeline.run(folder_id)
        
    except Exception as e:
        logger.critical(f"Erro crítico: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
```

---

## RESUMO DE RECOMENDAÇÕES

### 📌 Para seu caso (DICOM + Google Drive)

1. **Autenticação**: OAuth 2.0 com `google-api-python-client`
2. **Paralelização**: ThreadPoolExecutor (5-10 workers)
3. **Logging**: Loguru com rotação automática
4. **Rate Limiting**: 5-10 requisições/segundo
5. **Tratamento de Erros**: Retry exponencial + notificações

### 📦 Dependências Recomendadas

```bash
pip install \
  google-api-python-client \
  google-auth-oauthlib \
  google-auth-httplib2 \
  loguru \
  tqdm \
  pydicom  # se necessário para processamento DICOM
```

### 🚀 Próximos Passos

1. Configure Google Cloud Console e obtenha `credentials.json`
2. Implemente autenticação OAuth
3. Teste downloads com pequenos volumes
4. Escale para processamento em lote
5. Configure monitoring e alertas
