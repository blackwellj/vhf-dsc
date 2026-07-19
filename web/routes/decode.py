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
    <html>
    <head><title>DSC Decode</title></head>
    <body>
        <h1>Upload Audio for DSC Decoding</h1>
        <form action="/decode/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".wav,.raw,.iq">
            <button type="submit">Decode</button>
        </form>
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
