"""Status route - health and metrics."""

from fastapi import APIRouter

router = APIRouter(prefix="/status", tags=["status"])

_message_count = 0
_error_count = 0
_start_time = None


@router.get("/")
async def get_status():
    return {
        "status": "ok",
        "messages_decoded": _message_count,
        "errors": _error_count,
        "uptime": "running",
    }


@router.get("/health")
async def health_check():
    return {"status": "healthy"}
