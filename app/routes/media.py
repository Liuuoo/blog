import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services import get_media_path

router = APIRouter()


@router.get("/api/media/{filename:path}")
async def serve_media(filename: str):
    """根据文件名从媒体索引中查找并返回图片/视频文件。"""
    # 安全：只取文件名，防止路径穿越
    safe_name = os.path.basename(filename)
    if not safe_name:
        raise HTTPException(status_code=400, detail="无效文件名")

    real_path = get_media_path(safe_name)
    if not real_path or not os.path.exists(real_path):
        raise HTTPException(status_code=404, detail="媒体文件不存在")

    return FileResponse(real_path)
