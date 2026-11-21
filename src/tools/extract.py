# ゲームのデータ（resources.assets）から文章の表 Main_xx / Defines_xx を work/loc/ に書き出す
import UnityPy, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
D = r'L:\SteamLibrary\steamapps\common\Wasteland 2\Build\WL2_Data'
out = os.path.join(ROOT, 'work', 'loc'); os.makedirs(out, exist_ok=True)
env = UnityPy.load(os.path.join(D, 'resources.assets'))
for o in env.objects:
    if o.type.name != 'TextAsset': continue
    d = o.read()
    b = d.m_Script
    if isinstance(b, str): b = b.encode('utf-8', 'surrogateescape')
    open(os.path.join(out, d.m_Name + '.txt'), 'wb').write(b)
    print(d.m_Name, len(b))
