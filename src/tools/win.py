# 試験用：Wasteland 2 を動かす。窓は固有のタイトル "WL2JP-TEST <pid>" で探す（前面の窓は使わない）
#   python src/tools/win.py start [classic|dc] [en]   build/test/<版>/version.dll（試験版）を入れて起動（en: DLL なし）
#   python src/tools/win.py stop
#   python src/tools/win.py shot NAME     PrintWindow で capture/NAME.png
#   python src/tools/win.py click X Y [right] / move X Y / key K.. / type TEXT / wait MS
#   座標はクライアント領域のピクセル（shot の画像と同じ）
import sys, os, time, subprocess, shutil, ctypes, ctypes.wintypes as W
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
GAMES = {'classic': r'L:\SteamLibrary\steamapps\common\Wasteland 2\Build',
         'dc': r"L:\SteamLibrary\steamapps\common\Wasteland 2 Director's Cut\Build"}
VERF = os.path.join(ROOT, 'test', 'ver.txt')     # いま動かしている版（start で決める）
VER = open(VERF).read().strip() if os.path.exists(VERF) else 'classic'
GAME = GAMES[VER]
u = ctypes.windll.user32
u.SetProcessDPIAware()
VK = {'esc': 0x1b, 'enter': 0x0d, 'space': 0x20, 'tab': 0x09, 'back': 0x08, 'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
      'shift': 0x10, 'ctrl': 0x11, 'alt': 0x12, 'home': 0x24, 'end': 0x23, 'pgup': 0x21, 'pgdn': 0x22}
for i in range(1, 13): VK['f%d' % i] = 0x6f + i
PIDF = os.path.join(ROOT, 'test', 'pid.txt')


def hwnd():
    hw = []
    @ctypes.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
    def cb(h, l):
        b = ctypes.create_unicode_buffer(128); u.GetWindowTextW(h, b, 128)
        if b.value.startswith('WL2JP-TEST '):
            p = W.DWORD(); u.GetWindowThreadProcessId(h, ctypes.byref(p))
            if b.value == 'WL2JP-TEST %d' % p.value: hw.append((h, p.value))
        return True
    u.EnumWindows(cb, 0)
    if not hw: raise SystemExit('WL2JP-TEST window not found')
    return hw[0]


def client(h):
    r = W.RECT(); u.GetClientRect(h, ctypes.byref(r)); return r.right, r.bottom


def shot(name):
    # DLL に頼んで Present のときに裏の画面を BMP で書いてもらう（PrintWindow では D3D11 の画面が取れない）
    from PIL import Image
    hwnd()
    bmp = os.path.join(ROOT, 'test', 'shot.bmp')
    if os.path.exists(bmp): os.remove(bmp)
    req = os.path.join(GAME, 'wl2jp_shot.req')
    open(req, 'w', encoding='utf-8').write(bmp)
    for i in range(100):
        time.sleep(0.1)
        if not os.path.exists(req) and os.path.exists(bmp): break
    else:
        raise SystemExit('shot timeout')
    time.sleep(0.2)
    im = Image.open(bmp).convert('RGB')
    p = os.path.join(ROOT, 'capture', name + '.png'); im.save(p); print(p, im.size)


def lp(x, y): return (int(y) << 16) | (int(x) & 0xffff)


def start(ver, variant):
    global GAME
    GAME = GAMES[ver]; open(VERF, 'w').write(ver)
    dst = os.path.join(GAME, 'version.dll')
    if os.path.exists(dst): os.remove(dst)
    if variant != 'en': shutil.copy(os.path.join(ROOT, 'build', 'test', ver, 'version.dll'), dst)   # 試験版（build.bat test）
    open(os.path.join(GAME, 'wl2jp_test'), 'w').close()
    subprocess.Popen([os.path.join(GAME, 'WL2.exe'), '-screen-width', '1280', '-screen-height', '720', '-screen-fullscreen', '0'], cwd=GAME)
    for i in range(120):
        time.sleep(0.5)
        try:
            h, p = hwnd(); open(PIDF, 'w').write(str(p)); print('pid', p); return
        except SystemExit:
            pass
    print('window not found yet')


def stop():
    try:
        p = int(open(PIDF).read())
        subprocess.call(['taskkill', '/PID', str(p), '/F'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(e)
    time.sleep(1)


def main():
    a = sys.argv[1:]
    c = a[0]
    if c == 'start': start(a[1] if len(a) > 1 else 'classic', a[2] if len(a) > 2 else 'jp'); return
    if c == 'stop': stop(); return
    if c == 'shot': shot(a[1]); return
    h, _ = hwnd()
    # Unity は窓が有効になっていないと入力を捨てるので、先に有効化の知らせを送る（前面には出さない）
    u.PostMessageW(h, 0x1c, 1, 0); u.PostMessageW(h, 0x6, 1, 0); u.PostMessageW(h, 0x7, 0, 0); time.sleep(0.15)
    if c in ('click', 'move'):
        # マウスは DLL の共有メモリ WL2JP_TESTIO {有効, x, y, ボタン} で見せかける（本物のカーソルは動かさない）
        import mmap, struct
        io = mmap.mmap(-1, 16, tagname='WL2JP_TESTIO')
        x, y = int(a[1]), int(a[2])
        struct.pack_into('<iiii', io, 0, 1, x, y, 0)
        u.PostMessageW(h, 0x200, 0, lp(x, y)); time.sleep(0.3)
        if c == 'click':
            right = len(a) > 3 and a[3] == 'right'
            dn, up, mk, b = (0x204, 0x205, 2, 2) if right else (0x201, 0x202, 1, 1)
            struct.pack_into('<i', io, 12, b); u.PostMessageW(h, dn, mk, lp(x, y)); time.sleep(0.15)
            struct.pack_into('<i', io, 12, 0); u.PostMessageW(h, up, 0, lp(x, y)); time.sleep(0.3)
    elif c == 'drag':
        # drag X1 Y1 X2 Y2（左ボタンを押したまま動かす）
        import mmap, struct
        io = mmap.mmap(-1, 16, tagname='WL2JP_TESTIO')
        x1, y1, x2, y2 = [int(v) for v in a[1:5]]
        struct.pack_into('<iiii', io, 0, 1, x1, y1, 0); u.PostMessageW(h, 0x200, 0, lp(x1, y1)); time.sleep(0.3)
        struct.pack_into('<i', io, 12, 1); u.PostMessageW(h, 0x201, 1, lp(x1, y1)); time.sleep(0.2)
        for i in range(1, 11):
            x = x1 + (x2 - x1) * i // 10; y = y1 + (y2 - y1) * i // 10
            struct.pack_into('<ii', io, 4, x, y); u.PostMessageW(h, 0x200, 1, lp(x, y)); time.sleep(0.05)
        time.sleep(0.2)
        struct.pack_into('<i', io, 12, 0); u.PostMessageW(h, 0x202, 0, lp(x2, y2)); time.sleep(0.3)
    elif c == 'scroll':
        # scroll X Y N（N>0 で下へ）。ホイールは画面座標を渡す
        import mmap, struct
        io = mmap.mmap(-1, 16, tagname='WL2JP_TESTIO')
        x, y, n = int(a[1]), int(a[2]), int(a[3])
        struct.pack_into('<iiii', io, 0, 1, x, y, 0)
        u.PostMessageW(h, 0x200, 0, lp(x, y)); time.sleep(0.2)
        pt = W.POINT(x, y); u.ClientToScreen(h, ctypes.byref(pt))
        d = -120 if n > 0 else 120
        for i in range(abs(n)):
            u.PostMessageW(h, 0x20a, (d & 0xffff) << 16, lp(pt.x, pt.y)); time.sleep(0.12)
    elif c == 'key':
        for k in a[1:]:
            if k.startswith('wait:'): time.sleep(float(k[5:])); continue
            vk = VK.get(k.lower()) or ord(k.upper())
            sc = u.MapVirtualKeyW(vk, 0)
            u.PostMessageW(h, 0x100, vk, 1 | (sc << 16)); time.sleep(0.1)
            if len(k) == 1: u.PostMessageW(h, 0x102, ord(k), 1 | (sc << 16)); time.sleep(0.05)
            u.PostMessageW(h, 0x101, vk, 0xc0000001 | (sc << 16)); time.sleep(0.2)
    elif c == 'type':
        for ch in ' '.join(a[1:]): u.PostMessageW(h, 0x102, ord(ch), 1); time.sleep(0.06)
    elif c == 'wait':
        time.sleep(int(a[1]) / 1000)


if __name__ == '__main__':
    main()
