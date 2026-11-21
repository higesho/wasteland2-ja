# 訳す単位をほどよい大きさに分ける → work/chunks/cNNN.json
#   {"items": [{"k": 番号, "en": 英語, "src": 出どころのスクリプト, "note": 注意}], "glossary": {英: 日}}
#   用語集 = text/glossary_core.json（優先）+ work/gloss_out/*.json → text/glossary.json
import os, re, json, glob
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
J = lambda *a: os.path.join(ROOT, *a)
LIMIT = 18000
STOP = {'General', 'Militant', 'Robot', 'Chinese', 'Rails', 'You Lose', 'Svargas Snake', 'Red', 'Center', 'Base', 'Part', 'Children', 'Church', 'Temple', 'Mayor', 'Militia', 'Silo', 'Angel', 'Servants', 'Jerks'}
COUNT_RE = re.compile(r'^\((a|an|the|some|a pair of|a set of|a box of)?/\[COUNT\]\)\s*(.+?)(\{[MFN]\})?\s*$')


def singular(s):
    # "fl(y/ies)" → "fly"、"round(/s)" → "round"
    return re.sub(r'\(([^()/]*)/[^()]*\)', r'\1', s).strip()


def count_base(en):
    m = COUNT_RE.match(en)
    return singular(m.group(2)), (m.group(3) or '')


def glossary():
    g = {}
    for f in sorted(glob.glob(J('work', 'gloss_out', '*.json'))):
        for k, v in json.load(open(f, encoding='utf-8')).items():
            k = k.strip()
            if not (isinstance(v, str) and v and k): continue
            if re.search(r"'s?$|\?$", k) or k in STOP: continue
            g[k] = v.strip()
    core = {k: v for k, v in json.load(open(J('text', 'glossary_core.json'), encoding='utf-8')).items() if not k.startswith('_')}
    # 中心の用語を含む名前で、その訳語を使っていないものは捨てる（例: コチーズ基地 ≠ コーチス基地）
    for k in list(g):
        for ck, cv in core.items():
            if len(ck) >= 4 and k != ck and re.search(r'\b%s\b' % re.escape(ck), k) and cv not in g[k] and not re.search(r'[a-z]', cv):
                del g[k]; break
    g.update(core)
    json.dump(dict(sorted(g.items())), open(J('text', 'glossary.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    return g


def main(tag=''):
    # tag='' 旧版の全体（c000..）、tag='dc' ディレクターズカット版の新しい文（d000..、番号は 100000 から）
    sfx = '_' + tag if tag else ''
    pre = 'd' if tag else 'c'
    base = 100000 if tag else 0
    g = glossary()
    units = json.load(open(J('work', 'units%s.json' % sfx), encoding='utf-8'))
    src = json.load(open(J('work', 'srcmap.json'), encoding='utf-8'))
    seen = {}
    items = []
    for u in units:
        if u['cat'] == 'key': continue
        en = u['en']; note = None
        if u['cat'] == 'count':
            en, _ = count_base(en)
            note = '物・人・生き物の名前（1つ分の名前だけを訳す。数や冠詞は付けない）'
        elif u['cat'] == 'label':
            note = '会話のキーワードのボタン（短い名詞か短い言い方）。* は付けない'
        key = (en, note)
        if key in seen: continue
        seen[key] = len(items)
        it = {'k': base + len(items), 'en': en}
        if u['key'] in src: it['src'] = src[u['key']]
        if note: it['note'] = note
        items.append(it)
    json.dump(items, open(J('work', 'items%s.json' % sfx), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    keys = sorted((k for k in g if len(k) >= 3), key=len, reverse=True)
    pat = re.compile(r'\b(' + '|'.join(re.escape(k) for k in keys) + r')\b')
    os.makedirs(J('work', 'chunks'), exist_ok=True)
    for f in glob.glob(J('work', 'chunks', pre + '[0-9]*.json')): os.remove(f)
    cur, size, n = [], 0, 0

    def flush():
        nonlocal cur, size, n
        if not cur: return
        text = '\n'.join(x['en'] for x in cur)
        gl = {}
        for m in pat.finditer(text): gl[m.group(1)] = g[m.group(1)]
        json.dump({'items': cur, 'glossary': gl}, open(J('work', 'chunks', pre + '%03d.json' % n), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        n += 1; cur, size = [], 0

    for it in items:
        if size + len(it['en']) > LIMIT: flush()
        cur.append(it); size += len(it['en']) + 20
    flush()
    print('items', len(items), 'chunks', n, 'glossary', len(g))


if __name__ == '__main__':
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else '')
