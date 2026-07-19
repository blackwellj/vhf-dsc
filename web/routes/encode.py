"""Encode route - generate DSC test messages."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import io

from vhf_dsc.encoder import TestMessageGenerator, DSCModulator
from vhf_dsc.io.wav import write_wav_normalized
from vhf_dsc.protocol.symbols import SYM_NATURE_UNDESIGNATED
from vhf_dsc.protocol.constants import INTERNAL_SAMPLE_RATE

router = APIRouter(prefix="/encode", tags=["encode"])


@router.get("/", response_class=HTMLResponse)
async def encode_page():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>DSC Encoder</title></head>
    <body>
        <h1>Generate DSC Test Messages</h1>
        <form action="/encode/generate" method="post">
            <label>Message Type:</label>
            <select name="msg_type">
                <option value="distress">Distress</option>
                <option value="safety">Safety</option>
                <option value="urgency">Urgency</option>
                <option value="routine">Routine</option>
                <option value="test">Test</option>
            </select><br>
            <label>MMSI:</label>
            <input type="text" name="mmsi" value="234567890"><br>
            <label>Latitude:</label>
            <input type="number" name="lat" value="51.5074" step="0.0001"><br>
            <label>Longitude:</label>
            <input type="number" name="lon" value="-0.1278" step="0.0001"><br>
            <button type="submit">Generate WAV</button>
        </form>
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
