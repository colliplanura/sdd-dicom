"""
Wrapper para dcm2niix - Conversão DICOM para NIfTI
"""
import subprocess
from pathlib import Path
from typing import Optional, Dict
from loguru import logger

from ..core.exceptions import DIOMConversionError
from ..core.config import DCM2NIIX_CONFIG


class DIOMConverter:
    """
    Wrapper para dcm2niix
    
    Executa conversão DICOM → NIfTI com:
    - Detecção de instalação
    - Timeout configurável
    - Captura de stderr/stdout
    - Tratamento de erros
    """
    
    def __init__(self, dcm2niix_path: str = "dcm2niix"):
        """
        Inicializar converter
        
        Args:
            dcm2niix_path: Caminho para executável dcm2niix
        """
        self.dcm2niix_path = dcm2niix_path
        self._verify_installation()
    
    def _verify_installation(self) -> None:
        """Verificar se dcm2niix está instalado"""
        try:
            result = subprocess.run(
                [self.dcm2niix_path, "-v"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"✓ dcm2niix detectado: {version}")
            else:
                raise DIOMConversionError(f"dcm2niix retornou erro: {result.stderr}")
        
        except FileNotFoundError:
            raise DIOMConversionError(
                f"dcm2niix não encontrado: {self.dcm2niix_path}\n"
                "Instale com: brew install dcm2niix (macOS) "
                "ou apt-get install dcm2niix (Linux)"
            )
        except subprocess.TimeoutExpired:
            raise DIOMConversionError("dcm2niix timeout ao verificar versão")
    
    def convert(
        self,
        input_dir: str,
        output_dir: str,
        filename_template: str = "%p_%t_%s",
        compress: bool = True,
        bids: bool = True,
        timeout_seconds: int = 600
    ) -> Dict:
        """
        Converter série DICOM para NIfTI
        
        Args:
            input_dir: Diretório com arquivos DICOM
            output_dir: Diretório de saída
            filename_template: Template de nome (%p=patient, %t=time, %s=series)
            compress: Gerar .nii.gz (vs .nii)
            bids: Gerar sidecars JSON (BIDS)
            timeout_seconds: Timeout em segundos
        
        Returns:
            Dict com {status, files} ou {status, error}
        """
        try:
            input_dir = Path(input_dir)
            output_dir = Path(output_dir)
            
            if not input_dir.is_dir():
                raise DIOMConversionError(f"Input directory not found: {input_dir}")
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Construir comando
            cmd = [
                self.dcm2niix_path,
                "-f", filename_template,
                "-o", str(output_dir),
            ]
            
            if compress:
                cmd.extend(["-z", "y"])
            
            if bids:
                cmd.extend(["-b", "y"])
            
            # Adicionar diretório de entrada no final
            cmd.append(str(input_dir))
            
            logger.info(f"Executando: {' '.join(cmd)}")
            
            # Executar
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=str(output_dir)
            )
            
            if result.returncode == 0:
                logger.info(f"✓ Conversão bem-sucedida: {input_dir}")
                
                # Procurar outputs
                output_files = self._find_outputs(output_dir)
                return {
                    'status': 'success',
                    'files': output_files
                }
            else:
                error_msg = result.stderr or result.stdout
                logger.error(f"Conversão falhou: {error_msg}")
                return {
                    'status': 'error',
                    'error': error_msg
                }
        
        except subprocess.TimeoutExpired:
            logger.error(f"Conversão expirou (timeout): {input_dir}")
            return {'status': 'timeout', 'error': f'Timeout after {timeout_seconds}s'}
        
        except Exception as e:
            logger.error(f"Erro na conversão: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _find_outputs(self, output_dir: Path) -> Dict[str, Path]:
        """Encontrar arquivos de saída gerados"""
        outputs = {}
        
        # Procurar .nii.gz ou .nii
        nifti_files = list(output_dir.glob('*.nii.gz'))
        if not nifti_files:
            nifti_files = list(output_dir.glob('*.nii'))
        
        # Procurar .json sidecars
        json_files = list(output_dir.glob('*.json'))
        
        if nifti_files:
            outputs['nifti'] = [str(f) for f in nifti_files]
        
        if json_files:
            outputs['json'] = [str(f) for f in json_files]
        
        return outputs
