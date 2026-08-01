"""
Script para filtrar dados de inscrições por LOCAL + CURSO
e criar abas separadas na mesma planilha do Google Sheets.

LÓGICA:
  - Nomes de local passam por normalize_local() para mesclar variantes
    do mesmo endereço físico em um único nome canônico.
  - Cada combinação única de LOCAL (canônico) + CURSO gera uma aba própria.
  - Nome da aba: "LOCAL - CURSO" (truncado em 100 caracteres).
  - Antes de rodar, todas as abas exceto DADOS são deletadas.
  - O dashboard mostra LOCAL, CURSO, DATA DE INÍCIO (coluna J) e totais,
    ordenado pela DATA DE INÍCIO (menor → maior), formatado em tons de
    pele claro/escuro alternados, com cabeçalho e linha de totais em preto.
"""

import os
import gspread
import time
import requests.exceptions
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

SPREADSHEET_ID    = "1AHUNdkZAdXEpCScu3ndEEIEH_Xa35ryJo8W18ItyrIE"
ORIGIN_SHEET_NAME = "DADOS"

COL_DATA        = 0
COL_CURSO       = 4   # coluna E
COL_LOCAL       = 8   # coluna I
COL_DATA_INICIO = 9   # coluna J

HEADERS = [
    'DATA', 'NOME', 'CPF', 'GÊNERO', 'CURSO', 'WHATSAPP',
    'CEP', 'EMAIL', 'LOCAL DO CURSO', 'DATA DE INÍCIO', 'HORÁRIO'
]

# Cores do dashboard (tons de pele)
COR_PELE_ESCURO = {"red": 0.886, "green": 0.722, "blue": 0.529}  # Bege escuro
COR_PELE_CLARO  = {"red": 0.965, "green": 0.871, "blue": 0.741}  # Bege claro
COR_HEADER      = {"red": 0.0,   "green": 0.0,   "blue": 0.0}    # Preto


# =============================================================================
# NORMALIZAÇÃO DE LOCAIS
# =============================================================================

LOCAL_SALA_EMPREENDEDOR = 'SALA DO EMPREENDEDOR NO CAMPO DE SANTANA (UDES) - Praça da República, 139 – Centro'

NORMALIZACAO = {
    'SALA DO EMPREENDEDOR NO CAMPO DE SANTANA (UDES) - Praça da República, 139 – Centro':
        LOCAL_SALA_EMPREENDEDOR,
    'UDES - SALA DO EMPREENDEDOR - Praça da República, nº 139 – Centro':
        LOCAL_SALA_EMPREENDEDOR,
    'UDES - SALA DO EMPREENDEDOR - Praça da República, no 139 – Centro':
        LOCAL_SALA_EMPREENDEDOR,
    'UDES - SALA DO EMPREENDEDOR NO CAMPO DE SANTANA - Praça da República, 139 – Centro':
        LOCAL_SALA_EMPREENDEDOR,
}


def normalize_local(local_name: str) -> str:
    """Retorna o nome canônico do local, aplicando o mapa de normalização."""
    return NORMALIZACAO.get(local_name.strip(), local_name.strip())


# =============================================================================
# Autenticação
# =============================================================================

def _set_timeout(client, seconds: int):
    """Define timeout na sessão HTTP (compatível com gspread 5.x e 6.x)."""
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
    """Gera o título da aba: 'LOCAL - CURSO' truncado a 100 chars."""
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
    return func()   # última tentativa — propaga erro se falhar


def parse_date(date_str: str):
    if not date_str or not date_str.strip():
        return None
    for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%y']:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            pass
    return None


# =============================================================================
# Limpeza de abas
# =============================================================================

def cleanup_sheets(spreadsheet):
    """Deleta todas as abas exceto DADOS antes de recriar."""
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

    # Remove se já existir (segurança)
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
# Dashboard
# =============================================================================

def build_data_inicio(registros: list) -> str:
    """Retorna o primeiro valor não vazio da coluna J (DATA DE INÍCIO)."""
    for row in registros:
        if len(row) > COL_DATA_INICIO:
            val = row[COL_DATA_INICIO].strip()
            if val:
                return val
    return ''


def create_dashboard(spreadsheet, combos_dict: dict):
    """
    combos_dict: { (local, curso): [linhas] }

    Dashboard:
      A — LOCAL
      B — CURSO
      C — DATA DE INÍCIO
      D — TOTAL
      E — DIA ANTERIOR
      F — ÚLTIMA SEMANA
      G — DATA CONSULTA

    Ordenado por DATA DE INÍCIO (menor → maior). Locais sem data
    válida vão para o final.
    """
    DASH = "DASHBOARD"
    try:
        spreadsheet.del_worksheet(spreadsheet.worksheet(DASH))
        time.sleep(1)
    except gspread.exceptions.WorksheetNotFound:
        pass

    sheet = retry_api_call(
        lambda: spreadsheet.add_worksheet(title=DASH, rows=2000, cols=7)
    )

    headers = ['LOCAL', 'CURSO', 'DATA DE INÍCIO', 'TOTAL', 'DIA ANTERIOR', 'ÚLTIMA SEMANA', 'DATA CONSULTA']
    retry_api_call(lambda: sheet.update('A1:G1', [headers]))

    today     = datetime.now()
    yesterday = today - timedelta(days=1)
    week_ago  = today - timedelta(days=7)

    dashboard_data = []

    for (local, curso), registros in combos_dict.items():
        total   = len(registros)
        y_count = 0
        w_count = 0

        for row in registros:
            d = parse_date(row[COL_DATA]) if len(row) > COL_DATA else None
            if d:
                if d.date() == yesterday.date(): y_count += 1
                if d.date() >= week_ago.date():  w_count += 1

        data_inicio_str = build_data_inicio(registros)
        data_inicio_dt  = parse_date(data_inicio_str)

        dashboard_data.append({
            'local': local,
            'curso': curso,
            'data_inicio_str': data_inicio_str,
            'data_inicio_dt': data_inicio_dt,
            'total': total,
            'y_count': y_count,
            'w_count': w_count,
        })

    # Ordena por DATA DE INÍCIO (menor → maior); sem data vai para o final
    dashboard_data.sort(
        key=lambda x: (
            x['data_inicio_dt'] is None,
            x['data_inicio_dt'] or datetime.max,
            x['local'].upper(),
            x['curso'].upper(),
        )
    )

    rows_out = [
        [
            d['local'],
            d['curso'],
            d['data_inicio_str'],
            d['total'],
            d['y_count'],
            d['w_count'],
            today.strftime('%d/%m/%Y'),
        ]
        for d in dashboard_data
    ]

    if rows_out:
        retry_api_call(lambda: sheet.update(
            f"A2:G{len(rows_out)+1}", rows_out
        ))

    # Linha de totais
    total_row = len(rows_out) + 2
    totals = [
        'TOTAL:',
        f'=COUNTA(B2:B{total_row-1})',
        '',
        f'=SUM(D2:D{total_row-1})',
        f'=SUM(E2:E{total_row-1})',
        f'=SUM(F2:F{total_row-1})',
        '',
    ]
    retry_api_call(lambda: sheet.update(f"A{total_row}:G{total_row}", [totals]))

    time.sleep(2)

    # ── Formatação ────────────────────────────────────────────────────────────
    fmt = [
        # Cabeçalho: preto, texto branco, negrito
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id,
                           "startRowIndex": 0, "endRowIndex": 1,
                           "startColumnIndex": 0, "endColumnIndex": 7},
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
        # Linha de totais: preto, texto branco, negrito
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id,
                           "startRowIndex": total_row - 1, "endRowIndex": total_row,
                           "startColumnIndex": 0, "endColumnIndex": 7},
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
        # Fonte base nas linhas de dados
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id,
                           "startRowIndex": 1, "endRowIndex": total_row - 1,
                           "startColumnIndex": 0, "endColumnIndex": 7},
                "cell": {"userEnteredFormat": {
                    "textFormat": {"fontSize": 10, "fontFamily": "Arial"},
                    "wrapStrategy": "WRAP",
                }},
                "fields": "userEnteredFormat(textFormat,wrapStrategy)",
            }
        },
        # Colunas C→G centralizadas
        {
            "repeatCell": {
                "range": {"sheetId": sheet.id,
                           "startRowIndex": 1, "endRowIndex": total_row,
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
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2}, "properties": {"pixelSize": 300}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 2, "endIndex": 3}, "properties": {"pixelSize": 130}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 3, "endIndex": 4}, "properties": {"pixelSize": 80},  "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 4, "endIndex": 5}, "properties": {"pixelSize": 100}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 5, "endIndex": 6}, "properties": {"pixelSize": 110}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 6, "endIndex": 7}, "properties": {"pixelSize": 110}, "fields": "pixelSize"}}, 
    ]

    # Linhas alternadas: tom de pele escuro / claro
    for i in range(len(rows_out)):
        bg = COR_PELE_ESCURO if i % 2 == 0 else COR_PELE_CLARO
        fmt.append({
            "repeatCell": {
                "range": {"sheetId": sheet.id,
                           "startRowIndex": i + 1, "endRowIndex": i + 2,
                           "startColumnIndex": 0, "endColumnIndex": 7},
                "cell": {"userEnteredFormat": {"backgroundColor": bg}},
                "fields": "userEnteredFormat(backgroundColor)",
            }
        })
    
    retry_api_call(lambda: spreadsheet.batch_update({"requests": fmt}))

    # Negrito na coluna LOCAL
    retry_api_call(lambda: spreadsheet.batch_update({"requests": [{
        "repeatCell": {
            "range": {"sheetId": sheet.id,
                       "startRowIndex": 1, "endRowIndex": total_row - 1,
                       "startColumnIndex": 0, "endColumnIndex": 1},
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
            "fields": "userEnteredFormat(textFormat)",
        }
    }]}))

    print(f"   ✓ DASHBOARD criado — {len(rows_out)} combinação(ões) LOCAL+CURSO")


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 60)
    print("FILTRADOR DE INSCRIÇÕES — LOCAL + CURSO")
    print("=" * 60)

    # 1. Conecta
    print("\n1. Conectando ao Google Sheets...")
    client      = get_gsheet_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    print(f"   ✓ Planilha aberta: {spreadsheet.title}")

    # 2. Limpa abas antigas
    cleanup_sheets(spreadsheet)

    # 3. Lê dados
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

    # 4. Agrupa por (LOCAL canônico, CURSO)
    print("\n4. Agrupando por LOCAL + CURSO...")
    combos_dict: dict[tuple, list] = {}

    for row in data_rows:
        raw_local = row[COL_LOCAL].strip() if len(row) > COL_LOCAL else ''
        curso     = row[COL_CURSO].strip() if len(row) > COL_CURSO else ''
        if raw_local:
            local = normalize_local(raw_local)
            combos_dict.setdefault((local, curso), []).append(row)

    print(f"   ✓ {len(combos_dict)} combinação(ões) LOCAL+CURSO")

    # 5. Cria abas
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

            # Pausa a cada 5 abas para não estourar rate limit
            if idx % 5 == 0:
                print("   ⏳ Pausando 10s...")
                time.sleep(10)

        except Exception as e:
            print(f"   ✗ Erro em '{title}': {e}")

    # 6. Dashboard
    print("\n6. Criando DASHBOARD...")
    create_dashboard(spreadsheet, combos_dict)

    print("\n" + "=" * 60)
    print("✅ CONCLUÍDO!")
    print("=" * 60)
    print(f"\n  Combinações LOCAL+CURSO: {len(combos_dict)}")
    print(f"  Registros totais:        {len(data_rows)}")


if __name__ == "__main__":
    main()
