/* Pixel Fox.exe: starts Pixel Fox from the folder the .exe sits in, with no console window.
 * It runs start.ps1 there (which checks for updates, installs what's needed and starts the foxes), the same
 * as double-clicking Pixel Fox.cmd. If that fails, it says so and points at Pixel Fox.cmd, which shows why.
 * Build: launcher/build.sh (needs the MinGW-w64 cross compiler). */
#include <windows.h>
#include <wchar.h>

#define LONG_PATH 4096

static void say(const wchar_t *text) {
    MessageBoxW(NULL, text, L"Pixel Fox", MB_OK | MB_ICONINFORMATION);
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR args, int show) {
    (void)instance; (void)previous; (void)args; (void)show;
    static wchar_t dir[LONG_PATH], script[LONG_PATH + 16], system[MAX_PATH], shell[MAX_PATH + 64];
    static wchar_t line[LONG_PATH + MAX_PATH + 128];

    DWORD n = GetModuleFileNameW(NULL, dir, LONG_PATH);
    if (n == 0 || n >= LONG_PATH) return 1;
    wchar_t *slash = wcsrchr(dir, L'\\');
    if (slash) *slash = 0;

    _snwprintf(script, LONG_PATH + 16, L"%ls\\start.ps1", dir);
    if (GetFileAttributesW(script) == INVALID_FILE_ATTRIBUTES) {
        say(L"Pixel Fox.exe needs to be in the Pixel Fox folder, next to start.ps1.");
        return 1;
    }

    /* Windows PowerShell by its full path, so nothing else named powershell.exe is ever picked up */
    UINT got = GetSystemDirectoryW(system, MAX_PATH);
    if (got == 0 || got >= MAX_PATH) return 1;
    _snwprintf(shell, MAX_PATH + 64, L"%ls\\WindowsPowerShell\\v1.0\\powershell.exe", system);
    _snwprintf(line, LONG_PATH + MAX_PATH + 128,
               L"\"%ls\" -NoProfile -ExecutionPolicy Bypass -File \"%ls\"", shell, script);
    STARTUPINFOW si = { sizeof si };
    PROCESS_INFORMATION pi;
    if (!CreateProcessW(shell, line, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, dir, &si, &pi)) {
        say(L"Windows PowerShell couldn't be started, so Pixel Fox can't start.");
        return 1;
    }
    WaitForSingleObject(pi.hProcess, INFINITE);  /* start.ps1 finishes once the foxes are running */
    DWORD code = 1;
    GetExitCodeProcess(pi.hProcess, &code);
    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);
    if (code != 0) {
        say(L"Pixel Fox couldn't start.\n\nDouble-click \"Pixel Fox.cmd\" in the same folder to see what went wrong.");
    }
    return (int)code;
}
