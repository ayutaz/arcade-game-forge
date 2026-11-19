# 実機の検証記録

2026-11-17 JST。[匿名化結果](device/games-v1.json)。FWの変更はない。
3本とも[benchmark](../benchmarks/results-v1.json)で採用した同一packageを使用。

| app | 勝利 | 描画の検証 |
|---|---|---|
| forge-maze | 得点1 | 同じ入力のホストWASMと矩形CRC一致 |
| forge-collect | 得点5 | 同じ入力のホストWASMと矩形CRC一致 |
| forge-dodge | 得点3 | 独立規則の矩形CRCから状態を一意に復号して回避 |

HOME/キー解放、専用ID、draw権限、16KiB、catalog空きを確認してから追加。
既存更新は正確な前package hashが必須。前後で他appのid/title/version/hashを照合した。
新規3本の追加後は合計15本、既存12本を保持。論理FN+BでHOMEへ戻った。

配備ガードは`arcade_game_forge.deploy.install_game`。SDKのclient/decodeを渡して使う。
削除・FW更新・既存他app変更を含まない。前後照合に失敗したら再試行せず停止する。
`install` CLIから同じガードを使える。採用済みrun/hash/metadataをポート接続前に検査する。

```sh
uv run --locked python -m arcade_game_forge install runs/my-maze \
  --sdk <固定SDKのpath> --port <検出した本体ポート>
```

既存の同IDを更新する場合は、一覧で照合した前版のSHA-256を`--previous-sha`へ指定する。
本体のHOMEとキー解放が必要。未対応FWにはbeacon確認前に送信しない。
FWの書き込み・自動削除・再起動は行わない。

物理キー/実LCD/電源再投入の確認ではない。CRC一致は見た目の目視確認を代行しない。
Macは同じ迷路packageをSDLで3600frames実行し、終了時に資源を解放した。
ウィンドウの目視はツールのUI安全制限で確認できず、別経路で迂回していない。
公開画像はホストの決定的なWASM再生であり、実機写真ではない。

## 公開CLIでの追加照合

後続で`install runs/benchmark-v1/maze --previous-sha <exact installed hash>`を実行し、
同一の所有済みmazeだけを更新した。package SHA3997ee6b…、HOME/キー解放、全15appの
id/title/version/hash不変を再接続して照合。[匿名結果](device/cli-v1.json)。新FWは適用していない。

## 音声FW追加後の互換性

2026-11-17 JST。音声FW1affc424…へ個別許可後に更新し、AI Petを含む16本を保持した環境でも確認した。
通常SoC resetの新boot後、同じ3packageの表紙描画命令CRC/終了/HOME/VM復帰/heap減少4KiB以内と全16本の版/hash一致に成功した。
この回帰は表紙と終了の範囲。先の得点1/5/3の勝利を、このFWで再測定したとは扱わない。
実LCD/物理キー/電池の電源断は未確認。ゲームのコード/packageは変更していない。

## 音声v3版での限定互換性

2026-11-18。別途レビュー/個別許可したOS e5915861…の通常SoC reset後、既存3packageで表紙CRC/終了/HOME・VM復帰/heap減少4KiB以内・全16本の版/hash保持を確認した。[匿名結果](device/voice-v3-compatibility-v1.json)。

ゲームのcode/packageは変更していない。この試験は表紙と終了の回帰で、以前の勝利/得点を新FWで再計測した結果ではない。実LCD/物理キー/電池の電源断/実機撮影は引き続き未確認。

## 2026-11-19の実物の受入

ユーザーが3本の表示・物理ボタン操作に問題がないことを確認した。 自動試験の再実行とは区別する。この文書更新でapp/package/FWは変更していない。電池の電源断や実機の撮影を新たに確認したものではない。
