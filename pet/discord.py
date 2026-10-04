"""Finding a Discord window on screen, for the foxes' message-stealing mischief (Windows only).

Only the window's position is looked up here; the message itself is just a picture copied off the
screen by the app and put back afterwards. Nothing in Discord is read, changed or sent, and the picture
is never saved.
"""
import ctypes
import os
import sys
from ctypes import wintypes

ON_WINDOWS = sys.platform == "win32"

if ON_WINDOWS:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    dwmapi = ctypes.WinDLL("dwmapi")
    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    DWMWA_EXTENDED_FRAME_BOUNDS = 9
    GA_ROOT = 2


def _exe_name(hwnd):
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not handle:
        return ""
    try:
        size = wintypes.DWORD(1024)
        buffer = ctypes.create_unicode_buffer(1024)
        if kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return buffer.value.rsplit("\\", 1)[-1].lower()
        return ""
    finally:
        kernel32.CloseHandle(handle)


def _bounds(hwnd):
    """The window's visible rectangle (left, top, right, bottom) in screen pixels."""
    rect = wintypes.RECT()
    if dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_EXTENDED_FRAME_BOUNDS, ctypes.byref(rect), ctypes.sizeof(rect)) != 0:
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom


def find_window():
    """(hwnd, (left, top, right, bottom)) of a visible, not-minimised Discord window, or None."""
    if not ON_WINDOWS:
        return None
    found = []

    def check(hwnd, _):
        if user32.IsWindowVisible(hwnd) and not user32.IsIconic(hwnd) and user32.GetWindowTextLengthW(hwnd) > 0:
            if _exe_name(hwnd) == "discord.exe":
                left, top, right, bottom = _bounds(hwnd)
                if right - left > 500 and bottom - top > 300:
                    found.append((hwnd, (left, top, right, bottom)))
                    return False  # stop looking
        return True

    user32.EnumWindows(EnumWindowsProc(check), 0)
    return found[0] if found else None


def _ours(window):
    """A window belonging to Pixel Fox itself (the pets' see-through windows)."""
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(window, ctypes.byref(pid))
    return pid.value == os.getpid()


def shows_at(hwnd, x, y):
    """True if the point (screen pixels) shows this window. Pixel Fox's own windows (a tree or a fox in
    front of it) don't count as covering it; any other window on top does."""
    if not ON_WINDOWS:
        return False
    point = wintypes.POINT(int(x), int(y))
    top = user32.WindowFromPoint(point)
    if not top:
        return False
    root = user32.GetAncestor(top, GA_ROOT)
    if root == hwnd:
        return True
    if _ours(root):  # our window on top: look at what's underneath it in the stacking order
        below = user32.GetWindow(root, 2)  # GW_HWNDNEXT
        while below:
            rect = wintypes.RECT()
            user32.GetWindowRect(below, ctypes.byref(rect))
            if user32.IsWindowVisible(below) and not _ours(below) and                     rect.left <= point.x < rect.right and rect.top <= point.y < rect.bottom:
                return below == hwnd
            below = user32.GetWindow(below, 2)
    return False


def still_there(hwnd, bounds):
    """The window hasn't moved, been resized, minimised or closed."""
    if not ON_WINDOWS or not user32.IsWindow(hwnd) or user32.IsIconic(hwnd) or not user32.IsWindowVisible(hwnd):
        return False
    return _bounds(hwnd) == bounds
