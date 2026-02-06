# 🔧 Guia de Instalação de Dependências

## ❌ Problemas Encontrados

1. **dcm2niix NÃO INSTALADO** (crítico)
2. **google-api-python-client ausente** (crítico)

## ✅ Solução

### 1. Instalar dcm2niix

#### macOS (Recomendado)
```bash
brew install dcm2niix
```

**Verificar instalação:**
```bash
dcm2niix -v
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install dcm2niix
```

#### Linux (CentOS/RHEL)
```bash
sudo yum install dcm2niix
```

#### Conda (Qualquer SO)
```bash
conda install -c conda-forge dcm2niix
```

#### Compilar do Código-Fonte
```bash
git clone https://github.com/rordenlab/dcm2niix.git
cd dcm2niix/console
make
sudo cp dcm2niix /usr/local/bin/
```

### 2. Instalar Pacotes Python Ausentes

```bash
pip install google-api-python-client
```

### 3. Instalar Todos os Requisitos (Recomendado)

```bash
pip install -r requirements.txt
```

## 🧪 Testar Instalação

```bash
# Teste 1: Verificar dcm2niix
dcm2niix -v

# Teste 2: Verificar Python packages
python3 -c "import google.auth; import loguru; print('✓ Pacotes OK')"

# Teste 3: Diagnóstico completo
python3 check_dependencies.py
```

## 🚀 Depois de Instalar

Reinicie a aplicação:

```bash
python3 main.py --list --max-files 5
```

## 📋 Checklist de Instalação

- [ ] dcm2niix instalado (`dcm2niix -v` funciona)
- [ ] google-api-python-client instalado
- [ ] Arquivo `config/credentials.json` existe
- [ ] Arquivo `config/token.json` existe
- [ ] Diretórios `temp/` e `logs/` existem
- [ ] `python3 check_dependencies.py` mostra tudo ✓

## ❓ Solução de Problemas

### dcm2niix não funciona após instalação
```bash
# Verifique o PATH
which dcm2niix

# Ou tente o caminho completo
/usr/local/bin/dcm2niix -v

# Se usou Homebrew em M1/M2
which dcm2niix  # Deve estar em /opt/homebrew/bin/dcm2niix
```

### Import error: google.auth
```bash
pip install --upgrade google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Erro: "command not found: dcm2niix"
O dcm2niix não está no PATH. Tente:
```bash
# Verificar instalação
brew list dcm2niix  # macOS

# Reinstalar
brew uninstall dcm2niix && brew install dcm2niix  # macOS
```

### macOS M1/M2 (Apple Silicon)
```bash
# Certifique-se de usar a versão ARM64
brew install dcm2niix

# Verifique
file $(which dcm2niix)
# Deve mostrar: Mach-O 64-bit executable arm64
```

## 📦 requirements.txt Atualizado

```
google-auth-oauthlib>=1.0.0
google-auth-httplib2>=0.1.1
google-api-python-client>=2.80.0
loguru>=0.7.0
pydicom>=2.3.0
```

## 🎯 Próximos Passos

1. Execute o diagnóstico novamente:
```bash
python3 check_dependencies.py
```

2. Se tudo estiver OK, teste a aplicação:
```bash
python3 main.py --list --max-files 5
```

3. Se ainda tiver problemas, execute o diagnóstico do Google Drive:
```bash
python3 diagnose_drive.py
```

---

**Dúvidas?** Verifique os logs:
```bash
cat logs/*.log
```
