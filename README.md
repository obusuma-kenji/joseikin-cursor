## joseikin-cursor（キャリアアップ助成金・正社員化コース専用）

このフォルダは「キャリアアップ助成金（正社員化コース）」の申請準備を支援するためのローカル実行ツールです。

`rules.md` を判定フローの骨格として使い、`laws/career-up-guideline.pdf`（制度Q&A）に基づく実務上のNGポイントをチェックに反映し、`templates/` から文章・一覧を生成します。

### できること
- **①対象判定チェック**（企業/労働者/賃金/期限の観点で判定）
- **②不足資料一覧生成**
- **③申請理由文ドラフト生成**
- **④提出前チェックリスト生成**
- **⑤NGになりやすいポイント警告表示**

### セットアップ

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 起動（簡易Web）

```bash
streamlit run app\main.py
```

### 起動（Pythonなしで動かす / 推奨）

PythonやNodeが入っていない環境では、`careerup.html` をブラウザで直接開くと動作します。

- `careerup.html` を開く
- 可能なら「templatesフォルダを選択」「rules.mdを選択」を押して読み込む
- 入力して「判定 / 生成」

### 起動（CLI）

```bash
python -m app.cli --input sample_input.json
```

### 入力データ
Webではフォーム入力、CLIではJSON入力に対応しています。

### 注意
- 本ツールは申請可否を最終判断するものではありません。最終的には提出先の労働局・ハローワーク案内と最新様式に従ってください。
- 添付書類の「加工・転記」は不正受給認定のリスクになり得るため、原本/原本複写を前提に確認してください（ガイドラインQ&Aの趣旨）。
