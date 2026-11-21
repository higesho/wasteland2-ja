# 訳の点検: check(en, ja) → 問題のリスト（空なら合格）
#   記号 [..] {..} の数、*キーワード* の数と中身、\n の数、前後の空白、半角の ( ) / の使いすぎ
import re, collections

TOK = re.compile(r'\[[^\]\s]{1,40}\]|\{[^}\s]{1,60}\}')
STAR = re.compile(r'\*([^*]+)\*')
GROUP = re.compile(r'\((%|-|\+)?[^()]*/[^()]*\)')     # 英語の文法の選択（a/b）


def strip_groups(s):
    # 選択の中にある記号は数えない（日本語では消えてよい）
    return GROUP.sub('', s)


def toks(s):
    return collections.Counter(t for t in TOK.findall(s))


def check(en, ja):
    errs = []
    # ** は飾りの星（「**咳**」のような動作の書き方）でキーワードではない
    en = en.replace('**', '\x01'); ja = ja.replace('**', '\x01')
    if not ja.strip():
        return ['empty']
    te = toks(strip_groups(en)); tj = toks(strip_groups(ja))
    for t, n in te.items():
        if tj[t] < n and not re.match(r'\[(COUNT|\.#)\]', t): errs.append('lost ' + t)
    for t, n in tj.items():
        if te[t] < n and t not in toks(en): errs.append('extra ' + t)
    se = STAR.findall(en); sj = STAR.findall(ja)
    if len(se) != len(sj):
        errs.append('stars %d/%d' % (len(se), len(sj)))
    else:
        ens = collections.Counter(s.strip() for s in se)
        got = collections.Counter()
        for s in sj:
            if '/' not in s: errs.append('star no /: ' + s[:30]); continue
            got[s.split('/', 1)[1].strip()] += 1
        if not errs and got != ens:
            # 英語の側の写しが違う（大文字小文字だけの違いは許す）
            if collections.Counter(k.lower() for k in got.elements()) != collections.Counter(k.lower() for k in ens.elements()):
                errs.append('star english differs')
    if en.count('\\n') != ja.count('\\n'): errs.append('newline %d/%d' % (en.count('\\n'), ja.count('\\n')))
    le = len(en) - len(en.lstrip(' ')); lj = len(ja) - len(ja.lstrip(' '))
    if (le > 0) != (lj > 0): errs.append('lead space')
    # 本文に半角の ( ) / が残っていないか（(%..) の選択・*キーワード*・記号は除く）
    body = STAR.sub('', TOK.sub('', ja))
    body = re.sub(r'\\.', '', body)                      # \( \) \/ は文字そのもの
    body = re.sub(r'\(%[^()]*\)', '', body)
    # 英語と同じ形の選択（例: ([ITEM]/, [ITEM]/ and [ITEM])）は許す
    eg = len(re.findall(r'\((?!%)[^()]*/[^()]*\)', re.sub(r'\\.', '', en)))
    jg = re.findall(r'\([^()]*\)', body)
    if re.search(r'[()]', body) and not (eg and len(jg) == eg and '[' in ''.join(jg)): errs.append('ascii paren')
    if re.search(r'[Ａ-Ｚａ-ｚ０-９]', ja): errs.append('fullwidth alnum')
    return errs
