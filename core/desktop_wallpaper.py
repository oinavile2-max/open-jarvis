from __future__ import annotations
import ctypes
from ctypes import wintypes
import os

user32 = ctypes.windll.user32

SMTO_NORMAL = 0x0000
PROGMAN_SPAWN_WORKERW = 0x052C
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
SWP_NOZORDER = 0x0004
SWP_FRAMECHANGED = 0x0020

FindWindowW = user32.FindWindowW
FindWindowExW = user32.FindWindowExW
SetParent = user32.SetParent
GetWindowLongW = user32.GetWindowLongW
SetWindowLongW = user32.SetWindowLongW
SetWindowPos = user32.SetWindowPos
GetClientRect = user32.GetClientRect
EnumWindows = user32.EnumWindows
SendMessageTimeoutW = user32.SendMessageTimeoutW

EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long), ("top", ctypes.c_long),
        ("right", ctypes.c_long), ("bottom", ctypes.c_long),
    ]

def _spawn_workerw():
    progman = FindWindowW("Progman", None)
    if not progman:
        return
    result = wintypes.DWORD()
    SendMessageTimeoutW(
        progman, PROGMAN_SPAWN_WORKERW, 0, 0,
        SMTO_NORMAL, 1000, ctypes.byref(result)
    )

def find_desktop_workerw() -> int:
    _spawn_workerw()
    found = {"worker": 0}

    @EnumWindowsProc
    def cb(hwnd, lparam):
        shell_view = FindWindowExW(hwnd, 0, "SHELLDLL_DefView", None)
        if shell_view:
            worker = FindWindowExW(0, hwnd, "WorkerW", None)
            if worker:
                found["worker"] = int(worker)
                return False
        return True

    EnumWindows(cb, 0)
    if found["worker"]:
        return found["worker"]

    progman = FindWindowW("Progman", None)
    return int(progman or 0)

def attach_qt_window_to_desktop(hwnd: int):
    if os.name != "nt":
        return False, "Modo wallpaper disponível apenas no Windows.", (0, 0)

    parent = find_desktop_workerw()
    if not parent:
        return False, "Camada do desktop do Windows não encontrada.", (0, 0)

    ex = GetWindowLongW(hwnd, GWL_EXSTYLE)
    SetWindowLongW(hwnd, GWL_EXSTYLE, ex | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)

    SetParent(hwnd, parent)

    rect = RECT()
    if GetClientRect(parent, ctypes.byref(rect)):
        width = max(1, rect.right - rect.left)
        height = max(1, rect.bottom - rect.top)
        SetWindowPos(hwnd, 0, 0, 0, width, height, SWP_NOZORDER | SWP_FRAMECHANGED)
        return True, "JARVIS conectado ao fundo da Área de Trabalho.", (width, height)

    return True, "JARVIS conectado ao fundo da Área de Trabalho.", (0, 0)
