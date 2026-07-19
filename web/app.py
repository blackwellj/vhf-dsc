"""FastAPI application for VHF DSC web interface."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from web.routes.decode import router as decode_router
from web.routes.encode import router as encode_router
from web.routes.status import router as status_router
from web.routes.stream import router as stream_router

app = FastAPI(
    title="VHF DSC Encoder/Decoder",
    description="ITU-R M.493-16 compliant DSC encoder and decoder",
    version="0.1.0",
)

app.include_router(decode_router)
app.include_router(encode_router)
app.include_router(stream_router)
app.include_router(status_router)


@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VHF DSC Encoder/Decoder</title>
        <style>
            :root {
                color-scheme: light dark;
                --bg: #f7f9fc;
                --card: #ffffff;
                --text: #102a43;
                --muted: #486581;
                --accent: #0f5bd8;
                --border: #d9e2ec;
                --feed-bg: #030712;
            }
            @media (prefers-color-scheme: dark) {
                :root {
                    --bg: #0f172a;
                    --card: #111c36;
                    --text: #e6edf7;
                    --muted: #9fb3c8;
                    --accent: #7fb3ff;
                    --border: #243b53;
                    --feed-bg: #020617;
                }
            }
            body {
                font-family: system-ui, sans-serif;
                max-width: 960px;
                margin: 2rem auto;
                padding: 0 1rem;
                background: var(--bg);
                color: var(--text);
            }
            h1 { margin-bottom: 0.5rem; }
            .grid { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
            .card {
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 1.25rem;
                background: var(--card);
            }
            .card h2 { margin-top: 0; }
            a { color: var(--accent); text-decoration: none; font-weight: 600; }
            a:hover { text-decoration: underline; }
            .status {
                display: inline-block;
                padding: 0.25rem 0.6rem;
                border-radius: 999px;
                background: #d9fbe5;
                color: #11653a;
                font-size: 0.85rem;
                font-weight: 700;
            }
            #live-feed {
                max-height: 280px;
                overflow: auto;
                background: var(--feed-bg);
                color: #d1fae5;
                border-radius: 8px;
                padding: 0.75rem;
                font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
                font-size: 0.8rem;
                margin-top: 0.75rem;
                white-space: pre-wrap;
                word-break: break-word;
            }
            .hint { color: var(--muted); font-size: 0.9rem; }
        </style>
    </head>
    <body>
        <h1>VHF DSC Encoder/Decoder</h1>
        <p><span class="status">ITU-R M.493-16 Compliant</span></p>
        <p class="hint">Encode DSC test audio, decode uploaded recordings, and watch live decoded traffic.</p>

        <div class="grid">
            <div class="card">
                <h2>Decode</h2>
                <p>Upload audio files (WAV, raw, IQ) for DSC decoding.</p>
                <a href="/decode/">Go to Decoder &rarr;</a>
            </div>
            <div class="card">
                <h2>Encode</h2>
                <p>Generate DSC test messages and download .wav output.</p>
                <a href="/encode/">Go to Encoder &rarr;</a>
            </div>
            <div class="card">
                <h2>API</h2>
                <p>REST API documentation is available at <a href="/docs">/docs</a>.</p>
            </div>
            <div class="card">
                <h2>Live Feed</h2>
                <p id="stream-status" class="hint">Connecting to WebSocket...</p>
                <div id="live-feed">Waiting for live decoded messages...</div>
            </div>
        </div>
        <script>
            const protocol = location.protocol === "https:" ? "wss" : "ws";
            const socketUrl = `${protocol}://${location.host}/stream/ws`;
            const feed = document.getElementById("live-feed");
            const status = document.getElementById("stream-status");
            const MAX_RECONNECT_DELAY_MS = 10000;
            const MAX_RETRIES = 20;
            let socket = null;
            let retries = 0;

            function pushLine(text) {
                const stamp = new Date().toLocaleTimeString();
                feed.textContent = `[${stamp}] ${text}\n` + feed.textContent;
            }

            function connect() {
                socket = new WebSocket(socketUrl);
                socket.onopen = () => {
                    retries = 0;
                    status.textContent = "Connected to live feed.";
                    pushLine("Live feed connected.");
                };
                socket.onmessage = (event) => pushLine(event.data);
                socket.onerror = () => status.textContent = "Live feed connection error.";
                socket.onclose = () => {
                    if (retries >= MAX_RETRIES) {
                        status.textContent = "Live feed unavailable after repeated retries.";
                        pushLine("Live feed retry limit reached.");
                        return;
                    }
                    status.textContent = "Live feed disconnected. Reconnecting...";
                    pushLine("Live feed disconnected.");
                    retries += 1;
                    const waitMs = Math.min(MAX_RECONNECT_DELAY_MS, Math.pow(2, retries - 1) * 1000);
                    setTimeout(connect, waitMs);
                };
            }

            connect();
        </script>
    </body>
    </html>
    """
