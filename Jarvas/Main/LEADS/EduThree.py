import numpy as np
from PIL import ImageGrab
import easyocr
import pyautogui
import pyperclip
import time
import re

# Inicialize o reader apenas uma vez
reader = easyocr.Reader(['pt'])  # Use só o idioma necessário

# Aguarda 5 segundos antes de começar
time.sleep(5)

def capturar_e_ler_tela():
    # Define a região (bbox): (left, top, right, bottom)
    largura_tela, altura_tela = ImageGrab.grab().size
    bbox = (0, 0, int(largura_tela * 0.4), int(altura_tela * 0.8))  # Ajuste a altura se quiser menos
    screenshot = ImageGrab.grab(bbox=bbox)
    img_np = np.array(screenshot)


for programa in range(100):
    # COPIA CPF   
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(1)
    pyperclip.paste() 
    time.sleep(1)
    pyautogui.hotkey('alt', 'tab')
    time.sleep(1)
    pyautogui.press('insert')
    time.sleep(1)
    pyautogui.press('tab')
    time.sleep(5)
    pyautogui.press('Enter')
    time.sleep(3)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1)   
    
    # EXTRA
    pyautogui.press('enter')
    time.sleep(1)
    pyautogui.hotkey('Ctrl', 'c')
    time.sleep(1)
    pyautogui.press('enter')    
    time.sleep(1)
    '''# DATA DE NASCIMENTO
    pyautogui.write('18/12/2000')''' 
    # BOTÃO SEXO 
    '''pyautogui.hotkey('alt', 'tab')
    time.sleep(1)
    pyautogui.press('right')
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(1)
    pyautogui.press('left')
    time.sleep(1)
    sexo = pyperclip.paste()
    pyautogui.hotkey('alt', 'tab')
    time.sleep(1)
    pyautogui.click(x=284, y=450)
    time.sleep(1)
    pyautogui.write(sexo)
    time.sleep(1)'''
    # BOTÃO CEP         
    pyautogui.click(x=45, y=567)
    time.sleep(1)
    pyautogui.hotkey('alt', 'tab')
    time.sleep(1)
    for r in range(4):
        pyautogui.press('right')
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(1)
    cep = pyperclip.paste()
    time.sleep(1)
    for l in range(4):
        pyautogui.press('left')
    time.sleep(1)
    pyautogui.hotkey('alt', 'tab')
    time.sleep(1)
    pyautogui.write(cep)
    time.sleep(1)
    # BOTÃO PROXIMO - 1
    pyautogui.click(x=890, y=802)
    time.sleep(2)
    pyautogui.press('tab')
    time.sleep(1)

    # TIPO DE CONTRATO
    pyautogui.hotkey('alt', 'tab')
    time.sleep(1)
    for i in range(9):
        pyautogui.press('right')
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(1)
    turma = pyperclip.paste()
    time.sleep(1)
    for i in range(9):
        pyautogui.press('left') 
    time.sleep(1)
    pyautogui.hotkey('alt', 'tab')      
    time.sleep(1)
    pyautogui.write(turma)
    time.sleep(1)
    pyautogui.press('tab')
    
    # CHROME
    pyautogui.hotkey('alt', 'tab')
    time.sleep(1)
    for i in range(4):
        pyautogui.press('left')
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(1)
    data_de_inscricao = pyperclip.paste()
    time.sleep(1)
    for i in range(4):
        pyautogui.press('right')
    time.sleep(1)

    # F10
    pyautogui.hotkey('alt', 'tab')              
    time.sleep(1)
    pyautogui.click(x=205, y=405)
    time.sleep(1)
    for i in range(8):
        pyautogui.press('backspace')
    pyautogui.write(data_de_inscricao)
    time.sleep(1)
    pyautogui.press('tab')
    pyautogui.press('tab')

    # EVENTO
    pyautogui.write("11 - Movimenta.Rio: Ação Externa")
    time.sleep(1)
    pyautogui.press('tab')  

    # CURSO
    '''for i in range(67):
        pyautogui.press('down')
    pyautogui.press('tab')
    '''
##########################################################################
    '''pyautogui.hotkey('alt', 'tab')
    time.sleep(1)
    for _ in range(2):
        pyautogui.press('right')
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(1)
    curso_copiado = pyperclip.paste()
    time.sleep(1)
    for _ in range(2): 
        pyautogui.press('left')
    time.sleep(1)
    pyautogui.hotkey('alt', 'tab')'''
    '''
    Auxiliar Administrativo
    Marketing Digital
    Cumim - Boteco
    Inteligência Artificial
    Garçom - Boteco
    Agente de Defesa Ambiental
    Social Midia
    Assistente de Logística
    Auxiliar de Cozinha - Boteco
    Governança ESG (Micro Certificado)
    UX/UI Designer
    Gerenciamento Tráfego Digital
    Camareiro
    Orientador de Hotelaria
    Pedreiro de Alvenaria Estrutural
    Aplicação de Revestimento Cerâmicos
    Instalador Hidráulico Predial
    Carpinteiro de Obras
    Eletricista Predial
    Serralheiro de Alumínio
    Recepcionista
    Agente de Turismo Corporativo
    Monitor de Lazer e Recreação
    Atendente de Salão para Café da Manhã 
    Benefício de Pescado para Venda
    Técnicas e Pesca Sustentável
    Ecoturismo e Gestão de Unidades
    Gestor de Resíduos Sólidos
    Operador de Sistema de Compostagem e Resíduos Orgânicos
    '''
    # CURSO ESCOLHIDO

    '''if curso_copiado == "ODONTO MÓVEL":'''
    pyautogui.write("Odonto Movel: Presencial - Saude Bucal")  
    """
    elif curso_copiado == "AUXILIAR ADMINISTRATIVO":
        pyautogui.write("Movimenta: Hibrido - Auxiliar Administrativo v2")
    elif curso_copiado == "AGENTE DE DEFESA AMBIENTAL" :
        pyautogui.write("Movimenta: Hibrido - Agente de Defesa Ambiental v2")
    elif curso_copiado == "MARKETING DIGITAL" or curso_copiado == " MARKETING DIGITAL":
        pyautogui.write("Movimenta: Hibrido - Marketing Digital v2")        
    elif curso_copiado == "GARÇOM":
        pyautogui.write("Movimenta: Hibrido - Garcom (Boteco) v2")
    elif curso_copiado == "INTELIGÊNCIA ARTIFICIAL":
        pyautogui.write("Movimenta: Hibrido - Inteligencia Artificial v2")
    elif curso_copiado == "CUMIN":
        pyautogui.write("Movimenta: Hibrido - Cumim (Boteco) v2")
    elif curso_copiado == "RECEPCIONISTA":
        pyautogui.write("Movimenta: Hibrido - Recepcionista v2")
    elif curso_copiado == "SOCIAL MEDIA" or curso_copiado == " SOCIAL MEDIA":
        pyautogui.write("Movimenta: Hibrido - Social Media v2")
    elif curso_copiado == "ASSISTENTE DE LOGÍSTICA":
        pyautogui.write("Movimenta: Hibrido - Assistente de Logistica v2")
    elif curso_copiado == "AUXILIAR DE COZINHA":
        pyautogui.write("Movimenta: Hibrido - Auxiliar de Cozinha v2")
    elif curso_copiado == "GOVERNANÇA ESG":
        pyautogui.write("Movimenta: Hibrido - Gerenciamento ESG v2")
    elif curso_copiado == "UXUI DESIGNER":
        pyautogui.write("Movimenta: Hibrido - UX/UI Designer v2")       
    elif curso_copiado == "GERENCIAMENTO TRÁFEGO DIGITAL":
        pyautogui.write("Movimenta: Hibrido - Gerenciamento Trafego Digital v2")
    elif curso_copiado == "CAMAREIRO":
        pyautogui.write("Movimenta: Hibrido - Camareiro v2")
    elif curso_copiado == "ORIENTADOR DE HOTELARIA": 
        pyautogui.write("Movimenta: Hibrido - Orientador de Hotelaria v2")
    elif curso_copiado == "PEDREIRO DE ALVENARIA ESTRUTURAL":
        pyautogui.write("Movimenta: Hibrido - Pedreiro de Alvenaria Estrutural v2")
    elif curso_copiado == "APLICAÇÃO DE REVESTIMENTO CERÂMICOS":
        pyautogui.write("Movimenta: Hibrido - Aplicacao de Revestimento Ceramicos v2")
    elif curso_copiado == "INSTALADOR HIDRÁULICO PREDIAL":
        pyautogui.write("Movimenta: Hibrido - Instalador Hidraulico Predial v2")
    elif curso_copiado == "CARPINTEIRO DE OBRAS":
        pyautogui.write("Movimenta: Hibrido - Carpinteiro de Obras v2")
    elif curso_copiado == "ELETRICISTA PREDIAL":
        pyautogui.write("Movimenta: Hibrido - Eletricista Predial v2")
    elif curso_copiado == "SERRALHEIRO DE ALUMÍNIO":
        pyautogui.write("Movimenta: Hibrido - Serralheiro de Aluminio v2")
    elif curso_copiado == "AGENTE DE TURISMO CORPORATIVO":
        pyautogui.write("Movimenta: Hibrido - Agente de Turismo Corporativo v2")
    elif curso_copiado == "MONITOR DE LAZER E RECREAÇÃO":
        pyautogui.write("Movimenta: Hibrido - Monitor de Lazer e Recreacao v2")
    elif curso_copiado == "ATENDENTE DE SALÃO PARA CAFÉ DA MANHÃ":
        pyautogui.write("Movimenta: Hibrido - Atendente de Salao para Cafe da Manha v2")
    elif curso_copiado == "BENEFÍCIO DE PESCADO PARA VENDA":
        pyautogui.write("Movimenta: Hibrido - Beneficio de Pescado para Venda v2")
    elif curso_copiado == "TÉCNICAS E PESCA SUSTENTÁVEL":
        pyautogui.write("Movimenta: Hibrido - Tecnicas e Pesca Sustentavel v2")
    elif curso_copiado == "ECOTURISMO E GESTÃO DE UNIDADES":
        pyautogui.write("Movimenta: Hibrido - Ecoturismo e Gestao de Unidades v2")
    elif curso_copiado == "GESTOR DE RESÍDUOS SÓLIDOS":
        pyautogui.write("Movimenta: Hibrido - Gestor de Residuos Solidos v2")
    elif curso_copiado == "OPERADOR DE SISTEMA DE COMPOSTAGEM":
        pyautogui.write("Movimenta: Hibrido - Operador de Sistema de Compostagem v2")
    elif curso_copiado == "📑 PREPARATÓRIO ENCCEJA 2026":
        pyautogui.write("1 - Preparatorio Encceja: Presencial - Encceja 2025")
    elif curso_copiado == "DESIGNER DE SOBRANCELHAS" or curso_copiado == " DESIGNER DE SOBRANCELHAS":
        pyautogui.write("Movimenta: Hibrido - Designer De Sobrancelhas v2")
    elif curso_copiado == "MANICURE" or curso_copiado == " MANICURE":
        pyautogui.write("Movimenta: Hibrido - Manicure v2")
    elif curso_copiado == "TRANCISTA":
        pyautogui.write("Movimenta: Hibrido - Trancista v2")
    elif curso_copiado == "PEDICURE" or curso_copiado == " PEDICURE":
        pyautogui.write("Movimenta: Hibrido - Pedicure v2")
    elif curso_copiado == "DESIGNER DE UNHAS" or curso_copiado == " DESIGNER DE UNHAS":
        pyautogui.write("Movimenta: Hibrido - Designer De Unhas v2")    
    elif curso_copiado == " EXTENSÃO DE CÍLIOS" or curso_copiado == " EXTENSÃO DE CÍLIOS":
        pyautogui.write("Movimenta: Hibrido - Extensao de Cilios V2")"""
    time.sleep(1)          
    pyautogui.press('tab')
    time.sleep(1)   

##########################################################################

    # ADMINISTRADO
    pyautogui.write("Lucas Luan Pereira Vieira")
    time.sleep(1)
    pyautogui.press('tab')

    # COORDENADOR
    pyautogui.write("Marcus Vinicius Coppola Souto")
    time.sleep(1)

    # BOTÃO PROXIMO - 2
    for _ in range(5):
        pyautogui.press('tab')      
    time.sleep(1)

    # PARTE - 3
    pyautogui.press('space')
    for _ in range(2):
        pyautogui.press('tab')
    pyautogui.write("CE - Fortaleza")
    time.sleep(1)

    # BOTÃO GRAVAR
    for _ in range(15):
        pyautogui.press('tab')
    pyautogui.press('enter')
    time.sleep(1)
    pyautogui.press('tab')
    time.sleep(1)
    for _ in range(2):
        pyautogui.press('enter')
    time.sleep(1)
    pyautogui.click(x=946, y=805)

    # EXCEL
    pyautogui.hotkey('alt', 'tab')
    time.sleep(1)
    pyautogui.press('left')
    pyautogui.press('space')
    time.sleep(1)       
    pyautogui.press('down')
    pyautogui.press('right')
    time.sleep(1)
