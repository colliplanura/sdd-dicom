"""
Configuração de testes
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configurar logging para testes
import os
os.environ['LOG_LEVEL'] = 'DEBUG'

# Suprimir warnings ruidosos durante os testes
import warnings

# Ignorar deprecações e avisos genéricos de bibliotecas externas durante o test run
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Ignorar mensagens específicas conhecidas (asyncio/pytest-asyncio, pkg_resources)
warnings.filterwarnings("ignore", ".*asyncio.iscoroutinefunction.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", ".*asyncio.get_event_loop_policy.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", ".*pkg_resources.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", ".*declare_namespace.*", category=DeprecationWarning)
