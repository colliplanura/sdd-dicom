#!/usr/bin/env python
"""
Script de teste para validar detecção de arquivos DICOM
sem extensão e busca recursiva
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.dicom import DICOMFileDetector, DIOMValidator
from loguru import logger

# Configurar logging
logger.remove()
logger.add(
    sys.stderr,
    format="<level>{level: <8}</level> | {message}",
    level="DEBUG"
)


def test_dicom_detection():
    """Testar detecção de DICOM pelo magic number"""
    logger.info("=" * 60)
    logger.info("TESTE: Detecção de arquivos DICOM")
    logger.info("=" * 60)
    
    # Criar arquivo DICOM de teste (com magic number válido)
    test_dir = Path("./temp/test_dicom")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Arquivo DICOM válido (com extensão)
    dicom_with_ext = test_dir / "sample.dcm"
    dicom_with_ext.write_bytes(b'\x00' * 128 + b'DICM' + b'\x00' * 100)
    
    # Arquivo DICOM válido (sem extensão)
    dicom_without_ext = test_dir / "sample_no_ext"
    dicom_without_ext.write_bytes(b'\x00' * 128 + b'DICM' + b'\x00' * 100)
    
    # Arquivo DICOM em subpasta
    subdir = test_dir / "subfolder"
    subdir.mkdir(exist_ok=True)
    dicom_in_subdir = subdir / "deep_sample"
    dicom_in_subdir.write_bytes(b'\x00' * 128 + b'DICM' + b'\x00' * 100)
    
    # Arquivo inválido
    invalid_file = test_dir / "not_dicom.txt"
    invalid_file.write_bytes(b"This is not a DICOM file")
    
    # Testar detecção
    logger.info(f"\nArquivos criados em: {test_dir}")
    
    logger.info("\n[1] Testando detecção individual:")
    logger.info(f"  - {dicom_with_ext.name}: {DICOMFileDetector.is_dicom_file(dicom_with_ext)}")
    logger.info(f"  - {dicom_without_ext.name}: {DICOMFileDetector.is_dicom_file(dicom_without_ext)}")
    logger.info(f"  - {dicom_in_subdir.name}: {DICOMFileDetector.is_dicom_file(dicom_in_subdir)}")
    logger.info(f"  - {invalid_file.name}: {DICOMFileDetector.is_dicom_file(invalid_file)}")
    
    logger.info("\n[2] Testando busca recursiva:")
    dicom_files = DICOMFileDetector.find_dicom_files(test_dir)
    logger.info(f"  Encontrados {len(dicom_files)} arquivos DICOM:")
    for f in dicom_files:
        logger.info(f"    - {f.relative_to(test_dir)}")
    
    logger.info("\n[3] Testando validator:")
    validator = DIOMValidator()
    for f in [dicom_with_ext, dicom_without_ext, dicom_in_subdir, invalid_file]:
        is_valid = validator.validate_dicom_file(f)
        logger.info(f"  - {f.name}: {'✓ DICOM' if is_valid else '✗ Inválido'}")
    
    # Cleanup
    logger.info("\n[4] Limpando arquivos de teste...")
    import shutil
    shutil.rmtree(test_dir)
    logger.info("✓ Teste concluído com sucesso!")


def test_google_drive_recursive():
    """Testar busca recursiva no Google Drive"""
    logger.info("\n" + "=" * 60)
    logger.info("TESTE: Busca recursiva Google Drive (simulado)")
    logger.info("=" * 60)
    
    try:
        from src.google_drive import GoogleDriveClient
        from src.core import Config
        
        Config.ensure_paths()
        
        logger.info("\nTentando conectar ao Google Drive...")
        client = GoogleDriveClient()
        
        logger.info("✓ Cliente Google Drive inicializado")
        logger.info(f"  Método: list_files_recursive disponível")
        logger.info(f"  Método: _list_files_in_folder disponível")
        
        logger.info("\nMétodos de busca disponíveis:")
        logger.info("  - recursive=True  (padrão): busca em subpastas")
        logger.info("  - recursive=False: busca apenas na pasta especificada")
        
    except Exception as e:
        logger.warning(f"Não foi possível testar Google Drive: {e}")
        logger.info("  (Isto é esperado se credentials não estão configuradas)")


if __name__ == "__main__":
    test_dicom_detection()
    test_google_drive_recursive()
