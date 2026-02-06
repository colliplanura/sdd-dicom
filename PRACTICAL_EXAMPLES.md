# Exemplos Práticos Prontos para Usar

## 1. Setup Básico (Comece aqui)

### requirements.txt

```txt
google-api-python-client==1.12.8
google-auth-oauthlib==1.2.1
google-auth-httplib2==0.2.0
loguru==0.7.2
tqdm==4.66.2
python-dateutil==2.8.2
```

### Instalação

```bash
pip install -r requirements.txt
```

---

## 2. Exemplo Mínimo: Download de Arquivo

```python
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os

# Configurar credenciais
SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    return build('drive', 'v3', credentials=creds)

def download_file(file_id, output_path):
    service = get_drive_service()
    
    # Download
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(output_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    while not done:
        status, done = downloader.next_chunk()
        if status:
            print(f"Download {int(status.progress() * 100)}%")
    
    print(f"Arquivo salvo em {output_path}")

# Uso
download_file('seu_file_id_aqui', 'output.dcm')
```

---

## 3. Download em Lote (ThreadPoolExecutor)

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os
from loguru import logger

logger.add("batch_download.log", level="DEBUG")

class BatchDownloader:
    def __init__(self, max_workers=5):
        self.max_workers = max_workers
        self.service = self._authenticate()
    
    def _authenticate(self):
        SCOPES = ['https://www.googleapis.com/auth/drive']
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        return build('drive', 'v3', credentials=creds)
    
    def download_file(self, file_id, output_path):
        """Download individual"""
        try:
            request = self.service.files().get_media(fileId=file_id)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with io.FileIO(output_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request, chunksize=1024*1024)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            
            logger.info(f"✓ {os.path.basename(output_path)}")
            return True
        except Exception as e:
            logger.error(f"✗ {file_id}: {e}")
            return False
    
    def batch_download(self, file_list, output_dir):
        """
        Download em lote
        file_list: lista de dicts com {'id': 'file_id', 'name': 'filename'}
        """
        results = {'success': 0, 'failed': 0}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self.download_file,
                    item['id'],
                    os.path.join(output_dir, item['name'])
                ): item['id']
                for item in file_list
            }
            
            for future in as_completed(futures):
                if future.result():
                    results['success'] += 1
                else:
                    results['failed'] += 1
        
        logger.info(f"Download completo: {results['success']} sucesso, {results['failed']} falhas")
        return results

# Uso
downloader = BatchDownloader(max_workers=5)
files = [
    {'id': 'file_id_1', 'name': 'file1.dcm'},
    {'id': 'file_id_2', 'name': 'file2.dcm'},
    {'id': 'file_id_3', 'name': 'file3.dcm'},
]
downloader.batch_download(files, './downloads')
```

---

## 4. Listar e Filtrar Arquivos

```python
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

class GoogleDriveLister:
    def __init__(self):
        SCOPES = ['https://www.googleapis.com/auth/drive']
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        self.service = build('drive', 'v3', credentials=creds)
    
    def list_files_in_folder(self, folder_id, file_type=None):
        """Lista arquivos em uma pasta"""
        query = f"'{folder_id}' in parents and trashed=false"
        
        # Filtrar por tipo MIME se especificado
        if file_type:
            query += f" and mimeType='{file_type}'"
        
        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, mimeType, size, modifiedTime)',
            pageSize=1000
        ).execute()
        
        return results.get('files', [])
    
    def list_dicom_files(self, folder_id):
        """Lista especificamente arquivos DICOM"""
        query = f"'{folder_id}' in parents and trashed=false and name contains '.dcm'"
        
        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, size, modifiedTime)',
            pageSize=1000
        ).execute()
        
        return results.get('files', [])
    
    def search_files_by_name(self, search_term):
        """Busca arquivos pelo nome"""
        query = f"name contains '{search_term}' and trashed=false"
        
        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, webViewLink)',
            pageSize=100
        ).execute()
        
        return results.get('files', [])

# Uso
lister = GoogleDriveLister()

# Listar arquivos DICOM
dicom_files = lister.list_dicom_files('pasta_id')
print(f"Encontrados {len(dicom_files)} arquivos DICOM:")
for file in dicom_files:
    print(f"  - {file['name']} ({file['size']} bytes)")

# Buscar por nome
results = lister.search_files_by_name('radiografia')
for r in results:
    print(f"  - {r['name']}: {r['webViewLink']}")
```

---

## 5. Upload de Arquivos

```python
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
import os
from loguru import logger

logger.add("batch_upload.log", level="DEBUG")

class BatchUploader:
    def __init__(self, max_workers=5):
        self.max_workers = max_workers
        SCOPES = ['https://www.googleapis.com/auth/drive']
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        self.service = build('drive', 'v3', credentials=creds)
    
    def upload_file(self, local_path, parent_folder_id, file_name=None):
        """Upload de um arquivo"""
        file_name = file_name or os.path.basename(local_path)
        
        file_metadata = {
            'name': file_name,
            'parents': [parent_folder_id]
        }
        
        media = MediaFileUpload(local_path, resumable=True)
        
        request = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name'
        )
        
        response = None
        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    print(f"Upload {int(status.progress() * 100)}%")
            except Exception as e:
                logger.error(f"Erro no upload: {e}")
                return None
        
        logger.info(f"✓ Arquivo enviado: {response['name']} (ID: {response['id']})")
        return response['id']
    
    def upload_folder(self, local_dir, parent_folder_id):
        """Upload recursivo de pasta"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        uploaded_ids = []
        
        # Primeiro, cria estrutura de pastas
        for root, dirs, files in os.walk(local_dir):
            for dir_name in dirs:
                folder_id = self.create_folder(dir_name, parent_folder_id)
                if folder_id:
                    uploaded_ids.append(folder_id)
            
            # Depois faz upload dos arquivos em paralelo
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {}
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    future = executor.submit(
                        self.upload_file,
                        file_path,
                        parent_folder_id,
                        file_name
                    )
                    futures[future] = file_name
                
                for future in as_completed(futures):
                    file_id = future.result()
                    if file_id:
                        uploaded_ids.append(file_id)
        
        return uploaded_ids
    
    def create_folder(self, folder_name, parent_folder_id):
        """Cria pasta no Google Drive"""
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        
        folder = self.service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        
        return folder.get('id')

# Uso
uploader = BatchUploader(max_workers=5)

# Upload de arquivo único
file_id = uploader.upload_file(
    'local_file.dcm',
    'parent_folder_id',
    'output_name.dcm'
)

# Upload de pasta completa
uploader.upload_folder('./local_folder', 'parent_folder_id')
```

---

## 6. Rate Limiting e Retry

```python
import time
from functools import wraps
from loguru import logger

class RateLimiter:
    def __init__(self, requests_per_second=10):
        self.rps = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request = 0
    
    def wait(self):
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()
    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.wait()
            return func(*args, **kwargs)
        return wrapper

def retry_with_backoff(max_retries=3, backoff_factor=2):
    """Decorator para retry automático"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        logger.warning(f"Tentativa {attempt + 1}/{max_retries} em {wait_time}s")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Falha após {max_retries} tentativas")
                        raise
        return wrapper
    return decorator

# Uso
rate_limiter = RateLimiter(requests_per_second=5)

@rate_limiter
def api_call():
    print("Fazendo requisição à API")

@retry_with_backoff(max_retries=3, backoff_factor=2)
def download_with_retry(file_id):
    print(f"Baixando {file_id}")
    # Se falhar, retry automaticamente

# Chamar
for i in range(10):
    api_call()  # Respeita rate limit

download_with_retry('file_id')  # Com retry
```

---

## 7. Configuração Completa de Logging

```python
from loguru import logger
import sys
import os
from datetime import datetime

def setup_logging():
    """Configure logging para o sistema"""
    
    # Remove handler padrão
    logger.remove()
    
    # Console output com cores
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True
    )
    
    # Arquivo de log geral
    os.makedirs('logs', exist_ok=True)
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="500 MB",
        retention="10 days",
        compression="zip"
    )
    
    # Arquivo apenas para erros
    logger.add(
        "logs/errors_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="daily"
    )
    
    return logger

# Usar em seu código
setup_logging()

logger.info("Aplicação iniciada")
logger.debug("Mensagem de debug")
logger.warning("Aviso importante")
logger.error("Erro ocorreu")
```

---

## 8. Monitoramento de Progresso

```python
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

def download_with_progress(file_list, downloader):
    """Download com barra de progresso"""
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(downloader.download_file, f['id'], f['name']): f['name']
            for f in file_list
        }
        
        # Envolver com tqdm para progresso
        for future in tqdm(as_completed(futures), total=len(file_list)):
            file_name = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"Erro em {file_name}: {e}")

# Uso
download_with_progress(files, downloader)
```

---

## 9. Exemplo Final: Pipeline Completo

```python
#!/usr/bin/env python3
"""
Pipeline completo de processamento:
1. Listar arquivos DICOM no Google Drive
2. Download paralelo
3. Processar (stub)
4. Upload de resultados
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger
from tqdm import tqdm

# Seu código aqui...

def main():
    logger.info("=== Iniciando Pipeline DICOM ===")
    start = time.time()
    
    try:
        # 1. Setup
        logger.info("Etapa 1: Autenticação...")
        
        # 2. Listar
        logger.info("Etapa 2: Listando arquivos...")
        
        # 3. Download
        logger.info("Etapa 3: Download em lote...")
        
        # 4. Processar
        logger.info("Etapa 4: Processamento...")
        
        # 5. Upload
        logger.info("Etapa 5: Upload de resultados...")
        
        # 6. Limpeza
        logger.info("Etapa 6: Limpeza...")
        
        duration = time.time() - start
        logger.info(f"✓ Pipeline completo em {duration:.2f}s")
        
    except Exception as e:
        logger.critical(f"Erro no pipeline: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
```

---

## 📋 Checklist de Implementação

- [ ] Gerar `credentials.json` no Google Cloud Console
- [ ] Instalar dependências: `pip install -r requirements.txt`
- [ ] Configurar logging com Loguru
- [ ] Implementar autenticação
- [ ] Teste: Download de 1 arquivo
- [ ] Teste: Download em lote de 10 arquivos
- [ ] Adicionar rate limiting
- [ ] Adicionar retry com backoff
- [ ] Implementar processamento DICOM
- [ ] Adicionar monitoramento
- [ ] Testes com volumes grandes
- [ ] Configurar notificações de erro
- [ ] Deploy em produção

---

## 🐛 Troubleshooting

### "403 Forbidden"
- Verificar escopos em `SCOPES`
- Deletar `token.json` e fazer login novamente

### "429 Too Many Requests"
- Reduzir `max_workers`
- Aumentar intervalo do rate limiter

### Memória alta em processamento em lote
- Reduzir `max_workers`
- Implementar streaming em vez de carregar em memória

### Arquivo grande falha no upload
- Usar `resumable=True` (já feito)
- Aumentar timeout
- Usar Cloud Storage em vez de Drive

