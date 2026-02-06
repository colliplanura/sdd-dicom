#!/usr/bin/env python
"""
Script de Diagnóstico para Problemas de Busca no Google Drive
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core import Config, setup_logging
from src.google_drive import GoogleDriveClient
from loguru import logger


def diagnose_folder_search():
    """Diagnosticar problema com busca de pasta"""
    print("\n" + "=" * 70)
    print("DIAGNÓSTICO: Problema ao Encontrar Pasta no Google Drive")
    print("=" * 70)
    
    try:
        Config.ensure_paths()
        Config.LOG_LEVEL = 'DEBUG'
        setup_logging()
        
        client = GoogleDriveClient()
        logger.info("✓ Conectado ao Google Drive\n")
        
        # Teste 1: Buscar pasta completa
        print("\n[Teste 1] Buscando caminho completo:")
        print(f"  Caminho: {Config.GOOGLE_DRIVE_FOLDER}")
        
        folder_id = client._find_folder_by_name(Config.GOOGLE_DRIVE_FOLDER)
        
        if folder_id:
            logger.info(f"✓ Pasta encontrada! ID: {folder_id}")
        else:
            logger.warning("✗ Pasta não encontrada. Testando componentes...\n")
            
            # Teste 2: Testar cada parte do caminho
            print("\n[Teste 2] Testando cada parte do caminho:")
            parts = [p.strip() for p in Config.GOOGLE_DRIVE_FOLDER.split('/') if p.strip()]
            
            for i, part in enumerate(parts):
                indent = "  " * (i + 1)
                print(f"\n{indent}[{i+1}] Buscando: {part}")
                
                found = client._find_folder_by_name(part)
                if found:
                    logger.info(f"{indent}✓ Encontrada! ID: {found}")
                else:
                    logger.error(f"{indent}✗ Não encontrada")
                    break
        
        # Teste 3: Listar pastas na raiz
        print("\n\n[Teste 3] Listando pastas na raiz do Google Drive:")
        
        try:
            request = client.service.files().list(
                q="mimeType='application/vnd.google-apps.folder' and trashed=false",
                spaces='drive',
                pageSize=50,
                fields='files(id, name)',
                orderBy='name'
            )
            
            results = client._execute_with_rate_limit(request)
            folders = results.get('files', [])
            
            if folders:
                print(f"  Encontradas {len(folders)} pastas na raiz:\n")
                for f in folders[:10]:  # Mostrar primeiras 10
                    print(f"    - {f['name']}")
                if len(folders) > 10:
                    print(f"    ... e mais {len(folders) - 10}")
            else:
                logger.warning("Nenhuma pasta encontrada na raiz")
        
        except Exception as e:
            logger.error(f"Erro ao listar pastas: {e}")
        
        # Teste 4: Sugestões
        print("\n\n[Sugestões]")
        print("""
1. Verifique se a pasta existe no Google Drive
2. Copie o nome exato (com espaços e caracteres especiais)
3. Se usar um caminho aninhado, garanta que todas as pastas existem
4. Se a busca falhar, tente usar o ID da pasta diretamente:
   
   client.list_files(folder_id='ID_DA_PASTA', max_results=10)
   
   Para encontrar o ID:
   - Abra a pasta no Google Drive
   - O ID está na URL: https://drive.google.com/drive/folders/ID_DA_PASTA
""")
    
    except Exception as e:
        logger.error(f"Erro no diagnóstico: {e}")
        import traceback
        traceback.print_exc()


def test_folder_access():
    """Testar acesso a pasta com ID"""
    print("\n" + "=" * 70)
    print("TESTE: Acesso com ID de Pasta")
    print("=" * 70)
    
    print("""
Para usar ID direto:

1. Abra a pasta no Google Drive
2. Copie o ID da URL:
   https://drive.google.com/drive/folders/XXXXXXXXXXX
   
3. Use assim:

   from src.google_drive import GoogleDriveClient
   client = GoogleDriveClient()
   files = client.list_files(
       folder_id='XXXXXXXXXXX',
       max_results=10
   )
""")


def test_alternative_paths():
    """Testar caminhos alternativos"""
    print("\n" + "=" * 70)
    print("TESTE: Caminhos Alternativos")
    print("=" * 70)
    
    try:
        Config.ensure_paths()
        setup_logging()
        
        client = GoogleDriveClient()
        
        # Caminhos alternativos para testar
        paths = [
            'Medicina/Doutorado IDOR/Exames/DICOM',
            'Exames/DICOM',
            'DICOM',
            'Exames',
            'Medicina/Doutorado',
        ]
        
        print("\nTestando caminhos alternativos:\n")
        
        for path in paths:
            print(f"  Testando: {path}...", end=' ')
            folder_id = client._find_folder_by_name(path)
            
            if folder_id:
                print(f"✓ ENCONTRADA (ID: {folder_id})")
            else:
                print("✗ não encontrada")
    
    except Exception as e:
        logger.error(f"Erro: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Diagnóstico de problemas com Google Drive'
    )
    parser.add_argument(
        '--diagnose',
        action='store_true',
        default=True,
        help='Executar diagnóstico completo (padrão)'
    )
    parser.add_argument(
        '--test-id',
        action='store_true',
        help='Mostrar como testar com ID'
    )
    parser.add_argument(
        '--test-paths',
        action='store_true',
        help='Testar caminhos alternativos'
    )
    
    args = parser.parse_args()
    
    if args.diagnose:
        diagnose_folder_search()
    if args.test_id:
        test_folder_access()
    if args.test_paths:
        test_alternative_paths()
    
    if not (args.diagnose or args.test_id or args.test_paths):
        diagnose_folder_search()
