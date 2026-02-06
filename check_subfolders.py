#!/usr/bin/env python3
"""
Verificar o conteúdo das subpastas DICOM
"""
from src.google_drive.auth import GoogleDriveAuth
from src.google_drive.client import GoogleDriveClient

auth = GoogleDriveAuth('config/credentials.json', 'config/token.json')
auth.authenticate()
client = GoogleDriveClient()

# Checar cada subpasta
subfolders = ['1pALyoowtM3o8jP9_WIIt9RPkxTY1686G', '17xFRfNtUVHkljlz4ZuTzXyYN7aEmPqTu', '1reXeWimQw4v8DM0ctc5ebHo9nsbMGdAV']
subfolder_names = ['AAA3', 'AAA2', 'AAA1']

for name, folder_id in zip(subfolder_names, subfolders):
    print(f'\n📁 {name}:')
    results = client.service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        spaces='drive',
        fields='files(id, name, mimeType, size)',
        pageSize=20
    ).execute()
    
    items = results.get('files', [])
    print(f'   Encontrados {len(items)} itens')
    for f in items[:5]:  # Mostrar primeiros 5
        mtype = 'pasta' if f.get('mimeType') == 'application/vnd.google-apps.folder' else 'arquivo'
        size = int(f.get('size', 0) or 0) / (1024*1024)
        print(f'   - {f["name"]} ({mtype}, {size:.1f}MB)')
    if len(items) > 5:
        print(f'   ... e {len(items)-5} outros')
