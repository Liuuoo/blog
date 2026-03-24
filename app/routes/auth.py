import hashlib

from fastapi import APIRouter, HTTPException

from app.config import LOCKED_CATEGORIES
from app.models import PasswordRequest
from app.services import get_lock_scope
from app.state import verified_sessions

router = APIRouter()


@router.post("/api/verify-password")
async def verify_password(req: PasswordRequest):
    lock_scope = get_lock_scope(req.category) or req.category
    expected = LOCKED_CATEGORIES.get(lock_scope)
    if expected is None:
        raise HTTPException(status_code=400, detail="该分类无需密码")

    if req.password == expected:
        token = hashlib.md5(f"{lock_scope}:{expected}".encode()).hexdigest()
        verified_sessions.add(token)
        return {"success": True, "message": "验证通过"}

    raise HTTPException(status_code=401, detail="密码错误")
