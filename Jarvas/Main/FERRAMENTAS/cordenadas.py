import pyautogui
import time

time.sleep(8)  # Tempo para o usuário posicionar o mouse na tela desejada

x, y = pyautogui.position()
print(f"Posição atual: x={x}, y={y}")

