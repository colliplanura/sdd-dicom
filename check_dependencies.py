#!/usr/bin/env python
"""
Diagnóstico de Dependências - Verificar se tudo está instalado
"""
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger


def check_python_version():
    """Verificar versão do Python"""
    print("\n" + "=" * 70)
    print("1. VERIFICAÇÃO: Versão do Python")
    print("=" * 70)
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    print(f"Python: {version_str}")
    
    if version.major >= 3 and version.minor >= 8:
        print("✓ Versão compatível (Python 3.8+)")
        return True
    else:
        print("✗ Versão incompatível (requer Python 3.8+)")
        return False


def check_dcm2niix():
    """Verificar se dcm2niix está instalado"""
    print("\n" + "=" * 70)
    print("2. VERIFICAÇÃO: dcm2niix (Conversor DICOM → NIfTI)")
    print("=" * 70)
    
    try:
        result = subprocess.run(
            ['dcm2niix', '-v'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # dcm2niix retorna exit code 3 mesmo com sucesso
        # Verificar se encontramos a versão
        output = (result.stdout + result.stderr).strip()
        
        if "dcm2niiX version" in output or result.returncode in [0, 3]:
            # Extrair a versão
            version_line = output.split('\n')[0] if output else "desconhecida"
            print(f"✓ dcm2niix instalado")
            print(f"  Versão: {version_line}")
            return True
        else:
            print("✗ dcm2niix retornou erro inesperado")
            print(f"  Exit code: {result.returncode}")
            print(f"  Stdout: {result.stdout}")
            print(f"  Stderr: {result.stderr}")
            return False
    
    except FileNotFoundError:
        print("✗ dcm2niix NÃO ENCONTRADO")
        print("\n  Solução para macOS:")
        print("    brew install dcm2niix")
        print("\n  Solução para Linux:")
        print("    sudo apt-get install dcm2niix")
        print("\n  Solução com Conda:")
        print("    conda install -c conda-forge dcm2niix")
        return False
    
    except subprocess.TimeoutExpired:
        print("✗ dcm2niix não respondeu (timeout)")
        return False


def check_python_packages():
    """Verificar pacotes Python necessários"""
    print("\n" + "=" * 70)
    print("3. VERIFICAÇÃO: Pacotes Python")
    print("=" * 70)
    
    required_packages = {
        'google-auth-oauthlib': 'Google Drive Auth',
        'google-auth-httplib2': 'Google Drive HTTP',
        'google-api-python-client': 'Google Drive API',
        'loguru': 'Logging',
        'pydicom': 'Leitura DICOM (opcional)',
    }
    
    all_ok = True
    
    for package, description in required_packages.items():
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package:<30} ({description})")
        except ImportError:
            print(f"✗ {package:<30} ({description}) - NÃO INSTALADO")
            all_ok = False
    
    return all_ok


def check_credentials():
    """Verificar arquivo de credenciais"""
    print("\n" + "=" * 70)
    print("4. VERIFICAÇÃO: Credenciais do Google Drive")
    print("=" * 70)
    
    cred_path = Path('./config/credentials.json')
    token_path = Path('./config/token.json')
    
    if cred_path.exists():
        print(f"✓ Arquivo de credenciais encontrado")
        print(f"  {cred_path}")
    else:
        print(f"✗ Arquivo de credenciais NÃO ENCONTRADO")
        print(f"  Procurado em: {cred_path}")
        print(f"\n  Solução:")
        print(f"    1. Vá a: https://console.cloud.google.com/")
        print(f"    2. Crie um projeto")
        print(f"    3. Ative a API do Google Drive")
        print(f"    4. Baixe as credenciais (JSON)")
        print(f"    5. Salve como: {cred_path}")
        return False
    
    if token_path.exists():
        print(f"✓ Token de autenticação encontrado")
        print(f"  {token_path}")
    else:
        print(f"⚠ Token não encontrado (será criado na primeira execução)")
        print(f"  {token_path}")
    
    return True


def check_directories():
    """Verificar diretórios necessários"""
    print("\n" + "=" * 70)
    print("5. VERIFICAÇÃO: Diretórios")
    print("=" * 70)
    
    dirs = {
        './temp': 'Arquivos temporários',
        './logs': 'Arquivos de log',
        './config': 'Configuração',
        './src': 'Código-fonte',
    }
    
    all_ok = True
    
    for dir_path, description in dirs.items():
        path = Path(dir_path)
        if path.exists():
            print(f"✓ {dir_path:<20} ({description})")
        else:
            print(f"✗ {dir_path:<20} ({description}) - NÃO EXISTE")
            all_ok = False
    
    return all_ok


def print_summary(results):
    """Imprimir resumo dos testes"""
    print("\n" + "=" * 70)
    print("RESUMO")
    print("=" * 70)
    
    all_ok = all(results.values())
    
    print("\nVerificações:")
    for check, result in results.items():
        status = "✓" if result else "✗"
        print(f"  {status} {check}")
    
    print()
    
    if all_ok:
        print("✓ TUDO OK! Você pode executar a aplicação.")
        print("\n  $ python3 main.py --list")
    else:
        print("✗ Existem problemas. Veja as soluções acima.")
        print("\nProblema crítico: dcm2niix não está instalado")
        print("  → Instale: brew install dcm2niix (macOS)")
    
    print()


def main():
    """Função principal"""
    print("\n" + "╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "DIAGNÓSTICO DE DEPENDÊNCIAS" + " " * 27 + "║")
    print("╚" + "=" * 68 + "╝")
    
    results = {
        'Python': check_python_version(),
        'dcm2niix': check_dcm2niix(),
        'Pacotes Python': check_python_packages(),
        'Credenciais': check_credentials(),
        'Diretórios': check_directories(),
    }
    
    print_summary(results)


if __name__ == "__main__":
    main()
