import pyautogui
import time
import pyperclip

time.sleep(7)
c = 0

while True:
    c += 1
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(1)
    pyautogui.hotkey('alt', 'tab')
    time.sleep(1)
    pyautogui.press('f4')
    time.sleep(1)
    pyautogui.press('tab')
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(1)
    pyautogui.press('down')
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(1)

    valor = pyperclip.paste().strip()
    if not valor:
        continue

    pyautogui.press('apps')
    time.sleep(1)
    for _ in range(7):
        pyautogui.press('down')
    pyautogui.press('enter')
    time.sleep(1)
    pyautogui.press('down')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(1)

    for _ in range(4):
        pyautogui.press('tab')

    pyautogui.press('enter')
    pyautogui.press('enter')
    time.sleep(1)
    pyautogui.hotkey('alt', 'tab')
    time.sleep(1)
    pyautogui.press('right')
    time.sleep(1)
    pyautogui.press('space')
    time.sleep(1)
    pyautogui.press('left')
    time.sleep(2)
    pyautogui.press('down')
    time.sleep(1)

    if c == 40:
        break