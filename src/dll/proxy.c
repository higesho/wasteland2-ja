/* version.dll の代理：本物の version.dll へ全部の関数を渡す */
#include <windows.h>

static HMODULE g_real;
static FARPROC pf[17];
static const char *names[17] = {
    "GetFileVersionInfoA", "GetFileVersionInfoByHandle", "GetFileVersionInfoExA", "GetFileVersionInfoExW",
    "GetFileVersionInfoSizeA", "GetFileVersionInfoSizeExA", "GetFileVersionInfoSizeExW", "GetFileVersionInfoSizeW",
    "GetFileVersionInfoW", "VerFindFileA", "VerFindFileW", "VerInstallFileA", "VerInstallFileW",
    "VerLanguageNameA", "VerLanguageNameW", "VerQueryValueA", "VerQueryValueW"};

void proxy_init(void)
{
    char path[MAX_PATH];
    UINT n = GetSystemDirectoryA(path, MAX_PATH);
    lstrcpyA(path + n, "\\version.dll");
    g_real = LoadLibraryA(path);
    for (int i = 0; i < 17; i++) pf[i] = g_real ? GetProcAddress(g_real, names[i]) : NULL;
}

void logf_(const char *fmt, ...);
typedef UINT_PTR U;
#define L(i) logf_("ver %s\n", names[i]);
U WINAPI P_GetFileVersionInfoA(U a, U b, U c, U d) { U r = ((U (WINAPI *)(U,U,U,U))pf[0])(a, b, c, d); logf_("InfoA(%s) = %llx\n", (char *)a, (unsigned long long)r); return r; }
U WINAPI P_GetFileVersionInfoByHandle(U a, U b, U c, U d) { L(1) return ((U (WINAPI *)(U,U,U,U))pf[1])(a, b, c, d); }
U WINAPI P_GetFileVersionInfoExA(U a, U b, U c, U d, U e) { L(2) return ((U (WINAPI *)(U,U,U,U,U))pf[2])(a, b, c, d, e); }
U WINAPI P_GetFileVersionInfoExW(U a, U b, U c, U d, U e) { L(3) return ((U (WINAPI *)(U,U,U,U,U))pf[3])(a, b, c, d, e); }
U WINAPI P_GetFileVersionInfoSizeA(U a, U b) { U r = ((U (WINAPI *)(U,U))pf[4])(a, b); logf_("SizeA(%s) = %llx\n", (char *)a, (unsigned long long)r); return r; }
U WINAPI P_GetFileVersionInfoSizeExA(U a, U b, U c) { L(5) return ((U (WINAPI *)(U,U,U))pf[5])(a, b, c); }
U WINAPI P_GetFileVersionInfoSizeExW(U a, U b, U c) { L(6) return ((U (WINAPI *)(U,U,U))pf[6])(a, b, c); }
U WINAPI P_GetFileVersionInfoSizeW(U a, U b) { L(7) return ((U (WINAPI *)(U,U))pf[7])(a, b); }
U WINAPI P_GetFileVersionInfoW(U a, U b, U c, U d) { L(8) return ((U (WINAPI *)(U,U,U,U))pf[8])(a, b, c, d); }
U WINAPI P_VerFindFileA(U a, U b, U c, U d, U e, U f, U g, U h) { L(9) return ((U (WINAPI *)(U,U,U,U,U,U,U,U))pf[9])(a, b, c, d, e, f, g, h); }
U WINAPI P_VerFindFileW(U a, U b, U c, U d, U e, U f, U g, U h) { L(10) return ((U (WINAPI *)(U,U,U,U,U,U,U,U))pf[10])(a, b, c, d, e, f, g, h); }
U WINAPI P_VerInstallFileA(U a, U b, U c, U d, U e, U f, U g, U h) { L(11) return ((U (WINAPI *)(U,U,U,U,U,U,U,U))pf[11])(a, b, c, d, e, f, g, h); }
U WINAPI P_VerInstallFileW(U a, U b, U c, U d, U e, U f, U g, U h) { L(12) return ((U (WINAPI *)(U,U,U,U,U,U,U,U))pf[12])(a, b, c, d, e, f, g, h); }
U WINAPI P_VerLanguageNameA(U a, U b, U c) { L(13) return ((U (WINAPI *)(U,U,U))pf[13])(a, b, c); }
U WINAPI P_VerLanguageNameW(U a, U b, U c) { L(14) return ((U (WINAPI *)(U,U,U))pf[14])(a, b, c); }
U WINAPI P_VerQueryValueA(U a, U b, U c, U d) { L(15) return ((U (WINAPI *)(U,U,U,U))pf[15])(a, b, c, d); }
U WINAPI P_VerQueryValueW(U a, U b, U c, U d) { L(16) return ((U (WINAPI *)(U,U,U,U))pf[16])(a, b, c, d); }
