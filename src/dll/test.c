/* 試験用（ゲームのフォルダに wl2jp_test があるときだけ動く）
 *   - 窓のタイトルを固有の "WL2JP-TEST <pid>" にする（前面の窓ではなくこのタイトルで探して操作する）
 *   - 画面の取得: ゲームのフォルダに wl2jp_shot.req（中身 = 書き出す先の道）を置くと、
 *     次の Present のときに裏の画面を BMP で書き出して .req を消す（PrintWindow では D3D11 の画面が取れないため）
 *   - 入力: 共有メモリ WL2JP_TESTIO {有効, x, y, ボタン} を見て、マウスの位置（GetCursorPos）・ボタン（GetAsyncKeyState/GetKeyState）
 *     と、前面の窓の問い合わせ（GetForegroundWindow/GetActiveWindow/GetFocus）をゲームの窓に見せかける。実際の前面の窓は変えない。
 */
#define COBJMACROS
#include <windows.h>
#include <stdio.h>
#include <d3d11.h>
#include <dxgi.h>
void logf_(const char *fmt, ...);
void *hook5_any(void *target, void *detour);

static wchar_t g_req[MAX_PATH];
static int g_frame;
static HWND g_hwnd;
typedef struct { volatile LONG on, x, y, buttons; } TESTIO;
static TESTIO *g_io;

typedef BOOL (WINAPI *GetCursorPos_t)(LPPOINT);
typedef SHORT (WINAPI *GetKeyState_t)(int);
typedef HWND (WINAPI *GetHwnd_t)(void);
static GetCursorPos_t o_GetCursorPos;
static GetKeyState_t o_GetAsyncKeyState, o_GetKeyState;
static GetHwnd_t o_GetForegroundWindow, o_GetActiveWindow, o_GetFocus;

static BOOL WINAPI h_GetCursorPos(LPPOINT p)
{
    if (g_io && g_io->on && g_hwnd && p) { p->x = g_io->x; p->y = g_io->y; ClientToScreen(g_hwnd, p); return TRUE; }
    return o_GetCursorPos(p);
}
static SHORT btn(int vk, SHORT r)
{
    if (g_io && g_io->on) {
        int b = vk == VK_LBUTTON ? 1 : vk == VK_RBUTTON ? 2 : vk == VK_MBUTTON ? 4 : 0;
        if (b) return (g_io->buttons & b) ? (SHORT)0x8000 : 0;
    }
    return r;
}
static SHORT WINAPI h_GetAsyncKeyState(int vk) { return btn(vk, o_GetAsyncKeyState(vk)); }
static SHORT WINAPI h_GetKeyState(int vk) { return btn(vk, o_GetKeyState(vk)); }
static HWND WINAPI h_GetForegroundWindow(void) { return (g_io && g_io->on && g_hwnd) ? g_hwnd : o_GetForegroundWindow(); }
static HWND WINAPI h_GetActiveWindow(void) { return (g_io && g_io->on && g_hwnd) ? g_hwnd : o_GetActiveWindow(); }
static HWND WINAPI h_GetFocus(void) { return (g_io && g_io->on && g_hwnd) ? g_hwnd : o_GetFocus(); }

static void hook_input(void)
{
    HMODULE u = GetModuleHandleW(L"user32.dll");
    HANDLE m = CreateFileMappingW(INVALID_HANDLE_VALUE, NULL, PAGE_READWRITE, 0, sizeof(TESTIO), L"WL2JP_TESTIO");
    g_io = (TESTIO *)MapViewOfFile(m, FILE_MAP_ALL_ACCESS, 0, 0, sizeof(TESTIO));
    o_GetCursorPos = (GetCursorPos_t)hook5_any(GetProcAddress(u, "GetCursorPos"), (void *)h_GetCursorPos);
    o_GetAsyncKeyState = (GetKeyState_t)hook5_any(GetProcAddress(u, "GetAsyncKeyState"), (void *)h_GetAsyncKeyState);
    o_GetKeyState = (GetKeyState_t)hook5_any(GetProcAddress(u, "GetKeyState"), (void *)h_GetKeyState);
    o_GetForegroundWindow = (GetHwnd_t)hook5_any(GetProcAddress(u, "GetForegroundWindow"), (void *)h_GetForegroundWindow);
    o_GetActiveWindow = (GetHwnd_t)hook5_any(GetProcAddress(u, "GetActiveWindow"), (void *)h_GetActiveWindow);
    o_GetFocus = (GetHwnd_t)hook5_any(GetProcAddress(u, "GetFocus"), (void *)h_GetFocus);
    logf_("input hooks %p %p %p %p %p %p\n", o_GetCursorPos, o_GetAsyncKeyState, o_GetKeyState, o_GetForegroundWindow, o_GetActiveWindow, o_GetFocus);
}

static BOOL CALLBACK enum_cb(HWND h, LPARAM l)
{
    DWORD pid; wchar_t cls[64], t[64], cur[64];
    GetWindowThreadProcessId(h, &pid);
    if (pid != GetCurrentProcessId()) return TRUE;
    GetClassNameW(h, cls, 64);
    if (wcscmp(cls, L"UnityWndClass")) return TRUE;
    swprintf(t, 64, L"WL2JP-TEST %lu", pid);
    GetWindowTextW(h, cur, 64);
    if (wcscmp(cur, t)) { SetWindowTextW(h, t); logf_("title set %ls\n", t); }
    g_hwnd = h;
    return TRUE;
}

static void save_bmp(const wchar_t *path, const unsigned char *px, int pitch, int w, int h, int rgba)
{
    FILE *f = _wfopen(path, L"wb");
    BITMAPFILEHEADER fh = {0}; BITMAPINFOHEADER ih = {0};
    unsigned char *row;
    if (!f) return;
    fh.bfType = 0x4d42; fh.bfOffBits = sizeof fh + sizeof ih; fh.bfSize = fh.bfOffBits + w * h * 4;
    ih.biSize = sizeof ih; ih.biWidth = w; ih.biHeight = -h; ih.biPlanes = 1; ih.biBitCount = 32;
    fwrite(&fh, sizeof fh, 1, f); fwrite(&ih, sizeof ih, 1, f);
    row = (unsigned char *)malloc(w * 4);
    for (int y = 0; y < h; y++) {
        const unsigned char *s = px + y * pitch;
        for (int x = 0; x < w; x++) {
            if (rgba) { row[x*4] = s[x*4+2]; row[x*4+1] = s[x*4+1]; row[x*4+2] = s[x*4]; }
            else { row[x*4] = s[x*4]; row[x*4+1] = s[x*4+1]; row[x*4+2] = s[x*4+2]; }
            row[x*4+3] = 255;
        }
        fwrite(row, w * 4, 1, f);
    }
    free(row); fclose(f);
}

static void capture(IDXGISwapChain *sc)
{
    ID3D11Texture2D *bb = NULL, *st = NULL, *rs = NULL;
    ID3D11Device *dev = NULL; ID3D11DeviceContext *ctx = NULL;
    D3D11_TEXTURE2D_DESC d; D3D11_MAPPED_SUBRESOURCE m;
    wchar_t out[MAX_PATH] = {0};
    FILE *f = _wfopen(g_req, L"rb");
    if (f) { char b[MAX_PATH * 2] = {0}; fread(b, 1, sizeof b - 1, f); fclose(f);
        MultiByteToWideChar(CP_UTF8, 0, b, -1, out, MAX_PATH);
        for (wchar_t *p = out; *p; p++) if (*p == L'\r' || *p == L'\n') *p = 0; }
    DeleteFileW(g_req);
    if (!out[0]) return;
    if (FAILED(IDXGISwapChain_GetBuffer(sc, 0, &IID_ID3D11Texture2D, (void **)&bb))) { logf_("GetBuffer failed\n"); return; }
    ID3D11Texture2D_GetDevice(bb, &dev); ID3D11Device_GetImmediateContext(dev, &ctx);
    ID3D11Texture2D_GetDesc(bb, &d);
    {
        DXGI_FORMAT fmt = d.Format;
        ID3D11Texture2D *src = bb;
        if (d.SampleDesc.Count > 1) {
            D3D11_TEXTURE2D_DESC r = d; r.SampleDesc.Count = 1; r.SampleDesc.Quality = 0; r.BindFlags = 0; r.MiscFlags = 0;
            ID3D11Device_CreateTexture2D(dev, &r, NULL, &rs);
            ID3D11DeviceContext_ResolveSubresource(ctx, (ID3D11Resource *)rs, 0, (ID3D11Resource *)bb, 0, fmt);
            src = rs;
        }
        d.SampleDesc.Count = 1; d.SampleDesc.Quality = 0; d.Usage = D3D11_USAGE_STAGING; d.BindFlags = 0;
        d.CPUAccessFlags = D3D11_CPU_ACCESS_READ; d.MiscFlags = 0;
        if (SUCCEEDED(ID3D11Device_CreateTexture2D(dev, &d, NULL, &st))) {
            ID3D11DeviceContext_CopyResource(ctx, (ID3D11Resource *)st, (ID3D11Resource *)src);
            if (SUCCEEDED(ID3D11DeviceContext_Map(ctx, (ID3D11Resource *)st, 0, D3D11_MAP_READ, 0, &m))) {
                int rgba = fmt == DXGI_FORMAT_R8G8B8A8_UNORM || fmt == DXGI_FORMAT_R8G8B8A8_UNORM_SRGB;
                save_bmp(out, (unsigned char *)m.pData, m.RowPitch, d.Width, d.Height, rgba);
                ID3D11DeviceContext_Unmap(ctx, (ID3D11Resource *)st, 0);
                logf_("shot %ls %ux%u fmt %d\n", out, d.Width, d.Height, fmt);
            }
            ID3D11Texture2D_Release(st);
        }
    }
    if (rs) ID3D11Texture2D_Release(rs);
    ID3D11DeviceContext_Release(ctx); ID3D11Device_Release(dev); ID3D11Texture2D_Release(bb);
}

typedef HRESULT (STDMETHODCALLTYPE *Present_t)(IDXGISwapChain *, UINT, UINT);
static Present_t o_Present;
static HRESULT STDMETHODCALLTYPE h_Present(IDXGISwapChain *sc, UINT a, UINT b)
{
    if ((++g_frame & 7) == 0 && GetFileAttributesW(g_req) != INVALID_FILE_ATTRIBUTES) capture(sc);
    return o_Present(sc, a, b);
}

static void hook_present(void)
{
    typedef HRESULT (WINAPI *Create_t)(IDXGIAdapter *, D3D_DRIVER_TYPE, HMODULE, UINT, const D3D_FEATURE_LEVEL *, UINT, UINT,
                                       const DXGI_SWAP_CHAIN_DESC *, IDXGISwapChain **, ID3D11Device **, D3D_FEATURE_LEVEL *, ID3D11DeviceContext **);
    HMODULE d3d = GetModuleHandleW(L"d3d11.dll");
    Create_t create = (Create_t)GetProcAddress(d3d, "D3D11CreateDeviceAndSwapChain");
    HWND w = CreateWindowExW(0, L"STATIC", L"wl2jp-dummy", WS_OVERLAPPED, 0, 0, 64, 64, NULL, NULL, NULL, NULL);
    DXGI_SWAP_CHAIN_DESC sd = {0};
    IDXGISwapChain *sc = NULL; ID3D11Device *dev = NULL; ID3D11DeviceContext *ctx = NULL;
    sd.BufferCount = 1; sd.BufferDesc.Width = 64; sd.BufferDesc.Height = 64; sd.BufferDesc.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
    sd.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT; sd.OutputWindow = w; sd.SampleDesc.Count = 1; sd.Windowed = TRUE;
    if (!create || FAILED(create(NULL, D3D_DRIVER_TYPE_HARDWARE, NULL, 0, NULL, 0, D3D11_SDK_VERSION, &sd, &sc, &dev, NULL, &ctx))) {
        logf_("dummy swapchain failed\n"); DestroyWindow(w); return;
    }
    {
        void **vt = *(void ***)sc;
        o_Present = (Present_t)hook5_any(vt[8], (void *)h_Present);
        logf_("present hook %p\n", o_Present);
    }
    IDXGISwapChain_Release(sc); ID3D11DeviceContext_Release(ctx); ID3D11Device_Release(dev);
    DestroyWindow(w);
}

static DWORD WINAPI test_thread(LPVOID p)
{
    int hooked = 0;
    for (;;) {
        EnumWindows(enum_cb, 0);
        if (!hooked && GetModuleHandleW(L"d3d11.dll")) { Sleep(500); hook_present(); hooked = 1; }
        Sleep(500);
    }
    return 0;
}

void test_init(void)
{
    wchar_t exe[MAX_PATH], *s;
    GetModuleFileNameW(NULL, exe, MAX_PATH);
    s = wcsrchr(exe, L'\\'); if (s) s[1] = 0;
    swprintf(g_req, MAX_PATH, L"%lswl2jp_shot.req", exe);
    hook_input();
    CreateThread(NULL, 0, test_thread, NULL, 0, NULL);
}
