#!/usr/bin/env python3
"""
Encontrar arquivos DICOM reais recursivamente
"""
from src.google_drive.auth import GoogleDriveAuth
from src.google_drive.client import GoogleDriveClient

auth = GoogleDriveAuth('config/credentials.json', 'config/token.json')
auth.authenticate()
client = GoogleDriveClient()

# Buscar arquivos recursivamente
all_files = client._list_files_recursive('1TuMvrvnNrMFWJO-Vq02d2Uo2WGe39_Dn', max_results=1000)

print(f'Total de arquivos encontrados: {len(all_files)}')
print()

# Agrupar por tipo
by_name = {}
for f in all_files:
    name = f['name']
    by_name[name] = by_name.get(name, 0) + 1

print('Arquivos mais comuns:')
for name in sorted(by_name.keys(), key=lambda x: -by_name[x])[:15]:
    print(f'  {name}: {by_name[name]}x')

# Procurar por arquivos sem extensão comum
print()
print('Arquivos sem extensão comum (potenciais DICOM):')
count = 0
for f in all_files:
    name = f['name']
    if '.' not in name or name.startswith('.'):
        size_kb = int(f.get('size', 0) or 0) / 1024
        print(f'  {name} ({size_kb:.0f}KB)')
        count += 1
        if count >= 15:
            break

if count == 0:
    print('  Nenhum arquivo sem extensão encontrado nos primeiros 1000')
