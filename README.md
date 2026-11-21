# ウェイストランド2 日本語化パッチ

Steam 版「Wasteland 2」（最初の版）と「Wasteland 2: Director's Cut」を日本語で遊べるようにする、非公式のファンメイド日本語化パッチです。
開発元・販売元とは関係ありません。

- サイト（紹介・入れ方）: https://higesho.github.io/wasteland2-ja/
- ダウンロード: [リリース](https://github.com/higesho/wasteland2-ja/releases/latest) の `Wasteland2_JP.zip`
- ウェイストランド（1作目）の日本語化: https://higesho.github.io/wasteland-ja/
- バーズテイル三部作の日本語化: https://higesho.github.io/bardstale-ja/

## 入れ方

1. `Wasteland2_JP.zip` の中から、持っている版のフォルダの `version.dll` を選びます。
   - Wasteland 2: Director's Cut → `DirectorsCut\version.dll`
   - Wasteland 2（最初の版） → `Classic\version.dll`
2. ゲームのフォルダの中の `Build` フォルダ（`WL2.exe` があるフォルダ）に置きます。
3. いつもどおり Steam から起動します。

外すときは、`version.dll` を消せば英語版に戻ります。
ゲームのファイルは書き換えません。配布物には原作のプログラムやデータは入っていません。

## ご意見・誤訳の報告

誤訳や不自然な訳に気づいたら、Issues で教えてください。

## クレジット・権利

- Director's Cut 用の DLL では MinHook（BSD 2-Clause License）を使っています。
- `src/` の自作のプログラムは MIT License です。
- Wasteland は inXile Entertainment の商標です。ゲームの画像・文章の権利は原作の権利者にあります。
