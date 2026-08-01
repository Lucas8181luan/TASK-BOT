"""
Script para filtrar dados de inscrições por LOCAL + CURSO
e criar abas separadas na mesma planilha do Google Sheets.

LÓGICA:
  - Cada combinação única de LOCAL + CURSO gera uma aba própria.
  - Nome da aba: "LOCAL - CURSO" (truncado em 100 caracteres).
  - Antes de rodar, todas as abas exceto DADOS são deletadas.
  - O dashboard reflete LOCAL, CURSO, DATA DE INÍCIO, TOTAL, TOTAL NO MÊS,
    DIA ANTERIOR, ÚLTIMA SEMANA, DATA CONSULTA + colunas mensais dinâmicas
    (do primeiro mês com inscrição até o último mês com inscrição).
  - Dashboard formatado em amarelo escuro / amarelo claro alternados.
"""

import os
import gspread
import time
import requests.exceptions
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from collections import defaultdict

SPREADSHEET_ID    = "1abhr3M3FBNOeXKopdEd_Z7O40th4EwW2x4MtECgQOe4"
ORIGIN_SHEET_NAME = "DADOS"

COL_DATA        = 0
COL_CURSO       = 4
COL_LOCAL       = 8
COL_DATA_INICIO = 9

HEADERS = [
    'DATA', 'NOME', 'CPF', 'GÊNERO', 'CURSO', 'WHATSAPP',
    'CEP', 'EMAIL', 'LOCAL DO CURSO', 'DATA DE INÍCIO', 'HORÁRIO'
]

MESES_PT = {
    1: 'JAN', 2: 'FEV', 3: 'MAR', 4: 'ABR', 5: 'MAI', 6: 'JUN',
    7: 'JUL', 8: 'AGO', 9: 'SET', 10: 'OUT', 11: 'NOV', 12: 'DEZ'
}

# Cores do dashboard
COR_AMARELO_ESCURO = {"red": 1.000, "green": 0.851, "blue": 0.302}
COR_AMARELO_CLARO  = {"red": 1.000, "green": 0.953, "blue": 0.651}
COR_HEADER         = {"red": 0.741, "green": 0.584, "blue": 0.000}  # dourado
COR_MES_HEADER     = {"red": 0.25,  "green": 0.25,  "blue": 0.25}   # cinza escuro
COR_MES_ATUAL      = {"red": 0.13,  "green": 0.37,  "blue": 0.13}   # verde escuro


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

def sanitize_sheet_name(name: str) -> str:
    if not name:
        return "Sem_Nome"
    name = str(name)[:100]
    for ch in ['\\', '/', '*', '?', ':', '[', ']']:
        name = name.replace(ch, '_')
    name = ' '.join(name.split())
    if not name or name.isdigit():
        name = "Local_" + name
    return name.strip()


def make_tab_title(local: str, curso: str) -> str:
    title = f"{local} - {curso}" if curso else local
    return sanitize_sheet_name(title)


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


def parse_date(date_str: str):
    if not date_str or not date_str.strip():
        return None
    for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%y']:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            pass
    return None


def build_data_inicio(registros: list) -> str:
    for row in registros:
        if len(row) > COL_DATA_INICIO:
            val = row[COL_DATA_INICIO].strip()
            if val:
                return val
    return ''


def mes_label(year: int, month: int) -> str:
    return f"{MESES_PT[month]}/{str(year)[-2:]}"


def gerar_meses(min_ym: tuple, max_ym: tuple) -> list:
    meses = []
    y, m = min_ym
    while (y, m) <= max_ym:
        meses.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return meses


# =============================================================================
# Limpeza de abas
# =============================================================================

def cleanup_sheets(spreadsheet):
    keep = {ORIGIN_SHEET_NAME.upper(), "DADOS"}
    to_delete = [
        ws for ws in spreadsheet.worksheets()
        if ws.title.strip().upper() not in keep
    ]
    print(f"\n2. Limpando {len(to_delete)} aba(s) existente(s)...")
    for ws in to_delete:
        try:
            spreadsheet.del_worksheet(ws)
            print(f"   🗑️  Deletada: {ws.title}")
            time.sleep(0.8)
        except Exception as e:
            print(f"   ⚠️  Erro ao deletar '{ws.title}': {e}")
    print(f"   ✓ Limpeza concluída")


# =============================================================================
# Criação de aba por LOCAL+CURSO
# =============================================================================

def create_tab(spreadsheet, title: str):
    sanitized = sanitize_sheet_name(title)
    for ws in spreadsheet.worksheets():
        if ws.title.strip().upper() == sanitized.strip().upper():
            spreadsheet.del_worksheet(ws)
            time.sleep(0.5)
            break
    sheet = retry_api_call(
        lambda: spreadsheet.add_worksheet(title=sanitized, rows=1000, cols=11)
    )
    retry_api_call(lambda: sheet.update('A1:K1', [HEADERS]))
    return sheet


# =============================================================================
# Dashboard com colunas mensais
# =============================================================================

def create_dashboard(spreadsheet, combos_dict: dict):
    """
    combos_dict: { (local, curso): [linhas] }

    Colunas fixas (A-H):
      A — LOCAL           E — TOTAL NO MÊS
      B — CURSO           F — DIA ANTERIOR
      C — DATA DE INÍCIO  G — ÚLTIMA SEMANA
      D — TOTAL           H — DATA CONSULTA

    Colunas dinâmicas (I em diante):
      Uma por mês, do primeiro mês com inscrição ao último,
      mostrando o total da combinação LOCAL+CURSO naquele mês.
      Para exatamente no último mês com dados.
    """
    DASH = "DASHBOARD"
    try:
        spreadsheet.del_worksheet(spreadsheet.worksheet(DASH))
        time.sleep(1)
    except gspread.exceptions.WorksheetNotFound:
        pass

    COLS_FIXAS = 8
    today       = datetime.now()
    yesterday   = today - timedelta(days=1)
    week_ago    = today - timedelta(days=7)
    month_start = today.replace(day=1)

    # ── 1. Intervalo de meses ─────────────────────────────────────────────────
    all_dates = []
    for registros in combos_dict.values():
        for row in registros:
            d = parse_date(row[COL_DATA])
            if d:
                all_dates.append(d.date())

    if all_dates:
        min_ym = (min(all_dates).year, min(all_dates).month)
        # Para no último mês com inscrição real
        max_ym = (max(all_dates).year, max(all_dates).month)
    else:
        min_ym = max_ym = (today.year, today.month)

    meses      = gerar_meses(min_ym, max_ym)
    n_meses    = len(meses)
    total_cols = COLS_FIXAS + n_meses

    mes_atual_ym  = (today.year, today.month)
    mes_atual_idx = meses.index(mes_atual_ym) if mes_atual_ym in meses else -1

    # ── 2. Contagem mensal por combo ──────────────────────────────────────────
    contagem_mensal: dict[tuple, dict] = {}
    for combo_key, registros in combos_dict.items():
        contagem_mensal[combo_key] = defaultdict(int)
        for row in registros:
            d = parse_date(row[COL_DATA])
            if d:
                contagem_mensal[combo_key][(d.year, d.month)] += 1

    # ── 3. Criar aba ──────────────────────────────────────────────────────────
    sheet = retry_api_call(
        lambda: spreadsheet.add_worksheet(title=DASH, rows=2000, cols=total_cols + 2)
    )

    from gspread.utils import rowcol_to_a1

    def col_letter(idx):
        return rowcol_to_a1(1, idx).rstrip('1')

    headers_fixos = [
        'LOCAL', 'CURSO', 'DATA DE INÍCIO', 'TOTAL', 'TOTAL NO MÊS',
        'DIA ANTERIOR', 'ÚLTIMA SEMANA', 'DATA CONSULTA',
    ]
    headers = headers_fixos + [mes_label(y, m) for y, m in meses]
    retry_api_call(lambda: sheet.update(f"A1:{col_letter(total_cols)}1", [headers]))

    # ── 4. Montar dados ───────────────────────────────────────────────────────
    dashboard_data = []

    for (local, curso), registros in combos_dict.items():
        total   = len(registros)
        y_count = 0
        w_count = 0
        m_count = 0

        for row in registros:
            d = parse_date(row[COL_DATA]) if len(row) > COL_DATA else None
            if d:
                if d.date() == yesterday.date():                          y_count += 1
                if d.date() >= week_ago.date():                           w_count += 1
                if month_start.date() <= d.date() <= today.date():        m_count += 1

        data_inicio_str = build_data_inicio(registros)
        mensais         = [contagem_mensal[(local, curso)].get(ym, 0) for ym in meses]

        dashboard_data.append({
            'local': local, 'curso': curso,
            'data_inicio_str': data_inicio_str,
            'total': total, 'm_count': m_count,
            'y_count': y_count, 'w_count': w_count,
            'mensais': mensais,
        })

    dashboard_data.sort(key=lambda x: (x['local'].upper(), x['curso'].upper()))

    rows_out = [
        [d['local'], d['curso'], d['data_inicio_str'], d['total'],
         d['m_count'], d['y_count'], d['w_count'], today.strftime('%d/%m/%Y')]
        + d['mensais']
        for d in dashboard_data
    ]

    if rows_out:
        chunk_size = 50
        for i in range(0, len(rows_out), chunk_size):
            chunk = rows_out[i:i + chunk_size]
            ec = col_letter(total_cols)
            retry_api_call(lambda c=chunk, idx=i, e=ec:
                sheet.update(f"A{idx+2}:{e}{idx+len(c)+1}", c))
            print(f"   ✓ Dashboard — bloco {i // chunk_size + 1} enviado")

    # Linha de totais
    total_row = len(rows_out) + 2
    totals_fixos = [
        'TOTAL:', f'=COUNTA(B2:B{total_row-1})',
        '', f'=SUM(D2:D{total_row-1})', f'=SUM(E2:E{total_row-1})',
        f'=SUM(F2:F{total_row-1})', f'=SUM(G2:G{total_row-1})', '',
    ]
    totals_meses = [
        f'=SUM({col_letter(COLS_FIXAS+i+1)}2:{col_letter(COLS_FIXAS+i+1)}{total_row-1})'
        for i in range(n_meses)
    ]
    retry_api_call(lambda: sheet.update(
        f"A{total_row}:{col_letter(total_cols)}{total_row}",
        [totals_fixos + totals_meses]
    ))

    # ── 5. Formatação ─────────────────────────────────────────────────────────
    time.sleep(2)

    fmt = [
        # Cabeçalho colunas fixas: dourado
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id, "startRowIndex": 0, "endRowIndex": 1,
                           "startColumnIndex": 0, "endColumnIndex": COLS_FIXAS},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": COR_HEADER,
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
        # Cabeçalho colunas mensais: cinza escuro
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id, "startRowIndex": 0, "endRowIndex": 1,
                           "startColumnIndex": COLS_FIXAS, "endColumnIndex": total_cols},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": COR_MES_HEADER,
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
        # Linha de totais: dourado
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id, "startRowIndex": total_row - 1, "endRowIndex": total_row,
                           "startColumnIndex": 0, "endColumnIndex": total_cols},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": COR_HEADER,
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
        # Fonte base
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id, "startRowIndex": 1, "endRowIndex": total_row - 1,
                           "startColumnIndex": 0, "endColumnIndex": total_cols},
                "cell": {"userEnteredFormat": {
                    "textFormat": {"fontSize": 10, "fontFamily": "Arial"},
                    "wrapStrategy": "WRAP",
                }},
                "fields": "userEnteredFormat(textFormat,wrapStrategy)",
            }
        },
        # Centralizar colunas C em diante
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id, "startRowIndex": 1, "endRowIndex": total_row,
                           "startColumnIndex": 2, "endColumnIndex": total_cols},
                "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
                "fields": "userEnteredFormat(horizontalAlignment)",
            }
        },
        # Congelar cabeçalho + colunas LOCAL e CURSO
        {
            "updateSheetProperties": {
                "properties": {"sheetId": sheet.id, "gridProperties": {
                    "frozenRowCount": 1, "frozenColumnCount": 2,
                }},
                "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount",
            }
        },
        # Larguras colunas fixas
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 340}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2}, "properties": {"pixelSize": 300}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 2, "endIndex": 3}, "properties": {"pixelSize": 130}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 3, "endIndex": 4}, "properties": {"pixelSize": 80},  "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 4, "endIndex": 5}, "properties": {"pixelSize": 100}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 5, "endIndex": 6}, "properties": {"pixelSize": 100}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 6, "endIndex": 7}, "properties": {"pixelSize": 110}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 7, "endIndex": 8}, "properties": {"pixelSize": 110}, "fields": "pixelSize"}},
        # Largura colunas mensais
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet.id, "dimension": "COLUMNS",
                       "startIndex": COLS_FIXAS, "endIndex": total_cols},
            "properties": {"pixelSize": 75}, "fields": "pixelSize"
        }},
    ]

    # Destaque cabeçalho do mês atual em verde
    if mes_atual_idx >= 0:
        col_idx = COLS_FIXAS + mes_atual_idx
        fmt.append({
            "repeatCell": {
                "range": {"sheetId": sheet.id, "startRowIndex": 0, "endRowIndex": 1,
                           "startColumnIndex": col_idx, "endColumnIndex": col_idx + 1},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": COR_MES_ATUAL,
                        "textFormat": {
                            "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                            "bold": True, "fontSize": 10, "fontFamily": "Arial",
                        },
                        "horizontalAlignment": "CENTER",
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
            }
        })

    # Linhas alternadas: amarelo nas fixas, versão clara nas mensais
    for i in range(len(rows_out)):
        bg = COR_AMARELO_ESCURO if i % 2 == 0 else COR_AMARELO_CLARO
        fmt.append({
            "repeatCell": {
                "range": {"sheetId": sheet.id, "startRowIndex": i + 1, "endRowIndex": i + 2,
                           "startColumnIndex": 0, "endColumnIndex": COLS_FIXAS},
                "cell": {"userEnteredFormat": {"backgroundColor": bg}},
                "fields": "userEnteredFormat(backgroundColor)",
            }
        })
        # Colunas mensais: versão desbotada do amarelo
        bg_mes = {k: min(1.0, v * 0.3 + 0.7) for k, v in bg.items()}
        fmt.append({
            "repeatCell": {
                "range": {"sheetId": sheet.id, "startRowIndex": i + 1, "endRowIndex": i + 2,
                           "startColumnIndex": COLS_FIXAS, "endColumnIndex": total_cols},
                "cell": {"userEnteredFormat": {"backgroundColor": bg_mes}},
                "fields": "userEnteredFormat(backgroundColor)",
            }
        })

    retry_api_call(lambda: spreadsheet.batch_update({"requests": fmt}))

    # Negrito coluna LOCAL
    retry_api_call(lambda: spreadsheet.batch_update({"requests": [{
        "repeatCell": {
            "range": {"sheetId": sheet.id, "startRowIndex": 1, "endRowIndex": total_row - 1,
                       "startColumnIndex": 0, "endColumnIndex": 1},
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
            "fields": "userEnteredFormat(textFormat)",
        }
    }]}))

    print(f"   ✓ DASHBOARD criado — {len(rows_out)} combo(s) × {n_meses} meses "
          f"({mes_label(*min_ym)} → {mes_label(*max_ym)})")


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 60)
    print("FILTRADOR DE INSCRIÇÕES — LOCAL + CURSO")
    print("=" * 60)

    print("\n1. Conectando ao Google Sheets...")
    client      = get_gsheet_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    print(f"   ✓ Planilha aberta: {spreadsheet.title}")

    cleanup_sheets(spreadsheet)

    print("\n3. Lendo aba DADOS...")
    try:
        origin = spreadsheet.worksheet(ORIGIN_SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        print(f"   ✗ Aba '{ORIGIN_SHEET_NAME}' não encontrada")
        return

    all_values = origin.get_all_values()
    if not all_values:
        print("   ✗ Planilha vazia")
        return

    data_rows = all_values[1:]
    print(f"   ✓ {len(data_rows)} registro(s) encontrado(s)")

    print("\n4. Agrupando por LOCAL + CURSO...")
    combos_dict: dict[tuple, list] = {}
    for row in data_rows:
        local = row[COL_LOCAL].strip() if len(row) > COL_LOCAL else ''
        curso = row[COL_CURSO].strip() if len(row) > COL_CURSO else ''
        if local:
            combos_dict.setdefault((local, curso), []).append(row)
    print(f"   ✓ {len(combos_dict)} combinação(ões) LOCAL+CURSO")

    print("\n5. Criando abas...")
    for idx, ((local, curso), registros) in enumerate(combos_dict.items(), start=1):
        title = make_tab_title(local, curso)
        try:
            sheet = create_tab(spreadsheet, title)
            new_rows = []
            for r in registros:
                while len(r) < 11:
                    r.append('')
                new_rows.append([r[i] for i in range(11)])
            if new_rows:
                chunk_size = 100
                for i in range(0, len(new_rows), chunk_size):
                    chunk = new_rows[i:i + chunk_size]
                    retry_api_call(
                        lambda c=chunk, s=sheet, i=i:
                            s.update(f"A{i+2}:K{i+len(c)+1}", c)
                    )
            print(f"   ✓ [{idx}] {title} ({len(registros)} registro(s))")
            if idx % 5 == 0:
                print("   ⏳ Pausando 10s...")
                time.sleep(10)
        except Exception as e:
            print(f"   ✗ Erro em '{title}': {e}")

    print("\n6. Criando DASHBOARD...")
    create_dashboard(spreadsheet, combos_dict)

    print("\n" + "=" * 60)
    print("✅ CONCLUÍDO!")
    print("=" * 60)
    print(f"\n  Combinações LOCAL+CURSO: {len(combos_dict)}")
    print(f"  Registros totais:        {len(data_rows)}")


if __name__ == "__main__":
    main()
