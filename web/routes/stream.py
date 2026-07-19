"""Stream route - WebSocket for live monitoring."""

from fastapi import APIRouter, WebSocket
import json
import asyncio

from vhf_dsc.decoder import DSCDecoderPipeline
from vhf_dsc.protocol.constants import INTERNAL_SAMPLE_RATE

router = APIRouter(prefix="/stream", tags=["stream"])

_connected_clients: list[WebSocket] = []
_pipeline = DSCDecoderPipeline(INTERNAL_SAMPLE_RATE)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _connected_clients.append(websocket)

    try:
        while True:
            data = await websocket.receive_bytes()
            import numpy as np
            samples = np.frombuffer(data, dtype=np.float32)
            messages = _pipeline.process(samples)

            for msg in messages:
                msg_data = msg.to_dict()
                for client in _connected_clients:
                    try:
                        await client.send_text(json.dumps(msg_data))
                    except Exception:
                        pass
    except Exception:
        pass
    finally:
        _connected_clients.remove(websocket)
