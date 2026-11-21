ウェイストランド2 日本語化パッチ v1.0

Steam 版「Wasteland 2」（最初の版）と「Wasteland 2: Director's Cut」を日本語で遊べるようにする、非公式のファンメイド日本語化パッチです。
開発元・販売元とは関係ありません。

■ 入れ方
持っている版のフォルダの version.dll を使います。
  Wasteland 2: Director's Cut → DirectorsCut\version.dll
  Wasteland 2（最初の版）     → Classic\version.dll
1. Steam のライブラリでゲームを右クリックし、「管理」→「ローカルファイルを閲覧」でゲームのフォルダを開きます。
2. その中の Build フォルダ（WL2.exe があるフォルダ）に、版に合った version.dll を置きます。
3. いつもどおり Steam から起動します。

■ 外し方
Build フォルダから version.dll を消すと、英語版に戻ります。
ゲームのファイルは書き換えません。起動したとき、日本語の文章の表を %LOCALAPPDATA%\WL2_JP に書き出します。
これも消したいときは、そのフォルダを消してください。セーブデータは英語版と共通です。

■ 遊ぶときの注意
・Director's Cut は、オプションの「言語」を English のままにしてください。
・会話のキーワードは、ボタンや色のついた言葉をクリックすれば使えます。
  打ち込んで尋ねるときは、英語版と同じ英語で打ち込みます（例: 任務なら duty）。
・キャラクターの名前は英字で入力します。
・キー割り当ての画面のキーの名前と、絵になっている文字は英語のままです。

■ サイト
https://higesho.github.io/wasteland2-ja/
誤訳の報告: https://github.com/higesho/wasteland2-ja/issues

■ クレジット
・Director's Cut 用の DLL では、関数のフックに MinHook（BSD 2-Clause License）を使っています（MinHook-LICENSE.txt）。
・このパッチの使用は自己責任でお願いします。
・配布物には原作のプログラムやデータは入っていません。
Wasteland は inXile Entertainment の商標です。
