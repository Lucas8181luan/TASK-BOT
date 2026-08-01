# -*- coding: utf-8 -*-
"""
================================================================================
 AUTOMAÇÃO DE CADASTRO - MULTI-POLO (Movimenta.Rio / Fortaleza / outros)
================================================================================
 NOVIDADE DESTA VERSÃO: COORDENADAS EDITÁVEIS POR POLO
 -------------------------------------------------------------------------
 Cada polo agora guarda também um dicionário "coordenadas", com os pontos
 de clique (x, y) usados durante a automação (ex: campo Nome, campo Sexo,
 campo CEP, botão Próximo...). Esses pontos podem ser:
   1) Editados manualmente (digitando x e y direto na tela).
   2) Capturados automaticamente: a pessoa clica em "Capturar (8s)", tem
      8 segundos (com contagem regressiva visível) para posicionar o
      mouse no lugar certo da tela, e a coordenada é lida com
      pyautogui.position(). Depois aparece um aviso mostrando a
      coordenada capturada, com um botão "Copiar coordenadas".
 Cada ponto de coordenada pode ter uma IMAGEM DE REFERÊNCIA (um print
 mostrando visualmente onde aquele ponto fica na tela do sistema), para
 ajudar a pessoa a saber exatamente onde clicar durante a captura.
 Ao criar um POLO NOVO, a pessoa também configura as coordenadas dele
 (a tela de coordenadas abre automaticamente logo após criar o polo).

 NOVIDADE DESTA REVISÃO:
 -------------------------------------------------------------------------
 - Adicionada a coordenada "Campo Nome" (com imagem de referência
   coordenadas_nome.png), que agora é a PRIMEIRA coordenada mostrada na
   tela de configuração de cada polo, pois é o primeiro clique feito no
   fluxo da automação.
 - Esse clique no campo Nome corrige um bug em que o nome não aparecia
   corretamente na hora de criar a matrícula.
 - As imagens de referência foram exibidas em um tamanho um pouco maior.
 - A ordem das coordenadas na tela agora segue exatamente a ordem em que
   elas são usadas dentro do código da automação.
================================================================================
"""
import numpy as np
from PIL import ImageGrab, Image, ImageTk
import easyocr
import pyautogui
import pyperclip
import time
import re
import threading
import json
import os
import uuid
import tkinter as tk
from tkinter import ttk, messagebox
# ==============================================================================
# IMAGENS DE REFERÊNCIA DAS COORDENADAS (ajuste os caminhos se necessário)
# ==============================================================================
PASTA_IMAGENS_COORDENADAS = r"C:\Users\lucas\OneDrive\Documentos\JARVAS\Jarvas\Main\APPS\STYLE"
# Metadados de cada TIPO de coordenada que pode existir em um polo.
# "imagem": caminho do print de referência (pode não existir -- nesse caso
# a tela mostra um aviso "Imagem não encontrada" em vez de travar o programa).
# "explicacao": texto opcional exibido embaixo do título, para dar contexto
# extra sobre a importância daquele clique.
COORD_METADADOS = {
    "nome": {
        "label": "Campo Nome (1\u00ba clique)",
        "imagem": os.path.join(PASTA_IMAGENS_COORDENADAS, "coordenadas_nome.png"),
        "explicacao": (
            "Clique neste campo (Nome) logo no in\u00edcio do preenchimento. "
            "Isso evita um bug em que o nome n\u00e3o aparece corretamente na "
            "hora de criar a matr\u00edcula."
        ),
    },
    "sexo": {
        "label": "Campo Sexo",
        "imagem": os.path.join(PASTA_IMAGENS_COORDENADAS, "coordenada_sexo.png"),
    },
    "cep": {
        "label": "Campo CEP",
        "imagem": os.path.join(PASTA_IMAGENS_COORDENADAS, "coordenada_cep.png"),
    },
    "botao_proximo1": {
        "label": "Botão Próximo (1)",
        "imagem": os.path.join(PASTA_IMAGENS_COORDENADAS, "coordenada_bot\u00e3o_proximo.png"),
    },
    "f10_click": {
        "label": "Clique extra do F10 (só fluxo Fortaleza)",
        "imagem": None,
    },
    "botao_final": {
        "label": "Botão final de confirmação (só fluxo Fortaleza)",
        "imagem": None,
    },
}
# Quais coordenadas cada MODELO de fluxo usa, e na ordem que aparecem na tela
# (a ordem abaixo é a MESMA ordem em que cada coordenada é usada dentro do
# código da automação, do primeiro clique até o último).
FLUXO_COORDENADAS = {
    "rj": ["nome", "sexo", "cep", "botao_proximo1"],
    "fortaleza": ["nome", "sexo", "cep", "botao_proximo1", "f10_click", "botao_final"],
}
# Coordenadas padrão (as mesmas que já estavam fixas no código antes)
COORDENADAS_RJ_PADRAO = {
    "nome": [480, 320],
    "sexo": [480, 361],
    "cep": [289, 456],
    "botao_proximo1": [964, 644],
}
COORDENADAS_CE_PADRAO = {
    "nome": [284, 410],
    "sexo": [284, 450],
    "cep": [45, 567],
    "botao_proximo1": [890, 802],
    "f10_click": [205, 405],
    "botao_final": [946, 805],
}
def copia_coordenadas_padrao(fluxo):
    base = COORDENADAS_CE_PADRAO if fluxo == "fortaleza" else COORDENADAS_RJ_PADRAO
    return {k: list(v) for k, v in base.items()}
# ==============================================================================
# CURSOS PADRÃO -- POLO RJ (Movimenta.Rio)
# ==============================================================================
CURSOS_RJ_PADRAO = [
    {"chaves": ["AUXILIAR ADMINISTRATIVO"],
     "texto": "Movimenta: Hibrido - Auxiliar Administrativo v2"},
    {"chaves": ["AGENTE DE DEFESA AMBIENTAL"],
     "texto": "Movimenta: Hibrido - Agente de Defesa Ambiental v2"},
    {"chaves": ["MARKETING DIGITAL", "MARKETING"],
     "texto": "Movimenta: Hibrido - Marketing Digital v2"},
    {"chaves": ["GAR\u00c7OM"],
     "texto": "Movimenta: Hibrido - Garcom (Boteco) v2"},
    {"chaves": ["INTELIG\u00caNCIA ARTIFICIAL"],
     "texto": "Movimenta: Hibrido - Inteligencia Artificial v2"},
    {"chaves": ["CUMIN"],
     "texto": "Movimenta: Hibrido - Cumim (Boteco) v2"},
    {"chaves": ["RECEPCIONISTA"],
     "texto": "Movimenta: Hibrido - Recepcionista v2"},
    {"chaves": ["SOCIAL MEDIA"],
     "texto": "Movimenta: Hibrido - Social Media v2"},
    {"chaves": ["ASSISTENTE DE LOG\u00cdSTICA"],
     "texto": "Movimenta: Hibrido - Assistente de Logistica v2"},
    {"chaves": ["AUXILIAR DE COZINHA"],
     "texto": "Movimenta: Hibrido - Auxiliar de Cozinha v2"},
    {"chaves": ["GOVERNAN\u00c7A ESG"],
     "texto": "Movimenta: Hibrido - Gerenciamento ESG v2"},
    {"chaves": ["UXUI DESIGNER"],
     "texto": "Movimenta: Hibrido - UX/UI Designer v2"},
    {"chaves": ["GERENCIAMENTO TR\u00c1FEGO DIGITAL"],
     "texto": "Movimenta: Hibrido - Gerenciamento Trafego Digital v2"},
    {"chaves": ["CAMAREIRO"],
     "texto": "Movimenta: Hibrido - Camareiro v2"},
    {"chaves": ["ORIENTADOR DE HOTELARIA"],
     "texto": "Movimenta: Hibrido - Orientador de Hotelaria v2"},
    {"chaves": ["PEDREIRO DE ALVENARIA ESTRUTURAL"],
     "texto": "Movimenta: Hibrido - Pedreiro de Alvenaria Estrutural v2"},
    {"chaves": ["APLICA\u00c7\u00c3O DE REVESTIMENTO CER\u00c2MICOS"],
     "texto": "Movimenta: Hibrido - Aplicacao de Revestimento Ceramicos v2"},
    {"chaves": ["INSTALADOR HIDR\u00c1ULICO PREDIAL"],
     "texto": "Movimenta: Hibrido - Instalador Hidraulico Predial v2"},
    {"chaves": ["CARPINTEIRO DE OBRAS"],
     "texto": "Movimenta: Hibrido - Carpinteiro de Obras v2"},
    {"chaves": ["ELETRICISTA PREDIAL"],
     "texto": "Movimenta: Hibrido - Eletricista Predial v2"},
    {"chaves": ["SERRALHEIRO DE ALUM\u00cdNIO"],
     "texto": "Movimenta: Hibrido - Serralheiro de Aluminio v2"},
    {"chaves": ["AGENTE DE TURISMO CORPORATIVO"],
     "texto": "Movimenta: Hibrido - Agente de Turismo Corporativo v2"},
    {"chaves": ["MONITOR DE LAZER E RECREA\u00c7\u00c3O"],
     "texto": "Movimenta: Hibrido - Monitor de Lazer e Recreacao v2"},
    {"chaves": ["ATENDENTE DE SAL\u00c3O PARA CAF\u00c9 DA MANH\u00c3"],
     "texto": "Movimenta: Hibrido - Atendente de Salao para Cafe da Manha v2"},
    {"chaves": ["BENEF\u00cdCIO DE PESCADO PARA VENDA"],
     "texto": "Movimenta: Hibrido - Beneficio de Pescado para Venda v2"},
    {"chaves": ["T\u00c9CNICAS E PESCA SUSTENT\u00c1VEL"],
     "texto": "Movimenta: Hibrido - Tecnicas e Pesca Sustentavel v2"},
    {"chaves": ["ECOTURISMO E GEST\u00c3O DE UNIDADES"],
     "texto": "Movimenta: Hibrido - Ecoturismo e Gestao de Unidades v2"},
    {"chaves": ["GESTOR DE RES\u00cdDUOS S\u00d3LIDOS"],
     "texto": "Movimenta: Hibrido - Gestor de Residuos Solidos v2"},
    {"chaves": ["OPERADOR DE SISTEMA DE COMPOSTAGEM"],
     "texto": "Movimenta: Hibrido - Operador de Sistema de Compostagem v2"},
    {"chaves": ["\U0001f4d1 PREPARAT\u00d3RIO ENCCEJA 2026"],
     "texto": "1 - Preparatorio Encceja: Presencial - Encceja 2025"},
    {"chaves": ["DESIGNER DE SOBRANCELHAS"],
     "texto": "Movimenta: Hibrido - Designer De Sobrancelhas v2"},
    {"chaves": ["MANICURE"],
     "texto": "Movimenta: Hibrido - Manicure v2"},
    {"chaves": ["TRANCISTA"],
     "texto": "Movimenta: Hibrido - Trancista v2"},
]
# ==============================================================================
# CURSOS PADRÃO -- POLO CE (Fortaleza)
# ==============================================================================
CURSOS_CE_PADRAO = [
    {"chaves": ["AUXILIAR ADMINISTRATIVO"],
     "texto": "Movimenta: Hibrido - Auxiliar Administrativo v2"},
    {"chaves": ["AGENTE DE DEFESA AMBIENTAL"],
     "texto": "Movimenta: Hibrido - Agente de Defesa Ambiental v2"},
    {"chaves": ["MARKETING DIGITAL"],
     "texto": "Movimenta: Hibrido - Marketing Digital v2"},
    {"chaves": ["GAR\u00c7OM"],
     "texto": "Movimenta: Hibrido - Garcom (Boteco) v2"},
    {"chaves": ["INTELIG\u00caNCIA ARTIFICIAL"],
     "texto": "Movimenta: Hibrido - Inteligencia Artificial v2"},
    {"chaves": ["CUMIN"],
     "texto": "Movimenta: Hibrido - Cumim (Boteco) v2"},
    {"chaves": ["RECEPCIONISTA"],
     "texto": "Movimenta: Hibrido - Recepcionista v2"},
    {"chaves": ["SOCIAL MEDIA"],
     "texto": "Movimenta: Hibrido - Social Media v2"},
    {"chaves": ["ASSISTENTE DE LOG\u00cdSTICA"],
     "texto": "Movimenta: Hibrido - Assistente de Logistica v2"},
    {"chaves": ["AUXILIAR DE COZINHA"],
     "texto": "Movimenta: Hibrido - Auxiliar de Cozinha v2"},
    {"chaves": ["GOVERNAN\u00c7A ESG"],
     "texto": "Movimenta: Hibrido - Gerenciamento ESG v2"},
    {"chaves": ["UXUI DESIGNER"],
     "texto": "Movimenta: Hibrido - UX/UI Designer v2"},
    {"chaves": ["GERENCIAMENTO TR\u00c1FEGO DIGITAL"],
     "texto": "Movimenta: Hibrido - Gerenciamento Trafego Digital v2"},
    {"chaves": ["CAMAREIRO"],
     "texto": "Movimenta: Hibrido - Camareiro v2"},
    {"chaves": ["ORIENTADOR DE HOTELARIA"],
     "texto": "Movimenta: Hibrido - Orientador de Hotelaria v2"},
    {"chaves": ["PEDREIRO DE ALVENARIA ESTRUTURAL"],
     "texto": "Movimenta: Hibrido - Pedreiro de Alvenaria Estrutural v2"},
    {"chaves": ["APLICA\u00c7\u00c3O DE REVESTIMENTO CER\u00c2MICOS"],
     "texto": "Movimenta: Hibrido - Aplicacao de Revestimento Ceramicos v2"},
    {"chaves": ["INSTALADOR HIDR\u00c1ULICO PREDIAL"],
     "texto": "Movimenta: Hibrido - Instalador Hidraulico Predial v2"},
    {"chaves": ["CARPINTEIRO DE OBRAS"],
     "texto": "Movimenta: Hibrido - Carpinteiro de Obras v2"},
    {"chaves": ["ELETRICISTA PREDIAL"],
     "texto": "Movimenta: Hibrido - Eletricista Predial v2"},
    {"chaves": ["SERRALHEIRO DE ALUM\u00cdNIO"],
     "texto": "Movimenta: Hibrido - Serralheiro de Aluminio v2"},
    {"chaves": ["AGENTE DE TURISMO CORPORATIVO"],
     "texto": "Movimenta: Hibrido - Agente de Turismo Corporativo v2"},
    {"chaves": ["MONITOR DE LAZER E RECREA\u00c7\u00c3O"],
     "texto": "Movimenta: Hibrido - Monitor de Lazer e Recreacao v2"},
    {"chaves": ["ATENDENTE DE SAL\u00c3O PARA CAF\u00c9 DA MANH\u00c3"],
     "texto": "Movimenta: Hibrido - Atendente de Salao para Cafe da Manha v2"},
    {"chaves": ["BENEF\u00cdCIO DE PESCADO PARA VENDA"],
     "texto": "Movimenta: Hibrido - Beneficio de Pescado para Venda v2"},
    {"chaves": ["T\u00c9CNICAS E PESCA SUSTENT\u00c1VEL"],
     "texto": "Movimenta: Hibrido - Tecnicas e Pesca Sustentavel v2"},
    {"chaves": ["ECOTURISMO E GEST\u00c3O DE UNIDADES"],
     "texto": "Movimenta: Hibrido - Ecoturismo e Gestao de Unidades v2"},
    {"chaves": ["GESTOR DE RES\u00cdDUOS S\u00d3LIDOS"],
     "texto": "Movimenta: Hibrido - Gestor de Residuos Solidos v2"},
    {"chaves": ["OPERADOR DE SISTEMA DE COMPOSTAGEM"],
     "texto": "Movimenta: Hibrido - Operador de Sistema de Compostagem v2"},
    {"chaves": ["\U0001f4d1 PREPARAT\u00d3RIO ENCCEJA 2026"],
     "texto": "1 - Preparatorio Encceja: Presencial - Encceja 2025"},
    {"chaves": ["DESIGNER DE SOBRANCELHAS"],
     "texto": "Movimenta: Hibrido - Designer De Sobrancelhas v2"},
    {"chaves": ["MANICURE"],
     "texto": "Movimenta: Hibrido - Manicure v2"},
    {"chaves": ["TRANCISTA"],
     "texto": "Movimenta: Hibrido - Trancista v2"},
    {"chaves": ["PEDICURE"],
     "texto": "Movimenta: Hibrido - Pedicure v2"},
    {"chaves": ["DESIGNER DE UNHAS"],
     "texto": "Movimenta: Hibrido - Designer De Unhas v2"},
    {"chaves": ["EXTENS\u00c3O DE C\u00cdLIOS"],
     "texto": "Movimenta.Fortaleza: Hibrido - Extens\u00e3o de C\u00edlios"},
]
def novo_id():
    return uuid.uuid4().hex[:8]
POLOS = [
    {
        "id": "rj",
        "nome": "RJ - Movimenta.Rio",
        "evento": "11 - Movimenta.Rio: A\u00e7\u00e3o Externa",
        "polo_texto": "RJ - Movimenta.Rio",
        "fluxo": "rj",
        "cursos": CURSOS_RJ_PADRAO,
        "coordenadas": copia_coordenadas_padrao("rj"),
    },
    {
        "id": "ce",
        "nome": "CE - Fortaleza",
        "evento": "11 - Movimenta.Rio: A\u00e7\u00e3o Externa",
        "polo_texto": "CE - Fortaleza",
        "fluxo": "fortaleza",
        "cursos": CURSOS_CE_PADRAO,
        "coordenadas": copia_coordenadas_padrao("fortaleza"),
    },
]
ARQUIVO_CONFIG_POLOS = "polos_config.json"
def carregar_config_polos():
    """Se existir um arquivo salvo (polos_config.json), ele SUBSTITUI
    totalmente a lista POLOS. Se algum polo salvo não tiver "coordenadas"
    (arquivos salvos de versões antigas do programa), aplica as
    coordenadas padrão do modelo de fluxo dele, para não quebrar. Se o
    polo já tiver "coordenadas" mas faltar alguma chave nova (ex: "nome",
    adicionada nesta vers\u00e3o), completa só a chave que falta com o valor
    padrão, sem mexer nas que já foram configuradas manualmente."""
    global POLOS
    if os.path.exists(ARQUIVO_CONFIG_POLOS):
        try:
            with open(ARQUIVO_CONFIG_POLOS, "r", encoding="utf-8") as f:
                salvos = json.load(f)
            nova_lista = []
            for p in salvos:
                if all(k in p for k in ("nome", "evento", "polo_texto", "fluxo", "cursos")):
                    padrao = copia_coordenadas_padrao(p["fluxo"])
                    coordenadas = p.get("coordenadas") or {}
                    for chave, valor in padrao.items():
                        coordenadas.setdefault(chave, valor)
                    nova_lista.append({
                        "id": p.get("id", novo_id()),
                        "nome": p["nome"],
                        "evento": p["evento"],
                        "polo_texto": p["polo_texto"],
                        "fluxo": p["fluxo"],
                        "cursos": p["cursos"],
                        "coordenadas": coordenadas,
                    })
            if nova_lista:
                POLOS[:] = nova_lista
        except Exception as e:
            print(f"[AVISO] N\u00e3o foi poss\u00edvel carregar {ARQUIVO_CONFIG_POLOS}: {e}")
def salvar_config_polos():
    try:
        with open(ARQUIVO_CONFIG_POLOS, "w", encoding="utf-8") as f:
            json.dump(POLOS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[AVISO] N\u00e3o foi poss\u00edvel salvar {ARQUIVO_CONFIG_POLOS}: {e}")
def obter_texto_do_curso(cursos_lista, curso_copiado):
    for item in cursos_lista:
        if curso_copiado in item["chaves"]:
            return item["texto"]
    return None
def obter_coordenada(polo, chave):
    """Retorna (x, y) da coordenada 'chave' do polo. Se não existir por
    algum motivo, cai para o padrão do modelo de fluxo do polo."""
    coords = polo.get("coordenadas") or {}
    valor = coords.get(chave)
    if not valor:
        valor = copia_coordenadas_padrao(polo["fluxo"]).get(chave, [0, 0])
    return int(valor[0]), int(valor[1])
# ==============================================================================
# CONTROLE DE EXECUÇÃO
# ==============================================================================
class ControleAutomacao:
    def __init__(self):
        self.rodando = False
        self.evento_parar = threading.Event()
        self.thread = None
        self.velocidade = 1.0
controle = ControleAutomacao()
class ParadaSolicitada(Exception):
    pass
def deve_parar():
    return controle.evento_parar.is_set()
def espera(segundos_multiplo=1):
    total = segundos_multiplo * controle.velocidade
    fatia = 0.1
    tempo_restante = total
    while tempo_restante > 0:
        if deve_parar():
            raise ParadaSolicitada()
        time.sleep(min(fatia, tempo_restante))
        tempo_restante -= fatia
# ==============================================================================
# OCR
# ==============================================================================
reader = None
def inicializar_ocr():
    global reader
    if reader is None:
        reader = easyocr.Reader(['pt'])
def capturar_e_ler_tela():
    largura_tela, altura_tela = ImageGrab.grab().size
    bbox = (0, 0, int(largura_tela * 0.4), int(altura_tela * 0.8))
    screenshot = ImageGrab.grab(bbox=bbox)
    img_np = np.array(screenshot)
    return img_np
# ==============================================================================
# FLUXO "RJ" -- coordenadas vêm de polo["coordenadas"]
# ==============================================================================
def _fluxo_rj(polo, log, callback_status):
    for programa in range(100):
        if deve_parar():
            raise ParadaSolicitada()
        log(f"--- Iniciando registro {programa + 1} ({polo['nome']}) ---")
        pyautogui.hotkey('Ctrl', 'c')
        espera()
        pyperclip.paste()
        espera()
        pyautogui.hotkey('alt', 'tab')
        espera()
        pyautogui.press('insert')
        espera()
        pyautogui.press('tab')
        espera(6)
        pyautogui.press('Enter')
        espera(3)
        pyautogui.hotkey('Ctrl', 'v')
        espera()
        pyautogui.press('enter')
        espera()
        pyautogui.hotkey('Ctrl', 'v')
        espera()
        pyautogui.press('enter')
        espera()
        # BOTÃO SEXO
        pyautogui.hotkey('alt', 'tab')
        espera()
        pyautogui.press('right')
        espera()
        pyautogui.hotkey('Ctrl', 'c')
        espera()
        pyautogui.press('left')
        espera()
        sexo = pyperclip.paste()
        pyautogui.hotkey('alt', 'tab')
        espera()
        # CAMPO NOME -- clique feito primeiro para evitar o bug do nome não
        # aparecer corretamente na hora de criar a matrícula
        x_nome, y_nome = obter_coordenada(polo, "nome")
        pyautogui.click(x=x_nome, y=y_nome)
        espera()
        x_sexo, y_sexo = obter_coordenada(polo, "sexo")
        pyautogui.click(x=x_sexo, y=y_sexo)
        espera()
        pyautogui.write(sexo)
        espera()
        # BOTÃO CEP
        x_cep, y_cep = obter_coordenada(polo, "cep")
        pyautogui.click(x=x_cep, y=y_cep)
        espera()
        pyautogui.hotkey('alt', 'tab')
        espera()
        for r in range(4):
            pyautogui.press('right')
        espera()
        pyautogui.hotkey('Ctrl', 'c')
        espera()
        cep = pyperclip.paste()
        espera()
        for l in range(4):
            pyautogui.press('left')
        espera()
        pyautogui.hotkey('alt', 'tab')
        espera()
        pyautogui.write(cep)
        espera()
        # BOTÃO PROXIMO - 1
        x_prox, y_prox = obter_coordenada(polo, "botao_proximo1")
        pyautogui.click(x=x_prox, y=y_prox)
        espera()
        pyautogui.press('tab')
        espera()
        # TIPO DE CONTRATO
        pyautogui.hotkey('alt', 'tab')
        espera()
        for i in range(9):
            pyautogui.press('right')
        espera()
        pyautogui.hotkey('Ctrl', 'c')
        espera()
        turma = pyperclip.paste()
        espera()
        for i in range(9):
            pyautogui.press('left')
        espera()
        pyautogui.hotkey('alt', 'tab')
        espera()
        pyautogui.write("Bolsa")
        espera()
        pyautogui.press('tab')
        # CHROME
        pyautogui.hotkey('alt', 'tab')
        espera(2)
        for i in range(4):
            pyautogui.press('left')
        espera()
        pyautogui.hotkey('Ctrl', 'c')
        espera()
        data_de_inscricao = pyperclip.paste()
        espera()
        for i in range(4):
            pyautogui.press('right')
        espera()
        # F10
        pyautogui.hotkey('alt', 'tab')
        espera()
        for i in range(8):
            pyautogui.press('backspace')
        pyautogui.write(data_de_inscricao)
        espera()
        pyautogui.press('tab')
        pyautogui.press('tab')
        # EVENTO
        pyautogui.write(polo["evento"])
        espera()
        pyautogui.press('tab')
        # CURSO
        pyautogui.hotkey('alt', 'tab')
        espera()
        for _ in range(2):
            pyautogui.press('right')
        espera()
        pyautogui.hotkey('Ctrl', 'c')
        espera()
        curso_copiado = pyperclip.paste()
        espera()
        for _ in range(2):
            pyautogui.press('left')
        espera()
        pyautogui.hotkey('alt', 'tab')
        texto_curso = obter_texto_do_curso(polo["cursos"], curso_copiado)
        if texto_curso is not None:
            pyautogui.write(texto_curso)
        else:
            log(f"[AVISO] Curso n\u00e3o mapeado: '{curso_copiado}' (nada foi escrito).")
        espera(2)
        pyautogui.press('tab')
        espera(2)
        # ADMINISTRADOR / COORDENADOR
        pyautogui.write("Daniele Rodrigues da Silva")
        espera()
        pyautogui.press('tab')
        pyautogui.write("Guilherme Carvalho")
        espera()
        # BOTÃO PROXIMO - 2
        for _ in range(5):
            pyautogui.press('tab')
        espera()
        # PARTE - 3
        pyautogui.press('space')
        for _ in range(2):
            pyautogui.press('tab')
        pyautogui.write(polo["polo_texto"])
        espera()
        # BOTÃO GRAVAR
        for _ in range(6):
            pyautogui.press('tab')
        pyautogui.press('enter')
        espera()
        # EXCEL
        pyautogui.hotkey('alt', 'tab')
        espera()
        pyautogui.press('left')
        pyautogui.press('space')
        espera()
        pyautogui.press('down')
        pyautogui.press('right')
        espera()
        log(f"--- Registro {programa + 1} conclu\u00eddo ---")
        if callback_status:
            callback_status(programa + 1)
# ==============================================================================
# FLUXO "FORTALEZA" -- coordenadas vêm de polo["coordenadas"]
# ==============================================================================
def _fluxo_fortaleza(polo, log, callback_status):
    for programa in range(100):
        if deve_parar():
            raise ParadaSolicitada()
        log(f"--- Iniciando registro {programa + 1} ({polo['nome']}) ---")
        pyautogui.hotkey('ctrl', 'c')
        espera()
        pyperclip.paste()
        espera()
        pyautogui.hotkey('alt', 'tab')
        espera()
        pyautogui.press('insert')
        espera()
        pyautogui.press('tab')
        espera(5)
        pyautogui.press('Enter')
        espera(3)
        pyautogui.hotkey('ctrl', 'v')
        espera()
        pyautogui.press('enter')
        espera()
        pyautogui.hotkey('Ctrl', 'c')
        espera()
        pyautogui.press('enter')
        espera()
        # BOTÃO SEXO
        pyautogui.hotkey('alt', 'tab')
        espera()
        pyautogui.press('right')
        espera()
        pyautogui.hotkey('ctrl', 'c')
        espera()
        pyautogui.press('left')
        espera()
        sexo = pyperclip.paste()
        pyautogui.hotkey('alt', 'tab')
        espera()
        # CAMPO NOME -- clique feito primeiro para evitar o bug do nome não
        # aparecer corretamente na hora de criar a matrícula
        x_nome, y_nome = obter_coordenada(polo, "nome")
        pyautogui.click(x=x_nome, y=y_nome)
        espera()
        x_sexo, y_sexo = obter_coordenada(polo, "sexo")
        pyautogui.click(x=x_sexo, y=y_sexo)
        espera()
        pyautogui.write(sexo)
        espera()
        # BOTÃO CEP
        x_cep, y_cep = obter_coordenada(polo, "cep")
        pyautogui.click(x=x_cep, y=y_cep)
        espera()
        pyautogui.hotkey('alt', 'tab')
        espera()
        for r in range(4):
            pyautogui.press('right')
        espera()
        pyautogui.hotkey('ctrl', 'c')
        espera()
        cep = pyperclip.paste()
        espera()
        for l in range(4):
            pyautogui.press('left')
        espera()
        pyautogui.hotkey('alt', 'tab')
        espera()
        pyautogui.write(cep)
        espera()
        # BOTÃO PROXIMO - 1
        x_prox, y_prox = obter_coordenada(polo, "botao_proximo1")
        pyautogui.click(x=x_prox, y=y_prox)
        espera(2)
        pyautogui.press('tab')
        espera()
        # TIPO DE CONTRATO
        pyautogui.hotkey('alt', 'tab')
        espera()
        for i in range(9):
            pyautogui.press('right')
        espera()
        pyautogui.hotkey('ctrl', 'c')
        espera()
        turma = pyperclip.paste()
        espera()
        for i in range(9):
            pyautogui.press('left')
        espera()
        pyautogui.hotkey('alt', 'tab')
        espera()
        pyautogui.write(turma)
        espera()
        pyautogui.press('tab')
        # CHROME
        pyautogui.hotkey('alt', 'tab')
        espera()
        for i in range(4):
            pyautogui.press('left')
        espera()
        pyautogui.hotkey('ctrl', 'c')
        espera()
        data_de_inscricao = pyperclip.paste()
        espera()
        for i in range(4):
            pyautogui.press('right')
        espera()
        # F10
        pyautogui.hotkey('alt', 'tab')
        espera()
        x_f10, y_f10 = obter_coordenada(polo, "f10_click")
        pyautogui.click(x=x_f10, y=y_f10)
        espera()
        for i in range(8):
            pyautogui.press('backspace')
        pyautogui.write(data_de_inscricao)
        espera()
        pyautogui.press('tab')
        pyautogui.press('tab')
        # EVENTO
        pyautogui.write(polo["evento"])
        espera()
        pyautogui.press('tab')
        # CURSO
        pyautogui.hotkey('alt', 'tab')
        espera()
        for _ in range(2):
            pyautogui.press('right')
        espera()
        pyautogui.hotkey('ctrl', 'c')
        espera()
        curso_copiado = pyperclip.paste()
        espera()
        for _ in range(2):
            pyautogui.press('left')
        espera()
        pyautogui.hotkey('alt', 'tab')
        texto_curso = obter_texto_do_curso(polo["cursos"], curso_copiado)
        if texto_curso is not None:
            pyautogui.write(texto_curso)
        else:
            log(f"[AVISO] Curso n\u00e3o mapeado: '{curso_copiado}' (nada foi escrito).")
        espera()
        pyautogui.press('tab')
        espera()
        # ADMINISTRADOR / COORDENADOR
        pyautogui.write("Lucas Luan Pereira Vieira")
        espera()
        pyautogui.press('tab')
        pyautogui.write("Marcus Vinicius Coppola Souto")
        espera()
        # BOTÃO PROXIMO - 2
        for _ in range(5):
            pyautogui.press('tab')
        espera()
        # PARTE - 3
        pyautogui.press('space')
        for _ in range(2):
            pyautogui.press('tab')
        pyautogui.write(polo["polo_texto"])
        espera()
        # BOTÃO GRAVAR
        for _ in range(15):
            pyautogui.press('tab')
        pyautogui.press('enter')
        espera()
        pyautogui.press('tab')
        espera()
        for _ in range(2):
            pyautogui.press('enter')
        espera()
        x_final, y_final = obter_coordenada(polo, "botao_final")
        pyautogui.click(x=x_final, y=y_final)
        espera()
        # EXCEL
        pyautogui.hotkey('alt', 'tab')
        espera()
        pyautogui.press('left')
        pyautogui.press('space')
        espera()
        pyautogui.press('down')
        pyautogui.press('right')
        espera()
        log(f"--- Registro {programa + 1} conclu\u00eddo ---")
        if callback_status:
            callback_status(programa + 1)
# ==============================================================================
# PONTO ÚNICO DE ENTRADA DA AUTOMAÇÃO
# ==============================================================================
def rodar_automacao(polo, callback_status=None, callback_log=None):
    def log(msg):
        print(msg)
        if callback_log:
            callback_log(msg)
    try:
        inicializar_ocr()
        capturar_e_ler_tela()
        log(f"Polo selecionado: {polo['nome']}")
        log("Aguardando 5 segundos antes de iniciar...")
        espera(5)
        if polo["fluxo"] == "fortaleza":
            _fluxo_fortaleza(polo, log, callback_status)
        else:
            _fluxo_rj(polo, log, callback_status)
        log("Automa\u00e7\u00e3o finalizada (todos os registros processados).")
    except ParadaSolicitada:
        log("Automa\u00e7\u00e3o encerrada pelo usu\u00e1rio.")
    finally:
        controle.rodando = False
        if callback_status:
            callback_status(None)
# ==============================================================================
# INTERFACE GRÁFICA
# ==============================================================================
COR_FUNDO            = "#0B1220"
COR_FUNDO_PAINEL     = "#0F1B33"
COR_FUNDO_PAINEL_2   = "#13224A"
COR_BORDA            = "#1E2E5C"
COR_TEXTO            = "#E6EAF5"
COR_TEXTO_SECUNDARIO = "#9AA6C7"
COR_DESTAQUE         = "#3B6CF6"
COR_DESTAQUE_HOVER   = "#5A85FF"
COR_PERIGO           = "#E5484D"
COR_PERIGO_HOVER     = "#F16469"
COR_SUCESSO          = "#2FD07A"
COR_SUCESSO_HOVER    = "#4CE092"
COR_AVISO            = "#F5A623"
def configurar_estilo(root):
    estilo = ttk.Style(root)
    estilo.theme_use("clam")
    root.configure(bg=COR_FUNDO)
    estilo.configure("TFrame", background=COR_FUNDO)
    estilo.configure("Painel.TFrame", background=COR_FUNDO_PAINEL)
    estilo.configure("TLabelframe", background=COR_FUNDO_PAINEL,
                      bordercolor=COR_BORDA, relief="flat")
    estilo.configure("TLabelframe.Label", background=COR_FUNDO_PAINEL,
                      foreground=COR_DESTAQUE, font=("Segoe UI", 10, "bold"))
    estilo.configure("TLabel", background=COR_FUNDO_PAINEL, foreground=COR_TEXTO,
                      font=("Segoe UI", 10))
    estilo.configure("Titulo.TLabel", background=COR_FUNDO, foreground=COR_TEXTO,
                      font=("Segoe UI", 20, "bold"))
    estilo.configure("Subtitulo.TLabel", background=COR_FUNDO, foreground=COR_TEXTO_SECUNDARIO,
                      font=("Segoe UI", 10))
    estilo.configure("Secundario.TLabel", background=COR_FUNDO_PAINEL,
                      foreground=COR_TEXTO_SECUNDARIO, font=("Segoe UI", 9))
    estilo.configure("TEntry", fieldbackground=COR_FUNDO_PAINEL_2, foreground=COR_TEXTO,
                      bordercolor=COR_BORDA, insertcolor=COR_TEXTO, relief="flat", padding=6)
    estilo.map("TEntry", fieldbackground=[("focus", COR_FUNDO_PAINEL_2)])
    estilo.configure("TCombobox", fieldbackground=COR_FUNDO_PAINEL_2, background=COR_FUNDO_PAINEL_2,
                      foreground=COR_TEXTO, arrowcolor=COR_TEXTO, bordercolor=COR_BORDA,
                      relief="flat", padding=6)
    estilo.map("TCombobox", fieldbackground=[("readonly", COR_FUNDO_PAINEL_2)],
               foreground=[("readonly", COR_TEXTO)])
    estilo.configure("Primario.TButton", background=COR_DESTAQUE, foreground="#FFFFFF",
                      font=("Segoe UI", 10, "bold"), padding=(14, 8), borderwidth=0, relief="flat")
    estilo.map("Primario.TButton",
               background=[("active", COR_DESTAQUE_HOVER), ("disabled", "#2A3560")],
               foreground=[("disabled", "#6E7897")])
    estilo.configure("Perigo.TButton", background=COR_PERIGO, foreground="#FFFFFF",
                      font=("Segoe UI", 10, "bold"), padding=(14, 8), borderwidth=0, relief="flat")
    estilo.map("Perigo.TButton",
               background=[("active", COR_PERIGO_HOVER), ("disabled", "#2A3560")],
               foreground=[("disabled", "#6E7897")])
    estilo.configure("PerigoPequeno.TButton", background=COR_PERIGO, foreground="#FFFFFF",
                      font=("Segoe UI", 9, "bold"), padding=(6, 3), borderwidth=0, relief="flat")
    estilo.map("PerigoPequeno.TButton", background=[("active", COR_PERIGO_HOVER)])
    estilo.configure("Secundario.TButton", background=COR_FUNDO_PAINEL_2, foreground=COR_TEXTO,
                      font=("Segoe UI", 10), padding=(12, 7), borderwidth=0, relief="flat")
    estilo.map("Secundario.TButton", background=[("active", COR_BORDA)])
    estilo.configure("Sucesso.TButton", background=COR_SUCESSO, foreground="#062012",
                      font=("Segoe UI", 10, "bold"), padding=(14, 8), borderwidth=0, relief="flat")
    estilo.map("Sucesso.TButton",
               background=[("active", COR_SUCESSO_HOVER), ("disabled", "#2A3560")],
               foreground=[("disabled", "#6E7897")])
    estilo.configure("Aviso.TButton", background=COR_AVISO, foreground="#241900",
                      font=("Segoe UI", 9, "bold"), padding=(10, 6), borderwidth=0, relief="flat")
    estilo.map("Aviso.TButton", background=[("active", "#FFB847"), ("disabled", "#2A3560")])
    estilo.configure("Vertical.TScrollbar", background=COR_FUNDO_PAINEL_2,
                      troughcolor=COR_FUNDO, bordercolor=COR_FUNDO,
                      arrowcolor=COR_TEXTO_SECUNDARIO, relief="flat")
    return estilo
# ==============================================================================
# WIDGET: Linha de captura/edição de UMA coordenada (com imagem de referência)
# ==============================================================================
class LinhaCoordenada(tk.Frame):
    """Um "quadrinho" para uma coordenada: mostra a imagem de referência (se
    existir), uma explicação opcional, os campos X/Y editáveis, e o botão de
    captura com contagem regressiva de 8 segundos."""
    TAMANHO_IMAGEM = (280, 170)
    def __init__(self, master, chave, valor_atual, bg):
        super().__init__(master, bg=bg)
        self.chave = chave
        meta = COORD_METADADOS.get(chave, {"label": chave, "imagem": None})
        self._imagem_tk = None  # precisa manter referência viva
        self.configure(padx=10, pady=10, highlightbackground=COR_BORDA,
                        highlightthickness=1)
        # --- Coluna da imagem -------------------------------------------------
        frame_imagem = tk.Frame(self, bg=bg, width=self.TAMANHO_IMAGEM[0],
                                 height=self.TAMANHO_IMAGEM[1])
        frame_imagem.pack(side="left", padx=(0, 14))
        frame_imagem.pack_propagate(False)
        self._carregar_imagem(frame_imagem, meta.get("imagem"))
        # --- Coluna de informações e campos ------------------------------------
        frame_info = tk.Frame(self, bg=bg)
        frame_info.pack(side="left", fill="both", expand=True)
        tk.Label(frame_info, text=meta.get("label", chave), bg=bg, fg=COR_TEXTO,
                 font=("Segoe UI", 10, "bold"), anchor="w").pack(anchor="w")
        explicacao = meta.get("explicacao")
        if explicacao:
            tk.Label(frame_info, text=explicacao, bg=bg, fg=COR_AVISO,
                     font=("Segoe UI", 9), anchor="w", justify="left",
                     wraplength=520).pack(anchor="w", pady=(4, 0))
        linha_campos = tk.Frame(frame_info, bg=bg)
        linha_campos.pack(anchor="w", pady=(8, 4))
        tk.Label(linha_campos, text="X:", bg=bg, fg=COR_TEXTO_SECUNDARIO,
                 font=("Segoe UI", 9)).pack(side="left")
        self.var_x = tk.StringVar(value=str(valor_atual[0]))
        ttk.Entry(linha_campos, textvariable=self.var_x, width=6,
                  font=("Segoe UI", 9)).pack(side="left", padx=(4, 12))
        tk.Label(linha_campos, text="Y:", bg=bg, fg=COR_TEXTO_SECUNDARIO,
                 font=("Segoe UI", 9)).pack(side="left")
        self.var_y = tk.StringVar(value=str(valor_atual[1]))
        ttk.Entry(linha_campos, textvariable=self.var_y, width=6,
                  font=("Segoe UI", 9)).pack(side="left", padx=(4, 12))
        self.btn_capturar = ttk.Button(linha_campos, text="\U0001f4cd Capturar (8s)",
                                        style="Aviso.TButton", command=self.iniciar_captura)
        self.btn_capturar.pack(side="left")
        self.label_status = tk.Label(frame_info, text="", bg=bg, fg=COR_TEXTO_SECUNDARIO,
                                      font=("Segoe UI", 9), anchor="w")
        self.label_status.pack(anchor="w", pady=(4, 0))
        self._contador = 0
    def _carregar_imagem(self, frame_imagem, caminho):
        if caminho and os.path.exists(caminho):
            try:
                img = Image.open(caminho)
                img.thumbnail(self.TAMANHO_IMAGEM)
                self._imagem_tk = ImageTk.PhotoImage(img)
                tk.Label(frame_imagem, image=self._imagem_tk, bg=frame_imagem["bg"]
                         ).pack(expand=True)
                return
            except Exception as e:
                print(f"[AVISO] Falha ao carregar imagem '{caminho}': {e}")
        # Sem imagem (arquivo ausente ou não configurado) -> placeholder
        texto = "Sem imagem\nde refer\u00eancia" if not caminho else "Imagem n\u00e3o\nencontrada"
        tk.Label(frame_imagem, text=texto, bg=frame_imagem["bg"], fg=COR_TEXTO_SECUNDARIO,
                 font=("Segoe UI", 9), justify="center").pack(expand=True)
    def obter_valor(self):
        try:
            x = int(float(self.var_x.get().strip()))
            y = int(float(self.var_y.get().strip()))
            return [x, y]
        except ValueError:
            return None
    # --------------------------------------------------------------------
    # Captura com contagem regressiva (não trava a interface: usa self.after)
    # --------------------------------------------------------------------
    def iniciar_captura(self):
        self._contador = 8
        self.btn_capturar.config(state="disabled")
        self._contagem_regressiva()
    def _contagem_regressiva(self):
        if self._contador > 0:
            self.label_status.config(
                text=f"\u23f1\ufe0f Posicione o mouse no local desejado... {self._contador}s",
                fg=COR_AVISO
            )
            self._contador -= 1
            self.after(1000, self._contagem_regressiva)
        else:
            x, y = pyautogui.position()
            self.var_x.set(str(x))
            self.var_y.set(str(y))
            self.label_status.config(text=f"\u2705 Coordenada capturada: x={x}, y={y}",
                                      fg=COR_SUCESSO)
            self.btn_capturar.config(state="normal")
            self._mostrar_popup_resultado(x, y)
    def _mostrar_popup_resultado(self, x, y):
        popup = tk.Toplevel(self)
        popup.title("Coordenada capturada")
        popup.configure(bg=COR_FUNDO)
        popup.geometry("360x160")
        popup.resizable(False, False)
        popup.attributes("-topmost", True)
        meta = COORD_METADADOS.get(self.chave, {"label": self.chave})
        tk.Label(popup, text=f"Coordenada de \"{meta.get('label', self.chave)}\" capturada:",
                 bg=COR_FUNDO, fg=COR_TEXTO, font=("Segoe UI", 10, "bold"),
                 wraplength=320, justify="left").pack(padx=16, pady=(16, 6), anchor="w")
        texto_coord = f"x = {x}    y = {y}"
        tk.Label(popup, text=texto_coord, bg=COR_FUNDO_PAINEL_2, fg=COR_SUCESSO,
                 font=("Consolas", 14, "bold"), pady=10).pack(fill="x", padx=16)
        rodape = tk.Frame(popup, bg=COR_FUNDO)
        rodape.pack(fill="x", padx=16, pady=16)
        def copiar():
            popup.clipboard_clear()
            popup.clipboard_append(f"{x}, {y}")
            btn_copiar.config(text="Copiado \u2713")
            popup.after(1200, lambda: btn_copiar.config(text="Copiar coordenadas"))
        btn_copiar = ttk.Button(rodape, text="Copiar coordenadas", style="Primario.TButton",
                                 command=copiar)
        btn_copiar.pack(side="left")
        ttk.Button(rodape, text="Fechar", style="Secundario.TButton",
                   command=popup.destroy).pack(side="right")
# ==============================================================================
# JANELA: Configurar coordenadas DE UM POLO ESPECÍFICO
# ==============================================================================
class JanelaCoordenadas(tk.Toplevel):
    def __init__(self, master, polo, ao_salvar=None):
        super().__init__(master)
        self.master_janela = master
        self.polo = polo
        self.ao_salvar = ao_salvar  # callback opcional (usado ao criar polo novo)
        self.title(f"Coordenadas do polo — {polo['nome']}")
        self.configure(bg=COR_FUNDO)
        self.geometry("980x760")
        self.minsize(760, 520)
        tk.Label(self, text=f"Coordenadas do polo: {polo['nome']}",
                 bg=COR_FUNDO, fg=COR_TEXTO, font=("Segoe UI", 12, "bold")
                 ).pack(anchor="w", padx=16, pady=(16, 2))
        tk.Label(self,
                 text=("Para cada ponto abaixo, você pode digitar X e Y manualmente ou clicar em "
                       "\"Capturar (8s)\": você terá 8 segundos para posicionar o mouse no lugar "
                       "certo da tela (olhando a imagem de refer\u00eancia, se houver) antes da "
                       "coordenada ser lida automaticamente. Os pontos abaixo estão na mesma "
                       "ordem em que são usados durante a automação — o campo Nome é sempre "
                       "o primeiro clique."),
                 bg=COR_FUNDO, fg=COR_TEXTO_SECUNDARIO, font=("Segoe UI", 9), wraplength=940,
                 justify="left").pack(anchor="w", padx=16, pady=(0, 12))
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=16, pady=(0, 4))
        canvas = tk.Canvas(container, borderwidth=0, bg=COR_FUNDO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        frame_lista = ttk.Frame(canvas, style="Painel.TFrame")
        frame_lista.bind("<Configure>",
                          lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame_lista, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        # A ordem das chaves em FLUXO_COORDENADAS já reflete a ordem exata
        # em que cada coordenada é usada dentro do código da automação
        # (campo Nome primeiro, depois Sexo, CEP, etc.).
        chaves_deste_fluxo = FLUXO_COORDENADAS.get(polo["fluxo"], [])
        coords_atuais = polo.get("coordenadas") or copia_coordenadas_padrao(polo["fluxo"])
        self.linhas = []  # lista de LinhaCoordenada
        for idx, chave in enumerate(chaves_deste_fluxo):
            cor_linha = COR_FUNDO_PAINEL if idx % 2 == 0 else COR_FUNDO_PAINEL_2
            valor_atual = coords_atuais.get(chave, [0, 0])
            linha = LinhaCoordenada(frame_lista, chave, valor_atual, cor_linha)
            linha.pack(fill="x", pady=(0, 8))
            self.linhas.append(linha)
        rodape = ttk.Frame(self)
        rodape.pack(fill="x", padx=16, pady=12)
        ttk.Button(rodape, text="Salvar coordenadas", style="Primario.TButton",
                   command=self.salvar).pack(side="right")
        ttk.Button(rodape, text="Fechar sem salvar", style="Secundario.TButton",
                   command=self.destroy).pack(side="right", padx=(0, 8))
    def salvar(self):
        novas_coords = dict(self.polo.get("coordenadas") or {})
        erros = []
        for linha in self.linhas:
            valor = linha.obter_valor()
            if valor is None:
                meta = COORD_METADADOS.get(linha.chave, {"label": linha.chave})
                erros.append(meta.get("label", linha.chave))
                continue
            novas_coords[linha.chave] = valor
        if erros:
            messagebox.showwarning(
                "Valores inválidos",
                "Estas coordenadas têm X ou Y inválido e não foram salvas:\n\n"
                + "\n".join(erros)
            )
        self.polo["coordenadas"] = novas_coords
        salvar_config_polos()
        if self.ao_salvar:
            self.ao_salvar()
        messagebox.showinfo("Salvo", "Coordenadas do polo atualizadas com sucesso.")
        self.destroy()
# ==============================================================================
# JANELA: Editor de cursos DE UM POLO ESPECÍFICO
# ==============================================================================
class JanelaEditarCursos(tk.Toplevel):
    def __init__(self, master, polo):
        super().__init__(master)
        self.master_janela = master
        self.polo = polo
        self.title(f"Cursos do polo — {polo['nome']}")
        self.configure(bg=COR_FUNDO)
        self.geometry("1150x780")
        self.minsize(850, 520)
        aviso_frame = tk.Frame(self, bg=COR_FUNDO)
        aviso_frame.pack(fill="x", padx=16, pady=(16, 4))
        tk.Label(
            aviso_frame,
            text=f"Cursos do polo: {polo['nome']}",
            bg=COR_FUNDO, fg=COR_TEXTO, font=("Segoe UI", 11, "bold"), anchor="w"
        ).pack(anchor="w")
        tk.Label(
            aviso_frame,
            text=("Chaves: separe múltiplas chaves com  |  (barra vertical).\n"
                  "A CHAVE é o nome exatamente como aparece reconhecido na tela; "
                  "o TEXTO é o que será digitado no campo do curso."),
            bg=COR_FUNDO, fg=COR_TEXTO_SECUNDARIO, font=("Segoe UI", 9),
            justify="left", anchor="w"
        ).pack(anchor="w", pady=(4, 0))
        frame_add = ttk.LabelFrame(self, text="  ADICIONAR NOVO CURSO  ", padding=14)
        frame_add.pack(fill="x", padx=16, pady=(14, 6))
        linha_add = tk.Frame(frame_add, bg=COR_FUNDO_PAINEL)
        linha_add.pack(fill="x")
        tk.Label(linha_add, text="Chave (nome reconhecido na tela):",
                 bg=COR_FUNDO_PAINEL, fg=COR_TEXTO, font=("Segoe UI", 9)
                 ).grid(row=0, column=0, sticky="w", padx=(0, 6), pady=(0, 3))
        self.var_nova_chave = tk.StringVar()
        ttk.Entry(linha_add, textvariable=self.var_nova_chave, font=("Segoe UI", 10)
                  ).grid(row=1, column=0, sticky="ew", padx=(0, 10), ipady=3)
        tk.Label(linha_add, text="Curso (texto que será digitado):",
                 bg=COR_FUNDO_PAINEL, fg=COR_TEXTO, font=("Segoe UI", 9)
                 ).grid(row=0, column=1, sticky="w", padx=(0, 6), pady=(0, 3))
        self.var_novo_texto = tk.StringVar()
        ttk.Entry(linha_add, textvariable=self.var_novo_texto, font=("Segoe UI", 10)
                  ).grid(row=1, column=1, sticky="ew", padx=(0, 10), ipady=3)
        ttk.Button(linha_add, text="+ Adicionar curso", style="Sucesso.TButton",
                   command=self.adicionar_curso).grid(row=1, column=2, sticky="e")
        linha_add.columnconfigure(0, weight=1)
        linha_add.columnconfigure(1, weight=2)
        tk.Label(frame_add,
                 text=("Dica: se o curso tiver mais de um nome possível na tela, separe "
                       "com  |  (ex: MARKETING DIGITAL | MARKETING)."),
                 bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_SECUNDARIO, font=("Segoe UI", 8)
                 ).pack(anchor="w", pady=(8, 0))
        tk.Label(self, text="CURSOS CONFIGURADOS NESTE POLO", bg=COR_FUNDO, fg=COR_DESTAQUE,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(14, 4))
        col_frame = tk.Frame(self, bg=COR_BORDA)
        col_frame.pack(fill="x", padx=16, pady=(0, 0))
        tk.Label(col_frame, text="  Chaves de reconhecimento (separadas por  |  )",
                 bg=COR_BORDA, fg=COR_TEXTO, font=("Segoe UI", 9, "bold"),
                 width=40, anchor="w").pack(side="left", ipady=4)
        tk.Label(col_frame, text="  Texto digitado (pyautogui.write(...))",
                 bg=COR_BORDA, fg=COR_TEXTO, font=("Segoe UI", 9, "bold"),
                 anchor="w").pack(side="left", fill="x", expand=True, ipady=4)
        tk.Label(col_frame, text="  ", bg=COR_BORDA, width=10).pack(side="left", ipady=4)
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=16, pady=(0, 4))
        canvas = tk.Canvas(container, borderwidth=0, bg=COR_FUNDO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.frame_lista = ttk.Frame(canvas, style="Painel.TFrame")
        self.frame_lista.bind("<Configure>",
                               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.frame_lista, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.entradas = []
        self._popular_lista_cursos()
        rodape = ttk.Frame(self)
        rodape.pack(fill="x", padx=16, pady=12)
        ttk.Button(rodape, text="Salvar alterações", style="Primario.TButton",
                   command=self.salvar).pack(side="right")
        ttk.Button(rodape, text="Fechar sem salvar", style="Secundario.TButton",
                   command=self.destroy).pack(side="right", padx=(0, 8))
        tk.Label(rodape, text="Dica: chaves em branco serão ignoradas ao salvar.",
                 bg=COR_FUNDO, fg=COR_TEXTO_SECUNDARIO, font=("Segoe UI", 9)).pack(side="left")
    def _popular_lista_cursos(self):
        for widget in self.frame_lista.winfo_children():
            widget.destroy()
        self.entradas = []
        for idx, item in enumerate(self.polo["cursos"]):
            chaves_str = " | ".join(item["chaves"])
            cor_linha = COR_FUNDO_PAINEL if idx % 2 == 0 else COR_FUNDO_PAINEL_2
            linha = tk.Frame(self.frame_lista, bg=cor_linha)
            linha.pack(fill="x", pady=1, padx=0)
            tk.Label(linha, text=f"{idx + 1:2d}.", width=3,
                     bg=cor_linha, fg=COR_TEXTO_SECUNDARIO,
                     font=("Segoe UI", 9)).pack(side="left", padx=(6, 0), pady=6)
            var_chaves = tk.StringVar(value=chaves_str)
            ttk.Entry(linha, textvariable=var_chaves, font=("Segoe UI", 9), width=38
                      ).pack(side="left", padx=(4, 6), pady=6)
            tk.Label(linha, text="→", bg=cor_linha, fg=COR_DESTAQUE,
                     font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 6))
            var_texto = tk.StringVar(value=item["texto"])
            ttk.Entry(linha, textvariable=var_texto, font=("Segoe UI", 9)
                      ).pack(side="left", fill="x", expand=True, padx=(0, 6), pady=6)
            ttk.Button(linha, text="🗑 Excluir", style="PerigoPequeno.TButton",
                       command=lambda item=item: self.excluir_curso(item)
                       ).pack(side="left", padx=(0, 10), pady=6)
            self.entradas.append((var_chaves, var_texto, item))
    def adicionar_curso(self):
        chave_raw = self.var_nova_chave.get().strip()
        texto_raw = self.var_novo_texto.get().strip()
        if not chave_raw or not texto_raw:
            messagebox.showwarning("Campos obrigatórios",
                                    "Preencha a Chave e o Curso (texto) antes de adicionar.")
            return
        novas_chaves = [c.strip() for c in chave_raw.split("|") if c.strip()]
        if not novas_chaves:
            messagebox.showwarning("Chave inválida", "A chave não pode estar vazia.")
            return
        chaves_existentes = set()
        for item in self.polo["cursos"]:
            for c in item["chaves"]:
                chaves_existentes.add(c.strip().upper())
        conflitos = [c for c in novas_chaves if c.upper() in chaves_existentes]
        if conflitos:
            prosseguir = messagebox.askyesno(
                "Chave já existe",
                "A(s) chave(s) abaixo já estão cadastradas em outro curso deste polo:\n\n"
                + ", ".join(conflitos) +
                "\n\nComo a lista é percorrida em ordem, o curso mais acima "
                "sempre vence. Deseja adicionar mesmo assim?"
            )
            if not prosseguir:
                return
        self.polo["cursos"].append({"chaves": novas_chaves, "texto": texto_raw})
        salvar_config_polos()
        self.var_nova_chave.set("")
        self.var_novo_texto.set("")
        self._popular_lista_cursos()
        if hasattr(self.master_janela, "atualizar_contador_cursos"):
            self.master_janela.atualizar_contador_cursos()
        messagebox.showinfo("Curso adicionado",
                             f"Curso adicionado com sucesso!\n\nChave(s): {', '.join(novas_chaves)}\n"
                             f"Texto: {texto_raw}")
    def excluir_curso(self, item):
        chaves_str = " | ".join(item["chaves"])
        confirmar = messagebox.askyesno(
            "Excluir curso",
            f"Tem certeza que deseja excluir este curso do polo {self.polo['nome']}?\n\n"
            f"Chave(s): {chaves_str}\nTexto: {item['texto']}\n\nEssa ação não pode ser desfeita."
        )
        if not confirmar:
            return
        if item in self.polo["cursos"]:
            self.polo["cursos"].remove(item)
            salvar_config_polos()
            self._popular_lista_cursos()
            if hasattr(self.master_janela, "atualizar_contador_cursos"):
                self.master_janela.atualizar_contador_cursos()
            self.master_janela.log(f"Curso excluído ({self.polo['nome']}): {chaves_str}")
    def salvar(self):
        erros = []
        for var_chaves, var_texto, item in self.entradas:
            chaves_raw = var_chaves.get().strip()
            texto_raw = var_texto.get().strip()
            novas_chaves = [c.strip() for c in chaves_raw.split("|") if c.strip()]
            if not novas_chaves:
                erros.append(f"Curso com texto '{item['texto']}': chave não pode ficar vazia.")
                continue
            item["chaves"] = novas_chaves
            item["texto"] = texto_raw
        if erros:
            messagebox.showwarning("Atenção", "Algumas linhas não foram salvas:\n\n" + "\n".join(erros))
        salvar_config_polos()
        if hasattr(self.master_janela, "atualizar_contador_cursos"):
            self.master_janela.atualizar_contador_cursos()
        messagebox.showinfo("Salvo", "Chaves e textos dos cursos foram atualizados com sucesso.")
        self.destroy()
# ==============================================================================
# JANELA: Gerenciar POLOS (adicionar, editar evento/texto, excluir, coordenadas)
# ==============================================================================
class JanelaPolos(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master_janela = master
        self.title("Gerenciar polos")
        self.configure(bg=COR_FUNDO)
        self.geometry("1080x720")
        self.minsize(800, 480)
        tk.Label(self, text="Gerenciar polos",
                 bg=COR_FUNDO, fg=COR_TEXTO, font=("Segoe UI", 13, "bold")
                 ).pack(anchor="w", padx=16, pady=(16, 2))
        tk.Label(self,
                 text=("Cada polo tem seu próprio EVENTO, texto de POLO, lista de cursos e "
                       "COORDENADAS de clique, digitados/usados na automação."),
                 bg=COR_FUNDO, fg=COR_TEXTO_SECUNDARIO, font=("Segoe UI", 9)
                 ).pack(anchor="w", padx=16, pady=(0, 10))
        # ------------------------------------------------------------
        # BLOCO: Adicionar novo polo
        # ------------------------------------------------------------
        frame_add = ttk.LabelFrame(self, text="  ADICIONAR NOVO POLO  ", padding=14)
        frame_add.pack(fill="x", padx=16, pady=(0, 10))
        grade = tk.Frame(frame_add, bg=COR_FUNDO_PAINEL)
        grade.pack(fill="x")
        tk.Label(grade, text="Nome do polo (ex: MG - Belo Horizonte):",
                 bg=COR_FUNDO_PAINEL, fg=COR_TEXTO, font=("Segoe UI", 9)
                 ).grid(row=0, column=0, sticky="w", padx=(0, 6), pady=(0, 3))
        self.var_nome = tk.StringVar()
        ttk.Entry(grade, textvariable=self.var_nome, font=("Segoe UI", 10)
                  ).grid(row=1, column=0, sticky="ew", padx=(0, 10), ipady=3)
        tk.Label(grade, text="Texto do EVENTO:",
                 bg=COR_FUNDO_PAINEL, fg=COR_TEXTO, font=("Segoe UI", 9)
                 ).grid(row=0, column=1, sticky="w", padx=(0, 6), pady=(0, 3))
        self.var_evento = tk.StringVar(value="11 - Movimenta.Rio: A\u00e7\u00e3o Externa")
        ttk.Entry(grade, textvariable=self.var_evento, font=("Segoe UI", 10)
                  ).grid(row=1, column=1, sticky="ew", padx=(0, 10), ipady=3)
        tk.Label(grade, text="Texto do POLO (Parte 3):",
                 bg=COR_FUNDO_PAINEL, fg=COR_TEXTO, font=("Segoe UI", 9)
                 ).grid(row=2, column=0, sticky="w", padx=(0, 6), pady=(8, 3))
        self.var_polo_texto = tk.StringVar()
        ttk.Entry(grade, textvariable=self.var_polo_texto, font=("Segoe UI", 10)
                  ).grid(row=3, column=0, sticky="ew", padx=(0, 10), ipady=3)
        tk.Label(grade, text="Modelo de fluxo (cliques/teclas + coordenadas iniciais):",
                 bg=COR_FUNDO_PAINEL, fg=COR_TEXTO, font=("Segoe UI", 9)
                 ).grid(row=2, column=1, sticky="w", padx=(0, 6), pady=(8, 3))
        self.var_fluxo = tk.StringVar(value="Baseado no RJ - Movimenta.Rio")
        combo_fluxo = ttk.Combobox(
            grade, textvariable=self.var_fluxo, state="readonly", font=("Segoe UI", 10),
            values=["Baseado no RJ - Movimenta.Rio", "Baseado no CE - Fortaleza"]
        )
        combo_fluxo.grid(row=3, column=1, sticky="ew", padx=(0, 10), ipady=3)
        grade.columnconfigure(0, weight=1)
        grade.columnconfigure(1, weight=1)
        ttk.Button(frame_add, text="+ Adicionar polo", style="Sucesso.TButton",
                   command=self.adicionar_polo).pack(anchor="e", pady=(10, 0))
        tk.Label(frame_add,
                 text=("Dica: após adicionar, a tela de coordenadas desse novo polo abre "
                       "automaticamente para você ajustar os pontos de clique (o modelo "
                       "escolhido só define os valores iniciais)."),
                 bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_SECUNDARIO, font=("Segoe UI", 8), wraplength=1000,
                 justify="left").pack(anchor="w", pady=(6, 0))
        # ------------------------------------------------------------
        # Lista de polos existentes
        # ------------------------------------------------------------
        tk.Label(self, text="POLOS CADASTRADOS", bg=COR_FUNDO, fg=COR_DESTAQUE,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(6, 4))
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=16, pady=(0, 4))
        canvas = tk.Canvas(container, borderwidth=0, bg=COR_FUNDO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.frame_lista = ttk.Frame(canvas, style="Painel.TFrame")
        self.frame_lista.bind("<Configure>",
                               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.frame_lista, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.entradas_polos = []
        self._popular_lista_polos()
        rodape = ttk.Frame(self)
        rodape.pack(fill="x", padx=16, pady=12)
        ttk.Button(rodape, text="Salvar alterações", style="Primario.TButton",
                   command=self.salvar).pack(side="right")
        ttk.Button(rodape, text="Fechar sem salvar", style="Secundario.TButton",
                   command=self.destroy).pack(side="right", padx=(0, 8))
    def _popular_lista_polos(self):
        for widget in self.frame_lista.winfo_children():
            widget.destroy()
        self.entradas_polos = []
        for idx, polo in enumerate(POLOS):
            cor_linha = COR_FUNDO_PAINEL if idx % 2 == 0 else COR_FUNDO_PAINEL_2
            bloco = tk.Frame(self.frame_lista, bg=cor_linha)
            bloco.pack(fill="x", pady=2, padx=0)
            linha1 = tk.Frame(bloco, bg=cor_linha)
            linha1.pack(fill="x", padx=8, pady=(8, 2))
            tk.Label(linha1, text="Nome:", bg=cor_linha, fg=COR_TEXTO_SECUNDARIO,
                     font=("Segoe UI", 8), width=10, anchor="w").pack(side="left")
            var_nome = tk.StringVar(value=polo["nome"])
            ttk.Entry(linha1, textvariable=var_nome, font=("Segoe UI", 9), width=26
                      ).pack(side="left", padx=(0, 10))
            tk.Label(linha1, text=f"Modelo: {'Fortaleza' if polo['fluxo'] == 'fortaleza' else 'RJ'}"
                                   f"  |  {len(polo['cursos'])} cursos",
                     bg=cor_linha, fg=COR_TEXTO_SECUNDARIO, font=("Segoe UI", 8)
                     ).pack(side="left", padx=(0, 10))
            ttk.Button(linha1, text="\U0001f4cd Coordenadas", style="Secundario.TButton",
                       command=lambda polo=polo: self.abrir_coordenadas(polo)
                       ).pack(side="right", padx=(6, 0))
            ttk.Button(linha1, text="🗑 Excluir polo", style="PerigoPequeno.TButton",
                       command=lambda polo=polo: self.excluir_polo(polo)
                       ).pack(side="right")
            linha2 = tk.Frame(bloco, bg=cor_linha)
            linha2.pack(fill="x", padx=8, pady=(2, 8))
            tk.Label(linha2, text="Evento:", bg=cor_linha, fg=COR_TEXTO_SECUNDARIO,
                     font=("Segoe UI", 8), width=10, anchor="w").pack(side="left")
            var_evento = tk.StringVar(value=polo["evento"])
            ttk.Entry(linha2, textvariable=var_evento, font=("Segoe UI", 9)
                      ).pack(side="left", fill="x", expand=True, padx=(0, 12))
            linha3 = tk.Frame(bloco, bg=cor_linha)
            linha3.pack(fill="x", padx=8, pady=(0, 8))
            tk.Label(linha3, text="Texto do polo:", bg=cor_linha, fg=COR_TEXTO_SECUNDARIO,
                     font=("Segoe UI", 8), width=10, anchor="w").pack(side="left")
            var_polo_texto = tk.StringVar(value=polo["polo_texto"])
            ttk.Entry(linha3, textvariable=var_polo_texto, font=("Segoe UI", 9)
                      ).pack(side="left", fill="x", expand=True, padx=(0, 12))
            self.entradas_polos.append((var_nome, var_evento, var_polo_texto, polo))
    def abrir_coordenadas(self, polo):
        JanelaCoordenadas(self, polo)
    def adicionar_polo(self):
        nome = self.var_nome.get().strip()
        evento = self.var_evento.get().strip()
        polo_texto = self.var_polo_texto.get().strip()
        fluxo = "fortaleza" if "Fortaleza" in self.var_fluxo.get() else "rj"
        if not nome or not evento or not polo_texto:
            messagebox.showwarning("Campos obrigatórios",
                                    "Preencha o nome do polo, o evento e o texto do polo.")
            return
        if any(p["nome"].strip().upper() == nome.upper() for p in POLOS):
            messagebox.showwarning("Polo já existe", "Já existe um polo com esse nome.")
            return
        cursos_base = CURSOS_CE_PADRAO if fluxo == "fortaleza" else CURSOS_RJ_PADRAO
        cursos_copia = [{"chaves": list(item["chaves"]), "texto": item["texto"]}
                         for item in cursos_base]
        novo_polo = {
            "id": novo_id(),
            "nome": nome,
            "evento": evento,
            "polo_texto": polo_texto,
            "fluxo": fluxo,
            "cursos": cursos_copia,
            "coordenadas": copia_coordenadas_padrao(fluxo),
        }
        POLOS.append(novo_polo)
        salvar_config_polos()
        self.var_nome.set("")
        self.var_polo_texto.set("")
        self._popular_lista_polos()
        if hasattr(self.master_janela, "atualizar_lista_polos"):
            self.master_janela.atualizar_lista_polos()
        messagebox.showinfo("Polo adicionado",
                             f"Polo '{nome}' adicionado com sucesso!\n\n"
                             f"Agora ajuste as coordenadas de clique desse polo.")
        # Abre automaticamente a tela de coordenadas do polo recém-criado
        JanelaCoordenadas(self, novo_polo, ao_salvar=self._popular_lista_polos)
    def excluir_polo(self, polo):
        if len(POLOS) <= 1:
            messagebox.showwarning("Não é possível excluir",
                                    "Precisa existir pelo menos 1 polo cadastrado.")
            return
        if controle.rodando:
            messagebox.showwarning("Automação em execução",
                                    "Encerre a automação antes de excluir um polo.")
            return
        confirmar = messagebox.askyesno(
            "Excluir polo",
            f"Tem certeza que deseja excluir o polo '{polo['nome']}'?\n\n"
            f"Todos os cursos e coordenadas cadastrados nele também serão excluídos.\n"
            f"Essa ação não pode ser desfeita."
        )
        if not confirmar:
            return
        if polo in POLOS:
            POLOS.remove(polo)
            salvar_config_polos()
            self._popular_lista_polos()
            if hasattr(self.master_janela, "atualizar_lista_polos"):
                self.master_janela.atualizar_lista_polos()
            self.master_janela.log(f"Polo excluído: {polo['nome']}")
    def salvar(self):
        nomes_vistos = set()
        erros = []
        for var_nome, var_evento, var_polo_texto, polo in self.entradas_polos:
            nome = var_nome.get().strip()
            evento = var_evento.get().strip()
            polo_texto = var_polo_texto.get().strip()
            if not nome or not evento or not polo_texto:
                erros.append(f"Polo '{polo['nome']}': nome, evento e texto do polo não podem ficar vazios.")
                continue
            if nome.upper() in nomes_vistos:
                erros.append(f"Nome duplicado: '{nome}'.")
                continue
            nomes_vistos.add(nome.upper())
            polo["nome"] = nome
            polo["evento"] = evento
            polo["polo_texto"] = polo_texto
        if erros:
            messagebox.showwarning("Atenção", "Algumas alterações não foram salvas:\n\n" + "\n".join(erros))
        salvar_config_polos()
        if hasattr(self.master_janela, "atualizar_lista_polos"):
            self.master_janela.atualizar_lista_polos()
        messagebox.showinfo("Salvo", "Polos atualizados com sucesso.")
        self.destroy()
# ==============================================================================
# JANELA PRINCIPAL
# ==============================================================================
class JanelaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Automa\u00e7\u00e3o Multi-Polo")
        configurar_estilo(self)
        try:
            self.state("zoomed")
        except tk.TclError:
            largura = self.winfo_screenwidth()
            altura = self.winfo_screenheight()
            self.geometry(f"{largura}x{altura}+0+0")
        self._tela_cheia_total = False
        self.bind("<F11>", self.alternar_tela_cheia_total)
        self.bind("<Escape>", self.sair_tela_cheia_total)
        carregar_config_polos()
        wrapper = tk.Frame(self, bg=COR_FUNDO)
        wrapper.pack(fill="both", expand=True)
        area = ttk.Frame(wrapper, padding=(40, 30))
        area.pack(fill="both", expand=True)
        cabecalho = tk.Frame(area, bg=COR_FUNDO)
        cabecalho.pack(fill="x", pady=(0, 25))
        ttk.Label(cabecalho, text="Automa\u00e7\u00e3o de Cadastro \u2014 Multi-Polo",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(cabecalho,
                  text="Escolha o polo, controle a execu\u00e7\u00e3o e configure cursos/coordenadas por polo",
                  style="Subtitulo.TLabel").pack(anchor="w", pady=(4, 0))
        frame_polo = ttk.LabelFrame(area, text="  POLO  ", padding=16)
        frame_polo.pack(fill="x", pady=(0, 20))
        linha_polo = tk.Frame(frame_polo, bg=COR_FUNDO_PAINEL)
        linha_polo.pack(fill="x")
        self.var_polo_selecionado = tk.StringVar()
        self.combo_polo = ttk.Combobox(linha_polo, textvariable=self.var_polo_selecionado,
                                        state="readonly", font=("Segoe UI", 11), width=28)
        self.combo_polo.pack(side="left", padx=(0, 10), ipady=3)
        self.combo_polo.bind("<<ComboboxSelected>>", lambda e: self.atualizar_contador_cursos())
        ttk.Button(linha_polo, text="Gerenciar polos", style="Secundario.TButton",
                   command=self.abrir_gerenciar_polos).pack(side="left", padx=(0, 8))
        ttk.Button(linha_polo, text="\U0001f4cd Coordenadas deste polo", style="Secundario.TButton",
                   command=self.abrir_coordenadas_polo_atual).pack(side="left")
        self.label_info_polo = ttk.Label(frame_polo, text="", style="Secundario.TLabel")
        self.label_info_polo.pack(anchor="w", pady=(10, 0))
        linha_topo = tk.Frame(area, bg=COR_FUNDO)
        linha_topo.pack(fill="x", pady=(0, 20))
        frame_velocidade = ttk.LabelFrame(linha_topo, text="  VELOCIDADE  ", padding=16)
        frame_velocidade.pack(side="left", fill="both", expand=True, padx=(0, 10))
        linha_vel = tk.Frame(frame_velocidade, bg=COR_FUNDO_PAINEL)
        linha_vel.pack(fill="x")
        self.var_velocidade = tk.StringVar(value=str(controle.velocidade))
        ttk.Entry(linha_vel, textvariable=self.var_velocidade,
                  width=8, font=("Segoe UI", 11)).pack(side="left", padx=(0, 10), ipady=3)
        ttk.Button(linha_vel, text="Aplicar", style="Primario.TButton",
                   command=self.aplicar_velocidade).pack(side="left")
        ttk.Label(frame_velocidade,
                  text="Multiplicador usado em todos os tempos de espera (time.sleep)",
                  style="Secundario.TLabel").pack(anchor="w", pady=(10, 0))
        frame_controle = ttk.LabelFrame(linha_topo, text="  CONTROLE  ", padding=16)
        frame_controle.pack(side="left", fill="both", expand=True, padx=(10, 0))
        linha_botoes = tk.Frame(frame_controle, bg=COR_FUNDO_PAINEL)
        linha_botoes.pack(fill="x")
        self.btn_iniciar = ttk.Button(linha_botoes, text="\u25b6  Iniciar",
                                       style="Primario.TButton",
                                       command=self.iniciar_automacao)
        self.btn_iniciar.pack(side="left", padx=(0, 10))
        self.btn_encerrar = ttk.Button(linha_botoes, text="\u25a0  Encerrar",
                                        style="Perigo.TButton",
                                        command=self.encerrar_automacao, state="disabled")
        self.btn_encerrar.pack(side="left")
        self.label_estado = ttk.Label(frame_controle, text="\u25cf  Parado",
                                       style="Secundario.TLabel")
        self.label_estado.pack(anchor="w", pady=(12, 0))
        frame_cursos = ttk.LabelFrame(area, text="  CONFIGURA\u00c7\u00c3O DE CURSOS DO POLO  ", padding=16)
        frame_cursos.pack(fill="x", pady=(0, 20))
        linha_cursos = tk.Frame(frame_cursos, bg=COR_FUNDO_PAINEL)
        linha_cursos.pack(fill="x")
        ttk.Button(linha_cursos, text="Adicionar / Editar / Excluir cursos",
                   style="Secundario.TButton",
                   command=self.abrir_editor_cursos).pack(side="left")
        self.label_contador_cursos = ttk.Label(frame_cursos, text="", style="Secundario.TLabel")
        self.label_contador_cursos.pack(anchor="w", pady=(10, 0))
        # Só agora todos os widgets necessários já existem, então é seguro
        # popular a lista de polos e atualizar os contadores/labels.
        self.atualizar_lista_polos()
        frame_status = ttk.LabelFrame(area, text="  STATUS  ", padding=10)
        frame_status.pack(fill="both", expand=True)
        self.texto_status = tk.Text(
            frame_status, state="disabled", wrap="word",
            bg=COR_FUNDO_PAINEL_2, fg=COR_TEXTO, insertbackground=COR_TEXTO,
            relief="flat", font=("Consolas", 10), padx=10, pady=10,
            borderwidth=0, highlightthickness=1,
            highlightbackground=COR_BORDA, highlightcolor=COR_DESTAQUE
        )
        self.texto_status.pack(fill="both", expand=True, side="left")
        scroll_status = ttk.Scrollbar(frame_status, command=self.texto_status.yview)
        scroll_status.pack(side="right", fill="y")
        self.texto_status.configure(yscrollcommand=scroll_status.set)
        self.protocol("WM_DELETE_WINDOW", self.ao_fechar)
    def alternar_tela_cheia_total(self, event=None):
        self._tela_cheia_total = not self._tela_cheia_total
        self.attributes("-fullscreen", self._tela_cheia_total)
    def sair_tela_cheia_total(self, event=None):
        if self._tela_cheia_total:
            self._tela_cheia_total = False
            self.attributes("-fullscreen", False)
            try:
                self.state("zoomed")
            except tk.TclError:
                pass
    def obter_polo_selecionado(self):
        nome = self.var_polo_selecionado.get()
        for p in POLOS:
            if p["nome"] == nome:
                return p
        return POLOS[0] if POLOS else None
    def atualizar_lista_polos(self):
        nome_atual = self.var_polo_selecionado.get()
        nomes = [p["nome"] for p in POLOS]
        self.combo_polo["values"] = nomes
        if nome_atual in nomes:
            self.var_polo_selecionado.set(nome_atual)
        elif nomes:
            self.var_polo_selecionado.set(nomes[0])
        self.label_info_polo.config(
            text=f"{len(POLOS)} polo(s) cadastrado(s). O EVENTO, o texto do POLO e as "
                 f"COORDENADAS de clique usados na automação vêm do polo selecionado acima."
        )
        self.atualizar_contador_cursos()
    def atualizar_contador_cursos(self):
        polo = self.obter_polo_selecionado()
        if polo:
            self.label_contador_cursos.config(
                text=(f"{len(polo['cursos'])} cursos configurados no polo \"{polo['nome']}\"  \u2014  "
                      "Adicione, edite ou exclua cursos.")
            )
    def abrir_gerenciar_polos(self):
        JanelaPolos(self)
    def abrir_editor_cursos(self):
        polo = self.obter_polo_selecionado()
        if not polo:
            messagebox.showwarning("Nenhum polo", "Cadastre pelo menos um polo primeiro.")
            return
        JanelaEditarCursos(self, polo)
    def abrir_coordenadas_polo_atual(self):
        polo = self.obter_polo_selecionado()
        if not polo:
            messagebox.showwarning("Nenhum polo", "Cadastre pelo menos um polo primeiro.")
            return
        JanelaCoordenadas(self, polo)
    def aplicar_velocidade(self):
        try:
            novo_valor = float(self.var_velocidade.get().replace(",", "."))
            if novo_valor < 0:
                raise ValueError
            controle.velocidade = novo_valor
            self.log(f"Velocidade atualizada para: {novo_valor}")
        except ValueError:
            messagebox.showerror("Valor inv\u00e1lido", "Digite um n\u00famero v\u00e1lido (ex: 1, 0.5, 2).")
    def iniciar_automacao(self):
        if controle.rodando:
            messagebox.showinfo("J\u00e1 em execu\u00e7\u00e3o", "A automa\u00e7\u00e3o j\u00e1 est\u00e1 rodando.")
            return
        polo = self.obter_polo_selecionado()
        if not polo:
            messagebox.showwarning("Nenhum polo", "Cadastre e selecione um polo antes de iniciar.")
            return
        controle.evento_parar.clear()
        controle.rodando = True
        self.btn_iniciar.config(state="disabled")
        self.btn_encerrar.config(state="normal")
        self.label_estado.config(text="\u25cf  Em execu\u00e7\u00e3o")
        self.log(f"Automa\u00e7\u00e3o iniciada no polo: {polo['nome']}")
        controle.thread = threading.Thread(
            target=rodar_automacao,
            kwargs={
                "polo": polo,
                "callback_status": self.atualizar_status_registro,
                "callback_log": self.log,
            },
            daemon=True
        )
        controle.thread.start()
    def encerrar_automacao(self):
        if not controle.rodando:
            return
        controle.evento_parar.set()
        self.log("Solicitado encerramento...")
        self.btn_encerrar.config(state="disabled")
        self.label_estado.config(text="\u25cf  Encerrando...")
    def ao_fechar(self):
        if controle.rodando:
            resposta = messagebox.askyesno(
                "Automa\u00e7\u00e3o em execu\u00e7\u00e3o",
                "A automa\u00e7\u00e3o ainda est\u00e1 rodando. Deseja encerrá-la e fechar?"
            )
            if not resposta:
                return
            controle.evento_parar.set()
        self.destroy()
    def log(self, mensagem):
        def _escrever():
            self.texto_status.config(state="normal")
            self.texto_status.insert("end", mensagem + "\n")
            self.texto_status.see("end")
            self.texto_status.config(state="disabled")
        self.after(0, _escrever)
    def atualizar_status_registro(self, numero_registro):
        def _atualizar():
            if numero_registro is None:
                self.btn_iniciar.config(state="normal")
                self.btn_encerrar.config(state="disabled")
                self.label_estado.config(text="\u25cf  Parado")
                self.title("Automa\u00e7\u00e3o Multi-Polo")
                controle.rodando = False
            else:
                polo = self.obter_polo_selecionado()
                nome_polo = polo["nome"] if polo else ""
                self.title(f"Automa\u00e7\u00e3o Multi-Polo \u2014 {nome_polo} \u2014 Registro {numero_registro}")
                self.label_estado.config(
                    text=f"\u25cf  Em execu\u00e7\u00e3o \u2014 registro {numero_registro}")
        self.after(0, _atualizar)
# ==============================================================================
# PONTO DE ENTRADA
# ==============================================================================
if __name__ == "__main__":
    app = JanelaPrincipal()
    app.mainloop()