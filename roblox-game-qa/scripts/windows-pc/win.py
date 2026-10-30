# win.py: python win.py focus "<title part>" [max] | shot out.png | click x y | clickrel "<title part>" fx fy
import sys, time, pyautogui, pygetwindow as gw
def find(part):
    ws = [w for w in gw.getAllWindows() if part.lower() in w.title.lower() and "grok" not in w.title.lower()]
    if not ws: sys.exit("no window: " + part)
    return ws[0]
a = sys.argv[1:]
i = 0
while i < len(a):
    c = a[i]
    if c == "focus":
        w = find(a[i+1]); i += 2
        try:
            w.minimize(); time.sleep(0.3); w.restore(); time.sleep(0.3); w.activate()
        except Exception as e: print("activate warn", e)
        if i < len(a) and a[i] == "max": w.maximize(); i += 1
        time.sleep(0.8); print("focused", w.title, w.left, w.top, w.width, w.height)
    elif c == "shot": pyautogui.screenshot(a[i+1]); print("shot", a[i+1]); i += 2
    elif c == "click": pyautogui.click(int(a[i+1]), int(a[i+2])); print("click", a[i+1], a[i+2]); time.sleep(1); i += 3
    elif c == "sleep": time.sleep(float(a[i+1])); i += 2
    elif c == "key": pyautogui.press(a[i+1]); i += 2
    elif c == "titles": print([w.title for w in gw.getAllWindows() if w.title]); i += 1
    else: sys.exit("bad cmd " + c)
