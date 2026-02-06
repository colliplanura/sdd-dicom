"""
Exceções customizadas do SDD-DICOM
"""

class SddDicomError(Exception):
    """Exceção base para erros do SDD-DICOM"""
    pass


class ConfigurationError(SddDicomError):
    """Erro de configuração"""
    pass


class AuthenticationError(SddDicomError):
    """Erro de autenticação com Google Drive"""
    pass


class GoogleDriveError(SddDicomError):
    """Erro geral na interação com Google Drive"""
    pass


class FileNotFoundError(GoogleDriveError):
    """Arquivo não encontrado no Google Drive"""
    pass


class DownloadError(GoogleDriveError):
    """Erro ao fazer download"""
    pass


class UploadError(GoogleDriveError):
    """Erro ao fazer upload"""
    pass


class DIOMConversionError(SddDicomError):
    """Erro ao converter DICOM para NIfTI"""
    pass


class ValidationError(SddDicomError):
    """Erro de validação de dados"""
    pass


class TimeoutError(SddDicomError):
    """Operação expirou"""
    pass


class RateLimitError(GoogleDriveError):
    """Rate limit atingido"""
    pass
