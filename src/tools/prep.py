# 英語の表（work/loc/Main_en.txt）から訳す単位を作る → work/units.json
#   各項目: {"key": キー, "en": 表示される英語（訳す対象）, "cat": 種類}
#   種類: count = "(a/[COUNT]) X(/s)" 形の名前（名前だけ訳して型にはめる）
#         label = "<@Label>" だけのキーワード（訳/英語 の形にする）
#         text  = そのほか
import os, re, json, collections
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def parse(p):
    d = {}; k = None
    for l in open(p, encoding='utf-8', errors='replace').read().split('\n'):
        l = l.rstrip('\r')
        if l.startswith('#'): k = l[1:]
        elif l.startswith('=') and k is not None:
            d[k] = l[1:]; k = None
    return d


def split_english(m):
    """Language.SplitEnglishText と同じ"""
    if not m: return ''
    n = 1 if m[0] == '!' else 0
    if n >= len(m): return ''
    flag = m[n] == '<'
    n2 = m.find('>'); n3 = m.find('=')
    n4 = n3 + 1
    if n3 < 0 or (flag and n3 >= n2):
        n4 = n + (2 if flag else 0)
        if n4 < len(m) and m[n4] == '~': n4 += 1
    n5 = (n2 - n4) if flag else (len(m) - n4)
    if flag and len(m) > n2 + 1: return m[n2 + 1:]
    if n5 > 0: return m[n4:n4 + n5]
    return ''


COUNT_RE = re.compile(r'^\((a|an|the|some|a pair of|a set of|a box of)?/\[COUNT\]\)\s*(.+?)(\{[MFN]\})?\s*$')


def main():
    en = parse(os.path.join(ROOT, 'work', 'loc', 'Main_en.txt'))
    units = []
    cats = collections.Counter()
    for k, v in en.items():
        src = v if v else split_english(k)
        if not src.strip():
            continue
        if not re.search(r'[A-Za-z]', src):
            continue
        cat = 'text'
        if re.match(r'^!?<@~?[^>]+>$', k): cat = 'label'
        elif COUNT_RE.match(src): cat = 'count'
        elif re.match(r'^<@(keyboard|mouse_input)>', k): cat = 'key'
        units.append({'key': k, 'en': src, 'cat': cat})
        cats[cat] += 1
    json.dump(units, open(os.path.join(ROOT, 'work', 'units.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    uniq = len({u['en'] for u in units})
    print(len(units), 'units', uniq, 'unique', dict(cats), 'chars', sum(len(u['en']) for u in units))


if __name__ == '__main__':
    main()
