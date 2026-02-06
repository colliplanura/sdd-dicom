#!/usr/bin/env python3
"""
Testar download de estudo DICOM
"""
from pathlib import Path
from src.google_drive.auth import GoogleDriveAuth
from src.google_drive.client import GoogleDriveClient

auth = GoogleDriveAuth('config/credentials.json', 'config/token.json')
auth.authenticate()
client = GoogleDriveClient()

# Listar 1 estudo
studies = client.list_dicom_studies('Medicina/Doutorado IDOR/Exames/DICOM', max_results=1)

if studies:
    study = studies[0]
    print(f'\nBaixando estudo: {study["name"]}')
    
    # Download
    output_dir = Path('temp/test_study')
    study_path = client.download_study(study, output_dir.parent, chunk_size_mb=50)
    
    if study_path:
        print(f'✓ Estudo baixado para: {study_path}')
        
        # Listar arquivos baixados
        import subprocess
        result = subprocess.run(['find', str(study_path), '-type', 'f'], 
                              capture_output=True, text=True)
        files = [f for f in result.stdout.strip().split('\n') if f]
        print(f'\nArquivos baixados: {len(files)}')
        for f in files[:10]:
            print(f'  - {Path(f).name}')
        if len(files) > 10:
            print(f'  ... e {len(files)-10} outros')
    else:
        print('✗ Falha no download')
