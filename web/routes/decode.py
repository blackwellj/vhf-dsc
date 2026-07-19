"""Decode route - file upload and decode."""

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from vhf_dsc.decoder import DSCDecoderPipeline
from vhf_dsc.io.file_upload import FileUploadHandler

router = APIRouter(prefix="/decode", tags=["decode"])
upload_handler = FileUploadHandler()


@router.get("/", response_class=HTMLResponse)
async def decode_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DSC Decoder \u2014 VHF DSC</title>
        <style>
            :root {
                color-scheme: light dark;
                --bg: #f7f9fc; --card: #ffffff; --text: #102a43; --muted: #486581;
                --accent: #0f5bd8; --border: #d9e2ec;
                --btn: #0f5bd8; --btn-h: #0d4db8; --in-border: #bcccdc;
            }
            @media (prefers-color-scheme: dark) {
                :root {
                    --bg: #0f172a; --card: #111c36; --text: #e6edf7; --muted: #9fb3c8;
                    --accent: #7fb3ff; --border: #243b53;
                    --btn: #1d6ef5; --btn-h: #2a7bff; --in-border: #2d4a6e;
                }
            }
            *, *::before, *::after { box-sizing: border-box; }
            body {
                font-family: system-ui, sans-serif; max-width: 860px;
                margin: 2rem auto; padding: 0 1rem;
                background: var(--bg); color: var(--text);
            }
            .nav { margin-bottom: 1.5rem; }
            .nav a { color: var(--accent); text-decoration: none; font-weight: 600; font-size: 0.9rem; }
            .nav a:hover { text-decoration: underline; }
            h1 { margin: 0 0 0.25rem; font-size: 1.5rem; }
            .sub { color: var(--muted); margin: 0 0 1.5rem; font-size: 0.9rem; }
            .card {
                border: 1px solid var(--border); border-radius: 12px;
                padding: 1.5rem; background: var(--card); margin-bottom: 1rem;
            }
            .drop-zone {
                border: 2px dashed var(--in-border); border-radius: 10px;
                padding: 2rem 1rem; text-align: center; cursor: pointer;
                color: var(--muted); transition: border-color 0.15s, background 0.15s;
            }
            .drop-zone.over, .drop-zone:hover { border-color: var(--accent); }
            .drop-zone input[type="file"] { display: none; }
            .drop-zone .icon { margin: 0 auto 0.5rem; opacity: 0.45; }
            .drop-zone .fname {
                font-weight: 600; color: var(--text);
                margin-top: 0.4rem; font-size: 0.88rem; display: none;
            }
            button {
                padding: 0.7rem; border-radius: 8px; border: none;
                font: inherit; font-weight: 600; font-size: 0.95rem;
                background: var(--btn); color: white; cursor: pointer;
                width: 100%; margin-top: 0.75rem; transition: background 0.15s;
            }
            button:hover:not(:disabled) { background: var(--btn-h); }
            button:disabled { opacity: 0.55; cursor: not-allowed; }
            .alert {
                margin-top: 0.75rem; padding: 0.6rem 0.9rem;
                border-radius: 8px; font-size: 0.88rem; color: var(--muted);
            }
            .alert.err { background: #fde8eb; color: #c0152a; }
            .alert.run { background: #eff6ff; color: #1d4ed8; }
            .alert.ok  { background: #d9fbe5; color: #11653a; }
            @media (prefers-color-scheme: dark) {
                .alert.err { background: #2a0a0f; color: #f87171; }
                .alert.run { background: #0c1a40; color: #7fb3ff; }
                .alert.ok  { background: #042f20; color: #34d399; }
            }
            #results { margin-top: 0; }
            .msg-card {
                border: 1px solid var(--border); border-left: 4px solid var(--border);
                border-radius: 8px; padding: 0.9rem 1rem; margin-bottom: 0.75rem;
                background: var(--card);
            }
            .msg-card.distress { border-left-color: #e53e3e; }
            .msg-card.urgency  { border-left-color: #d97706; }
            .msg-card.safety   { border-left-color: #059669; }
            .msg-card.routine  { border-left-color: #0f5bd8; }
            .msg-card.test     { border-left-color: #9ca3af; }
            .msg-head { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
            .badge {
                display: inline-block; padding: 0.2rem 0.55rem; border-radius: 4px;
                font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;
            }
            .badge.distress { background: #fee2e2; color: #991b1b; }
            .badge.urgency  { background: #fef3c7; color: #92400e; }
            .badge.safety   { background: #d1fae5; color: #065f46; }
            .badge.routine  { background: #dbeafe; color: #1e40af; }
            .badge.test     { background: #f3f4f6; color: #374151; }
            @media (prefers-color-scheme: dark) {
                .badge.distress { background: #4a1010; color: #fca5a5; }
                .badge.urgency  { background: #3a1f00; color: #fcd34d; }
                .badge.safety   { background: #04291a; color: #6ee7b7; }
                .badge.routine  { background: #0c1e40; color: #93c5fd; }
                .badge.test     { background: #1a2030; color: #9ca3af; }
            }
            .msg-fields {
                display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
                gap: 0.35rem; margin-top: 0.4rem;
            }
            .mf { font-size: 0.82rem; }
            .mf .lbl { color: var(--muted); }
            .mf .val { font-weight: 600; }
            .raw-toggle {
                font-size: 0.78rem; color: var(--muted); cursor: pointer;
                user-select: none; margin-top: 0.5rem; display: inline-block;
            }
            .raw-block {
                display: none; background: #030712; color: #d1fae5;
                border-radius: 6px; padding: 0.6rem; font-family: ui-monospace, monospace;
                font-size: 0.78rem; margin-top: 0.35rem; white-space: pre-wrap; word-break: break-all;
            }
            .raw-block.open { display: block; }
            .empty { color: var(--muted); font-style: italic; }
        </style>
    </head>
    <body>
        <div class="nav"><a href="/">&larr; Dashboard</a></div>
        <h1>Decode DSC Audio</h1>
        <p class="sub">Upload a WAV, raw, or IQ audio file to extract DSC messages.</p>
        <div class="card">
            <div class="drop-zone" id="drop">
                <svg class="icon" width="36" height="36" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                </svg>
                <div>Drop audio file here or <strong>click to browse</strong></div>
                <div class="fname" id="fname"></div>
                <input type="file" id="filein" accept=".wav,.raw,.iq">
            </div>
            <button id="btn" disabled>Decode File</button>
            <div class="alert" id="alert">Select a file to begin.</div>
        </div>
        <div id="results"></div>
        <script>
            const drop = document.getElementById("drop");
            const filein = document.getElementById("filein");
            const btn = document.getElementById("btn");
            const alertEl = document.getElementById("alert");
            const results = document.getElementById("results");
            const fnameEl = document.getElementById("fname");
            let selFile = null;

            function setFile(f) {
                selFile = f;
                fnameEl.style.display = "block";
                fnameEl.textContent = f.name;
                btn.disabled = false;
                setAlert("Ready: " + f.name);
            }
            function setAlert(msg, cls) {
                alertEl.textContent = msg;
                alertEl.className = "alert" + (cls ? " " + cls : "");
            }

            drop.addEventListener("click", () => filein.click());
            filein.addEventListener("change", () => { if (filein.files[0]) setFile(filein.files[0]); });
            drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
            drop.addEventListener("dragleave", () => drop.classList.remove("over"));
            drop.addEventListener("drop", (e) => {
                e.preventDefault(); drop.classList.remove("over");
                if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]);
            });

            function msgClass(d) {
                const cat = (d.category || d.format || "").toLowerCase();
                if (d.is_distress || cat.includes("distress")) return "distress";
                if (cat.includes("urgency")) return "urgency";
                if (cat.includes("safety")) return "safety";
                if (cat.includes("test")) return "test";
                return "routine";
            }
            function mf(label, val) {
                if (!val || val === "None" || val === "null") return "";
                return `<div class="mf"><span class="lbl">${label}: </span><span class="val">${val}</span></div>`;
            }
            function renderMsg(d, i) {
                const cls = msgClass(d);
                const label = d.is_distress ? "DISTRESS" : (d.category || d.format || "MSG").replace(/_/g, " ");
                return `<div class="msg-card ${cls}">
                    <div class="msg-head">
                        <span class="badge ${cls}">${label}</span>
                        ${d.mmsi_self ? "<strong>MMSI: " + d.mmsi_self + "</strong>" : ""}
                        ${d.timestamp
                            ? '<span style="color:var(--muted);font-size:0.78rem">'
                              + d.timestamp + "</span>"
                            : ""}
                    </div>
                    <div class="msg-fields">
                        ${mf("Format", d.format)}
                        ${mf("Category", d.category)}
                        ${mf("From", d.mmsi_self)}
                        ${mf("To", d.mmsi_dest)}
                        ${d.nature && d.nature !== "None" ? mf("Nature", d.nature) : ""}
                        ${mf("Position", d.position)}
                        ${mf("Time UTC", d.time_utc)}
                        ${mf("Channel", d.channel)}
                        ${d.tc1 && d.tc1 !== "None" ? mf("TC1", d.tc1) : ""}
                        ${d.tc2 && d.tc2 !== "None" ? mf("TC2", d.tc2) : ""}
                        ${d.status ? mf("Status", d.status) : ""}
                    </div>
                    <span class="raw-toggle" onclick="toggleRaw(${i})">\u25ba Raw JSON</span>
                    <div class="raw-block" id="raw${i}">${JSON.stringify(d, null, 2)}</div>
                </div>`;
            }
            function toggleRaw(i) {
                const el = document.getElementById("raw" + i);
                el.classList.toggle("open");
                const open = el.classList.contains("open");
                el.previousElementSibling.textContent = open
                    ? "\u25bc Raw JSON" : "\u25ba Raw JSON";
            }

            btn.addEventListener("click", async () => {
                if (!selFile) return;
                btn.disabled = true;
                results.innerHTML = "";
                setAlert("Decoding\u2026", "run");
                const fd = new FormData();
                fd.append("file", selFile);
                try {
                    const res = await fetch("/decode/upload", { method: "POST", body: fd });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || "HTTP " + res.status);
                    const msgs = data.messages || [];
                    setAlert("Done \u2014 " + msgs.length + " message(s), " + data.errors + " error(s).", "ok");
                    results.innerHTML = msgs.length
                        ? msgs.map(renderMsg).join("")
                        : "<p class='empty'>No DSC messages found in this file.</p>";
                } catch (err) {
                    setAlert("Decode failed: " + err.message, "err");
                } finally {
                    btn.disabled = false;
                }
            });
        </script>
    </body>
    </html>
    """


@router.post("/upload")
async def decode_upload(file: UploadFile = File(...)):
    content = await file.read()
    filepath = upload_handler.save_upload(file.filename, content)

    try:
        samples, sr = upload_handler.load_audio(filepath)
        pipeline = DSCDecoderPipeline(sr)
        messages = pipeline.process_stream(samples)

        result = {
            "messages": [msg.to_dict() for msg in messages],
            "total": len(messages),
            "errors": pipeline.error_count,
        }
        return JSONResponse(result)
    finally:
        upload_handler.cleanup(filepath)
