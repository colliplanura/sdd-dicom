#!/usr/bin/env python
"""
Script principal para executar a pipeline SDD-DICOM

Uso:
    python main.py --help
"""
import sys
import argparse
from pathlib import Path
from loguru import logger

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.core import Config, setup_logging
from src.google_drive import GoogleDriveClient
from src.dicom import DIOMConverter
from src.pipeline import BatchPipeline, ProcessingTask


def setup_args():
    """Configurar argumentos da linha de comando"""
    parser = argparse.ArgumentParser(
        description='SDD-DICOM - Conversão DICOM para NIfTI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Listar arquivos disponíveis
  python main.py --list

  # Processar lote de arquivos
  python main.py --process
        """
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='Listar arquivos DICOM disponíveis'
    )
    
    parser.add_argument(
        '--list-studies',
        action='store_true',
        help='Listar estudos DICOM (abordagem por estudo)'
    )
    
    parser.add_argument(
        '--process',
        action='store_true',
        help='Processar lote de arquivos'
    )
    
    parser.add_argument(
        '--process-studies',
        action='store_true',
        help='Processar estudos DICOM (abordagem por estudo)'
    )
    
    parser.add_argument(
        '--max-files',
        type=int,
        default=10,
        help='Máximo de arquivos a processar (padrão: 10)'
    )
    
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Nível de logging'
    )
    
    return parser.parse_args()


def list_dicom_files(client: GoogleDriveClient, max_files: int = 10):
    """Listar arquivos DICOM disponíveis"""
    try:
        logger.info(f"Listando até {max_files} arquivos DICOM...")
        
        files = client.list_files(
            folder_name=Config.GOOGLE_DRIVE_FOLDER,
            max_results=max_files
        )
        
        logger.info(f"\nEncontrados {len(files)} arquivos:\n")
        
        for i, f in enumerate(files, 1):
            size_bytes = int(f.get('size', 0) or 0)  # Converter para int
            size_mb = size_bytes / (1024 * 1024)
            logger.info(f"  {i}. {f['name']} ({size_mb:.1f} MB)")
        
        return files
    
    except Exception as e:
        logger.error(f"Erro ao listar arquivos: {e}")
        return []


def process_dicom_files(client: GoogleDriveClient, max_files: int = 10):
    """Processar arquivos DICOM"""
    try:
        # Listar arquivos
        files = client.list_files(
            folder_name=Config.GOOGLE_DRIVE_FOLDER,
            max_results=max_files
        )
        
        if not files:
            logger.error("Nenhum arquivo encontrado")
            return
        
        logger.info(f"Processando {len(files)} arquivos...")
        
        # Criar tarefas
        tasks = [
            ProcessingTask(
                file_id=f['id'],
                file_name=f['name'],
                patient_id=f"P{i:03d}",
                size_mb=int(f.get('size', 0) or 0) / (1024 * 1024)  # Converter para int
            )
            for i, f in enumerate(files, 1)
        ]
        
        # Criar pipeline
        pipeline = BatchPipeline(
            google_drive_client=client,
            dicom_converter=DIOMConverter()
        )
        
        # Processar
        results = pipeline.process_batch(tasks)
        
        logger.info(f"✓ Processamento concluído: {len(results)} sucesso")
    
    except Exception as e:
        logger.error(f"Erro no processamento: {e}")
        import traceback
        traceback.print_exc()


def list_dicom_studies(client: GoogleDriveClient, max_studies: int = 10):
    """Listar estudos DICOM disponíveis"""
    try:
        logger.info(f"Listando até {max_studies} estudos DICOM...")
        
        studies = client.list_dicom_studies(
            folder_name=Config.GOOGLE_DRIVE_FOLDER,
            max_results=max_studies
        )
        
        logger.info(f"\nEncontrados {len(studies)} estudos:\n")
        
        for i, study in enumerate(studies, 1):
            logger.info(f"  {i}. {study['name']} (ID: {study['study_number']})")
        
        return studies
    
    except Exception as e:
        logger.error(f"Erro ao listar estudos: {e}")
        return []


def process_dicom_studies(client: GoogleDriveClient, max_studies: int = 10):
    """Processar estudos DICOM"""
    try:
        # Listar estudos
        studies = client.list_dicom_studies(
            folder_name=Config.GOOGLE_DRIVE_FOLDER,
            max_results=max_studies
        )
        
        if not studies:
            logger.error("Nenhum estudo encontrado")
            return
        
        logger.info(f"Processando {len(studies)} estudos DICOM...")
        
        # Criar tarefas para cada estudo
        tasks = []
        for i, study in enumerate(studies, 1):
            # Para estudos, passamos study_info
            task = ProcessingTask(
                file_id=study['dicom_folder_id'],
                file_name=study['name'],
                patient_id=f"P{i:03d}",
                size_mb=0,  # Não aplicável para estudos
                study_info=study  # ← Passando informações do estudo
            )
            tasks.append(task)
        
        # Criar pipeline
        pipeline = BatchPipeline(
            google_drive_client=client,
            dicom_converter=DIOMConverter()
        )
        
        # Processar
        results = pipeline.process_batch(tasks)
        
        logger.info(f"✓ Processamento de estudos concluído: {len(results)} sucesso")
    
    except Exception as e:
        logger.error(f"Erro no processamento de estudos: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Função principal"""
    args = setup_args()
    
    # Configurar
    Config.LOG_LEVEL = args.log_level
    Config.ensure_paths()
    setup_logging()
    
    logger.info(f"SDD-DICOM v1.0.0")
    logger.info(f"Configuração carregada")
    
    # Inicializar cliente
    try:
        client = GoogleDriveClient()
    except Exception as e:
        logger.error(f"Falha ao conectar Google Drive: {e}")
        sys.exit(1)
    
    # Executar comando
    if args.list:
        list_dicom_files(client, args.max_files)
    
    elif args.list_studies:
        list_dicom_studies(client, args.max_files)
    
    elif args.process:
        process_dicom_files(client, args.max_files)
    
    elif args.process_studies:
        process_dicom_studies(client, args.max_files)
    
    else:
        # Sem argumento, mostrar ajuda
        logger.info("Use --help para ver opções disponíveis")
        logger.info("Exemplos:")
        logger.info("  python main.py --list               (listar arquivos)")
        logger.info("  python main.py --list-studies       (listar estudos)")
        logger.info("  python main.py --process            (processar arquivos)")
        logger.info("  python main.py --process-studies    (processar estudos)")


if __name__ == '__main__':
    main()
