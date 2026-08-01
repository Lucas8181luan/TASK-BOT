"""
Script para filtrar dados de inscrições por local de curso
e criar abas separadas na mesma planilha do Google Sheets.

Locais com o mesmo nome diferindo apenas em acentos/caracteres especiais
são mesclados automaticamente numa única aba.

DASHBOARD inclui DATA DE INÍCIO, lida diretamente da coluna J (índice 9)
de cada registro — sem alterar as demais colunas/lógica existentes.
"""

import os
import re
import unicodedata
import gspread
import time
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

SPREADSHEET_ID = "1jsPa-_iqxmGdIT0NWMYzRPPe6z86lLA33zhW_wW1Nn4"
ORIGIN_SHEET_NAME = "DADOS"

COL_DATA        = 0
COL_LOCAL       = 8   # coluna I
COL_DATA_INICIO = 9   # coluna J  ← DATA DE INÍCIO

HEADERS = [
    'DATA',
    'NOME',
    'CPF',
    'GÊNERO',
    'CURSO',
    'WHATSAPP',
    'CEP',
    'EMAIL',
    'LOCAL DO CURSO',
    'DATA DE INÍCIO',
    'HORÁRIO'
]

# Cores zebrado (linhas pares/ímpares)
COLOR_ODD  = {"red": 0.678, "green": 0.847, "blue": 0.902}  # azul claro
COLOR_EVEN = {"red": 0.565, "green": 0.753, "blue": 0.820}  # azul um pouco mais escuro


# =========================
# NORMALIZAÇÃO DE LOCAIS
# =========================

def normalize_local(name: str) -> str:
    """
    Retorna uma chave de comparação sem acentos, sem pontuação
    e em maiúsculas. Usada para detectar locais "iguais" que foram
    escritos de formas diferentes (ex.: MARÊ vs MARÉ vs MARE).
    """
    nfkd = unicodedata.normalize('NFKD', name)
    without_accents = ''.join(c for c in nfkd if not unicodedata.combining(c))
    upper = without_accents.upper()
    cleaned = re.sub(r'[^A-Z0-9\s\-/]', '', upper)
    cleaned = re.sub(r'[\s\-]+', ' ', cleaned).strip()
    return cleaned


def build_locals_dict(rows: list) -> dict:
    """
    Agrupa as linhas por local do curso (coluna índice 8).
    Locais cujos nomes normalizados são idênticos são mesclados;
    o nome canônico é o da PRIMEIRA ocorrência encontrada.
    """
    canonical: dict[str, str] = {}
    result: dict[str, list] = {}

    for row in rows:
        if len(row) <= COL_LOCAL:
            continue
        local = row[COL_LOCAL].strip()
        if not local:
            continue

        key = normalize_local(local)

        if key not in canonical:
            canonical[key] = local
            result[local] = []

        result[canonical[key]].append(row)

    return result


def build_data_inicio(registros: list) -> str:
    """Retorna o primeiro valor não vazio da coluna J (DATA DE INÍCIO)."""
    for row in registros:
        if len(row) > COL_DATA_INICIO:
            val = row[COL_DATA_INICIO].strip()
            if val:
                return val
    return ''


# =========================
# GOOGLE SHEETS
# =========================

def get_gsheet_client():
    import tempfile
    creds_path = os.environ.get(
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
        raise FileNotFoundError(
            f"Arquivo de credencial não encontrado: {creds_path}\n"
            "Verifique o caminho ou a variável de ambiente GOOGLE_SHEETS_CREDS."
        )

    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    return gspread.authorize(creds)


def sanitize_sheet_name(name):
    if not name:
        return "Local_Sem_Nome"
    name = str(name)[:100]
    for char in ['\\', '/', '*', '?', ':', '[', ']']:
        name = name.replace(char, '_')
    name = ' '.join(name.split())
    if not name or name.isdigit():
        name = "Local_" + name
    return name.strip()


def retry_api_call(func, max_retries=5, base_delay=2):
    for attempt in range(max_retries):
        try:
            return func()
        except gspread.exceptions.APIError as e:
            if '429' in str(e):
                wait_time = base_delay * (2 ** attempt)
                print(f"   ⚠️ Quota excedida. Tentando novamente em {wait_time}s (tentativa {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                raise
    return func()


def filter_by_local(spreadsheet, local_name):
    sanitized_name = sanitize_sheet_name(local_name)

    try:
        for ws in spreadsheet.worksheets():
            if ws.title.strip().upper() == sanitized_name.strip().upper():
                spreadsheet.del_worksheet(ws)
                time.sleep(1)
    except Exception as e:
        print(f"Erro ao deletar aba existente: {e}")

    new_sheet = retry_api_call(
        lambda: spreadsheet.add_worksheet(title=sanitized_name, rows=1000, cols=len(HEADERS))
    )
    retry_api_call(lambda: new_sheet.insert_row(HEADERS, 1))
    time.sleep(1)

    return new_sheet


def parse_date(date_str):
    if not date_str or not date_str.strip():
        return None
    date_str = date_str.strip()
    for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%y']:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


# =========================
# DASHBOARD
# =========================

def create_dashboard(spreadsheet, locals_dict):
    """
    Dashboard:
      A — LOCAL
      B — DATA DE INÍCIO  (coluna J da planilha de origem)
      C — TOTAL
      D — MÊS ATUAL
      E — ONTEM
      F — SEMANA
      G — ÚLTIMA DATA
    """
    DASHBOARD_SHEET_NAME = "DASHBOARD"

    try:
        spreadsheet.del_worksheet(spreadsheet.worksheet(DASHBOARD_SHEET_NAME))
        time.sleep(1)
    except gspread.exceptions.WorksheetNotFound:
        pass

    sheet = retry_api_call(
        lambda: spreadsheet.add_worksheet(title=DASHBOARD_SHEET_NAME, rows=2000, cols=7)
    )

    headers = ['LOCAL', 'DATA DE INÍCIO', 'TOTAL', 'MÊS ATUAL', 'ONTEM', 'SEMANA', 'ÚLTIMA DATA']
    retry_api_call(lambda: sheet.update('A1:G1', [headers]))

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=6)
    month_start = today.replace(day=1)

    dashboard_data = []

    for local_name, registros in locals_dict.items():
        total = len(registros)
        y_count = 0
        w_count = 0
        m_count = 0
        datas_registro = []

        for row in registros:
            parsed = parse_date(row[COL_DATA])
            if parsed:
                d = parsed.date()
                datas_registro.append(d)
                if d == yesterday:
                    y_count += 1
                if week_ago <= d <= today:
                    w_count += 1
                if month_start <= d <= today:
                    m_count += 1

        data_inicio_str = build_data_inicio(registros)
        ultima_data = max(datas_registro).strftime('%d/%m/%Y') if datas_registro else ''

        dashboard_data.append([
            local_name, data_inicio_str, total, m_count, y_count, w_count, ultima_data
        ])

    # Ordena A-Z pelo nome do local
    dashboard_data.sort(key=lambda x: x[0].upper())

    if dashboard_data:
        retry_api_call(lambda: sheet.update(f"A2:G{len(dashboard_data)+1}", dashboard_data))

    # Linha de totais
    total_row = len(dashboard_data) + 2
    totals = [
        'TOTAL:',
        '',
        f'=SUM(C2:C{total_row-1})',
        f'=SUM(D2:D{total_row-1})',
        f'=SUM(E2:E{total_row-1})',
        f'=SUM(F2:F{total_row-1})',
        ''
    ]
    retry_api_call(lambda: sheet.update(f"A{total_row}:G{total_row}", [totals]))

    # ---- FORMATAÇÃO ----
    time.sleep(2)

    formatting_requests = [
        # Cabeçalho: fundo preto, texto branco negrito
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id, "startRowIndex": 0, "endRowIndex": 1,
                          "startColumnIndex": 0, "endColumnIndex": 7},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0},
                        "textFormat": {
                            "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                            "bold": True, "fontSize": 10, "fontFamily": "Arial"
                        },
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },
        # Linha de totais: fundo preto, texto branco negrito
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id, "startRowIndex": total_row - 1, "endRowIndex": total_row,
                          "startColumnIndex": 0, "endColumnIndex": 7},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0},
                        "textFormat": {
                            "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                            "bold": True, "fontSize": 10, "fontFamily": "Arial"
                        },
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },
        # Fonte base nas linhas de dados
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id, "startRowIndex": 1, "endRowIndex": total_row - 1,
                          "startColumnIndex": 0, "endColumnIndex": 7},
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {"fontSize": 10, "fontFamily": "Arial"}
                    }
                },
                "fields": "userEnteredFormat(textFormat)"
            }
        },
        # Congela cabeçalho
        {
            "updateSheetProperties": {
                "properties": {"sheetId": sheet.id, "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount"
            }
        },
        # Larguras das colunas
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 400}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2}, "properties": {"pixelSize": 130}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 2, "endIndex": 3}, "properties": {"pixelSize": 70},  "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 3, "endIndex": 4}, "properties": {"pixelSize": 90},  "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 4, "endIndex": 5}, "properties": {"pixelSize": 70},  "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 5, "endIndex": 6}, "properties": {"pixelSize": 80},  "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 6, "endIndex": 7}, "properties": {"pixelSize": 110}, "fields": "pixelSize"}},
    ]

    # Zebrado: linhas alternadas com dois tons de azul
    for i in range(len(dashboard_data)):
        row_index = i + 1  # linha 1 = cabeçalho, dados começam em 1
        bg = COLOR_ODD if (i % 2 == 0) else COLOR_EVEN
        formatting_requests.append({
            "repeatCell": {
                "range": {"sheetId": sheet.id, "startRowIndex": row_index, "endRowIndex": row_index + 1,
                          "startColumnIndex": 0, "endColumnIndex": 7},
                "cell": {"userEnteredFormat": {"backgroundColor": bg}},
                "fields": "userEnteredFormat(backgroundColor)"
            }
        })

    retry_api_call(lambda: spreadsheet.batch_update({"requests": formatting_requests}))

    # Centraliza colunas numéricas e datas
    retry_api_call(lambda: spreadsheet.batch_update({"requests": [
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id, "startRowIndex": 1, "endRowIndex": total_row,
                          "startColumnIndex": 1, "endColumnIndex": 7},
                "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
                "fields": "userEnteredFormat(horizontalAlignment)"
            }
        }
    ]}))

    print(f"   ✓ DASHBOARD criado e formatado com {len(dashboard_data)} locais")
    return sheet


# =========================
# MAIN
# =========================

def main():
    print("=" * 60)
    print("FILTRADOR DE INSCRIÇÕES POR LOCAL")
    print("=" * 60)

    print("\n1. Conectando ao Google Sheets...")
    client = get_gsheet_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    print(f"   ✓ Planilha aberta: {spreadsheet.title}")

    print("\n2. Acessando aba DADOS...")
    try:
        origin_sheet = spreadsheet.worksheet(ORIGIN_SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        print(f"   ✗ Erro: Aba '{ORIGIN_SHEET_NAME}' não encontrada!")
        return

    print("   ✓ Carregando dados...")
    all_values = origin_sheet.get_all_values()

    if not all_values:
        print("   ✗ Erro: Planilha vazia!")
        return

    data_rows = all_values[1:]
    print(f"   ✓ Total de registros: {len(data_rows)}")

    print("\n3. Identificando locais únicos (com mesclagem por acentos)...")
    locals_dict = build_locals_dict(data_rows)

    print(f"   ✓ Encontrados {len(locals_dict)} locais únicos:")
    for local, registros in locals_dict.items():
        print(f"      - {local}: {len(registros)} inscrições")

    print("\n4. Criando abas filtradas por local...")

    for local_name, registros in locals_dict.items():
        try:
            new_sheet = filter_by_local(spreadsheet, local_name)

            rows_to_insert = []
            for row in registros:
                while len(row) < 11:
                    row.append('')
                rows_to_insert.append([
                    row[0],   # DATA
                    row[1],   # NOME
                    row[2],   # CPF
                    row[3],   # GÊNERO
                    row[4],   # CURSO
                    row[5],   # WHATSAPP
                    row[6],   # CEP
                    row[7],   # EMAIL
                    row[8],   # LOCAL DO CURSO
                    row[9],   # DATA DE INÍCIO
                    row[10],  # HORÁRIO
                ])

            if rows_to_insert:
                retry_api_call(lambda: new_sheet.insert_rows(rows_to_insert, 2))
                time.sleep(1)

            # Remove linhas em branco
            all_sheet_values = new_sheet.get_all_values()
            rows_to_delete = []
            for idx, row in enumerate(all_sheet_values[1:], start=2):
                if all(cell.strip() == '' for cell in row):
                    rows_to_delete.append(idx)
            for idx in reversed(rows_to_delete):
                retry_api_call(lambda: new_sheet.delete_rows(idx))
                time.sleep(0.5)

            print(f"   ✓ {sanitize_sheet_name(local_name)}: {len(registros)} registros salvos")

        except Exception as e:
            print(f"   ✗ Erro ao criar aba '{local_name}': {str(e)}")

    print("\n5. Criando DASHBOARD...")
    create_dashboard(spreadsheet, locals_dict)

    print("\n" + "=" * 60)
    print("PROCESSO CONCLUÍDO!")
    print("=" * 60)
    print(f"\nResumo:")
    print(f"  - Total de locais processados: {len(locals_dict)}")
    print(f"  - Total de registros: {len(data_rows)}")
    print(f"  - Abas criadas na planilha: {len(locals_dict)}")


if __name__ == "__main__":
    main()
