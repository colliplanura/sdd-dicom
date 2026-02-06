# 🚀 Quick Start - Primeiros Passos

## 1. Instalação (5 minutos)

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/sdd-dicom.git
cd sdd-dicom

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # macOS/Linux
# ou
venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt
```

## 2. Configuração Google Drive (10 minutos)

### Passo 1: Criar Credenciais

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto
3. Ative a Google Drive API
4. Crie um "OAuth 2.0 Client ID" (Desktop application)
5. Faça download e salve como `credentials.json`

### Passo 2: Colocar credenciais no projeto

```bash
cp ~/Downloads/credentials.json ./config/credentials.json
```

## 3. Primeiro Teste (2 minutos)

```python
from src.google_drive.client import GoogleDriveClient

# Conectar ao Google Drive
client = GoogleDriveClient(credentials_path='config/credentials.json')

# Listar primeiros arquivos
files = client.list_files(max_results=10)
for f in files:
    print(f"- {f['name']} ({f['size']} bytes)")
```

## 4. Estrutura do Projeto

```
sdd-dicom/
├── src/                    # 💻 Código-fonte
│   ├── core/              # Módulos core
│   ├── google_drive/      # Cliente Google Drive
│   ├── dicom/             # Conversor DICOM
│   ├── pipeline/          # Orquestração
│   └── utils/             # Utilidades
│
├── tests/                 # ✅ Testes
├── config/                # ⚙️ Configuração (credentials.json)
├── docs/                  # 📚 Documentação
└── requirements.txt       # 📦 Dependências
```

## 5. Próximas Etapas

- [ ] Ler [../02-architecture/SYSTEM_DESIGN.md](../02-architecture/SYSTEM_DESIGN.md)
- [ ] Entender [../03-technical-specs/PRD.yaml](../03-technical-specs/PRD.yaml)
- [ ] Explorar [../05-examples/CODE_REFERENCES.md](../05-examples/CODE_REFERENCES.md)
- [ ] Executar testes: `python -m pytest tests/`

---

**Próximo:** [../02-architecture/SYSTEM_DESIGN.md](../02-architecture/SYSTEM_DESIGN.md)
