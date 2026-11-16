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
