# 導入

ホストPythonは3.12.13、依存/実行はuvとlockfileを使う。
実compilerとMac試遊は現在macOS arm64を対象にする。Linux CIは標準試験を担当。

## 固定SDK

[公開OS](https://github.com/ayutaz/scratch-arcade-os)の
`547e7ac7e1af8eedf1dc063f97a27a93425f50b7`を、追跡ファイルの変更がない状態で用意する。
SDK側で次を実行する。

```sh
uv run --locked python tools/bootstrap.py
```

これにより固定Zig 0.15.2、WAMR 2.4.5、LittleFSの公開依存を取得する。
Forgeの`--sdk`はそのcheckoutへのパス。実機・GPIO・Flashへは接続しない。

## 生成器

現在の接続は既存のChatGPT認証を持つ`codex exec`だけ。
`codex login status`の結果を内部で確認し、APIキー認証なら実行しない。
APIキー/トークンを子プロセス環境へ渡さず、有料APIや別プロバイダーへ自動切替しない。

1試行は標準180秒、1〜5試行まで。生成はread-only sandbox、承認要求は拒否、
新規private作業場所、JSON schema出力、出力量制限を使う。
保護解除・信頼設定の追加・ユーザーの別作業の停止は行わない。
タイムアウト時は所有する子プロセスのgroupだけを終了する。
CLIの一時logは`runs/`内に保持し、Gitへ含めない。

read-only sandboxの指定を、ネットワーク隔離や完全なコード安全性の証明とは扱わない。
モデルにはツール使用を禁止し、tool eventが出た試行は採用しない。

## 成果物

`runs/<name>/result.json`がaccepted=trueの場合だけ、ready.folderの
`build/app.labapp`を採用候補にする。各attemptの失敗、C、評価、再現buildも保持する。
生成Cは限定したprofileで検査し、別header・asm・pragma等を拒否する。
完成packageは権限drawのみ。配備ガードと実機の検証範囲は[実機記録](device-validation.md)を参照。

## 試遊と画像

`sample maze|collect|dodge --sdk <SDK> --output runs/<new>`は認証なしで公開Cを再ビルドする。
`play runs/<name> --sdk <SDK>`は採用済みの同じpackageをMacのウィンドウで実行する。
`--frames 3600`のように有限にできる。出力やpackageの変更、未採用runは拒否する。

```sh
uv run --locked python -m arcade_game_forge render runs/my-maze \
  --sdk ../scratch-arcade-os --output images/my-maze
```

画像は実WASMのtitle/play/win/lossと勝利GIF。実機撮影や実時間録画とは区別する。
出力先は新規フォルダのみ。`docs/media/`は公開した3本の例。
