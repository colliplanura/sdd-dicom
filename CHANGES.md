# Ajustes para Arquivos DICOM em Subpastas Sem Extensão

## Resumo das Alterações

A aplicação foi ajustada para lidar com dois cenários comuns:

1. **Arquivos DICOM em subpastas**: Os arquivos DICOM podem estar organizados em subpastas dentro de "Medicina/Doutorado IDOR/Exames/DICOM"
2. **Sem extensão .dcm**: Os arquivos DICOM podem não possuir a extensão `.dcm`

## Mudanças Implementadas

### 1. Busca Recursiva no Google Drive (`src/google_drive/client.py`)

#### Antes:
- `list_files()` buscava apenas na pasta especificada (nível único)

#### Depois:
- Novo método: `_list_files_recursive()` busca em todas as subpastas
- Novo método: `_list_files_in_folder()` busca apenas na pasta (modo não-recursivo)
- Parâmetro `recursive=True` (padrão) habilita busca em subpastas
- Parâmetro `filter_dicom=True` filtra apenas arquivos (não pastas)

**Exemplo de uso:**
```python
# Busca recursiva em subpastas (padrão)
files = client.list_files(
    folder_name='Medicina/Doutorado IDOR/Exames/DICOM',
    recursive=True
)

# Apenas na pasta (sem subpastas)
files = client.list_files(
    folder_name='Medicina/Doutorado IDOR/Exames/DICOM',
    recursive=False
)
```

### 2. Detecção de DICOM sem Extensão (`src/dicom/file_detector.py`)

#### Novo arquivo: `DICOMFileDetector`

Detecta arquivos DICOM pelo **magic number** (bytes específicos), não depende de extensão:

- **Magic number DICOM**: `DICM` na posição 128-132 do arquivo
- **Tamanho mínimo**: 132 bytes (128 + 4)

**Métodos disponíveis:**
```python
from src.dicom import DICOMFileDetector

# Verificar um arquivo específico
is_dicom = DICOMFileDetector.is_dicom_file(Path('arquivo_sem_ext'))

# Encontrar todos os DICOM em diretório
files = DICOMFileDetector.find_dicom_files(Path('./dados'))

# Com limite de arquivos
files = DICOMFileDetector.find_dicom_files_in_folder(
    Path('./dados'),
    max_files=100
)
```

### 3. Validador Melhorado (`src/dicom/validator.py`)

#### Antes:
- Verificava magic number manualmente

#### Depois:
- Usa `DICOMFileDetector` para validação robusta
- Melhor tratamento de erros
- Funciona com ou sem extensão `.dcm`

### 4. Pipeline Atualizado (`src/pipeline/batch_pipeline.py`)

#### Antes:
```python
output_path = self.config.TEMP_DIR / f"{task.file_id}.dcm"
```

#### Depois:
```python
# Usa nome do arquivo original (sem forçar .dcm)
output_path = self.config.TEMP_DIR / task.file_name
```

## Fluxo de Funcionamento

```
1. DESCOBERTA (Google Drive)
   ├─ Listar pastas/subpastas recursivamente
   ├─ Filtrar apenas arquivos (não pastas)
   └─ Retornar lista com names originais

2. DOWNLOAD
   ├─ Usar nome do arquivo original
   ├─ Arquivo salvo em: ./temp/{arquivo_original}
   └─ Sem forçar extensão .dcm

3. VALIDAÇÃO
   ├─ Verificar magic number DICOM
   ├─ Funciona com qualquer nome (com/sem extensão)
   └─ Ignorar arquivos não-DICOM

4. CONVERSÃO
   ├─ dcm2niix processa arquivo independente de extensão
   └─ Gera saída em ./temp/{arquivo}_nifti/

5. UPLOAD
   └─ Enviar NIfTI para Google Drive
```

## Exemplos de Estrutura de Pastas Suportadas

### Estrutura 1: Subpastas por Paciente
```
Medicina/Doutorado IDOR/Exames/DICOM/
├─ Paciente_001/
│  ├─ exam_001
│  ├─ exam_002
│  └─ study_20240101
├─ Paciente_002/
│  ├─ series_1
│  └─ series_2
└─ Paciente_003/
   └─ scan_data
```

### Estrutura 2: Subpastas por Data
```
Medicina/Doutorado IDOR/Exames/DICOM/
├─ 2024-01/
│  ├─ arquivo1
│  ├─ arquivo2.dcm
│  └─ imagem_scan
├─ 2024-02/
│  └─ dados_exam
└─ 2024-03/
   └─ serie_dicom
```

### Estrutura 3: Mista (Paciente + Data)
```
Medicina/Doutorado IDOR/Exames/DICOM/
├─ Paciente_A/
│  ├─ 2024-01/
│  │  ├─ scan1
│  │  └─ scan2.dcm
│  └─ 2024-02/
│     └─ followup
└─ Paciente_B/
   └─ scans/
      └─ baseline
```

## Teste

Para validar as mudanças:

```bash
python3 test_detection.py
```

**Saída esperada:**
```
✓ Detecção de DICOM com extensão: True
✓ Detecção de DICOM sem extensão: True
✓ Detecção recursiva em subpastas: 3 arquivos encontrados
✓ Rejeição de arquivo não-DICOM: False
```

## Compatibilidade

- ✅ Arquivos DICOM com extensão `.dcm` (backwards-compatible)
- ✅ Arquivos DICOM sem extensão
- ✅ Arquivos DICOM em subpastas
- ✅ Mistura de nomes com/sem extensão na mesma pasta
- ✅ Google Drive com estrutura de pastas profunda

## Configuração (opcional)

No `main.py`, você pode controlar o comportamento:

```python
# Busca recursiva (padrão)
files = client.list_files(
    folder_name=Config.GOOGLE_DRIVE_FOLDER,
    recursive=True,
    max_results=100
)

# Apenas pasta raiz (não-recursivo)
files = client.list_files(
    folder_name=Config.GOOGLE_DRIVE_FOLDER,
    recursive=False,
    max_results=100
)
```

## Performance

- Busca recursiva respeita `max_results` para evitar timeout
- Rate limiting mantido (5 req/s padrão)
- Processamento em paralelo continua funcionando normalmente
