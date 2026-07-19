"""Encode route - generate DSC test messages."""

import io

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, field_validator

from vhf_dsc.encoder import DSCModulator, TestMessageGenerator
from vhf_dsc.io.wav import write_wav_normalized
from vhf_dsc.protocol.constants import INTERNAL_SAMPLE_RATE
from vhf_dsc.protocol.symbols import SYM_NATURE_UNDESIGNATED

router = APIRouter(prefix="/encode", tags=["encode"])


@router.get("/", response_class=HTMLResponse)
async def encode_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DSC Encoder \u2014 VHF DSC</title>
        <style>
            :root {
                color-scheme: light dark;
                --bg: #f7f9fc; --card: #ffffff; --text: #102a43; --muted: #486581;
                --accent: #0f5bd8; --border: #d9e2ec;
                --btn: #0f5bd8; --btn-h: #0d4db8;
                --in-bg: #ffffff; --in-border: #bcccdc;
                --ok-text: #11653a; --ok-bg: #d9fbe5;
            }
            @media (prefers-color-scheme: dark) {
                :root {
                    --bg: #0f172a; --card: #111c36; --text: #e6edf7; --muted: #9fb3c8;
                    --accent: #7fb3ff; --border: #243b53;
                    --btn: #1d6ef5; --btn-h: #2a7bff;
                    --in-bg: #1a2744; --in-border: #2d4a6e;
                    --ok-text: #34d399; --ok-bg: #042f20;
                }
            }
            *, *::before, *::after { box-sizing: border-box; }
            body {
                font-family: system-ui, sans-serif; max-width: 620px;
                margin: 2rem auto; padding: 0 1rem;
                background: var(--bg); color: var(--text);
            }
            .nav { margin-bottom: 1.5rem; }
            .nav a { color: var(--accent); text-decoration: none; font-weight: 600; font-size: 0.9rem; }
            .nav a:hover { text-decoration: underline; }
            h1 { margin: 0 0 0.25rem; font-size: 1.5rem; }
            .sub { color: var(--muted); margin: 0 0 1.5rem; font-size: 0.9rem; }
            .card { border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; background: var(--card); }
            .form-grid { display: grid; gap: 1rem; }
            .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
            .field { display: flex; flex-direction: column; gap: 0.3rem; }
            label { font-weight: 600; font-size: 0.88rem; }
            .hint { font-weight: 400; color: var(--muted); font-size: 0.78rem; }
            input, select {
                padding: 0.6rem 0.75rem; border-radius: 8px;
                border: 1px solid var(--in-border); font: inherit; font-size: 0.93rem;
                background: var(--in-bg); color: var(--text); width: 100%;
                transition: border-color 0.15s, outline 0.15s;
            }
            input:focus, select:focus { outline: 2px solid var(--accent); border-color: transparent; }
            button {
                padding: 0.75rem; border-radius: 8px; border: none;
                font: inherit; font-weight: 600; font-size: 0.95rem;
                background: var(--btn); color: white; cursor: pointer;
                width: 100%; margin-top: 0.25rem; transition: background 0.15s;
            }
            button:hover:not(:disabled) { background: var(--btn-h); }
            button:disabled { opacity: 0.55; cursor: not-allowed; }
            .alert {
                margin-top: 1rem; padding: 0.65rem 0.9rem; border-radius: 8px;
                font-size: 0.88rem; display: none;
            }
            .alert.show { display: block; }
            .alert.ok  { background: var(--ok-bg);  color: var(--ok-text); }
            .alert.err { background: #fde8eb; color: #c0152a; }
            .alert.run { background: #eff6ff; color: #1d4ed8; }
            @media (prefers-color-scheme: dark) {
                .alert.err { background: #2a0a0f; color: #f87171; }
                .alert.run { background: #0c1a40; color: #7fb3ff; }
            }
            audio { width: 100%; margin-top: 1rem; border-radius: 8px; display: none; }
            audio.show { display: block; }
        </style>
    </head>
    <body>
        <div class="nav"><a href="/">&larr; Dashboard</a></div>
        <h1>Generate DSC Message</h1>
        <p class="sub">Encode a DSC test message and download the .wav audio file.</p>
        <div class="card">
            <form id="form" class="form-grid" novalidate>
                <div class="field">
                    <label for="msg_type">Message Type</label>
                    <select id="msg_type" name="msg_type">
                        <option value="distress">Distress Alert</option>
                        <option value="safety">All Ships Safety</option>
                        <option value="urgency">All Ships Urgency</option>
                        <option value="routine">Individual Routine</option>
                        <option value="test" selected>Test Call</option>
                    </select>
                </div>
                <div class="field">
                    <label for="mmsi">MMSI <span class="hint">9 digits</span></label>
                    <input id="mmsi" type="text" name="mmsi" value="234567890"
                           pattern="[0-9]{9}" maxlength="9" inputmode="numeric" required>
                </div>
                <div class="form-row">
                    <div class="field">
                        <label for="lat">Latitude</label>
                        <input id="lat" type="number" name="lat" value="51.5074" step="0.0001" min="-90" max="90">
                    </div>
                    <div class="field">
                        <label for="lon">Longitude</label>
                        <input id="lon" type="number" name="lon" value="-0.1278" step="0.0001" min="-180" max="180">
                    </div>
                </div>
                <button type="submit" id="btn">Generate &amp; Download .wav</button>
            </form>
            <div class="alert" id="alert"></div>
            <audio id="preview" controls></audio>
        </div>
        <script>
            const form = document.getElementById("form");
            const btn  = document.getElementById("btn");
            const alertEl = document.getElementById("alert");
            const preview = document.getElementById("preview");

            function setAlert(msg, cls) {
                alertEl.textContent = msg;
                alertEl.className = "alert show " + cls;
            }

            form.addEventListener("submit", async (e) => {
                e.preventDefault();
                btn.disabled = true;
                preview.classList.remove("show");
                setAlert("Generating\u2026", "run");

                const payload = Object.fromEntries(new FormData(form).entries());
                payload.lat = Number(payload.lat);
                payload.lon = Number(payload.lon);

                try {
                    const res = await fetch("/encode/generate", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload),
                    });
                    if (!res.ok) throw new Error("HTTP " + res.status);

                    const blob = await res.blob();
                    const url = URL.createObjectURL(blob);

                    const a = document.createElement("a");
                    a.href = url; a.download = "dsc_" + payload.msg_type + ".wav";
                    document.body.appendChild(a); a.click(); a.remove();

                    preview.src = url;
                    preview.classList.add("show");
                    const msg = "\u2713 Download started \u2014 "
                        + payload.msg_type.toUpperCase() + " message generated.";
                    setAlert(msg, "ok");
                } catch (err) {
                    setAlert("Generation failed: " + err.message, "err");
                } finally {
                    btn.disabled = false;
                }
            });
        </script>
    </body>
    </html>
    """


NATURE_MAP = {
    "not_specified": SYM_NATURE_UNDESIGNATED,
}


class EncodeRequest(BaseModel):
    msg_type: str = "test"
    mmsi: str = "234567890"
    lat: float = 51.5074
    lon: float = -0.1278
    time_utc: str = "1200"
    nature: str = "not_specified"
    channel: int = 6
    sample_rate: int = INTERNAL_SAMPLE_RATE

    @field_validator("mmsi", mode="before")
    @classmethod
    def normalize_mmsi(cls, value: str) -> str:
        normalized = str(value).strip()
        if len(normalized) != 9 or not normalized.isdigit():
            raise ValueError("MMSI must be exactly 9 digits")
        return normalized


@router.post("/generate")
async def generate(req: EncodeRequest):
    nature_sym = NATURE_MAP.get(req.nature, SYM_NATURE_UNDESIGNATED)

    generators = {
        "distress": lambda: TestMessageGenerator.distress(req.mmsi, nature_sym, req.lat, req.lon, req.time_utc),
        "safety": lambda: TestMessageGenerator.all_ships_safety(req.mmsi),
        "urgency": lambda: TestMessageGenerator.all_ships_urgency(req.mmsi),
        "routine": lambda: TestMessageGenerator.individual_routine(req.mmsi, "334455667"),
        "test": lambda: TestMessageGenerator.test(req.mmsi),
    }

    msg_gen = generators.get(req.msg_type, generators["test"])
    msg = msg_gen()

    modulator = DSCModulator(req.sample_rate)
    audio = modulator.modulate(msg)

    buf = io.BytesIO()
    write_wav_normalized(buf, audio, req.sample_rate)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="audio/wav",
        headers={"Content-Disposition": f"attachment; filename=dsc_{req.msg_type}.wav"},
    )
