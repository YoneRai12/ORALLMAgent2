# Manus-Style Autonomous Agent Scaffold / マヌス風自律エージェント雛形

## Overview / 概要
This project provides a scaffold for building a Manus-style autonomous AI agent. It communicates with local LLM servers via HTTP APIs and can be extended to perform browser automation, file operations, and more.

本プロジェクトは、Manus 風の自律型 AI エージェントを構築するための雛形です。HTTP API を介してローカル LLM サーバーと通信し、ブラウザ自動化やファイル操作等を拡張して利用できます。

## Features / 特徴
- CLI, REST API, and future web/Apple app integration / CLI・REST API・Web/Apple アプリ統合
- JWT 認証・CSRF 対策・レート制限・CORS 対応 / JWT auth, CSRF protection, rate limiting, and CORS
- LLM server configurable via `.env` / LLM サーバーは `.env` で設定可能
- `/status` health endpoint / `/status` ヘルスチェックエンドポイント
- Prompt template for merge conflict resolution / マージコンフリクト解消プロンプト
- Real-time browser automation streaming & recording with WebSocket / ブラウザ操作のリアルタイム配信・録画 (WebSocket)
- Multi-user authentication with JWT & signup / JWT によるマルチユーザー認証とサインアップ
- File upload/download API for agent tasks / ファイルアップロード・ダウンロード API
- Multi-user chat and task control / マルチユーザーチャットとタスク制御
- Sub-agent management via API / API からのサブエージェント管理
- Plugin & workflow scaffolds for extensibility / プラグイン・ワークフロー拡張の雛形
- Session manager with persistent logs & replay / セッション管理とログ保存・リプレイ
- Plugin auto-loader for drop-in tools / 追加ツール用プラグインオートローダー
- Dashboard endpoint to monitor agents and sessions / エージェント・セッション監視用ダッシュボード
- Dashboard and architecture docs / ダッシュボードおよびアーキテクチャ文書
  (see `docs/architecture.md`)

## Security Notes / セキュリティ注意
- **Expose LLM and agent APIs only to localhost or trusted LAN.** / **LLM やエージェント API はローカルまたは信頼できる LAN のみに公開してください。**
- **Never commit real credentials or API keys. Use `.env` files.** / **認証情報や API キーをコードに直接書かないでください。必ず `.env` を使用してください。**
- User data is processed in-memory only; enable logging explicitly if needed. / ユーザーデータはメモリ上のみで処理されます。ログ記録が必要な場合は明示的に有効化してください。
- The agent will not bypass CAPTCHAs or 2FA. / エージェントは CAPTCHA や 2FA を回避しません。
- Recorded browser sessions may contain sensitive data—store and delete them carefully. / 保存されたブラウザセッションには機微情報が含まれる可能性があるため、取り扱いと削除に注意してください。

## Quick Start / クイックスタート
### 1. Clone and setup / クローンとセットアップ
```
git clone <repo>
cd ORALLMAgent2
cp .env.example .env
```
Edit `.env` with your local LLM endpoint, API credentials, etc.
```
# Linux / WSL / macOS
bash scripts/setup_linux.sh

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File scripts/setup_windows.ps1
```

### 2. Run REST API / REST API 実行
```
python main.py --api
```
API docs available at `http://localhost:8001/docs`.

### 3. Run CLI / CLI 実行
```
python main.py "write a haiku about the sky"
```

### 4. Start session & browser stream / セッション開始とブラウザストリーム
1. Create session / セッション作成:
   ```bash
   curl -X POST http://localhost:8001/sessions \
        -H "Authorization: Bearer <ACCESS_TOKEN>" \
        -H "X-CSRF-Token: <CSRF_TOKEN>" \
        -b cookie.txt \
        -d '{"profile": "default"}'
   ```
   Response contains `session_id` and `agent_id`.
2. Start browser / ブラウザ起動:
   ```bash
   curl -X POST http://localhost:8001/sessions/<session_id>/browser/start \
        -H "Authorization: Bearer <ACCESS_TOKEN>" \
        -H "X-CSRF-Token: <CSRF_TOKEN>" \
        -b cookie.txt \
        -d '{"url": "https://example.com"}'
   ```
3. Connect via WebSocket / WebSocket で接続:
   ```javascript
   const ws = new WebSocket('ws://localhost:8001/ws/session/<session_id>?token=<ACCESS_TOKEN>');
   ws.onmessage = ev => {
     const img = document.getElementById('view');
     img.src = `data:image/png;base64,${ev.data}`;
   };
   ```
   A minimal viewer is provided at `dashboard/viewer.html`.
   Safari/iOS clients automatically switch to HLS `/stream/<session_id>/master.m3u8`.
4. Control session / セッション制御:
   ```bash
   curl -X POST http://localhost:8001/sessions/<session_id>/browser/command \
        -H "Authorization: Bearer <ACCESS_TOKEN>" \
        -H "X-CSRF-Token: <CSRF_TOKEN>" \
        -b cookie.txt \
        -d '{"action": "pause"}'
   ```

### File upload/download / ファイルアップロード・ダウンロード
```bash
# upload
curl -X POST -H "Authorization: Bearer <ACCESS_TOKEN>" \
     -F "uploaded=@path/to/file" http://localhost:8001/sessions/<session_id>/files

# download
curl -OJ -H "Authorization: Bearer <ACCESS_TOKEN>" \
     http://localhost:8001/sessions/<session_id>/files/<filename>
```

### Recorded video / 録画取得
```bash
curl -OJ -H "Authorization: Bearer <ACCESS_TOKEN>" \
     http://localhost:8001/sessions/<session_id>/browser/video
```
### Performance knobs / パフォーマンス調整
- `STREAM_FPS` – Frame rate for capture (default 12) / キャプチャのフレームレート（既定12fps）
- `PNG_QUALITY` – JPEG quality 0-100 (default 70) / JPEG画質0-100（既定70）
- `MAX_VIEWERS` – Max simultaneous viewers (default 6) / 同時視聴者数の上限（既定6）
- `HLS_SEGMENT_TIME` – HLS segment length in seconds (default 4) / HLSセグメント長(秒)（既定4）

### 5. Run tests / テスト実行
```bash
pytest -q
```



## 🔴 Manus Mode / マヌスモード
1. Launch API / API を起動:
   ```bash
   python -m uvicorn main:app --reload
   ```
2. Get JWT token (see below) / JWT トークン取得（後述）
3. Create session / セッション作成:
   ```bash
   curl -X POST http://localhost:8000/api/sessions \\
        -H "Authorization: Bearer <TOKEN>"
   ```
   Response → `{ "session_id": "..." }`
4. Open live viewer / ライブビューアを開く:
   - Access `http://localhost:8000/dashboard/viewer.html`
   - Enter token & session ID then connect

### API examples / API 例
Upload / アップロード:
```bash
curl -X POST -H "Authorization: Bearer <TOKEN>" \\
     -F "file=@path/to/file" http://localhost:8000/api/upload
```

Download / ダウンロード:
```bash
curl -OJ -H "Authorization: Bearer <TOKEN>" \\
     http://localhost:8000/api/download/<filename>
```


## API Authentication / API 認証
1. Sign up / サインアップ:
```bash
curl -X POST http://localhost:8001/users/signup \
     -H 'Content-Type: application/json' \
     -d '{"username":"alice", "password":"secret"}'
```
2. Request a token / トークン取得:
```bash
curl -X POST -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=change_me" \
     -c cookie.txt \
     http://localhost:8001/token -D -
```
The response header `X-CSRF-Token` and the JWT in JSON should be used for subsequent requests.
3. Call secured endpoint / 認証付きエンドポイント呼び出し:
```bash
curl -X POST http://localhost:8001/api/task \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <ACCESS_TOKEN>" \
     -H "X-CSRF-Token: <CSRF_TOKEN>" \
     -b cookie.txt \
     -d '{"instruction": "tell me a joke"}'
```

## Example Clients
### JavaScript (fetch)
```javascript
// Login and get token
const loginRes = await fetch('http://localhost:8001/token', {
  method: 'POST',
  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
  body: new URLSearchParams({username: 'admin', password: 'change_me'})
});
const csrfToken = loginRes.headers.get('X-CSRF-Token');
const {access_token} = await loginRes.json();

// Send task
await fetch('http://localhost:8001/api/task', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`,
    'X-CSRF-Token': csrfToken
  },
  credentials: 'include',
  body: JSON.stringify({instruction: 'write a poem'})
});
```

### JavaScript (WebSocket)
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/session/<session_id>');
ws.onmessage = ev => {
  const img = document.getElementById('view');
  img.src = `data:image/png;base64,${ev.data}`;
};
```

### JavaScript (Collaboration Chat)
```javascript
const chat = new WebSocket('ws://localhost:8001/ws/chat/lobby');
chat.onmessage = ev => console.log('msg', ev.data);
chat.onopen = () => chat.send('hello everyone');
```

### Swift (URLSession)
```swift
struct Token: Decodable { let access_token: String }

// Login
var req = URLRequest(url: URL(string: "http://localhost:8001/token")!)
req.httpMethod = "POST"
req.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
req.httpBody = "username=admin&password=change_me".data(using: .utf8)
let (data, resp) = try await URLSession.shared.data(for: req)
let csrf = (resp as? HTTPURLResponse)?.value(forHTTPHeaderField: "X-CSRF-Token") ?? ""
let token = try JSONDecoder().decode(Token.self, from: data).access_token

// Send task
var taskReq = URLRequest(url: URL(string: "http://localhost:8001/api/task")!)
taskReq.httpMethod = "POST"
taskReq.setValue("application/json", forHTTPHeaderField: "Content-Type")
taskReq.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
taskReq.setValue(csrf, forHTTPHeaderField: "X-CSRF-Token")
let payload = try JSONSerialization.data(withJSONObject: ["instruction": "hello"], options: [])
taskReq.httpBody = payload
let (_, _) = try await URLSession.shared.data(for: taskReq)
```

### Swift (WebSocket)
```swift
let url = URL(string: "ws://localhost:8001/ws/session/<session_id>")!
let ws = URLSession.shared.webSocketTask(with: url)
ws.receive { result in
    if case let .success(.string(text)) = result {
        // text contains base64 PNG data
    }
}
ws.resume()
```

## Directory Structure / ディレクトリ構成
- `main.py` : CLI & API entry point / CLI & API エントリーポイント
- `agent/` : Core planning/execution scaffolding / 計画・実行の核となる雛形
- `tools/` : Tool implementations (web search, browser automation, etc.) / ツール実装
- `sessions/` : Session management code / セッション管理コード
- `log/` : Action logs & replay utilities / 行動ログとリプレイユーティリティ
- `plugins/` : Drop-in extension modules / 拡張モジュール
- `session_data/` : Runtime session storage (gitignored) / 実行時セッション保存先（Git 管理外）
- `prompts/` : Prompt templates / プロンプトテンプレート
- `scripts/` : Environment setup scripts / 環境構築スクリプト

## License / ライセンス
MIT License

## Changelog / 変更履歴
### 0.9.0 – first public preview / 初の公開プレビュー
- HLS fallback streaming and ffmpeg-based recording
- E2E tests, security hardening, performance knobs
