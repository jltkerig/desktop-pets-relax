/* Pixel Fox.exe: starts Pixel Fox from the folder the .exe sits in, with no console window.
 * It runs start.ps1 there (which checks for updates, installs what's needed and starts the foxes), the same
 * as double-clicking Pixel Fox.cmd. If that fails, it says so and points at Pixel Fox.cmd, which shows why.
 *
 * Built with -DSCREENSAVER it is Pixel Fox.scr, the screen saver. Windows runs it with /s (show it), /c (its
 * settings) or /p (the little preview, left empty). It starts pythonw.exe straight away if start.ps1 has
 * remembered where it is (python-path.txt), or else goes through start.ps1 -Saver. Either way it waits until
 * the screen saver closes, which is how Windows knows it's still showing.
 * Build: launcher/build.sh (needs the MinGW-w64 cross compiler). */
#include <windows.h>
#include <wchar.h>

#define LONG_PATH 4096

static void say(const wchar_t *text) {
    MessageBoxW(NULL, text, L"Pixel Fox", MB_OK | MB_ICONINFORMATION);
}

/* Run a command line in dir with no window, wait for it, and return its exit code (or -1 if it didn't start). */
static long run(const wchar_t *program, wchar_t *line, const wchar_t *dir) {
    STARTUPINFOW si = { sizeof si };
    PROCESS_INFORMATION pi;
    if (!CreateProcessW(program, line, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, dir, &si, &pi)) return -1;
    WaitForSingleObject(pi.hProcess, INFINITE);
    DWORD code = 1;
    GetExitCodeProcess(pi.hProcess, &code);
    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);
    return (long)code;
}

#ifdef SCREENSAVER
/* The switch Windows passed ("/s", "/c", "/c:1234", "/p 1234"), as one of L"/s", L"/c" or L"/p". */
static const wchar_t *saver_switch(PWSTR args) {
    while (*args == L' ' || *args == L'\t') args++;
    if (*args == L'/' || *args == L'-') args++;
    switch (*args) {
        case L's': case L'S': return L"/s";
        case L'p': case L'P': return L"/p";
        default: return L"/c";  /* /c, or nothing at all (double-clicked): the settings */
    }
}

/* python-path.txt, written by start.ps1 (UTF-16 with a byte-order mark), into path. */
static int remembered_python(const wchar_t *dir, wchar_t *path, int size) {
    static wchar_t file[LONG_PATH + 32];
    _snwprintf(file, LONG_PATH + 32, L"%ls\\python-path.txt", dir);
    HANDLE h = CreateFileW(file, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
    if (h == INVALID_HANDLE_VALUE) return 0;
    DWORD got = 0;
    BOOL ok = ReadFile(h, path, (DWORD)((size - 1) * sizeof(wchar_t)), &got, NULL);
    CloseHandle(h);
    if (!ok) return 0;
    path[got / sizeof(wchar_t)] = 0;
    wchar_t *start = path[0] == 0xFEFF ? path + 1 : path;
    wchar_t *end = start + wcslen(start);
    while (end > start && (end[-1] == L'\r' || end[-1] == L'\n' || end[-1] == L' ')) *--end = 0;
    memmove(path, start, (wcslen(start) + 1) * sizeof(wchar_t));
    return path[0] && GetFileAttributesW(path) != INVALID_FILE_ATTRIBUTES;
}
#endif

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR args, int show) {
    (void)instance; (void)previous; (void)show;
    static wchar_t dir[LONG_PATH], script[LONG_PATH + 16], system[MAX_PATH], shell[MAX_PATH + 64];
    static wchar_t line[2 * LONG_PATH + MAX_PATH + 128];

    DWORD n = GetModuleFileNameW(NULL, dir, LONG_PATH);
    if (n == 0 || n >= LONG_PATH) return 1;
    wchar_t *slash = wcsrchr(dir, L'\\');
    if (slash) *slash = 0;

#ifdef SCREENSAVER
    const wchar_t *mode = saver_switch(args);
    if (wcscmp(mode, L"/p") == 0) return 0;  /* no preview: the box in Windows' settings stays empty */
    static wchar_t python[LONG_PATH];
    if (remembered_python(dir, python, LONG_PATH)) {
        _snwprintf(line, sizeof line / sizeof *line, L"\"%ls\" \"%ls\\pixelfox.py\" --scr %ls", python, dir, mode);
        if (run(python, line, dir) >= 0) return 0;
    }
#else
    (void)args;
#endif

    _snwprintf(script, LONG_PATH + 16, L"%ls\\start.ps1", dir);
    if (GetFileAttributesW(script) == INVALID_FILE_ATTRIBUTES) {
        say(L"Pixel Fox needs to be in the Pixel Fox folder, next to start.ps1.");
        return 1;
    }

    /* Windows PowerShell by its full path, so nothing else named powershell.exe is ever picked up */
    UINT got = GetSystemDirectoryW(system, MAX_PATH);
    if (got == 0 || got >= MAX_PATH) return 1;
    _snwprintf(shell, MAX_PATH + 64, L"%ls\\WindowsPowerShell\\v1.0\\powershell.exe", system);
#ifdef SCREENSAVER
    _snwprintf(line, sizeof line / sizeof *line,
               L"\"%ls\" -NoProfile -ExecutionPolicy Bypass -File \"%ls\" -Saver %ls", shell, script, mode);
    run(shell, line, dir);  /* a screen saver that can't start just doesn't show: no message to click away */
    return 0;
#else
    _snwprintf(line, sizeof line / sizeof *line,
               L"\"%ls\" -NoProfile -ExecutionPolicy Bypass -File \"%ls\"", shell, script);
    long code = run(shell, line, dir);  /* start.ps1 finishes once the foxes are running */
    if (code < 0) {
        say(L"Windows PowerShell couldn't be started, so Pixel Fox can't start.");
        return 1;
    }
    if (code != 0) {
        say(L"Pixel Fox couldn't start.\n\nDouble-click \"Pixel Fox.cmd\" in the same folder to see what went wrong.");
    }
    return (int)code;
#endif
}
