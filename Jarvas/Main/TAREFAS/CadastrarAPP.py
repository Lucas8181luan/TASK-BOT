import time
import pyautogui
from PIL import ImageGrab
import easyocr
import numpy as np


def capturar_e_ler_tela():
    # Define a região (bbox): (left, top, right, bottom)
    largura_tela, altura_tela = ImageGrab.grab().size
    bbox = (0, 0, int(largura_tela * 0.6), int(altura_tela * 0.8))  # Ajuste a altura se quiser menos
    screenshot = ImageGrab.grab(bbox=bbox)
    img_np = np.array(screenshot)
    reader = easyocr.Reader(['pt'])
    resultado = reader.readtext(img_np, detail=0)
    texto = '\n'.join(resultado)
    return texto


def executar_cadastrar_app():

    for _ in range(305):
        pyautogui.press('apps')
        time.sleep(2)
        # Tecla de contexto (menu do botão direito)
        if "Parcela" in capturar_e_ler_tela():
            pyautogui.press('esc')
            time.sleep(1)
            pyautogui.press('down')
            time.sleep(1)
            continue
        time.sleep(2)
        
        for _ in range(3):
            pyautogui.press('down')
        time.sleep(1)
        for _ in range(3):
            pyautogui.press('right')
        time.sleep(1)           
        pyautogui.press('enter')
        time.sleep(1)
        if "Inclusão de pessoas no APP IFP Brasil:" in capturar_e_ler_tela():
            pyautogui.press('enter')
            time.sleep(1)
            pyautogui.press('down')
            time.sleep(1)
            continue
        time.sleep(2)
        pyautogui.press('enter')
        time.sleep(2)
        pyautogui.press('right')
        time.sleep(2)
        pyautogui.press('enter')
        time.sleep(2)
        pyautogui.press('enter')
        time.sleep(2)
        pyautogui.hotkey('alt', 'tab')
        time.sleep(2)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(2) 
        pyautogui.press('down')
        time.sleep(2)
        pyautogui.hotkey('alt', 'tab')
        time.sleep(2)
        pyautogui.press('down')
        time.sleep(2)         
    time.sleep(5)

if __name__ == "__main__":
    print("Iniciando em 5 segundos...")
    time.sleep(5)
    executar_cadastrar_app()
