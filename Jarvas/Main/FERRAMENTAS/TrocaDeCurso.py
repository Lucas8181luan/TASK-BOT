import pyautogui
import time

time.sleep(3)

for i in range(260):
    pyautogui.press("Enter")
    time.sleep(3)
    pyautogui.press("Tab")
    time.sleep(0.3)
    pyautogui.hotkey("Ctrl", "V")
    time.sleep(0.3)
    for i in range(24):
        pyautogui.press("Tab")
    for i in range(3):
      pyautogui.press("Enter")
      time.sleep(0.3)
    time.sleep(1)
    pyautogui.press("Down")
