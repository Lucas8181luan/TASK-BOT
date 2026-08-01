"""
Bot de comparação entre LISTA DE CERTIFICADOS e LISTA DE LEADS.

Lógica:
  - Lê nomes da aba "LISTA DE CERTIFICADOS" (coluna A a partir de A2)
    e também CURSO (coluna B) e LOCAL (coluna C).
  - Lê nomes da aba "LISTA DE LEADS" (coluna A a partir de A2).
  - Gera (ou recria) a aba "RESULTADO" com os nomes que estão em
    LISTA DE CERTIFICADOS mas NÃO estão em LISTA DE LEADS, incluindo
    CURSO e LOCAL de cada um.
  - A comparação ignora diferenças de maiúsculas/minúsculas e espaços.
  - A aba RESULTADO é formatada em zebra azul claro/escuro com totais.
"""

import os
import gspread
import time
from google.oauth2.service_account import Credentials
from datetime import datetime

SPREADSHEET_ID    = "1M-tcGtQuFfVAqnko9bN_yXQfzZa4dUg2OdxQ6ldpNug"
ABA_CERTIFICADOS  = "LISTA DE CERTIFICADOS"
ABA_LEADS         = "LISTA DE LEADS"
ABA_RESULTADO     = "RESULTADO"

# Cores
COR_AZUL_ESCURO = {"red": 0.565, "green": 0.753, "blue": 0.902}
COR_AZUL_CLARO  = {"red": 0.780, "green": 0.902, "blue": 0.961}
COR_HEADER      = {"red": 0.067, "green": 0.333, "blue": 0.600}   # azul marinho
COR_TOTAL       = {"red": 0.122, "green": 0.467, "blue": 0.706}   # azul médio


# =============================================================================
# Autenticação
# =============================================================================

def _set_timeout(client, seconds: int):
    for obj in (client, getattr(client, 'http_client', None)):
        if obj is None:
            continue
        session = getattr(obj, 'session', None)
        if session is not None and hasattr(session, 'timeout'):
            session.timeout = seconds
            return


def get_gsheet_client():
    creds_path = os.environ.get(
        "GOOGLE_SHEETS_CREDS",
        r"C:/Users/lucas/OneDrive/Documentos/SITE-RIOELAS-TESTE/identificador-488615-c1ab55e9b31b.json"
    )
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive',
    ]
    creds  = Credentials.from_service_account_file(creds_path, scopes=scopes)
    client = gspread.authorize(creds)
    _set_timeout(client, 120)
    return client


def retry_api_call(func, max_retries=8, base_delay=3):
    import requests.exceptions
    TRANSIENT = (
        requests.exceptions.ReadTimeout,
        requests.exceptions.ConnectTimeout,
        requests.exceptions.ConnectionError,
    )
    for attempt in range(max_retries):
        try:
            return func()
        except gspread.exceptions.APIError as e:
            if '429' in str(e):
                wait = base_delay * (2 ** attempt)
                print(f"   ⚠️  Rate limit — aguardando {wait}s... ({attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                raise
        except TRANSIENT as e:
            wait = base_delay * (2 ** attempt)
            print(f"   ⚠️  Erro de rede ({type(e).__name__}) — aguardando {wait}s... ({attempt+1}/{max_retries})")
            time.sleep(wait)
    return func()


# =============================================================================
# Leitura das abas
# =============================================================================

def ler_certificados(spreadsheet) -> list[dict]:
    """
    Lê LISTA DE CERTIFICADOS.
    Retorna lista de dicts: {nome, curso, local, nome_norm}
    """
    ws = spreadsheet.worksheet(ABA_CERTIFICADOS)
    values = retry_api_call(lambda: ws.get_all_values())

    registros = []
    for row in values[1:]:   # pula cabeçalho
        nome  = row[0].strip() if len(row) > 0 else ''
        curso = row[1].strip() if len(row) > 1 else ''
        local = row[2].strip() if len(row) > 2 else ''
        if nome:
            registros.append({
                'nome':      nome,
                'curso':     curso,
                'local':     local,
                'nome_norm': nome.strip().upper(),
            })
    return registros


def ler_leads(spreadsheet) -> set[str]:
    """
    Lê LISTA DE LEADS coluna A.
    Retorna conjunto de nomes normalizados (upper + strip).
    """
    ws = spreadsheet.worksheet(ABA_LEADS)
    values = retry_api_call(lambda: ws.get_all_values())

    nomes = set()
    for row in values[1:]:
        nome = row[0].strip() if len(row) > 0 else ''
        if nome:
            nomes.add(nome.strip().upper())
    return nomes


# =============================================================================
# Gerar aba RESULTADO
# =============================================================================

def gerar_resultado(spreadsheet, ausentes: list[dict],
                    total_cert: int, total_leads: int):
    """
    Cria (ou recria) a aba RESULTADO com:
      - Título com data/hora da geração
      - Cabeçalho: #, NOME, CURSO, LOCAL
      - Linhas zebradas azul claro/escuro
      - Bloco de totais no final
    """
    # Apaga aba existente se houver
    for ws in spreadsheet.worksheets():
        if ws.title.strip().upper() == ABA_RESULTADO.upper():
            spreadsheet.del_worksheet(ws)
            time.sleep(1)
            break

    sheet = retry_api_call(
        lambda: spreadsheet.add_worksheet(title=ABA_RESULTADO, rows=2000, cols=5)
    )

    agora = datetime.now().strftime('%d/%m/%Y %H:%M')

    # ── Dados ────────────────────────────────────────────────────────────────
    headers = ['#', 'NOME', 'CURSO', 'LOCAL', 'STATUS']

    rows_data = []
    for i, r in enumerate(ausentes, start=1):
        rows_data.append([
            i,
            r['nome'],
            r['curso'],
            r['local'],
            'Certificado emitido — não está nos Leads',
        ])

    # Escreve cabeçalho
    retry_api_call(lambda: sheet.update('A1:E1', [headers]))

    # Escreve dados
    if rows_data:
        retry_api_call(lambda: sheet.update(f"A2:E{len(rows_data)+1}", rows_data))

    # Linha em branco + bloco de totais
    total_row  = len(rows_data) + 3   # +2 (cabeçalho + 1 blank)
    totais_data = [
        ['TOTAL CERTIFICADOS',  total_cert,                  '', '', ''],
        ['TOTAL LEADS',         total_leads,                 '', '', ''],
        ['AUSENTES DOS LEADS',  len(ausentes),               '', '', ''],
        ['COBERTURA (%)',
         f'{(total_leads/total_cert*100):.1f}%' if total_cert else '0%',
         '', '', ''],
        ['GERADO EM',           agora,                       '', '', ''],
    ]
    retry_api_call(lambda: sheet.update(
        f"A{total_row}:E{total_row + len(totais_data) - 1}", totais_data
    ))

    # ── Formatação ────────────────────────────────────────────────────────────
    time.sleep(2)
    n_dados = len(rows_data)

    fmt = [
        # Cabeçalho: azul marinho, texto branco, negrito
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id,
                           "startRowIndex": 0, "endRowIndex": 1,
                           "startColumnIndex": 0, "endColumnIndex": 5},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": COR_HEADER,
                        "textFormat": {
                            "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                            "bold": True, "fontSize": 11, "fontFamily": "Arial",
                        },
                        "horizontalAlignment": "CENTER",
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
            }
        },
        # Fonte base nas linhas de dados
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id,
                           "startRowIndex": 1, "endRowIndex": n_dados + 1,
                           "startColumnIndex": 0, "endColumnIndex": 5},
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {"fontSize": 10, "fontFamily": "Arial"},
                        "wrapStrategy": "WRAP",
                    }
                },
                "fields": "userEnteredFormat(textFormat,wrapStrategy)",
            }
        },
        # Coluna # centralizada
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id,
                           "startRowIndex": 1, "endRowIndex": n_dados + 1,
                           "startColumnIndex": 0, "endColumnIndex": 1},
                "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
                "fields": "userEnteredFormat(horizontalAlignment)",
            }
        },
        # Bloco de totais: azul médio, texto branco, negrito
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id,
                           "startRowIndex": total_row - 1,
                           "endRowIndex": total_row - 1 + len(totais_data),
                           "startColumnIndex": 0, "endColumnIndex": 5},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": COR_TOTAL,
                        "textFormat": {
                            "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                            "bold": True, "fontSize": 10, "fontFamily": "Arial",
                        },
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat)",
            }
        },
        # Coluna B dos totais centralizada
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id,
                           "startRowIndex": total_row - 1,
                           "endRowIndex": total_row - 1 + len(totais_data),
                           "startColumnIndex": 1, "endColumnIndex": 2},
                "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
                "fields": "userEnteredFormat(horizontalAlignment)",
            }
        },
        # Congelar cabeçalho
        {
            "updateSheetProperties": {
                "properties": {"sheetId": sheet.id,
                                "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount",
            }
        },
        # Larguras de coluna
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 50},  "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2}, "properties": {"pixelSize": 280}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 2, "endIndex": 3}, "properties": {"pixelSize": 260}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 3, "endIndex": 4}, "properties": {"pixelSize": 300}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 4, "endIndex": 5}, "properties": {"pixelSize": 280}, "fields": "pixelSize"}},
    ]

    # Zebra: linhas alternadas azul escuro / azul claro
    for i in range(n_dados):
        bg = COR_AZUL_ESCURO if i % 2 == 0 else COR_AZUL_CLARO
        fmt.append({
            "repeatCell": {
                "range": {"sheetId": sheet.id,
                           "startRowIndex": i + 1, "endRowIndex": i + 2,
                           "startColumnIndex": 0, "endColumnIndex": 5},
                "cell": {"userEnteredFormat": {"backgroundColor": bg}},
                "fields": "userEnteredFormat(backgroundColor)",
            }
        })

    retry_api_call(lambda: spreadsheet.batch_update({"requests": fmt}))

    # Negrito coluna NOME
    retry_api_call(lambda: spreadsheet.batch_update({"requests": [{
        "repeatCell": {
            "range": {"sheetId": sheet.id,
                       "startRowIndex": 1, "endRowIndex": n_dados + 1,
                       "startColumnIndex": 1, "endColumnIndex": 2},
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
            "fields": "userEnteredFormat(textFormat)",
        }
    }]}))

    print(f"   ✓ Aba '{ABA_RESULTADO}' criada com {n_dados} ausente(s)")
    return sheet


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 60)
    print("COMPARADOR: CERTIFICADOS × LEADS")
    print("=" * 60)

    print("\n1. Conectando ao Google Sheets...")
    client      = get_gsheet_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    print(f"   ✓ Planilha: {spreadsheet.title}")

    print(f"\n2. Lendo '{ABA_CERTIFICADOS}'...")
    certificados = ler_certificados(spreadsheet)
    print(f"   ✓ {len(certificados)} nome(s) encontrado(s)")

    print(f"\n3. Lendo '{ABA_LEADS}'...")
    leads = ler_leads(spreadsheet)
    print(f"   ✓ {len(leads)} nome(s) encontrado(s)")

    print("\n4. Comparando...")
    ausentes = [r for r in certificados if r['nome_norm'] not in leads]
    presentes = len(certificados) - len(ausentes)
    print(f"   ✓ Presentes nos Leads:     {presentes}")
    print(f"   ✓ Ausentes dos Leads:      {len(ausentes)}")
    cobertura = (len(leads) / len(certificados) * 100) if certificados else 0
    print(f"   ✓ Cobertura de Leads:      {cobertura:.1f}%")

    print(f"\n5. Gerando aba '{ABA_RESULTADO}'...")
    gerar_resultado(spreadsheet, ausentes,
                    total_cert=len(certificados),
                    total_leads=len(leads))

    print("\n" + "=" * 60)
    print("✅ CONCLUÍDO!")
    print("=" * 60)
    print(f"\n  Certificados:    {len(certificados)}")
    print(f"  Leads:           {len(leads)}")
    print(f"  Ausentes:        {len(ausentes)}")
    print(f"  Cobertura:       {cobertura:.1f}%")


if __name__ == "__main__":
    main()