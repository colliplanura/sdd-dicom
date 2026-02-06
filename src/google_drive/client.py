"""
Cliente para Google Drive
"""
from pathlib import Path
from typing import List, Optional, Dict
from loguru import logger

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import io

from ..core.config import Config
from ..core.exceptions import GoogleDriveError, DownloadError, UploadError
from .auth import GoogleDriveAuth
from .rate_limiter import RateLimiter


class GoogleDriveClient:
    """
    Cliente para interagir com Google Drive
    
    Encapsula:
    - Autenticação
    - Listagem de arquivos
    - Download/Upload
    - Rate limiting
    - Retry automático
    """
    
    def __init__(
        self,
        credentials_path: Optional[Path] = None,
        token_path: Optional[Path] = None,
        rate_limit_rps: int = 5
    ):
        """
        Inicializar cliente
        
        Args:
            credentials_path: Caminho para credentials.json
            token_path: Caminho para token.json
            rate_limit_rps: Requisições por segundo
        """
        self.credentials_path = credentials_path or Config.CREDENTIALS_PATH
        self.token_path = token_path or Config.TOKEN_PATH
        self.rate_limiter = RateLimiter(rate_limit_rps)
        
        # Autenticar
        auth = GoogleDriveAuth(self.credentials_path, self.token_path)
        creds = auth.authenticate()
        
        # Criar serviço
        self.service = build('drive', 'v3', credentials=creds)
        logger.info("✓ Google Drive client initialized")
    
    def _execute_with_rate_limit(self, request):
        """Executar requisição com rate limiting"""
        with self.rate_limiter:
            return request.execute()
    
    def list_files(
        self,
        folder_id: Optional[str] = None,
        folder_name: Optional[str] = None,
        recursive: bool = True,
        max_results: int = 1000
    ) -> List[Dict]:
        """
        Listar arquivos em pasta
        
        Args:
            folder_id: ID da pasta (se conhecido)
            folder_name: Nome da pasta (se ID não conhecido)
            recursive: Listar recursivamente
            max_results: Máximo de resultados
        
        Returns:
            Lista de arquivos com metadados
        """
        try:
            # Se não tem folder_id, procurar pelo nome
            if not folder_id and folder_name:
                folder_id = self._find_folder_by_name(folder_name)
                if not folder_id:
                    raise GoogleDriveError(f"Pasta não encontrada: {folder_name}")
            
            files = []
            query = f"'{folder_id}' in parents and trashed=false"
            
            logger.info(f"Listando arquivos da pasta: {folder_id}")
            
            page_token = None
            while True:
                request = self.service.files().list(
                    q=query,
                    spaces='drive',
                    pageSize=100,
                    pageToken=page_token,
                    fields='files(id, name, size, mimeType, modifiedTime, parents)',
                )
                
                results = self._execute_with_rate_limit(request)
                files.extend(results.get('files', []))
                
                page_token = results.get('nextPageToken')
                if not page_token or len(files) >= max_results:
                    break
            
            # Truncar se necessário
            files = files[:max_results]
            logger.info(f"✓ {len(files)} arquivos listados")
            
            return files
        
        except HttpError as e:
            raise GoogleDriveError(f"Erro ao listar arquivos: {e}")
    
    def _find_folder_by_name(self, folder_name: str) -> Optional[str]:
        """Encontrar ID de pasta pelo nome"""
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            request = self.service.files().list(
                q=query,
                spaces='drive',
                pageSize=1,
                fields='files(id)',
            )
            
            results = self._execute_with_rate_limit(request)
            files = results.get('files', [])
            
            if files:
                return files[0]['id']
            return None
        
        except HttpError:
            return None
    
    def download_file(
        self,
        file_id: str,
        output_path: Path,
        chunk_size_mb: int = 10,
        timeout_seconds: int = 300
    ) -> bool:
        """
        Download de arquivo com suporte a resume
        
        Args:
            file_id: ID do arquivo no Google Drive
            output_path: Caminho local de saída
            chunk_size_mb: Tamanho de chunk em MB
            timeout_seconds: Timeout em segundos
        
        Returns:
            True se sucesso, False se falha
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Preparar requisição
            request = self.service.files().get_media(fileId=file_id)
            
            logger.info(f"Iniciando download: {file_id} → {output_path}")
            
            with open(output_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(
                    fh,
                    request,
                    chunksize=chunk_size_mb * 1024 * 1024,
                    resumable=True
                )
                
                done = False
                start_time = None
                while not done:
                    try:
                        status, done = downloader.next_chunk()
                        
                        if status:
                            progress = int(status.progress() * 100)
                            logger.debug(f"Download progress: {progress}%")
                    
                    except HttpError as e:
                        logger.error(f"Download interrupted: {e}")
                        raise DownloadError(f"Download failed: {e}")
            
            logger.info(f"✓ Download concluído: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Erro no download: {e}")
            raise DownloadError(f"Erro ao fazer download: {e}")
    
    def upload_file(
        self,
        file_path: Path,
        folder_id: str,
        file_name: Optional[str] = None
    ) -> str:
        """
        Upload de arquivo para Google Drive
        
        Args:
            file_path: Caminho do arquivo local
            folder_id: ID da pasta de destino
            file_name: Nome do arquivo no Drive (padrão: nome local)
        
        Returns:
            ID do arquivo criado no Google Drive
        """
        try:
            file_path = Path(file_path)
            file_name = file_name or file_path.name
            
            logger.info(f"Iniciando upload: {file_path} → {file_name}")
            
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            
            media = MediaFileUpload(
                str(file_path),
                resumable=True,
                chunksize=10 * 1024 * 1024
            )
            
            request = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id',
                supportsAllDrives=True
            )
            
            file_id = None
            while not file_id:
                status, done = request.next_chunk()
                if done:
                    file_id = request.execute().get('id')
            
            logger.info(f"✓ Upload concluído: {file_id}")
            return file_id
        
        except Exception as e:
            logger.error(f"Erro no upload: {e}")
            raise UploadError(f"Erro ao fazer upload: {e}")
    
    def get_file_info(self, file_id: str) -> Dict:
        """Obter informações de arquivo"""
        try:
            request = self.service.files().get(
                fileId=file_id,
                fields='id, name, size, mimeType, modifiedTime'
            )
            return self._execute_with_rate_limit(request)
        
        except HttpError as e:
            raise GoogleDriveError(f"Erro ao obter info: {e}")
