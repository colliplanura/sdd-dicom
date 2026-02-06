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
        max_results: int = 1000,
        filter_dicom: bool = True
    ) -> List[Dict]:
        """
        Listar arquivos em pasta (recursivamente se configurado)
        
        Args:
            folder_id: ID da pasta (se conhecido)
            folder_name: Nome da pasta (se ID não conhecido)
            recursive: Listar recursivamente em subpastas
            max_results: Máximo de resultados
            filter_dicom: Filtrar apenas arquivos DICOM (magic number)
        
        Returns:
            Lista de arquivos com metadados
        """
        try:
            # Se não tem folder_id, procurar pelo nome
            if not folder_id and folder_name:
                logger.info(f"Procurando pasta: {folder_name}")
                folder_id = self._find_folder_by_name(folder_name)
                if not folder_id:
                    error_msg = (
                        f"Pasta não encontrada: {folder_name}\n"
                        f"Verifique:\n"
                        f"  1. Se o caminho está correto\n"
                        f"  2. Se a pasta existe no Google Drive\n"
                        f"  3. Se você tem permissão de acesso\n"
                        f"  4. Espaços/caracteres especiais no nome"
                    )
                    logger.error(error_msg)
                    raise GoogleDriveError(error_msg)
            
            files = []
            
            if recursive:
                # Busca recursiva em subpastas
                logger.info(f"Listando recursivamente arquivos da pasta: {folder_id}")
                files = self._list_files_recursive(folder_id, max_results)
            else:
                # Busca apenas na pasta especificada
                logger.info(f"Listando arquivos da pasta: {folder_id}")
                files = self._list_files_in_folder(folder_id, max_results)
            
            # Filtrar apenas arquivos (não pastas)
            files = [f for f in files if f.get('mimeType', '') != 'application/vnd.google-apps.folder']
            
            # Truncar se necessário
            files = files[:max_results]
            logger.info(f"✓ {len(files)} arquivos listados")
            
            return files
        
        except HttpError as e:
            raise GoogleDriveError(f"Erro ao listar arquivos: {e}")
    
    def _list_files_in_folder(
        self,
        folder_id: str,
        max_results: int = 1000
    ) -> List[Dict]:
        """Listar arquivos apenas na pasta especificada (não recursivo)"""
        files = []
        query = f"'{folder_id}' in parents and trashed=false"
        
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
        
        return files
    
    def _list_files_recursive(
        self,
        folder_id: str,
        max_results: int = 1000
    ) -> List[Dict]:
        """Listar arquivos recursivamente em subpastas"""
        all_files = []
        folders_to_process = [folder_id]
        processed_folders = set()
        
        while folders_to_process and len(all_files) < max_results:
            current_folder = folders_to_process.pop(0)
            
            # Evitar processar pasta duplicada
            if current_folder in processed_folders:
                continue
            processed_folders.add(current_folder)
            
            try:
                query = f"'{current_folder}' in parents and trashed=false"
                
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
                    items = results.get('files', [])
                    
                    for item in items:
                        # Se é pasta, adicionar para processar depois
                        if item.get('mimeType') == 'application/vnd.google-apps.folder':
                            if item['id'] not in processed_folders:
                                folders_to_process.append(item['id'])
                        else:
                            # É arquivo, adicionar à lista
                            all_files.append(item)
                            if len(all_files) >= max_results:
                                break
                    
                    page_token = results.get('nextPageToken')
                    if not page_token or len(all_files) >= max_results:
                        break
            
            except HttpError as e:
                logger.warning(f"Erro ao listar pasta {current_folder}: {e}")
                continue
        
        return all_files[:max_results]
    
    def _find_folder_by_name(self, folder_name: str) -> Optional[str]:
        """
        Encontrar ID de pasta pelo nome
        
        Suporta:
        - Nome simples: "Exames"
        - Caminho: "Medicina/Doutorado IDOR/Exames/DICOM"
        
        Args:
            folder_name: Nome da pasta ou caminho completo
        
        Returns:
            ID da pasta ou None se não encontrada
        """
        try:
            # Se contém "/", é um caminho aninhado
            if '/' in folder_name:
                return self._find_folder_by_path(folder_name)
            
            # Busca simples por nome
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
        
        except HttpError as e:
            logger.warning(f"Erro ao buscar pasta '{folder_name}': {e}")
            return None
    
    def _find_folder_by_path(self, path: str) -> Optional[str]:
        """
        Encontrar pasta navegando por caminho aninhado
        
        Ex: "Medicina/Doutorado IDOR/Exames/DICOM"
        
        Args:
            path: Caminho com pastas separadas por "/"
        
        Returns:
            ID da pasta final ou None se caminho não encontrado
        """
        try:
            parts = [p.strip() for p in path.split('/') if p.strip()]
            
            if not parts:
                logger.warning("Caminho vazio fornecido")
                return None
            
            current_folder_id = None
            
            # Navegar por cada parte do caminho
            for i, part in enumerate(parts):
                logger.debug(f"Buscando pasta: {part}")
                
                if current_folder_id:
                    # Buscar dentro da pasta atual
                    query = f"name='{part}' and mimeType='application/vnd.google-apps.folder' and '{current_folder_id}' in parents and trashed=false"
                else:
                    # Buscar na raiz
                    query = f"name='{part}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
                
                request = self.service.files().list(
                    q=query,
                    spaces='drive',
                    pageSize=10,  # Aumentado para lidar com homônimos
                    fields='files(id, name)',
                )
                
                results = self._execute_with_rate_limit(request)
                files = results.get('files', [])
                
                if not files:
                    logger.warning(f"Pasta não encontrada: {part}")
                    logger.warning(f"Caminho procurado até: {'/'.join(parts[:i])}")
                    return None
                
                # Se múltiplas opções, preferir match exato
                found = None
                for f in files:
                    if f['name'] == part:  # Match exato
                        found = f
                        break
                
                # Se não encontrou match exato, usar primeiro resultado
                if not found:
                    found = files[0]
                    logger.debug(f"Usando aproximação: {found['name']}")
                
                current_folder_id = found['id']
                logger.debug(f"✓ Pasta encontrada: {found['name']} (ID: {current_folder_id})")
            
            logger.info(f"✓ Caminho encontrado: {path} → {current_folder_id}")
            return current_folder_id
        
        except HttpError as e:
            logger.error(f"Erro ao navegar caminho '{path}': {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar caminho '{path}': {e}")
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
                # MediaIoBaseDownload não aceita 'resumable' no construtor
                downloader = MediaIoBaseDownload(
                    fh,
                    request,
                    chunksize=chunk_size_mb * 1024 * 1024
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
