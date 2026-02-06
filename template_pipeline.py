"""
Template pronto para usar - Copiar e adaptar para seu projeto
"""

import os
import sys
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json

# Dependências (instalar com: pip install -r requirements.txt)
from loguru import logger
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

# ============================================================================
# PARTE 1: CONFIGURAÇÃO
# ============================================================================

# Escopos de acesso ao Google Drive
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    # Alternativas mais restritivas:
    # 'https://www.googleapis.com/auth/drive.file',      # Apenas arquivos criados pela app
    # 'https://www.googleapis.com/auth/drive.readonly',  # Apenas leitura
]

# Configurações
CONFIG = {
    'credentials_file': 'credentials.json',  # Obtido no Google Cloud Console
    'token_file': 'token.json',              # Gerado automaticamente
    'temp_dir': './temp',
    'log_dir': './logs',
    'max_workers': 5,                        # Threads paralelas
    'rate_limit': 10,                        # Requisições por segundo
    'timeout_seconds': 30,
    'max_retries': 3,
    'retry_backoff': 2,                      # Exponential backoff
}

# ============================================================================
# PARTE 2: SETUP DE LOGGING
# ============================================================================

def setup_logging():
    """Configura logging com Loguru"""
    os.makedirs(CONFIG['log_dir'], exist_ok=True)
    
    # Remove handler padrão
    logger.remove()
    
    # Console (colorido)
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        level="INFO",
        colorize=True
    )
    
    # Arquivo log geral
    logger.add(
        f"{CONFIG['log_dir']}/app_{{time:YYYY-MM-DD}}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="500 MB",
        retention="10 days",
        compression="zip"
    )
    
    # Arquivo apenas erros
    logger.add(
        f"{CONFIG['log_dir']}/errors_{{time:YYYY-MM-DD}}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="ERROR",
        rotation="daily"
    )
    
    logger.info("✓ Logging configurado")

# ============================================================================
# PARTE 3: AUTENTICAÇÃO
# ============================================================================

class GoogleDriveAuth:
    """Gerencia autenticação com Google Drive"""
    
    def __init__(self, credentials_file=None, token_file=None):
        self.credentials_file = credentials_file or CONFIG['credentials_file']
        self.token_file = token_file or CONFIG['token_file']
        self.creds = None
    
    def authenticate(self):
        """Realiza autenticação e retorna credenciais"""
        # Carregar token existente
        if os.path.exists(self.token_file):
            logger.debug("Carregando token existente...")
            self.creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        # Se não há credenciais válidas, fazer login
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                logger.debug("Renovando token expirado...")
                self.creds.refresh(Request())
            else:
                logger.info("Iniciando fluxo de autenticação...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            
            # Salvar credenciais para próxima execução
            with open(self.token_file, 'w') as token:
                token.write(self.creds.to_json())
            logger.info("✓ Credenciais salvas em token.json")
        
        return self.creds
    
    def get_service(self):
        """Retorna serviço autenticado do Google Drive"""
        if not self.creds:
            self.authenticate()
        return build('drive', 'v3', credentials=self.creds)

# ============================================================================
# PARTE 4: OPERAÇÕES GOOGLE DRIVE
# ============================================================================

class GoogleDriveManager:
    """Gerencia operações com Google Drive"""
    
    def __init__(self, service):
        self.service = service
    
    def list_files(self, folder_id, query_filter=None):
        """Lista arquivos em uma pasta"""
        try:
            query = f"'{folder_id}' in parents and trashed=false"
            if query_filter:
                query += f" and {query_filter}"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, mimeType, size, modifiedTime)',
                pageSize=1000
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"✓ Encontrados {len(files)} arquivos")
            return files
        except HttpError as e:
            logger.error(f"✗ Erro ao listar arquivos: {e}")
            return []
    
    def download_file(self, file_id, output_path, chunk_size=10*1024*1024):
        """Baixa um arquivo do Google Drive"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            request = self.service.files().get_media(fileId=file_id)
            with io.FileIO(output_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request, chunksize=chunk_size)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            
            logger.debug(f"✓ {os.path.basename(output_path)}")
            return True
        except Exception as e:
            logger.error(f"✗ Erro ao baixar {file_id}: {e}")
            return False
    
    def upload_file(self, file_path, parent_folder_id, file_name=None):
        """Faz upload de um arquivo"""
        try:
            file_name = file_name or os.path.basename(file_path)
            
            file_metadata = {
                'name': file_name,
                'parents': [parent_folder_id]
            }
            
            media = MediaFileUpload(file_path, resumable=True)
            
            request = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name'
            )
            
            response = None
            while response is None:
                try:
                    status, response = request.next_chunk()
                except HttpError as error:
                    logger.error(f"Erro no upload: {error}")
                    return None
            
            logger.debug(f"✓ {response['name']} (ID: {response['id']})")
            return response['id']
        except Exception as e:
            logger.error(f"✗ Erro ao fazer upload: {e}")
            return None

# ============================================================================
# PARTE 5: RATE LIMITING
# ============================================================================

class RateLimiter:
    """Controla taxa de requisições"""
    
    def __init__(self, requests_per_second=10):
        self.rps = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request = 0
    
    def wait(self):
        """Aguarda se necessário para respeitar limite"""
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()

# ============================================================================
# PARTE 6: RETRY COM BACKOFF
# ============================================================================

def retry_with_backoff(max_retries=None, backoff_factor=None):
    """Decorator para retry automático com backoff exponencial"""
    max_retries = max_retries or CONFIG['max_retries']
    backoff_factor = backoff_factor or CONFIG['retry_backoff']
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        logger.warning(f"Tentativa {attempt + 1}/{max_retries} para {func.__name__} em {wait_time}s")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Falha permanente em {func.__name__} após {max_retries} tentativas")
                        raise
        return wrapper
    return decorator

# ============================================================================
# PARTE 7: PIPELINE DE PROCESSAMENTO
# ============================================================================

class BatchPipeline:
    """Pipeline de processamento em lote"""
    
    def __init__(self, drive_manager, max_workers=None):
        self.drive = drive_manager
        self.max_workers = max_workers or CONFIG['max_workers']
        self.rate_limiter = RateLimiter(CONFIG['rate_limit'])
        self.batch_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.stats = {'total': 0, 'success': 0, 'failed': 0}
        
        os.makedirs(CONFIG['temp_dir'], exist_ok=True)
    
    def batch_download(self, file_list):
        """Download em lote com controle de taxa e retry"""
        logger.info(f"Iniciando download de {len(file_list)} arquivos...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._download_with_rate_limit, f): f['id']
                for f in file_list
            }
            
            for future in as_completed(futures):
                file_id = futures[future]
                try:
                    result = future.result(timeout=CONFIG['timeout_seconds'])
                    if result:
                        self.stats['success'] += 1
                    else:
                        self.stats['failed'] += 1
                except Exception as e:
                    logger.error(f"Erro em {file_id}: {e}")
                    self.stats['failed'] += 1
                
                self.stats['total'] += 1
        
        logger.info(f"Download completo: {self.stats['success']}/{self.stats['total']} sucesso")
        return self.stats
    
    @retry_with_backoff()
    def _download_with_rate_limit(self, file_info):
        """Download individual com rate limiting"""
        self.rate_limiter.wait()
        
        output_path = os.path.join(CONFIG['temp_dir'], file_info['name'])
        return self.drive.download_file(file_info['id'], output_path)
    
    def cleanup(self):
        """Limpa arquivos temporários"""
        try:
            import shutil
            if os.path.exists(CONFIG['temp_dir']):
                shutil.rmtree(CONFIG['temp_dir'])
                logger.info("✓ Limpeza realizada")
        except Exception as e:
            logger.warning(f"Erro na limpeza: {e}")

# ============================================================================
# PARTE 8: FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal - executar seu pipeline aqui"""
    
    # Setup
    setup_logging()
    logger.info("=== Iniciando Pipeline ===")
    start_time = time.time()
    
    try:
        # 1. Autenticar
        logger.info("Etapa 1: Autenticação...")
        auth = GoogleDriveAuth()
        service = auth.get_service()
        
        # 2. Gerenciar Google Drive
        logger.info("Etapa 2: Listando arquivos...")
        drive = GoogleDriveManager(service)
        
        # TODO: Substituir 'folder_id' pelo ID da sua pasta
        folder_id = 'COLOQUE_SEU_FOLDER_ID_AQUI'
        
        # Filtro opcional: apenas arquivos DICOM
        # query_filter = "name contains '.dcm'"
        
        files = drive.list_files(folder_id)
        
        if not files:
            logger.warning("Nenhum arquivo encontrado")
            return 0
        
        # 3. Download em lote
        logger.info("Etapa 3: Download em lote...")
        pipeline = BatchPipeline(drive, max_workers=CONFIG['max_workers'])
        results = pipeline.batch_download(files)
        
        # 4. TODO: Seu processamento aqui
        logger.info("Etapa 4: Processamento...")
        # def process_file(file_path):
        #     # Sua lógica de processamento
        #     pass
        
        # 5. Limpeza
        logger.info("Etapa 5: Limpeza...")
        pipeline.cleanup()
        
        # Resumo
        duration = time.time() - start_time
        success_rate = (results['success'] / results['total'] * 100) if results['total'] > 0 else 0
        
        logger.info(f"""
╔═══════════════════════════════════╗
║        RESUMO DO PIPELINE         ║
╠═══════════════════════════════════╣
║ Total: {results['total']:30} ║
║ Sucesso: {results['success']:27} ║
║ Falhas: {results['failed']:28} ║
║ Taxa: {success_rate:.1f}%{' ':28}║
║ Duração: {duration:.2f}s{' ':25}║
╚═══════════════════════════════════╝
        """)
        
        return 0
        
    except Exception as e:
        logger.critical(f"Erro crítico: {e}", exc_info=True)
        return 1

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    exit(main())


# ============================================================================
# PRÓXIMOS PASSOS
# ============================================================================
"""
1. SETUP GOOGLE CLOUD:
   - Ir em https://cloud.google.com/console
   - Criar novo projeto
   - Ativar "Google Drive API"
   - Criar OAuth 2.0 Client ID (Desktop application)
   - Baixar JSON como 'credentials.json'

2. INSTALAR DEPENDÊNCIAS:
   pip install google-api-python-client google-auth-oauthlib google-auth-httplib2 loguru

3. CONFIGURAR:
   - Editar CONFIG['credentials_file'] com seu arquivo
   - Editar folder_id na função main()

4. EXECUTAR:
   python seu_arquivo.py

5. PERSONALIZAR:
   - Adicionar sua lógica de processamento
   - Modificar rate_limit conforme necessário
   - Adicionar mais filtros em list_files()

"""
