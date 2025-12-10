from fastapi import APIRouter

router = APIRouter()

from . import chat, upload

__all__ = ["router"]