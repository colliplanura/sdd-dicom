#!/usr/bin/env python3
"""
Script para listar todas as pastas no Google Drive
Útil para descobrir a estrutura correta de pastas
"""

from src.google_drive.client import GoogleDriveClient
from loguru import logger

def list_all_folders():
    """Lista todas as pastas no Google Drive"""
    try:
        client = GoogleDriveClient(credentials_path='config/credentials.json')
        logger.info("Conectado ao Google Drive")
        
        # Listar todas as pastas na raiz
        logger.info("=" * 60)
        logger.info("PASTAS NA RAIZ DO GOOGLE DRIVE:")
        logger.info("=" * 60)
        
        folders = client.service.files().list(
            spaces='drive',
            fields='files(id, name, mimeType, parents)',
            pageSize=100,
            q="mimeType='application/vnd.google-apps.folder' and trashed=false"
        ).execute()
        
        if not folders.get('files'):
            logger.warning("Nenhuma pasta encontrada")
            return
        
        # Criar dicionário de pastas por ID
        folder_dict = {}
        for folder in folders['files']:
            folder_dict[folder['id']] = folder
            
        # Exibir pastas
        for i, folder in enumerate(folders['files'], 1):
            logger.info(f"{i}. {folder['name']} (ID: {folder['id'][:20]}...)")
        
        # Agora listar todas as subpastas (1 nível de profundidade)
        logger.info("")
        logger.info("=" * 60)
        logger.info("ESTRUTURA DE PASTAS (com subpastas):")
        logger.info("=" * 60)
        
        for folder in folders['files']:
            folder_name = folder['name']
            folder_id = folder['id']
            
            logger.info(f"\n📁 {folder_name}/")
            
            # Listar subpastas
            subfolders = client.service.files().list(
                spaces='drive',
                fields='files(id, name, mimeType)',
                pageSize=50,
                q=f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            ).execute()
            
            if subfolders.get('files'):
                for subfolder in subfolders['files']:
                    logger.info(f"   └── {subfolder['name']}/")
                    
                    # Listar arquivos nesta subpasta (mostra os primeiros 3)
                    files_in_subfolder = client.service.files().list(
                        spaces='drive',
                        fields='files(id, name, size)',
                        pageSize=3,
                        q=f"'{subfolder['id']}' in parents and trashed=false"
                    ).execute()
                    
                    if files_in_subfolder.get('files'):
                        for file in files_in_subfolder['files'][:3]:
                            size_bytes = int(file.get('size', 0) or 0)  # Proteção extra
                            size_mb = size_bytes / (1024*1024)
                            logger.info(f"       • {file['name']} ({size_mb:.1f} MB)")
            else:
                # Se não tem subpastas, listar arquivos direto
                files_in_folder = client.service.files().list(
                    spaces='drive',
                    fields='files(id, name, size)',
                    pageSize=3,
                    q=f"'{folder_id}' in parents and trashed=false"
                ).execute()
                
                if files_in_folder.get('files'):
                    for file in files_in_folder['files'][:3]:
                        size_bytes = int(file.get('size', 0) or 0)  # Proteção extra
                        size_mb = size_bytes / (1024*1024)
                        logger.info(f"   • {file['name']} ({size_mb:.1f} MB)")
                else:
                    logger.info("   (vazia)")
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ Para usar uma pasta, copie o caminho exato acima")
        logger.info("   Exemplo: GD_FOLDER=Pasta/Subfolder/DICOM")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Erro: {e}")

if __name__ == "__main__":
    list_all_folders()
