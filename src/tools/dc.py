# ディレクターズカット版（DC）の表を作る
#   DC の Main_en.txt（UTF-16）の各キーに、旧版の訳（text/ja.json）を当てる。
#     1) 同じキーがあればその訳
#     2) なければ、声の印 {#...} を除いた英語が同じ旧版の項目の訳に、DC の印を付けなおす
#     3) それもなければ「新しい文」として work/dc_new.json に書き出す（あとで訳す）
#   出力: text/ja_dc.json {DCのキー: 日本語}
#   python src/tools/dc.py
import os, re, json, sys
sys.path.insert(0, os.path.dirname(__file__))
from prep import split_english
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
J = lambda *a: os.path.join(ROOT, *a)
DC = r"L:\SteamLibrary\steamapps\common\Wasteland 2 Director's Cut\Build\WL2_Data\StreamingAssets\Localization"
TAG = re.compile(r'^(\{#?[^}]*\})+')


def parse(p, enc):
    d = {}; k = None
    for l in open(p, encoding=enc, errors='replace').read().split('\n'):
        l = l.rstrip('\r')
        if l.startswith('#'): k = l[1:]
        elif l.startswith('=') and k is not None:
            d[k] = l[1:]; k = None
    return d


def disp(k, v):
    return v if v else split_english(k)


def norm(s):
    return re.sub(r'\s+', ' ', TAG.sub('', s)).strip()


def main():
    dc = parse(os.path.join(DC, 'Main_en.txt'), 'utf-16')
    cl = parse(J('work', 'loc', 'Main_en.txt'), 'utf-8')
    ja = json.load(open(J('text', 'ja.json'), encoding='utf-8'))
    # 旧版: 声の印を除いた英語 → 日本語（印を除いたもの）
    by_text = {}
    for k, v in cl.items():
        if k in ja:
            by_text.setdefault(norm(disp(k, v)), TAG.sub('', ja[k]))
    out = {}; new = []; n1 = n2 = 0
    for k, v in dc.items():
        if k in ja and norm(disp(k, v)) == norm(disp(k, cl.get(k, v))):
            out[k] = ja[k]; n1 += 1; continue
        d = disp(k, v)
        t = by_text.get(norm(d))
        if t is not None:
            m = TAG.match(d)
            out[k] = (m.group(0) if m else '') + t; n2 += 1; continue
        if re.search('[A-Za-z]', d) and not re.match(r'^<@(keyboard|mouse_input)>', k):
            new.append({'key': k, 'en': d})
    json.dump(out, open(J('text', 'ja_dc.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    json.dump(new, open(J('work', 'dc_new.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    # 新しい文を訳す単位にする（種類は prep.py と同じ決め方）、出どころのスクリプトは DC の逆コンパイルから
    from prep import COUNT_RE
    from srcmap import LIT, unesc
    import glob
    units = []
    for x in new:
        k, en = x['key'], x['en']
        cat = 'label' if re.match(r'^!?<@~?[^>]+>$', k) else 'count' if COUNT_RE.match(en) else 'text'
        units.append({'key': k, 'en': en, 'cat': cat})
    json.dump(units, open(J('work', 'units_dc.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    want = {x['key'] for x in new}
    sm = json.load(open(J('work', 'srcmap.json'), encoding='utf-8'))
    for f in sorted(glob.glob(J('work', 'decomp_dc', '**', '*.cs'), recursive=True)):
        name = os.path.splitext(os.path.basename(f))[0]
        for m in LIT.finditer(open(f, encoding='utf-8', errors='replace').read()):
            s = unesc(m.group(1))
            if s in want and s not in sm: sm[s] = name
    json.dump(sm, open(J('work', 'srcmap.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('dc', len(dc), 'same key', n1, 'by text', n2, 'new', len(new), 'chars', sum(len(x['en']) for x in new))


if __name__ == '__main__':
    main()
