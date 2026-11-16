# Arcade Game Forge

小さなゲーム仕様から、[Scratch Arcade OS](https://github.com/ayutaz/scratch-arcade-os)向けの
WASMアプリを作るツールです。ローカルのCodex CLIがCを生成し、独立したゲーム規則と両VMで
検証します。失敗を渡して修正し、同じpackageを再ビルドできたものだけを採用します。

[English](README.md)

## 現在の状態

ホストの生成/修正pipelineと異常処理の試験が通りました。
実際のAI生成、遊べるサンプル、本体配備はこれから確認します。**実機確認済みリリースではありません。**
現在の試験は偽の生成器、実プロセス、実WASM compiler、Wasmtime、WAMRを使用します。
コンパイル成功だけでは合格になりません。

初版は迷路・落下物回避・コイン収集の3種類です。任意のゲームやOSの新機能を生成するものではありません。

## 使い方

[uv](https://docs.astral.sh/uv/)、ChatGPTで認証済みのCodex CLI、
[固定OS SDK](docs/setup.md)を用意します。

```sh
uv sync --locked
uv run --locked python -m arcade_game_forge validate examples/specs/maze.json
uv run --locked python -m arcade_game_forge make examples/specs/maze.json \
  --sdk ../scratch-arcade-os --output runs/my-maze --attempts 3 --timeout 180
```

独立検証と同一packageの再ビルドに成功したときだけ成功終了します。
失敗した試行もローカルへ保存し、本体には接続しません。
生成は読み取り専用sandboxと新しい作業場所を使い、APIキー/有料APIへの切替は無効です。
GPUは不要です。

## テスト

```sh
uv run --locked python -m unittest discover -s tests -v
# 固定OS SDKとZig/WAMRソースを用意した場合:
uv run --locked python -m unittest discover -s tests/integration -v
```

標準試験にモデル認証・GPU・実機は不要です。統合試験は実WASMをコンパイルし、
両VMが一致してもゲームの動作が誤っていれば拒否することを確認します。

[ゲーム規則](docs/specification.md)・[導入](docs/setup.md)・[検証記録](docs/validation.md)を参照してください。
コードは[Apache-2.0](LICENSE)です。
