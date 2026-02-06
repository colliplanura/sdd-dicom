#!/usr/bin/env python3
"""
Verificar a estrutura profunda das pastas DICOM
"""
from src.google_drive.auth import GoogleDriveAuth
from src.google_drive.client import GoogleDriveClient

auth = GoogleDriveAuth('config/credentials.json', 'config/token.json')
auth.authenticate()
client = GoogleDriveClient()

# Verificar AAA3/7 (primeira subpasta do AAA3)
folder_id = '1pALyoowtM3o8jP9_WIIt9RPkxTY1686G'  # AAA3

# Listar conteúdo de AAA3
results = client.service.files().list(
    q=f"'{folder_id}' in parents and trashed=false",
    spaces='drive',
    fields='files(id, name, mimeType)',
    pageSize=20
).execute()

print('Conteúdo de AAA3:')
subfolder_7_id = None
for f in results.get('files', []):
    is_folder = f.get('mimeType') == 'application/vnd.google-apps.folder'
    print(f"- {f['name']} ({'pasta' if is_folder else 'arquivo'})")
    if f['name'] == '7':
        subfolder_7_id = f['id']

# Agora listar dentro de AAA3/7
if subfolder_7_id:
    print(f'\nConteúdo de AAA3/7:')
    results = client.service.files().list(
        q=f"'{subfolder_7_id}' in parents and trashed=false",
        spaces='drive',
        fields='files(id, name, mimeType, size)',
        pageSize=20
    ).execute()
    
    for f in results.get('files', [])[:10]:
        is_folder = f.get('mimeType') == 'application/vnd.google-apps.folder'
        mtype = 'pasta' if is_folder else 'arquivo'
        size = int(f.get('size', 0) or 0) / (1024*1024)
        print(f"- {f['name']} ({mtype}, {size:.1f}MB)")
