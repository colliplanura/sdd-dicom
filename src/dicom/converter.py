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
            
            # dcm2niix retorna exit code 3 mesmo com sucesso
            # Verificamos se encontramos a versão no stdout
            version_output = (result.stdout + result.stderr).strip()
            
            if "dcm2niiX version" in version_output or result.returncode in [0, 3]:
                # Extrair a versão
                version = version_output.split('\n')[0] if version_output else "desconhecida"
                logger.info(f"✓ dcm2niix detectado: {version}")
            else:
                # Erro real ao executar dcm2niix
                error_msg = result.stderr.strip() if result.stderr else "sem mensagem de erro"
                logger.error(f"dcm2niix retornou erro: {error_msg}")
                raise DIOMConversionError(
                    f"dcm2niix retornou erro ao verificar versão:\n{error_msg}\n\n"
                    f"Solução:\n"
                    f"  macOS:  brew install dcm2niix\n"
                    f"  Linux:  apt-get install dcm2niix\n"
                    f"  Docker: Use a imagem oficial com dcm2niix pré-instalado"
                )
        
        except FileNotFoundError:
            raise DIOMConversionError(
                f"❌ dcm2niix não encontrado no PATH\n\n"
                f"Caminho procurado: {self.dcm2niix_path}\n\n"
                f"Solução:\n"
                f"  1. macOS (Homebrew):\n"
                f"     brew install dcm2niix\n\n"
                f"  2. Linux (apt):\n"
                f"     sudo apt-get install dcm2niix\n\n"
                f"  3. Linux (conda):\n"
                f"     conda install -c conda-forge dcm2niix\n\n"
                f"  4. Compilar do código-fonte:\n"
                f"     https://github.com/rordenlab/dcm2niix\n\n"
                f"Depois de instalar, reinicie a aplicação."
            )
        except subprocess.TimeoutExpired:
            raise DIOMConversionError(
                f"❌ dcm2niix não respondeu após 5 segundos\n"
                f"Isso pode indicar:\n"
                f"  - Caminho incorreto: {self.dcm2niix_path}\n"
                f"  - Permissões insuficientes\n"
                f"  - Sistema muito lento"
            )
        except Exception as e:
            raise DIOMConversionError(
                f"❌ Erro inesperado ao verificar dcm2niix:\n{e}\n"
                f"Instale dcm2niix: brew install dcm2niix (macOS)"
            )
    
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
