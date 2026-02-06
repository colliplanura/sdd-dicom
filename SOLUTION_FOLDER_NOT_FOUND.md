# 🔧 Solução: Pasta Não Encontrada no Google Drive

## ❌ Erro
```
Erro ao listar arquivos: Pasta não encontrada: Medicina/Doutorado IDOR/Exames/DICOM
```

## ✅ Correção Implementada

Ajustei o código para **navegar corretamente por caminhos aninhados** no Google Drive:

### O Problema
- O método anterior buscava por nome **exato** de pasta
- Um caminho como `"Medicina/Doutorado IDOR/Exames/DICOM"` é **múltiplas pastas**, não uma única

### A Solução
Novo método: `_find_folder_by_path()` que:
1. Divide o caminho por `/`
2. Navega pasta a pasta
3. Encontra o ID correto da pasta final

## 🚀 Como Usar

### Opção 1: Usar o Novo Código (Recomendado)
O código agora suporta caminhos completos automaticamente:

```python
from src.google_drive import GoogleDriveClient

client = GoogleDriveClient()

# Funciona agora! ✓
files = client.list_files(
    folder_name='Medicina/Doutorado IDOR/Exames/DICOM',
    max_results=20
)
```

### Opção 2: Usar ID Direto (Se o Caminho Continuar Falhando)

1. **Encontre o ID da pasta:**
   - Abra a pasta no Google Drive
   - Copie o ID da URL: `https://drive.google.com/drive/folders/XXXXX`

2. **Use o ID:**
```python
client.list_files(
    folder_id='XXXXX_ID_DA_PASTA_XXXXX',
    max_results=20
)
```

## 🔍 Diagnosticar o Problema

Se ainda assim não funcionar, execute o script de diagnóstico:

```bash
python3 diagnose_drive.py
```

**Isto mostra:**
- ✓ Pastas que existem na raiz
- ✓ Se cada parte do caminho existe
- ✓ Sugestões de solução

## 📋 Possíveis Causas

| Causa | Solução |
|-------|---------|
| Caminho com espaços errados | Use caracteres exatos, copie do Drive |
| Pasta não existe | Verifique se a pasta está no Drive |
| Sem permissão | Verifique permissões da credencial |
| Nome com caracteres especiais | Use `diagnose_drive.py` para verificar |
| Pasta foi movida/deletada | Verifique estrutura atual no Drive |

## 🛠 Mudanças Implementadas

### Arquivo: `src/google_drive/client.py`

**Novo método:** `_find_folder_by_path()`
```python
# Navega por caminho aninhado
folder_id = client._find_folder_by_path(
    'Medicina/Doutorado IDOR/Exames/DICOM'
)
```

**Melhorado:** `_find_folder_by_name()`
```python
# Agora detecta se é caminho e chama _find_folder_by_path()
folder_id = client._find_folder_by_name(
    'Medicina/Doutorado IDOR/Exames/DICOM'
)
```

**Melhorado:** Mensagens de erro mais informativas

## 📊 Exemplos

### Exemplo 1: Caminho Simples
```python
# Funciona se "DICOM" é uma pasta na raiz
files = client.list_files(
    folder_name='DICOM'
)
```

### Exemplo 2: Caminho Aninhado (NOVO)
```python
# Funciona mesmo com múltiplos níveis
files = client.list_files(
    folder_name='Medicina/Doutorado IDOR/Exames/DICOM'
)
```

### Exemplo 3: Usar ID Direto
```python
# Sempre funciona se o ID está correto
files = client.list_files(
    folder_id='1a2b3c4d5e6f7g8h9i0j'
)
```

## ✨ Recursos Novos

✅ Navegação automática de caminhos aninhados
✅ Logs detalhados para debugar
✅ Melhor tratamento de erros
✅ Script de diagnóstico (`diagnose_drive.py`)

## 🎯 Próximas Etapas

1. **Teste o novo código:**
   ```bash
   python3 main.py --list --max-files 5
   ```

2. **Se não funcionar, execute o diagnóstico:**
   ```bash
   python3 diagnose_drive.py
   ```

3. **Se precisar usar ID, encontre assim:**
   - Abra a pasta no Google Drive
   - Copie o ID da URL
   - Use `folder_id=` em vez de `folder_name=`

## 💡 Dicas

- O novo código é **100% compatível** com o antigo
- Funciona com nomes que contêm espaços
- Suporta caracteres especiais (acentos, etc)
- Log detalhado ajuda a debugar

---

**Está funcionando?** → Ótimo! Continue normalmente.

**Ainda não?** → Execute `python3 diagnose_drive.py` e verifique a saída.
