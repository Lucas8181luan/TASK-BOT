"""
Script para filtrar dados de inscrições por local de curso
e criar abas separadas na mesma planilha do Google Sheets.

Dashboard inclui: LOCAL, CURSOS, DATA DE INÍCIO, TOTAL, DIA ANTERIOR,
ÚLTIMA SEMANA e DATA CONSULTA.

DATA DE INÍCIO é lida diretamente da coluna J (índice 9) de cada registro.
  - Se o local tiver um único curso → exibe só a data.
  - Se tiver múltiplos cursos com datas diferentes → exibe "CURSO: DATA | ..."
"""

import os
import gspread
import time
import requests.exceptions
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

SPREADSHEET_ID    = "1Bgs1W28A60XZvdzpxS22N7i5F07NgfWFIGPPpTaRlAk"
ORIGIN_SHEET_NAME = "DADOS"

COL_DATA        = 0
COL_CURSO       = 4   # coluna E
COL_LOCAL       = 8   # coluna I
COL_DATA_INICIO = 9   # coluna J  ← DATA DE INÍCIO

HEADERS = [
    'DATA', 'NOME', 'CPF', 'GÊNERO', 'CURSO', 'WHATSAPP',
    'CEP', 'EMAIL', 'LOCAL DO CURSO', 'DATA DE INÍCIO', 'HORÁRIO'
]


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
    import tempfile

    creds_path    = os.environ.get(
        "GOOGLE_SHEETS_CREDS",
        r"C:/Users/lucas/OneDrive/Documentos/SITE-RIOELAS-TESTE/identificador-488615-c1ab55e9b31b.json"
    )
    creds_content = os.environ.get("GOOGLE_SHEETS_CREDS_CONTENT")

    if creds_content:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        tmp.write(creds_content.encode('utf-8'))
        tmp.close()
        creds_path = tmp.name

    if not os.path.exists(creds_path):
        raise FileNotFoundError(f"Credencial não encontrada: {creds_path}")

    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive',
    ]
    client = gspread.authorize(
        Credentials.from_service_account_file(creds_path, scopes=scopes)
    )
    _set_timeout(client, 120)
    return client


# =============================================================================
# Helpers
# =============================================================================

def sanitize_sheet_name(name):
    if not name:
        return "Local_Sem_Nome"
    name = str(name)[:100]
    for ch in ['\\', '/', '*', '?', ':', '[', ']']:
        name = name.replace(ch, '_')
    name = ' '.join(name.split())
    if not name or name.isdigit():
        name = "Local_" + name
    return name.strip()


def retry_api_call(func, max_retries=8, base_delay=3):
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


def parse_date(date_str):
    if not date_str or not date_str.strip():
        return None
    for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%y']:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            pass
    return None


def build_data_inicio_str(registros: list) -> str:
    """
    Lê a coluna J (DATA DE INÍCIO) de cada registro e constrói
    a string a exibir no dashboard:
      - Um único valor único → retorna só a data.
      - Múltiplos cursos com datas diferentes → "CURSO: DATA | CURSO: DATA"
    """
    # Mapeia curso → primeiro valor de data de início encontrado
    curso_data: dict[str, str] = {}
    for row in registros:
        curso = row[COL_CURSO].strip()       if len(row) > COL_CURSO       else ''
        data  = row[COL_DATA_INICIO].strip() if len(row) > COL_DATA_INICIO else ''
        if data and curso not in curso_data:
            curso_data[curso] = data

    if not curso_data:
        return ''

    datas_unicas = list(dict.fromkeys(curso_data.values()))   # preserva ordem

    if len(datas_unicas) == 1:
        # Todos os cursos têm a mesma data (ou há apenas um curso)
        return datas_unicas[0]

    # Datas distintas por curso → mostra "CURSO: DATA | ..."
    return " | ".join(
        f"{curso}: {data}" for curso, data in curso_data.items() if data
    )


# =============================================================================
# Criação de abas individuais por local
# =============================================================================

def filter_by_local(spreadsheet, local_name):
    sanitized = sanitize_sheet_name(local_name)

    try:
        for ws in spreadsheet.worksheets():
            if ws.title.strip().upper() == sanitized.strip().upper():
                spreadsheet.del_worksheet(ws)
                print(f"   🗑️  Aba removida: {sanitized}")
    except Exception as e:
        print(f"   Erro ao deletar aba: {e}")

    sheet = retry_api_call(
        lambda: spreadsheet.add_worksheet(title=sanitized, rows=1000, cols=len(HEADERS))
    )
    retry_api_call(lambda: sheet.update('A1:K1', [HEADERS]))
    return sheet


# =============================================================================
# Dashboard
# =============================================================================

def create_dashboard(spreadsheet, locals_dict):
    """
    Cria aba DASHBOARD com:
      Col A — LOCAL
      Col B — CURSOS          (cursos únicos separados por " | ")
      Col C — DATA DE INÍCIO  (da coluna J; por curso se datas distintas)
      Col D — TOTAL INSCRIÇÕES
      Col E — DIA ANTERIOR
      Col F — ÚLTIMA SEMANA
      Col G — DATA CONSULTA
    """
    DASH = "DASHBOARD"

    try:
        spreadsheet.del_worksheet(spreadsheet.worksheet(DASH))
        print("   🗑️  Dashboard antigo removido")
    except gspread.exceptions.WorksheetNotFound:
        pass

    sheet = retry_api_call(
        lambda: spreadsheet.add_worksheet(title=DASH, rows=2000, cols=7)
    )

    headers = [
        'LOCAL',
        'CURSOS',
        'DATA DE INÍCIO',
        'TOTAL INSCRIÇÕES',
        'DIA ANTERIOR',
        'ÚLTIMA SEMANA',
        'DATA CONSULTA',
    ]
    retry_api_call(lambda: sheet.update('A1:G1', [headers]))

    today     = datetime.now()
    yesterday = today - timedelta(days=1)
    week_ago  = today - timedelta(days=7)

    dashboard_data = []

    for local_name, registros in locals_dict.items():
        total         = len(registros)
        yesterday_cnt = 0
        week_cnt      = 0
        cursos_vistos = []

        for row in registros:
            curso = row[COL_CURSO].strip() if len(row) > COL_CURSO else ''
            if curso and curso not in cursos_vistos:
                cursos_vistos.append(curso)

            if len(row) > COL_DATA:
                d = parse_date(row[COL_DATA])
                if d:
                    if d.date() == yesterday.date(): yesterday_cnt += 1
                    if d.date() >= week_ago.date():  week_cnt      += 1

        cursos_str     = " | ".join(cursos_vistos) if cursos_vistos else ''
        data_inicio_str = build_data_inicio_str(registros)

        dashboard_data.append([
            local_name,
            cursos_str,
            data_inicio_str,
            total,
            yesterday_cnt,
            week_cnt,
            today.strftime('%d/%m/%Y'),
        ])

    dashboard_data.sort(key=lambda x: x[0].upper())

    if dashboard_data:
        chunk_size = 50
        for i in range(0, len(dashboard_data), chunk_size):
            chunk = dashboard_data[i:i + chunk_size]
            retry_api_call(lambda c=chunk, idx=i: sheet.update(
                f"A{idx+2}:G{idx+len(c)+1}", c
            ))
            print(f"   ✓ Dashboard — bloco {i // chunk_size + 1} enviado")

    # ── Formatação ────────────────────────────────────────────────────────
    time.sleep(2)
    n_rows = len(dashboard_data)

    fmt_requests = [
        # Cabeçalho: fundo preto, texto branco, negrito, centralizado
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id,
                           "startRowIndex": 0, "endRowIndex": 1,
                           "startColumnIndex": 0, "endColumnIndex": 7},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0},
                        "textFormat": {
                            "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                            "bold": True, "fontSize": 10, "fontFamily": "Arial",
                        },
                        "horizontalAlignment": "CENTER",
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
            }
        },
        # Dados: fonte Arial 10, wrap
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id,
                           "startRowIndex": 1, "endRowIndex": n_rows + 1,
                           "startColumnIndex": 0, "endColumnIndex": 7},
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {"fontSize": 10, "fontFamily": "Arial"},
                        "wrapStrategy": "WRAP",
                    }
                },
                "fields": "userEnteredFormat(textFormat,wrapStrategy)",
            }
        },
        # Colunas C→G centralizadas (DATA DE INÍCIO, TOTAL, DIA ANT, SEMANA, DATA CONSULTA)
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id,
                           "startRowIndex": 1, "endRowIndex": n_rows + 1,
                           "startColumnIndex": 2, "endColumnIndex": 7},
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
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 340}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2}, "properties": {"pixelSize": 340}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 2, "endIndex": 3}, "properties": {"pixelSize": 200}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 3, "endIndex": 4}, "properties": {"pixelSize": 120}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 4, "endIndex": 5}, "properties": {"pixelSize": 100}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 5, "endIndex": 6}, "properties": {"pixelSize": 110}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 6, "endIndex": 7}, "properties": {"pixelSize": 110}, "fields": "pixelSize"}},
    ]

    # Zebra: cinza claro / branco
    for i in range(n_rows):
        bg = ({"red": 0.95, "green": 0.95, "blue": 0.95}
              if i % 2 == 0
              else {"red": 1.0, "green": 1.0, "blue": 1.0})
        fmt_requests.append({
            "repeatCell": {
                "range": {"sheetId": sheet.id,
                           "startRowIndex": i + 1, "endRowIndex": i + 2,
                           "startColumnIndex": 0, "endColumnIndex": 7},
                "cell": {"userEnteredFormat": {"backgroundColor": bg}},
                "fields": "userEnteredFormat(backgroundColor)",
            }
        })

    retry_api_call(lambda: spreadsheet.batch_update({"requests": fmt_requests}))

    # Negrito na coluna LOCAL
    retry_api_call(lambda: spreadsheet.batch_update({"requests": [{
        "repeatCell": {
            "range": {"sheetId": sheet.id,
                       "startRowIndex": 1, "endRowIndex": n_rows + 1,
                       "startColumnIndex": 0, "endColumnIndex": 1},
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
            "fields": "userEnteredFormat(textFormat)",
        }
    }]}))

    print(f"   ✓ DASHBOARD criado — {len(dashboard_data)} local(is)")


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 60)
    print("FILTRADOR DE INSCRIÇÕES POR LOCAL")
    print("=" * 60)

    print("\n1. Conectando ao Google Sheets...")
    client      = get_gsheet_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    print(f"   ✓ Planilha aberta: {spreadsheet.title}")

    print("\n2. Acessando aba DADOS...")
    try:
        origin_sheet = spreadsheet.worksheet(ORIGIN_SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        print(f"   ✗ Aba '{ORIGIN_SHEET_NAME}' não encontrada")
        return

    print("   ✓ Carregando dados...")
    all_values = origin_sheet.get_all_values()
    if not all_values:
        print("   ✗ Planilha vazia")
        return

    data_rows = all_values[1:]
    print(f"   ✓ Total de registros: {len(data_rows)}")

    # ── Agrupa por local ──────────────────────────────────────────────────
    print("\n3. Identificando locais...")
    locals_dict = {}
    for row in data_rows:
        if len(row) > COL_LOCAL:
            local = row[COL_LOCAL].strip()
            if local:
                locals_dict.setdefault(local, []).append(row)
    print(f"   ✓ {len(locals_dict)} local(is) encontrado(s)")

    # ── Remove abas antigas (exceto DADOS) ───────────────────────────────
    print("\n4. Limpando abas antigas...")
    keep = {ORIGIN_SHEET_NAME.upper(), "DADOS"}
    to_delete = [
        ws for ws in spreadsheet.worksheets()
        if ws.title.strip().upper() not in keep
    ]
    for ws in to_delete:
        try:
            spreadsheet.del_worksheet(ws)
            print(f"   🗑️  Deletada: {ws.title}")
            time.sleep(1)
        except Exception as e:
            print(f"   ⚠️  Erro ao deletar '{ws.title}': {e}")
    print(f"   ✓ {len(to_delete)} aba(s) removida(s)")

    # ── Cria abas por local ───────────────────────────────────────────────
    print("\n5. Criando abas por local...")
    for index, (local_name, registros) in enumerate(locals_dict.items(), start=1):
        sheet_name = sanitize_sheet_name(local_name)
        try:
            new_sheet = filter_by_local(spreadsheet, sheet_name)

            rows_to_insert = []
            for row in registros:
                while len(row) < 11:
                    row.append('')
                rows_to_insert.append([row[i] for i in range(11)])

            if rows_to_insert:
                chunk_size = 100
                for i in range(0, len(rows_to_insert), chunk_size):
                    chunk = rows_to_insert[i:i + chunk_size]
                    retry_api_call(
                        lambda c=chunk, s=new_sheet, i=i:
                            s.update(f"A{i+2}:K{i+len(c)+1}", c)
                    )
                    print(f"   ✓ {sheet_name} → bloco {i // chunk_size + 1}")

            print(f"   ✓ {sheet_name}: {len(registros)} registro(s)")

            if index % 5 == 0:
                print("   ⏳ Pausando 15s para respeitar limite da API...")
                time.sleep(15)

        except Exception as e:
            print(f"   ✗ Erro em '{sheet_name}': {e}")

    # ── Dashboard ─────────────────────────────────────────────────────────
    print("\n6. Criando DASHBOARD...")
    create_dashboard(spreadsheet, locals_dict)

    print("\n" + "=" * 60)
    print("✅ PROCESSO CONCLUÍDO!")
    print("=" * 60)
    print(f"\n  Locais:    {len(locals_dict)}")
    print(f"  Registros: {len(data_rows)}")


if __name__ == "__main__":
    main()
