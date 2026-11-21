/* Wasteland 2 日本語化：version.dll の代理
 *   ゲームは WL2_Data/Localization/Main_en.txt があれば英語の表を上書きする。
 *   この DLL は、そのファイルを開こうとしたときに、DLL に埋め込んだ日本語の表（作業用フォルダに書き出したもの）を渡す。
 *   ゲームのフォルダには何も書かない。DLL を消せば英語に戻る。
 *   試験用: ゲームのフォルダに wl2jp_test があれば、窓のタイトルを "WL2JP-TEST <pid>" にし、wl2jp_log.txt に記録する。
 */
#include <windows.h>
#include <stdio.h>
#include <stdarg.h>
#include "resource.h"

void proxy_init(void);
int lz4_decompress(const unsigned char *src, int srclen, unsigned char *dst, int dstlen);
void test_init(void);

static int g_test;
static FILE *g_log;
static CRITICAL_SECTION g_logcs;
static wchar_t g_cache[MAX_PATH];      /* 日本語の表（書き出したもの） */
static wchar_t g_defs[MAX_PATH];       /* Defines_en の差し替え（あれば） */
static wchar_t g_dir[MAX_PATH];        /* 作業用フォルダ %LOCALAPPDATA%\WL2_JP */

void logf_(const char *fmt, ...)
{
    if (!g_log) return;
    va_list ap; va_start(ap, fmt);
    EnterCriticalSection(&g_logcs);
    vfprintf(g_log, fmt, ap); fflush(g_log);
    LeaveCriticalSection(&g_logcs);
    va_end(ap);
}

#ifdef _WIN64
/* ---- 64 ビット（ディレクターズカット版）: MinHook でフックする ---- */
#include "minhook/include/MinHook.h"
static void *hook5(void *target, void *detour)
{
    static int inited;
    void *orig = NULL;
    if (!target) return NULL;
    if (!inited) { MH_Initialize(); inited = 1; }
    if (MH_CreateHook(target, detour, &orig) != MH_OK || MH_EnableHook(target) != MH_OK) {
        logf_("MinHook failed %p\n", target); return NULL;
    }
    return orig;
}
#else
/* ---- 32 ビット（旧版）: 5 バイトの飛び先を書きかえるフック（関数の頭が mov edi,edi / push ebp / mov ebp,esp のときだけ） ---- */
static void *hook5(void *target, void *detour)
{
    unsigned char *p = (unsigned char *)target, *tr;
    DWORD old;
    if (!p) return NULL;
    if (!(p[0] == 0x8b && p[1] == 0xff && p[2] == 0x55 && p[3] == 0x8b && p[4] == 0xec)) {
        logf_("hook5: unexpected prologue %02x %02x %02x %02x %02x\n", p[0], p[1], p[2], p[3], p[4]);
        return NULL;
    }
    tr = (unsigned char *)VirtualAlloc(NULL, 16, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    memcpy(tr, p, 5);
    tr[5] = 0xe9; *(int *)(tr + 6) = (int)(p + 5) - (int)(tr + 10);
    VirtualProtect(p, 5, PAGE_EXECUTE_READWRITE, &old);
    p[0] = 0xe9; *(int *)(p + 1) = (int)detour - (int)(p + 5);
    VirtualProtect(p, 5, old, &old);
    FlushInstructionCache(GetCurrentProcess(), p, 5);
    return tr;
}
#endif

void *hook5_any(void *target, void *detour) { return hook5(target, detour); }

/* ---- 道の名前の置きかえ ---- */
static int ends_with(const wchar_t *s, const wchar_t *tail)
{
    size_t a = wcslen(s), b = wcslen(tail);
    if (a < b) return 0;
    for (size_t i = 0; i < b; i++) {
        wchar_t c = s[a - b + i], d = tail[i];
        if (c == L'/') c = L'\\';
        if (towlower(c) != towlower(d)) return 0;
    }
    return 1;
}

typedef HANDLE (WINAPI *CreateFileW_t)(LPCWSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
typedef BOOL (WINAPI *GetFileAttributesExW_t)(LPCWSTR, GET_FILEEX_INFO_LEVELS, LPVOID);
typedef DWORD (WINAPI *GetFileAttributesW_t)(LPCWSTR);
static CreateFileW_t o_CreateFileW;
static GetFileAttributesExW_t o_GetFileAttributesExW;
static GetFileAttributesW_t o_GetFileAttributesW;

static const wchar_t *redirect(const wchar_t *path)
{
    if (!path) return path;
    /* WL2_Data\Localization\ は上書き用の置き場（ディレクターズカット版の StreamingAssets\Localization\ は本体なので触らない） */
    if (g_cache[0] && ends_with(path, L"\\WL2_Data\\Localization\\Main_en.txt")) return g_cache;
    if (g_defs[0] && ends_with(path, L"\\WL2_Data\\Localization\\Defines_en.txt")) return g_defs;
    /* ディレクターズカット版にはこのフォルダがなく、Mono はファイルを開く前にフォルダの有無を見るので、作業用フォルダを見せる */
    if (g_dir[0] && (ends_with(path, L"\\WL2_Data\\Localization") || ends_with(path, L"\\WL2_Data\\Localization\\"))) {
        DWORD a = o_GetFileAttributesW ? o_GetFileAttributesW(path) : INVALID_FILE_ATTRIBUTES;
        if (a == INVALID_FILE_ATTRIBUTES) return g_dir;
    }
    return path;
}


static HANDLE WINAPI h_CreateFileW(LPCWSTR p, DWORD a, DWORD s, LPSECURITY_ATTRIBUTES sa, DWORD c, DWORD f, HANDLE t)
{
    const wchar_t *q = redirect(p);
    if (q != p) logf_("CreateFileW %ls -> %ls\n", p, q);
    return o_CreateFileW(q, a, s, sa, c, f, t);
}
static BOOL WINAPI h_GetFileAttributesExW(LPCWSTR p, GET_FILEEX_INFO_LEVELS l, LPVOID i)
{
    const wchar_t *q = redirect(p);
    if (q != p) logf_("GetFileAttributesExW %ls -> %ls\n", p, q);
    return o_GetFileAttributesExW(q, l, i);
}
static DWORD WINAPI h_GetFileAttributesW(LPCWSTR p)
{
    const wchar_t *q = redirect(p);
    if (q != p) logf_("GetFileAttributesW %ls -> %ls\n", p, q);
    return o_GetFileAttributesW(q);
}

/* ---- 埋め込んだ表を作業用フォルダに書き出す ---- */
static unsigned fnv(const unsigned char *p, size_t n)
{
    unsigned h = 2166136261u;
    while (n--) { h ^= *p++; h *= 16777619u; }
    return h;
}

static int write_res(int id, const wchar_t *name, wchar_t *out)
{
    HMODULE me; HRSRC r; HGLOBAL g; const unsigned char *d; DWORD n; unsigned raw;
    wchar_t dir[MAX_PATH];
    GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT, (LPCWSTR)write_res, &me);
    r = FindResourceW(me, MAKEINTRESOURCEW(id), (LPCWSTR)RT_RCDATA);
    if (!r) return 0;
    g = LoadResource(me, r); d = (const unsigned char *)LockResource(g); n = SizeofResource(me, r);
    if (n < 8) return 0;
    raw = *(const unsigned *)d;
    if (!GetEnvironmentVariableW(L"LOCALAPPDATA", dir, MAX_PATH)) return 0;
    wcscat(dir, L"\\WL2_JP");
    CreateDirectoryW(dir, NULL);
#ifdef WL2DC
    wcscat(dir, L"\\dc");
#else
    wcscat(dir, L"\\classic");
#endif
    CreateDirectoryW(dir, NULL);
    wcscpy(g_dir, dir);
    swprintf(out, MAX_PATH, L"%ls\\%ls_%08x.txt", dir, name, fnv(d, n));
    if (GetFileAttributesW(out) != INVALID_FILE_ATTRIBUTES) return 1;
    {
        /* 前の版の書き出しが残っていれば消す */
        WIN32_FIND_DATAW fd; HANDLE fh; wchar_t pat[MAX_PATH], old[MAX_PATH];
        swprintf(pat, MAX_PATH, L"%ls\\%ls_*.txt", dir, name);
        fh = FindFirstFileW(pat, &fd);
        if (fh != INVALID_HANDLE_VALUE) {
            do { swprintf(old, MAX_PATH, L"%ls\\%ls", dir, fd.cFileName); DeleteFileW(old); } while (FindNextFileW(fh, &fd));
            FindClose(fh);
        }
    }
    {
        unsigned char *buf = (unsigned char *)malloc(raw);
        int m = lz4_decompress(d + 4, n - 4, buf, raw);
        HANDLE h; DWORD w;
        wchar_t tmp[MAX_PATH];
        if (m != (int)raw) { logf_("lz4 failed %d %u\n", m, raw); free(buf); out[0] = 0; return 0; }
        swprintf(tmp, MAX_PATH, L"%ls.tmp", out);
        h = CreateFileW(tmp, GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, 0, NULL);
        if (h == INVALID_HANDLE_VALUE) { free(buf); out[0] = 0; return 0; }
        WriteFile(h, buf, raw, &w, NULL); CloseHandle(h); free(buf);
        if (!MoveFileExW(tmp, out, MOVEFILE_REPLACE_EXISTING)) { DeleteFileW(tmp); }
    }
    return GetFileAttributesW(out) != INVALID_FILE_ATTRIBUTES;
}

static void init(void)
{
    wchar_t exe[MAX_PATH], *s;
    GetModuleFileNameW(NULL, exe, MAX_PATH);
    s = wcsrchr(exe, L'\\'); if (s) s[1] = 0;
    {
        wchar_t f[MAX_PATH];
        swprintf(f, MAX_PATH, L"%lswl2jp_test", exe);
        g_test = GetFileAttributesW(f) != INVALID_FILE_ATTRIBUTES;
        if (g_test) {
            swprintf(f, MAX_PATH, L"%lswl2jp_log.txt", exe);
            g_log = _wfopen(f, L"w");
        }
    }
    if (!write_res(IDR_MAIN, L"Main_en", g_cache)) g_cache[0] = 0;
    if (!write_res(IDR_DEFS, L"Defines_en", g_defs)) g_defs[0] = 0;
    logf_("cache %ls\ndefs %ls\n", g_cache, g_defs);
    {
        HMODULE kb = GetModuleHandleW(L"kernelbase.dll");
        o_CreateFileW = (CreateFileW_t)hook5(GetProcAddress(kb, "CreateFileW"), h_CreateFileW);
        o_GetFileAttributesExW = (GetFileAttributesExW_t)hook5(GetProcAddress(kb, "GetFileAttributesExW"), h_GetFileAttributesExW);
        o_GetFileAttributesW = (GetFileAttributesW_t)hook5(GetProcAddress(kb, "GetFileAttributesW"), h_GetFileAttributesW);
        logf_("hooks %p %p %p\n", o_CreateFileW, o_GetFileAttributesExW, o_GetFileAttributesW);
    }
    if (g_test) test_init();
}

BOOL WINAPI DllMain(HINSTANCE h, DWORD r, LPVOID v)
{
    if (r == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(h);
        InitializeCriticalSection(&g_logcs);
        proxy_init();
        init();
    }
    return TRUE;
}
