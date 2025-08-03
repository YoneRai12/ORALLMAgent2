# Manus-Style Autonomous Agent Scaffold / マヌス風自律エージェント雛形

## Overview / 概要
This project provides a scaffold for building a Manus-style autonomous AI agent.
It communicates with local LLM servers via HTTP APIs and can be extended to
perform browser automation, file operations, and more.

本プロジェクトは、Manus 風の自律型 AI エージェントを構築するための雛形です。
HTTP API を介してローカル LLM サーバーと通信し、ブラウザ自動化やファイル操作等を
拡張して利用できます。

## Features / 特徴
- CLI and REST API interfaces / CLI と REST API インターフェース
- Supports multiple local LLM servers (configurable via `.env`) / 複数のローカル LLM サーバーを `.env` で切替可能
- Secure credential management via environment variables / 環境変数による安全な認証情報管理
- Playwright/Selenium ready for browser automation / Playwright/Selenium によるブラウザ自動化
- Prompt template for AI-driven git merge conflict resolution / AI を用いたマージコンフリクト解消テンプレート

## Security Notes / セキュリティ注意
- **Expose LLM and agent APIs only to localhost or trusted LAN.** / **LLM やエージェント API はローカルまたは信頼できる LAN のみに公開してください。**
- **Never commit real credentials or API keys. Use `.env` files.** / **認証情報や API キーをコードに直接書かないでください。必ず `.env` を使用してください。**
- The agent will not bypass CAPTCHAs or 2FA; manual user input is required. / エージェントは CAPTCHA や 2FA を回避しません。必要に応じて手動入力してください。

## Quick Start / クイックスタート
### 1. Clone and setup / クローンとセットアップ
```
git clone <repo>
cd ORALLMAgent2
cp .env.example .env
```
Edit `.env` with your local LLM endpoint and credentials.
```
# Linux / WSL
bash scripts/setup_linux.sh

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File scripts/setup_windows.ps1
```

### 2. Run CLI / CLI 実行
```
python main.py "write a haiku about the sky"
```
Example commands / 例:
```
!websearch 富士山
!amazon "wireless mouse"
!twitter "post hello world"
```

### 3. Run REST API / REST API 実行
```
python main.py --api
```
Then send a request / その後リクエスト:
```
curl -X POST http://localhost:8001/api/task -H "Content-Type: application/json" -d '{"instruction": "tell me a joke"}'
```

## Directory Structure / ディレクトリ構成
- `main.py` : CLI & API entry point / CLI & API エントリーポイント
- `agent/` : Core planning/execution scaffolding / 計画・実行の核となる雛形
- `tools/` : Tool implementations (web search, browser automation, etc.) / ツール実装
- `prompts/` : Prompt templates / プロンプトテンプレート
- `scripts/` : Environment setup scripts / 環境構築スクリプト

## License / ライセンス
MIT License

