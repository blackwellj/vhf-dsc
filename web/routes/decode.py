"""Decode route - file upload and decode."""

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse

from vhf_dsc.decoder import DSCDecoderPipeline
from vhf_dsc.io.wav import read_wav
from vhf_dsc.io.raw import read_real
from vhf_dsc.io.file_upload import FileUploadHandler

router = APIRouter(prefix="/decode", tags=["decode"])
upload_handler = FileUploadHandler()


@router.get("/", response_class=HTMLResponse)
async def decode_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head><title>DSC Decode</title></head>
    <body>
        <style>
            body { font-family: system-ui, sans-serif; max-width: 860px; margin: 2rem auto; padding: 0 1rem; }
            .card { border: 1px solid #d9e2ec; border-radius: 12px; padding: 1.25rem; }
            h1 { margin-top: 0; }
            form { display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center; }
            input, button { padding: 0.6rem; border-radius: 8px; border: 1px solid #bcccdc; font: inherit; }
            button { background: #0f5bd8; color: white; border-color: #0f5bd8; cursor: pointer; }
            button:hover { background: #0d4db8; }
            #status { color: #486581; margin: 0.75rem 0; }
            #results {
                background: #0b1220;
                color: #d1fae5;
                border-radius: 8px;
                padding: 0.9rem;
                min-height: 220px;
                white-space: pre-wrap;
                word-break: break-word;
                font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
                font-size: 0.84rem;
            }
            a { color: #0f5bd8; text-decoration: none; font-weight: 600; }
        </style>
        <div class="card">
            <h1>Decode DSC Audio</h1>
            <form id="decode-form">
                <input type="file" name="file" accept=".wav,.raw,.iq" required>
                <button type="submit">Decode File</button>
            </form>
            <p id="status">Select a file and click decode.</p>
            <div id="results">Decoded output will appear here.</div>
            <p><a href="/">Back to dashboard</a></p>
        </div>
        <script>
            const form = document.getElementById("decode-form");
            const status = document.getElementById("status");
            const results = document.getElementById("results");

            form.addEventListener("submit", async (event) => {
                event.preventDefault();
                status.textContent = "Decoding...";
                results.textContent = "Processing file...";

                try {
                    const response = await fetch("/decode/upload", {
                        method: "POST",
                        body: new FormData(form),
                    });
                    const data = await response.json();
                    if (!response.ok) {
                        throw new Error(data.detail || `HTTP ${response.status}`);
                    }

                    status.textContent = `Done. Messages: ${data.total}, Errors: ${data.errors}`;
                    results.textContent = JSON.stringify(data, null, 2);
                } catch (error) {
                    status.textContent = `Decode failed: ${error.message}`;
                    results.textContent = "No decoded output available.";
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
