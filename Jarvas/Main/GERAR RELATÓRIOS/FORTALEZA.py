"""
Script para filtrar dados de inscrições por local de curso
e criar abas separadas na mesma planilha do Google Sheets.

LÓGICA:
  - Antes de qualquer leitura, TODAS as abas de local (exceto DADOS) são
    deletadas — a limpeza acontece logo após conectar, antes de ler os dados.
  - Cada LOCAL gera uma aba própria com seus registros.
  - Dashboard inclui: LOCAL, CURSOS, DATA DE INÍCIO, TOTAL, DIA ANTERIOR,
    ÚLTIMA SEMANA, DATA CONSULTA + colunas mensais dinâmicas.
  - Colunas mensais: uma por mês, do mês da primeira inscrição até o mês
    da última, mostrando o total de inscrições por local naquele mês.
  - Dashboard formatado em vermelho escuro / vermelho claro alternados,
    com cabeçalho e linha de totais em preto.
"""

import os
import gspread
import time
import requests.exceptions
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from collections import defaultdict

SPREADSHEET_ID    = "1_xIjtNB3NIJzrbTsUkNd8PbVtMh7US0d2URi_UssFZc"
ORIGIN_SHEET_NAME = "DADOS"

COL_DATA        = 0
COL_CURSO       = 4   # coluna E
COL_LOCAL       = 8   # coluna I
COL_DATA_INICIO = 9   # coluna J

HEADERS = [
    'DATA', 'NOME', 'CPF', 'GÊNERO', 'CURSO', 'WHATSAPP',
    'CEP', 'EMAIL', 'LOCAL DO CURSO', 'DATA DE INÍCIO', 'HORÁRIO'
]

MESES_PT = {
    1: 'JAN', 2: 'FEV', 3: 'MAR', 4: 'ABR', 5: 'MAI', 6: 'JUN',
    7: 'JUL', 8: 'AGO', 9: 'SET', 10: 'OUT', 11: 'NOV', 12: 'DEZ'
}

# Cores do dashboard
COR_VERMELHO_ESCURO = {"red": 0.808, "green": 0.224, "blue": 0.224}
COR_VERMELHO_CLARO  = {"red": 0.957, "green": 0.741, "blue": 0.741}
COR_HEADER          = {"red": 0.0,   "green": 0.0,   "blue": 0.0}   # preto
COR_MES_HEADER      = {"red": 0.25,  "green": 0.25,  "blue": 0.25}  # cinza escuro
COR_MES_ATUAL       = {"red": 0.13,  "green": 0.37,  "blue": 0.13}  # verde escuro destaque


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
    Lê a coluna J (DATA DE INÍCIO) e constrói a string para o dashboard:
      - Um único valor único → retorna só a data.
      - Múltiplos cursos com datas diferentes → "CURSO: DATA | CURSO: DATA"
    """
    curso_data: dict[str, str] = {}
    for row in registros:
        curso = row[COL_CURSO].strip()       if len(row) > COL_CURSO       else ''
        data  = row[COL_DATA_INICIO].strip() if len(row) > COL_DATA_INICIO else ''
        if data and curso not in curso_data:
            curso_data[curso] = data
    if not curso_data:
        return ''
    datas_unicas = list(dict.fromkeys(curso_data.values()))
    if len(datas_unicas) == 1:
        return datas_unicas[0]
    return " | ".join(f"{curso}: {data}" for curso, data in curso_data.items() if data)


def mes_label(year: int, month: int) -> str:
    return f"{MESES_PT[month]}/{str(year)[-2:]}"


def gerar_meses(min_ym: tuple, max_ym: tuple) -> list:
    """Retorna lista de (ano, mês) do mínimo ao máximo inclusive."""
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
    print(f"\n2. Limpando {len(to_delete)} aba(s) de local existente(s)...")
    for ws in to_delete:
        try:
            spreadsheet.del_worksheet(ws)
            print(f"   🗑️  Deletada: {ws.title}")
            time.sleep(0.8)
        except Exception as e:
            print(f"   ⚠️  Erro ao deletar '{ws.title}': {e}")
    print(f"   ✓ Limpeza concluída")


# =============================================================================
# Criação de abas individuais por local
# =============================================================================

def filter_by_local(spreadsheet, local_name):
    sanitized = sanitize_sheet_name(local_name)
    for ws in spreadsheet.worksheets():
        if ws.title.strip().upper() == sanitized.strip().upper():
            spreadsheet.del_worksheet(ws)
            time.sleep(0.5)
            break
    sheet = retry_api_call(
        lambda: spreadsheet.add_worksheet(title=sanitized, rows=1000, cols=len(HEADERS))
    )
    retry_api_call(lambda: sheet.update('A1:K1', [HEADERS]))
    return sheet


# =============================================================================
# Dashboard com colunas mensais
# =============================================================================

def create_dashboard(spreadsheet, locals_dict):
    """
    Dashboard:
      Colunas fixas (A-G):
        A — LOCAL
        B — CURSOS
        C — DATA DE INÍCIO
        D — TOTAL INSCRIÇÕES
        E — DIA ANTERIOR
        F — ÚLTIMA SEMANA
        G — DATA CONSULTA

      Colunas dinâmicas (H em diante):
        Uma coluna por mês, do mês da primeira inscrição ao mês da última,
        com o total de inscrições naquele local naquele mês.
        O mês atual é destacado em verde no cabeçalho.
    """
    DASH = "DASHBOARD"
    try:
        spreadsheet.del_worksheet(spreadsheet.worksheet(DASH))
        print("   🗑️  Dashboard antigo removido")
    except gspread.exceptions.WorksheetNotFound:
        pass

    COLS_FIXAS = 7
    today     = datetime.now()
    yesterday = today - timedelta(days=1)
    week_ago  = today - timedelta(days=7)

    # ── 1. Determinar intervalo de meses ──────────────────────────────────────
    all_dates = []
    for registros in locals_dict.values():
        for row in registros:
            d = parse_date(row[COL_DATA])
            if d:
                all_dates.append(d.date())

    if all_dates:
        min_ym = (min(all_dates).year, min(all_dates).month)
        max_ym = (max(all_dates).year, max(all_dates).month)
    else:
        min_ym = max_ym = (today.year, today.month)

    meses    = gerar_meses(min_ym, max_ym)
    n_meses  = len(meses)
    total_cols = COLS_FIXAS + n_meses

    mes_atual_ym = (today.year, today.month)
    try:
        mes_atual_idx = meses.index(mes_atual_ym)
    except ValueError:
        mes_atual_idx = -1

    # ── 2. Contagem mensal por local ──────────────────────────────────────────
    contagem_mensal: dict[str, dict] = {}
    for local_name, registros in locals_dict.items():
        contagem_mensal[local_name] = defaultdict(int)
        for row in registros:
            d = parse_date(row[COL_DATA])
            if d:
                contagem_mensal[local_name][(d.year, d.month)] += 1

    # ── 3. Criar aba ──────────────────────────────────────────────────────────
    sheet = retry_api_call(
        lambda: spreadsheet.add_worksheet(title=DASH, rows=2000, cols=total_cols + 2)
    )

    from gspread.utils import rowcol_to_a1

    def col_letter(idx):   # 1-based col index → letter(s)
        return rowcol_to_a1(1, idx).rstrip('1')

    headers_fixos = [
        'LOCAL', 'CURSOS', 'DATA DE INÍCIO', 'TOTAL INSCRIÇÕES',
        'DIA ANTERIOR', 'ÚLTIMA SEMANA', 'DATA CONSULTA',
    ]
    headers_meses = [mes_label(y, m) for y, m in meses]
    headers = headers_fixos + headers_meses

    end_hdr = col_letter(total_cols)
    retry_api_call(lambda: sheet.update(f"A1:{end_hdr}1", [headers]))

    # ── 4. Montar dados ───────────────────────────────────────────────────────
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

        cursos_str      = " | ".join(cursos_vistos) if cursos_vistos else ''
        data_inicio_str = build_data_inicio_str(registros)
        mensais         = [contagem_mensal[local_name].get(ym, 0) for ym in meses]

        dashboard_data.append(
            [local_name, cursos_str, data_inicio_str, total,
             yesterday_cnt, week_cnt, today.strftime('%d/%m/%Y')]
            + mensais
        )

    dashboard_data.sort(key=lambda x: x[0].upper())

    if dashboard_data:
        chunk_size = 50
        for i in range(0, len(dashboard_data), chunk_size):
            chunk = dashboard_data[i:i + chunk_size]
            end_c = col_letter(total_cols)
            retry_api_call(lambda c=chunk, idx=i, ec=end_c: sheet.update(
                f"A{idx+2}:{ec}{idx+len(c)+1}", c
            ))
            print(f"   ✓ Dashboard — bloco {i // chunk_size + 1} enviado")

    # Linha de totais
    total_row = len(dashboard_data) + 2
    totals_fixos = [
        'TOTAL:', f'=COUNTA(B2:B{total_row-1})',
        '', f'=SUM(D2:D{total_row-1})',
        f'=SUM(E2:E{total_row-1})', f'=SUM(F2:F{total_row-1})',
        '',
    ]
    totals_meses = [
        f'=SUM({col_letter(COLS_FIXAS+i+1)}2:{col_letter(COLS_FIXAS+i+1)}{total_row-1})'
        for i in range(n_meses)
    ]
    totals = totals_fixos + totals_meses
    end_tot = col_letter(total_cols)
    retry_api_call(lambda: sheet.update(f"A{total_row}:{end_tot}{total_row}", [totals]))

    # ── 5. Formatação ─────────────────────────────────────────────────────────
    time.sleep(2)
    n_rows = len(dashboard_data)

    fmt = [
        # Cabeçalho colunas fixas: preto
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
        # Linha de totais: preto
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
        # Fonte base dados
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id, "startRowIndex": 1, "endRowIndex": total_row - 1,
                           "startColumnIndex": 0, "endColumnIndex": total_cols},
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {"fontSize": 10, "fontFamily": "Arial"},
                        "wrapStrategy": "WRAP",
                    }
                },
                "fields": "userEnteredFormat(textFormat,wrapStrategy)",
            }
        },
        # Colunas C em diante centralizadas
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id, "startRowIndex": 1, "endRowIndex": total_row,
                           "startColumnIndex": 2, "endColumnIndex": total_cols},
                "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
                "fields": "userEnteredFormat(horizontalAlignment)",
            }
        },
        # Congelar cabeçalho + 2 primeiras colunas (LOCAL e CURSOS)
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
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 2, "endIndex": 3}, "properties": {"pixelSize": 180}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 3, "endIndex": 4}, "properties": {"pixelSize": 110}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 4, "endIndex": 5}, "properties": {"pixelSize": 100}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 5, "endIndex": 6}, "properties": {"pixelSize": 110}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 6, "endIndex": 7}, "properties": {"pixelSize": 110}, "fields": "pixelSize"}},
        # Largura colunas mensais
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet.id, "dimension": "COLUMNS",
                       "startIndex": COLS_FIXAS, "endIndex": total_cols},
            "properties": {"pixelSize": 75}, "fields": "pixelSize"
        }},
    ]

    # Destaque coluna do mês atual no cabeçalho
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

    # Linhas alternadas vermelho escuro/claro (fixas) + versão desbotada (mensais)
    for i in range(n_rows):
        bg = COR_VERMELHO_ESCURO if i % 2 == 0 else COR_VERMELHO_CLARO
        # colunas fixas
        fmt.append({
            "repeatCell": {
                "range": {"sheetId": sheet.id, "startRowIndex": i + 1, "endRowIndex": i + 2,
                           "startColumnIndex": 0, "endColumnIndex": COLS_FIXAS},
                "cell": {"userEnteredFormat": {"backgroundColor": bg}},
                "fields": "userEnteredFormat(backgroundColor)",
            }
        })
        # colunas mensais: versão mais clara (mistura com branco)
        bg_mes = {k: min(1.0, v * 0.35 + 0.65) for k, v in bg.items()}
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

    print(f"   ✓ DASHBOARD criado — {n_rows} local(is) × {n_meses} meses "
          f"({mes_label(*min_ym)} → {mes_label(*max_ym)})")


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

    cleanup_sheets(spreadsheet)

    print("\n3. Acessando aba DADOS...")
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

    print("\n4. Identificando locais...")
    locals_dict = {}
    for row in data_rows:
        if len(row) > COL_LOCAL:
            local = row[COL_LOCAL].strip()
            if local:
                locals_dict.setdefault(local, []).append(row)
    print(f"   ✓ {len(locals_dict)} local(is) encontrado(s)")

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

    print("\n6. Criando DASHBOARD...")
    create_dashboard(spreadsheet, locals_dict)

    print("\n" + "=" * 60)
    print("✅ PROCESSO CONCLUÍDO!")
    print("=" * 60)
    print(f"\n  Locais:    {len(locals_dict)}")
    print(f"  Registros: {len(data_rows)}")


if __name__ == "__main__":
    main()
