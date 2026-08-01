import os
# Configura o caminho do executável do Tesseract
# Programa para tirar print da tela e ler informações (OCR)
from PIL import ImageGrab
import numpy as np
import easyocr

def capturar_e_ler_tela():
    # Define a região (bbox): (left, top, right, bottom)
    largura_tela, altura_tela = ImageGrab.grab().size
    bbox = (0, 0, int(largura_tela * 0.8), int(altura_tela * 0.8))  # Ajuste a altura se quiser menos
    screenshot = ImageGrab.grab(bbox=bbox)
    img_np = np.array(screenshot)
    reader = easyocr.Reader(['pt', 'en'])
    resultado = reader.readtext(img_np, detail=0)
    texto = '\n'.join(resultado)
    print('Texto extraído:')
    print(texto)
    return texto

if __name__ == "__main__":
	capturar_e_ler_tela()
