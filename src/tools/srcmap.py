# 文字列がどのスクリプト（逆コンパイルした .cs）に出てくるかを調べる → work/srcmap.json {キー: ファイル名}
import os, re, json, glob, collections
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
LIT = re.compile(r'"((?:[^"\\\n]|\\.)*)"')
ESC = {'n': '\n', 't': '\t', 'r': '\r', '"': '"', "'": "'", '\\': '\\', '0': '\0'}


def unesc(s):
    out = []; i = 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i + 1 < len(s):
            d = s[i + 1]
            if d == 'u':
                out.append(chr(int(s[i + 2:i + 6], 16))); i += 6; continue
            out.append(ESC.get(d, d)); i += 2; continue
        out.append(c); i += 1
    return ''.join(out)


def main():
    idx = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'work', 'decomp', '**', '*.cs'), recursive=True)):
        name = os.path.splitext(os.path.basename(f))[0]
        for m in LIT.finditer(open(f, encoding='utf-8', errors='replace').read()):
            s = unesc(m.group(1))
            idx.setdefault(s, name)
    units = json.load(open(os.path.join(ROOT, 'work', 'units.json'), encoding='utf-8'))
    out = {}
    for u in units:
        k = u['key']
        f = idx.get(k) or idx.get(k.replace('\\n', '\n'))
        if f: out[k] = f
    json.dump(out, open(os.path.join(ROOT, 'work', 'srcmap.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('mapped', len(out), 'of', len(units))
    c = collections.Counter(out.values())
    print(len(c), c.most_common(15))


if __name__ == '__main__':
    main()
