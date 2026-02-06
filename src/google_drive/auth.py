"""
Autenticação com Google Drive
"""
import os
from pathlib import Path
from typing import Optional
from loguru import logger

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.service_account import Credentials as ServiceAccountCredentials

from ..core.config import GOOGLE_DRIVE_SCOPES
from ..core.exceptions import AuthenticationError


class GoogleDriveAuth:
    """Gerenciador de autenticação com Google Drive"""
    
    def __init__(
        self,
        credentials_file: Path,
        token_file: Path,
        scopes: Optional[list] = None
    ):
        """
        Inicializar autenticação
        
        Args:
            credentials_file: Caminho para credentials.json
            token_file: Caminho para armazenar token.json
            scopes: Scopes de acesso (padrão: leitura completa)
        """
        self.credentials_file = Path(credentials_file)
        self.token_file = Path(token_file)
        self.scopes = scopes or GOOGLE_DRIVE_SCOPES
        self.creds: Optional[Credentials] = None
    
    def authenticate(self) -> Credentials:
        """
        Realizar autenticação e retornar credenciais
        
        Estratégia:
        1. Se token.json existe e é válido, usar
        2. Se token expirado, renovar
        3. Senão, fazer login com OAuth 2.0
        
        Returns:
            Credenciais autenticadas
            
        Raises:
            AuthenticationError: Se falhar na autenticação
        """
        try:
            # Tentar carregar token existente
            if self.token_file.exists():
                self.creds = Credentials.from_authorized_user_file(
                    str(self.token_file),
                    self.scopes
                )
                logger.debug(f"Credenciais carregadas de {self.token_file}")
            
            # Se não há credenciais ou expirou, renovar/fazer login
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    logger.info("Renovando token expirado...")
                    self.creds.refresh(Request())
                else:
                    logger.info("Iniciando autenticação OAuth 2.0...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_file),
                        self.scopes
                    )
                    self.creds = flow.run_local_server(port=0)
                
                # Salvar token para próxima execução
                self.token_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.token_file, 'w') as token:
                    token.write(self.creds.to_json())
                logger.info(f"✓ Token salvo em {self.token_file}")
            
            logger.info("✓ Autenticação concluída com sucesso")
            return self.creds
        
        except FileNotFoundError as e:
            raise AuthenticationError(f"Arquivo de credenciais não encontrado: {e}")
        except Exception as e:
            raise AuthenticationError(f"Falha na autenticação: {e}")
    
    def get_credentials(self) -> Credentials:
        """Obter credenciais (autenticando se necessário)"""
        if not self.creds:
            self.authenticate()
        return self.creds


class ServiceAccountAuth:
    """Autenticação com Service Account (para servidores)"""
    
    def __init__(
        self,
        credentials_file: Path,
        scopes: Optional[list] = None
    ):
        """
        Inicializar com Service Account
        
        Args:
            credentials_file: Caminho para service-account-key.json
            scopes: Scopes de acesso
        """
        self.credentials_file = Path(credentials_file)
        self.scopes = scopes or GOOGLE_DRIVE_SCOPES
        self.creds: Optional[ServiceAccountCredentials] = None
    
    def authenticate(self) -> ServiceAccountCredentials:
        """Autenticar com Service Account"""
        try:
            self.creds = ServiceAccountCredentials.from_service_account_file(
                str(self.credentials_file),
                scopes=self.scopes
            )
            logger.info(f"✓ Service Account autenticado: {self.creds.service_account_email}")
            return self.creds
        except Exception as e:
            raise AuthenticationError(f"Falha na autenticação de Service Account: {e}")
    
    def get_credentials(self) -> ServiceAccountCredentials:
        """Obter credenciais"""
        if not self.creds:
            self.authenticate()
        return self.creds
