"""FastAPI application for VHF DSC web interface."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from web.routes.decode import router as decode_router
from web.routes.encode import router as encode_router
from web.routes.stream import router as stream_router
from web.routes.status import router as status_router

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
            body { font-family: system-ui, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
            h1 { color: #1a1a2e; }
            .card { border: 1px solid #ddd; border-radius: 8px; padding: 1.5rem; margin: 1rem 0; }
            .card h2 { margin-top: 0; }
            a { color: #0066cc; text-decoration: none; }
            a:hover { text-decoration: underline; }
            .status { display: inline-block; padding: 0.25rem 0.5rem; border-radius: 4px; background: #d4edda; color: #155724; }
        </style>
    </head>
    <body>
        <h1>VHF DSC Encoder/Decoder</h1>
        <p><span class="status">ITU-R M.493-16 Compliant</span></p>

        <div class="card">
            <h2>Decode</h2>
            <p>Upload audio files (WAV, raw) for DSC message decoding.</p>
            <a href="/decode/">Go to Decoder &rarr;</a>
        </div>

        <div class="card">
            <h2>Encode</h2>
            <p>Generate DSC test messages as WAV audio files.</p>
            <a href="/encode/">Go to Encoder &rarr;</a>
        </div>

        <div class="card">
            <h2>Live Monitor</h2>
            <p>Connect via WebSocket for real-time DSC message monitoring.</p>
            <p>WebSocket: <code>ws://localhost:8000/stream/ws</code></p>
        </div>

        <div class="card">
            <h2>API</h2>
            <p>REST API documentation available at <a href="/docs">/docs</a></p>
        </div>
    </body>
    </html>
    """
