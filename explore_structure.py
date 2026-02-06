#!/usr/bin/env python3
"""
Explorar a estrutura de pastas e arquivos DICOM no Google Drive
"""

import sys
from loguru import logger
from src.core.config import Config
from src.google_drive.auth import GoogleDriveAuth
from src.google_drive.client import GoogleDriveClient
from src.dicom.file_detector import DICOMFileDetector

logger.remove()
logger.add(
    sys.stderr,
    format="<level>{level: <8}</level> | <level>{message}</level>",
    colorize=True
)

def explore_structure(client, folder_id, prefix="", level=0, max_level=3):
    """Explorar recursivamente a estrutura de pastas"""
    if level > max_level:
        return
    
    indent = "  " * level
    
    try:
        results = client.service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            spaces='drive',
            fields='files(id, name, mimeType, size)',
            pageSize=100
        ).execute()
        
        items = results.get('files', [])
        
        # Separar pastas e arquivos
        folders = [f for f in items if f.get('mimeType') == 'application/vnd.google-apps.folder']
        files = [f for f in items if f.get('mimeType') != 'application/vnd.google-apps.folder']
        
        # Mostrar pastas
        for folder in folders:
            print(f"{indent}📁 {folder['name']}")
            explore_structure(client, folder['id'], prefix + folder['name'] + "/", level + 1, max_level)
        
        # Mostrar arquivos
        for file in files:
            size_mb = int(file.get('size', 0) or 0) / (1024 * 1024)
            print(f"{indent}  📄 {file['name']} ({size_mb:.1f} MB)")
            
    except Exception as e:
        print(f"{indent}  ❌ Erro ao listar: {e}")

def main():
    logger.info("Conectando ao Google Drive...")
    
    config = Config()
    auth = GoogleDriveAuth(
        credentials_file="config/credentials.json",
        token_file="config/token.json"
    )
    auth.authenticate()
    client = GoogleDriveClient()
    
    # Encontrar a pasta DICOM
    logger.info("Buscando pasta: Medicina/Doutorado IDOR/Exames/DICOM")
    
    try:
        files = client.list_files(folder_name="Medicina/Doutorado IDOR/Exames/DICOM", max_results=5)
        
        if not files:
            logger.error("Nenhum arquivo encontrado")
            return
        
        # Pegar o ID da pasta
        folder_id_results = client.service.files().list(
            q="name='DICOM' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id, name)',
            pageSize=1
        ).execute()
        
        if not folder_id_results.get('files'):
            logger.error("Pasta DICOM não encontrada")
            return
        
        dicom_folder = folder_id_results['files'][0]
        folder_id = dicom_folder['id']
        
        logger.info(f"✓ Pasta encontrada: {dicom_folder['name']} (ID: {folder_id})")
        logger.info("")
        logger.info("📊 ESTRUTURA DE PASTAS E ARQUIVOS:")
        logger.info("=" * 60)
        print(f"Medicina/Doutorado IDOR/Exames/DICOM/")
        explore_structure(client, folder_id, "", 0, 4)
        
    except Exception as e:
        logger.error(f"Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
