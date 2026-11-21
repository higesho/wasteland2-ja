# 訳をまとめて text/ja.json {キー: 日本語} を作る
#   work/units.json（キーと英語）+ work/items.json（訳す単位）+ work/out/c*.json（訳）+ text/fix.json（手直し、キー → 日本語）
#   - *日本語/English* → *<@ラベル>日本語/English*（日本語の語順でキーワードの順が変わっても、ラベルを英語の側から取れるように）
#   - キーワードだけの項目（<@Label>）→ 日本語/英語（打ち込みは英語でも通る）
#   - (a/[COUNT]) X(/s) の名前 → 日本語(/×[COUNT])
import os, re, json, glob, sys
sys.path.insert(0, os.path.dirname(__file__))
from chunk import count_base
from check import check
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
J = lambda *a: os.path.join(ROOT, *a)
STAR = re.compile(r'\*([^*]+)\*')


def star_label(e):
    """英語の *…* の中身からラベルを取る（Drama.SplitKeywordLabelAndTextVariants と同じ考え）"""
    if e.startswith('<@'):
        i = e.find('>')
        lab = e[2:i]
        return lab.split('=')[0], e[i + 1:]
    return e.split('/')[0], e


def fix_stars(en, ja):
    en = en.replace('**', '\x01'); ja = ja.replace('**', '\x01')
    return _fix_stars(en, ja).replace('\x01', '**')


def _fix_stars(en, ja):
    se = [s for s in STAR.findall(en)]
    pool = {s.lower(): s for s in se}

    def rep(m):
        s = m.group(1)
        if '/' not in s: return m.group(0)
        jp, e = s.split('/', 1)
        orig = pool.get(e.strip().lower())
        if orig is None: return m.group(0)
        lab, etext = star_label(orig)
        etext = etext.replace('&', '')
        return '*<@%s>%s/%s*' % (lab, jp.strip(), etext)
    return STAR.sub(rep, ja)


def load_out(pre='c'):
    out = {}
    for f in sorted(glob.glob(J('work', 'out', pre + '*.json'))):   # cr*.json（直し）は後に読む
        try:
            d = json.load(open(f, encoding='utf-8'))
        except Exception as e:
            print('bad json', f, e); continue
        for k, v in d.items():
            if isinstance(v, str): out[int(k)] = v
    return out


def add_star_en(en, ja):
    # *日本語* に英語の写しがなければ、同じ順番の英語の *キーワード* を付ける（数が同じときだけ）
    E = en.replace('**', ''); T = ja.replace('**', '')
    se = re.findall(r'\*([^*]+)\*', E); sj = re.findall(r'\*([^*]+)\*', T)
    if len(se) != len(sj) or all('/' in x for x in sj): return ja
    out = []; pos = 0
    for m, e in zip(re.finditer(r'\*([^*]+)\*', T), se):
        x = m.group(1)
        out.append(T[pos:m.start()]); out.append('*' + (x if '/' in x else x + '/' + e.strip()) + '*'); pos = m.end()
    out.append(T[pos:])
    return ''.join(out).replace('', '**')


def main(tag=''):
    # tag='' 旧版の全体、tag='dc' ディレクターズカット版で新しく増えた文
    sfx = '_' + tag if tag else ''
    units = json.load(open(J('work', 'units%s.json' % sfx), encoding='utf-8'))
    items = json.load(open(J('work', 'items%s.json' % sfx), encoding='utf-8'))
    idx = {(it['en'], it.get('note')): it['k'] for it in items}
    out = load_out('d' if tag else 'c')
    fixp = J('text', 'fix.json')
    fix = json.load(open(fixp, encoding='utf-8')) if os.path.exists(fixp) else {}
    ja = {}; bad = []; missing = 0
    for u in units:
        k = u['key']
        if u['cat'] == 'key': continue
        if k in fix:
            ja[k] = fix_stars(u['en'], fix[k]) if u['cat'] == 'text' else fix[k]; continue
        if u['cat'] == 'count':
            base, meta = count_base(u['en'])
            t = out.get(idx.get((base, '物・人・生き物の名前（1つ分の名前だけを訳す。数や冠詞は付けない）')))
            if t is None: missing += 1; continue
            t = t.strip().replace('(', '（').replace(')', '）').replace('/', '／')
            ja[k] = t + '(/×[COUNT])' + meta
            continue
        if u['cat'] == 'label':
            t = out.get(idx.get((u['en'], '会話のキーワードのボタン（短い名詞か短い言い方）。* は付けない')))
            if t is None: missing += 1; continue
            t = t.strip().strip('*').replace('／', '/')
            ja[k] = t + '/' + u['en']
            continue
        i = idx.get((u['en'], None))
        t = out.get(i)
        if t is None: missing += 1; continue
        # 文頭の {WL2_...} {#...} の印が落ちていたら戻す
        m = re.match(r'^(\{[^}]*\})+', u['en'])
        if m and not t.startswith(m.group(0)):
            t = m.group(0) + re.sub(r'^(\{[^}]*\})+', '', t)
        # **咳/cough** のように飾りの星にまで英語を付けたものは日本語だけにする
        t = re.sub(r'\*\*([^*/]+)/[^*]*\*\*', r'**\1**', t)
        t = add_star_en(u['en'], t)
        e = check(u['en'], t)
        if e: bad.append({'k': i, 'key': k, 'en': u['en'], 'ja': t, 'err': e})
        ja[k] = fix_stars(u['en'], t)
    json.dump(ja, open(J('text', 'ja%s.json' % ('_dcnew' if tag else '')), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    json.dump(bad, open(J('work', 'bad%s.json' % sfx), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('entries', len(ja), 'missing', missing, 'bad', len(bad))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '')
