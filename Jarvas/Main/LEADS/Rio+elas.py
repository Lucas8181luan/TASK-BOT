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
    resultado = reader.readtext(img_np, detail=0)
    texto = '\n'.join(resultado)
    return texto

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
    time.sleep(3)
    pyautogui.press('Enter')
    time.sleep(3)
    pyautogui.hotkey('Ctrl', 'v')
    time.sleep(1)   
    
    # EXTRA
    pyautogui.press('enter')
    time.sleep(1)
    pyautogui.hotkey('Ctrl', 'v')
    time.sleep(1)
    pyautogui.press('enter')    
    time.sleep(1)
    # BOTÃO SEXO
    pyautogui.hotkey('alt', 'tab')
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
    pyautogui.click(x=287, y=667)
    time.sleep(1)
    pyautogui.write(sexo)
    time.sleep(1)
    # BOTÃO CEP
    pyautogui.click(x=47, y=781)
    time.sleep(1)
    pyautogui.hotkey('alt', 'tab')
    time.sleep(1)
    for r in range(4):
        pyautogui.press('right')
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(1)
    cep = pyperclip.paste()
    for l in range(4):
        pyautogui.press('left')
    time.sleep(1)
    pyautogui.hotkey('alt', 'tab')
    time.sleep(1)
    pyautogui.write(cep)
    time.sleep(1)
    # BOTÃO PROXIMO - 1
    pyautogui.click(x=887, y=1019)
    time.sleep(1)
    '''if "Digito Verificador do CPF ou do CNPJ não confere" in capturar_e_ler_tela():
        time.sleep(1)
        pyautogui.hotkey('alt', 'tab')
        time.sleep(1)
        pyautogui.press('down')
            time.sleep(1)
            
        pyautogui.hotkey('Ctrl', 'c')
        pyperclip.paste() 
        time.sleep(1)
        pyautogui.hotkey('alt', 'tab')
        time.sleep(1)
        pyautogui.press('Enter')
        time.sleep(1)
            pyautogui.hotkey('', 't         
            
            pyautogui.press('tab')
            time.sleep(3)
        pyautogui.hotkey('Ctrl', 'v')
        time.sleep(1)
        pyautogui.write("M")
        time.sleep(1)
        pyautogui.click(x=892, y=843)'''
        
    time.sleep(2)
    pyautogui.press('tab')  
    time.sleep(1)

    # TIPO DE CONTRATO
    pyautogui.write("Bolsa")
    pyautogui.press('tab')
    
    # DATA DA MATRÍCULAM
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
    for i in range(8):
        pyautogui.press('backspace')
    pyautogui.write(data_de_inscricao)
    time.sleep(1)
    pyautogui.press('tab')
    pyautogui.press('tab')

    # EVENTO
    pyautogui.write("7 - Rio+Elas")
    time.sleep(1)
    pyautogui.press('tab')  

    # CURSO
    '''for i in range(67):Bolsa 
        pyautogui.press('down')
    pyautogui.press('tab')
    '''
##########################################################################
    pyautogui.hotkey('alt', 'tab')
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
    pyautogui.hotkey('alt', 'tab')
    
    # CURSO ESCMarcus Vinicius Coppola SoutoOLHIDO   
    
    if curso_copiado == "TRANCISTA":
        pyautogui.write(": Presencial - Trancista")
    elif curso_copiado == "DESIGNER DE SOBRANCELHAS" :
        pyautogui.write("Rio+Elas: Presencial - Designer de Sobrancelhas")
    elif curso_copiado == "NAILS DESIGNER" or curso_copiado == "DESIGNER DE UNHAS":
        pyautogui.write("Rio+Elas: Presencial - Designer de Unhas")   
    elif curso_copiado == "EXTENSÃO DE CÍLIOS":
        pyautogui.write("Rio+Elas: Presencial - Extensao de Cilios")       
    time.sleep(1)  
    pyautogui.press('tab')
    time.sleep(1)

##########################################################################

    # ADMINISTRADO
    pyautogui.write("Lucas Luan Pereira Vieira")                
    time.sleep(1)      
    pyautogui.press('tab')


    # COORDENADOR
    pyautogui.write("Stefanie Lucena Pereira de Melo")
    time.sleep(1)

    # BOTÃO PROXIMO - 2
    for _ in range(5):
        pyautogui.press('tab')      
    time.sleep(1)
  
    # PARTE - 3         RJ - Ri
    #   o+Elas
    pyautogui.press('space')
    for _ in range(2):
        pyautogui.press('tab')
    pyautogui.write("RJ - Rio+Elas")
    time.sleep(1)   

    # BOTÃO GRAVAR
    for _ in range(6):
        pyautogui.press('tab')
    pyautogui.press('enter')
    time.sleep(1)       

    # EXCEL
    pyautogui.hotkey('alt', 'tab')
  
    time.sleep(1)
    pyautogui.press('left')
    pyautogui.press('space')
    time.sleep(1)       
    pyautogui.press('down')
    pyautogui.press('right')
        