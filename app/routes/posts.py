import hashlib
import os
from typing import List

import frontmatter
from fastapi import APIRouter, HTTPException, Query

from app.config import ALLOWED_EXTENSIONS, EXTERNAL_SOURCES, LOCKED_CATEGORIES, POSTS_DIR
from app.models import PostDetail, PostSummary
from app.services import (
    build_post_summary,
    get_file_extension,
    get_grouped_source_members,
    get_lock_scope,
    get_post_category_label,
    normalize_post_date,
    render_markdown,
    resolve_path,
    scan_posts,
    strip_virtual_unarchived,
)
from app.state import verified_sessions

router = APIRouter()


def _ensure_category_access(category: str) -> None:
    lock_scope = get_lock_scope(category)
    if not lock_scope:
        return

    token = hashlib.md5(f"{lock_scope}:{LOCKED_CATEGORIES[lock_scope]}".encode()).hexdigest()
    if token not in verified_sessions:
        raise HTTPException(status_code=403, detail="该分类已加密，请先验证密码")


def _build_search_paths(path: str) -> List[str]:
    search_paths = [path]
    for ext in sorted(ALLOWED_EXTENSIONS):
        candidate = f"{path}{ext}"
        if candidate not in search_paths:
            search_paths.append(candidate)
    return search_paths


@router.get("/api/posts", response_model=List[PostSummary])
async def list_posts(category: str = Query(default="", description="分类名")):
    if category == "_uncategorized":
        return scan_posts("")
    if category:
        _ensure_category_access(category)
        return scan_posts(category)

    all_posts = scan_posts("")
    grouped_members = set(get_grouped_source_members())

    if os.path.exists(POSTS_DIR):
        for name in os.listdir(POSTS_DIR):
            if os.path.isdir(os.path.join(POSTS_DIR, name)) and not get_lock_scope(name):
                all_posts.extend(scan_posts(name))

    for cat_name in EXTERNAL_SOURCES:
        if cat_name in grouped_members or get_lock_scope(cat_name):
            continue
        all_posts.extend(scan_posts(cat_name))

    all_posts.sort(key=lambda item: item.date, reverse=True)
    return all_posts


@router.get("/api/posts/{slug:path}", response_model=PostDetail)
async def get_post(slug: str):
    cleaned_slug, _ = strip_virtual_unarchived(slug)
    cleaned_parts = [part for part in cleaned_slug.split("/") if part]
    if len(cleaned_parts) > 1:
        _ensure_category_access(cleaned_parts[0])

    filename = cleaned_parts[-1] if cleaned_parts else slug
    virtual_parent = "/".join([part for part in slug.split("/")[:-1] if part])
    resolved_path = resolve_path(slug)

    actual_path = None
    for search_path in _build_search_paths(resolved_path):
        if os.path.exists(search_path):
            actual_path = search_path
            filename = os.path.basename(search_path)
            break

    if not actual_path:
        raise HTTPException(status_code=404, detail="找不到该文章或源码文件")

    ext = get_file_extension(filename)
    category_label = get_post_category_label(virtual_parent)

    try:
        if ext == ".md":
            post = frontmatter.load(actual_path)
            return PostDetail(
                slug=slug,
                title=str(post.get("title", filename.replace(".md", ""))),
                date=normalize_post_date(post.get("date"), actual_path),
                summary=build_post_summary(post.get("summary", ""), post.content),
                category=category_label,
                content=render_markdown(post.content),
                is_source=False,
            )

        with open(actual_path, "r", encoding="utf-8", errors="replace") as file:
            raw_code = file.read()
        lang = ext[1:]
        return PostDetail(
            slug=slug,
            title=filename,
            date=normalize_post_date(None, actual_path),
            summary=f"{lang.upper()} 源码",
            category=category_label,
            content=render_markdown(f"```{lang}\n{raw_code}\n```"),
            is_source=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"渲染失败: {exc}") from exc
