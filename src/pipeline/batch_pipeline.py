"""
Pipeline Batch - Orquestrador principal de processamento
"""
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass
import time
from loguru import logger

from ..core.config import Config
from ..core.types import ProcessingStatus, ProcessingResult
from ..core.exceptions import SddDicomError
from ..google_drive import GoogleDriveClient
from ..dicom import DIOMConverter, DIOMValidator
from ..utils import (
    calculate_checksum,
    ensure_directory,
    clean_temp_directory,
    retry_with_backoff,
    CircuitBreaker
)


@dataclass
class ProcessingTask:
    """Tarefa de processamento"""
    file_id: str
    file_name: str
    patient_id: str
    size_mb: float


class BatchPipeline:
    """
    Orquestrador do pipeline de conversão
    
    Fluxo:
    1. DESCOBERTA: Listar arquivos DICOM no Drive
    2. DOWNLOAD: Baixar em paralelo (ThreadPoolExecutor)
    3. VALIDAÇÃO: Validar DICOM
    4. CONVERSÃO: Converter para NIfTI (ProcessPoolExecutor)
    5. UPLOAD: Fazer upload dos resultados (ThreadPoolExecutor)
    """
    
    def __init__(
        self,
        google_drive_client: Optional[GoogleDriveClient] = None,
        dicom_converter: Optional[DIOMConverter] = None,
        config: Optional[Config.__class__] = None
    ):
        """
        Inicializar pipeline
        
        Args:
            google_drive_client: Cliente Google Drive
            dicom_converter: Converter DICOM
            config: Configuração
        """
        self.config = config or Config
        self.google_drive = google_drive_client or GoogleDriveClient()
        self.converter = dicom_converter or DIOMConverter()
        self.validator = DIOMValidator()
        
        # Circuit breaker para Google Drive
        self.drive_circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout_seconds=60
        )
        
        # Estatísticas
        self.stats = {
            'total': 0,
            'completed': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': None,
            'end_time': None,
        }
        
        logger.info("✓ BatchPipeline inicializado")
    
    def process_batch(self, tasks: List[ProcessingTask]) -> List[ProcessingResult]:
        """
        Processar lote de tarefas
        
        Args:
            tasks: Lista de tarefas
        
        Returns:
            Lista de resultados
        """
        self.stats['start_time'] = time.time()
        self.stats['total'] = len(tasks)
        
        logger.info(f"Iniciando processamento de {len(tasks)} tarefas")
        
        results = []
        
        # Download em paralelo (I/O-bound)
        logger.info("[1/5] DOWNLOAD - Iniciando downloads paralelos")
        downloaded_files = self._download_stage(tasks)
        
        # Validação DICOM
        logger.info("[2/5] VALIDAÇÃO - Validando arquivos DICOM")
        validated_files = self._validate_stage(downloaded_files)
        
        # Conversão em paralelo (CPU-bound)
        logger.info("[3/5] CONVERSÃO - Convertendo para NIfTI")
        converted_files = self._conversion_stage(validated_files)
        
        # Upload em paralelo (I/O-bound)
        logger.info("[4/5] UPLOAD - Fazendo upload dos resultados")
        results = self._upload_stage(converted_files)
        
        # Limpeza
        logger.info("[5/5] LIMPEZA - Removendo arquivos temporários")
        self._cleanup_stage()
        
        self.stats['end_time'] = time.time()
        
        # Relatório final
        self._print_summary(results)
        
        return results
    
    def _download_stage(self, tasks: List[ProcessingTask]) -> List[Dict]:
        """
        Estágio 1: Download de arquivos
        
        Uses: ThreadPoolExecutor (I/O-bound)
        """
        ensure_directory(self.config.TEMP_DIR)
        
        downloaded = []
        
        with ThreadPoolExecutor(max_workers=self.config.MAX_WORKERS_DOWNLOAD) as executor:
            futures = {}
            
            for task in tasks:
                output_path = self.config.TEMP_DIR / f"{task.file_id}.dcm"
                futures[executor.submit(
                    self._download_file,
                    task.file_id,
                    output_path
                )] = task
            
            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                    if result:
                        downloaded.append(result)
                        logger.info(f"✓ Download: {task.file_name}")
                except Exception as e:
                    logger.error(f"✗ Download falhou: {task.file_name} - {e}")
        
        logger.info(f"Download concluído: {len(downloaded)}/{len(tasks)}")
        return downloaded
    
    @retry_with_backoff(max_retries=3)
    def _download_file(self, file_id: str, output_path: Path) -> Optional[Dict]:
        """Download individual com retry"""
        try:
            self.google_drive.download_file(
                file_id,
                output_path,
                timeout_seconds=self.config.TIMEOUT_DOWNLOAD_SECONDS
            )
            return {
                'file_id': file_id,
                'local_path': output_path,
                'status': ProcessingStatus.DOWNLOADING
            }
        except Exception as e:
            logger.error(f"Download falhou: {e}")
            raise
    
    def _validate_stage(self, downloaded: List[Dict]) -> List[Dict]:
        """
        Estágio 2: Validação de arquivos DICOM
        """
        validated = []
        
        for item in downloaded:
            try:
                local_path = Path(item['local_path'])
                
                if self.validator.validate_dicom_file(local_path):
                    validated.append(item)
                    logger.debug(f"✓ DICOM válido: {local_path.name}")
                else:
                    logger.warning(f"✗ DICOM inválido: {local_path.name}")
                    self.stats['skipped'] += 1
            
            except Exception as e:
                logger.error(f"Erro na validação: {e}")
                self.stats['failed'] += 1
        
        logger.info(f"Validação concluída: {len(validated)}/{len(downloaded)}")
        return validated
    
    def _conversion_stage(self, validated: List[Dict]) -> List[Dict]:
        """
        Estágio 3: Conversão DICOM → NIfTI
        
        Uses: ProcessPoolExecutor (CPU-bound)
        """
        converted = []
        
        with ProcessPoolExecutor(max_workers=self.config.MAX_WORKERS_PROCESS) as executor:
            futures = {}
            
            for item in validated:
                futures[executor.submit(
                    self._convert_file,
                    item['local_path']
                )] = item
            
            for future in as_completed(futures):
                item = futures[future]
                try:
                    result = future.result()
                    if result:
                        converted.append(result)
                except Exception as e:
                    logger.error(f"Conversão falhou: {item['file_id']} - {e}")
                    self.stats['failed'] += 1
        
        logger.info(f"Conversão concluída: {len(converted)}/{len(validated)}")
        return converted
    
    def _convert_file(self, local_path: Path) -> Optional[Dict]:
        """Conversão individual"""
        try:
            local_path = Path(local_path)
            output_dir = local_path.parent / f"{local_path.stem}_nifti"
            
            result = self.converter.convert(
                str(local_path),
                str(output_dir),
                timeout_seconds=self.config.TIMEOUT_CONVERSION_SECONDS
            )
            
            if result['status'] == 'success':
                return {
                    'local_path': local_path,
                    'output_dir': output_dir,
                    'output_files': result['files'],
                    'status': ProcessingStatus.CONVERTING
                }
            else:
                raise Exception(result.get('error', 'Conversão falhou'))
        
        except Exception as e:
            logger.error(f"Erro na conversão: {e}")
            raise
    
    def _upload_stage(self, converted: List[Dict]) -> List[ProcessingResult]:
        """
        Estágio 4: Upload de resultados
        
        Uses: ThreadPoolExecutor (I/O-bound)
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=self.config.MAX_WORKERS_UPLOAD) as executor:
            futures = {}
            
            for item in converted:
                futures[executor.submit(
                    self._upload_file,
                    item
                )] = item
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        self.stats['completed'] += 1
                except Exception as e:
                    logger.error(f"Upload falhou: {e}")
                    self.stats['failed'] += 1
        
        logger.info(f"Upload concluído: {len(results)} arquivos")
        return results
    
    @retry_with_backoff(max_retries=3)
    def _upload_file(self, item: Dict) -> Optional[ProcessingResult]:
        """Upload individual com retry"""
        try:
            output_files = item['output_files']
            
            # Upload NIfTI
            if 'nifti' in output_files:
                for nifti_file in output_files['nifti']:
                    self.google_drive.upload_file(
                        nifti_file,
                        self._get_output_folder_id()
                    )
            
            # Upload JSON
            if 'json' in output_files:
                for json_file in output_files['json']:
                    self.google_drive.upload_file(
                        json_file,
                        self._get_output_folder_id()
                    )
            
            return ProcessingResult(
                file_id=str(item['local_path']),
                patient_id='unknown',
                status=ProcessingStatus.COMPLETED,
                input_path=str(item['local_path']),
                output_path=str(item['output_dir']),
                error=None,
                duration_seconds=0
            )
        
        except Exception as e:
            logger.error(f"Erro no upload: {e}")
            raise
    
    def _cleanup_stage(self):
        """Estágio 5: Limpeza de arquivos temporários"""
        try:
            removed = clean_temp_directory(self.config.TEMP_DIR)
            logger.info(f"✓ Limpeza concluída: {removed} arquivos removidos")
        except Exception as e:
            logger.warning(f"Erro na limpeza: {e}")
    
    def _get_output_folder_id(self) -> str:
        """Obter ID da pasta de output"""
        # TODO: Implementar caching de folder_id
        folders = self.google_drive.list_files(
            folder_name=self.config.GOOGLE_DRIVE_OUTPUT_FOLDER,
            max_results=1
        )
        if folders:
            return folders[0]['id']
        raise Exception("Pasta de output não encontrada")
    
    def _print_summary(self, results: List[ProcessingResult]):
        """Imprimir resumo de execução"""
        elapsed = self.stats['end_time'] - self.stats['start_time']
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("RESUMO DE EXECUÇÃO")
        logger.info("=" * 60)
        logger.info(f"Total de tarefas: {self.stats['total']}")
        logger.info(f"Completadas: {self.stats['completed']}")
        logger.info(f"Falhadas: {self.stats['failed']}")
        logger.info(f"Ignoradas: {self.stats['skipped']}")
        logger.info(f"Tempo total: {elapsed:.2f}s ({elapsed/60:.2f} min)")
        logger.info("=" * 60)
