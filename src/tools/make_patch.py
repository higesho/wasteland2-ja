# 日本語の表を DLL に埋め込む形にする
#   旧版: text/ja.json → build/classic/main.lz
#   ディレクターズカット版: text/ja_dc.json + text/ja_dcnew.json（+ text/fix_dc.json）→ build/dc/main.lz
#   どちらも Defines の上書き（[COUNT] を数字だけにする）→ defs.lz
#   形: u32 元の大きさ + LZ4 ブロック（store_size=False）。中身は「#キー / =日本語」の並び（UTF-8）
import os, json, struct
import lz4.block
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
J = lambda *a: os.path.join(ROOT, *a)
DEFINES = '* Wasteland 2 日本語化: 数の言い方は数字だけにする\r\n#[COUNT]\r\n=[.#]\r\n'


def pack(raw, out):
    c = lz4.block.compress(raw, mode='high_compression', compression=12, store_size=False)
    open(out, 'wb').write(struct.pack('<I', len(raw)) + c)
    return len(c)


def esc(s):
    return s.replace('\r\n', '\\n').replace('\n', '\\n').replace('\r', '\\n')


def load(*names):
    d = {}
    for n in names:
        p = J('text', n)
        if os.path.exists(p): d.update(json.load(open(p, encoding='utf-8')))
    return d


def build(ja, sub):
    os.makedirs(J('build', sub), exist_ok=True)
    lines = ['* Wasteland 2 日本語化']
    for k, v in ja.items():
        lines.append('#' + esc(k)); lines.append('=' + esc(v)); lines.append('')
    raw = ('\r\n'.join(lines) + '\r\n').encode('utf-8')
    n = pack(raw, J('build', sub, 'main.lz'))
    pack(DEFINES.encode('utf-8'), J('build', sub, 'defs.lz'))
    print(sub, 'entries', len(ja), 'raw', len(raw), 'lz4', n)


def main():
    build(load('ja.json'), 'classic')
    dc = load('ja_dc.json', 'ja_dcnew.json', 'fix_dc.json')
    # 手直し（text/fix.json）は旧版の表に入っているので、同じキーがあれば DC にも写す
    classic = load('ja.json'); fix = load('fix.json')
    for k in fix:
        if k in dc: dc[k] = classic.get(k, fix[k])
    build(dc, 'dc')


if __name__ == '__main__':
    main()
