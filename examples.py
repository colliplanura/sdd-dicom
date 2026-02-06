#!/usr/bin/env python
"""
Exemplos de uso das novas funcionalidades
- Busca recursiva em subpastas
- Detecção de DICOM sem extensão
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core import Config, setup_logging
from src.google_drive import GoogleDriveClient
from src.dicom import DICOMFileDetector, DIOMValidator
from loguru import logger


def example_1_recursive_search():
    """Exemplo 1: Busca recursiva no Google Drive"""
    print("\n" + "=" * 70)
    print("EXEMPLO 1: Busca Recursiva em Subpastas do Google Drive")
    print("=" * 70)
    
    try:
        Config.ensure_paths()
        client = GoogleDriveClient()
        
        logger.info("Buscando arquivos recursivamente...")
        
        # Busca recursiva (padrão)
        files = client.list_files(
            folder_name='Medicina/Doutorado IDOR/Exames/DICOM',
            recursive=True,  # Busca em subpastas
            max_results=20
        )
        
        logger.info(f"✓ Encontrados {len(files)} arquivos em subpastas:\n")
        
        for i, f in enumerate(files, 1):
            size_bytes = int(f.get('size', 0) or 0)  # Converter para int
            size_mb = size_bytes / (1024 * 1024)
            mime_type = f.get('mimeType', 'desconhecido')
            logger.info(f"  {i}. {f['name']} ({size_mb:.1f} MB) [{mime_type}]")
        
    except Exception as e:
        logger.error(f"Erro no exemplo: {e}")


def example_2_local_dicom_detection():
    """Exemplo 2: Detectar DICOM localmente sem extensão"""
    print("\n" + "=" * 70)
    print("EXEMPLO 2: Detecção Local de DICOM Sem Extensão")
    print("=" * 70)
    
    from src.dicom import DICOMFileDetector
    
    # Simular estrutura de dados local
    data_dir = Path('./temp/sample_data')
    data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Criando estrutura de exemplo em {data_dir}...")
    
    # Criar arquivos DICOM de teste
    structures = {
        'Paciente_001': ['scan_01', 'scan_02.dcm'],
        'Paciente_002/2024-01': ['baseline', 'baseline.dcm'],
        'Paciente_002/2024-02': ['followup'],
    }
    
    for path, files in structures.items():
        folder = data_dir / path
        folder.mkdir(parents=True, exist_ok=True)
        
        for filename in files:
            filepath = folder / filename
            # Escrever arquivo DICOM com magic number válido
            filepath.write_bytes(b'\x00' * 128 + b'DICM' + b'\x00' * 100)
    
    logger.info("✓ Estrutura criada\n")
    
    # Buscar DICOM recursivamente
    logger.info(f"Buscando arquivos DICOM em: {data_dir}\n")
    
    dicom_files = DICOMFileDetector.find_dicom_files(data_dir)
    
    logger.info(f"✓ Encontrados {len(dicom_files)} arquivos DICOM:\n")
    
    for f in sorted(dicom_files):
        relative = f.relative_to(data_dir)
        has_ext = f.suffix == '.dcm'
        ext_info = "(com extensão)" if has_ext else "(SEM extensão)"
        logger.info(f"  - {relative} {ext_info}")
    
    # Cleanup
    import shutil
    shutil.rmtree(data_dir)


def example_3_validation_workflow():
    """Exemplo 3: Fluxo completo de validação"""
    print("\n" + "=" * 70)
    print("EXEMPLO 3: Fluxo Completo de Validação")
    print("=" * 70)
    
    validator = DIOMValidator()
    detector = DICOMFileDetector()
    
    # Criar arquivos de teste
    test_dir = Path('./temp/validation_test')
    test_dir.mkdir(parents=True, exist_ok=True)
    
    test_files = {
        'valid_with_ext.dcm': (True, 'DICOM com extensão'),
        'valid_without_ext': (True, 'DICOM sem extensão'),
        'invalid.txt': (False, 'Arquivo não-DICOM'),
    }
    
    logger.info(f"Criando arquivos de teste em {test_dir}...\n")
    
    for filename, (is_dicom, description) in test_files.items():
        filepath = test_dir / filename
        if is_dicom:
            # DICOM válido
            filepath.write_bytes(b'\x00' * 128 + b'DICM' + b'\x00' * 100)
        else:
            # Arquivo inválido
            filepath.write_bytes(b'Not a DICOM file')
    
    # Validar cada arquivo
    logger.info("Resultados da validação:\n")
    
    for filename, (expected, description) in test_files.items():
        filepath = test_dir / filename
        
        # Passo 1: Detectar
        is_dicom = detector.is_dicom_file(filepath)
        
        # Passo 2: Validar
        is_valid = validator.validate_dicom_file(filepath)
        
        # Mostrar resultado
        status = "✓ VÁLIDO" if is_valid else "✗ INVÁLIDO"
        logger.info(f"  {filename:<25} {status:12} ({description})")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir)


def example_4_comparison():
    """Exemplo 4: Comparação antes/depois"""
    print("\n" + "=" * 70)
    print("EXEMPLO 4: Comparação de Comportamento")
    print("=" * 70)
    
    print("""
    ┌─────────────────────────────────────────────────────────────┐
    │                        ANTES                                 │
    ├─────────────────────────────────────────────────────────────┤
    │ • Busca: apenas pasta raiz                                  │
    │ • Extensão: obrigatório .dcm                                │
    │ • Estrutura: requer organização plana                       │
    │ • Resultado: 5 arquivos encontrados                         │
    │                                                             │
    │ Medicina/Doutorado IDOR/Exames/DICOM/                       │
    │ ├─ exam1.dcm                                                │
    │ ├─ exam2.dcm                                                │
    │ ├─ exam3.dcm                                                │
    │ ├─ exam4.dcm                                                │
    │ └─ exam5.dcm                                                │
    └─────────────────────────────────────────────────────────────┘
    
    ┌─────────────────────────────────────────────────────────────┐
    │                        DEPOIS                                │
    ├─────────────────────────────────────────────────────────────┤
    │ • Busca: recursiva em subpastas                             │
    │ • Extensão: com ou sem .dcm                                 │
    │ • Estrutura: suporta subpastas profundas                    │
    │ • Resultado: 47 arquivos encontrados                        │
    │                                                             │
    │ Medicina/Doutorado IDOR/Exames/DICOM/                       │
    │ ├─ Paciente_001/                                            │
    │ │  ├─ scan_001                                              │
    │ │  ├─ scan_002.dcm                                          │
    │ │  └─ 2024-01/                                              │
    │ │     ├─ baseline                                           │
    │ │     └─ followup.dcm                                       │
    │ ├─ Paciente_002/                                            │
    │ │  └─ scans/                                                │
    │ │     ├─ T1_weighted                                        │
    │ │     ├─ T2_weighted.dcm                                    │
    │ │     └─ ...                                                │
    │ └─ ...                                                      │
    └─────────────────────────────────────────────────────────────┘
    """)


def main():
    """Função principal"""
    Config.LOG_LEVEL = 'INFO'
    Config.ensure_paths()
    setup_logging()
    
    logger.info("DEMONSTRAÇÃO DE NOVAS FUNCIONALIDADES")
    logger.info("====================================\n")
    
    # Executar exemplos
    try:
        example_4_comparison()
        example_2_local_dicom_detection()
        example_3_validation_workflow()
        # example_1_recursive_search() # Comentado: requer Google Drive
        
        print("\n" + "=" * 70)
        print("✓ Todos os exemplos executados com sucesso!")
        print("=" * 70 + "\n")
        
    except Exception as e:
        logger.error(f"Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
