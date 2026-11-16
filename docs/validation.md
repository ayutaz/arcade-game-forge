# 実装・検証記録

2026-11-17 JST、macOS arm64、Python3.12.13/uv、固定SDK547e7ac。
この時点でGPU課金・有料API呼出し・本体変更はない。

| 対象 | 意図したRed | Green |
|---|---|---|
| 仕様/独立Game | spec/reference module欠落 | 7件、0.001秒 |
| C profile/入力列 | source/traces module欠落 | 12件、0.003秒 |
| 独立評価/SDK build | evaluate/sdk module欠落 | unit15件、0.016秒。統合3件、2.360秒 |
| 生成器/修正pipeline | generator/pipeline module欠落 | 21件、0.420秒 |
| CLI | cli module欠落 | 23件、0.438秒 |

```sh
uv run --locked python -m unittest discover -s tests -v
uv run --locked python -m unittest discover -s tests/integration -v
```

unitは偽生成器、実fixture子プロセス、独立Game oracleを使用。
生成器のdeadline/出力超過/失敗、修正への診断、全失敗時の未採用、
既存出力の保護、再現buildの不一致を検証した。
統合では実ZigでWASMを作り、WasmtimeとWAMRが同じ誤動作をしても
独立Gameの規則と違えば不合格にした。

既存ChatGPT CLIの認証状態は読み取りで確認したが、この段階では
実モデルの生成成功・3サンプル・Mac試遊・実機動作を完了としていない。
基盤commit後、新しい3仕様で本物の生成器を評価する。

## C include検査の回帰修正

文字列内のcomment開始/終了表記で外部includeを隠せるケースと、Cのdigraph `%:`を先行テストで再現してRed。
文字列/文字literalとcommentを区別し、digraphを拒否して4件Green（0.001秒）。
実生成した3appにはこの記法はなく、外部ファイルを実際にcompileした試験ではない。

## 3仕様の実生成と自動修正

評価器を99b3d2dとして固定・公開した後に新しい3仕様を用意した。
CLI0.169.0の既存ChatGPT認証で生成、tool call 0、手修正0。
3本とも初回で採用、計615framesを独立規則/Wasmtime/WAMRで確認し、再build hashが一致。
Cと仕様/来歴は`examples/games/`、数値は[benchmark](../benchmarks/results-v1.json)。
モデル名はCLIの既定で、今回の記録から特定していない。一般成功率とはしない。

別実験として迷路の勝利得点だけを1→0へ意図的に壊した。
両VMは同じ誤値でも独立規則がframe34で拒否し、実Codexが診断から修正した。
初回AI生成の失敗と混同せず、seeded repairとして記録した。

## 試遊/サンプル/画像/配備ガードのTDD

| 動作 | 意図したRed | Green |
|---|---|---|
| 固定packageの試遊 | play module欠落 | 採用/hash/パス境界、Homeの起動/終了解放 |
| サンプル再build | samples module欠落 | 3本の来歴hash、モデルを呼ばない再build |
| play/sample CLI | subcommand欠落 | CLI引数と生成しない経路 |
| 配備ガード | deploy module欠落 | 専用ID/権限/HOME/旧hash/他app不変 |
| 実WASM画像 | media module欠落 | 4画面と動くGIF、上書き拒否 |
| render CLI | subcommand欠落 | 採用runから画像作成だけを実行 |

サンプルunitの偽forgeが出力フォルダを作らず失敗した1回はfixture不備で、TDDのRedに数えない。
上記のunit33件Green（0.492秒）、実SDK統合6件Green（5.492秒）。
統合は別seedで3生成ゲームを再検証した。標準試験と同じ2コマンドで再実行可能。

[実機の勝利/既存12本保持とMac3600frames](device-validation.md)は追加の動作検証。
本体の見た目/物理操作や任意入力までの保証へは広げない。
新FW・有料API・GPU契約は使用していない。
