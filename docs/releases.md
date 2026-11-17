# ソースリリース

2026-11-18。通常CIに加え、タグのsource配布手順を用意した。**まだ正式タグ/Releaseは公開していない。**
実機の受入とデモが揃ってから、対象commitと版を決める。CI成功だけを作品完成と扱わない。

## 配布物

- `<project>-<version>-source.tar.gz`: Git追跡source、LICENSE、文書/公開デモ素材。
- `SHA256SUMS`: archiveのSHA-256。

firmwareやpaired app package、本体録音、鍵、build/cacheは含めない。

## 公開前の条件

| 条件 | 検査 |
|---|---|
| 版 | `vMAJOR.MINOR.PATCH`とpyproject.tomlが一致 |
| source | cleanなcheckout、タグがHEADを指し、origin/mainの履歴に含まれる |
| 試験 | タグ上で通常の全CIを再実行。失敗/skipで公開へ進めない |
| 配布境界 | 追跡済み秘密/生成物パス、firmware/録音/鍵、symlink、認証情報形式を拒否 |
| 出力 | dist内の新規実ディレクトリのみ。既存archiveやReleaseを上書きしない |

archiveは同じcommitでtimestampを固定して再生成できる。バイナリのビルド再現性とは別の検査。

## タグ作成後の処理

[Source release workflow](../.github/workflows/release.yml)が[通常CI](../.github/workflows/tests.yml)を呼び、全jobの成功後だけpublishへ進む。
publish jobだけにcontents:writeを与え、checkoutの資格情報を保存しない。Actionsとuvは既存CIと同じ固定版。
Source archiveとchecksumだけを`gh release create --verify-tag`で登録する。タグ/既存Releaseは削除・上書きしない。

ローカルで同じarchiveを作る場合は、受入済みmainの対象タグをcheckoutしたclean環境で実行する。

```sh
uv sync --locked
uv run --locked python tools/source_release.py --tag v0.1.0
```

このコマンド自体はGitHubへ送信せず、実機にも接続しない。タグ未作成/不一致なら停止する。
タグpushは公開操作であり、受入前の準備作業では行わない。

## TDDと範囲

新tool未作成のFileNotFoundErrorで先行Redを確認後、最小実装。
5件の契約試験は一時Git repoを実際に作り、main/tag/clean、同一archiveとSHA、秘密パス/symlink/出力境界、CI公開順序を検査する。
初回のGreen試行はtarfileがrootディレクトリ名の末尾slashを除くことをfixtureが考慮せず1失敗。
archiveのsource範囲を変えず期待値を修正し、5件すべて成功した。これは製品のRedへ数えない。

```sh
uv run --locked python -m unittest discover -s tests -p test_source_release.py -v
```

ローカルarchive生成はfixtureで検証。実Releaseへのアップロードは未実行で、workflowの実発火は正式タグの公開時に検証する。

最終回帰: 標準41件/2.840秒、実SDK統合7件/6.078秒が成功（skipなし）。uv lock・actionlint1.7.12・差分検査も成功。Actionsの実発火や本体の動作を保証する結果とは区別する。
単一backslashのファイル名も拒否する既存動作を追加照合した。これは先行Redを伴う新実装ではない。
