#!/usr/bin/env python
"""
Exemplo Visual: Como a Busca de Pasta Funciona
"""

FLUXO_BUSCA = """
╔═════════════════════════════════════════════════════════════════╗
║               FLUXO DE BUSCA DE PASTA NO GOOGLE DRIVE          ║
╚═════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────┐
│ ENTRADA: 'Medicina/Doutorado IDOR/Exames/DICOM'               │
└─────────────────────────────────────────────────────────────────┘

                            ↓

┌─────────────────────────────────────────────────────────────────┐
│ DETECÇÃO: Contém '/'?                                          │
│ Sim → Usar _find_folder_by_path()                              │
└─────────────────────────────────────────────────────────────────┘

                            ↓

┌─────────────────────────────────────────────────────────────────┐
│ SPLIT: Dividir por '/'                                          │
│ ['Medicina', 'Doutorado IDOR', 'Exames', 'DICOM']              │
└─────────────────────────────────────────────────────────────────┘

                            ↓

┌─────────────────────────────────────────────────────────────────┐
│ PASSO 1: Buscar 'Medicina' na RAIZ                             │
│                                                                 │
│  Google Drive API:                                              │
│  query = "name='Medicina' and mimeType=folder"                 │
│                                                                 │
│  ✓ Encontrada! ID = abc123                                     │
└─────────────────────────────────────────────────────────────────┘

                            ↓

┌─────────────────────────────────────────────────────────────────┐
│ PASSO 2: Buscar 'Doutorado IDOR' DENTRO de 'Medicina'         │
│                                                                 │
│  Google Drive API:                                              │
│  query = "name='Doutorado IDOR' and 'abc123' in parents"       │
│                                                                 │
│  ✓ Encontrada! ID = def456                                     │
└─────────────────────────────────────────────────────────────────┘

                            ↓

┌─────────────────────────────────────────────────────────────────┐
│ PASSO 3: Buscar 'Exames' DENTRO de 'Doutorado IDOR'           │
│                                                                 │
│  Google Drive API:                                              │
│  query = "name='Exames' and 'def456' in parents"               │
│                                                                 │
│  ✓ Encontrada! ID = ghi789                                     │
└─────────────────────────────────────────────────────────────────┘

                            ↓

┌─────────────────────────────────────────────────────────────────┐
│ PASSO 4: Buscar 'DICOM' DENTRO de 'Exames'                    │
│                                                                 │
│  Google Drive API:                                              │
│  query = "name='DICOM' and 'ghi789' in parents"                │
│                                                                 │
│  ✓ Encontrada! ID = jkl000                                     │
└─────────────────────────────────────────────────────────────────┘

                            ↓

┌─────────────────────────────────────────────────────────────────┐
│ RESULTADO FINAL:                                                │
│ ID da pasta 'DICOM' = jkl000                                    │
│                                                                 │
│ ✓ Sucesso! Agora pode buscar arquivos nesta pasta              │
└─────────────────────────────────────────────────────────────────┘

════════════════════════════════════════════════════════════════════
"""

COMPARACAO_ANTES_DEPOIS = """
┌─────────────────────────────────────────────────────────────────┐
│                   ANTES vs. DEPOIS                              │
└─────────────────────────────────────────────────────────────────┘

ANTES: Busca por nome exato
═══════════════════════════

❌ client.list_files(
       folder_name='Medicina/Doutorado IDOR/Exames/DICOM'
   )
   
   Resultado: Pasta não encontrada!
   Motivo: Procurava por um nome que contém '/'

✅ client.list_files(
       folder_name='DICOM'
   )
   
   Resultado: Funciona, mas encontra outras pastas chamadas 'DICOM'


DEPOIS: Busca com navegação de caminho
═════════════════════════════════════════

✅ client.list_files(
       folder_name='Medicina/Doutorado IDOR/Exames/DICOM'
   )
   
   Resultado: FUNCIONA! ✓
   Navega por cada pasta automaticamente

✅ client.list_files(
       folder_name='DICOM'
   )
   
   Resultado: Continua funcionando
   Busca simples (sem '/' no nome)

✅ client.list_files(
       folder_id='jkl000'
   )
   
   Resultado: SEMPRE funciona
   Busca direta por ID (mais rápido)
"""

CASOS_USO = """
┌─────────────────────────────────────────────────────────────────┐
│                  CASOS DE USO                                   │
└─────────────────────────────────────────────────────────────────┘

CASO 1: Estrutura simples (uma pasta)
══════════════════════════════════════

Estrutura:
  Google Drive
  └─ DICOM

Código:
  files = client.list_files(
      folder_name='DICOM'
  )
  
Status: ✓ Funciona (antes e depois)


CASO 2: Estrutura aninhada (múltiplas pastas)
═════════════════════════════════════════════

Estrutura:
  Google Drive
  └─ Medicina
     └─ Doutorado IDOR
        └─ Exames
           └─ DICOM

Código (ANTES):
  ❌ files = client.list_files(
         folder_name='Medicina/Doutorado IDOR/Exames/DICOM'
     )
     Resultado: Pasta não encontrada

Código (DEPOIS):
  ✅ files = client.list_files(
         folder_name='Medicina/Doutorado IDOR/Exames/DICOM'
     )
     Resultado: FUNCIONA!


CASO 3: Estrutura profunda com múltiplas pastas
════════════════════════════════════════════════

Estrutura:
  Google Drive
  ├─ Paciente_001
  │  └─ 2024-01
  │     └─ Scans
  │        └─ T1
  │           └─ DICOM
  └─ Paciente_002
     └─ Scans
        └─ DICOM

Código:
  ✅ files = client.list_files(
         folder_name='Paciente_001/2024-01/Scans/T1/DICOM'
     )
     
Status: ✓ Funciona com a nova implementação


CASO 4: Usar ID direto (mais rápido)
═════════════════════════════════════

Se o ID é conhecido:

  ✅ files = client.list_files(
         folder_id='abc123def456'
     )

Status: ✓ SEMPRE funciona (antes e depois)
        ✓ Mais rápido que busca por nome
"""

SOLUCAO_ERROS = """
┌─────────────────────────────────────────────────────────────────┐
│              SOLUÇÃO DE PROBLEMAS                               │
└─────────────────────────────────────────────────────────────────┘

Erro: "Pasta não encontrada: Medicina/Doutorado IDOR/Exames/DICOM"
═════════════════════════════════════════════════════════════════

Passo 1: Verifique o caminho
   ❌ Digitou certo? Espaços? Acentos? Maiúsculas?
   ✅ Copie o nome exato de cada pasta no Google Drive

Passo 2: Verifique a estrutura
   ❌ Todas as pastas existem?
   ✅ Navegue no Google Drive e confirme

Passo 3: Teste com nome de pasta única
   ❌ files = client.list_files(folder_name='Medicina/...')
   ✅ files = client.list_files(folder_name='DICOM')

Passo 4: Use ID direto (solução rápida)
   ✅ files = client.list_files(folder_id='XXXXX')
   
   Para encontrar o ID:
   1. Abra a pasta no Google Drive
   2. Copie na URL: https://drive.google.com/drive/folders/XXXXX

Passo 5: Execute diagnóstico
   $ python3 diagnose_drive.py


Debug com Logs
══════════════

Ative debug logging para ver o que está acontecendo:

  from src.core import Config
  Config.LOG_LEVEL = 'DEBUG'
  
  # Agora vê logs detalhados


Permissões
══════════

Se a pasta não é encontrada mesmo existindo:

  ✓ Verifique se a credencial tem acesso
  ✓ Verifique se a pasta foi compartilhada
  ✓ Tente compartilhar com o email da Service Account
"""

if __name__ == '__main__':
    print(FLUXO_BUSCA)
    print("\n" + COMPARACAO_ANTES_DEPOIS)
    print("\n" + CASOS_USO)
    print("\n" + SOLUCAO_ERROS)
