"""Encode route - generate DSC test messages."""

import io

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

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
    <head><title>DSC Encoder</title></head>
    <body>
        <style>
            body { font-family: system-ui, sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; }
            .card { border: 1px solid #d9e2ec; border-radius: 12px; padding: 1.25rem; }
            h1 { margin-top: 0; }
            form { display: grid; gap: 0.75rem; }
            label { font-weight: 600; display: grid; gap: 0.35rem; }
            input, select, button { padding: 0.6rem; border-radius: 8px; border: 1px solid #bcccdc; font: inherit; }
            button { background: #0f5bd8; color: white; border-color: #0f5bd8; cursor: pointer; }
            button:hover { background: #0d4db8; }
            #status { margin-top: 0.75rem; color: #486581; font-size: 0.95rem; }
            a { color: #0f5bd8; text-decoration: none; font-weight: 600; }
        </style>
        <div class="card">
            <h1>Generate DSC Test Message (.wav)</h1>
            <form id="encode-form">
                <label>Message Type
                    <select name="msg_type">
                        <option value="distress">Distress</option>
                        <option value="safety">Safety</option>
                        <option value="urgency">Urgency</option>
                        <option value="routine">Routine</option>
                        <option value="test">Test</option>
                    </select>
                </label>
                <label>MMSI
                    <input type="text" name="mmsi" value="234567890" pattern="[0-9]{9}" required>
                </label>
                <label>Latitude
                    <input type="number" name="lat" value="51.5074" step="0.0001">
                </label>
                <label>Longitude
                    <input type="number" name="lon" value="-0.1278" step="0.0001">
                </label>
                <button type="submit">Generate and Download WAV</button>
            </form>
            <p id="status">Ready.</p>
            <a href="/">Back to dashboard</a>
        </div>
        <script>
            const form = document.getElementById("encode-form");
            const status = document.getElementById("status");

            form.addEventListener("submit", async (event) => {
                event.preventDefault();
                status.textContent = "Generating .wav file...";
                const payload = Object.fromEntries(new FormData(form).entries());
                payload.lat = Number(payload.lat);
                payload.lon = Number(payload.lon);

                try {
                    const response = await fetch("/encode/generate", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload),
                    });
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    const blob = await response.blob();
                    const msgType = payload.msg_type || "test";
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement("a");
                    link.href = url;
                    link.download = `dsc_${msgType}.wav`;
                    document.body.appendChild(link);
                    link.click();
                    link.remove();
                    URL.revokeObjectURL(url);
                    status.textContent = "Download started.";
                } catch (error) {
                    status.textContent = `Generation failed: ${error.message}`;
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
