"""Keeping a window just above the desktop (the wallpaper and icons) and below every other window (Windows only),
for the sun and moon. Qt's "stay on bottom" puts a window underneath the desktop itself, where it can't be seen,
so instead it's slotted in right above the desktop's own windows, and put back there now and then.
"""
import ctypes
import sys

ON_WINDOWS = sys.platform == "win32"
GW_HWNDPREV = 3
GWL_EXSTYLE = -20
WS_EX_TOPMOST = 0x0008
SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE, SWP_NOOWNERZORDER = 0x0001, 0x0002, 0x0010, 0x0200
HWND_NOTOPMOST = -2

if ON_WINDOWS:
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.FindWindowW.argtypes = (wintypes.LPCWSTR, wintypes.LPCWSTR)
    user32.FindWindowW.restype = wintypes.HWND
    user32.GetWindow.argtypes = (wintypes.HWND, wintypes.UINT)
    user32.GetWindow.restype = wintypes.HWND
    user32.GetClassNameW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
    user32.GetWindowLongW.argtypes = (wintypes.HWND, ctypes.c_int)
    user32.GetWindowLongW.restype = wintypes.LONG
    user32.SetWindowPos.argtypes = (wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                    ctypes.c_int, wintypes.UINT)


def _class(hwnd):
    buffer = ctypes.create_unicode_buffer(64)
    user32.GetClassNameW(hwnd, buffer, 64)
    return buffer.value


def just_above_desktop(hwnd):
    """Slot the window (a native handle) in right above the desktop and below everything else. False if it
    couldn't (not Windows, or no desktop found)."""
    if not ON_WINDOWS:
        return False
    try:
        mine = wintypes.HWND(int(hwnd))

        def above(h):  # the next window up the stack, not counting ours
            h = user32.GetWindow(h, GW_HWNDPREV)
            while h and h == mine.value:
                h = user32.GetWindow(h, GW_HWNDPREV)
            return h

        layer = user32.FindWindowW("Progman", None)
        if not layer:
            return False
        # the desktop can be several windows (Progman, and WorkerW ones for the wallpaper) stacked together
        while above(layer) and _class(above(layer)) == "WorkerW":
            layer = above(layer)
        top = above(layer)
        if not top or user32.GetWindowLongW(top, GWL_EXSTYLE) & WS_EX_TOPMOST:
            after = wintypes.HWND(HWND_NOTOPMOST)  # only always-on-top windows above: top of the normal ones
        else:
            after = wintypes.HWND(top)  # (SetWindowPos puts us just below this one, so just above the desktop)
        flags = SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_NOOWNERZORDER
        return bool(user32.SetWindowPos(mine, after, 0, 0, 0, 0, flags))
    except Exception:
        return False
