"""The folder icons on your desktop: where they are, and moving them (Windows only), for the foxes' folder
mischief. A fox pulls a folder icon down to the bottom of the screen and drags it somewhere else.

Only the icons' positions are read and changed (the same as dragging them yourself); the folders and what's
in them are never touched. Where each folder was before a fox first moved it is kept in user-data/world.json
("folder_homes"), and the tray menu's "Put the desktop folders back" moves them all back there.

The desktop is a list view (SysListView32) inside Explorer. Reading an icon's name or position from another
process needs a little memory inside Explorer to receive the answer: allocated, read and freed right away.
Positions here are in physical screen pixels. Nothing happens if the desktop's icons are set to "Auto arrange"
(they'd only jump back), or hidden, or anything looks odd: every function just returns None or False.
"""
import ctypes
import os
import sys

ON_WINDOWS = sys.platform == "win32"

LVM_GETITEMCOUNT = 0x1004
LVM_GETITEMRECT = 0x100E
LVM_SETITEMPOSITION = 0x100F
LVM_GETITEMPOSITION = 0x1010
LVM_GETITEMTEXTW = 0x1073
LVS_AUTOARRANGE = 0x0100
LVIR_BOUNDS = 0
GWL_STYLE = -16
PROCESS_ACCESS = 0x0008 | 0x0010 | 0x0020 | 0x0400  # VM operation, read, write; query information
MEM_COMMIT_RESERVE, MEM_RELEASE, PAGE_READWRITE = 0x3000, 0x8000, 0x04
CSIDL_DESKTOPDIRECTORY, CSIDL_COMMON_DESKTOPDIRECTORY = 0x10, 0x19

if ON_WINDOWS:
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    shell32 = ctypes.WinDLL("shell32")
    LRESULT = ctypes.c_ssize_t
    user32.FindWindowW.argtypes = (wintypes.LPCWSTR, wintypes.LPCWSTR)
    user32.FindWindowW.restype = wintypes.HWND
    user32.FindWindowExW.argtypes = (wintypes.HWND, wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR)
    user32.FindWindowExW.restype = wintypes.HWND
    user32.SendMessageW.argtypes = (wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
    user32.SendMessageW.restype = LRESULT
    user32.GetWindowLongW.argtypes = (wintypes.HWND, ctypes.c_int)
    user32.GetWindowLongW.restype = wintypes.LONG
    user32.IsWindowVisible.argtypes = (wintypes.HWND,)
    user32.ClientToScreen.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.POINT))
    user32.ScreenToClient.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.POINT))
    user32.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
    kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.VirtualAllocEx.argtypes = (wintypes.HANDLE, wintypes.LPVOID, ctypes.c_size_t, wintypes.DWORD,
                                        wintypes.DWORD)
    kernel32.VirtualAllocEx.restype = wintypes.LPVOID
    kernel32.VirtualFreeEx.argtypes = (wintypes.HANDLE, wintypes.LPVOID, ctypes.c_size_t, wintypes.DWORD)
    kernel32.ReadProcessMemory.argtypes = (wintypes.HANDLE, wintypes.LPCVOID, wintypes.LPVOID, ctypes.c_size_t,
                                           ctypes.POINTER(ctypes.c_size_t))
    kernel32.WriteProcessMemory.argtypes = (wintypes.HANDLE, wintypes.LPVOID, wintypes.LPCVOID, ctypes.c_size_t,
                                            ctypes.POINTER(ctypes.c_size_t))
    kernel32.IsWow64Process.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL))
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    class LVITEMW(ctypes.Structure):
        _fields_ = [("mask", wintypes.UINT), ("iItem", ctypes.c_int), ("iSubItem", ctypes.c_int),
                    ("state", wintypes.UINT), ("stateMask", wintypes.UINT), ("pszText", ctypes.c_void_p),
                    ("cchTextMax", ctypes.c_int), ("iImage", ctypes.c_int), ("lParam", wintypes.LPARAM),
                    ("iIndent", ctypes.c_int), ("iGroupId", ctypes.c_int), ("cColumns", wintypes.UINT),
                    ("puColumns", ctypes.c_void_p), ("piColFmt", ctypes.c_void_p), ("iGroup", ctypes.c_int)]


def find_listview():
    """The desktop's icon list view, or None."""
    if not ON_WINDOWS:
        return None
    progman = user32.FindWindowW("Progman", None)
    view = user32.FindWindowExW(progman, None, "SHELLDLL_DefView", None) if progman else None
    if not view:  # with a slideshow wallpaper, it lives in one of the WorkerW windows instead
        found = []

        def check(hwnd, _):
            child = user32.FindWindowExW(hwnd, None, "SHELLDLL_DefView", None)
            if child:
                found.append(child)
                return False
            return True

        user32.EnumWindows(EnumWindowsProc(check), 0)
        view = found[0] if found else None
    if not view:
        return None
    listview = user32.FindWindowExW(view, None, "SysListView32", None)
    return listview or None


def can_move(listview):
    """Icons visible, and not on Auto arrange."""
    return bool(listview) and bool(user32.IsWindowVisible(listview)) and \
        not (user32.GetWindowLongW(listview, GWL_STYLE) & LVS_AUTOARRANGE)


def _desktop_dirs():
    dirs = []
    for csidl in (CSIDL_DESKTOPDIRECTORY, CSIDL_COMMON_DESKTOPDIRECTORY):
        buffer = ctypes.create_unicode_buffer(260)
        if shell32.SHGetFolderPathW(None, csidl, None, 0, buffer) == 0 and buffer.value:
            dirs.append(buffer.value)
    return dirs


def is_folder(name, dirs=None):
    """Is the desktop icon called this a folder (rather than a file, a shortcut or This PC)?"""
    if not name or name in (".", "..") or any(c in name for c in '\\/:*?"<>|'):
        return False
    return any(os.path.isdir(os.path.join(d, name)) for d in (dirs if dirs is not None else _desktop_dirs()))


class _Explorer:
    """A little scratch memory inside Explorer, to receive the list view's answers."""

    SIZE = 4096

    def __init__(self, listview):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(listview, ctypes.byref(pid))
        self.process = kernel32.OpenProcess(PROCESS_ACCESS, False, pid.value)
        self.memory = None
        if not self.process:
            return
        mine, theirs = wintypes.BOOL(), wintypes.BOOL()
        kernel32.IsWow64Process(kernel32.GetCurrentProcess(), ctypes.byref(mine))
        kernel32.IsWow64Process(self.process, ctypes.byref(theirs))
        if mine.value != theirs.value:  # 32-bit Python on 64-bit Windows: the structures wouldn't match
            return
        self.memory = kernel32.VirtualAllocEx(self.process, None, self.SIZE, MEM_COMMIT_RESERVE, PAGE_READWRITE)

    def __enter__(self):
        return self if self.memory else None

    def __exit__(self, *_):
        if self.memory:
            kernel32.VirtualFreeEx(self.process, self.memory, 0, MEM_RELEASE)
        if self.process:
            kernel32.CloseHandle(self.process)

    def write(self, offset, struct):
        done = ctypes.c_size_t()
        return kernel32.WriteProcessMemory(self.process, self.memory + offset, ctypes.byref(struct),
                                           ctypes.sizeof(struct), ctypes.byref(done))

    def read(self, offset, struct):
        done = ctypes.c_size_t()
        return kernel32.ReadProcessMemory(self.process, self.memory + offset, ctypes.byref(struct),
                                          ctypes.sizeof(struct), ctypes.byref(done))


def _icons(listview, explorer):
    """[(index, name, position (client), bounds (client: left, top, right, bottom))] for every desktop icon."""
    count = user32.SendMessageW(listview, LVM_GETITEMCOUNT, 0, 0)
    out = []
    text_at, point_at, rect_at = 1024, 512, 768  # offsets into the scratch memory
    for index in range(min(count, 500)):
        item = LVITEMW(iSubItem=0, pszText=explorer.memory + text_at, cchTextMax=(explorer.SIZE - text_at) // 2)
        explorer.write(0, item)
        length = user32.SendMessageW(listview, LVM_GETITEMTEXTW, index, explorer.memory)
        text = ctypes.create_unicode_buffer(max(1, length + 1))
        if length > 0:
            explorer.read(text_at, text)
        point = wintypes.POINT()
        if not user32.SendMessageW(listview, LVM_GETITEMPOSITION, index, explorer.memory + point_at):
            continue
        explorer.read(point_at, point)
        rect = wintypes.RECT(LVIR_BOUNDS, 0, 0, 0)
        explorer.write(rect_at, rect)
        if not user32.SendMessageW(listview, LVM_GETITEMRECT, index, explorer.memory + rect_at):
            continue
        explorer.read(rect_at, rect)
        out.append((index, text.value, (point.x, point.y), (rect.left, rect.top, rect.right, rect.bottom)))
    return out


def _to_screen(listview, x, y):
    p = wintypes.POINT(x, y)
    user32.ClientToScreen(listview, ctypes.byref(p))
    return p.x, p.y


def _to_client(listview, x, y):
    p = wintypes.POINT(x, y)
    user32.ScreenToClient(listview, ctypes.byref(p))
    return p.x, p.y


def folders():
    """Each folder icon on the desktop: {"name", "left", "top", "width", "height"} (its whole box, label and
    all, in physical screen pixels) and "place" (its position as the list view keeps it). [] if there are
    none, or they can't be moved."""
    try:
        listview = find_listview()
        if not can_move(listview):
            return []
        dirs = _desktop_dirs()
        with _Explorer(listview) as explorer:
            if explorer is None:
                return []
            found = []
            for index, name, place, (left, top, right, bottom) in _icons(listview, explorer):
                if not is_folder(name, dirs):
                    continue
                sx, sy = _to_screen(listview, left, top)
                found.append({"name": name, "left": sx, "top": sy, "width": right - left, "height": bottom - top,
                              "place": list(place), "nudge": (place[0] - left, place[1] - top)})
            return found
    except Exception:
        return []


def _lparam(x, y):
    return ((int(y) & 0xFFFF) << 16) | (int(x) & 0xFFFF)


def _index_of(listview, name):
    with _Explorer(listview) as explorer:
        if explorer is None:
            return None
        for index, found, _, _ in _icons(listview, explorer):
            if found == name:
                return index
    return None


class Mover:
    """Moves one folder icon about smoothly while a fox has it (looked up once, then moved every frame)."""

    def __init__(self, name):
        self.name = name
        self.listview = find_listview() if ON_WINDOWS else None
        self.index = None
        self.nudge = (0, 0)
        if can_move(self.listview):
            try:
                self.index = _index_of(self.listview, name)
                spot = next((f for f in folders() if f["name"] == name), None)
                if spot is not None:
                    self.nudge = spot["nudge"]
            except Exception:
                self.index = None

    @property
    def ok(self):
        return self.index is not None

    def move_box(self, left, top):
        """Put the icon's box with its top-left corner here (physical screen pixels)."""
        if self.index is None:
            return False
        try:
            cx, cy = _to_client(self.listview, int(left), int(top))
            user32.SendMessageW(self.listview, LVM_SETITEMPOSITION, self.index,
                                _lparam(max(0, cx + self.nudge[0]), max(0, cy + self.nudge[1])))
            return True
        except Exception:
            return False


def put_back(homes):
    """Move each folder back to where it was ({name: [x, y]} list-view positions). How many were moved."""
    try:
        listview = find_listview()
        if not can_move(listview):
            return 0
        moved = 0
        with _Explorer(listview) as explorer:
            if explorer is None:
                return 0
            for index, name, _, _ in _icons(listview, explorer):
                if name in homes:
                    x, y = homes[name]
                    user32.SendMessageW(listview, LVM_SETITEMPOSITION, index, _lparam(x, y))
                    moved += 1
        return moved
    except Exception:
        return 0
