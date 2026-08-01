import pyautogui
import time

time.sleep(7)

for i in range(37):

    #Seleciona Matrícula F10#
    pyautogui.press("Enter")
    time.sleep(4)

    #TAB até o campo de DATA DE MATRÍCULA e copia#
    for i in range(14):
        pyautogui.press("Tab")
    time.sleep(1)
    pyautogui.hotkey("Ctrl", "C")
    time.sleep(2)

    #ALT+TAB para planilha Sheets e cola a data#
    pyautogui.hotkey("Alt", "Tab")
    time.sleep(1)
    pyautogui.press("Left")
    time.sleep(1)
    pyautogui.hotkey("Ctrl", "v")
    time.sleep(1)

    #A planilha altera a data para o mesmo dia do mês selecionado#

    #Seleciona a nova data copia#
    pyautogui.press("Right")
    time.sleep(1)
    pyautogui.hotkey("Ctrl", "C")
    time.sleep(1)

    #ALT+TAB para F10 e cola a nova data no campo DATA DE MATRÍCULA#
    pyautogui.hotkey("Alt", "Tab")
    time.sleep(2)
    pyautogui.hotkey("Ctrl", "v")

    #TAB até o botão para confirmar e ENTER para o "OK"#
    for i in range(15):
        pyautogui.press("Tab")
    time.sleep(1)
    pyautogui.press("Enter")
    time.sleep(3)

    #Próximo#
    pyautogui.press("Down")
    