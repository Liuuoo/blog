from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import ADMIN_PASSWORD, CATEGORY_ALIASES, save_config

router = APIRouter()


class RenameCategoryRequest(BaseModel):
    password: str
    path: str
    new_name: str


@router.post("/api/admin/rename-category")
async def rename_category(req: RenameCategoryRequest):
    if req.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="管理员密码错误")

    if not req.path or not req.new_name.strip():
        raise HTTPException(status_code=400, detail="路径和新名称不能为空")

    CATEGORY_ALIASES[req.path] = req.new_name.strip()
    save_config()

    return {"success": True, "message": f"已将 '{req.path}' 重命名为 '{req.new_name.strip()}'"}
