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
            }
            @media (prefers-color-scheme: dark) {
                :root {
                    --bg: #0f172a;
                    --card: #111c36;
                    --text: #e6edf7;
                    --muted: #9fb3c8;
                    --accent: #7fb3ff;
                    --border: #243b53;
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
            .hint { color: var(--muted); font-size: 0.9rem; }
            .live-card { grid-column: 1 / -1; }
            #stream-status { color: var(--muted); font-size: 0.85rem; margin: 0 0 0.75rem; }
            #live-feed {
                max-height: 380px;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
            }
            .lf-empty { color: var(--muted); font-style: italic; font-size: 0.9rem; }
            .lf-msg {
                border: 1px solid var(--border);
                border-left: 4px solid var(--border);
                border-radius: 8px;
                padding: 0.65rem 0.85rem;
                background: var(--bg);
                font-size: 0.85rem;
                animation: fadein 0.3s ease;
            }
            @keyframes fadein { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: none; } }
            .lf-msg.distress { border-left-color: #e53e3e; background: color-mix(in srgb, #e53e3e 6%, var(--card)); }
            .lf-msg.urgency  { border-left-color: #d97706; background: color-mix(in srgb, #d97706 6%, var(--card)); }
            .lf-msg.safety   { border-left-color: #059669; background: color-mix(in srgb, #059669 6%, var(--card)); }
            .lf-msg.routine  { border-left-color: var(--accent); }
            .lf-msg.test     { border-left-color: #9ca3af; }
            .lf-head { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.35rem; }
            .lf-badge {
                display: inline-block; padding: 0.18rem 0.5rem; border-radius: 4px;
                font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;
            }
            .lf-badge.distress { background: #fee2e2; color: #991b1b; }
            .lf-badge.urgency  { background: #fef3c7; color: #92400e; }
            .lf-badge.safety   { background: #d1fae5; color: #065f46; }
            .lf-badge.routine  { background: #dbeafe; color: #1e40af; }
            .lf-badge.test     { background: #f3f4f6; color: #374151; }
            @media (prefers-color-scheme: dark) {
                .lf-badge.distress { background: #4a1010; color: #fca5a5; }
                .lf-badge.urgency  { background: #3a1f00; color: #fcd34d; }
                .lf-badge.safety   { background: #04291a; color: #6ee7b7; }
                .lf-badge.routine  { background: #0c1e40; color: #93c5fd; }
                .lf-badge.test     { background: #1a2030; color: #9ca3af; }
            }
            .lf-fields { display: flex; flex-wrap: wrap; gap: 0.25rem 1rem; }
            .lf-field { font-size: 0.8rem; }
            .lf-field .lbl { color: var(--muted); }
            .lf-stamp { color: var(--muted); font-size: 0.75rem; margin-left: auto; }
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
            <div class="card live-card">
                <h2>Live Feed</h2>
                <p id="stream-status">Connecting to live stream&hellip;</p>
                <div id="live-feed">
                    <span class="lf-empty">Waiting for live decoded messages&hellip;</span>
                </div>
            </div>
        </div>
        <script>
            const feed = document.getElementById("live-feed");
            const wsStatus = document.getElementById("stream-status");
            const pageProtocol = location.protocol.toLowerCase();
            const isHttps = pageProtocol === "https:";
            const protocol = isHttps ? "wss" : "ws";
            const socketUrl = `${protocol}://${location.host}/stream/ws`;
            const MAX_RECONNECT_DELAY_MS = 10000;
            const MAX_RETRIES = 20;
            let socket = null;
            let retryCount = 0;
            let msgCount = 0;

            function msgClass(d) {
                const cat = (d.category || d.format || "").toLowerCase();
                if (d.is_distress || cat.includes("distress")) return "distress";
                if (cat.includes("urgency")) return "urgency";
                if (cat.includes("safety")) return "safety";
                if (cat.includes("test")) return "test";
                return "routine";
            }

            function lf(label, val) {
                if (!val || val === "None" || val === "null") return "";
                return `<span class="lf-field"><span class="lbl">${label}:</span> <strong>${val}</strong></span>`;
            }

            function pushMessage(d) {
                const cls = msgClass(d);
                const label = d.is_distress ? "DISTRESS" : (d.category || d.format || "MSG").replace(/_/g, " ");
                const stamp = new Date().toLocaleTimeString();

                // Remove empty placeholder
                const empty = feed.querySelector(".lf-empty");
                if (empty) empty.remove();

                const div = document.createElement("div");
                div.className = "lf-msg " + cls;
                div.innerHTML = `
                    <div class="lf-head">
                        <span class="lf-badge ${cls}">${label}</span>
                        ${d.mmsi_self ? `<strong>MMSI: ${d.mmsi_self}</strong>` : ""}
                        ${d.mmsi_dest ? `<span style="color:var(--muted)">&#8594; ${d.mmsi_dest}</span>` : ""}
                        <span class="lf-stamp">${stamp}</span>
                    </div>
                    <div class="lf-fields">
                        ${lf("Pos", d.position)}
                        ${lf("Time UTC", d.time_utc)}
                        ${lf("Ch", d.channel)}
                        ${d.nature && d.nature !== "None" ? lf("Nature", d.nature) : ""}
                        ${d.status ? lf("Status", d.status) : ""}
                    </div>`;
                feed.prepend(div);
                msgCount++;
                wsStatus.textContent = `Connected \u2014 ${msgCount} message(s) received.`;
                // Keep at most 50 cards
                while (feed.children.length > 50) feed.lastChild.remove();
            }

            function connect() {
                if (pageProtocol !== "http:" && pageProtocol !== "https:") {
                    wsStatus.textContent = "Live feed unavailable for this page protocol.";
                    return;
                }
                socket = new WebSocket(socketUrl);
                socket.onopen = () => {
                    retryCount = 0;
                    wsStatus.textContent = "Connected \u2014 waiting for messages\u2026";
                };
                socket.onmessage = (event) => {
                    try {
                        const d = JSON.parse(event.data);
                        pushMessage(d);
                    } catch (_) {
                        // non-JSON system message, ignore
                    }
                };
                socket.onerror = () => { wsStatus.textContent = "Live feed connection error."; };
                socket.onclose = () => {
                    retryCount += 1;
                    if (retryCount > MAX_RETRIES) {
                        wsStatus.textContent = "Live feed unavailable after repeated retries.";
                        return;
                    }
                    wsStatus.textContent = "Disconnected \u2014 reconnecting\u2026";
                    const waitMs = Math.min(MAX_RECONNECT_DELAY_MS, Math.pow(2, retryCount - 1) * 1000);
                    setTimeout(connect, waitMs);
                };
            }

            connect();
        </script>
    </body>
    </html>
    """
